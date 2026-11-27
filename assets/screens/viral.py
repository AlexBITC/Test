"""Bildschirm-Ebenen fuer die Folge 'Byte macht Kalle viral' (folge-06-viral), 1280x720 pro Frame.

Wird von engine/overlays.screen_frame geladen (Episoden-Screens: assets/screens/<slug>.py, Funktion frame).
Theke: Laptop-Bildschirm (die Regie legt die Bildfolge per UV auf das Laptop-Display, perspektivisch korrekt).
Studio: grosser Screen. Inhalte (keine Requisiten): rohvideo_wackelig, schnitt_timeline, effekte_haekchen,
fertiges_video_hochformat, erstes_frame_gross. Zahlen = Sprechtext: 03:00, 0:08, 30, 12.000.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from engine.overlays import font, ease_out, ease_in_out, clamp01, ease_out_back

SW, SH = 1280, 720
HERE = Path(__file__).resolve().parent / "viral"
BG = (18, 16, 31)
PANEL = (30, 27, 52)
PANEL2 = (40, 36, 70)
TURQ = (46, 230, 214)
YELLOW = (255, 225, 77)
RED = (255, 77, 90)
GREEN = (61, 220, 132)
WHITE = (255, 255, 255)
GREY = (150, 148, 180)
_IMG = {}


def _kalle(kind="schlingt"):
    """Standbild von Kalle beim Brezelschlingen (aus einem Render dieser Folge, assets/screens/viral/)."""
    if kind in _IMG:
        return _IMG[kind]
    p = HERE / f"kalle_{kind}.png"
    if p.exists():
        im = Image.open(p).convert("RGB")
    else:                                  # Platzhalter bis zum ersten Render
        im = Image.new("RGB", (900, 1600), (120, 100, 90))
        d = ImageDraw.Draw(im)
        d.ellipse((250, 300, 650, 700), fill=(231, 176, 138))
        d.rectangle((200, 700, 700, 1600), fill=(124, 141, 181))
    _IMG[kind] = im
    return im


def _fit(im, w, h, zoom=1.0, cx=0.5, cy=0.42):
    """Ausschnitt mit Seitenverhaeltnis w:h, Zoom um (cx, cy)."""
    iw, ih = im.size
    asp = w / h
    if iw / ih > asp:
        ch, cw = ih, ih * asp
    else:
        cw, ch = iw, iw / asp
    cw, ch = cw / zoom, ch / zoom
    x0 = min(max(0, cx * iw - cw / 2), iw - cw)
    y0 = min(max(0, cy * ih - ch / 2), ih - ch)
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((int(w), int(h)), Image.LANCZOS)


def _chrome(img, title, f):
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, SW, 64), fill=PANEL)
    for i, col in enumerate((RED, YELLOW, GREEN)):
        d.ellipse((24 + 34 * i, 20, 48 + 34 * i, 44), fill=col)
    d.text((150, 32), title, font=font(38), fill=WHITE, anchor="lm")
    return d


def _t(d, xy, s, size, col, anchor="mm", alpha=255, stroke=0):
    d.text(xy, s, font=font(size), fill=col + (alpha,) if len(col) == 3 else col, anchor=anchor,
           stroke_width=stroke, stroke_fill=(10, 8, 20))


def _heart(d, cx, cy, r, col):
    pts = []
    for k in range(32):
        t = 2 * math.pi * k / 32
        pts.append((cx + r * 16 * math.sin(t) ** 3 / 16,
                    cy - r * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16))
    d.polygon(pts, fill=col)


def _wf(s, core, default=None):
    for w in s["words"]:
        if w["w"].strip(".,!?:…").lower() == core.lower():
            return w["f0"]
    return default if default is not None else s["f0"] + 6


def _glow(img, a):
    """Tuerkiser Lichtblitz (Byte kommt aus dem Laptop / taucht wieder ein)."""
    if a <= 0:
        return img
    ov = Image.new("RGB", (SW, SH), (190, 255, 250))
    d = ImageDraw.Draw(ov)
    return Image.blend(img.convert("RGB"), ov, min(1.0, a)).convert("RGBA")


def _check(d, cx, cy, s, col, t):
    """Haekchen, zeichnet sich in t 0..1."""
    pts = [(cx - s * 0.5, cy), (cx - s * 0.15, cy + s * 0.35), (cx + s * 0.55, cy - s * 0.4)]
    if t <= 0:
        return
    l1 = math.dist(pts[0], pts[1])
    l2 = math.dist(pts[1], pts[2])
    tot = (l1 + l2) * t
    if tot <= l1:
        p = pts[0][0] + (pts[1][0] - pts[0][0]) * tot / l1, pts[0][1] + (pts[1][1] - pts[0][1]) * tot / l1
        d.line([pts[0], p], fill=col, width=int(s * 0.16), joint="curve")
    else:
        k = (tot - l1) / l2
        p = pts[1][0] + (pts[2][0] - pts[1][0]) * k, pts[1][1] + (pts[2][1] - pts[1][1]) * k
        d.line([pts[0], pts[1], p], fill=col, width=int(s * 0.16), joint="curve")


# ------------------------------------------------------------------ Szenen
def _desktop(img, s, f, tl):
    d = _chrome(img, "Neues Projekt", f)
    d.polygon([(SW / 2 - 60, 250), (SW / 2 - 60, 410), (SW / 2 + 80, 330)], fill=(70, 66, 110))
    _t(d, (SW / 2, 500), "Video importieren …", 54, GREY)
    return img


def _rec(img, s, f, tl):
    """Szene 4: Live-Bild der Mini-Kamera, REC blinkt, Zeit laeuft."""
    im = _fit(_kalle("schlingt"), SW, SH - 64, zoom=1.15)
    im = ImageEnhance.Brightness(im).enhance(0.8)
    img.paste(im, (0, 64))
    d = _chrome(img, "Kamera · live", f)
    t = (f - s["f0"]) / 30
    if int(f / 8) % 2 == 0:
        d.ellipse((60, 100, 104, 144), fill=RED)
    _t(d, (124, 122), f"REC  00:0{int(t)}", 52, WHITE, anchor="lm", stroke=3)
    return img


def _rohvideo(img, s, f, tl):
    """Szene 5: wackelig, zu dunkel, Mehlfleck mitten im Bild, Zeitstempel 03:00."""
    d0 = _chrome(img, "Rohvideo.mp4", f)
    r = random.Random(int(f / 2))
    vid_w, vid_h = 900, 506
    big = _fit(_kalle("schlingt"), vid_w + 80, vid_h + 80, zoom=1.05)
    big = ImageEnhance.Brightness(big).enhance(0.42)
    big = big.rotate(r.uniform(-2.5, 2.5), resample=Image.BICUBIC)
    dx, dy = r.randint(-28, 28), r.randint(-22, 22)
    frame = big.crop((40 + dx, 40 + dy, 40 + dx + vid_w, 40 + dy + vid_h)).filter(ImageFilter.GaussianBlur(2.2))
    blob = Image.new("L", (vid_w, vid_h), 0)
    bd = ImageDraw.Draw(blob)
    bx, by = vid_w / 2 + 20, vid_h / 2 - 10
    bd.ellipse((bx - 150, by - 110, bx + 150, by + 110), fill=235)
    bd.ellipse((bx - 40, by - 160, bx + 120, by - 40), fill=200)
    blob = blob.filter(ImageFilter.GaussianBlur(26))
    frame.paste(Image.new("RGB", (vid_w, vid_h), (250, 248, 240)), (0, 0), blob)
    x0, y0 = (SW - vid_w) // 2, 84
    img.paste(frame, (x0, y0))
    d = ImageDraw.Draw(img)
    d.rectangle((x0 - 3, y0 - 3, x0 + vid_w + 3, y0 + vid_h + 3), outline=(70, 66, 110), width=3)
    _t(d, (x0 + 24, y0 + 36), "ROH", 40, YELLOW, anchor="lm", stroke=3)
    # Zeitleiste mit Zeitstempel 03:00 (= 'Drei Minuten')
    hl = _wf(s, "drei")
    a = ease_out((f - hl + 2) / 8)
    yb = 640
    d.rounded_rectangle((60, yb - 10, 900, yb + 10), 10, fill=PANEL2)
    d.rounded_rectangle((60, yb - 10, 60 + 840 * clamp01((f - s["f0"]) / (s["f1"] - s["f0"])), yb + 10), 10,
                        fill=GREY)
    sz = int(96 * (1 + 0.15 * math.sin(math.pi * clamp01((f - hl) / 8)))) if f >= hl else 96
    _t(d, (1090, yb - 4), "03:00", sz, WHITE if a < 1 else YELLOW, stroke=4)
    return img


SEGS = [  # (Breite-Anteil, gut?)
    (0.10, False), (0.07, False), (0.12, False), (0.05, True), (0.11, False), (0.09, False), (0.14, False),
    (0.08, False), (0.24, False)]


def _timeline(img, s, f, tl):
    """Szene 6: Schnitt-Timeline. Clip wird zerlegt, schlechte Teile rot markiert und fliegen raus,
    uebrig bleibt ein gruener Block '0:08'."""
    d = _chrome(img, "Schnitt", f)
    # Vorschau oben
    pv = _fit(_kalle("schlingt"), 400, 225, zoom=1.2)
    img.paste(pv, (SW // 2 - 200, 84))
    d.rectangle((SW // 2 - 203, 81, SW // 2 + 203, 312), outline=(70, 66, 110), width=3)
    # Lineal 0:00 .. 3:00
    X0, X1, Y = 70, SW - 70, 360
    d.line([(X0, Y), (X1, Y)], fill=(90, 86, 130), width=2)
    for k in range(7):
        x = X0 + (X1 - X0) * k / 6
        d.line([(x, Y - 12), (x, Y)], fill=(120, 116, 160), width=3)
        _t(d, (x, Y - 32), f"{k // 2}:{30 * (k % 2):02d}", 30, GREY)
    f_cut = _wf(s, "such") - 2
    f_mark = _wf(s, "besten") - 4
    f_fly = f_mark + 10
    f_acht = _wf(s, "acht")
    ty0, ty1 = 400, 540
    # Spuren (Video, Audio)
    d.rounded_rectangle((X0 - 10, ty0 - 10, X1 + 10, ty1 + 80), 14, fill=PANEL)
    x = X0
    n_cut = sum(1 for _ in SEGS)
    for k, (wf, good) in enumerate(SEGS):
        w = (X1 - X0) * wf
        cut_t = clamp01((f - f_cut - 2 * k) / 4)
        gap = 6 * cut_t
        col = (70, 110, 220)
        dy, alpha = 0, 255
        if not good and f >= f_mark + 1.5 * k:
            col = RED
        if not good and f >= f_fly + k:
            tt = clamp01((f - f_fly - k) / 9)
            dy = -260 * ease_out(tt) * (1 if k % 2 else 0.8)
            alpha = int(255 * (1 - tt))
        if good:
            col = (70, 110, 220) if f < f_mark else GREEN
        if alpha > 0:
            box = (x + gap, ty0 + dy, x + w - gap, ty1 + dy)
            if good and f >= f_fly + 4:         # gruener Block waechst in die Mitte
                g = ease_out(clamp01((f - f_fly - 4) / 8))
                cxm = x + w / 2 + (SW / 2 - (x + w / 2)) * g
                hw = w / 2 + 150 * g
                box = (cxm - hw, ty0, cxm + hw, ty1)
            ov = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            od.rounded_rectangle(box, 12, fill=col + (alpha,), outline=(255, 255, 255, int(alpha * 0.6)), width=2)
            if not good and f >= f_mark + 1.5 * k:
                od.line([(box[0] + 14, box[1] + 14), (box[2] - 14, box[3] - 14)], fill=(255, 255, 255, alpha), width=6)
                od.line([(box[0] + 14, box[3] - 14), (box[2] - 14, box[1] + 14)], fill=(255, 255, 255, alpha), width=6)
            img.alpha_composite(ov)
            d = ImageDraw.Draw(img)
            if good and f >= f_fly + 12:
                a = clamp01((f - f_acht + 4) / 6)
                if a > 0:
                    sz = int(120 * (1 + 0.15 * math.sin(math.pi * clamp01((f - f_acht) / 8))))
                    _t(d, ((box[0] + box[2]) / 2, (ty0 + ty1) / 2), "0:08", sz, WHITE, stroke=5)
        x += w
    # Audiospur (Wellenform)
    pts = []
    for k in range(120):
        xx = X0 + (X1 - X0) * k / 119
        pts.append((xx, ty1 + 40 + 22 * math.sin(k * 0.7 + f * 0.3) * (0.4 + 0.6 * abs(math.sin(k * 0.13)))))
    d.line(pts, fill=(46, 230, 214), width=4)
    # Abspielkopf bewegt sich
    ph = X0 + (X1 - X0) * ((f - s["f0"]) * 0.012 % 1.0)
    d.line([(ph, Y - 6), (ph, ty1 + 78)], fill=YELLOW, width=5)
    d.polygon([(ph - 14, Y - 20), (ph + 14, Y - 20), (ph, Y - 2)], fill=YELLOW)
    return img


EFFEKTE = [("Zeitlupe", "zeitlupe"), ("Untertitel", "untertitel"), ("Musik", "musik")]


def _preview_portrait(img, f, x0, y0, w, h, slow=False, sub=False, music=False, zoom=1.0, kind="schlingt", t=0.0):
    im = _fit(_kalle(kind), w, h, zoom=zoom * (1 + 0.04 * t), cx=0.5, cy=0.45)
    if slow:
        im = Image.blend(im, im.filter(ImageFilter.BoxBlur(6)), 0.35)
    img.paste(im, (int(x0), int(y0)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0 - 6, y0 - 6, x0 + w + 6, y0 + h + 6), 22, outline=(230, 230, 240), width=6)
    if slow:
        d.rounded_rectangle((x0 + 14, y0 + 16, x0 + 120, y0 + 66), 14, fill=(0, 0, 0))
        _t(d, (x0 + 67, y0 + 41), "0,5×", 34, YELLOW)
    if sub:
        _t(d, (x0 + w / 2, y0 + h * 0.74), "Seit 30 Jahren.", int(w * 0.11), WHITE, stroke=4)
        _t(d, (x0 + w / 2, y0 + h * 0.74 + w * 0.13), "Blind.", int(w * 0.11), YELLOW, stroke=4)
    if music:
        for k in range(14):
            hh = 10 + 26 * abs(math.sin(f * 0.5 + k * 0.9))
            xx = x0 + 20 + k * (w - 40) / 13
            d.line([(xx, y0 + h - 30 - hh), (xx, y0 + h - 30)], fill=TURQ, width=7)
    return d


def _effekte(img, s, f, tl):
    """Szene 7: drei Effekte mit Haekchen, jeder sofort in der Vorschau sichtbar."""
    d = _chrome(img, "Effekte", f)
    times = [_wf(s, "zeitlupe") + 2, _wf(s, "untertitel") + 2, _wf(s, "musik") + 2]
    on = [f >= t for t in times]
    _preview_portrait(img, f, 90, 84, 340, 604, slow=on[0], sub=on[1], music=on[2], t=(f - s["f0"]) / 60)
    d = ImageDraw.Draw(img)
    for k, (lab, _) in enumerate(EFFEKTE):
        y = 170 + k * 170
        hit = f >= times[k]
        pk = 1 + 0.08 * math.sin(math.pi * clamp01((f - times[k]) / 6)) if hit else 1.0
        d.rounded_rectangle((520, y - 62, 1210, y + 62), 22, fill=PANEL2 if not hit else (32, 70, 60),
                            outline=GREEN if hit else (80, 76, 120), width=4)
        _t(d, (570, y), lab, int(72 * pk), WHITE, anchor="lm")
        d.rounded_rectangle((1080, y - 42, 1164, y + 42), 16, fill=(20, 18, 36), outline=GREEN if hit else GREY, width=4)
        _check(d, 1122, y + 2, 64, GREEN, clamp01((f - times[k]) / 5))
    return img


def _fertig(img, s, f, tl):
    """Szene 8: fertiges Video im Hochformat, Kalle in Zeitlupe."""
    d = _chrome(img, "Fertig", f)
    h = 610
    w = h * 9 / 16
    x0 = SW / 2 - w / 2
    t = (f - s["f0"]) / 90
    _preview_portrait(img, f, x0, 84, w, h, slow=True, sub=True, music=True, t=t)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0, 84 + h + 8, x0 + w * clamp01(t), 84 + h + 16), 4, fill=RED)
    _t(d, (x0 - 60, 380), "0:08", 64, WHITE, anchor="rm")
    _check(d, x0 + w + 110, 380, 110, GREEN, 1.0)
    return img


def _erstes_frame(img, s, f, tl):
    """Szene 9 (Studio-Screen): erstes Frame stark vergroessert, Text 'Seit 30 Jahren. Blind.'"""
    t = (f - s["f0"]) / 110
    im = _fit(_kalle("blind"), SW, SH, zoom=1.0 + 0.12 * ease_in_out(clamp01(t)), cx=0.5, cy=0.4)
    img.paste(im, (0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((26, 24, 250, 84), 16, fill=(0, 0, 0))
    _t(d, (138, 54), "FRAME 1", 40, YELLOW)
    a = clamp01((f - s["f0"] - 4) / 6)
    if a > 0:
        y = 150 - 30 * (1 - ease_out(a))
        _t(d, (SW / 2, y), "Seit 30 Jahren.", 118, WHITE, stroke=8)
        _t(d, (SW / 2, y + 130), "Blind.", 130, YELLOW, stroke=8)
    # Abspielkopf auf 0:00
    d.rectangle((0, SH - 14, SW, SH), fill=(30, 28, 50))
    d.rectangle((0, SH - 14, 18, SH), fill=RED)
    return img


def _reichweite(img, s, f, tl):
    """Szene 12-14: Laptop zeigt das gepostete Video mit 12.000 Aufrufen."""
    d = _chrome(img, "Gepostet", f)
    h = 600
    w = h * 9 / 16
    _preview_portrait(img, f, 110, 90, w, h, slow=False, sub=True, t=0.5)
    d = ImageDraw.Draw(img)
    _t(d, (860, 270), "12.000", 170, WHITE, stroke=6)
    _t(d, (860, 390), "Aufrufe", 72, GREY)
    for k in range(5):
        x = 650 + k * 100 + 20 * math.sin(f * 0.1 + k)
        y = 560 - ((f * 3 + k * 47) % 140)
        _heart(d, x, y, 30, (255, 79, 123))
    return img


def frame(tl, s, f):
    """Rueckgabe: PIL-Bild (RGBA, 1280x720) oder None (leerer Bildschirm)."""
    i = s["i"]
    N = tl["frames"]
    img = Image.new("RGBA", (SW, SH), BG + (255,))
    if s["set"] == "studio":
        return _erstes_frame(img, s, f, tl)
    if s["set"] != "theke":
        return None
    if i == 0:
        img = _desktop(img, s, f, tl)
    elif i in (1, 2):
        img = _desktop(img, s, f, tl)
    elif i == 3:
        img = _rec(img, s, f, tl)
    elif i == 4:
        img = _rohvideo(img, s, f, tl)
    elif i == 5:
        img = _timeline(img, s, f, tl)
    elif i == 6:
        img = _effekte(img, s, f, tl)
    elif i == 7:
        img = _fertig(img, s, f, tl)
    else:
        img = _reichweite(img, s, f, tl) if i < 13 else _desktop(img, s, f, tl)
    # Loop: Lichtblitz, wenn Byte aus dem Laptop schiesst (Anfang) bzw. am Ende wieder hinein
    g = max(1 - f / 10, (f - (N - 12)) / 11 if f >= N - 12 else 0.0)
    return _glow(img, 0.85 * g)
