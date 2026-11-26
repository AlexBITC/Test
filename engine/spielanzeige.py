"""Spielanzeige [GAME] (Engine 2.5), mit Pillow gezeichnet, Teil der 2D-Ebene (overlays.overlay_frame).

Die Regie liefert pro Frame einen Zustand (W.hud_fn(f) -> dict oder None), scene.export_anchors legt ihn in
anchors.json ("hud") ab. Alle Elemente sind optional; Startzeitpunkte sind absolute Frames ("f0"), daraus ergeben sich
die Animationen. Ziffern nur fuer 'TAG x', Uhrzeit, Mengen und Preise.

Layout (1080 x 1920, Safe Zones: oben Hook-Zone bis 520, rechts 160 px frei, unten 420 px frei):
  Obere Leiste      y 532-700   TAG x (64 px), Uhr mit Sonne/Mond (60 px), Geldleiste (gruen/rot, pulsiert in Gefahr),
                                5 Herzen, Mehlsack mit Fuellstand
  Facecam           x 60-384, y 716-1116 (Rahmen und LIVE-Punkt hier, das Bild setzt composite.py ein)
  Regler/Menge      x 404-920, y 724-834 rechts neben der Facecam (Preis mit Brezel-Symbol, Plus/Minus), 2. Reihe 846
  Aktionsleiste     y 1112-1240, 4 runde Knoepfe BACKEN, PREIS, EINKAUF, BAUEN (gedrueckter leuchtet kurz)
  Banner            faellt von oben auf y 340-500 (Text >= 80 px, Symbol, kurzes Wackeln)
  Erfolg            unten links ueber der Aktionsleiste (bei Facecam rechts daneben), mit Pokal
  Byte-Tipp         tuerkise Sprechblase mit Pfeil (auf Anker oder Bildpunkt)
  Mission           Schriftrolle mit Haken-Kaestchen (nur zu Beginn)
  PLEITE            abgedunkelte Welt (Lichtkegel auf Mini-Kalle), grosses rotes 'PLEITE', Knopf 'NOCHMAL'
  Level-up          goldener Strahlenkranz, 'FILIALE 2 FREIGESCHALTET', Konfetti
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFilter

try:
    from . import overlays as O
except ImportError:
    import overlays as O

X0, X1 = 60, 920
TOP_Y0, TOP_Y1 = 532, 700
FACECAM = (60, 716, 384, 1116)
AKTION_Y = 1162
REGLER_Y0, REGLER_Y1 = 724, 834
KNOEPFE = ["BACKEN", "PREIS", "EINKAUF", "BAUEN"]
TURQ, NAVY, GOLD, RED, GREEN, YELLOW, WHITE = O.TURQ, O.NAVY, O.GOLD, O.RED, O.GREEN, O.YELLOW, (255, 255, 255)
ROLLE = (246, 230, 196)
BRAUN = (110, 70, 40)


def _lay(img):
    return Image.new("RGBA", img.size, (0, 0, 0, 0))


def _rgba(c, a):
    return (*c[:3], max(0, min(255, int(255 * a))))


def _ein(f, f0, dur=7):
    return O.clamp01((f - f0) / dur)


def _alpha(f, el, dur=7, aus=6):
    a = _ein(f, el["f0"], dur)
    if el.get("f1") is not None:
        a = min(a, O.clamp01((el["f1"] - f) / aus))
    return a


# ------------------------------------------------------------------ Symbole
def herz(d, cx, cy, s, fill, outline=None):
    r = s * 0.28
    d.ellipse((cx - 2 * r, cy - 1.6 * r, cx, cy + 0.4 * r), fill=fill, outline=outline, width=3)
    d.ellipse((cx, cy - 1.6 * r, cx + 2 * r, cy + 0.4 * r), fill=fill, outline=outline, width=3)
    d.polygon([(cx - 1.95 * r, cy - 0.3 * r), (cx + 1.95 * r, cy - 0.3 * r), (cx, cy + 1.9 * r)], fill=fill)
    if outline:
        d.line([(cx - 1.95 * r, cy - 0.2 * r), (cx, cy + 1.9 * r), (cx + 1.95 * r, cy - 0.2 * r)], fill=outline, width=3)


def sonne(d, cx, cy, r, a=1.0):
    for k in range(8):
        w = k * math.pi / 4
        d.line([(cx + math.cos(w) * r * 1.3, cy + math.sin(w) * r * 1.3), (cx + math.cos(w) * r * 1.75, cy + math.sin(w) * r * 1.75)],
               fill=_rgba(YELLOW, a), width=5)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_rgba(YELLOW, a))


def mond(d, cx, cy, r, bg, a=1.0):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_rgba((240, 236, 200), a))
    d.ellipse((cx - r + r * 0.55, cy - r - r * 0.2, cx + r + r * 0.55, cy + r - r * 0.2), fill=_rgba(bg, a))


def muenze(d, cx, cy, r, a=1.0):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_rgba(GOLD, a), outline=_rgba((150, 96, 30), a), width=3)
    d.ellipse((cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6), outline=_rgba((255, 230, 150), a), width=3)


def sack(d, cx, cy, s, fuell, a=1.0):
    """Mehlsack (Breite ~s) mit Fuellstand 0..1 von unten."""
    x0, y0, x1, y1 = cx - s * 0.5, cy - s * 0.45, cx + s * 0.5, cy + s * 0.65
    d.rounded_rectangle((x0, y0, x1, y1), int(s * 0.22), fill=_rgba((90, 80, 110), a))
    if fuell > 0.01:
        yf = y1 - (y1 - y0) * min(1.0, fuell)
        d.rounded_rectangle((x0, max(y0, yf), x1, y1), int(s * 0.22), fill=_rgba((245, 232, 205), a))
    d.rounded_rectangle((x0, y0, x1, y1), int(s * 0.22), outline=_rgba(WHITE, a), width=3)
    d.polygon([(cx - s * 0.28, y0 + 2), (cx, y0 - s * 0.32), (cx + s * 0.28, y0 + 2)], fill=_rgba((245, 232, 205), a),
              outline=_rgba(WHITE, a))
    d.line([(cx - s * 0.2, y0 - 2), (cx + s * 0.2, y0 - 2)], fill=_rgba(BRAUN, a), width=4)


def brezel(d, cx, cy, s, a=1.0, col=(201, 128, 60)):
    w = max(3, int(s * 0.16))
    c = _rgba(col, a)
    d.arc((cx - s * 0.55, cy - s * 0.45, cx + s * 0.05, cy + s * 0.25), 120, 420, fill=c, width=w)
    d.arc((cx - s * 0.05, cy - s * 0.45, cx + s * 0.55, cy + s * 0.25), 120, 420, fill=c, width=w)
    d.arc((cx - s * 0.6, cy - s * 0.25, cx + s * 0.6, cy + s * 0.55), 200, 340, fill=c, width=w)


def wolke(d, cx, cy, s, a=1.0, col=(200, 210, 228), tropfen=True):
    c = _rgba(col, a)
    for dx, dy, r in ((-0.3, 0.05, 0.28), (0.0, -0.12, 0.36), (0.32, 0.04, 0.26)):
        d.ellipse((cx + (dx - r) * s, cy + (dy - r) * s, cx + (dx + r) * s, cy + (dy + r) * s), fill=c)
    d.rounded_rectangle((cx - 0.55 * s, cy - 0.02 * s, cx + 0.55 * s, cy + 0.28 * s), int(0.14 * s), fill=c)
    if tropfen:
        for k in range(3):
            x = cx + (-0.3 + 0.3 * k) * s
            d.line([(x, cy + 0.42 * s), (x - 0.08 * s, cy + 0.62 * s)], fill=_rgba((120, 190, 255), a), width=max(3, int(0.07 * s)))


def pokal(d, cx, cy, s, a=1.0):
    c, k = _rgba(GOLD, a), _rgba((160, 100, 30), a)
    d.pieslice((cx - s * 0.4, cy - s * 0.75, cx + s * 0.4, cy + s * 0.1), 0, 180, fill=c, outline=k, width=3)
    d.rectangle((cx - s * 0.4, cy - s * 0.4, cx + s * 0.4, cy - s * 0.32), fill=c)
    for sx in (-1, 1):
        d.arc((cx + sx * s * 0.42 - s * 0.18, cy - s * 0.38, cx + sx * s * 0.42 + s * 0.18, cy - s * 0.05), 0, 360, fill=c, width=5)
    d.rectangle((cx - s * 0.07, cy + s * 0.08, cx + s * 0.07, cy + s * 0.32), fill=c)
    d.rounded_rectangle((cx - s * 0.3, cy + s * 0.3, cx + s * 0.3, cy + s * 0.45), 4, fill=c, outline=k, width=2)


def knopf_symbol(d, name, cx, cy, s, col):
    c = col
    if name == "BACKEN":            # Ofen mit Flamme
        d.rounded_rectangle((cx - s * 0.5, cy - s * 0.42, cx + s * 0.5, cy + s * 0.42), int(s * 0.12), outline=c, width=5)
        d.rounded_rectangle((cx - s * 0.3, cy - s * 0.1, cx + s * 0.3, cy + s * 0.26), int(s * 0.06), fill=c)
        d.polygon([(cx - s * 0.12, cy - s * 0.18), (cx, cy - s * 0.38), (cx + s * 0.12, cy - s * 0.18)], fill=c)
    elif name == "PREIS":           # Preisschild
        d.polygon([(cx - s * 0.5, cy - s * 0.12), (cx - s * 0.18, cy - s * 0.45), (cx + s * 0.5, cy - s * 0.45),
                   (cx + s * 0.5, cy + s * 0.25), (cx - s * 0.18, cy + s * 0.25)], outline=c, width=5)
        d.ellipse((cx - s * 0.2, cy - s * 0.18, cx - s * 0.06, cy - s * 0.04), fill=c)
        d.line([(cx + s * 0.05, cy - s * 0.1), (cx + s * 0.36, cy - s * 0.1)], fill=c, width=5)
    elif name == "EINKAUF":         # Einkaufswagen
        d.line([(cx - s * 0.55, cy - s * 0.4), (cx - s * 0.38, cy - s * 0.4), (cx - s * 0.2, cy + s * 0.18), (cx + s * 0.38, cy + s * 0.18),
                (cx + s * 0.5, cy - s * 0.22), (cx - s * 0.3, cy - s * 0.22)], fill=c, width=5)
        for x in (-0.12, 0.3):
            d.ellipse((cx + x * s - s * 0.08, cy + s * 0.3, cx + x * s + s * 0.08, cy + s * 0.46), fill=c)
    elif name == "BAUEN":           # Haus mit Hammer
        d.polygon([(cx - s * 0.5, cy - s * 0.02), (cx, cy - s * 0.48), (cx + s * 0.5, cy - s * 0.02)], fill=c)
        d.rectangle((cx - s * 0.36, cy - s * 0.04, cx + s * 0.36, cy + s * 0.42), outline=c, width=5)
        d.rectangle((cx - s * 0.1, cy + s * 0.12, cx + s * 0.1, cy + s * 0.42), fill=c)


# ------------------------------------------------------------------ Elemente
def obere_leiste(img, f, t, a):
    O.card(img, (X0, TOP_Y0, X1, TOP_Y1), a, radius=30)
    lay = _lay(img)
    d = ImageDraw.Draw(lay)
    # Zeile 1: TAG x (links), Uhr mit Sonne/Mond (rechts)
    nacht = t.get("nacht", False)
    if nacht:
        mond(d, 640, 578, 24, (40, 36, 70), a)
    else:
        sonne(d, 640, 578, 19, a)
    # Zeile 2: Muenze + Geldleiste, Herzen, Mehlsack
    muenze(d, 104, 656, 22, a)
    gx0, gx1, gy = 138, 520, 656
    d.rounded_rectangle((gx0, gy - 17, gx1, gy + 17), 17, fill=_rgba((255, 255, 255), 0.16 * a))
    geld = max(0.0, min(1.0, t.get("geld", 0.5)))
    gefahr = t.get("gefahr", False)
    col = GREEN if t.get("gewinn", True) else RED
    if geld > 0.005:
        d.rounded_rectangle((gx0, gy - 17, gx0 + max(34, (gx1 - gx0) * geld), gy + 17), 17, fill=_rgba(col, a))
    if gefahr:
        p = 0.5 + 0.5 * math.sin(f * 0.5)
        d.rounded_rectangle((gx0 - 4, gy - 21, gx1 + 4, gy + 21), 21, outline=_rgba(RED, a * (0.5 + 0.5 * p)), width=5)
    else:
        d.rounded_rectangle((gx0, gy - 17, gx1, gy + 17), 17, outline=_rgba(WHITE, 0.5 * a), width=2)
    hz = t.get("herzen", 5)
    for k in range(5):
        cx = 572 + 50 * k
        herz(d, cx, 652, 44, _rgba((90, 84, 120), a))
        if hz >= k + 1:
            herz(d, cx, 652, 44, _rgba(RED, a))
        elif hz > k:
            sub = _lay(img)
            herz(ImageDraw.Draw(sub), cx, 652, 44, _rgba(RED, a))
            sub = sub.crop((0, 0, int(cx), img.size[1]))
            lay.alpha_composite(sub, (0, 0))
    sack(d, 862, 656, 46, t.get("mehl", 1.0), a)
    img.alpha_composite(lay)
    O.text_center(img, (92, 580), f"TAG {t.get('tag', 1)}", 64, WHITE, a, anchor="lm")
    if t.get("uhr"):                           # ohne Uhrzeit nur Sonne/Mond
        O.text_center(img, (680, 580), t["uhr"], 60, WHITE, a, anchor="lm")
    # Geld-Aenderung (z. B. Muenz-Pop): kurzes Aufleuchten der Leiste
    if t.get("blitz") is not None and 0 <= f - t["blitz"] < 8:
        k = 1 - (f - t["blitz"]) / 8
        lay = _lay(img)
        ImageDraw.Draw(lay).rounded_rectangle((gx0 - 6, gy - 23, gx1 + 6, gy + 23), 23, outline=_rgba(YELLOW, a * k), width=6)
        img.alpha_composite(lay)


def aktionsleiste(img, f, akt, a):
    lay = _lay(img)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((X0, AKTION_Y - 58, X1, AKTION_Y + 76), 34, fill=_rgba(NAVY, 0.3 * a))
    img.alpha_composite(lay)
    ged = akt.get("gedrueckt")
    seit = f - akt.get("f_druck", -999)
    for j, name in enumerate(KNOEPFE):
        cx = X0 + (X1 - X0) * (j + 0.5) / 4
        aktiv = name == ged and 0 <= seit < akt.get("dauer", 14)
        sc = 1.0 + (0.14 * math.sin(math.pi * min(1.0, seit / 8)) if aktiv else 0.0)
        r = 44 * sc
        lay = _lay(img)
        d = ImageDraw.Draw(lay)
        if aktiv:
            g = _lay(img)
            ImageDraw.Draw(g).ellipse((cx - r - 16, AKTION_Y - r - 16, cx + r + 16, AKTION_Y + r + 16), fill=_rgba(TURQ, 0.55 * a))
            img.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)))
        d.ellipse((cx - r, AKTION_Y - r, cx + r, AKTION_Y + r), fill=_rgba(TURQ if aktiv else NAVY, a),
                  outline=_rgba(WHITE if aktiv else TURQ, a), width=4)
        knopf_symbol(d, name, cx, AKTION_Y, 46 * sc, _rgba(NAVY if aktiv else WHITE, a))
        img.alpha_composite(lay)
        O.text_center(img, (cx, AKTION_Y + 60), name, 30, YELLOW if aktiv else WHITE, a)


def preisregler(img, f, r, a, y0=REGLER_Y0):
    x0 = 404 if r.get("rechts", True) else X0
    O.card(img, (x0, y0, X1, y0 + 110), a)
    lay = _lay(img)
    d = ImageDraw.Draw(lay)
    brezel(d, x0 + 56, y0 + 55, 64, a)
    tx0, tx1, ty = x0 + 108, x0 + 300, y0 + 55
    d.rounded_rectangle((tx0, ty - 7, tx1, ty + 7), 7, fill=_rgba((255, 255, 255), 0.25 * a))
    pos = max(0.0, min(1.0, r.get("pos", 0.5)))
    d.rounded_rectangle((tx0, ty - 7, tx0 + (tx1 - tx0) * pos, ty + 7), 7, fill=_rgba(TURQ, a))
    kx = tx0 + (tx1 - tx0) * pos
    d.ellipse((kx - 20, ty - 20, kx + 20, ty + 20), fill=_rgba(WHITE, a), outline=_rgba(TURQ, a), width=5)
    img.alpha_composite(lay)
    col = {"rot": RED, "gruen": GREEN}.get(r.get("farbe"), WHITE)
    O.text_center(img, (X1 - 26, y0 + 57), r.get("preis", ""), 64, col, a, anchor="rm")


def mengenregler(img, f, m, a, y0=REGLER_Y0):
    x0 = 404
    O.card(img, (x0, y0, X1, y0 + 110), a)
    lay = _lay(img)
    d = ImageDraw.Draw(lay)
    klick = m.get("klick")
    for j, (sym, cx) in enumerate((("-", x0 + 60), ("+", X1 - 60))):
        ak = klick == sym and 0 <= f - m.get("f_klick", -99) < 8
        rr = 34 * (1.12 if ak else 1.0)
        d.ellipse((cx - rr, y0 + 55 - rr, cx + rr, y0 + 55 + rr), fill=_rgba(TURQ if ak else NAVY, a), outline=_rgba(TURQ, a), width=4)
        d.line([(cx - 14, y0 + 55), (cx + 14, y0 + 55)], fill=_rgba(NAVY if ak else WHITE, a), width=7)
        if sym == "+":
            d.line([(cx, y0 + 41), (cx, y0 + 69)], fill=_rgba(NAVY if ak else WHITE, a), width=7)
    if m.get("wert") is None:                  # ohne Zahl: Stufe 0..1 als Reihe kleiner Brezeln
        n = max(0, min(6, round(6 * m.get("stufe", 0.5))))
        for j in range(6):
            brezel(d, x0 + 150 + 46 * j, y0 + 55, 40, a if j < n else 0.25 * a)
        img.alpha_composite(lay)
        return
    brezel(d, x0 + 150, y0 + 55, 56, a)
    img.alpha_composite(lay)
    O.text_center(img, ((x0 + X1) / 2 + 40, y0 + 57), str(m.get("wert", "")), 72, YELLOW if m.get("gross") else WHITE, a)


def banner(img, f, b, a_hud):
    t = f - b["f0"]
    if t < 0 or (b.get("f1") is not None and f > b["f1"] + 8):
        return
    fall = O.ease_out_back(O.clamp01(t / 10), 1.8)
    y = -200 + (420 + 200) * fall
    a = a_hud * (1 - O.clamp01((f - b["f1"]) / 8) if b.get("f1") is not None and f > b["f1"] else 1.0)
    wack = math.sin(t * 0.9) * 4.0 * math.exp(-max(0, t - 8) / 8) if t > 6 else 0.0
    farbe = {"rot": RED, "blau": (80, 150, 255), "gold": GOLD, "gruen": GREEN}.get(b.get("farbe", "blau"), (80, 150, 255))
    w0, h0 = 760, 160
    tile = Image.new("RGBA", (w0 + 80, h0 + 80), (0, 0, 0, 0))
    O.card(tile, (40, 40, 40 + w0, 40 + h0), a, border=farbe, fill=NAVY, fill_a=0.92, radius=36)
    d = ImageDraw.Draw(tile)
    ic = b.get("icon")
    if ic == "wolke":
        wolke(d, 140, 112, 110, a)
    elif ic == "muenze":
        muenze(d, 140, 120, 44, a)
    elif ic == "stern":
        sonne(d, 140, 120, 30, a)
    elif ic == "warnung":
        d.polygon([(140, 60), (196, 160), (84, 160)], fill=_rgba(YELLOW, a))
        d.rectangle((134, 92, 146, 132), fill=_rgba(NAVY, a))
        d.ellipse((134, 140, 146, 152), fill=_rgba(NAVY, a))
    O.text_center(tile, (40 + w0 / 2 + (60 if ic else 0), 40 + h0 / 2 + 4), b["text"], b.get("groesse", 96), WHITE, a, stroke=4,
                  stroke_fill=NAVY)
    tile = tile.rotate(wack, resample=Image.BICUBIC, center=(tile.size[0] / 2, 40))
    img.alpha_composite(tile, (int((X0 + X1) / 2 - tile.size[0] / 2), int(y - h0 / 2 - 40)))


def erfolg(img, f, e, a_hud, facecam):
    t = f - e["f0"]
    dur = e.get("dauer", 60)
    if t < 0 or t > dur + 8:
        return
    a = a_hud * min(O.clamp01(t / 6), O.clamp01((dur + 8 - t) / 8))
    dx = -420 * (1 - O.ease_out_back(O.clamp01(t / 9), 1.6))
    x0 = (404 if facecam else X0) + dx
    y0 = 846 if e.get("hoch") else 990
    O.card(img, (x0, y0, x0 + 500, y0 + 110), a, border=GOLD, radius=30)
    lay = _lay(img)
    pokal(ImageDraw.Draw(lay), x0 + 58, y0 + 60, 70, a)
    img.alpha_composite(lay)
    O.text_center(img, (x0 + 110, y0 + 36), "ERFOLG", 30, GOLD, a, anchor="lm")
    O.text_center(img, (x0 + 110, y0 + 76), e["text"], 48, WHITE, a, anchor="lm")
    if 4 <= t <= 20:          # kleine Sterne beim Aufpoppen
        lay = _lay(img)
        d = ImageDraw.Draw(lay)
        rnd = random.Random(int(e["f0"]))
        for k in range(8):
            w = rnd.uniform(0, 2 * math.pi)
            r = 40 + (t - 4) * 7
            cx, cy = x0 + 58 + math.cos(w) * r, y0 + 60 + math.sin(w) * r
            d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=_rgba(YELLOW, a * (1 - (t - 4) / 16)))
        img.alpha_composite(lay)


def byte_tipp(img, f, b, a_hud, anchors):
    t = f - b["f0"]
    if t < 0 or (b.get("f1") is not None and f > b["f1"] + 6):
        return
    a = a_hud * _alpha(f, b, 6, 6)
    x0, y0 = b.get("xy", (404, 770))
    fnt = O.font(46)
    zeilen = b["text"].split("\n")
    w = max(fnt.getlength(z) for z in zeilen) + 60
    x1 = min(X1, x0 + w)
    y1 = y0 + 26 + 58 * len(zeilen)
    sc = 0.85 + 0.15 * O.ease_out_back(O.clamp01(t / 7), 2.5)
    lay = _lay(img)
    d = ImageDraw.Draw(lay)
    ziel = b.get("ziel")
    if isinstance(ziel, str) and anchors and ziel in anchors.get("anchors", {}):
        ziel = anchors["anchors"][ziel][f][:2]
    if ziel:
        bx = min(max(ziel[0], x0 + 50), x1 - 50)
        unten = ziel[1] > y1
        by = y1 if unten else y0
        d.polygon([(bx - 26, by), (bx + 26, by), (ziel[0], ziel[1] - (26 if unten else -26))], fill=_rgba(TURQ, a))
    d.rounded_rectangle((x0, y0, x1, y1), 30, fill=_rgba(TURQ, a))
    img.alpha_composite(lay)
    # Mini-Byte-Kopf als Absender
    lay = _lay(img)
    d = ImageDraw.Draw(lay)
    d.ellipse((x0 - 24, y0 - 30, x0 + 34, y0 + 28), fill=_rgba(NAVY, a), outline=_rgba(WHITE, a), width=3)
    for ex in (-8, 16):
        d.rounded_rectangle((x0 + ex - 5, y0 - 10, x0 + ex + 5, y0 + 6), 4, fill=_rgba(TURQ, a))
    img.alpha_composite(lay)
    for i, z in enumerate(zeilen):
        O.text_center(img, (x0 + 30, y0 + 44 + 58 * i), z, int(46 * sc), NAVY, a, anchor="lm")


def info(img, f, k, a_hud):
    a = a_hud * _alpha(f, k, 6, 6)
    if a <= 0:
        return
    x0, y0 = k.get("xy", (404, 770))
    zeilen = k["zeilen"]
    fnt = O.font(52)
    w = max(fnt.getlength(z) for z in zeilen) + 64
    farbe = {"rot": RED, "gruen": GREEN, "gold": GOLD}.get(k.get("farbe"), TURQ)
    sc = 0.9 + 0.1 * O.ease_out_back(O.clamp01((f - k["f0"]) / 7), 2.5)
    O.card(img, (x0, y0, min(X1, x0 + w), y0 + 30 + 66 * len(zeilen)), a, border=farbe)
    for i, z in enumerate(zeilen):
        col = farbe if (i == len(zeilen) - 1 and k.get("letzte_farbig", True)) else WHITE
        O.text_center(img, (x0 + 32, y0 + 50 + 66 * i), z, int(52 * sc), col, a, anchor="lm")


def mission(img, f, m, a_hud):
    a = a_hud * _alpha(f, m, 8, 8)
    if a <= 0:
        return
    t = f - m["f0"]
    auf = O.ease_out_back(O.clamp01(t / 12), 1.4)
    cy, h = 840, 300 * auf
    x0, x1 = 90, 890
    lay = _lay(img)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, cy - h / 2, x1, cy + h / 2), 14, fill=_rgba(ROLLE, a), outline=_rgba(BRAUN, a), width=4)
    for yy in (cy - h / 2, cy + h / 2):          # aufgerollte Enden
        d.rounded_rectangle((x0 - 26, yy - 24, x1 + 26, yy + 24), 24, fill=_rgba((222, 196, 150), a), outline=_rgba(BRAUN, a), width=4)
        for xx in (x0 - 26, x1 + 26):
            d.ellipse((xx - 18, yy - 24, xx + 18, yy + 24), fill=_rgba((196, 160, 110), a), outline=_rgba(BRAUN, a), width=3)
    img.alpha_composite(lay)
    if auf < 0.7:
        return
    ta = a * O.clamp01((auf - 0.7) / 0.3)
    O.text_center(img, (x0 + 60, cy - 70), "MISSION:", 60, (196, 60, 50), ta, anchor="lm")
    O.text_center(img, (x0 + 140, cy + 10), "Mach deine Bäckerei", 52, BRAUN, ta, anchor="lm")
    O.text_center(img, (x0 + 140, cy + 72), "zur besten der Stadt.", 52, BRAUN, ta, anchor="lm")
    lay = _lay(img)
    d = ImageDraw.Draw(lay)
    bx, by = x0 + 60, cy + 40
    d.rounded_rectangle((bx - 30, by - 30, bx + 30, by + 30), 10, fill=_rgba(WHITE, ta), outline=_rgba(BRAUN, ta), width=5)
    if m.get("haken") is not None and f >= m["haken"]:
        k = O.ease_out_back(O.clamp01((f - m["haken"]) / 6), 2.6)
        O.check_icon(d, bx, by, 30 * k, _rgba((40, 170, 90), ta), width=max(1, int(9 * k)))
    img.alpha_composite(lay)


def pleite(img, f, p, a_hud, anchors):
    t = f - p["f0"]
    if t < 0:
        return
    a = a_hud * O.clamp01(t / 8)
    spot = p.get("spot")
    if isinstance(spot, str) and anchors and spot in anchors.get("anchors", {}):
        spot = anchors["anchors"][spot][f][:2]
    import numpy as np
    h, w = img.size[1], img.size[0]
    dunkel = np.full((h, w), 170 * a, np.float32)
    if spot:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt((xx - spot[0]) ** 2 + ((yy - spot[1]) * 0.85) ** 2)
        dunkel *= np.clip((r - 120) / 90, 0, 1)
    lay = np.zeros((h, w, 4), np.uint8)
    lay[..., 0], lay[..., 1], lay[..., 2] = 12, 8, 20
    lay[..., 3] = dunkel.astype(np.uint8)
    img.alpha_composite(Image.fromarray(lay, "RGBA"))
    sc = 0.5 + 0.5 * O.ease_out_back(O.clamp01((t - 2) / 9), 3.0)
    ruck = (math.sin(t * 2.3) * 10 * math.exp(-t / 6)) if t < 18 else 0.0
    px, py = p.get("x", (X0 + X1) / 2), p.get("y", 790)
    O.text_center(img, (px + ruck, py), "PLEITE", 150 if p.get("x") else 190, RED, a * O.clamp01((t - 2) / 4), stroke=12, stroke_fill=(40, 8, 12),
                  scale=sc)
    if t >= p.get("knopf_nach", 20):
        k = O.ease_out_back(O.clamp01((t - p.get("knopf_nach", 20)) / 8), 2.0)
        bx0, bx1, by0, by1 = px - 200, px + 200, py + 110, py + 200
        lay = _lay(img)
        d = ImageDraw.Draw(lay)
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        ww, hh = (bx1 - bx0) / 2 * k, (by1 - by0) / 2 * k
        puls = 0.5 + 0.5 * math.sin(t * 0.35)
        d.rounded_rectangle((cx - ww, cy - hh, cx + ww, cy + hh), 50, fill=_rgba(GREEN, a), outline=_rgba(WHITE, a * (0.6 + 0.4 * puls)),
                            width=5)
        img.alpha_composite(lay)
        O.text_center(img, (cx, cy + 3), "NOCHMAL", 64, WHITE, a * O.clamp01(k), stroke=3, stroke_fill=(20, 90, 50), scale=max(0.2, k))


def levelup(img, f, l, a_hud):
    t = f - l["f0"]
    if t < 0 or (l.get("f1") is not None and f > l["f1"] + 8):
        return
    a = a_hud * O.clamp01(t / 6) * (1 - O.clamp01((f - l["f1"]) / 8) if l.get("f1") is not None and f > l["f1"] else 1.0)
    cx, cy = (X0 + X1) / 2, l.get("y", 820)
    lay = _lay(img)
    d = ImageDraw.Draw(lay)
    rot = t * 0.02
    for k in range(16):
        w0 = rot + k * 2 * math.pi / 16
        w1 = w0 + math.pi / 16
        d.polygon([(cx, cy), (cx + math.cos(w0) * 1200, cy + math.sin(w0) * 1200), (cx + math.cos(w1) * 1200, cy + math.sin(w1) * 1200)],
                  fill=_rgba(GOLD, 0.34 * a))
    lay = lay.filter(ImageFilter.GaussianBlur(3))
    g = _lay(img)
    ImageDraw.Draw(g).ellipse((cx - 260, cy - 260, cx + 260, cy + 260), fill=_rgba((255, 236, 160), 0.55 * a))
    lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)))
    img.alpha_composite(lay)
    sc = 0.4 + 0.6 * O.ease_out_back(O.clamp01((t - 2) / 10), 2.6)
    zeilen = l.get("zeilen", ["FILIALE 2", "FREIGESCHALTET"])
    O.text_center(img, (cx, cy - 70), zeilen[0], 130, YELLOW, a, stroke=10, stroke_fill=(120, 70, 10), scale=sc)
    if len(zeilen) > 1:
        O.text_center(img, (cx, cy + 60), zeilen[1], 84, WHITE, a, stroke=8, stroke_fill=(120, 70, 10), scale=sc)
    # Konfetti (fallend, drehend)
    lay = _lay(img)
    d = ImageDraw.Draw(lay)
    rnd = random.Random(int(l["f0"]) + 3)
    for k in range(90):
        x = rnd.uniform(X0, X1 + 60)
        v = rnd.uniform(9, 17)
        y = -40 + (t - rnd.uniform(0, 14)) * v
        if y < -30 or y > 1500:
            continue
        x += math.sin(t * 0.15 + k) * 30
        c = rnd.choice([RED, YELLOW, GREEN, (80, 150, 255), WHITE, GOLD])
        s = rnd.uniform(9, 16)
        w = t * 0.2 + k
        dx, dy = math.cos(w) * s, abs(math.sin(w)) * s * 0.5 + 3
        d.polygon([(x - dx, y - dy), (x + dx, y - dy), (x + dx, y + dy), (x - dx, y + dy)], fill=_rgba(c, a))
    img.alpha_composite(lay)


def facecam_rahmen(img, f, fc, a_hud):
    a = a_hud * _alpha(f, fc, 6, 6)
    if a <= 0:
        return
    x0, y0, x1, y1 = FACECAM
    lay = _lay(img)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, y0, x1, y1), 28, outline=_rgba(TURQ, a), width=5)
    d.rounded_rectangle((x0 + 16, y0 + 16, x0 + 118, y0 + 56), 20, fill=_rgba(NAVY, 0.75 * a))
    p = 0.6 + 0.4 * (math.sin(f * 0.25) > 0)
    d.ellipse((x0 + 28, y0 + 26, x0 + 48, y0 + 46), fill=_rgba((255, 50, 60), a * p))
    img.alpha_composite(lay)
    O.text_center(img, (x0 + 56, y0 + 37), "LIVE", 28, WHITE, a, anchor="lm")


def draw_game(img, hud, f, anchors=None):
    """Zeichnet die Spielanzeige fuer Frame f (hud: Zustand aus der Regie)."""
    if not hud:
        return
    a = hud.get("a", 1.0)
    if a <= 0.01:
        return
    if hud.get("levelup"):
        levelup(img, f, hud["levelup"], a)
    if hud.get("pleite"):
        pleite(img, f, hud["pleite"], a, anchors)
    fc = hud.get("facecam")
    if fc:
        facecam_rahmen(img, f, fc, a)
    if hud.get("top"):
        obere_leiste(img, f, hud["top"], a * hud["top"].get("a", 1.0))
    if hud.get("aktion"):
        aktionsleiste(img, f, hud["aktion"], a * hud["aktion"].get("a", 1.0))
    if hud.get("regler"):
        preisregler(img, f, hud["regler"], a * _alpha(f, hud["regler"]))
    if hud.get("menge"):
        mengenregler(img, f, hud["menge"], a * _alpha(f, hud["menge"]), y0=hud["menge"].get("y0", REGLER_Y0))
    if hud.get("info"):
        info(img, f, hud["info"], a)
    if hud.get("mission"):
        mission(img, f, hud["mission"], a)
    if hud.get("tipp"):
        byte_tipp(img, f, hud["tipp"], a, anchors)
    if hud.get("erfolg"):
        erfolg(img, f, hud["erfolg"], a, bool(fc) and f < (fc.get("f1") or 10 ** 9))
    if hud.get("banner"):
        banner(img, f, hud["banner"], a)
