"""Bildschirm-Ebenen fuer 'Bytes Nachtschicht' (folge-08-nachtschicht), 1280x720 pro Frame.

Wird von engine/overlays.screen_frame geladen. Studio-Screen (Szene 3-5) und Laptop an der Theke (Szene 6-7).
Inhalte: bewerber_37_zu_3, preisvergleich_brezel, sterne_vergleich, bestellungen_62.
Zahlen = Sprechtext: 37, 3, 1,10, 1,20 (Kalles Preis zum Vergleich), 4,8, 4,1, 62.
"""
import math

from PIL import Image, ImageDraw

from engine.overlays import font, ease_out, clamp01, ease_out_back

SW, SH = 1280, 720
BG = (20, 18, 40)
PANEL = (36, 32, 74)
TURQ = (46, 230, 214)
GOLD = (242, 180, 90)
GREEN = (61, 220, 132)
GREY = (150, 148, 180)
WHITE = (255, 255, 255)
RED = (255, 77, 90)


def _wf(s, core, default=None):
    for w in s["words"]:
        if w["w"].strip(".,!?:…").lower() == core.lower():
            return w["f0"]
    return default if default is not None else s["f0"] + 6


def _t(d, xy, s, size, col, anchor="mm", a=1.0):
    d.text(xy, s, font=font(size), fill=tuple(col) + (int(255 * clamp01(a)),), anchor=anchor)


def _stern(d, cx, cy, r, col):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=col)


def _check(d, cx, cy, s, col, w=10):
    d.line([(cx - s * 0.5, cy), (cx - s * 0.15, cy + s * 0.35), (cx + s * 0.55, cy - s * 0.4)], fill=col, width=w, joint="curve")


def _base():
    img = Image.new("RGBA", (SW, SH), BG + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, SW, 160):
        d.line([(x, 0), (x, SH)], fill=(46, 230, 214, 14), width=2)
    for y in range(0, SH, 160):
        d.line([(0, y), (SW, y)], fill=(46, 230, 214, 14), width=2)
    return img


def _profil(d, cx, cy, r, col):
    d.ellipse((cx - r * 0.45, cy - r * 0.95, cx + r * 0.45, cy - r * 0.05), fill=col)
    d.pieslice((cx - r * 0.85, cy - r * 0.05, cx + r * 0.85, cy + r * 1.4), 180, 360, fill=col)


def bewerber(s, f):
    img = _base()
    d = ImageDraw.Draw(img, "RGBA")
    f37 = _wf(s, "37")
    f3 = _wf(s, "drei")
    a = ease_out((f - f37 + 4) / 8)
    _t(d, (SW / 2 - 150, 170), "37", 170, WHITE, a=a)
    b = ease_out((f - f3 + 6) / 8)
    if b > 0:
        cx, cy = SW / 2 + 10, 175
        d.rectangle((cx - 55, cy - 12, cx + 20, cy + 12), fill=TURQ + (int(255 * b),))
        d.polygon([(cx + 15, cy - 38), (cx + 65, cy), (cx + 15, cy + 38)], fill=TURQ + (int(255 * b),))
    _t(d, (SW / 2 + 170, 170), "3", 170, GOLD, a=b)
    for k, lab in enumerate(["Bäcker-Geselle", "Verkauf", "Aushilfe"]):
        t = ease_out_back(clamp01((f - f3 - 2 - 6 * k) / 8), 1.6)
        if t <= 0:
            continue
        cx = 240 + k * 400
        d.rounded_rectangle((cx - 170, 330, cx + 170, 680), 30, fill=PANEL + (255,), outline=GOLD + (255,), width=5)
        _profil(d, cx, 440, 80 * t, GOLD + (255,))
        _t(d, (cx, 610), lab, 52 if len(lab) < 12 else 42, WHITE, a=t)
        _check(d, cx + 120, 370, 50, GREEN, 9)
    return img


def preisvergleich(s, f):
    img = _base()
    d = ImageDraw.Draw(img, "RGBA")
    f110 = _wf(s, "1,10.")
    for k, (lab, preis, col, t0) in enumerate([("Kalle", "1,20 €", WHITE, s["f0"] + 6), ("Marktplatz", "1,10 €", RED, f110 - 4)]):
        a = ease_out((f - t0) / 8)
        if a <= 0:
            continue
        x0 = 90 + k * 570
        d.rounded_rectangle((x0, 140 - 30 * (1 - a), x0 + 530, 600 - 30 * (1 - a)), 34, fill=PANEL + (int(255 * a),),
                            outline=(col if k else TURQ) + (int(255 * a),), width=5)
        _t(d, (x0 + 265, 230), lab, 72, GREY if k == 0 else WHITE, a=a)
        pk = 1 + 0.1 * math.sin(math.pi * clamp01((f - f110) / 8)) if (k == 1 and f >= f110) else 1
        _t(d, (x0 + 265, 420), preis, int(150 * pk), col, a=a)
        _t(d, (x0 + 265, 545), "pro Brezel", 46, GREY, a=a)
    return img


def sterne(s, f):
    img = _base()
    d = ImageDraw.Draw(img, "RGBA")
    f48 = _wf(s, "4,8")
    f41 = _wf(s, "4,1.")
    for k, (lab, wert, col, t0) in enumerate([("Kalle", "4,8", GREEN, f48 - 4), ("Marktplatz", "4,1", GREY, f41 - 4)]):
        a = ease_out((f - t0) / 8)
        if a <= 0:
            continue
        x0 = 90 + k * 570
        d.rounded_rectangle((x0, 140, x0 + 530, 600), 34, fill=PANEL + (int(255 * a),), outline=col + (int(255 * a),), width=5)
        _t(d, (x0 + 265, 225), lab, 70, WHITE, a=a)
        _t(d, (x0 + 220, 400), wert, 170, col, a=a)
        _stern(d, x0 + 420, 395, 62, col + (int(255 * a),))
    return img


def bestellungen(s, f):
    img = _base()
    d = ImageDraw.Draw(img, "RGBA")
    f62 = _wf(s, "62")
    n = int(round(62 * ease_out(clamp01((f - s["f0"] - 2) / max(1, f62 - s["f0"] + 30)))))
    done = n >= 62
    _t(d, (SW / 2, 130), "BESTELLUNGEN HEUTE", 60, GREY)
    pk = 1 + 0.08 * math.sin(math.pi * clamp01((f - f62 - 32) / 8)) if done else 1
    _t(d, (SW / 2 - 60, 380), f"{n}/62", int(200 * pk), GREEN if done else WHITE)
    if done:
        _check(d, SW / 2 + 380, 380, 140, GREEN, 22)
        _t(d, (SW / 2, 600), "alle bestätigt", 64, GREEN)
    return img


def frame(tl, s, f):
    i = s["i"]
    if s["set"] == "studio":
        return {2: bewerber, 3: preisvergleich, 4: sterne}.get(i, lambda s, f: _base())(s, f)
    if s["set"] == "theke" and i in (5, 6):
        return bestellungen(tl["scenes"][5], f)
    return None
