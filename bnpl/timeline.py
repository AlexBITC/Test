"""Baut die Timeline (Satz- und Wortzeiten, Szenenfenster) aus den gewaehlten Takes.

  python3 -m motivation.timeline  -> out/motivation/timeline.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
OUT = ROOT / "out" / "bnpl"
FPS = 30
LEAD = 0.2           # Stimme beginnt nach 0,2 s (Hook)
OUTRO = 0.75         # nach "this?" bis zur Loop-Naht; mit LEAD ergibt das ~0,9 s Pause vor Satz 1
MIN_LEN, MAX_LEN = 35.3, 44.5


def audible(wav):
    """Erster/letzter hoerbarer Moment (-35 dB unter Spitze) in Sekunden."""
    import numpy as np
    import soundfile as sf
    y, sr = sf.read(str(ROOT / wav), dtype="float32")
    hop = int(0.005 * sr)
    rms = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2) + 1e-12) for i in range(0, len(y), hop)])
    loud = np.nonzero(rms > rms.max() * 10 ** (-35 / 20))[0]
    return loud[0] * hop / sr, (loud[-1] + 1) * hop / sr, len(y) / sr


def clean_cut(tk):
    """Satz-WAV ab erstem Wort -0,08 s bis letztem Wort +0,30 s schneiden (entfernt Klicks/Atem am
    Dateiende), weiche Blenden. Wortzeiten werden verschoben."""
    import numpy as np
    import soundfile as sf
    y, sr = sf.read(str(ROOT / tk["wav"]), dtype="float32")
    a = max(0.0, tk["words"][0]["start"] - 0.08)
    b = min(len(y) / sr, tk["words"][-1]["end"] + 0.30)
    y = y[int(a * sr):int(b * sr)].copy()
    fi, fo = int(0.01 * sr), int(0.12 * sr)
    y[:fi] *= np.linspace(0, 1, fi)
    y[-fo:] *= np.linspace(1, 0, fo) ** 2
    dst = OUT / "voice" / f"final_s{tk['id']:02d}.wav"
    sf.write(str(dst), y, sr, subtype="PCM_24")
    t = dict(tk)
    t["wav"] = str(dst.relative_to(ROOT))
    t["dur"] = len(y) / sr
    t["words"] = [{"w": w["w"], "start": w["start"] - a, "end": w["end"] - a} for w in tk["words"]]
    return t


def build():
    cfg = json.loads((HERE / "script.json").read_text())
    takes = json.loads((OUT / "voice" / "takes.json").read_text())
    chosen = []
    for s in cfg["sentences"]:
        e = takes[str(s["id"])]
        t = next(t for t in e["takes"] if t["seed"] == e["chosen"])
        chosen.append((s, clean_cut(t)))
    speech = sum((lambda a: a[1] - a[0])(audible(t["wav"])) for _, t in chosen)
    pauses = [s["pause_before"] for s, _ in chosen]
    outro = OUTRO
    total = LEAD + speech + sum(pauses) + outro
    # zu kurz: erst Pausen bis an die Obergrenze (0,5 s; vor Satz 8 fest 0,8 s), dann Outro bis 5,0 s
    if total < MIN_LEN:
        for i, (s, _) in enumerate(chosen):
            if i and s["id"] != 7 and total < MIN_LEN:
                add = max(0.0, min(0.6 - pauses[i], MIN_LEN - total))
                pauses[i] += add
                total += add
    if total < MIN_LEN:
        add = min(1.6 - outro, MIN_LEN - total)
        outro += add
        total += add
    sents, t = [], LEAD
    prev_off = 0.0
    for i, (s, tk) in enumerate(chosen):
        on, off, dur = audible(tk["wav"])
        if i:
            # Pause = Stille zwischen hoerbarem Ende und hoerbarem Anfang
            t = prev_end_abs + pauses[i] - on
        else:
            t = LEAD - on
        words = [{"w": w["w"], "start": round(t + w["start"], 3), "end": round(t + w["end"], 3)} for w in tk["words"]]
        sents.append({"id": s["id"], "text": s["text"], "mood": s["mood"], "start": round(t, 3),
                      "end": round(t + tk["dur"], 3), "wav": tk["wav"], "seed": tk["seed"],
                      "pause_before": round(pauses[i], 3), "lufs": tk["lufs"], "words": words})
        prev_end_abs = t + off
        sents[-1]["audible"] = [round(t + on, 3), round(t + off, 3)]
        t += tk["dur"]
    total = prev_end_abs + outro
    n_frames = int(math.ceil(total * FPS))
    tl = {"fps": FPS, "n_frames": n_frames, "duration": n_frames / FPS, "lead": LEAD, "outro": round(outro, 3),
          "voice": cfg["voice"], "mood_gain_db": cfg["mood_gain_db"], "sentences": sents}
    (OUT / "timeline.json").write_text(json.dumps(tl, indent=1, ensure_ascii=False))
    return tl


if __name__ == "__main__":
    tl = build()
    print(f"Dauer {tl['duration']:.2f} s, {tl['n_frames']} Frames, Outro {tl['outro']} s")
    for s in tl["sentences"]:
        print(f"S{s['id']:>2} hoerbar {s['audible'][0]:6.2f}-{s['audible'][1]:6.2f} {s['start']:6.2f}-{s['end']:6.2f}  Pause davor {s['pause_before']:.2f}  {s['text']}")
