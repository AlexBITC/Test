"""Bildschirm-Ebenen fuer 'Wo kommt Filiale Nr. 2 hin?' (folge-09-filiale), 1280x720 pro Frame.

Wird von engine/overlays.screen_frame geladen. Die Bildfolge laeuft auf der schwebenden Tafel ueber der Stadtkarte
(assets/props/filiale.screen_tafel). Inhalte: drei_von_hundert (Szene 9), rechnung_8000_3prozent (Szene 10).
Zahlen = Sprechtext: 3 von 100, 8.000, 3 %, 240.
"""
import math

from PIL import Image, ImageDraw

from engine.overlays import font, ease_out, clamp01, ease_out_back

SW, SH = 1280, 720
BG = (20, 18, 40)
TURQ = (46, 230, 214)
GOLD = (242, 180, 90)
GREEN = (61, 220, 132)
GREY = (150, 148, 180)
WHITE = (255, 255, 255)


def _wf(s, core, default=None):
    for w in s["words"]:
        if w["w"].strip(".,!?:…").lower() == core.lower():
            return w["f0"]
    return default if default is not None else s["f0"] + 6


def _base():
    img = Image.new("RGBA", (SW, SH), (*BG, 255))
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, SW, 160):
        d.line([(x, 0), (x, SH)], fill=(46, 230, 214, 16), width=2)
    for y in range(0, SH, 160):
        d.line([(0, y), (SW, y)], fill=(46, 230, 214, 16), width=2)
    return img, d


def _t(d, xy, s, size, col, anchor="mm", a=1.0):
    d.text(xy, s, font=font(size), fill=tuple(col) + (int(255 * clamp01(a)),), anchor=anchor)


def drei_von_hundert(s, f):
    """Info-Karte '3 von 100': grosse goldene 3, darunter 'von 100' (das Punkteraster schwebt als 3D-Requisite daneben)."""
    img, d = _base()
    g0 = _wf(s, "drei")
    a = ease_out_back(clamp01((f - g0 + 2) / 8), 2.0)
    if a > 0:
        _t(d, (640, 300), "3", int(330 * max(0.2, a)), GOLD)
        _t(d, (640, 560), "von 100", int(150 * max(0.2, a)), WHITE)
    return img


def rechnung(s, f):
    """'8.000 × 3 % = 240 Kunden/Tag' baut sich auf: 8.000 und × 3 % sofort, = 240 beim Wort, dann Kunden/Tag."""
    img, d = _base()
    f_a = s["f0"] + 2
    f_b = _wf(s, "240") - 2
    f_c = _wf(s, "Kunden") + 2
    a1 = ease_out(clamp01((f - f_a) / 6))
    _t(d, (640, 200), "8.000 × 3 %", 150, WHITE, a=a1)
    a2 = ease_out_back(clamp01((f - f_b) / 8), 2.2)
    if a2 > 0:
        _t(d, (640, 410), "= 240", int(210 * max(0.3, a2)), GOLD)
    a3 = ease_out(clamp01((f - f_c) / 6))
    if a3 > 0:
        _t(d, (640, 600), "Kunden/Tag", 110, GREEN, a=a3)
        if f - f_c < 12:
            k = 1 + 0.15 * math.sin(math.pi * clamp01((f - f_c) / 12))
            d.rounded_rectangle((640 - 330 * k, 545, 640 + 330 * k, 655), 28, outline=GREEN + (int(200 * a3),), width=5)
    return img


def frame(tl, s, f):
    i = s["i"]
    if s["set"] == "stadtkarte" and i == 8:
        return drei_von_hundert(s, f)
    if s["set"] == "stadtkarte" and i == 9:
        return rechnung(s, f)
    return None
