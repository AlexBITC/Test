"""Komplette Pipeline fuer das Motivationsvideo.

  python3 -m motivation.make            # alles (vorhandene Stimm-Takes/Frames werden wiederverwendet)
  python3 -m motivation.make --from audio

Stufen: voice -> timeline -> events -> render -> audio -> post -> cover -> qa
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "motivation"
FRAMES = ROOT / "out" / "work" / "mf2"
FINAL = ROOT / "out" / "dont-wait-for-tomorrow.mp4"
BL = os.environ.get("BLENDER", "blender")
STAGES = ["voice", "timeline", "events", "render", "audio", "post", "cover", "qa"]


def run(cmd, **kw):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(list(map(str, cmd)), check=True, cwd=ROOT, **kw)


def main():
    start = sys.argv[sys.argv.index("--from") + 1] if "--from" in sys.argv else "voice"
    todo = STAGES[STAGES.index(start):]
    py = sys.executable
    tl = OUT / "timeline.json"
    if "voice" in todo:
        run([py, "-m", "motivation.voice"])
    if "timeline" in todo:
        run([py, "-m", "motivation.timeline"])
    if "events" in todo:
        run([BL, "-b", "--factory-startup", "--python", "motivation/scene.py", "--", tl, OUT / "ev"],
            env={**os.environ, "EVENTS_OUT": str(OUT / "events.json")})
    if "render" in todo:
        FRAMES.mkdir(parents=True, exist_ok=True)
        run([BL, "-b", "--factory-startup", "--python", "motivation/scene.py", "--", tl, FRAMES, "all"],
            env={**os.environ, "CYCLES_SAMPLES": os.environ.get("CYCLES_SAMPLES", "16")})
    if "audio" in todo:
        run([py, "-m", "motivation.audio"])
    if "post" in todo:
        run([py, "-m", "motivation.post", FRAMES, FINAL, "--audio", OUT / "mix.wav"])
    if "cover" in todo:
        run([py, "-m", "motivation.cover", FRAMES])
    if "qa" in todo:
        run([py, "-m", "motivation.qa", FINAL])


if __name__ == "__main__":
    main()
