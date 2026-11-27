"""Cover-Bild (1080x1920 JPG): Figur auf dem goldenen Weg + Titelzeile, ohne Untertitel.

  python3 -m motivation.cover <renderdir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from motivation import post as P

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"


def main():
    rdir = sys.argv[1]
    ev = json.loads((P.OUT / "events.json").read_text())
    f = int(ev["ring"][1]) - 2      # Figur im fertigen Goldring, Berg rechts
    img = P.BG + P.particles(f)
    img = P.screen(np.clip(img, 0, 1), P.darken(P.load_render(rdir, f)))
    txt = Image.new("RGBA", (P.W, P.H), (0, 0, 0, 0))
    glow = Image.new("RGBA", (P.W, P.H), (0, 0, 0, 0))
    lay = P.layout_head(["DON'T WAIT FOR", "*TOMORROW*"])
    lay = [(toks, int(size * 1.08), y + 30) for toks, size, y in lay]
    P.draw_head(txt, glow, lay, 99, 1.0)
    # Unterzeile
    d = ImageDraw.Draw(txt)
    fnt = P.font(P.F_SUB, 58)
    s = "Start today. Start now."
    w = fnt.getlength(s)
    d.text((P.W / 2 - w / 2, 1420), s, font=fnt, fill=(255, 255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0, 220))
    sh = np.asarray(txt.getchannel("A").filter(ImageFilter.GaussianBlur(22)), np.float32)[..., None] / 255
    img *= 1 - np.clip(sh * 1.6, 0, 0.75)
    g = np.asarray(glow.filter(ImageFilter.GaussianBlur(18)), np.float32) / 255
    img = P.screen(img, g[..., :3] * g[..., 3:4] * 0.55)
    t = np.asarray(txt, np.float32) / 255
    img = img * (1 - t[..., 3:4]) + t[..., :3] * t[..., 3:4]
    out = OUT / "dont-wait-for-tomorrow_cover.jpg"
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(out, quality=93)
    print(out)


if __name__ == "__main__":
    main()
