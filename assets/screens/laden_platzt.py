"""Bildschirm-Inhalte fuer 'Ein Video – und der Laden platzt' (folge-13-laden-platzt), 1280x720.

Die Bildfolge liegt auf dem Studio-Screen und (per UV, siehe Regie) auf den Laptop-Displays in Theke und Buero.
Keine Logos, keine Markennamen. Zahlen = Sprechtext: Szene 6 '10 min → 15 s', Szene 8 Uhr '18:59' -> '19:00',
Szene 9 Zaehler wie ein Spielautomat bis '50.000' Aufrufe, Szene 10 '50.000 Aufrufe', Szene 12 Haken 'Mehl bestellt'.
Texte poppen mit leichtem Ueberschwingen, Ziffern klappen um.
"""
import math
import random

from PIL import Image, ImageDraw

from engine.overlays import font, clamp01, ease_out, ease_out_back

SW, SH = 1280, 720
BG = (18, 16, 31)
TURQ = (46, 230, 214)
GRUEN = (61, 220, 132)
ROT = (255, 77, 90)
GOLD = (242, 180, 90)
WEISS = (255, 255, 255)
PINK = (255, 92, 138)


def _bg(col=BG, raster=(28, 26, 48)):
    img = Image.new("RGB", (SW, SH), col)
    d = ImageDraw.Draw(img)
    for x in range(0, SW, 64):
        d.line([(x, 0), (x, SH)], fill=raster, width=1)
    for y in range(0, SH, 64):
        d.line([(0, y), (SW, y)], fill=raster, width=1)
    return img


def _pop_text(img, xy, s, size, col, t, dur=8, stroke=(10, 8, 20)):
    """Text poppt mit Ueberschwingen auf (t in Frames seit Beginn)."""
    if t < 0:
        return
    k = ease_out_back(clamp01(t / dur), 2.4)
    sz = max(6, int(size * (0.4 + 0.6 * k)))
    d = ImageDraw.Draw(img)
    d.text(xy, s, font=font(sz), fill=col, anchor="mm", stroke_width=max(1, sz // 18), stroke_fill=stroke)


def _herz(d, cx, cy, r, col):
    d.ellipse((cx - r, cy - r, cx, cy), fill=col)
    d.ellipse((cx, cy - r, cx + r, cy), fill=col)
    d.polygon([(cx - r, cy - r * 0.45), (cx + r, cy - r * 0.45), (cx, cy + r)], fill=col)


def _brezel(d, cx, cy, r, col=(201, 122, 62)):
    """Brezel: grosser unterer Bogen, zwei Schlaufen oben, gekreuzte Arme."""
    w = max(6, int(r * 0.26))
    d.arc((cx - r, cy - r * 0.55, cx + r, cy + r * 0.95), 200, 340 + 360, fill=col, width=w)
    d.ellipse((cx - r * 0.85, cy - r * 0.45, cx - r * 0.05, cy + r * 0.45), outline=col, width=w)
    d.ellipse((cx + r * 0.05, cy - r * 0.45, cx + r * 0.85, cy + r * 0.45), outline=col, width=w)
    d.line([(cx - r * 0.35, cy - r * 0.1), (cx + r * 0.2, cy + r * 0.75)], fill=col, width=w)
    d.line([(cx + r * 0.35, cy - r * 0.1), (cx - r * 0.2, cy + r * 0.75)], fill=col, width=w)


def _video(img, f, t):
    """Laptop in der Theke: Brezel-Video laeuft, Herzen steigen (ohne Zahlen)."""
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((420, 40, 860, 680), 30, fill=(243, 217, 177))
    _brezel(d, 640, 330 + int(12 * math.sin(f * 0.25)), 120)
    d.rounded_rectangle((460, 630, 820, 646), 8, fill=(142, 122, 102))
    d.rounded_rectangle((460, 630, 460 + int(360 * ((f % 90) / 90)), 646), 8, fill=ROT)
    r = random.Random(4)
    for q in range(7):
        ph = r.uniform(0, 1)
        u = ((t / 50.0) + ph) % 1.0
        x = 930 + r.randint(-40, 160) + int(20 * math.sin(f * 0.1 + q))
        _herz(d, x, int(660 - 560 * u), int(26 * (1 - 0.4 * u)), PINK)


def _slot(img, f, f_a, f_b, ziel=50000, y=330):
    """Zaehler wie ein Spielautomat: fuenf Walzen, rollen von links nach rechts aus (Ueberschwingen beim Stopp)."""
    d = ImageDraw.Draw(img)
    ziff = f"{ziel:05d}"
    x0, wz, hz = 190, 150, 220
    d.rounded_rectangle((x0 - 40, y - hz // 2 - 40, x0 + 5 * wz + 90 + 40, y + hz // 2 + 40), 36, fill=(150, 30, 46))
    for q in range(5):
        x = x0 + q * wz + (40 if q >= 2 else 0)
        stop = f_a + (f_b - f_a) * (0.45 + 0.55 * q / 4)
        d.rounded_rectangle((x, y - hz // 2, x + wz - 16, y + hz // 2), 18, fill=(250, 246, 236))
        walze = Image.new("RGBA", (wz - 16, hz), (0, 0, 0, 0))
        dw = ImageDraw.Draw(walze)
        cx_, cy_ = (wz - 16) / 2, hz / 2
        if f < stop:
            v = (f - f_a) * 0.9 + q * 3.3                   # laufende Walze: Ziffern rollen durch (im Fenster beschnitten)
            for j in range(-1, 2):
                z = int(math.floor(v) + j) % 10
                off = (v % 1.0 - j) * hz * 0.8
                dw.text((cx_, cy_ - off), str(z), font=font(150), fill=(60, 50, 80, 255), anchor="mm")
        else:
            k = ease_out_back(clamp01((f - stop) / 6), 3.0)
            dw.text((cx_, cy_ + (1 - k) * 40), ziff[q], font=font(160), fill=(20, 18, 40, 255), anchor="mm")
        img.paste(walze, (int(x), int(y - hz // 2)), walze)
        if q == 1:
            d.ellipse((x + wz + 2, y + 70, x + wz + 26, y + 94), fill=GOLD)
    for sy in (-1, 1):
        d.rectangle((x0 - 20, y + sy * (hz // 2 + 6) - 6, x0 + 5 * wz + 70, y + sy * (hz // 2 + 6) + 6), fill=(90, 14, 26))
    if f >= f_b:
        _pop_text(img, (SW / 2, 620), "Aufrufe", 96, GOLD, f - f_b, stroke=(40, 10, 20))
    else:
        d.text((SW / 2, 620), "Aufrufe", font=font(80), fill=(200, 170, 120), anchor="mm")


def _uhr(img, f, f_flip, y=360):
    """Digitaluhr 18:59 -> 19:00, Ziffern klappen um (obere Haelfte faellt)."""
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((240, y - 170, 1040, y + 170), 40, fill=(26, 22, 48))
    alt, neu = "18:59", "19:00"
    k = clamp01((f - f_flip) / 6)
    for q, (a, n) in enumerate(zip(alt, neu)):
        x = 330 + q * 155
        if a == ":":
            if (f // 15) % 2 == 0 or f >= f_flip:
                d.ellipse((x - 12, y - 60, x + 12, y - 36), fill=TURQ)
                d.ellipse((x - 12, y + 36, x + 12, y + 60), fill=TURQ)
            continue
        d.rounded_rectangle((x - 65, y - 120, x + 65, y + 120), 16, fill=(44, 40, 76))
        if a == n or f < f_flip:
            z, sq = a, 1.0
        else:                                      # erste Haelfte: alte Ziffer klappt weg, zweite: neue klappt auf
            z = a if k < 0.5 else n
            sq = abs(math.cos(math.pi * k))
        txt = Image.new("RGBA", (130, 240), (0, 0, 0, 0))
        ImageDraw.Draw(txt).text((65, 120), z, font=font(190), fill=(*TURQ, 255) if f >= f_flip else (*WEISS, 255), anchor="mm")
        if sq < 0.999:
            h = max(2, int(240 * sq))
            txt = txt.resize((130, h))
            img.paste(txt, (x - 65, y - h // 2), txt)
        else:
            img.paste(txt, (x - 65, y - 120), txt)
        d.line([(x - 65, y), (x + 65, y)], fill=(18, 16, 31), width=4)


def frame(tl, szene, f):
    i, f0, f1 = szene["i"], szene["f0"], szene["f1"]
    t = f - f0
    n = f1 - f0

    def ts(sek):                                   # wie t() in der Regie
        return int(min(sek * 30 * max(1.0, n / 135.0), n - 8))

    if i in (0, 10):                               # Theke heute: Video laeuft, Herzen
        img = _bg((40, 30, 52), (52, 42, 66))
        _video(img, f, t)
        return img
    if i == 1:                                     # gestern: grau, nichts los
        img = _bg((44, 44, 50), (52, 52, 58))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((420, 40, 860, 680), 30, fill=(70, 70, 78))
        if (f // 18) % 2 == 0:
            d.rectangle((630, 340, 650, 400), fill=(150, 150, 160))
        return img
    if i in (2, 3):                                # Byte ist aus dem Laptop: tuerkiser Nachglanz
        img = _bg()
        a = max(0.0, 1 - t / 24) if i == 2 else 0.0
        if a > 0:
            ov = Image.new("RGB", (SW, SH), TURQ)
            img = Image.blend(img, ov, 0.6 * a)
        return img
    if i == 4:                                     # Sucher: REC-Rahmen
        img = _bg((30, 26, 44))
        d = ImageDraw.Draw(img)
        for (x, y, sx, sy) in ((80, 60, 1, 1), (1200, 60, -1, 1), (80, 660, 1, -1), (1200, 660, -1, -1)):
            d.line([(x, y), (x + sx * 110, y)], fill=WEISS, width=8)
            d.line([(x, y), (x, y + sy * 110)], fill=WEISS, width=8)
        if (t // 9) % 2 == 0:
            d.ellipse((120, 100, 170, 150), fill=ROT)
        d.text((190, 125), "REC", font=font(56), fill=WEISS, anchor="lm")
        _brezel(d, 640, 380, 140)
        return img
    if i == 5:
        img = _bg()
        _pop_text(img, (SW / 2 - 300, SH / 2), "10 min", 150, TURQ, t - 8)
        _pop_text(img, (SW / 2 + 330, SH / 2), "15 s", 150, TURQ, t - 18)
        if t >= 12:                                # Pfeil (Schrift hat kein Pfeilzeichen) schiebt sich hinein
            k = ease_out_back(clamp01((t - 12) / 8), 2.0)
            d = ImageDraw.Draw(img)
            x0, x1, y = SW / 2 - 70, SW / 2 - 70 + 190 * k, SH / 2
            d.line([(x0, y), (x1, y)], fill=WEISS, width=22)
            d.polygon([(x1 + 30, y), (x1 - 22, y - 42), (x1 - 22, y + 42)], fill=WEISS)
        return img
    if i == 7:                                     # Buero abends: 18:59 -> 19:00
        img = _bg((20, 18, 40), (30, 28, 54))
        _uhr(img, f, f0 + 16)
        return img
    if i == 8:                                     # Buero morgens: Spielautomat bis 50.000
        img = _bg((26, 20, 44), (38, 30, 60))
        f_roll = f0 + ts(0.6)
        f_stop = f_roll + int(0.4 * (f1 - f_roll))
        _slot(img, f, f_roll, f_stop)
        return img
    if i == 9:
        img = _bg()
        _pop_text(img, (SW / 2, SH / 2), "50.000 Aufrufe", 150, GOLD, t - 6)
        return img
    if i == 11:                                    # gruener Haken 'Mehl bestellt'
        img = _bg((16, 40, 30), (24, 56, 42))
        d = ImageDraw.Draw(img)
        k = ease_out_back(clamp01((t - 8) / 8), 2.6)
        if t >= 8:
            r = int(170 * k)
            d.ellipse((SW / 2 - r, 300 - r, SW / 2 + r, 300 + r), fill=GRUEN)
            pts = [(SW / 2 - 80 * k, 300), (SW / 2 - 20 * k, 360 * 1), (SW / 2 + 90 * k, 230)]
            d.line(pts, fill=WEISS, width=max(4, int(34 * k)), joint="curve")
        _pop_text(img, (SW / 2, 590), "Mehl bestellt", 110, WEISS, t - 12)
        return img
    return None
