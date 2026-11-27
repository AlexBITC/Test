"""screen_dashboard: modernes Finanz-Dashboard im Dark-Look (Pillow), 1280x720, mit Zustaenden pro Aufbaustufe.

Wiederverwendbar: render(zustand) liefert ein RGBA-Bild. Zustand (alle Felder optional, Werte 0..1 = Einblendfortschritt):
    zaehler      Zahl (0..1200) oder None      Zaehler 'Buchungen' (Aufbaustufe Szene 4)
    ring         0..1                          Ring-Diagramm, fuenf Segmente wachsen nacheinander ein
    ring_gross   bool                          Ring gross mit allen Namen (Analyse) statt kompakt (fertiges Dashboard)
    karte        0..1                          Karte 'GELDFRESSER' (leere Zeilen mit rotem Punkt)
    zeilen       [0..1, 0..1, 0..1]            Zeile gefuellt (Symbol, Name, Betrag)
    kacheln      0..1                          zwei grosse Kacheln (UNNOETIG / ERSPARNIS)
    rot_puls     0..1                          rote Kachel pulsiert
    haken        [0..1, 0..1, 0..1]            Knopf 'Kuendigen' -> gruenes Haekchen 'Kuendigung vorbereitet'
    ersparnis    Zahl oder None                Ersparnis-Kachel gross (Szene 12), zaehlt hoch
    rechnung     0..1                          '138 € × 12' ueber der Ersparnis
Nur Zahlen, die gesprochen werden (Ausnahme: 138 € × 12 und 1.656 €).

upload_ablage(t, dateien) liefert die gestrichelte Ablageflaeche mit fallenden Dateien und Ladebalken.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
FONTS = Path(__file__).resolve().parent.parent / "fonts"
BG = (21, 23, 29)
CARD = (32, 35, 43)
CARD2 = (40, 44, 54)
LINE = (58, 62, 74)
TEXT = (238, 240, 245)
MUTED = (150, 156, 172)
TURQ = (46, 230, 214)
GREEN = (61, 220, 132)
GREEN_BG = (22, 64, 46)
RED = (255, 77, 90)
RED_BG = (74, 26, 34)
SEG = [("Mehl & Zutaten", (242, 180, 90)), ("Personal", (107, 85, 201)), ("Energie", (255, 225, 77)),
       ("Miete", (46, 140, 220)), ("Abos & Verträge", (46, 230, 214))]
ZEILEN = [("kaffee", "Kaffee-Miete", "49 €/Monat · seit 2022"),
          ("kasse", "Kassenprogramm doppelt", "29 €/Monat"),
          ("strom", "Strom, Altvertrag", "60 €/Monat")]
_F = {}


def font(size, weight="Bold"):
    key = (size, weight)
    if key not in _F:
        _F[key] = ImageFont.truetype(str(FONTS / f"Inter-{weight}.otf"), int(size))
    return _F[key]


def c01(t):
    return max(0.0, min(1.0, t))


def eo(t):
    t = c01(t)
    return 1 - (1 - t) ** 3


def fmt(v):
    return f"{int(round(v)):,}".replace(",", ".")


def _alpha(col, a):
    return tuple(col[:3]) + (int(255 * c01(a)),)


def _card(img, box, fill=CARD, a=1.0, r=26, outline=None, ow=3, shadow=True):
    if a <= 0:
        return
    x0, y0, x1, y1 = box
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((x0 + 4, y0 + 10, x1 + 4, y1 + 14), r, fill=(0, 0, 0, int(120 * a)))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(box, r, fill=_alpha(fill, a), outline=_alpha(outline, a) if outline else None,
                                         width=ow)
    img.alpha_composite(ov)


def _text(img, xy, s, size, col, weight="Bold", a=1.0, anchor="lm"):
    if a <= 0:
        return
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).text(xy, s, font=font(size, weight), fill=_alpha(col, a), anchor=anchor)
    img.alpha_composite(ov)


def _fit(s, size, maxw, weight="Bold", min_size=30):
    while size > min_size and font(size, weight).getlength(s) > maxw:
        size -= 1
    return size


def byte_icon(d, cx, cy, r):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=TURQ)
    d.ellipse((cx - r * 0.72, cy - r * 0.72, cx + r * 0.72, cy + r * 0.72), fill=(20, 18, 40))
    for sx in (-1, 1):
        d.ellipse((cx + sx * r * 0.3 - r * 0.13, cy - r * 0.2, cx + sx * r * 0.3 + r * 0.13, cy + r * 0.06), fill=TURQ)
    d.line([(cx + r * 0.1, cy - r), (cx + r * 0.1, cy - r * 1.35)], fill=(170, 176, 190), width=3)
    d.ellipse((cx + r * 0.1 - 5, cy - r * 1.35 - 5, cx + r * 0.1 + 5, cy - r * 1.35 + 5), fill=(255, 225, 77))


def _symbol(d, kind, cx, cy, r, col=TEXT):
    """Einfache Linien-Symbole: Kaffeemaschine, Kassenprogramm, Blitz (Strom)."""
    w = max(3, int(r * 0.12))
    if kind == "kaffee":
        d.rounded_rectangle((cx - r * 0.5, cy - r * 0.6, cx + r * 0.5, cy + r * 0.55), 5, outline=col, width=w)
        d.rectangle((cx - r * 0.5, cy - r * 0.6, cx + r * 0.5, cy - r * 0.3), fill=col)
        d.rounded_rectangle((cx - r * 0.22, cy + r * 0.05, cx + r * 0.22, cy + r * 0.45), 4, outline=col, width=w)
    elif kind == "kasse":
        d.rounded_rectangle((cx - r * 0.6, cy - r * 0.45, cx + r * 0.6, cy + r * 0.35), 5, outline=col, width=w)
        d.line([(cx - r * 0.3, cy + r * 0.6), (cx + r * 0.3, cy + r * 0.6)], fill=col, width=w)
        d.line([(cx, cy + r * 0.35), (cx, cy + r * 0.6)], fill=col, width=w)
        d.text((cx, cy - r * 0.05), "2×", font=font(int(r * 0.55), "ExtraBold"), fill=col, anchor="mm")
    elif kind == "strom":
        pts = [(cx + r * 0.1, cy - r * 0.7), (cx - r * 0.4, cy + r * 0.1), (cx, cy + r * 0.1), (cx - r * 0.1, cy + r * 0.7),
               (cx + r * 0.45, cy - r * 0.15), (cx + r * 0.05, cy - r * 0.15)]
        d.polygon(pts, fill=col)


def _check(d, cx, cy, s, col, t, w=None):
    if t <= 0:
        return
    pts = [(cx - s * 0.5, cy), (cx - s * 0.15, cy + s * 0.35), (cx + s * 0.55, cy - s * 0.4)]
    l1, l2 = math.dist(pts[0], pts[1]), math.dist(pts[1], pts[2])
    tot = (l1 + l2) * c01(t)
    w = w or int(s * 0.18)
    if tot <= l1:
        p = (pts[0][0] + (pts[1][0] - pts[0][0]) * tot / l1, pts[0][1] + (pts[1][1] - pts[0][1]) * tot / l1)
        d.line([pts[0], p], fill=col, width=w, joint="curve")
    else:
        k = (tot - l1) / l2
        p = (pts[1][0] + (pts[2][0] - pts[1][0]) * k, pts[1][1] + (pts[2][1] - pts[1][1]) * k)
        d.line([pts[0], pts[1], p], fill=col, width=w, joint="curve")


def _ring(img, cx, cy, ro, ri, t, rot_rand=True, sep=3):
    """Fuenf Segmente wachsen nacheinander ein (t 0..1). Anteile fest (keine Betraege im Bild)."""
    shares = [0.34, 0.27, 0.14, 0.15, 0.10]
    d = ImageDraw.Draw(img)
    a0 = -90.0
    n = len(shares)
    for k, (sh, (name, col)) in enumerate(zip(shares, SEG)):
        tk = eo((t * n - k) / 1.0)
        if tk > 0:
            a1 = a0 + 360 * sh * tk
            d.pieslice((cx - ro, cy - ro, cx + ro, cy + ro), a0 + sep / 2, a1 - sep / 2, fill=col)
            if k == 4 and rot_rand:
                d.arc((cx - ro - 7, cy - ro - 7, cx + ro + 7, cy + ro + 7), a0, a1, fill=RED, width=7)
        a0 += 360 * sh
    d.ellipse((cx - ri, cy - ri, cx + ri, cy + ri), fill=CARD)


def _legend(img, x, y, size, step, t, highlight=True):
    for k, (name, col) in enumerate(SEG):
        a = eo((t * 5 - k) / 1.0)
        if a <= 0:
            continue
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((x, y + k * step - size * 0.32, x + size * 0.64, y + k * step + size * 0.32), 5,
                            fill=_alpha(col, a))
        c = RED if (k == 4 and highlight) else TEXT
        _text(img, (x + size * 0.95, y + k * step), name, size, c, "SemiBold" if k < 4 else "Bold", a)


def _header(img, z):
    d = ImageDraw.Draw(img)
    _text(img, (40, 44), "Kalles Ausgaben", 40, TEXT, "ExtraBold")
    if z.get("zaehler") is not None and not z.get("kacheln"):
        pass
    byte_icon(d, W - 58, 46, 22)


def _zeile(img, k, box, fill_t, haken_t, knopf=True):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    cy = (y0 + y1) / 2
    kind, name, sub = ZEILEN[k]
    # Symbol bzw. roter Punkt (leer)
    if fill_t <= 0:
        r = 16 + 3 * math.sin(k)
        d.ellipse((x0 + 44 - r, cy - r, x0 + 44 + r, cy + r), fill=RED)
        d.rounded_rectangle((x0 + 92, cy - 30, x0 + 420, cy - 6), 10, fill=CARD2)
        d.rounded_rectangle((x0 + 92, cy + 10, x0 + 300, cy + 30), 10, fill=CARD2)
        return
    a = eo(fill_t)
    d.ellipse((x0 + 12, cy - 32, x0 + 76, cy + 32), fill=_alpha(RED_BG if haken_t <= 0 else GREEN_BG, 1))
    _symbol(d, kind, x0 + 44, cy, 30, RED if haken_t <= 0 else GREEN)
    bx0 = x1 - 236 if knopf else x1
    nsz = _fit(name, 44, bx0 - (x0 + 96) - 12, "Bold", 34)
    _text(img, (x0 + 96 - 20 * (1 - a), cy - 22), name, nsz, TEXT, "Bold", a)
    _text(img, (x0 + 96 - 20 * (1 - a), cy + 24), sub, 36, (255, 140, 148), "SemiBold", a)
    # Knopf
    if not knopf:
        return
    if haken_t <= 0:
        d.rounded_rectangle((bx0, cy - 34, x1 - 16, cy + 34), 18, fill=_alpha(RED, a))
        _text(img, ((bx0 + x1 - 16) / 2, cy), "Kündigen", 34, (255, 255, 255), "Bold", a, anchor="mm")
    else:
        g = eo(haken_t * 2)
        d.rounded_rectangle((bx0, cy - 40, x1 - 16, cy + 40), 18, fill=_alpha(GREEN, g))
        _check(d, bx0 + 38, cy + 2, 40, (255, 255, 255), haken_t * 1.6, w=8)
        _text(img, (bx0 + 70, cy - 15), "Kündigung", 27, (12, 40, 26), "Bold", g)
        _text(img, (bx0 + 70, cy + 17), "vorbereitet", 27, (12, 40, 26), "Bold", g)


def render(z):
    img = Image.new("RGBA", (W, H), BG + (255,))
    _header(img, z)
    # ---------------------------------------------------------------- Ersparnis gross (Szene 12)
    if z.get("ersparnis") is not None:
        _card(img, (140, 120, W - 140, 660), GREEN_BG, 1.0, r=40, outline=GREEN, ow=5)
        _text(img, (W / 2, 205), "ERSPARNIS / JAHR", 52, GREEN, "Bold", anchor="mm")
        ra = eo(z.get("rechnung", 1.0))
        _text(img, (W / 2, 300 - 20 * (1 - ra)), "138 € × 12", 64, TEXT, "Bold", ra, anchor="mm")
        v = z["ersparnis"]
        pk = 1 + 0.06 * z.get("ersparnis_peak", 0.0)
        _text(img, (W / 2, 470), f"{fmt(v)} €", int(190 * pk), (255, 255, 255), "ExtraBold", anchor="mm")
        return img
    voll = z.get("kacheln", 0) > 0
    # ---------------------------------------------------------------- Analyse (Szene 4-8): Zaehler + Ring gross
    if not voll:
        top = 92
        if z.get("zaehler") is not None:
            _card(img, (30, top, 500, 330), CARD)
            _text(img, (62, top + 52), "BUCHUNGEN", 30, MUTED, "Bold")
            _text(img, (62, top + 128), fmt(z["zaehler"]), 112, TEXT, "ExtraBold")
            _text(img, (62, top + 206), "sortiert", 32, TURQ, "SemiBold", c01(z["zaehler"] / 1200))
        if z.get("ring", 0) > 0:
            gx = 520 if z.get("zaehler") is not None else 30
            if z.get("karte", 0) <= 0:
                _card(img, (gx, top, W - 30, H - 22), CARD)
                cx, cy = gx + 200, top + 300
                _ring(img, cx, cy, 175, 104, z["ring"])
                _legend(img, gx + 410, top + 125, 34, 84, z["ring"])
            else:
                _card(img, (30, 350, 500, H - 22), CARD)
                _ring(img, 124, 525, 86, 52, z["ring"])
                _legend(img, 226, 438, 22, 44, z["ring"], highlight=True)
        if z.get("karte", 0) > 0:
            ka = eo(z["karte"])
            _card(img, (520, top, W - 30, H - 22), CARD, ka)
            _text(img, (552, top + 50), "GELDFRESSER", 36, RED, "ExtraBold", ka)
            for k in range(3):
                y0 = top + 92 + k * 172
                _zeile(img, k, (536, y0, W - 46, y0 + 160), (z.get("zeilen") or [0, 0, 0])[k], 0, knopf=False)
                if k < 2:
                    ImageDraw.Draw(img).line([(552, y0 + 166), (W - 62, y0 + 166)], fill=LINE, width=2)
        return img
    # ---------------------------------------------------------------- Fertiges Dashboard (ab Szene 9)
    ka = eo(z["kacheln"])
    rp = z.get("rot_puls", 0.0)
    ty0, ty1 = 86, 246
    grow = 10 * rp
    _card(img, (24 - grow, ty0 - grow, 628 + grow, ty1 + grow), RED_BG, ka, r=28, outline=RED, ow=4 + int(4 * rp))
    _text(img, (56, ty0 + 40), "UNNÖTIG", 32, RED, "Bold", ka)
    _text(img, (56, ty0 + 112), "138 €", 104, (255, 255, 255), "ExtraBold", ka)
    _text(img, (56 + font(104, "ExtraBold").getlength("138 € "), ty0 + 124), "/ Monat", 44, (255, 170, 176), "Bold", ka)
    _card(img, (652, ty0, W - 24, ty1), GREEN_BG, ka, r=28, outline=GREEN, ow=4)
    _text(img, (684, ty0 + 40), "ERSPARNIS / JAHR", 32, GREEN, "Bold", ka)
    _text(img, (684, ty0 + 112), "1.656 €", 104, (255, 255, 255), "ExtraBold", ka)
    # Ring kompakt
    _card(img, (24, 262, 444, H - 14), CARD)
    _text(img, (52, 300), "KATEGORIEN", 26, MUTED, "Bold")
    _ring(img, 118, 505, 86, 52, 1.0)
    _legend(img, 222, 418, 22, 44, 1.0)
    # Geldfresser
    _card(img, (458, 262, W - 24, H - 14), CARD)
    _text(img, (488, 300), "GELDFRESSER", 32, RED, "ExtraBold")
    hk = z.get("haken") or [0, 0, 0]
    for k in range(3):
        y0 = 328 + k * 126
        _zeile(img, k, (470, y0, W - 36, y0 + 120), 1.0, hk[k])
        if k < 2:
            ImageDraw.Draw(img).line([(488, y0 + 123), (W - 52, y0 + 123)], fill=LINE, width=2)
    return img


def upload_ablage(t, dateien=6):
    """Gestrichelte Ablageflaeche 'Hier ablegen', Dateien fallen hinein, Ladebalken fuellt sich (t 0..1)."""
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    _text(img, (40, 44), "Kontoauszüge hochladen", 40, TEXT, "ExtraBold")
    byte_icon(d, W - 58, 46, 22)
    x0, y0, x1, y1 = 120, 110, W - 120, 560
    act = c01(t * 3)
    col = TURQ if act > 0 else (90, 96, 112)
    d.rounded_rectangle((x0, y0, x1, y1), 34, fill=(26, 40, 46) if act > 0 else CARD)
    dash, gap = 26, 16
    per = 2 * ((x1 - x0) + (y1 - y0))
    s = 0.0
    while s < per:
        for a_, b_ in ((s, min(s + dash, per)),):
            pts = []
            for u in (a_, b_):
                if u < x1 - x0:
                    pts.append((x0 + u, y0))
                elif u < (x1 - x0) + (y1 - y0):
                    pts.append((x1, y0 + u - (x1 - x0)))
                elif u < 2 * (x1 - x0) + (y1 - y0):
                    pts.append((x1 - (u - (x1 - x0) - (y1 - y0)), y1))
                else:
                    pts.append((x0, y1 - (u - 2 * (x1 - x0) - (y1 - y0))))
            d.line(pts, fill=col, width=6)
        s += dash + gap
    # Pfeil + Text
    cx = W / 2
    d.polygon([(cx - 40, 400), (cx + 40, 400), (cx, 450)], fill=col)
    d.rectangle((cx - 14, 350, cx + 14, 402), fill=col)
    _text(img, (cx, 505), "Hier ablegen", 72, TEXT, "ExtraBold", anchor="mm")
    # fallende Dateien
    for k in range(dateien):
        tk = c01(t * 1.6 - k * 0.1)
        if 0 < tk < 1:
            fx = x0 + 160 + k * ((x1 - x0 - 320) / max(1, dateien - 1))
            fy = y0 - 60 + 280 * eo(tk)
            a = 1 - c01((tk - 0.75) / 0.25)
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            od.rounded_rectangle((fx - 40, fy - 52, fx + 40, fy + 52), 8, fill=(245, 241, 232, int(255 * a)))
            for j in range(4):
                od.line([(fx - 26, fy - 28 + j * 16), (fx + 26 - 10 * (j % 2), fy - 28 + j * 16)],
                        fill=(120, 126, 140, int(255 * a)), width=5)
            img.alpha_composite(ov)
    # Ladebalken
    p = c01(t)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((120, 600, W - 120, 640), 20, fill=CARD2)
    if p > 0:
        d.rounded_rectangle((120, 600, 120 + (W - 240) * p, 640), 20, fill=GREEN if p >= 1 else TURQ)
    _text(img, (W / 2, 682), "Fertig" if p >= 1 else f"{int(p * 100)} %", 32, GREEN if p >= 1 else MUTED, "Bold",
          anchor="mm")
    return img
