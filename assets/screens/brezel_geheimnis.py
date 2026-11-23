"""Bildschirm-Ebenen fuer 'Das Geheimnis in Kalles Haenden' (folge-10-brezel-geheimnis), 1280x720 pro Frame.

Wird von engine/overlays.screen_frame geladen (Studio-Screen).
  zeitlupe_kalle   (Szene 5): Kalles Schlingen in extremer Zeitlupe (0,25x): Strang legt sich zur Brezel, Haende als
                   Kreise an den Enden, schwebender Mehlstaub, Kennung 'ZEITLUPE 0,25x' mit REC-Punkt.
  bahnen_vergleich (Szene 6): zwei Bahnen uebereinander, 'KALLE' mit Bogen (tuerkis), 'LEA' flach (grau).
  wissen           (Szene 8): ruhiger Titel 'IMPLIZITES WISSEN' hinter dem Eisberg.
Zahlen = Sprechtext: 5 Schritte (Nummern 1-5 an den Standbildern, hier nicht noetig).
"""
import math
import random

from PIL import Image, ImageDraw

from engine.overlays import font, ease_out, clamp01, ease_in_out

SW, SH = 1280, 720
BG = (20, 18, 40)
TURQ = (46, 230, 214)
GOLD = (242, 180, 90)
GREY = (150, 148, 180)
WHITE = (255, 255, 255)
RED = (255, 77, 90)
TEIG = (235, 203, 156)


def _wf(s, core, default=None):
    for w in s["words"]:
        if w["w"].strip(".,!?:…").lower() == core.lower():
            return w["f0"]
    return default if default is not None else s["f0"] + 6


def _base():
    img = Image.new("RGBA", (SW, SH), (*BG, 255))
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, SW, 160):
        d.line([(x, 0), (x, SH)], fill=(46, 230, 214, 14), width=2)
    for y in range(0, SH, 160):
        d.line([(0, y), (SW, y)], fill=(46, 230, 214, 14), width=2)
    return img, d


def _t(d, xy, s, size, col, anchor="mm", a=1.0):
    d.text(xy, s, font=font(size), fill=tuple(col) + (int(255 * clamp01(a)),), anchor=anchor)


def _brezel_kurve(t):
    """Punkte der Brezel-Linie bis Anteil t (0..1), Bildschirm-Koordinaten."""
    pts = []
    n = 120
    for k in range(int(n * t) + 1):
        u = k / n
        if u < 0.55:                                   # Bauch
            a = math.pi * (0.95 + 1.1 * u / 0.55)
            pts.append((640 + 300 * math.cos(a), 430 - 220 * math.sin(a) * 0.9))
        else:                                          # Aermchen ueber Kreuz
            v = (u - 0.55) / 0.45
            x = 640 + 300 * math.cos(math.pi * 2.05) * (1 - v) + (-260) * v
            y = 430 - 40 - 160 * math.sin(math.pi * v)
            pts.append((x, y))
    return pts


def zeitlupe_kalle(s, f):
    img, d = _base()
    t = clamp01((f - s["f0"]) / max(1, s["f1"] - s["f0"] - 10)) * 0.25 / 0.25
    t = ease_in_out(t)
    pts = _brezel_kurve(0.15 + 0.85 * t)
    if len(pts) > 1:
        d.line(pts, fill=(*TEIG, 255), width=34, joint="curve")
        d.line(pts, fill=(255, 230, 190, 255), width=10, joint="curve")
    if pts:
        for (x, y), r in ((pts[0], 38), (pts[-1], 38)):
            d.ellipse((x - r, y - r, x + r, y + r), fill=(240, 200, 170, 235), outline=(*TURQ, 255), width=4)
    rnd = random.Random(4)
    for k in range(40):
        x0, y0, sp = rnd.uniform(0, SW), rnd.uniform(0, SH), rnd.uniform(0.2, 0.6)
        y = (y0 - (f - s["f0"]) * sp) % SH
        r = rnd.uniform(2, 5)
        d.ellipse((x0 - r, y - r, x0 + r, y + r), fill=(255, 255, 255, 120))
    d.rounded_rectangle((40, 30, 420, 100), 20, fill=(36, 32, 74, 235), outline=(*TURQ, 255), width=3)
    d.ellipse((66, 52, 92, 78), fill=(*RED, 255 if (f // 12) % 2 == 0 else 120))
    _t(d, (250, 66), "ZEITLUPE 0,25×", 40, WHITE)
    return img


def bahnen_vergleich(s, f):
    img, d = _base()
    f_a = s["f0"] + 4
    f_b = _wf(s, "Lea") - 4
    ta = ease_out(clamp01((f - f_a) / 30))
    tb = ease_out(clamp01((f - f_b) / 20))
    _t(d, (90, 200), "KALLE", 52, TURQ, anchor="lm")
    n = 60
    pk = []
    for k in range(int(n * ta) + 1):
        u = k / n
        x = 330 + 860 * u
        bogen = 120 * math.exp(-((u - 0.55) / 0.12) ** 2)
        pk.append((x, 230 - bogen))
    if len(pk) > 1:
        d.line(pk, fill=(*TURQ, 255), width=12, joint="curve")
        x, y = pk[-1]
        d.ellipse((x - 16, y - 16, x + 16, y + 16), fill=(*TURQ, 255))
    if ta > 0.6:
        _t(d, (330 + 860 * 0.55, 70), "Schwung!", 44, GOLD, a=(ta - 0.6) / 0.4)
    _t(d, (90, 520), "LEA", 52, GREY, anchor="lm")
    pl = [(330 + 860 * k / n, 540) for k in range(int(n * tb) + 1)]
    if len(pl) > 1:
        d.line(pl, fill=(*GREY, 255), width=12)
        x, y = pl[-1]
        d.ellipse((x - 16, y - 16, x + 16, y + 16), fill=(*GREY, 255))
    d.line([(60, 380), (1220, 380)], fill=(255, 255, 255, 40), width=2)
    return img


def wissen(s, f):
    img, d = _base()
    a = ease_out(clamp01((f - s["f0"] - 4) / 12))
    _t(d, (640, 120), "IMPLIZITES WISSEN", 70, GOLD, a=a)
    _t(d, (640, 200), "können ≠ erklären", 44, WHITE, a=a)
    return img


def frame(tl, s, f):
    i = s["i"]
    if s["set"] != "studio":
        return None
    return {4: zeitlupe_kalle, 5: bahnen_vergleich, 7: wissen}.get(i, lambda s_, f_: None)(s, f)
