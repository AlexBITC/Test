"""Abgeleitete Texturen aus den echten Playwright-Aufnahmen (website/shots) fuer Geraete-Displays,
plus der leere Browser mit Fragezeichen (Szene 1). Aufruf: python3 -m engine.textures"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "website" / "shots"
OUT = SHOTS / "geraete"
LILITA = Path(__file__).resolve().parent / "fonts" / "LilitaOne-Regular.ttf"
CREME = (255, 244, 224)


def boxes():
    return json.loads((SHOTS / "boxen.json").read_text())


def crop_viewport(name, top_css, out):
    """Ausschnitt in Viewport-Groesse ab top_css (CSS-Pixel) aus der Ganzseiten-Aufnahme."""
    b = boxes()
    dpr = b["dpr"]
    vp = b["breiten"][name]["viewport"]
    im = Image.open(SHOTS / f"seite_{name}.png").convert("RGB")
    y0 = int(top_css * dpr)
    h = int(vp["height"] * dpr)
    y0 = max(0, min(y0, im.height - h))
    im.crop((0, y0, im.width, y0 + h)).save(out)


def browser_leer(out, w=1440, h=900, q=(170, 176, 200)):
    im = Image.new("RGB", (w, h), (236, 238, 245))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 90), fill=(214, 218, 230))
    for i, c in enumerate([(255, 95, 87), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((30 + i * 44, 30, 60 + i * 44, 60), fill=c)
    d.rounded_rectangle((200, 22, w - 60, 68), 22, fill=(255, 255, 255))
    f = ImageFont.truetype(str(LILITA), 520)
    d.text((w / 2, h / 2 + 60), "?", font=f, fill=q, anchor="mm")
    im.save(out)


def handy_formular_frames():
    """Formular-Sequenz (echte Playwright-Frames) in einen Handy-Viewport gesetzt: Kopfzeile oben,
    darunter der Abschnitt 'Stollen vorbestellen'."""
    b = boxes()
    dpr = b["dpr"]
    vp = b["breiten"]["handy"]["viewport"]
    W, H = vp["width"] * dpr, vp["height"] * dpr
    kopf = Image.open(SHOTS / "abschnitte" / "stil_kopf.png").convert("RGB")
    res = []
    for i, fr in enumerate(b["formular"]):
        im = Image.new("RGB", (W, H), CREME)
        im.paste(kopf, (0, 0))
        sec = Image.open(SHOTS / "formular" / fr["datei"]).convert("RGB")
        im.paste(sec, (0, kopf.height + 30))
        p = OUT / f"handy_formular_{i:02d}.png"
        im.save(p)
        res.append({"datei": p.name, "schritt": fr["schritt"], "y_offset_px": kopf.height + 30})
    return res


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    b = boxes()
    for name in ("handy", "tablet", "laptop"):
        ang = b["breiten"][name]["boxen"]["angebot"]
        crop_viewport(name, ang["y"] - 12, OUT / f"angebot_{name}.png")
    browser_leer(OUT / "browser_leer.png")
    browser_leer(OUT / "browser_leer_blink.png", q=(255, 196, 40))
    info = {"formular": handy_formular_frames()}
    (OUT / "geraete.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
    return info


if __name__ == "__main__":
    print(build())
