"""ElevenLabs-Stimmen mit Zeichen-Zeitstempeln, Zahlen-Ausschreibung und Cache.

Der API-Key wird ausschliesslich aus der Umgebungsvariable ELEVENLABS_API_KEY gelesen.
Ist sie nicht gesetzt, wird ein Platzhalter gesendet; in Umgebungen mit
authentifizierendem Proxy (z. B. Claude-Code-Cloud) ersetzt der Proxy ihn.
Der Key wird nie geloggt, gespeichert oder in Dateien geschrieben.
"""
from __future__ import annotations

import base64
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "out" / "cache"
VOICES_FILE = Path(__file__).resolve().parent / "voices.json"
API = "https://api.elevenlabs.io"

# ---------------------------------------------------------------- Zahlen -> Worte
_UNITS = ["null", "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun",
          "zehn", "elf", "zwölf", "dreizehn", "vierzehn", "fünfzehn", "sechzehn", "siebzehn",
          "achtzehn", "neunzehn"]
_TENS = {2: "zwanzig", 3: "dreißig", 4: "vierzig", 5: "fünfzig", 6: "sechzig", 7: "siebzig",
         8: "achtzig", 9: "neunzig"}


def _u100(n: int, final: bool = True) -> str:
    if n < 20:
        w = _UNITS[n]
        return w if (final or n != 1) else "ein"
    t, u = divmod(n, 10)
    return ((("ein" if u == 1 else _UNITS[u]) + "und") if u else "") + _TENS[t]


def _u1000(n: int, final: bool = True) -> str:
    h, r = divmod(n, 100)
    s = ""
    if h:
        s = "hundert" if h == 1 else _u100(h, False) + "hundert"
    if r:
        s += _u100(r, final)
    return s or "null"


def zahl_de(n: int, final: bool = True) -> str:
    """Ganze Zahl (0..999999) als deutsches Zahlwort."""
    if n == 0:
        return "null"
    t, r = divmod(n, 1000)
    s = ""
    if t:
        s = "tausend" if t == 1 else _u1000(t, False) + "tausend"
    if r:
        s += _u1000(r, final)
    return s


_NUM = re.compile(r"^(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?$")


def _num_token(core: str):
    """'15,50' -> ('fünfzehn Euro fünfzig', True) ; '150' -> ('hundertfünfzig', False)."""
    m = _NUM.match(core)
    if not m:
        return None
    ganz = int(m.group(1).replace(".", ""))
    if m.group(2) is not None:
        cents = int(m.group(2).ljust(2, "0"))
        euro = "ein" if ganz == 1 else zahl_de(ganz)
        return (f"{euro} Euro {zahl_de(cents)}" if cents else f"{euro} Euro"), True
    return zahl_de(ganz), False


def split_words(text: str):
    """Untertitel-Woerter: an Leerzeichen getrennt, Satzzeichen bleiben am Wort."""
    return [w for w in text.split() if w]


def speech_mapping(text: str, speech_overrides: dict | None = None):
    """Erzeugt den Sprechtext und pro Untertitel-Wort den Zeichenbereich darin.

    Rueckgabe: (speech_text, [(wort, start_char, end_char), ...])
    end_char == start_char bedeutet: Wort wird nicht separat gesprochen (z. B. 'Euro'
    nach einem Dezimalbetrag, der bereits 'Euro' enthaelt).
    """
    words = split_words(text)
    out, spans, pos = [], [], 0
    skip_euro = False
    for w in words:
        m = re.match(r"^([\(\"'„]*)(.*?)([\.,!?;:…\)\"'“]*)$", w)
        pre, core, post = m.group(1), m.group(2), m.group(3)
        spoken = None
        if speech_overrides and w in speech_overrides:
            piece = speech_overrides[w]
            start = pos + (1 if out else 0)
            out.append(piece)
            pos = start + len(piece)
            spans.append((w, start, pos))
            skip_euro = False
            continue
        if speech_overrides and core in speech_overrides:
            spoken = speech_overrides[core]
        elif core in ("Euro", "€") and skip_euro:
            spoken = ""
        elif core == "€":
            spoken = "Euro"
        else:
            r = _num_token(core)
            if r:
                spoken, had_euro = r
                skip_euro = had_euro
                piece = pre + spoken + post
                start = pos + (1 if out else 0)
                out.append(piece)
                pos = start + len(piece)
                spans.append((w, start, pos))
                continue
            if "-" in core and re.match(r"^\w+-\w+$", core):
                spoken = core.replace("-", "").capitalize() if core[0].isupper() else core.replace("-", "")
        skip_euro = False if spoken != "" else skip_euro
        if spoken == "":
            # Satzzeichen des verschluckten Wortes an das vorige Stueck haengen
            if post and out:
                out[-1] = out[-1] + post
                pos += len(post)
            spans.append((w, pos, pos))
            continue
        if spoken is None:
            spoken = core
        piece = pre + spoken + post
        start = pos + (1 if out else 0)
        out.append(piece)
        pos = start + len(piece)
        spans.append((w, start, pos))
    return " ".join(out), spans


# ---------------------------------------------------------------- API
def _key() -> str:
    return os.environ.get("ELEVENLABS_API_KEY") or "proxy-injected"


def api(method: str, path: str, body: dict | None = None, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"xi-api-key": _key(), "Content-Type": "application/json",
                                          "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:400]
        raise RuntimeError(f"ElevenLabs {method} {path} -> HTTP {e.code}: {msg}") from None


MODEL = "eleven_multilingual_v2"


def pick_model() -> str:
    """Vorgabe: eleven_multilingual_v2. Ist die API nicht erreichbar -> 'piper' (Fallback)."""
    try:
        api("GET", "/v1/models", timeout=20)
        return MODEL
    except Exception as e:  # noqa: BLE001
        print("[tts] ElevenLabs nicht erreichbar -> Piper-Fallback:", str(e)[:120], flush=True)
        return "piper"


def _score(v: dict, role: str) -> float:
    lab = v.get("labels") or {}
    txt = (v.get("name", "") + " " + " ".join(str(x) for x in lab.values()) + " " +
           (v.get("description") or "")).lower()
    s = 0.0
    if role == "kalle":
        s += 3 * (lab.get("gender") == "male")
        s += 2 * (lab.get("age") in ("middle_aged", "middle aged", "old"))
        for k in ("warm", "deep", "resonant", "comforting", "cozy", "storyteller"):
            s += 1.5 * (k in txt)
        for k in ("fierce", "dominant", "formal", "husky"):
            s -= 2 * (k in txt)
    else:
        s += 2 * (lab.get("age") == "young")
        for k in ("bright", "friendly", "playful", "upbeat", "energetic", "warm", "enthusiast"):
            s += 1.5 * (k in txt)
        for k in ("robot", "cartoon", "child", "sassy", "rough"):
            s -= 3 * (k in txt)
    return s


def load_voices(model: str | None = None) -> dict:
    """voices.json lesen bzw. anlegen. ENV-Variablen haben Vorrang."""
    cfg = json.loads(VOICES_FILE.read_text()) if VOICES_FILE.exists() else {}
    env = {"kalle": os.environ.get("ELEVENLABS_VOICE_KALLE"), "byte": os.environ.get("ELEVENLABS_VOICE_BYTE")}
    need = [r for r in ("kalle", "byte") if not env[r] and r not in cfg.get("voices", {})]
    if need:
        voices = api("GET", "/v1/voices")["voices"]
        cfg.setdefault("voices", {})
        for r in need:
            other = cfg["voices"].get("kalle", {}).get("voice_id") if r == "byte" else None
            best = max((v for v in voices if v["voice_id"] != other), key=lambda v: _score(v, r))
            cfg["voices"][r] = {"voice_id": best["voice_id"], "name": best["name"], "source": "auto (GET /v1/voices)"}
        VOICES_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    for r in ("kalle", "byte"):
        if env[r]:
            cfg["voices"][r] = {"voice_id": env[r], "name": "aus ELEVENLABS_VOICE_" + r.upper(), "source": "env"}
    if model:
        cfg["model"] = model
    return cfg


def _ffmpeg():
    return os.environ.get("FFMPEG", "ffmpeg")


def synth(speech_text: str, voice_id: str, model: str, settings: dict, tag: str = "",
          tail: str = "", seed: int | None = None) -> dict:
    """Spricht speech_text; Ergebnis (WAV 48 kHz mono + Alignment) wird gecacht.

    tail: v3-Tag am Zeilenende – verhindert, dass das letzte Wort abgeschnitten wird;
    die dadurch entstehende Stille wird danach weggeschnitten.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    if model == "piper":
        return synth_piper(speech_text, voice_id, settings)
    full_text = ((tag + " ") if tag else "") + speech_text + ((" " + tail) if tail else "")
    h = hashlib.sha256(json.dumps([full_text, voice_id, model, settings, seed], sort_keys=True,
                                  ensure_ascii=False).encode()).hexdigest()[:20]
    meta_p, wav_p = CACHE / f"{h}.json", CACHE / f"{h}.wav"
    if meta_p.exists() and wav_p.exists():
        meta = json.loads(meta_p.read_text())
        meta["cached"] = True
        return meta
    body = {"text": full_text, "model_id": model, "voice_settings": settings, "language_code": "de"}
    if seed is not None:
        body["seed"] = seed
    try:
        d = api("POST", f"/v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128", body)
    except RuntimeError as e:
        if "language_code" in str(e):
            body.pop("language_code")
            d = api("POST", f"/v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128", body)
        else:
            raise
    mp3 = CACHE / f"{h}.mp3"
    mp3.write_bytes(base64.b64decode(d["audio_base64"]))
    raw_p = CACHE / f"{h}_raw.wav"
    subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", "48000", str(raw_p)], check=True)
    _trim_tail(raw_p, wav_p)
    al = d.get("alignment") or d.get("normalized_alignment")
    meta = {"hash": h, "text": full_text, "speech_text": speech_text, "tag": tag, "tail": tail, "seed": seed,
            "voice_id": voice_id,
            "model": model, "settings": settings, "wav": str(wav_p.relative_to(ROOT)),
            "chars": al["characters"], "starts": al["character_start_times_seconds"],
            "ends": al["character_end_times_seconds"]}
    meta_p.write_text(json.dumps(meta, ensure_ascii=False))
    meta["cached"] = False
    return meta


def word_times(meta: dict, spans) -> list:
    """Ordnet jedem Untertitel-Wort Start/Ende aus den Zeichen-Zeitstempeln zu."""
    chars = meta["chars"]
    al_text = "".join(chars)
    full = meta["text"]
    offset = (len(meta["tag"]) + 1) if meta.get("tag") else 0  # Laenge eines vorangestellten Tags
    # Zeichenindex im Volltext -> Index im Alignment (meist identisch)
    if al_text == full:
        idx_map = list(range(len(full)))
    else:
        idx_map = [None] * len(full)
        sm = difflib.SequenceMatcher(a=full, b=al_text, autojunk=False)
        for a0, b0, n in sm.get_matching_blocks():
            for k in range(n):
                idx_map[a0 + k] = b0 + k
    starts, ends = meta["starts"], meta["ends"]
    res, last_end = [], 0.0
    for w, s, e in spans:
        if e <= s:
            res.append({"w": w, "start": last_end, "end": last_end})
            continue
        ids = [idx_map[offset + i] for i in range(s, e) if offset + i < len(idx_map) and idx_map[offset + i] is not None]
        # nur Buchstaben/Ziffern fuer Start, damit Satzzeichen nicht verschieben
        letter_ids = [j for j, i in zip(ids, range(s, e)) if meta["speech_text"][i].isalnum()] or ids
        if not letter_ids:
            res.append({"w": w, "start": last_end, "end": last_end})
            continue
        st, en = starts[letter_ids[0]], ends[letter_ids[-1]]
        res.append({"w": w, "start": st, "end": en})
        last_end = en
    return res


def _trim_tail(src: Path, dst: Path, keep: float = 0.12):
    """Schneidet Stille am Ende weg (nach dem letzten hoerbaren Laut + keep s) mit kurzem Fade."""
    import numpy as np
    import soundfile as sf
    y, sr = sf.read(str(src), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    hop = int(0.01 * sr)
    rms = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2)) for i in range(0, len(y), hop)])
    thr = max(rms.max() * 10 ** (-40 / 20), 1e-4)
    loud = np.nonzero(rms > thr)[0]
    end = min(len(y), (int(loud[-1]) + 1) * hop + int(keep * sr)) if len(loud) else len(y)
    y = y[:end].copy()
    n = min(int(0.03 * sr), len(y))
    y[-n:] *= np.linspace(1, 0, n) ** 2
    sf.write(str(dst), y, sr, subtype="PCM_16")


def tighten(meta: dict, lead: float = 0.04, tail: float = 0.16) -> dict:
    """Schneidet Stille am Anfang/Ende und kuerzt lange Pausen zwischen Woertern.

    Erlaubte Pausen: nach Satzende 0,30 s, nach Komma/Doppelpunkt 0,20 s, nach '…' 0,45 s,
    sonst 0,14 s. Schnitte mit 12-ms-Crossfade. Zeitstempel werden mitverschoben.
    """
    import numpy as np
    import soundfile as sf
    src = ROOT / meta["wav"]
    dst = src.with_name(src.stem + "_tight.wav")
    chars, st, en = meta["chars"], meta["starts"], meta["ends"]
    off = (len(meta["tag"]) + 1) if meta.get("tag") else 0
    n_sp = len(meta["speech_text"])
    alnum = [i for i in range(off, off + n_sp) if i < len(chars) and chars[i].isalnum()]
    if not alnum:
        return meta
    y, sr = sf.read(str(src), dtype="float32")
    hop = int(0.01 * sr)
    rms = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2)) for i in range(0, len(y), hop)])
    silent = rms < max(rms.max() * 10 ** (-36 / 20), 2e-4)
    loud = np.nonzero(~silent)[0]
    first_loud, last_loud = loud[0] * 0.01, (loud[-1] + 1) * 0.01

    def silent_run(t0, t1):
        """laengster stiller Abschnitt in [t0, t1] (laut Pegel, nicht laut Zeitstempel)"""
        i0, i1 = int(t0 / 0.01), int(t1 / 0.01)
        best, cur = (0, 0), None
        for i in range(max(0, i0), min(len(silent), i1)):
            if silent[i]:
                cur = (cur[0], i + 1) if cur else (i, i + 1)
                if cur[1] - cur[0] > best[1] - best[0]:
                    best = cur
            else:
                cur = None
        return best[0] * 0.01, best[1] * 0.01

    keep = []  # (t0, t1) Bereiche der Quelle
    t0 = max(0.0, first_loud - lead)
    for a, b in zip(alnum, alnum[1:]):
        if b == a + 1:
            continue
        between = "".join(chars[a + 1:b])
        allow = 0.45 if "…" in between else 0.30 if any(c in between for c in ".!?") else \
            0.20 if any(c in between for c in ",:;") else 0.14
        s0, s1 = silent_run(en[a] - 0.15, st[b] + 0.15)
        if s1 - s0 > allow and s0 > t0:
            keep.append((t0, s0 + allow / 2))
            t0 = s1 - allow / 2
    end_t = min(len(y) / sr, last_loud + tail, en[alnum[-1]] + 0.6)
    keep.append((t0, max(end_t, t0 + 0.05)))
    xf = int(0.012 * sr)
    out = np.zeros(0, np.float32)
    mapping = []  # (src_t0, src_t1, dst_t0)
    for k0, k1 in keep:
        seg = y[int(k0 * sr):int(k1 * sr)].copy()
        dst_t0 = len(out) / sr
        if len(out) >= xf and len(seg) >= xf:
            fade = np.linspace(0, 1, xf, dtype=np.float32)
            out[-xf:] = out[-xf:] * (1 - fade) + seg[:xf] * fade
            dst_t0 = (len(out) - xf) / sr
            seg = seg[xf:]
            k0 += xf / sr
            dst_t0 = len(out) / sr - (xf / sr)
        mapping.append((k0 - (xf / sr if mapping else 0), k1, dst_t0 if mapping else 0.0))
        out = np.concatenate([out, seg])
    n = min(int(0.03 * sr), len(out))
    out[-n:] *= np.linspace(1, 0, n) ** 2
    sf.write(str(dst), out, sr, subtype="PCM_16")

    def remap(t):
        for s0, s1, d0 in mapping:
            if t <= s1:
                return d0 + max(0.0, t - s0)
        s0, s1, d0 = mapping[-1]
        return d0 + (s1 - s0)
    m = dict(meta)
    m["wav"] = str(dst.relative_to(ROOT))
    m["starts"] = [remap(t) for t in st]
    m["ends"] = [remap(t) for t in en]
    m["tightened"] = True
    return m


def stretch(meta: dict, factor: float, pitch_st: float = 0.0) -> dict:
    """Rubberband in einem Durchgang: Tempo (factor>1 = schneller, Tonhoehe bleibt) und optional
    Tonhoehe in Halbtoenen (Formanten bleiben erhalten -> hoeher, aber kein Micky-Maus-Klang)."""
    if abs(factor - 1) < 0.01 and abs(pitch_st) < 0.01:
        return meta
    src = ROOT / meta["wav"]
    dst = src.with_name(src.stem + f"_t{factor:.3f}" + (f"_p{pitch_st:+.1f}" if pitch_st else "") + ".wav")
    if not dst.exists():
        subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", str(src), "-af",
                        f"rubberband=tempo={factor:.4f}:pitch={2 ** (pitch_st / 12):.5f}:pitchq=quality:"
                        f"formant=preserved:transients=smooth",
                        "-ar", "48000", "-ac", "1", str(dst)], check=True)
    m = dict(meta)
    m["wav"] = str(dst.relative_to(ROOT))
    m["starts"] = [t / factor for t in meta["starts"]]
    m["ends"] = [t / factor for t in meta["ends"]]
    m["stretch"] = factor
    m["pitch_st"] = pitch_st
    return m


def audio_duration(wav: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


# Startwerte pro Rolle (Vorgabe, eleven_multilingual_v2)
BASE_SETTINGS = {
    "kalle": {"stability": 0.40, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": True, "speed": 0.9},
    "byte": {"stability": 0.50, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": True, "speed": 0.9},
}
# Ziel-Tempo (Woerter/s). eleven_v3 ignoriert 'speed' -> Korrektur per Rubberband-Stretch.
TEMPO = {"kalle": (2.1, 2.7), "byte": (2.2, 2.75)}
STRETCH_LIMIT = (0.88, 1.15)   # Natuerlichkeit schuetzen: hoechstens 12 % langsamer / 15 % schneller

def line_settings(role: str, attempt: int, cfg: dict, model: str):
    """Einstellungen und Seed pro Versuch (jeder Versuch ist eine neue, reproduzierbare Variante)."""
    s = dict(BASE_SETTINGS[role])
    s.update(cfg.get("settings", {}).get(role, {}))
    if attempt == 1:                  # zweiter Versuch: stabiler
        s["stability"] = round(min(1.0, s["stability"] + 0.25), 2)
    elif attempt == 2:                # dritter Versuch: mehr Ausdruck, weniger Stil
        s["stability"] = round(max(0.3, s["stability"] - 0.05), 2)
        s["style"] = round(max(0.0, s["style"] - 0.15), 2)
    seed = 4200 + 17 * attempt
    return s, seed


# ---------------------------------------------------------------- Piper-Fallback
PIPER_DIR = ROOT / "out" / "cache" / "piper"
PIPER_VOICES = {"kalle": ("de_DE-thorsten-high", 0.0), "byte": ("de_DE-thorsten-high", 3.0)}
PIPER_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high/"


def synth_piper(speech_text: str, role: str, settings: dict) -> dict:
    """Fallback ohne ElevenLabs: Piper (Thorsten). Byte = Thorsten +3 Halbtoene (Formanten erhalten).
    Wort-Zeitstempel proportional zur Zeichenanzahl."""
    import soundfile as sf
    name, pitch = PIPER_VOICES[role]
    PIPER_DIR.mkdir(parents=True, exist_ok=True)
    onnx = PIPER_DIR / f"{name}.onnx"
    for suf in (".onnx", ".onnx.json"):
        p = PIPER_DIR / (name + suf)
        if not p.exists():
            urllib.request.urlretrieve(PIPER_URL + name + suf, p)
    h = hashlib.sha256(json.dumps([speech_text, role, "piper"]).encode()).hexdigest()[:20]
    raw, wav = CACHE / f"{h}_piper.wav", CACHE / f"{h}.wav"
    if not wav.exists():
        subprocess.run([sys.executable, "-m", "piper", "-m", str(onnx), "-f", str(raw)], input=speech_text.encode(),
                       check=True)
        af = "aresample=48000" + (f",rubberband=pitch={2 ** (pitch / 12):.5f}:formant=preserved" if pitch else "")
        subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", str(raw), "-af", af, "-ac", "1", "-ar", "48000", str(wav)],
                       check=True)
    y, sr = sf.read(str(wav))
    dur = len(y) / sr
    n = len(speech_text)
    chars = list(speech_text)
    starts = [0.05 + (dur - 0.1) * i / n for i in range(n)]
    ends = [0.05 + (dur - 0.1) * (i + 1) / n for i in range(n)]
    return {"hash": h, "text": speech_text, "speech_text": speech_text, "tag": "", "tail": "", "seed": None,
            "voice_id": name, "model": "piper", "settings": {}, "wav": str(wav.relative_to(ROOT)),
            "chars": chars, "starts": starts, "ends": ends, "cached": False}


if __name__ == "__main__":
    if "--check-voices" in sys.argv:
        m = pick_model()
        print("Modell:", m)
        print(json.dumps(load_voices(m)["voices"], indent=2, ensure_ascii=False))
