"""2D-Ebene als transparente PNG-Sequenz (1080x1920) und Screen-Texturen fuer den Studio-Screen.

Einheitliches UI-System: abgerundete Karten (Radius 28 px), halbtransparentes Navy, 2 px tuerkise
Kante, weicher Schatten, Einblendungen mit Slide + Fade (200-300 ms). Eine Schriftfamilie
(Lilita One), zwei Groessen pro Bild: GROSS 84 px, KLEIN 40 px.
"""
from __future__ import annotations

import json
import math
import os
import re
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

try:
    from .timing import counter_window, calc_times
except ImportError:
    from timing import counter_window, calc_times

FONT = Path(__file__).resolve().parent / "fonts" / "LilitaOne-Regular.ttf"
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = 1080, 1920
BIG, SMALL = 84, 40
FPS = 30
# Palette
NAVY = (27, 24, 48)
TURQ = (46, 230, 214)
GOLD = (242, 180, 90)
FLOUR = (245, 241, 232)
RED = (255, 90, 95)
GREEN = (61, 220, 132)
YELLOW = (255, 225, 77)
GREY = (120, 116, 150)
# Layout (Safe Zone: oben 220, rechts 160, unten 420)
X0, X1 = 60, 920
TOP = 236
SUB_Y = 1330          # Mitte der Untertitel (Band 1250-1450)
BAR_Y = 1436          # Kapitel-Leiste unten, ueber der Safe Zone (endet bei 1492 < 1500)
SUB_X = (60 + 900) // 2


@lru_cache(maxsize=16)
def font(size):
    try:
        return ImageFont.truetype(str(FONT), size)
    except OSError:
        return ImageFont.truetype(FALLBACK, size)


def clamp01(t):
    return max(0.0, min(1.0, t))


def ease_out(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp01(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_back(t, s=1.70158):
    t = clamp01(t)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def slide(f, f_in, f_out=None, dur=8):
    """0..1 Sichtbarkeit (Slide + Fade, 8 Frames = 267 ms)."""
    a = ease_out((f - f_in) / dur)
    if f_out is not None:
        a = min(a, 1 - ease_in_out((f - f_out) / dur))
    return clamp01(a)


# ------------------------------------------------------------------ Zeichen-Helfer
def card(img, box, alpha=1.0, border=TURQ, fill=NAVY, fill_a=0.84, radius=28, glow=False):
    if alpha <= 0.01:
        return
    x0, y0, x1, y1 = [int(v) for v in box]
    pad = 40
    sh = Image.new("RGBA", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 10, pad + x1 - x0, pad + y1 - y0 + 10), radius,
                                         fill=(0, 0, 0, int(150 * alpha)))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(sh, (x0 - pad, y0 - pad))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x0, y0, x1, y1), radius, fill=(*fill, int(255 * fill_a * alpha)),
                        outline=(*border, int(255 * alpha)), width=2)
    img.alpha_composite(layer)


def sweep(img, box, t, radius=28, alpha=1.0):
    """Glanz-Sweep: diagonales Lichtband laeuft einmal ueber die Karte (t 0..1)."""
    if not (0 < t < 1) or alpha <= 0:
        return
    x0, y0, x1, y1 = [int(v) for v in box]
    w, h = x1 - x0, y1 - y0
    band = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(band)
    cx = -h + (w + 2 * h) * t
    d.polygon([(cx, 0), (cx + 70, 0), (cx + 70 - h * 0.6, h), (cx - h * 0.6, h)], fill=(255, 255, 255, int(90 * alpha)))
    band = band.filter(ImageFilter.GaussianBlur(6))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=255)
    clip = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    clip.paste(band, (0, 0), mask)
    img.alpha_composite(clip, (x0, y0))


def text_center(img, xy, s, size, fill, alpha=1.0, stroke=0, stroke_fill=(0, 0, 0), scale=1.0, anchor="mm"):
    if alpha <= 0.01:
        return
    sz = max(4, int(round(size * scale)))
    fnt = font(sz)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text(xy, s, font=fnt, fill=(*fill, int(255 * alpha)), anchor=anchor, stroke_width=int(stroke * scale),
           stroke_fill=(*stroke_fill, int(255 * alpha)))
    img.alpha_composite(layer)


GOLD_KONTUR = (242, 180, 90)


def text_kursiv(img, xy, s, size, fill, alpha=1.0, scale=1.0, schraeg=0.2):
    """2.5: kursiver Text (Scherung) mit feiner goldener Kontur und dunklem Schatten fuer Lesbarkeit."""
    if alpha <= 0.01:
        return
    sz = max(4, int(round(size * scale)))
    fnt = font(sz)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    d.text((x + 3, y + 4), s, font=fnt, fill=(10, 8, 24, int(150 * alpha)), anchor="mm",
           stroke_width=int(6 * scale), stroke_fill=(10, 8, 24, int(150 * alpha)))
    d.text(xy, s, font=fnt, fill=(*fill, int(255 * alpha)), anchor="mm", stroke_width=max(1, int(3 * scale)),
           stroke_fill=(*GOLD_KONTUR, int(255 * alpha)))
    layer = layer.transform(layer.size, Image.AFFINE, (1, schraeg, -schraeg * y, 0, 1, 0), resample=Image.BICUBIC)
    img.alpha_composite(layer)


def check_icon(d, cx, cy, s, color, width=6):
    d.line([(cx - s * 0.45, cy), (cx - s * 0.12, cy + s * 0.35), (cx + s * 0.5, cy - s * 0.4)], fill=color, width=width,
           joint="curve")


# ------------------------------------------------------------------ Untertitel-Gruppen
def subtitle_groups(scene):
    """2-4 Woerter pro Einblendung, Umbruch an Satzzeichen und nach Breite (max. 840 px)."""
    words = []
    for w in scene["words"]:
        if not any(ch.isalnum() for ch in w["w"]):
            if words:
                words[-1] = dict(words[-1], w=words[-1]["w"] + " " + w["w"])
            continue
        words.append(dict(w))
    fnt = font(BIG)
    groups, cur = [], []

    def width(ws):
        return sum(fnt.getlength(x["w"]) for x in ws) + (fnt.getlength(" ") + 16) * (len(ws) - 1)
    for w in words:
        if cur and (len(cur) >= 4 or width(cur + [w]) > 820):
            groups.append(cur)
            cur = []
        cur.append(w)
        if w["w"][-1] in ".!?:…," and len(cur) >= 2:
            groups.append(cur)
            cur = []
    if cur:
        if len(cur) == 1 and groups and len(groups[-1]) < 4 and width(groups[-1] + cur) <= 820:
            groups[-1] = groups[-1] + cur
        else:
            groups.append(cur)
    return groups


def draw_subtitles(img, tl, f):
    for si, s in enumerate(tl["scenes"]):
        if not (s["f0"] <= f < s["f1"]):
            continue
        groups = subtitle_groups(s)
        for gi, g in enumerate(groups):
            g0 = g[0]["f0"] - 2
            g1 = groups[gi + 1][0]["f0"] - 2 if gi + 1 < len(groups) else s["f1"] - 3
            if not (g0 <= f < g1):
                continue
            out = clamp01((g1 - f) / 3)
            fnt = font(BIG)
            space = fnt.getlength(" ") + 16
            total = sum(fnt.getlength(x["w"]) for x in g) + space * (len(g) - 1)
            x = SUB_X - total / 2
            for w in g:
                ww = fnt.getlength(w["w"])
                if f >= w["f0"] - 2:
                    t = (f - (w["f0"] - 2)) / 6
                    sc = 0.6 + 0.4 * ease_out_back(t, 3.0)
                    a = clamp01((f - (w["f0"] - 2) + 1) / 2) * out
                    if s.get("sprecher") == "erzaehler":       # 2.5: Erzaehler kursiv, weiss, feine goldene Kontur
                        text_kursiv(img, (x + ww / 2, SUB_Y), w["w"], BIG, (255, 255, 255), a, scale=sc)
                    else:
                        col = YELLOW if w["hl"] else (255, 255, 255)
                        text_center(img, (x + ww / 2, SUB_Y), w["w"], BIG, col, a, stroke=7, scale=sc)
                x += ww + space


# ------------------------------------------------------------------ Elemente
def draw_hook(img, tl, f):
    if isinstance(tl.get("hook"), dict):
        return draw_hook_card(img, tl, f)
    f_in, f_out = 0, 60
    if f > f_out + 10:
        return
    a = slide(f, f_in, f_out, 9)
    if a <= 0:
        return
    dy = -160 * (1 - a)
    m = re.search(r"Hook(?:-Text)?[^'\[]*'([^']+)'", tl["scenes"][0].get("visual", ""))
    hook = m.group(1) if m else tl["hook"]
    if font(BIG).getlength(hook) > (X1 - X0 - 60) and " – " not in hook and ". " not in hook:
        ws = hook.split()
        best = min(range(1, len(ws)), key=lambda k: abs(font(BIG).getlength(" ".join(ws[:k])) -
                                                         font(BIG).getlength(" ".join(ws[k:]))))
        lines = [" ".join(ws[:best]), " ".join(ws[best:])]
    elif " – " in hook:
        a1, a2 = hook.split(" – ", 1)
        lines = [a1 + " –", a2]
    else:
        parts = hook.split(". ", 1)
        lines = [parts[0] + "." if len(parts) > 1 else parts[0]] + ([parts[1]] if len(parts) > 1 else [])
    box = (X0, TOP + dy, X1, TOP + 60 + 92 * len(lines) + dy)
    card(img, box, a)
    for i, ln in enumerate(lines):
        col = YELLOW if i == len(lines) - 1 and len(lines) > 1 else (255, 255, 255)
        text_center(img, ((X0 + X1) / 2, TOP + 30 + 46 + 92 * i + dy), ln, BIG, col, a)




def draw_hook_card(img, tl, f):
    """Hook-Karte ab Frame 1 (sofort sichtbar, kleiner Pop) bei y 230-520, gelbes Teilstueck, mind. 1,5 s."""
    hk = tl["hook"]
    f_out = 56                     # 1,87 s sichtbar, dann Slide nach oben
    if f > f_out + 10:
        return
    a = 1.0 if f < f_out else 1 - ease_in_out((f - f_out) / 8)
    if a <= 0:
        return
    dy = -120 * (1 - a)
    sc = 0.94 + 0.06 * ease_out_back(clamp01((f + 1) / 6), 2.5)
    y0, y1 = 230, 520
    card(img, (X0, y0 + dy, X1, y1 + dy), a)
    txt = hk["text_oben"]
    parts = [p.strip() + ("." if not p.strip().endswith((".", "?", "!")) else "") for p in txt.split(". ") if p.strip()]
    gelb = hk.get("gelb", "")
    size = 104
    if len(parts) == 1 and font(size).getlength(parts[0]) > X1 - X0 - 60:      # hoechstens zweizeilig umbrechen
        ws = parts[0].split()
        k_ = min(range(1, len(ws)), key=lambda k: abs(font(size).getlength(" ".join(ws[:k])) -
                                                       font(size).getlength(" ".join(ws[k:]))))
        parts = [" ".join(ws[:k_]), " ".join(ws[k_:])]
    while size > 60 and max(font(size).getlength(p_) for p_ in parts) > X1 - X0 - 20:   # 2.3: nur wenn eine Zeile nicht passt
        size -= 4
    fnt = font(int(size * sc))
    for i, ln in enumerate(parts):
        cy = y0 + (y1 - y0) * (i + 1) / (len(parts) + 1) + dy
        if gelb and gelb in ln:
            pre, post = ln.split(gelb, 1)
            segs = [(pre, (255, 255, 255)), (gelb, YELLOW), (post, (255, 255, 255))]
        elif gelb and " " in gelb and not any(gelb in p_ for p_ in parts):
            # 2.2: Hervorhebung ueber einen Zeilenumbruch hinweg (Wort fuer Wort)
            gw = {w.strip(".,!?:") for w in gelb.split()}
            segs = []
            for j, w in enumerate(ln.split(" ")):
                segs.append((w + (" " if j < len(ln.split(" ")) - 1 else ""),
                             YELLOW if w.strip(".,!?:") in gw else (255, 255, 255)))
        else:
            segs = [(ln, (255, 255, 255))]
        total = sum(fnt.getlength(t) for t, _ in segs)
        x = (X0 + X1) / 2 - total / 2
        for t, col in segs:
            if t:
                text_center(img, (x, cy), t, int(size * sc), col, a, stroke=4, stroke_fill=NAVY, anchor="lm")
                x += fnt.getlength(t)


def chapter_state(tl, f):
    """(aktives Kapitel, Banner sichtbar, Leiste sichtbar, alle erledigt)"""
    for s in tl["scenes"]:
        if s["f0"] <= f < s["f1"]:
            return s
    return tl["scenes"][-1]


def draw_banner(img, tl, f):
    sc = tl["scenes"]
    # Banner-Bereiche: zusammenhaengende Szenen mit kapitel != None
    for i, s in enumerate(sc):
        if s["kapitel"] is None:
            continue
        k = s["kapitel"]
        first = i == 0 or sc[i - 1]["kapitel"] is None
        last = i == len(sc) - 1 or sc[i + 1]["kapitel"] is None
        f_in = s["f0"] if first else s["f0"] - 100000
        f_out = s["f1"] - 4 if last else None
        if not (s["f0"] - 2 <= f < s["f1"] + (6 if last else 0)):
            continue
        a = slide(f, f_in + 2, f_out, 8)
        dx = -80 * (1 - a)
        box = (X0 + dx, TOP, X1 + dx, TOP + 84)
        card(img, box, a)
        label = f"{k + 1} · {tl['kapitel'][k]}"
        text_center(img, (X0 + 34 + dx, TOP + 36), label, SMALL, (255, 255, 255), a, anchor="lm")
        ks = [x for x in sc if x["kapitel"] == k]
        c0, c1 = ks[0]["f0"], ks[-1]["f1"]
        prog = ease_in_out((f - c0 - 4) / max(1, c1 - c0 - 10))
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        bx0, bx1, by = X0 + 34 + dx, X1 - 34 + dx, TOP + 66
        d.rounded_rectangle((bx0, by, bx1, by + 8), 4, fill=(255, 255, 255, int(50 * a)))
        if prog > 0:
            d.rounded_rectangle((bx0, by, bx0 + (bx1 - bx0) * prog, by + 8), 4, fill=(*TURQ, int(255 * a)))
        img.alpha_composite(layer)


def draw_chapter_bar(img, tl, f):
    sc = tl["scenes"]
    n = len(tl["kapitel"])
    if n == 0:
        return
    cur = chapter_state(tl, f)
    idx = sc.index(cur)
    show_from = next((s["f0"] for s in sc if s["kapitel"] is not None), None)
    if show_from is None:
        return
    # Sichtbar nur in Szenen mit Kapitel (bei kapitel null ausgeblendet)
    chap_scenes = [i for i, s in enumerate(sc) if s["kapitel"] is not None]
    finale = None
    last = chap_scenes[-1]
    for i, s_ in enumerate(sc):
        if i > last and "Kapitel-Leiste" in (s_.get("visual", "") + str(s_.get("start", ""))):
            last = i
            finale = i
    vis_ranges = [(sc[chap_scenes[0]]["f0"], sc[last]["f1"])]
    a = 0.0
    for r0, r1 in vis_ranges:
        a = max(a, slide(f, r0 + 4, r1 - 5, 8))
    if a <= 0:
        return
    in_finale = finale is not None and sc[finale]["f0"] <= f < sc[finale]["f1"]
    y0 = BAR_Y
    gap = 14
    pw = (X1 - X0 - gap * (n - 1)) / n
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # Status je Kapitel
    active = cur["kapitel"]
    done = set()
    for s in sc:
        if s["kapitel"] is not None and s["f1"] <= f:
            done.add(s["kapitel"])
    if in_finale:
        done = set(range(n))
        active = None
    pills = []
    for j in range(n):
        x0 = X0 + j * (pw + gap)
        box = (x0, y0, x0 + pw, y0 + 56)
        # Pop des Hakens beim Abschluss
        done_f = next((s["f1"] for s in sc if s["kapitel"] == j), None)
        if j in done:
            k = ease_out_back((f - done_f) / 6, 2.6) if done_f and f >= done_f else 1.0
            fill, border, txt = (*GREEN, int(230 * a)), (*GREEN, int(255 * a)), (255, 255, 255)
        elif j == active:
            k = 1.0
            fill, border, txt = (*TURQ, int(235 * a)), (255, 255, 255, int(255 * a)), NAVY
        else:
            k = 1.0
            fill, border, txt = (*NAVY, int(200 * a)), (*GREY, int(255 * a)), GREY
        d.rounded_rectangle(box, 28, fill=fill, outline=border, width=2)
        pills.append((box, j, txt, k))
    img.alpha_composite(layer)
    for box, j, txt, k in pills:
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        if j in done:
            lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            dd = ImageDraw.Draw(lay)
            s_ = 30 * max(0.0, k)
            check_icon(dd, cx - 34, cy, s_, (255, 255, 255, int(255 * a)), width=max(1, int(7 * k)))
            img.alpha_composite(lay)
            text_center(img, (cx + 22, cy + 1), str(j + 1), SMALL, txt, a)
        else:
            text_center(img, (cx, cy + 1), str(j + 1), SMALL, txt, a)
    if in_finale:
        t = (f - sc[finale]["f0"] - 8) / 18
        for box, *_ in pills:
            sweep(img, box, t, 28, a)


def draw_term(img, tl, f, anchors):
    begriff = tl.get("begriff")
    if not begriff:
        return
    for s in tl["scenes"]:
        b = s["beats"].get(begriff)
        if b is None:
            b = next((w["f0"] - 3 for w in s["words"] if w["w"].strip(".,!?:").lower() == begriff.lower()), None)
        if b is None:
            continue
        f_in, f_out = b + 1, s["f1"] - 6
        if not (f_in - 1 <= f < s["f1"] + 4):
            continue
        a = slide(f, f_in, f_out, 8)
        dy = -60 * (1 - a)
        if isinstance(tl.get("hook"), dict):            # neues Format: Karte y 230-380, nur der Begriff
            oy = 110 if s.get("kapitel") is not None else 0     # unter dem Kapitel-Banner
            box = (X0, 230 + oy + dy, X1, 380 + oy + dy)
            card(img, box, a, border=YELLOW)
            text_center(img, ((X0 + X1) / 2, 305 + oy + dy), begriff.upper(), 96, YELLOW, a)
            sweep(img, box, (f - f_in - 4) / 16, 28, a)
            continue
        box = (X0, TOP + dy, X1, TOP + 172 + dy)
        card(img, box, a, border=YELLOW)
        text_center(img, ((X0 + X1) / 2, TOP + 66 + dy), begriff.upper(), BIG, YELLOW, a)
        # Definition aus dem Sprechtext nach dem Begriff (z. B. 'das Richtige zum besten Preis einkaufen')
        txt = s["text"]
        idx = txt.lower().find(begriff.lower())
        rest = txt[idx + len(begriff):].lstrip(":, ").split(".")[0] if idx >= 0 else ""
        mm = re.search(r"darunter 1 Zeile: '([^']+)'", s.get("visual", ""))
        if mm:
            rest = mm.group(1)
        if rest:
            text_center(img, ((X0 + X1) / 2, TOP + 132 + dy), rest[0].upper() + rest[1:], SMALL, (255, 255, 255), a)
        sweep(img, box, (f - f_in - 4) / 16, 28, a)


def fmt_num(v, dec=0):
    s = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def draw_labels(img, f, anchors):
    if not anchors:
        return
    for lab in anchors.get("labels", []):
        if not (lab["f0"] <= f < lab["f1"] + 6):
            continue
        a = slide(f, lab["f0"], lab["f1"], 6)
        pos = anchors["anchors"][lab["anchor"]][f]
        x, y, z = pos
        if z <= 0:
            continue
        t = ease_out((f - lab["count_f0"]) / max(1, lab["count_f1"] - lab["count_f0"]))
        v = lab["from"] + (lab["to"] - lab["from"]) * t
        s = lab["fmt"].format(fmt_num(round(v), lab.get("dec", 0)))
        fnt = font(BIG)
        half = fnt.getlength(s) / 2 + 30
        x = max(X0 + half, min(X1 - half, x))
        y = max(TOP + 60, min(1180, y + lab.get("dy", 0)))
        pop_k = 1 + 0.12 * math.sin(math.pi * clamp01((f - lab["count_f1"]) / 6)) if f >= lab["count_f1"] else 1.0
        text_center(img, (x, y), s, BIG, GOLD, a, stroke=8, stroke_fill=NAVY, scale=pop_k)


def draw_notification(img, tl, f, anchors):
    """Handy-Benachrichtigung ueber dem 3D-Handy (Anker 'phone_notify')."""
    if not anchors or "phone_notify" not in anchors.get("anchors", {}):
        return
    for s in tl["scenes"]:
        m = re.search(r"Benachrichtigung über dem Handy: '([^']+)'", s.get("visual", ""))
        if not m or not (s["f0"] <= f < s["f1"]):
            continue
        f_in = s["f0"] + 6
        a = slide(f, f_in, s["f1"] - 5, 6)
        if a <= 0:
            return
        x, y, z = anchors["anchors"]["phone_notify"][f]
        txt = m.group(1)
        title, _, body = txt.partition(": ")
        fs = font(SMALL)
        w = max(fs.getlength(title + ":"), font(56).getlength(body)) + 150
        x = max(X0 + w / 2, min(X1 - w / 2, x))
        y = max(TOP + 80, min(700, y)) + 30 * (1 - a)
        sc_ = 0.85 + 0.15 * ease_out_back(clamp01((f - f_in) / 7), 3.0)
        box = (x - w / 2 * sc_, y - 70 * sc_, x + w / 2 * sc_, y + 70 * sc_)
        card(img, box, a, border=YELLOW, fill=(255, 255, 255), fill_a=0.97, radius=34)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        cx, cy = box[0] + 62 * sc_, y
        d.ellipse((cx - 38 * sc_, cy - 38 * sc_, cx + 38 * sc_, cy + 38 * sc_), fill=(139, 74, 31, int(255 * a)))
        img.alpha_composite(lay)
        text_center(img, (cx, cy + 2), "!", 60, YELLOW, a, scale=sc_)
        text_center(img, (box[0] + 120 * sc_, y - 26 * sc_), title + ":", SMALL, (139, 74, 31), a, scale=sc_, anchor="lm")
        text_center(img, (box[0] + 120 * sc_, y + 24 * sc_), body, 56, NAVY, a, scale=sc_, anchor="lm")


def draw_big_overlay(img, tl, f):
    """[Overlay] '<Text>' gross und gruen/gelb: grosse Einblendung mit Pop (z. B. '−18 %')."""
    for s in tl["scenes"]:
        m = re.search(r"\[Overlay\] '([^']+)' gro(?:ß|ss) und (gr\u00fcn|gelb)", s.get("visual", ""))
        if not m or not (s["f0"] <= f < s["f1"] + 4):
            continue
        txt, col = m.group(1), GREEN if m.group(2) == "grün" else YELLOW
        hl = next((w["f0"] for w in s["words"] if w["hl"]), s["f0"] + 6)
        f_in = hl - 2
        a = slide(f, f_in, s["f1"] - 4, 5)
        if a <= 0:
            continue
        sc = 0.6 + 0.4 * ease_out_back(clamp01((f - f_in) / 7), 3.0)
        text_center(img, ((X0 + X1) / 2, 392), txt, 180, col, a, stroke=10, stroke_fill=NAVY, scale=sc)


_AR_CACHE = {}


def draw_ar(img, tl, f):
    """2.4: Ebene [AR] (durch Leas Brille): ganz dezente Scanlines und ein leichter tuerkiser Randschimmer, kein
    Flackern. Nur in Szenen, deren 'visual' [AR] … [/AR] enthaelt; Ein- und Ausblenden ueber 6 Frames."""
    s = next((x for x in tl["scenes"] if x["f0"] <= f < x["f1"]), None)
    if s is None or "[AR]" not in s.get("visual", ""):
        return
    a = min(1.0, (f - s["f0"] + 1) / 6, (s["f1"] - f) / 6)
    if a <= 0:
        return
    if "lay" not in _AR_CACHE:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for y in range(0, img.size[1], 6):
            d.line([(0, y), (img.size[0], y)], fill=(46, 230, 214, 14), width=1)
        import numpy as np
        h, w = img.size[1], img.size[0]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.maximum(np.abs(xx - w / 2) / (w / 2), np.abs(yy - h / 2) / (h / 2))
        glow = (np.clip((r - 0.78) / 0.22, 0, 1) ** 2 * 70).astype(np.uint8)
        g = np.zeros((h, w, 4), np.uint8)
        g[..., 0], g[..., 1], g[..., 2], g[..., 3] = 46, 230, 214, glow
        lay = Image.alpha_composite(lay, Image.fromarray(g, "RGBA"))
        _AR_CACHE["lay"] = lay
    lay = _AR_CACHE["lay"]
    if a < 1:
        lay = lay.copy()
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)


def overlay_frame(tl, f, anchors):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_big_overlay(img, tl, f)
    draw_notification(img, tl, f, anchors)
    draw_hook(img, tl, f)
    draw_banner(img, tl, f)
    draw_chapter_bar(img, tl, f)
    draw_term(img, tl, f, anchors)
    draw_labels(img, f, anchors)
    draw_ar(img, tl, f)
    if anchors and anchors.get("hud"):                # 2.5: Spielanzeige [GAME] (nur wenn die Regie sie liefert)
        try:
            from . import spielanzeige as SA
        except ImportError:
            import spielanzeige as SA
        hud = anchors["hud"][f] if f < len(anchors["hud"]) else None
        SA.draw_game(img, hud, f, anchors)
    draw_subtitles(img, tl, f)
    return img


_G = {}


def _init(tl, anchors, outdir):
    _G.update(tl=tl, anchors=anchors, outdir=outdir)


def _work(f):
    p = os.path.join(_G["outdir"], f"{f:05d}.png")
    overlay_frame(_G["tl"], f, _G["anchors"]).save(p, compress_level=1)
    return f


def overlay_frames(tl, outdir, frames, anchors_path, procs=4):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    anchors = json.loads(Path(anchors_path).read_text()) if Path(anchors_path).exists() else None
    with Pool(procs, initializer=_init, initargs=(tl, anchors, str(outdir))) as pool:
        for _ in pool.imap_unordered(_work, frames, chunksize=8):
            pass


# ================================================================== Screen-Texturen (1280x720)
SW, SH = 1280, 720


def _screen_bg(f, flicker=0.0):
    img = Image.new("RGBA", (SW, SH), (*NAVY, 255))
    d = ImageDraw.Draw(img)
    for x in range(0, SW, 160):
        d.line([(x, 110), (x, SH)], fill=(46, 230, 214, 14), width=2)
    for y in range(110, SH, 160):
        d.line([(0, y), (SW, y)], fill=(46, 230, 214, 14), width=2)
    # App-Kopfzeile
    d.rounded_rectangle((36, 30, SW - 36, 96), 22, fill=(36, 32, 74, 255), outline=(*TURQ, 255), width=2)
    for i, col in enumerate((RED, YELLOW, GREEN)):
        d.ellipse((64 + 34 * i, 52, 86 + 34 * i, 74), fill=(*col, 255))
    if flicker > 0:
        import random
        r = random.Random(int(f))
        for _ in range(int(14 * flicker)):
            y = r.randrange(0, SH)
            d.rectangle((0, y, SW, y + r.randint(2, 10)), fill=(46, 230, 214, int(90 * flicker)))
    return img


def _t(img, xy, s, size, col, alpha=1.0, anchor="lm"):
    d = ImageDraw.Draw(img)
    d.text(xy, s, font=font(size), fill=(*col, int(255 * alpha)), anchor=anchor)


_EP_SCREENS = {}


def episode_screens(slug):
    """Folgenspezifische Bildschirm-Inhalte: assets/screens/<slug>.py mit frame(tl, szene, f) -> Bild oder None."""
    if slug not in _EP_SCREENS:
        p = Path(__file__).resolve().parent.parent / "assets" / "screens" / f"{slug.replace('-', '_')}.py"
        mod = None
        if p.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"ep_screens_{slug}", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        _EP_SCREENS[slug] = mod
    return _EP_SCREENS[slug]


def screen_frame(tl, f):
    sc = tl["scenes"]
    s = chapter_state(tl, f)
    i = sc.index(s)
    ep = episode_screens(tl["slug"])
    if ep is not None:
        return ep.frame(tl, s, f)
    if s["set"] != "studio" and not s.get("screen"):
        return None
    img = _screen_bg(f, flicker=max(0.0, 1 - (f - s["f0"]) / 12) if i > 0 and sc[i - 1]["set"] != "studio" else 0.0)
    b = s["beats"]
    vis = s.get("visual", "")
    if s.get("screen"):
        return screen_lines(img, s, f)
    if "Kassenbon" in vis or "Zähler zählt schnell" in vis:
        return screen_bon(img, s, f, vis)
    if "Anruffenster" in vis or "Wellenform zappelt" in vis or "Stoppuhr stoppt" in vis or \
            re.search(r"\[Screen\] '([^']+)'", vis):
        return screen_calls(img, s, f, vis)
    if "Zähler zählt hoch" in vis:            # Code-Zaehler (echte Zeilenzahl)
        n = zeilen()
        f_a, f_b = counter_window(s)
        v = int(round(n * ease_out(clamp01((f - f_a) / max(1, f_b - f_a)))))
        pk = 1 + 0.12 * math.sin(math.pi * clamp01((f - f_b) / 6)) if f >= f_b else 1.0
        _t(img, (SW / 2, 300), "index.html", 64, (170, 170, 200), anchor="mm")
        d = ImageDraw.Draw(img)
        d.text((SW / 2, 470), f"{v} Zeilen", font=font(int(170 * pk)), fill=(*YELLOW, 255), anchor="mm")
        return img
    mrech = re.search(r"Rechnung groß: '([^']+)'", vis)
    if mrech:                                # Rechnung (hoechstens eine pro Szene)
        expr = mrech.group(1)
        left, _, right = expr.partition(" = ")
        t1, t2 = calc_times(s)
        a = ease_out((f - t1) / 7)
        if a > 0:
            fs_ = 150
            while font(fs_).getlength(left) > SW - 120:
                fs_ -= 6
            _t(img, (SW / 2, 270 - 30 * (1 - a)), left, fs_, (255, 255, 255), a, anchor="mm")
        a = ease_out((f - t2) / 7)
        if a > 0:
            total = int(re.sub(r"\D", "", right))
            v = int(round(total * ease_out((f - t2) / 16)))
            pk = 1 + 0.15 * math.sin(math.pi * clamp01((f - t2 - 16) / 6)) if f >= t2 + 16 else 1.0
            d = ImageDraw.Draw(img)
            d.text((SW / 2, 480 - 30 * (1 - a)), "= " + fmt_num(v) + " €", font=font(int(170 * pk)),
                   fill=(*GREEN, int(255 * a)), anchor="mm")
        return img
    # Screen-Typografie: zwei Groessen (SCR_SMALL 64, SCR_BIG 150 fuer Zahlen)
    if "18" in b and "15,50" in b:      # Szene: Angebote vergleichen
        for row, (key, lab, val, col, suf) in enumerate([("18", "Bisher:", 18.0, RED, " pro Sack"),
                                                         ("15,50", "Bestes Angebot:", 15.5, GREEN, "")]):
            bf = b[key]
            a = ease_out((f - (bf - 6)) / 8)
            if a <= 0:
                continue
            y = 235 + row * 180
            dx = -60 * (1 - a)
            v = val * ease_out((f - (bf - 2)) / 10)
            num = f"{v:.2f}".replace(".", ",") + " €"
            full = f"{val:.2f}".replace(".", ",") + " €"
            lw = font(64).getlength(lab + " ")
            nw = font(150).getlength(full)
            sw = (font(64).getlength(" " + suf.strip()) + 20) if suf else 0
            x0 = SW / 2 - (lw + nw + sw) / 2 + dx
            _t(img, (x0, y), lab, 64, (255, 255, 255), a)
            _t(img, (x0 + lw, y), num, 150, col, a)
            if suf:
                _t(img, (x0 + lw + nw + 20, y + 18), suf.strip(), 64, (200, 200, 220), a)
    elif "2,50" in b and "60" in b:     # Ersparnis rechnen
        y1, y2 = 235, 405
        x0 = SW / 2 - (font(150).getlength("2,50 € × 60 ") + font(64).getlength("Säcke")) / 2
        a = ease_out((f - (b["2,50"] - 4)) / 7)
        if a > 0:
            _t(img, (x0, y1 - 30 * (1 - a)), "2,50 €", 150, GOLD, a)
        x = x0 + font(150).getlength("2,50 € ")
        a = ease_out((f - (b["60"] - 4)) / 7)
        if a > 0:
            _t(img, (x, y1 - 30 * (1 - a)), "× 60", 150, (255, 255, 255), a)
            _t(img, (x + font(150).getlength("× 60 "), y1 + 18 - 30 * (1 - a)), "Säcke", 64, (200, 200, 220), a)
        a = ease_out((f - (b["150"] - 4)) / 7)
        if a > 0:
            v = int(round(150 * ease_out((f - b["150"]) / 14)))
            _t(img, (SW / 2, y2 - 30 * (1 - a)), f"= {v} €", 150, GREEN, a, anchor="mm")
    elif "schreibt" in b:               # Mail schreiben
        lines = ["Anfrage: 60 Sack Mehl pro Monat", "Bitte um eine Probelieferung", "Freundliche Grüße, Kalle"]
        starts = [b["schreibt"], b.get("Höflich", b["schreibt"] + 40) + 4, b.get("Probelieferung", b["schreibt"] + 80) + 14]
        _t(img, (90, 170), "An: neuer Lieferant", 64, (170, 170, 200))
        y = 260
        cur_xy = None
        for ln, st in zip(lines, starts):
            n = int(max(0, (f - st) / 1.1))
            shown = ln[:min(len(ln), n)]
            if shown:
                _t(img, (90, y), shown, 76, (255, 255, 255))
                if n <= len(ln) + 2:
                    cur_xy = (90 + font(76).getlength(shown) + 8, y)
            y += 92
        if cur_xy is None:
            cur_xy = (90, 260)
        if (f // 8) % 2 == 0:
            d = ImageDraw.Draw(img)
            d.rectangle((cur_xy[0], cur_xy[1] - 38, cur_xy[0] + 10, cur_xy[1] + 38), fill=(*TURQ, 255))
    elif "1.800" in b:                  # Beschaffung: aufs Jahr
        bf = b["1.800"]
        _t(img, (SW / 2, 235), "150 € × 12", 150, GOLD, anchor="mm")
        a = ease_out((f - (bf - 4)) / 7)
        if a > 0:
            v = int(round(1800 * ease_out((f - bf) / 40)))
            _t(img, (SW / 2, 405 - 30 * (1 - a)), "= " + fmt_num(v) + " €", 150, GREEN, a, anchor="mm")
    return img


_NUMRE = re.compile(r"\d{1,3}(?:\.\d{3})+|\d+")


def _count_text(line, t):
    """Alle Zahlen einer Zeile zaehlen mit ease-out hoch (t 0..1); Format bleibt (Tausenderpunkt)."""
    k = ease_out(t)

    def rep(m):
        v = int(m.group(0).replace(".", ""))
        return fmt_num(int(round(v * k)))
    return _NUMRE.sub(rep, line)


def _split_long(lines):
    """Rechnungen am '=' umbrechen, damit die Zahlen gross bleiben."""
    out = []
    for ln in lines:
        if len(ln) > 14 and " = " in ln:
            l1, l2 = ln.split(" = ", 1)
            if len(l1) > 16 and " − " in l1:          # sehr lange Rechnung: auch vor dem Minus umbrechen
                a_, b_ = l1.rsplit(" − ", 1)
                out += [a_, "− " + b_]
            else:
                out.append(l1)
            out.append("= " + l2)
        else:
            out.append(ln)
    return out


_BIGTOK = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+|[€×−+=·])")


def draw_mixed(img, xy, text, big, small, col, alpha=1.0, anchor="mm", max_w=None):
    """Zahlen, € und Rechenzeichen gross, Woerter klein (Grundlinie gemeinsam)."""
    parts = [p for p in _BIGTOK.split(text) if p]
    while True:
        segs = [(p, big if _BIGTOK.fullmatch(p.strip()) else small) for p in parts]
        w = sum(font(sz).getlength(p) for p, sz in segs)
        if max_w is None or w <= max_w or big < 60:
            break
        big, small = int(big * 0.94), int(small * 0.94)
    x, y = xy
    if anchor == "mm":
        x -= w / 2
    d = ImageDraw.Draw(img)
    for p, sz in segs:
        d.text((x, y + big * 0.36), p, font=font(sz), fill=(*col, int(255 * alpha)), anchor="ls")
        x += font(sz).getlength(p)
    return big


def screen_lines(img, s, f):
    """Screen-Zeilen aus dem Episoden-JSON: jede Zeile erscheint (Slide von links + Fade 6 Frames),
    Zahlen zaehlen mit ease-out hoch (18 Frames). Zeitpunkt: Beat, dessen Wort in der Zeile vorkommt,
    sonst gestaffelt. Mail-Fenster (Betreff) erscheint beim ersten Beat mit Stagger 4 Frames."""
    lines = _split_long(s["screen"])
    beats = s.get("beat_list", [])
    mail = lines[0].startswith("Betreff")
    t_prev = s["f0"] + 4
    starts = []
    for k, ln in enumerate(lines):
        if mail:
            t = (beats[0]["f_beat"] if beats else s["f0"] + 6) + 4 * k
        else:
            hit = next((bt["f_beat"] for bt in beats if bt["wort"] in ln), None)
            if k == 0 and hit is None and beats:
                hit = beats[0]["f_beat"]
            t = hit if hit is not None and hit >= t_prev - 2 else t_prev + (12 if k else 0)
        starts.append(t)
        t_prev = t
    d = ImageDraw.Draw(img)
    if mail:
        d.rounded_rectangle((60, 130, SW - 60, SH - 40), 26, fill=(245, 241, 232, 255))
        d.rectangle((60, 130, SW - 60, 200), fill=(46, 230, 214, 255))
        d.text((100, 165), "Neue Nachricht", font=font(48), fill=(*NAVY, 255), anchor="lm")
    n = len(lines)
    top, bot = (250, SH - 120) if mail else (170, SH - 60)
    for k, ln in enumerate(lines):
        a = ease_out((f - starts[k]) / 6)
        if a <= 0:
            continue
        txt = _count_text(ln, (f - starts[k]) / 18) if not mail else ln
        y = top + (bot - top) * (k + 0.5) / n
        x = (SW / 2 if not mail else 100) - 60 * (1 - a)
        col = (255, 255, 255) if not mail else NAVY
        if not mail and ln.startswith("="):
            col = RED if "600 €" in ln else GREEN
        if not mail and ln.startswith("Nur versprochen"):
            col = (170, 170, 200)
        big = (190 if n <= 2 else 150) if not mail else 104
        draw_mixed(img, (x, y), txt, big, 64 if not mail else 58, col, a, anchor="mm" if not mail else "lm",
                   max_w=SW - 120 if not mail else SW - 200)
    return img


def _wave(d, box, f, seed, amp=1.0, hektisch=False, col=TURQ):
    import random as _r
    x0, y0, x1, y1 = box
    cy = (y0 + y1) / 2
    rr = _r.Random(seed)
    ph = [rr.uniform(0, 6.28) for _ in range(3)]
    pts = []
    n = 48
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        sp = 0.55 if not hektisch else 1.6
        v = (math.sin(k * 0.55 + f * sp + ph[0]) * 0.6 + math.sin(k * 1.3 - f * sp * 1.4 + ph[1]) * 0.4)
        env = 0.5 + 0.5 * math.sin(f * (0.18 if not hektisch else 0.6) + ph[2])
        if hektisch:
            v *= 1.4 + 0.6 * math.sin(k * 3.1 + f * 2.3)
        pts.append((x, cy + v * (y1 - y0) * 0.42 * amp * env))
    d.line(pts, fill=(*col, 255), width=6, joint="curve")


def screen_bon(img, s, f, vis):
    """Kassenbon als roter Faden (Folge 'Der teuerste Rabatt'): weisser Bon rollt von oben herein,
    Zeilen erscheinen nacheinander; Verlust rot (blinkt), Gewinn gruen. Zaehler zaehlt schnell hoch."""
    t = f - s["f0"]
    d = ImageDraw.Draw(img)
    m = re.search(r"Zähler zählt schnell hoch bis '(\d+)'", vis)
    if m:
        n = int(m.group(1))
        hl = next((w["f0"] for w in s["words"] if w["hl"]), s["f0"] + 30)
        v = int(round(n * ease_out((f - s["f0"] - 4) / max(1, hl - s["f0"] + 6))))
        pk = 1 + 0.12 * math.sin(math.pi * clamp01((f - hl - 2) / 6)) if v >= n else 1.0
        d.text((SW / 2, 505), "BREZELN IM MÜLL", font=font(50), fill=(170, 170, 200, 255), anchor="mm")
        d.text((SW / 2, 622), str(v), font=font(int(170 * pk)), fill=(*RED, 255), anchor="mm")
        return img
    rows = []                                       # (Text, Farbe, gross?)
    if "Kassenbon rollt ins Bild" in vis:
        rows = [("KOSTEN      0,90 €", (40, 40, 60), False), ("PREIS       1,20 €", (40, 40, 60), False)]
    elif "Kassenbon-Summe" in vis:
        rows = [("KOSTEN      0,90 €", (40, 40, 60), False), ("PREIS       1,20 €", (40, 40, 60), False),
                ("+0,30 €", (30, 170, 90), True), ("MARGE", (30, 170, 90), False)]
    elif "−0,06" in vis:
        rows = [("KOSTEN      0,90 €", (40, 40, 60), False), ("PREIS −30 % 0,84 €", (200, 50, 55), False),
                ("−0,06 €", (220, 40, 50), True)]
    elif "= +24" in vis:
        rows = [("40 × 0,60 €", (40, 40, 60), True), ("= +24 €", (30, 170, 90), True)]
    roll = ease_out((t - 2) / 12)
    bw, bx = 640, (SW - 640) / 2
    bh = 120 + sum(150 if g else 90 for _, _, g in rows)
    by1 = 60 + (bh) * roll
    d.rectangle((bx, 40, bx + bw, by1), fill=(250, 248, 240, 255))
    for k_ in range(int(bw / 32)):                  # Zackenrand unten
        x = bx + k_ * 32
        d.polygon([(x, by1), (x + 16, by1 + 16), (x + 32, by1)], fill=(250, 248, 240, 255))
    d.text((SW / 2, 85), "BÄCKEREI KALLE", font=font(44), fill=(90, 90, 110, 255), anchor="mm")
    y = 150
    hl = [w["f0"] for w in s["words"] if w["hl"]] or [s["f0"] + 10]
    for k_, (txt, col, big) in enumerate(rows):
        start = s["f0"] + 6 + 8 * k_ if not big else hl[0] - 4
        h = 150 if big else 90
        if y + h / 2 < by1 and f >= start:
            a = ease_out((f - start) / 5)
            if big and col[0] > 200 and int((f - start) / 6) % 2 == 1:
                a *= 0.35                           # Verlust blinkt
            sz = 130 if big else 62
            d.text((SW / 2, y + h / 2), txt, font=font(sz), fill=(*col, int(255 * a)), anchor="mm")
        y += h
    return img


def screen_calls(img, s, f, vis):
    """Studio-Screen fuer die Telefon-Folge: Anruffenster mit Wellenformen, Stoppuhr, hektische Wellenform,
    Text-Screen ([Screen] '...')."""
    d = ImageDraw.Draw(img)
    t = f - s["f0"]
    if "Anruffenster" in vis:
        for k, lab in enumerate(["MÜHLE A", "MÜHLE B", "MÜHLE C"]):
            x0 = 60 + k * 400
            a = ease_out((t - 4 - 5 * k) / 6)
            if a <= 0:
                continue
            d.rounded_rectangle((x0, 140, x0 + 360, 660), 24, fill=(36, 32, 74, 255), outline=(*TURQ, int(255 * a)), width=4)
            d.text((x0 + 180, 200), lab, font=font(56), fill=(255, 255, 255, int(255 * a)), anchor="mm")
            d.ellipse((x0 + 150, 250, x0 + 210, 310), fill=(*GREEN, 255))
            d.text((x0 + 180, 282), "☎" if False else "●", font=font(30), fill=(255, 255, 255, 255), anchor="mm")
            _wave(d, (x0 + 30, 360, x0 + 330, 600), f, 11 + k)
        return img
    if "Stoppuhr stoppt" in vis:
        m = re.search(r"Stoppuhr stoppt bei (\d+):(\d+)", vis)
        stop = int(m.group(1)) * 60 + int(m.group(2)) if m else 40
        hl = next((w["f0"] for w in s["words"] if w["hl"]), s["f1"] - 20)
        sec = min(stop, int(stop * ease_out((f - s["f0"]) / max(1, hl - s["f0"]))))
        done = sec >= stop
        cx, cy, r = SW / 2, 400, 230
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(*(GREEN if done else TURQ), 255), width=14)
        d.rectangle((cx - 30, cy - r - 60, cx + 30, cy - r - 10), fill=(*TURQ, 255))
        a = 2 * math.pi * sec / 60
        d.line([(cx, cy), (cx + (r - 50) * math.sin(a), cy - (r - 50) * math.cos(a))], fill=(*RED, 255), width=12)
        d.text((cx, cy + 90), f"0:{sec:02d}", font=font(150), fill=(*(GREEN if done else (255, 255, 255)), 255),
               anchor="mm")
        return img
    if "Wellenform zappelt" in vis:
        d.rounded_rectangle((90, 140, SW - 90, 660), 26, fill=(36, 32, 74, 255), outline=(*RED, 255), width=5)
        d.text((SW / 2, 210), "STAMMLIEFERANT", font=font(72), fill=(255, 255, 255, 255), anchor="mm")
        _wave(d, (150, 290, SW - 150, 620), f, 77, amp=1.0, hektisch=True, col=YELLOW)
        return img
    m = re.search(r"\[Screen\] '([^']+)'", vis)
    if m:
        a = ease_out((t - 6) / 8)
        draw_mixed(img, (SW / 2, 400 - 30 * (1 - a)), m.group(1), 170, 90, (255, 255, 255), a, max_w=SW - 120)
    return img


def zeilen():
    p = Path(__file__).resolve().parent.parent / "website" / "meta.json"
    return int(json.loads(p.read_text())["zeilen"])


def screen_textures(tl, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    blank = outdir / "blank.png"
    _screen_bg(0).save(blank)
    for f in range(tl["frames"]):
        p = outdir / f"{f:05d}.png"
        im = screen_frame(tl, f)
        if p.exists() or p.is_symlink():
            p.unlink()
        if im is None:
            os.symlink("blank.png", p)
        else:
            im.convert("RGB").save(p, compress_level=1)
