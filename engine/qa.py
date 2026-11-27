"""Qualitaetspruefung: ffprobe-Werte, Prueffframes an den vorgegebenen Stellen, Loop-Vergleich.
Aufruf: python3 -m engine.qa episodes/folge-03-website.json"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def probe(mp4: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(mp4)],
                         capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next(s for s in d["streams"] if s["codec_type"] == "audio")
    return {"breite": v["width"], "hoehe": v["height"], "fps": v["r_frame_rate"], "video": v["codec_name"],
            "profil": v.get("profile"), "pix_fmt": v["pix_fmt"], "audio": a["codec_name"],
            "audio_hz": a["sample_rate"], "audio_kbit": round(int(a.get("bit_rate", 0)) / 1000),
            "dauer_s": round(float(d["format"]["duration"]), 2), "groesse_mb": round(int(d["format"]["size"]) / 1e6, 1)}


def frame_at(mp4: Path, f: int, out: Path):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-vf", f"select=eq(n\\,{f})", "-frames:v", "1",
                    str(out)], check=True)


def main():
    ep_path = ROOT / sys.argv[1]
    ep = json.loads(ep_path.read_text())
    mp4 = ROOT / "out" / f"{ep_path.stem}.mp4"
    tl = json.loads((ROOT / "out" / "work" / ep["slug"] / "timeline.json").read_text())
    sc = tl["scenes"]
    qa = ROOT / "out" / "work" / ep["slug"] / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    p = probe(mp4)
    print(json.dumps(p, ensure_ascii=False))

    def wf(i, core, nth=1):
        n = 0
        for w in sc[i]["words"]:
            if w["w"].strip(".,!?:–").lower() == core.lower():
                n += 1
                if n == nth:
                    return w["f0"]
        return sc[i]["f0"]
    s6 = sc[5]
    b0, c0 = wf(5, "Farben") - 5, wf(5, "klickbar") - 6
    picks = {"0_5s": 15,
             "szene5_zaehler": sc[4]["f0"] + int(0.8 * sc[4]["n"]),
             "szene6_A": (s6["f0"] + b0) // 2,
             "szene6_B": (b0 + c0) // 2 + 4,
             "szene6_C": (c0 + s6["f1"]) // 2,
             "szene7": (sc[6]["f0"] + sc[6]["f1"]) // 2,
             "szene10": sc[9]["f1"] - 12,
             "erstes": 0,
             "letztes": tl["frames"] - 1}
    for name, f in picks.items():
        frame_at(mp4, f, qa / f"{name}.png")
    a = np.asarray(Image.open(qa / "erstes.png").convert("L"), np.float32)
    b = np.asarray(Image.open(qa / "letztes.png").convert("L"), np.float32)
    dark = {n: float(np.asarray(Image.open(qa / f"{n}.png").convert("L")).mean()) for n in picks}
    res = {"probe": p, "frames": picks, "helligkeit": dark,
           "loop_mittlere_abweichung": float(np.abs(a - b).mean()),
           "schwarzes_bild": [n for n, v in dark.items() if v < 8]}
    (qa / "qa.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
