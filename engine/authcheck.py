"""Authentizitaets-Check der Stimmen einer Folge (nach dem Stimmen-Stage).
  python3 -m engine.authcheck <slug> [<slug> ...]   -> out/<slug>_authentizitaet.md
Prueft gegen die Referenzfolge (website, ElevenLabs):
  1. Gleiche Stimme: Voice-IDs, Tonlage (F0-Median) und Klangfarbe (MFCC-Mittel, Kosinus-Aehnlichkeit)
  2. Dialekt: Wird das Dialektwort so gesprochen? Whisper einmal frei, einmal mit dem Zeilentext als Hinweis
     (bleibt Whisper trotz Hinweis beim Hochdeutschen, hat die Stimme sehr wahrscheinlich hochdeutsch gesprochen)
  3. Natuerlichkeit: Tempo, Tonhoehen-Streuung, laengste Pause (aus dem Stimmen-Check)
  4. Stimmung: Aufgeregte Zeilen lauter/hoeher als ruhige?"""
import json
import re
import sys
from pathlib import Path

import librosa
import numpy as np

from . import voicecheck

ROOT = Path(__file__).resolve().parent.parent
REF = "website"
DIALEKT = {"des": "das", "net": "nicht", "i": "ich", "isch": "ist", "mi": "mich", "mei": "mein", "en": "einen",
           "spinnet": "spinnen", "hab": "habe", "hol": "hole", "schreib": "schreibe", "verkauf": "verkaufe",
           "verlier": "verliere", "behalt": "behalte", "brauch": "brauche", "telefonier": "telefoniere", "merk": "merke"}
HOCH = {"laut", "empört", "verzweifelt", "baff", "ungläubig", "triumphierend", "überglücklich", "lachend", "frech"}
TIEF = {"ruhig", "leise", "kleinlaut", "ernst", "erklärend", "präzise", "verschmitzt"}


def core(w):
    return re.sub(r"^[^\w']+|[^\w']+$", "", w).lower()


def feats(wav):
    y, sr = librosa.load(str(ROOT / wav), sr=16000)
    f0, vflag, _ = librosa.pyin(y, fmin=60, fmax=400, sr=sr, frame_length=1024)
    mf = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    n = min(mf.shape[1], len(vflag))
    voiced = vflag[:n]
    mfv = mf[1:, :n][:, voiced] if voiced.any() else mf[1:, :n]
    rms = librosa.feature.rms(y=y)[0]
    f0v = f0[~np.isnan(f0)]
    return {"mfcc": mfv.mean(axis=1), "f0": float(np.median(f0v)) if len(f0v) else 0.0,
            "f0_st": float(np.std(12 * np.log2(f0v / np.median(f0v)))) if len(f0v) > 5 else 0.0,
            "rms_db": float(20 * np.log10(np.percentile(rms, 90) + 1e-9))}


def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


_TOK = None


def score(wav, text):
    """Log-Wahrscheinlichkeit, dass Whisper genau diesen Text im Ton hoert (erzwungene Ausrichtung)."""
    global _TOK
    from faster_whisper.audio import pad_or_trim
    from faster_whisper.tokenizer import Tokenizer
    m = voicecheck.whisper()
    if _TOK is None:
        _TOK = Tokenizer(m.hf_tokenizer, True, task="transcribe", language="de")
    feats = m.feature_extractor(voicecheck.load16k(ROOT / wav))
    nf = feats.shape[-1]
    enc = m.encode(pad_or_trim(feats))
    res = m.model.align(enc, _TOK.sot_sequence, [_TOK.encode(" " + text.strip())], nf)[0]
    return float(np.log(np.maximum(np.array(res.text_token_probs), 1e-9)).sum())


def swap(text, idx, repl):
    toks = text.split()
    t = toks[idx]
    c = core(t)
    pre, post = t[:t.lower().find(c)], t[t.lower().find(c) + len(c):]
    rep = repl if t[:1].islower() else repl[:1].upper() + repl[1:]
    toks[idx] = pre + rep + post
    return " ".join(toks)


def transcribe(wav, prompt=None):
    y = voicecheck.load16k(ROOT / wav)
    segs, _ = voicecheck.whisper().transcribe(y, language="de", beam_size=5, vad_filter=False,
                                              initial_prompt=prompt, condition_on_previous_text=False)
    return " ".join(s.text.strip() for s in segs)


def load(slug):
    tl = json.loads((ROOT / "out" / "work" / slug / "timeline.json").read_text())
    return tl, [s for s in tl["scenes"] if s.get("wav")]


def profile(scenes):
    out = {}
    for s in scenes:
        out.setdefault(s["sprecher"], []).append(feats(s["wav"]))
    return {r: {"mfcc": np.mean([x["mfcc"] for x in v], axis=0), "f0": float(np.median([x["f0"] for x in v]))}
            for r, v in out.items()}


def check(slug, ref):
    tl, scenes = load(slug)
    ep = next(json.loads(p.read_text()) for p in (ROOT / "episodes").glob("*.json")
              if not p.name.endswith(".regie.json") and json.loads(p.read_text()).get("slug") == slug)
    cfg = json.loads((ROOT / "engine" / "voices.json").read_text())
    tune = cfg.get("line_tuning", {}).get(slug, {})
    F = [feats(s["wav"]) for s in scenes]
    prof = {}
    for s, f in zip(scenes, F):
        prof.setdefault(s["sprecher"], []).append(f)
    r = [f"# Authentizitäts-Check: {tl['titel']}", "",
         f"Referenz: Folge `{REF}` (ElevenLabs `eleven_multilingual_v2`). Modell dieser Folge: `{tl.get('model')}`.", ""]
    # 1) Stimme
    r += ["## 1. Gleiche Stimme wie in der Referenz", "",
          "| Figur | Stimme (Voice-ID) | F0-Median Folge | F0-Median Referenz | Abstand | Klangfarbe ähnlich zur Referenz (gleiche Figur) | zum Vergleich: andere Figur | Ergebnis |",
          "|---|---|---|---|---|---|---|---|"]
    ok_voice = True
    for role in ("kalle", "byte"):
        if role not in prof:
            continue
        mf = np.mean([x["mfcc"] for x in prof[role]], axis=0)
        f0 = float(np.median([x["f0"] for x in prof[role]]))
        other = "byte" if role == "kalle" else "kalle"
        same, diff = cos(mf, ref[role]["mfcc"]), cos(mf, ref[other]["mfcc"])
        st = 12 * np.log2(f0 / ref[role]["f0"])
        good = same > diff and abs(st) <= 3.0
        ok_voice &= good
        v = cfg["voices"][role]
        r.append(f"| {role.capitalize()} | {v['name'].split(' - ')[0]} (`{v['voice_id']}`) | {f0:.0f} Hz | {ref[role]['f0']:.0f} Hz | "
                 f"{st:+.1f} Halbtöne | {same:.3f} | {diff:.3f} | {'✓ gleiche Stimme' if good else '✗ prüfen'} |")
    r += ["", "Klangfarbe = Kosinus-Ähnlichkeit der mittleren MFCC-Vektoren (stimmhafte Abschnitte). Gleiche Stimme, wenn sie zur "
          "Referenz derselben Figur ähnlicher ist als zur anderen Figur und die Tonlage höchstens 3 Halbtöne abweicht.", ""]
    # 2) Dialekt
    r += ["## 2. Dialekt", "",
          "Methode: Whisper bewertet für jedes Dialektwort zwei Fassungen der Zeile, die sich nur in diesem Wort unterscheiden "
          "(erzwungene Ausrichtung, Log-Wahrscheinlichkeit). Δ = Dialekt − Hochdeutsch. Δ > −1: Dialekt gesprochen; "
          "Δ < −3: hochdeutsch gesprochen; dazwischen unklar. Whisper bevorzugt von sich aus leicht die Schriftsprache, "
          "deshalb die Toleranz von −1.", "",
          "| Szene | Wort im Text | an die Stimme geschickt | Whisper frei | Δ Dialekt − Hochdeutsch | Ergebnis |",
          "|---|---|---|---|---|---|"]
    n_d = n_ok = 0
    for s in scenes:
        toks = s["text"].split()
        idxs = [k for k, w in enumerate(toks) if core(w) in DIALEKT]
        if not idxs:
            continue
        sp = {k: v for k, v in cfg.get("speech_overrides", {}).items() if k in toks}   # wie render.voices_stage
        sp.update(tune.get(str(s["i"] + 1), {}).get("speech", {}))
        free = transcribe(s["wav"])
        for k in idxs:
            w = core(toks[k])
            sent = sp.get(toks[k], sp.get(core(toks[k]), w)).strip(".,!?:;…")
            n_d += 1
            spoken = w if core(sent) == DIALEKT[w] else sent       # umgangssprachliche Schreibweise ('n) zaehlt als Dialekt
            d = score(s["wav"], swap(s["text"], k, spoken)) - score(s["wav"], swap(s["text"], k, DIALEKT[w]))
            if core(sent) == DIALEKT[w]:
                res = f"bewusst hochdeutsch geschickt („{sent}“)"
            elif d > -1:
                res = "✓ Dialekt gesprochen"
                n_ok += 1
            elif d < -3:
                res = "✗ hochdeutsch gesprochen"
            else:
                res = "? unklar"
            r.append(f"| {s['i']+1} | {w} | {sent} | {free} | {d:+.1f} | {res} |")
    r += ["", f"Dialektwörter: {n_d}, davon als Dialekt gesprochen: {n_ok}.", ""]
    # 3) Natuerlichkeit
    r += ["## 3. Natürlichkeit", "", "| Szene | Sprecher | Tempo (W/s) | Tonhöhen-Streuung | Lautheit (P90) | Status |",
          "|---|---|---|---|---|---|"]
    for s, f in zip(scenes, F):
        n_w = len([w for w in s["text"].split() if re.search(r"\w", w)])
        ws = [w for w in s["words"] if re.search(r"\w", w["w"])]
        wps = n_w / max(0.1, ws[-1]["end"] - ws[0]["start"]) if ws else 0
        flag = "✓" if 2.0 <= wps <= 3.0 and f["f0_st"] >= 1.5 else "⚠ " + ("Tempo " if not 2.0 <= wps <= 3.0 else "") + \
            ("monoton" if f["f0_st"] < 1.5 else "")
        r.append(f"| {s['i']+1} | {s['sprecher']} | {wps:.2f} | {f['f0_st']:.1f} Halbtöne | {f['rms_db']:.1f} dB | {flag} |")
    r.append("")
    # 4) Stimmung
    r += ["## 4. Stimmung", ""]
    rows = []
    for s, f in zip(scenes, F):
        mood = (ep["szenen"][s["i"]].get("stimmung") or "").lower()
        txt = s["text"]
        lvl = "hoch" if (set(re.split(r"[ ,]+", mood)) & HOCH) or (not mood and "!" in txt) else \
            "ruhig" if (set(re.split(r"[ ,]+", mood)) & TIEF) or (not mood and "!" not in txt and "?" not in txt) else "mittel"
        base = np.median([x["f0"] for x in prof[s["sprecher"]]])
        rows.append((s, f, lvl, mood, 12 * np.log2(f["f0"] / base)))
    r += ["| Szene | Sprecher | Vorgabe | Erregung | F0 ggü. Figur-Mittel | Lautheit |", "|---|---|---|---|---|---|"]
    for s, f, lvl, mood, d in rows:
        r.append(f"| {s['i']+1} | {s['sprecher']} | {mood or ('Satzzeichen: ' + ('!' if '!' in s['text'] else '?' if '?' in s['text'] else '.'))} | {lvl} | {d:+.1f} Halbtöne | {f['rms_db']:.1f} dB |")
    hi = [d for _, _, lvl, _, d in rows if lvl == "hoch"]
    lo = [d for _, _, lvl, _, d in rows if lvl == "ruhig"]
    if hi and lo:
        r += ["", f"Mittel F0: aufgeregte Zeilen {np.mean(hi):+.1f} Halbtöne, ruhige {np.mean(lo):+.1f} Halbtöne → "
              f"{'✓ Stimmung hörbar' if np.mean(hi) > np.mean(lo) else '✗ kaum Unterschied'}."]
    r += ["", "Hinweis: `eleven_multilingual_v2` bekommt keine Stimmungs-Anweisung; die Stimmung entsteht nur aus Text, "
          "Satzzeichen und Stil-Einstellung (stability/style).", ""]
    (ROOT / "out" / f"{slug}_authentizitaet.md").write_text("\n".join(r) + "\n")
    print(f"[auth] {slug}: Stimme {'OK' if ok_voice else 'PRUEFEN'}, Dialekt {n_ok}/{n_d}")


def main():
    _, ref_sc = load(REF)
    ref = profile(ref_sc)
    for slug in sys.argv[1:]:
        check(slug, ref)


if __name__ == "__main__":
    main()
