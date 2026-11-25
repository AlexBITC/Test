"""Stimmen-Check: Whisper-Ruecktranskription, Wortfehler, Zahlen, Tempo, Tonhoehe, Clipping, Pausen.

Optional: Natuerlichkeits-Score (UTMOS22 strong ueber torch.hub, falls installierbar).
"""
from __future__ import annotations

import re
import numpy as np
import soundfile as sf

from .tts import _num_token, split_words

_WHISPER = None
_UTMOS = None
_UTMOS_ERR = None

# Dialekt/Umgangssprache: Whisper schreibt Standarddeutsch, beide Seiten werden angeglichen
# Eigennamen als Vokabelhinweis fuer Whisper (kein Satzinhalt)
NAMES = "Kalle, Byte."
# Schwaebische Woerter duerfen abweichen (zaehlen nicht als Wortfehler)
DIALECT = {"net", "nicht", "i", "ich", "des", "das", "verschlamp", "verschlampe"}
DIALECT_REF = {"net", "i", "des", "verschlamp", "kaufet", "koiner", "mei", "erschte", "gmeint", "glei", "mi",
               "gspielt", "kommet"}
DIALECT_REF_25 = {"a", "no"}       # 2.5: nur fuer Folgen mit 2.5-Merkmalen (stimme.v25), aeltere Berichte bleiben gleich
# Zahlwoerter und Pflichtbegriffe: muessen exakt erkannt werden
NUMBER_WORDS = {"null", "eins", "eine", "einen", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun",
                "zehn", "zwölf", "zwanzig", "dreißig", "fünfzig", "hundert", "tausend"}
MUST = {"code", "marketing"}
EQUIV = {"des": "das", "net": "nicht", "hab": "habe", "schick": "schicke", "schreib": "schreibe", "hol": "hole", "merk": "merke", "ah": "ha", "haha": "ha", "gibt's": "gibts",
         "eintausend": "tausend", "stop": "stopp",
         # bairische Formen (Kalle): gleiche Bedeutung wie Hochdeutsch
         "i": "ich", "mei": "mein", "behalt": "behalte", "verkauf": "verkaufe", "verlier": "verliere",
         "en": "einen", "spinnet": "spinnen", "isch": "ist", "mi": "mich", "telefonier": "telefoniere", "brauch": "brauche", "n": "einen",
         # schwaebische Formen (Folge viral)
         "koi": "kein", "hätt": "hätte", "au": "auch", "no": "noch", "a": "eine",
         # schwaebische Formen (ab 2.3)
         "kaufet": "kaufen", "koiner": "keiner",
         # 2.4: Kalle (Brezel-Geheimnis) und Umgangssprache
         "gmeint": "gemeint", "erschte": "erste", "glei": "gleich", "grad": "gerade",
         # 2.5: Kalle (Baeckerei-Spiel)
         "gspielt": "gespielt", "kommet": "kommen",}


ORDINAL = {1: "erste", 2: "zweite", 3: "dritte", 4: "vierte", 5: "fünfte", 6: "sechste", 7: "siebte", 8: "achte",
           9: "neunte", 10: "zehnte"}
ORD_ART = {"a", "eine", "ein", "einen", "die", "der", "das", "den", "dem", "zur", "zum", "am", "im"}


def whisper():
    global _WHISPER
    if _WHISPER is None:
        from faster_whisper import WhisperModel
        _WHISPER = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
    return _WHISPER


def load16k(path):
    y, sr = sf.read(str(path), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    if sr != 16000:
        import librosa
        y = librosa.resample(y, orig_sr=sr, target_sr=16000)
    return y


def normalize(text: str, mehl_is_mail_ok: bool = False) -> list:
    text = re.sub(r"(?<=[a-zäöüß])'s\b", " es", text)        # wird's / er's -> wird es / er es
    text = text.replace("€", " Euro ").replace("–", " ").replace("…", " ").replace("%", " Prozent ")
    text = re.sub(r"(?<=[A-Za-zÄÖÜäöüß])(?=\d)|(?<=\d)(?=[A-Za-zÄÖÜäöüß])", " ", text)
    out = []
    toks = text.split()
    for j, w in enumerate(toks):
        # 2.3: Ordinalzahl nach Artikel ("a 2. Filiale" -> "a zweite Filiale"), Whisper schreibt "zweite" als "2."
        if re.fullmatch(r"\d{1,2}\.", w) and 0 < j < len(toks) - 1 and toks[j - 1].lower() in ORD_ART \
                and toks[j + 1][:1].isalpha() and int(w[:-1]) in ORDINAL:
            out.append(ORDINAL[int(w[:-1])])
            continue
        core = re.sub(r"^[^\w]+|[^\w']+$", "", w)
        if not core:
            continue
        r = _num_token(core)
        if r:
            out += r[0].lower().split()
            continue
        core = core.lower().replace("-", "")
        core = EQUIV.get(core, core).replace("'", "")
        out.append(EQUIV.get(core, core))
    # "zwei euro fünfzig euro" -> doppelte Waehrung entfernen
    res = []
    for w in out:
        if w == "euro" and len(res) >= 2 and res[-2] == "euro":
            continue
        res.append(w)
    return res


def split_compounds(ref: list, hyp: list) -> list:
    """Whisper schreibt manchmal zwei Woerter zusammen ('preiseinkaufen'): wieder trennen."""
    pairs = {a + b: (a, b) for a, b in zip(ref, ref[1:])}
    out = []
    for w in hyp:
        out += list(pairs[w]) if (w in pairs and w not in ref) else [w]
    return out


def wer(ref: list, hyp: list, free=frozenset()) -> float:
    """Wortfehlerrate; Woerter aus 'free' (Dialekt) im Referenztext kosten bei Ersetzung nichts."""
    d = np.zeros((len(ref) + 1, len(hyp) + 1), dtype=int)
    d[:, 0] = np.cumsum([0] + [0 if w in free else 1 for w in ref])
    d[0, :] = np.arange(len(hyp) + 1)
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            d[i, j] = min(d[i - 1, j] + (0 if ref[i - 1] in free else 1), d[i, j - 1] + 1, d[i - 1, j - 1] + (ref[i - 1] != hyp[j - 1] and ref[i - 1] not in free))
    return d[-1, -1] / max(1, len(ref))


def _contains(seq: list, sub: list) -> bool:
    n = len(sub)
    return any(seq[i:i + n] == sub for i in range(len(seq) - n + 1))


def pitch_stats(path):
    """Median-F0 und Streuung (Halbtoene) mit pYIN auf der Original-Abtastrate (48 kHz, 85-ms-Fenster).
    Bei 16 kHz/1024 stuft pYIN kurze, kraeftige Ausrufe teils komplett als stimmlos ein."""
    import librosa
    y, sr = sf.read(str(path), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    f0, vf, _ = librosa.pyin(y, fmin=65, fmax=400, sr=sr, frame_length=4096)
    f = f0[~np.isnan(f0)]
    if len(f) < 8:
        return 0.0, 0.0
    med = float(np.median(f))
    st = 12 * np.log2(f / med)
    return med, float(np.std(st))


def utmos(y16):
    """UTMOS22 (SpeechMOS) – liefert None, wenn nicht verfuegbar."""
    global _UTMOS, _UTMOS_ERR
    if _UTMOS_ERR:
        return None
    try:
        if _UTMOS is None:
            import torch
            _UTMOS = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True)  # benoetigt GitHub-Zugriff
        import torch
        with torch.no_grad():
            return float(_UTMOS(torch.from_numpy(y16).unsqueeze(0), 16000).item())
    except Exception as e:  # noqa: BLE001
        _UTMOS_ERR = f"{type(e).__name__}: {str(e)[:120]}"
        return None


def check_line(wav_path, text: str, words: list, begriff: str | None, speaker: str, n_words: int | None = None,
               tempo=(2.0, 2.8), pause_limit: float = 0.7, dialekt_extra=()) -> dict:
    """words: [{'w','start','end'}] aus den API-Zeitstempeln."""
    y16 = load16k(wav_path)
    raw, sr = sf.read(str(wav_path), dtype="float32")
    dur = len(raw) / sr
    segs, _ = whisper().transcribe(y16, language="de", beam_size=5, vad_filter=False,
                                   condition_on_previous_text=False, initial_prompt=NAMES)
    hyp_text = " ".join(s.text.strip() for s in segs).strip()
    ref_n = normalize(text)
    hyp_n = split_compounds(ref_n, normalize(hyp_text))
    raw_ref = [re.sub(r"^[^\w]+|[^\w']+$", "", w).lower() for w in split_words(text)]
    free = frozenset(EQUIV.get(w, w) for w in raw_ref if w in DIALECT_REF or w in dialekt_extra)
    w_err = wer(ref_n, hyp_n, free)

    # Zahlen und Fachbegriff exakt
    exact = []
    for w in split_words(text):
        core = re.sub(r"^[^\w]+|[^\w]+$", "", w)
        if _num_token(core):
            sub = normalize(core)
            exact.append((core, _contains(hyp_n, sub)))
    for w in raw_ref:
        if w in NUMBER_WORDS:
            exact.append((w, w in hyp_n))
        elif w in MUST and begriff and w != begriff.lower():
            exact.append((w, w in hyp_n))
    if begriff and begriff.lower() in text.lower():
        if " " in begriff.strip():                 # 2.4: Begriff aus mehreren Woertern als Wortfolge pruefen
            exact.append((begriff, _contains(hyp_n, normalize(begriff))))
        else:
            exact.append((begriff, begriff.lower() in hyp_n))

    # Tempo: Woerter pro Sekunde ueber die gesprochene Spanne
    spoken = [w for w in words if re.search(r"\w", w["w"]) and w["end"] > w["start"]]
    if n_words is None:
        n_words = len([w for w in split_words(text) if re.search(r"\w", w)])
    span = (spoken[-1]["end"] - spoken[0]["start"]) if spoken else dur
    wps = n_words / max(0.1, span)

    # Pausen mitten in der Zeile (zwischen Woertern)
    gaps = []
    for a, b in zip(spoken, spoken[1:]):
        gaps.append((b["start"] - a["end"], a["w"]))
    max_gap = max(gaps, default=(0.0, ""))
    gap_limit = lambda after: (1.0 if after.endswith("…") or after == "…" else 0.7) if pause_limit >= 0.7 \
        else pause_limit  # noqa: E731
    long_pauses = [(round(g, 2), w) for g, w in gaps if g > gap_limit(w)]
    if pause_limit < 0.7:
        # Pausen am Signal messen (laengste Stille zwischen erstem und letztem Laut, -30 dB): Whisper-Wortgrenzen
        # sind bei Piper-Stimmen um 0,2-0,4 s ungenau.
        hop = int(0.01 * sr)
        rr = np.array([np.sqrt(np.mean(raw[i:i + hop] ** 2)) for i in range(0, len(raw), hop)])
        loud = np.nonzero(rr > rr.max() * 10 ** (-30 / 20))[0]
        run = best = 0
        for v_ in (rr[loud[0]:loud[-1]] <= rr.max() * 10 ** (-30 / 20)) if len(loud) else []:
            run = run + 1 if v_ else 0
            best = max(best, run)
        sig_gap = best * 0.01
        max_gap = (sig_gap, "Signal")
        long_pauses = [(round(sig_gap, 2), "Signal")] if sig_gap > pause_limit else []

    # Clipping / abgeschnitten
    peak = float(np.max(np.abs(raw))) if len(raw) else 0.0
    clip_frac = float(np.mean(np.abs(raw) >= 0.995))
    tail = raw[-int(0.03 * sr):]
    tail_db = 20 * np.log10(np.sqrt(np.mean(tail ** 2)) + 1e-9) if len(tail) else -99
    rms_db = 20 * np.log10(np.sqrt(np.mean(raw ** 2)) + 1e-9)
    # Ende abgeschnitten: nur ueber den Pegel (letzte 30 ms gegen den Zeilen-Durchschnitt). Der Whisper-
    # Zeitstempel des letzten Worts reicht bei knapp geschnittenem Ausklang (<= 0,08 s) fast immer bis zum Dateiende.
    cut = (tail_db - rms_db) > -12

    med, st = pitch_stats(wav_path)
    mos = utmos(y16)

    fails = []
    if w_err > 0.10:
        fails.append(f"WER {w_err:.0%} > 10 %")
    for core, ok in exact:
        if not ok:
            fails.append(f"'{core}' nicht exakt erkannt")
    if not (tempo[0] <= wps <= tempo[1]):
        fails.append(f"Tempo {wps:.2f} W/s ausserhalb {tempo[0]:.1f}–{tempo[1]:.1f}".replace(".", ","))
    if st < 1.5:
        fails.append(f"monoton (Tonhoehen-Streuung {st:.1f} Halbtoene)")
    if clip_frac > 0.001:
        fails.append(f"Uebersteuerung ({clip_frac:.2%} Samples am Limit)")
    if cut:
        fails.append("Ende wirkt abgeschnitten")
    if long_pauses:
        fails.append(f"lange Pause(n) {long_pauses}")
    if mos is not None and mos < 3.5:  # pragma: no branch
        fails.append(f"UTMOS {mos:.2f} < 3,5")
    return {"speaker": speaker, "text": text, "transcript": hyp_text, "wer": w_err, "exact": exact,
            "wps": wps, "dur": dur, "f0_median": med, "f0_std_st": st, "peak": peak,
            "clip_frac": clip_frac, "max_gap": max_gap[0], "long_pauses": long_pauses, "cut": bool(cut),
            "utmos": mos, "fails": fails, "ok": not fails}


def utmos_status():
    return _UTMOS_ERR
