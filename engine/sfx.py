"""Soundeffekte (Pop, Whoosh, Ding, Buzz) – mit ffmpeg aus Sinus und Rauschen erzeugt – und Audio-Mix.
Keine Musik. Lautheit: loudnorm I=-14 LUFS, TP=-1.5 dBTP (zwei Durchlaeufe)."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
SR = 48000
FPS = 30

# ffmpeg-lavfi-Rezepte (deterministisch: Rauschen mit festem Seed)
RECIPES = {
    "pop": ("aevalsrc=exprs='0.9*exp(-t*38)*sin(2*PI*(220*t+5200*t*t*exp(-t*30)))'"
            ":s=48000:d=0.16", "afade=t=out:st=0.12:d=0.04"),
    "whoosh": ("anoisesrc=color=pink:seed=42:amplitude=0.9:d=0.5:r=48000",
               "bandpass=f=900:width_type=o:w=2.2,volume='0.2+1.6*sin(PI*t/0.5)':eval=frame,"
               "afade=t=in:d=0.18,afade=t=out:st=0.25:d=0.25,highpass=f=180"),
    "ding": ("aevalsrc=exprs='0.55*exp(-t*4.5)*(sin(2*PI*1318*t)+0.45*sin(2*PI*2637*t)+0.2*sin(2*PI*3955*t))'"
             ":s=48000:d=1.1", "afade=t=in:d=0.004"),
    "buzz": ("aevalsrc=exprs='0.32*(sgn(sin(2*PI*110*t))+0.6*sgn(sin(2*PI*165*t)))*(0.6+0.4*sin(2*PI*22*t))'"
             ":s=48000:d=0.38", "lowpass=f=2200,afade=t=in:d=0.01,afade=t=out:st=0.28:d=0.1"),
}


def make_sfx(outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, (src, flt) in RECIPES.items():
        p = outdir / f"{name}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", src, "-af", flt, "-ac", "1",
                        "-ar", str(SR), str(p)], check=True)
        paths[name] = p
    return paths


def _load(p):
    y, sr = sf.read(str(p), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    assert sr == SR, (p, sr)
    return y


SFX_GAIN = {"pop": 0.30, "whoosh": 0.32, "ding": 0.30, "buzz": 0.22}


def build_mix(tl: dict, work: Path) -> Path:
    anchors = json.loads((work / "anchors.json").read_text())
    cues = anchors.get("cues", [])
    sfx = {k: _load(v) for k, v in make_sfx(work / "sfx").items()}
    n = int(tl["frames"] / FPS * SR) + SR
    mix = np.zeros(n, np.float32)
    for s in tl["scenes"]:
        y = _load(ROOT / s["wav"])
        a = int(round(s["audio_start"] * SR))
        mix[a:a + len(y)] += y[: max(0, n - a)]
    new_fmt = any(s.get("beat_list") for s in tl["scenes"])
    speech_peak = float(np.max(np.abs(mix))) if len(mix) else 1.0
    for f, kind, gain in cues:
        if new_fmt:
            # Soundeffekte 6 dB unter der Sprache: Effekt-Spitze = halbe Sprach-Spitze
            y = sfx[kind] / (np.max(np.abs(sfx[kind])) + 1e-9) * 0.5 * speech_peak * min(1.0, gain)
        else:
            y = sfx[kind] * SFX_GAIN[kind] * gain
        a = int(round(f / FPS * SR))
        if 0 <= a < n:
            mix[a:a + len(y)] += y[: n - a]
    mix = mix[: int(tl["frames"] / FPS * SR)]
    raw = work / "mix_raw.wav"
    sf.write(str(raw), mix, SR, subtype="FLOAT")
    # Lautheit in zwei Durchlaeufen
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(re.findall(r"\{[^{}]*\}", p.stderr)[-1])
    out = work / "mix.wav"
    flt = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
           f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
           f"linear=true,aresample=48000")
    tmp = work / "mix_ln.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", flt, "-ar", "48000", "-ac", "2",
                    str(tmp)], check=True)
    # Nachkorrektur: loudnorm trifft das Ziel bei kurzen Clips mit Pausen nicht immer exakt
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(tmp), "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m2 = json.loads(re.findall(r"\{[^{}]*\}", p.stderr)[-1])
    gain = min(-14.0 - float(m2["input_i"]), -1.5 - float(m2["input_tp"]))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-af", f"volume={gain:.2f}dB", "-ar", "48000",
                    "-ac", "2", str(out)], check=True)
    return out
