"""Code-Texturen aus dem echten Quelltext website/index.html.

Syntax-Highlighting: Tags tuerkis #2EE6D6, Attribute #FFE14D, Strings orange #FF9F43, Rest weiss.
Pro Zeile eine transparente PNG (JetBrains Mono, OFL) + eine Code-Wand (viele Zeilen, fuer Tiefenunschaerfe).
Aufruf: python3 -m engine.codetex
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "website" / "index.html"
OUT = ROOT / "website" / "shots" / "code"
FONT = Path(__file__).resolve().parent / "fonts" / "JetBrainsMono-Bold.ttf"

TAG = (46, 230, 214)
ATTR = (255, 225, 77)
STR = (255, 159, 67)
TXT = (255, 255, 255)
NUM = (150, 150, 180)

SIZE = 44          # Schriftgroesse der Zeilen-Texturen
LINE_H = 64
PLATES = 56

# Schluesselzeilen (Kopfzeile, Angebot, Formular) fuer die scharfen Code-Zeilen
KEY_LINES = {"kopf": '<header class="kopf" id="kopf">',
             "angebot": '<section id="angebot">',
             "formular": '<form id="formular" novalidate>'}

_TOKEN = re.compile(r'("[^"]*"|\'[^\']*\')|(</?[A-Za-z][A-Za-z0-9-]*|/?>|<!doctype)|'
                    r'(?<=\s)([A-Za-z_:][A-Za-z0-9_:-]*)(?==)', re.I)


def tokens(line: str, mode: str):
    """[(text, farbe)] fuer eine Zeile. mode: html | css | js."""
    out, pos = [], 0
    for m in _TOKEN.finditer(line):
        if m.start() > pos:
            out.append((line[pos:m.start()], TXT))
        if m.group(1):
            out.append((m.group(1), STR))
        elif m.group(2):
            # In CSS/JS sind '<'/'>' keine Tags, ausser echte <style>/<script>-Tags
            is_tag = mode == "html" or re.match(r"</?(style|script)", m.group(2), re.I)
            out.append((m.group(2), TAG if is_tag else TXT))
        else:
            out.append((m.group(3), ATTR if mode == "html" else TXT))
        pos = m.end()
    if pos < len(line):
        out.append((line[pos:], TXT))
    return out


def modes(lines):
    res, mode = [], "html"
    for ln in lines:
        s = ln.strip().lower()
        if s.startswith("</style") or s.startswith("</script"):
            mode = "html"
        res.append(mode)
        if s.startswith("<style"):
            mode = "css"
        elif s.startswith("<script"):
            mode = "js"
    return res


def font(size=SIZE):
    return ImageFont.truetype(str(FONT), size)


def render_line(text: str, mode: str, size=SIZE, line_h=LINE_H, number=None):
    f = font(size)
    toks = tokens(text.rstrip("\n"), mode)
    prefix = f"{number:>3}  " if number is not None else ""
    w = int(f.getlength(prefix + text.rstrip())) + 24
    img = Image.new("RGBA", (max(w, 32), line_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x, y = 12, line_h / 2
    if prefix:
        d.text((x, y), prefix, font=f, fill=(*NUM, 255), anchor="lm")
        x += f.getlength(prefix)
    for t, col in toks:
        d.text((x, y), t, font=f, fill=(*col, 255), anchor="lm")
        x += f.getlength(t)
    return img


def wall(lines, mds, start, count, size=30, line_h=44, width=1800):
    img = Image.new("RGBA", (width, line_h * count + 20), (0, 0, 0, 0))
    for k in range(count):
        i = (start + k) % len(lines)
        li = render_line(lines[i], mds[i], size, line_h, number=i + 1)
        img.alpha_composite(li.crop((0, 0, min(li.width, width), line_h)), (0, 10 + k * line_h))
    return img


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    lines = SRC.read_text().split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    mds = modes(lines)
    info = {"zeilen": len(lines), "dateien": [], "schluessel": {}}
    for i, (ln, md) in enumerate(zip(lines, mds)):
        p = OUT / f"zeile_{i + 1:03d}.png"
        render_line(ln.strip() or " ", md).save(p)
        info["dateien"].append({"zeile": i + 1, "datei": p.name, "text": ln.strip(), "modus": md})
    for k, needle in KEY_LINES.items():
        i = next(j for j, ln in enumerate(lines) if needle in ln)
        info["schluessel"][k] = i + 1
        render_line(lines[i].strip(), mds[i], 72, 104).save(OUT / f"fokus_{k}.png")
    # Platten fuer den Code-Turm: feste Breite, echte Zeilen gleichmaessig ueber die Datei verteilt
    filled = [j for j, ln in enumerate(lines) if len(ln.strip()) > 3]
    picks = [filled[int(k * (len(filled) - 1) / (PLATES - 1))] for k in range(PLATES)]
    info["platten"] = []
    for k, j in enumerate(picks):
        im = render_line(lines[j].strip(), mds[j], 40, 72, number=j + 1)
        pl = Image.new("RGBA", (900, 72), (0, 0, 0, 0))
        pl.alpha_composite(im.crop((0, 0, min(im.width, 900), 72)))
        pl.save(OUT / f"platte_{k:02d}.png")
        info["platten"].append(j + 1)
    wall(lines, mds, 0, 64).save(OUT / "wand_a.png")
    wall(lines, mds, 150, 64).save(OUT / "wand_b.png")
    (OUT / "code.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
    return info


if __name__ == "__main__":
    i = build()
    print("Code-Texturen:", i["zeilen"], "Zeilen, Schluessel:", i["schluessel"])
