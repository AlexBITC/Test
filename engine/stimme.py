"""Natuerlichere Stimme (Engine 2.3): Felder 'ton', 'betonung', 'tempo', 'sprechtext' pro Szene.

Nur Szenen mit mindestens einem dieser Felder laufen hier durch; alle anderen Zeilen (und damit alle
bisherigen Folgen) werden unveraendert von render.voices_stage erzeugt.

- ton       -> Stimm-Einstellungen (stability/style); similarity_boost bleibt aus engine/voices.json
- betonung  -> Satzform: kleine Pause davor (Komma), falls das Wort nicht schon am Satzende steht
- tempo     -> Zielbereich in Woertern/s ueber den ElevenLabs-Parameter 'speed'
- sprechtext-> Schreibweise nur fuer die Sprachausgabe; Zahlen darin werden immer als Woerter ausgeschrieben
Erweiterter Check (pro Zeile): Wortfehler, Zahlen/Begriff exakt, Spannweite der Satzmelodie >= 4 Halbtoene,
Frage steigt / Aussage faellt, Betonung (+2 dB oder +1,5 Halbtoene), Tempo im Zielbereich, kein Uebersteuern,
keine Pause > 0,6 s mitten im Satz (ausser nach '…'). Hoechstens 3 Versuche; eleven_v3 als Vergleich.
"""
from __future__ import annotations

import difflib
import re

import numpy as np

from . import tts, voicecheck

TON = {"begeistert": (0.30, 0.50), "ruhig": (0.60, 0.15), "nachdenklich": (0.55, 0.25), "neugierig": (0.40, 0.35),
       "verschmitzt": (0.35, 0.45), "ueberzeugt": (0.45, 0.35), "fragend": (0.40, 0.30),
       # 2.4: feinere Gefuehle
       "genervt": (0.35, 0.45), "enttaeuscht": (0.60, 0.20), "geruehrt": (0.65, 0.20), "stolz": (0.45, 0.35)}
TEMPO = {"langsam": (2.0, 2.2), "normal": (2.3, 2.6), "schnell": (2.6, 2.9)}
SPEED0 = {"langsam": 0.84, "normal": 0.92, "schnell": 1.0}
V3_TAG = {"begeistert": "[excited]", "ruhig": "[calm]", "nachdenklich": "[thoughtful]", "neugierig": "[curious]",
          "verschmitzt": "[playful]", "ueberzeugt": "[confident]", "fragend": "[curious]",
          "genervt": "[annoyed]", "enttaeuscht": "[sad]", "geruehrt": "[softly]", "stolz": "[proud]"}
FELDER = ("ton", "betonung", "tempo", "sprechtext")
TON_24 = ("genervt", "enttaeuscht", "geruehrt", "stolz")


def v24(ep: dict) -> bool:
    """Folge nutzt Merkmale ab Engine 2.4 (Lea, Musikbett, neue Toene oder 'geruehrt'): dann bleiben Atmer erhalten.
    Folgen bis 2.3 klingen dadurch unveraendert."""
    return any(sz.get("sprecher") == "lea" or sz.get("musik") or sz.get("ton") in TON_24 or sz.get("reaktion") == "geruehrt"
               for sz in ep.get("szenen", []))


def hat_felder(sz: dict) -> bool:
    return any(k in sz for k in FELDER)


def _core(w: str) -> str:
    return re.sub(r"^[^\w]+|[^\w]+$", "", w).lower()


def zahlen_als_woerter(s: str) -> str:
    """'8.000' -> 'achttausend', '240' -> 'zweihundertvierzig', '3 %' -> 'drei Prozent'."""
    def rep(m):
        n = int(m.group(1).replace(".", ""))
        return tts.zahl_de(n)
    s = re.sub(r"(\d+)\s*%", lambda m: tts.zahl_de(int(m.group(1))) + " Prozent", s)
    return re.sub(r"(?<![\w,])(\d{1,3}(?:\.\d{3})+|\d+)(?![\w,])", rep, s)


def _norm_tok(w: str) -> str:
    c = _core(w)
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+|\d+", c):
        c = tts.zahl_de(int(c.replace(".", "")))
    return c


def mapping(text: str, speech: str):
    """Untertitel-Woerter (text) auf den Sprechtext abbilden: (speech, spans) wie tts.speech_mapping."""
    tw = tts.split_words(text)
    sw = [w for w in speech.split() if w]
    pos, starts = 0, []
    for w in sw:
        i = speech.index(w, pos)
        starts.append((i, i + len(w)))
        pos = i + len(w)
    a = [_norm_tok(w) for w in tw]
    b_idx = [k for k, w in enumerate(sw) if _norm_tok(w)]           # '…' allein zaehlt nicht als Wort
    b = [_norm_tok(sw[k]) for k in b_idx]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    spans = [None] * len(tw)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for d in range(i2 - i1):
                k = b_idx[j1 + d]
                spans[i1 + d] = (tw[i1 + d], starts[k][0], starts[k][1])
        elif tag in ("replace", "delete"):
            if j2 > j1:
                s0, s1 = starts[b_idx[j1]][0], starts[b_idx[j2 - 1]][1]
                n = i2 - i1
                if n == j2 - j1:
                    for d in range(n):
                        k = b_idx[j1 + d]
                        spans[i1 + d] = (tw[i1 + d], starts[k][0], starts[k][1])
                else:
                    spans[i1] = (tw[i1], s0, s1)
                    for d in range(1, n):
                        spans[i1 + d] = (tw[i1 + d], s1, s1)
    last = 0
    for k, sp in enumerate(spans):
        if sp is None:
            spans[k] = (tw[k], last, last)
        else:
            last = sp[2]
    return speech, spans


def betonung_formen(speech: str, wort: str | None) -> str:
    """Kleine Pause vor dem Betonungswort, falls es nicht ohnehin am Satzende steht oder schon eine Pause hat."""
    if not wort:
        return speech
    toks = speech.split()
    for k, t in enumerate(toks):
        if _core(t) == _norm_tok(wort):
            satzende = bool(re.search(r"[.!?]$", t)) or (k + 1 < len(toks) and toks[k + 1] in ("…",)) or k == len(toks) - 1
            davor = k > 0 and (toks[k - 1].endswith((",", "…", ":")) or toks[k - 1] == "…")
            if satzende or davor:
                return speech
            if k == 0:
                return speech
            toks[k - 1] = toks[k - 1] + ","          # kleine Pause (Komma) vor dem Betonungswort
            return " ".join(toks)
    return speech


# ------------------------------------------------------------------ Messungen
def _f0(wav):
    import librosa
    y, sr = librosa.load(str(wav), sr=16000)
    f0, vflag, _ = librosa.pyin(y, fmin=60, fmax=450, sr=sr, frame_length=1024, hop_length=160)
    t = np.arange(len(f0)) * 160 / sr
    return y, sr, f0, t


def messen(wav, words, sz: dict, speech: str, spans=None) -> dict:
    """Satzmelodie, Frage/Aussage, Betonung, Pausen, Pegel."""
    y, sr, f0, t = _f0(wav)
    v = ~np.isnan(f0)
    st = 12 * np.log2(f0[v] / np.median(f0[v])) if v.any() else np.array([0.0])
    spann = float(np.percentile(st, 95) - np.percentile(st, 5)) if len(st) > 10 else 0.0
    spoken = [w for w in words if re.search(r"\w", w["w"]) and w["end"] > w["start"]]
    # Melodie am Satzende: letztes Wort gegen den Rest der Zeile
    ende = None
    if spoken:
        w_last = spoken[-1]
        m_end = v & (t >= w_last["start"]) & (t <= w_last["end"] + 0.05)
        m_rest = v & (t < w_last["start"])
        if m_end.sum() > 3 and m_rest.sum() > 3:
            fe = f0[m_end]
            ende = float(12 * np.log2(np.median(fe[len(fe) // 2:]) / np.median(f0[m_rest])))
    frage = sz["text"].rstrip().endswith("?")
    # Betonung: Wort gegen den Durchschnitt aller Woerter der Zeile. Je Wort: Spitzenpegel (95. Perzentil der
    # 10-ms-Pegel in dB) und Tonhoehe (90. Perzentil der F0). Ziel: >= +2 dB oder >= +1,5 Halbtoene.
    beto = None
    if sz.get("betonung") and spoken:
        hop = 160
        rms = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2)) + 1e-9 for i in range(0, len(y), hop)])
        tr = np.arange(len(rms)) * hop / sr
        db = 20 * np.log10(rms)

        def wert(w):
            mw = (tr >= w["start"]) & (tr <= w["end"])
            mf = v & (t >= w["start"]) & (t <= w["end"])
            pdb = float(np.percentile(db[mw], 95)) if mw.any() else None
            pf = float(np.percentile(f0[mf], 90)) if mf.sum() >= 2 else None
            return pdb, pf
        target = _norm_tok(sz["betonung"])
        ww = next((w for w in spoken if _norm_tok(w["w"]) == target), None) or \
            next((w for w in spoken if target in _norm_tok(w["w"])), None)
        if ww:
            alle = [wert(w) for w in spoken]
            wdb, wf = wert(ww)
            dbs = [x for x, _ in alle if x is not None]
            fs = [y_ for _, y_ in alle if y_ is not None]
            d_db = float(wdb - np.mean(dbs)) if wdb is not None and dbs else 0.0
            d_st = float(12 * np.log2(wf / np.mean(fs))) if wf is not None and fs else 0.0
            beto = {"wort": ww["w"], "db": d_db, "st": d_st, "ok": d_db >= 2.0 or d_st >= 1.5}
    # Pausen mitten im Satz (ueber 0,6 s nur nach '…' oder Satzende erlaubt)
    pausen = []
    gespr = [(w, sp) for w, sp in zip(words, spans or []) if re.search(r"\w", w["w"]) and sp[2] > sp[1]]
    for (a, sa), (b, sb) in zip(gespr, gespr[1:]):
        g = b["start"] - a["end"]
        zwischen = speech[sa[2]:sb[1]]
        if g > 0.6 and "…" not in zwischen and not re.search(r"[.!?]", zwischen):
            pausen.append(round(g, 2))
    peak = float(np.max(np.abs(y))) if len(y) else 0.0
    return {"f0_median": float(np.median(f0[v])) if v.any() else 0.0, "spannweite": spann, "ende_st": ende,
            "frage": frage, "betonung": beto, "pausen": pausen, "peak": peak}


def bewerten(chk: dict, mm: dict, sz: dict) -> list:
    """Liste der nicht erfuellten Kriterien."""
    fails = [f for f in chk["fails"] if not f.startswith("Tempo") and not f.startswith("lange Pause")
             and not f.startswith("monoton")]
    lo, hi = TEMPO.get(sz.get("tempo", "normal"), TEMPO["normal"])
    if not (lo - 0.05 <= chk["wps"] <= hi + 0.05):
        fails.append(f"Tempo {chk['wps']:.2f} W/s ausserhalb {lo:.1f}–{hi:.1f}".replace(".", ","))
    if mm["spannweite"] < 4.0:
        fails.append(f"monoton (Spannweite {mm['spannweite']:.1f} Halbtoene < 4)".replace(".", ","))
    if mm["ende_st"] is not None and not sz["text"].rstrip().endswith("…"):
        if mm["frage"] and mm["ende_st"] < 0.5:
            fails.append(f"Frage steigt nicht ({mm['ende_st']:+.1f} Halbtoene am Ende)".replace(".", ","))
        if not mm["frage"] and mm["ende_st"] > 1.0:
            fails.append(f"Aussage faellt nicht ({mm['ende_st']:+.1f} Halbtoene am Ende)".replace(".", ","))
    if mm["betonung"] is not None and not mm["betonung"]["ok"]:
        b = mm["betonung"]
        fails.append(f"Betonung '{b['wort']}' schwach ({b['db']:+.1f} dB, {b['st']:+.1f} Halbtoene)".replace(".", ","))
    if mm["pausen"]:
        fails.append(f"Pause mitten im Satz {mm['pausen']}")
    return fails


def _score(fails, chk, mm, sz):
    lo, hi = TEMPO.get(sz.get("tempo", "normal"), TEMPO["normal"])
    dev = max(0.0, lo - chk["wps"], chk["wps"] - hi)
    # Schwere statt nur Anzahl: jede Abweichung zaehlt 1, Tempo zusaetzlich nach Groesse (0,5 W/s = 1 Fehler),
    # Wortfehler nach Groesse (10 % = 1 Fehler)
    return (len(fails) + 2.0 * dev + 10.0 * chk["wer"], -mm["spannweite"])


# ------------------------------------------------------------------ Atmer (2.4)
def _atmer(meta):
    """Atmer vor dem ersten Wort finden (Pegel > -50 dB unter der Spitze, 0,12-0,9 s lang, direkt vor dem Wort).
    Rueckgabe: (lead fuer tts.tighten, Laenge des Atmers in s oder 0). Ohne Atmer: Standard-lead 0,04 s."""
    import soundfile as sf
    y, sr = sf.read(str(tts.ROOT / meta["wav"]), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    off = (len(meta["tag"]) + 1) if meta.get("tag") else 0
    chars, st = meta["chars"], meta["starts"]
    first = next((i for i in range(off, len(chars)) if chars[i].isalnum()), None)
    if first is None or not len(y):
        return 0.04, 0.0
    w0 = st[first]
    hop = int(0.01 * sr)
    rms = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2)) for i in range(0, len(y), hop)]) + 1e-9
    db = 20 * np.log10(rms / rms.max())
    loud36 = np.nonzero(db > -36)[0]
    first_loud = loud36[0] * 0.01 if len(loud36) else w0
    i = int(w0 / 0.01) - 1
    j = i
    while j > 0 and db[j] > -50:
        j -= 1
    dauer = w0 - j * 0.01
    if 0.12 <= dauer <= 0.9:
        return max(0.04, first_loud - j * 0.01 + 0.03), dauer
    return 0.04, 0.0


def _atmer_daempfen(meta, dauer, grenze=-14.0):
    """Atmer bleibt erhalten; nur ein lauter, stoerender Atmer (Pegel > grenze dB unter der Sprache) wird bis auf
    die Grenze gedaempft. Rueckgabe: Daempfung in dB (0 = unveraendert)."""
    import soundfile as sf
    p = tts.ROOT / meta["wav"]
    y, sr = sf.read(str(p), dtype="float32")
    off = (len(meta["tag"]) + 1) if meta.get("tag") else 0
    first = next((i for i in range(off, len(meta["chars"])) if meta["chars"][i].isalnum()), None)
    w0 = meta["starts"][first] if first is not None else 0.0
    n = int(max(0.0, w0 - 0.02) * sr)
    if n < int(0.08 * sr):
        return 0.0
    b = y[:n]
    s_ = y[n:]
    lb = 20 * np.log10(np.sqrt(np.mean(b ** 2)) + 1e-9)
    ls = 20 * np.log10(np.sqrt(np.mean(s_ ** 2)) + 1e-9)
    ueber = (lb - ls) - grenze
    if ueber <= 0:
        return 0.0
    g = 10 ** (-ueber / 20)
    ramp = np.ones(n, np.float32) * g
    k = min(n, int(0.03 * sr))
    ramp[-k:] = np.linspace(g, 1.0, k)
    y[:n] = b * ramp
    sf.write(str(p), y, sr, subtype="PCM_16")
    return round(float(ueber), 1)


# ------------------------------------------------------------------ Erzeugen
def _erzeuge(sz, ep, role, vid, model, settings, tag, seed, sp_text, spans, pitch=0.0):  # noqa: C901
    """Synthese, Stille kuerzen, Tempo-Rest tonhoehenerhaltend korrigieren (atempo, hoechstens tts.STRETCH_LIMIT),
    dann Whisper-Check und Messungen."""
    lo, hi = TEMPO.get(sz.get("tempo", "normal"), TEMPO["normal"])
    meta0 = tts.synth(sp_text, vid, model, settings, tag, seed=seed)
    lead, atem = _atmer(meta0) if v24(ep) else (0.04, 0.0)
    meta = tts.tighten(meta0, lead=lead)
    if atem:
        meta["atmer"] = _atmer_daempfen(meta, atem)
    raw = tts.word_times(meta, spans)
    sp = [w for w in raw if re.search(r"\w", w["w"]) and w["end"] > w["start"]]
    n_w = len([w for w in tts.split_words(sz["text"]) if re.search(r"\w", w)])
    wps0 = n_w / max(0.1, sp[-1]["end"] - sp[0]["start"]) if sp else (lo + hi) / 2
    factor = 1.0
    if wps0 > hi:
        factor = max(tts.STRETCH_LIMIT[0], (hi - 0.04) / wps0)
    elif wps0 < lo:
        factor = min(tts.STRETCH_LIMIT[1], (lo + 0.04) / wps0)
    meta = tts.stretch(meta, round(factor, 3), pitch)
    words = tts.word_times(meta, spans)
    chk = voicecheck.check_line(tts.ROOT / meta["wav"], sz["text"], words, ep.get("begriff"), role)
    chk["stretch"] = factor
    chk["wps_raw"] = wps0
    mm = messen(tts.ROOT / meta["wav"], words, sz, sp_text, spans)
    return meta, words, chk, mm, bewerten(chk, mm, sz)


def zeile(i: int, sz: dict, ep: dict, cfg: dict, model: str, log, v3_test: bool = True) -> dict:
    """Erzeugt eine Zeile mit den neuen Feldern (hoechstens 3 Versuche) und optional eine eleven_v3-Variante."""
    role = sz["sprecher"]
    vid = cfg["voices"][role]["voice_id"]
    ton = sz.get("ton")
    tempo = sz.get("tempo", "normal")
    lo, hi = TEMPO.get(tempo, TEMPO["normal"])
    base = dict(tts.BASE_SETTINGS[role])
    base.update(cfg.get("settings", {}).get(role, {}))
    stab, style = TON.get(ton, (base["stability"], base["style"]))
    speech0 = zahlen_als_woerter(sz.get("sprechtext") or sz["text"])
    tune = cfg.get("line_tuning", {}).get(ep["slug"], {}).get(str(i + 1), {})
    speed = tune.get("speed", SPEED0.get(tempo, 0.92))
    attempts = []
    speech = speech0
    for att in range(3):
        settings = {"stability": round(stab, 2), "similarity_boost": base["similarity_boost"], "style": round(style, 2),
                    "use_speaker_boost": True, "speed": round(speed, 2)}
        seed = tune.get("seed", 5300 + 31 * att + 7 * i)
        sp_text, spans = mapping(sz["text"], speech)
        meta, words, chk, mm, fails = _erzeuge(sz, ep, role, vid, model, settings, "", seed, sp_text, spans)
        a = {"meta": meta, "words": words, "check": chk, "mess": mm, "fails": fails, "settings": settings, "seed": seed,
             "speech": sp_text, "model": model, "versuch": att + 1}
        attempts.append(a)
        log(f"Szene {i+1} Versuch {att+1} ({model}): {'OK' if not fails else 'FAIL'} WER={chk['wer']:.0%} "
            f"{chk['wps']:.2f}W/s (roh {chk['wps_raw']:.2f}, x{chk['stretch']:.2f}) Spannweite={mm['spannweite']:.1f}st Ende={mm['ende_st']} "
            f"Betonung={mm['betonung']} | {chk['transcript']} | {fails}")
        if not fails:
            break
        # naechster Versuch: Tempo nachregeln, Satzform fuer Betonung, mehr Ausdruck bei monotonem Klang
        if any(f.startswith("Tempo") for f in fails):
            neu = max(0.7, min(1.2, speed * ((lo + hi) / 2) / max(0.5, chk["wps_raw"])))
            if chk["wps"] > hi and speed <= 0.71:       # 'speed' am Anschlag: Satzform (Komma vor dem Betonungswort)
                speech = betonung_formen(speech, sz.get("betonung"))
            speed = neu
        if any(f.startswith("Betonung") for f in fails):
            speech = betonung_formen(speech, sz.get("betonung"))
        if any(f.startswith("monoton") or f.startswith("Frage") for f in fails):
            stab, style = max(0.25, stab - 0.08), min(0.7, style + 0.1)
        if any(f.startswith("Pause") for f in fails):
            speech = speech.replace(" … ", ", ")
    best = min(attempts, key=lambda a: _score(a["fails"], a["check"], a["mess"], sz))
    v3 = None
    if v3_test and ton:
        try:
            tag = V3_TAG.get(ton, "")
            s3 = {"stability": 0.5, "similarity_boost": base["similarity_boost"], "style": round(style, 2),
                  "use_speaker_boost": True}
            sp_text, spans = mapping(sz["text"], best["speech"])
            meta, words, chk, mm, fails = _erzeuge(sz, ep, role, vid, "eleven_v3", s3, tag, best["seed"], sp_text, spans)
            v3 = {"meta": meta, "words": words, "check": chk, "mess": mm, "fails": fails, "settings": s3,
                  "seed": best["seed"], "speech": sp_text, "model": "eleven_v3", "versuch": "v3", "tag": tag}
            log(f"Szene {i+1} eleven_v3: {'OK' if not fails else 'FAIL'} WER={chk['wer']:.0%} {chk['wps']:.2f}W/s "
                f"Spannweite={mm['spannweite']:.1f}st | {chk['transcript']} | {fails}")
        except Exception as e:  # noqa: BLE001
            log(f"Szene {i+1} eleven_v3 nicht moeglich: {str(e)[:160]}")
    gewaehlt = best
    if v3 is not None and _score(v3["fails"], v3["check"], v3["mess"], sz) < _score(best["fails"], best["check"], best["mess"], sz):
        gewaehlt = v3
    gewaehlt = dict(gewaehlt)
    gewaehlt["alle"] = attempts + ([v3] if v3 else [])
    gewaehlt["v2_best"] = best
    gewaehlt["v3"] = v3
    gewaehlt["n_attempts"] = len(attempts)
    return gewaehlt


# ------------------------------------------------------------------ Bericht
def _klangfarbe(wavs):
    """Mittlere MFCC (2-20) ueber die stimmhaften Abschnitte mehrerer Zeilen (Klangfarbe, ohne Lautstaerke)."""
    import librosa
    acc = []
    for w in wavs:
        y, sr = librosa.load(str(tts.ROOT / w), sr=16000)
        mf = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        rms = librosa.feature.rms(y=y)[0]
        keep = rms > rms.max() * 0.1
        acc.append(mf[1:, keep[:mf.shape[1]]].mean(axis=1))
    return np.mean(acc, axis=0)


def pegel_db(wav):
    """Pegel der gesprochenen Abschnitte (RMS der 10-ms-Fenster ueber -40 dB unter der Spitze) in dBFS."""
    import soundfile as sf
    y, sr = sf.read(str(tts.ROOT / wav), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    hop = int(0.01 * sr)
    r = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2)) for i in range(0, len(y) - hop, hop)]) + 1e-9
    act = r[r > r.max() * 10 ** (-40 / 20)]
    return float(20 * np.log10(np.sqrt(np.mean(act ** 2))))


def pegel_anwenden(line, db):
    """Zeile leiser/lauter abmischen (Regie 'pegel_db'): neue Datei <wav>_g<db>.wav, Wort-Timing bleibt."""
    import soundfile as sf
    src = tts.ROOT / line["meta"]["wav"]
    dst = src.with_name(f"{src.stem}_g{db:+.1f}.wav".replace("+", "p").replace("-", "m"))
    y, sr = sf.read(str(src), dtype="float32")
    sf.write(str(dst), np.clip(y * 10 ** (db / 20), -1, 1), sr, subtype="PCM_16")
    line["meta"] = dict(line["meta"], wav=str(dst.relative_to(tts.ROOT)))
    line["pegel_db"] = db
    return line


def zuruecknahme(ep, lines, regie):
    """Zusatz-Check aus der Regie: {'zeilen': [..], 'db': -3, 'wps_max': 2.2} -> Liste (zeile, dB rel., W/s, ok)."""
    z = regie.get("zuruecknahme")
    if not z:
        return None
    pegel = [pegel_db(l["meta"]["wav"]) for l in lines]
    mittel = float(np.mean(pegel))
    out = []
    for n in z["zeilen"]:
        l = lines[n - 1]
        rel = pegel[n - 1] - mittel
        wps = l["check"]["wps"]
        out.append((n, rel, wps, rel <= z.get("db", -3.0) and wps < z.get("wps_max", 2.2)))
    return {"mittel": mittel, "zeilen": out, "db": z.get("db", -3.0), "wps_max": z.get("wps_max", 2.2)}


def bericht(ep: dict, lines: list, path, log=print, regie=None):
    f0 = {}
    for sz, l in zip(ep["szenen"], lines):
        if l.get("mess"):
            f0.setdefault(sz["sprecher"], []).append(l["mess"]["f0_median"])
    abstand = None
    if "kalle" in f0 and "byte" in f0:
        abstand = 12 * np.log2(np.median(f0["byte"]) / np.median(f0["kalle"]))
    n_v3 = sum(1 for l in lines if l.get("model") == "eleven_v3")
    n_v3_test = sum(1 for l in lines if l.get("v3"))
    r = [f"# Stimmen-Check: {ep['titel']}", "",
         "Erweiterter Check (Engine 2.3) für Zeilen mit `ton`/`betonung`/`tempo`/`sprechtext`. Stimmen: ElevenLabs, "
         "Kalle = Brian, Byte = Laura, Lea = Sarah (ab 2.4). Atmer am Satzanfang bleiben erhalten (laute werden gedämpft). Kriterien: Wortfehler ≤ 10 % (schwäbische Wörter frei), Zahlen und Begriff exakt, "
         "Spannweite der Satzmelodie ≥ 4 Halbtöne (5.–95. Perzentil), Frage steigt / Aussage fällt (letztes Wort gegen "
         "den Rest der Zeile), Betonungswort ≥ +2 dB oder ≥ +1,5 Halbtöne gegenüber dem Durchschnitt aller Wörter der "
         "Zeile (je Wort Spitzenpegel = 95. Perzentil, Tonhöhe = 90. Perzentil), Tempo im "
         "Zielbereich, kein Übersteuern, keine Pause > 0,6 s mitten im Satz (außer nach „…“). Höchstens 3 Versuche. Tempo: "
         "zuerst ElevenLabs `speed` (0,7–1,2), am Anschlag zusätzlich Satzform (Komma), Rest tonhöhenerhaltend per "
         "`atempo` (höchstens −12 % / +15 %, Spalte Tempo-Korrektur).", "",
         "| # | Sprecher | ton / tempo | Modell | Versuche | WER | W/s (Ziel), Tempo-Korrektur | F0 | Spannweite | Ende | Betonung | Peak | Status |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, (sz, l) in enumerate(zip(ep["szenen"], lines)):
        if not l.get("mess"):
            r.append(f"| {k+1} | {sz['sprecher']} | – | {l.get('model', 'v2')} | {l.get('n_attempts', 1)} | "
                     f"{l['check']['wer']:.0%} | {l['check']['wps']:.2f} | {l['check']['f0_median']:.0f} Hz | – | – | – | – | "
                     f"{'OK' if l['check']['ok'] else 'FAIL'} |")
            continue
        mm, c = l["mess"], l["check"]
        lo, hi = TEMPO.get(sz.get("tempo", "normal"), TEMPO["normal"])
        b = mm["betonung"]
        D = lambda x, fm: format(x, fm).replace(".", ",")  # noqa: E731
        bt = f"„{b['wort'].strip('.,!?…')}“ {D(b['db'], '+.1f')} dB / {D(b['st'], '+.1f')} HT" if b else "–"
        ende = f"{D(mm['ende_st'], '+.1f')} HT ({'Frage' if mm['frage'] else 'Aussage'})" if mm["ende_st"] is not None else "–"
        st = "OK" if not l["fails"] else "FAIL: " + "; ".join(l["fails"])
        r.append(f"| {k+1} | {sz['sprecher']} | {sz.get('ton', '–')} / {sz.get('tempo', 'normal')} | {l['model']} | "
                 f"{l['n_attempts']} | {c['wer']:.0%} | {D(c['wps'], '.2f')} ({D(lo, '.1f')}–{D(hi, '.1f')}), "
                 f"x{D(c.get('stretch', 1.0), '.2f')} | {mm['f0_median']:.0f} Hz | "
                 f"{D(mm['spannweite'], '.1f')} HT | {ende} | {bt} | {D(c['peak'], '.2f')} | {st} |".replace("HT", "Halbtöne"))
    r += [""]
    if abstand is not None:
        r.append(f"Kalle und Byte: mittlere Tonhöhe {np.median(f0['kalle']):.0f} Hz gegen {np.median(f0['byte']):.0f} Hz, "
                 f"Abstand {abstand:.1f} Halbtöne → {'✓ klar unterscheidbar' if abstand >= 4 else '✗ zu ähnlich'} (Ziel ≥ 4).")
    if "lea" in f0:                                       # 2.4: Lea gegen Kalle (Tonhoehe) und Byte (Klangfarbe)
        r.append("")
        if "kalle" in f0:
            a_k = 12 * np.log2(np.median(f0["lea"]) / np.median(f0["kalle"]))
            r.append(f"Lea und Kalle: {np.median(f0['lea']):.0f} Hz gegen {np.median(f0['kalle']):.0f} Hz, Lea liegt "
                     f"{a_k:.1f} Halbtöne höher → {'✓' if a_k >= 4 else '✗'} (Ziel ≥ 4).".replace(".", ",", 1))
        if "byte" in f0:
            wl = [l["meta"]["wav"] for sz, l in zip(ep["szenen"], lines) if sz["sprecher"] == "lea"]
            wb = [l["meta"]["wav"] for sz, l in zip(ep["szenen"], lines) if sz["sprecher"] == "byte"]
            wk = [l["meta"]["wav"] for sz, l in zip(ep["szenen"], lines) if sz["sprecher"] == "kalle"]
            cl, cb = _klangfarbe(wl), _klangfarbe(wb)
            d_lb = float(np.linalg.norm(cl - cb))
            d_kb = float(np.linalg.norm(_klangfarbe(wk) - cb)) if wk else None
            a_b = 12 * np.log2(np.median(f0["lea"]) / np.median(f0["byte"]))
            r.append(f"Lea und Byte: Tonhöhe {np.median(f0['lea']):.0f} Hz gegen {np.median(f0['byte']):.0f} Hz "
                     f"({a_b:+.1f} Halbtöne); Klangfarbe (Abstand der mittleren MFCC 2–20): {d_lb:.1f}"
                     + (f", zum Vergleich Kalle–Byte {d_kb:.1f}" if d_kb else "")
                     + f" → {'✓ klar unterscheidbar (Klangfarbe)' if d_lb >= 25 else '✗ Klangfarbe zu ähnlich'} (Ziel ≥ 25).")
    zr = zuruecknahme(ep, lines, regie or {})
    if zr:
        r += ["", "## Zurücknahme (Zusatz-Check dieser Folge)", "",
              f"Zeilen müssen mindestens {abs(zr['db']):.0f} dB leiser als der Durchschnitt der Folge "
              f"({zr['mittel']:.1f} dBFS, gesprochene Abschnitte) und langsamer als {zr['wps_max']:.1f} Wörter/s sein.".replace(".", ","),
              "", "| # | Sprecher | Pegel gegen Durchschnitt | W/s | Abmischung | Status |", "|---|---|---|---|---|---|"]
        for n, rel, wps, ok in zr["zeilen"]:
            l = lines[n - 1]
            r.append(f"| {n} | {ep['szenen'][n - 1]['sprecher']} | {rel:+.1f} dB | {wps:.2f} | "
                     f"{('%+.1f dB' % l['pegel_db']) if l.get('pegel_db') else '–'} | {'OK' if ok else 'FAIL'} |".replace(".", ","))
    r += ["", "## Sprechtext und Versuche", ""]
    for k, (sz, l) in enumerate(zip(ep["szenen"], lines)):
        if not l.get("alle"):
            continue
        r.append(f"**{k+1}. {sz['sprecher']}:** „{sz['text']}“  ")
        for a in l["alle"]:
            mark = " ← gewählt" if a is not None and a["meta"]["wav"] == l["meta"]["wav"] else ""
            if a is None:
                continue
            r.append(f"- {a['model']} Versuch {a['versuch']}: „{a['speech']}“, stability {a['settings']['stability']}, "
                     f"style {a['settings']['style']}, speed {a['settings'].get('speed', '–')}, Tempo-Korrektur x{a['check'].get('stretch', 1.0):.2f} → "
                     f"{'OK' if not a['fails'] else '; '.join(a['fails'])}; Whisper: „{a['check']['transcript']}“{mark}")
        r.append("")
    r += ["## eleven_v3", "",
          f"Für {n_v3_test} Zeilen mit `ton` wurde zusätzlich eine eleven_v3-Variante (mit Stimmungs-Tag) erzeugt und mit "
          f"demselben Check bewertet. Übernommen, weil besser als eleven_multilingual_v2: {n_v3} Zeilen.", ""]
    path.write_text("\n".join(r) + "\n")
    log(f"Stimmen-Bericht: {path}")
