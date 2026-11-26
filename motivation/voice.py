"""Stimme Satz fuer Satz mit ElevenLabs erzeugen, per Whisper pruefen, besten Take waehlen.

Der API-Schluessel kommt ausschliesslich aus ELEVENLABS_API_KEY. Ist die Variable leer,
wird ein Platzhalter gesendet, den der authentifizierende Proxy der Cloud-Umgebung ersetzt.
Der Schluessel wird nie geloggt oder gespeichert.

  python3 -m motivation.voice            # erzeugt/prueft alle Saetze -> out/motivation/voice/takes.json
  python3 -m motivation.voice --redo 5   # Satz 5 mit neuen Seeds neu erzeugen
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
OUT = ROOT / "out" / "motivation" / "voice"
CACHE = ROOT / "out" / "cache" / "motivation"
API = "https://api.elevenlabs.io"
SR = 48000
TAKES = int(os.environ.get("TAKES", "3"))


def _key() -> str:
    return os.environ.get("ELEVENLABS_API_KEY") or "proxy-injected"


def tts(text, voice_id, model, settings, seed, prev_text, next_text):
    CACHE.mkdir(parents=True, exist_ok=True)
    body = {"text": text, "model_id": model, "voice_settings": settings, "seed": seed,
            "previous_text": prev_text or None, "next_text": next_text or None}
    body = {k: v for k, v in body.items() if v is not None}
    h = hashlib.sha256(json.dumps([body, voice_id], sort_keys=True).encode()).hexdigest()[:20]
    meta_p, mp3_p = CACHE / f"{h}.json", CACHE / f"{h}.mp3"
    if not (meta_p.exists() and mp3_p.exists()):
        req = urllib.request.Request(
            f"{API}/v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_192",
            data=json.dumps(body).encode(), method="POST",
            headers={"xi-api-key": _key(), "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"ElevenLabs HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from None
        mp3_p.write_bytes(base64.b64decode(d["audio_base64"]))
        al = d.get("alignment") or d["normalized_alignment"]
        meta_p.write_text(json.dumps({"chars": al["characters"], "starts": al["character_start_times_seconds"],
                                      "ends": al["character_end_times_seconds"], "body": body}))
    meta = json.loads(meta_p.read_text())
    meta["hash"], meta["mp3"] = h, str(mp3_p)
    return meta


def decode_trim(mp3: str, dst: Path, lead=0.03, tail=0.14):
    """MP3 -> 48 kHz mono WAV, Stille am Anfang/Ende abschneiden. Rueckgabe: Versatz (s) fuer Zeitstempel."""
    raw = dst.with_suffix(".raw.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), str(raw)], check=True)
    y, sr = sf.read(str(raw), dtype="float32")
    raw.unlink()
    hop = int(0.005 * sr)
    rms = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2) + 1e-12) for i in range(0, len(y), hop)])
    thr = max(rms.max() * 10 ** (-42 / 20), 2e-4)
    loud = np.nonzero(rms > thr)[0]
    s = max(0, loud[0] * hop - int(lead * sr))
    e = min(len(y), (loud[-1] + 1) * hop + int(tail * sr))
    y = y[s:e].copy()
    f = int(0.006 * sr)
    y[:f] *= np.linspace(0, 1, f)
    f = int(0.04 * sr)
    y[-f:] *= np.linspace(1, 0, f) ** 2
    sf.write(str(dst), y, sr, subtype="PCM_24")
    return s / sr, len(y) / sr


def word_times(meta, text, offset):
    """Wortzeiten aus den Zeichen-Zeitstempeln (Satzzeichen bleiben am Wort)."""
    chars, st, en = meta["chars"], meta["starts"], meta["ends"]
    al = "".join(chars)
    assert al == text, f"Alignment-Text weicht ab: {al!r}"
    out, i = [], 0
    for m in re.finditer(r"\S+", text):
        ids = [k for k in range(m.start(), m.end()) if text[k].isalnum()]
        out.append({"w": m.group(), "start": round(st[ids[0]] - offset, 3), "end": round(en[ids[-1]] - offset, 3)})
    return out


_norm = lambda s: re.sub(r"[^a-z0-9' ]", " ", s.lower().replace("’", "'")).split()
_WHISPER = None


def whisper(wav: Path):
    global _WHISPER
    from faster_whisper import WhisperModel
    if _WHISPER is None:
        _WHISPER = WhisperModel("medium.en", device="cpu", compute_type="int8")
    import librosa
    y16 = librosa.load(str(wav), sr=16000, mono=True)[0].astype(np.float32)
    segs, _ = _WHISPER.transcribe(y16, language="en", beam_size=5, word_timestamps=True,
                                  condition_on_previous_text=False)
    words = [w for s in segs for w in s.words]
    return " ".join(w.word.strip() for w in words), [{"w": w.word.strip(), "start": w.start, "end": w.end} for w in words]


def wer(ref, hyp):
    r, h = _norm(ref), _norm(hyp)
    num = {"five": "5", "5": "5"}
    r, h = [num.get(x, x) for x in r], [num.get(x, x) for x in h]
    d = np.zeros((len(r) + 1, len(h) + 1), int)
    d[:, 0], d[0, :] = range(len(r) + 1), range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    return d[-1, -1] / max(1, len(r))


def prosody(wav: Path):
    import librosa
    import pyloudnorm as pyln
    y, sr = sf.read(str(wav), dtype="float32")
    y22 = librosa.resample(y, orig_sr=sr, target_sr=22050)
    f0, vf, _ = librosa.pyin(y22, fmin=70, fmax=450, sr=22050, frame_length=1024)
    f0 = f0[~np.isnan(f0)]
    st = 12 * np.log2(f0 / np.median(f0)) if len(f0) else np.array([0.0])
    meter = pyln.Meter(sr, block_size=0.2)
    return {"f0_median": float(np.median(f0)) if len(f0) else 0.0,
            "f0_std_st": float(np.std(st)),          # Tonhoehen-Bewegung in Halbtoenen
            "f0_range_st": float(np.percentile(st, 95) - np.percentile(st, 5)),
            "lufs": float(meter.integrated_loudness(y)) if len(y) > sr * 0.4 else float("nan"),
            "peak_db": float(20 * np.log10(np.abs(y).max() + 1e-9)),
            "dur": len(y) / sr}


def make_take(cfg, idx, seed):
    sents = cfg["sentences"]
    s = sents[idx]
    v = cfg["voice"]
    settings = dict(v["settings"])
    settings["speed"] = cfg["mood_speed"][s["mood"]]
    prev = " ".join(x["text"] for x in sents[max(0, idx - 3):idx])
    nxt = cfg["mood_cue"][s["mood"]]   # Regie-Hinweis als Folgetext: steuert die Stimmung, wird nicht gesprochen
    meta = tts(s["text"], v["voice_id"], v["model"], settings, seed, prev, nxt)
    wav = OUT / f"s{s['id']:02d}_seed{seed}.wav"
    off, dur = decode_trim(meta["mp3"], wav)
    words = word_times(meta, s["text"], off)
    hyp, wwords = whisper(wav)
    pr = prosody(wav)
    w = wer(s["text"], hyp)
    # Abgleich der Wortzeiten ElevenLabs <-> Whisper (Start-Abweichung)
    drift = []
    if len(wwords) == len(words):
        drift = [abs(a["start"] - b["start"]) for a, b in zip(words, wwords)]
    n_words = len(words)
    robot = (n_words >= 3 and pr["f0_std_st"] < 1.2) or pr["f0_range_st"] < 2.0
    wps = n_words / max(0.1, words[-1]["end"] - words[0]["start"])
    return {"id": s["id"], "seed": seed, "wav": str(wav.relative_to(ROOT)), "dur": round(dur, 3), "words": words,
            "whisper": hyp, "wer": round(w, 3), "max_drift": round(max(drift), 3) if drift else None,
            "robot_flag": bool(robot), "wps": round(wps, 2), "settings": settings,
            **{k: round(val, 2) for k, val in pr.items()}}


def punct_ok(ref, hyp):
    """Intonation grob ueber Whisper-Satzzeichen pruefen: Satzende-Zeichen muessen passen
    (Frage statt Aussage = falsche Melodie)."""
    pr = re.findall(r"[.?!]", ref)
    ph = re.findall(r"[.?!]", hyp)
    return pr == ph


def choose(cfg, idx, takes):
    """Bester Take: Whisper muss exakt stimmen, nicht roboterhaft; dann Betonung passend zur Stimmung."""
    mood = cfg["sentences"][idx]["mood"]
    ref = cfg["sentences"][idx]["text"]
    ok = [t for t in takes if t["wer"] == 0 and not t["robot_flag"] and punct_ok(ref, t["whisper"])]
    if not ok:
        return None
    def score(t):
        lively = min(t["f0_std_st"], 4.0)              # lebendig, aber nicht uebertrieben
        over = max(0.0, t["f0_std_st"] - 4.5) * 2
        tempo = -0.5 * abs(t["wps"] - {"calm": 2.7, "rising": 2.9, "quiet": 2.5, "strong": 2.7}[mood])
        energy = t["lufs"]
        e_w = {"calm": -0.05, "rising": 0.08, "quiet": -0.15, "strong": 0.2}[mood]
        return lively - over + tempo + e_w * energy
    return max(ok, key=score)


def rechoose():
    cfg = json.loads((HERE / "script.json").read_text())
    state_p = OUT / "takes.json"
    state = json.loads(state_p.read_text())
    bad = []
    for idx, s in enumerate(cfg["sentences"]):
        e = state[str(s["id"])]
        b = choose(cfg, idx, e["takes"])
        e["chosen"] = b["seed"] if b else None
        if not b:
            bad.append(s["id"])
        print(f"S{s['id']:>2} -> {b and b['seed']}  {b and b['whisper']}  f0std={b and b['f0_std_st']} lufs={b and b['lufs']}")
    state_p.write_text(json.dumps(state, indent=1))
    return bad


def main():
    cfg = json.loads((HERE / "script.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    state_p = OUT / "takes.json"
    state = json.loads(state_p.read_text()) if state_p.exists() else {}
    redo = [int(x) for x in sys.argv[sys.argv.index("--redo") + 1].split(",")] if "--redo" in sys.argv else []
    for idx, s in enumerate(cfg["sentences"]):
        key = str(s["id"])
        entry = state.get(key, {"takes": [], "rounds": 0})
        if entry.get("chosen") and s["id"] not in redo:
            continue
        for rnd in range(entry["rounds"], entry["rounds"] + 3):
            seeds = [1000 + 97 * s["id"] + 13 * (rnd * TAKES + k) for k in range(TAKES)]
            for seed in seeds:
                t = make_take(cfg, idx, seed)
                entry["takes"].append(t)
                print(f"S{s['id']} seed {seed}: wer={t['wer']} '{t['whisper']}' f0std={t['f0_std_st']} "
                      f"wps={t['wps']} lufs={t['lufs']} robot={t['robot_flag']} drift={t['max_drift']}", flush=True)
            entry["rounds"] = rnd + 1
            best = choose(cfg, idx, [t for t in entry["takes"] if s["id"] not in redo or t["seed"] in seeds])
            if best:
                entry["chosen"] = best["seed"]
                break
            print(f"S{s['id']}: kein Take ok -> neue Runde", flush=True)
        state[key] = entry
        state_p.write_text(json.dumps(state, indent=1))
    state_p.write_text(json.dumps(state, indent=1))
    for s in cfg["sentences"]:
        e = state[str(s["id"])]
        c = next((t for t in e["takes"] if t["seed"] == e.get("chosen")), None)
        print(f"S{s['id']:>2} -> {'seed ' + str(c['seed']) if c else 'KEIN TAKE'}  {c and c['whisper']}")


if __name__ == "__main__":
    if "--rechoose" in sys.argv:
        print("ohne gueltigen Take:", rechoose())
    else:
        main()
