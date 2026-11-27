"""Bildschirm-Inhalte fuer 'Meine KI macht jetzt meinen Job' (folge-12-kalle-vermieter), Studio-Screen 1280x720.

Zahlen = Sprechtext: Szene 4 Countdown-Ring (3 Sekunden), Szene 5 '60 m² · 250.000 €', Szene 7 'Rate: 1.000 € im Monat',
Szene 9 '1.000 € − 750 € = 250 €', Szene 11 'Nachtsuche läuft …' mit pulsierendem Ladebalken. Texte poppen mit
leichtem Ueberschwingen auf, nichts erscheint starr.
"""
import math

from PIL import Image, ImageDraw

from engine.overlays import font, clamp01, ease_out_back

SW, SH = 1280, 720
BG = (18, 16, 31)
TURQ = (46, 230, 214)
GRUEN = (61, 220, 132)
ROT = (255, 77, 90)
GOLD = (242, 180, 90)
WEISS = (255, 255, 255)


def _bg(f):
    img = Image.new("RGB", (SW, SH), BG)
    d = ImageDraw.Draw(img)
    for x in range(0, SW, 64):
        d.line([(x, 0), (x, SH)], fill=(28, 26, 48), width=1)
    for y in range(0, SH, 64):
        d.line([(0, y), (SW, y)], fill=(28, 26, 48), width=1)
    return img


def _pop_text(img, xy, s, size, col, t):
    """Text poppt mit Ueberschwingen auf (t in Frames seit Beginn)."""
    if t < 0:
        return
    k = ease_out_back(clamp01(t / 8), 2.4)
    sz = max(6, int(size * (0.4 + 0.6 * k)))
    d = ImageDraw.Draw(img)
    d.text(xy, s, font=font(sz), fill=col, anchor="mm", stroke_width=max(1, sz // 18), stroke_fill=(10, 8, 20))


def frame(tl, szene, f):
    i, f0, f1 = szene["i"], szene["f0"], szene["f1"]
    t = f - f0
    if i == 3:                                   # Countdown-Ring: in 3 Sekunden voll
        img = _bg(f)
        d = ImageDraw.Draw(img)
        p = clamp01((t - 10) / 90)
        box = (SW / 2 - 200, SH / 2 - 200, SW / 2 + 200, SH / 2 + 200)
        d.ellipse(box, outline=(40, 60, 80), width=26)
        if p > 0:
            d.arc(box, -90, -90 + 360 * p, fill=TURQ, width=26)
        _pop_text(img, (SW / 2, SH / 2), "3 s", 150, WEISS if p < 1 else GRUEN, t - 6)
        return img
    if i == 4:
        img = _bg(f)
        _pop_text(img, (SW / 2, SH / 2), "60 m² · 250.000 €", 120, GOLD, t - 30)
        return img
    if i == 6:
        img = _bg(f)
        _pop_text(img, (SW / 2, SH / 2), "Rate: 1.000 € im Monat", 104, ROT, t - 60)
        return img
    if i == 8:
        img = _bg(f)
        _pop_text(img, (SW / 2 - 300, SH / 2), "1.000 €", 100, ROT, t - 6)
        _pop_text(img, (SW / 2 - 60, SH / 2), "−", 100, WEISS, t - 14)
        _pop_text(img, (SW / 2 + 150, SH / 2), "750 €", 100, GRUEN, t - 20)
        _pop_text(img, (SW / 2 + 330, SH / 2), "=", 100, WEISS, t - 28)
        _pop_text(img, (SW / 2 + 300, SH / 2 + 170), "250 €", 130, ROT, t - 36)
        return img
    if i == 10:
        img = _bg(f)
        d = ImageDraw.Draw(img)
        _pop_text(img, (SW / 2, SH / 2 - 80), "Nachtsuche läuft …", 92, TURQ, t - 4)
        x0, x1, y = 260, 1020, SH / 2 + 90
        d.rounded_rectangle((x0, y - 18, x1, y + 18), 18, fill=(30, 40, 60))
        u = (t % 45) / 45
        puls = 0.6 + 0.4 * math.sin(t * 0.3)
        col = tuple(int(c * puls) for c in TURQ)
        d.rounded_rectangle((x0, y - 18, x0 + (x1 - x0) * u, y + 18), 18, fill=col)
        return img
    return None
