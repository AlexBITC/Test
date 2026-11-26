"""2D-Nachbearbeitung: Hintergrund, Bokeh, Staub, Blender-Render (Screen-Blend), Lichtblitz,
Schlagzeile (oben, ein Schluesselwort gold) und wortgenaue Untertitel (unten) -> H.264.

  python3 -m motivation.post <renderdir> <out.mp4> [--frames 0,100] [--audio mix.wav]
Alle zeitabhaengigen Ebenen sind periodisch in N Frames (nahtloser Loop).
"""
from __future__ import annotations

import json
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
OUT = ROOT / "out" / "motivation"
W, H = 1080, 1920
GOLD = (245, 196, 81)
WHITE = (255, 255, 255)
F_HEAD = str(HERE / "fonts" / "Anton-Regular.ttf")
F_SUB = str(HERE / "fonts" / "Inter-Black.otf")

TL = json.loads((OUT / "timeline.json").read_text())
FPS, N = TL["fps"], TL["n_frames"]
SENT = {s["id"]: s for s in TL["sentences"]}


def fr(t):
    return t * FPS


def word_frame(sid, word):
    for w in SENT[sid]["words"]:
        if w["w"].lower().strip(".,?!") == word:
            return fr(w["start"])
    raise KeyError(word)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lin(f, a, b):
    return clamp((f - a) / (b - a)) if b != a else float(f >= b)


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


NOW = word_frame(10, "now")
LOOP0 = N - 16
FLASH_PEAK = N - 10

# ------------------------------------------------------------------ Schlagzeilen
# (Start-Frame, Zeilen); *Wort* = gold. Ende = Start der naechsten.
HEADS = [
    (0, ["STILL WAITING FOR", "*TOMORROW?*"]),
    (fr(SENT[3]["start"]) - 4, ["THE MOST", "*DANGEROUS* WORD"]),
    (fr(SENT[4]["start"]) - 4, ["THE MOUNTAIN", "GETS *TALLER*"]),
    (fr(SENT[5]["start"]) - 4, ["THE *FIRST*", "STEP"]),
    (fr(SENT[6]["start"]) - 4, ["JUST *5*", "MINUTES"]),
    (fr(SENT[7]["start"]) - 4, ["DO IT", "*TODAY*"]),
    (fr(SENT[8]["start"]) - 6, ["TIME", "*RUNS OUT*"]),
    (fr(SENT[9]["start"]) - 4, ["STOP", "*WAITING*"]),
    (fr(SENT[10]["start"]) - 4, ["START", "*NOW*"]),
    (LOOP0, ["STILL WAITING FOR", "*TOMORROW?*"]),     # Loop: gleiche Schlagzeile wie Frame 0
]
HEAD_TOP, HEAD_BOTTOM = 190, 520      # Bereich der Schlagzeile (px); TikTok-UI oben frei
HEAD_MAXW = 900


def parse(line):
    """'GETS *TALLER*' -> [('GETS', False), ('TALLER', True)]"""
    res, gold = [], False
    for tok in line.split(" "):
        if tok.startswith("*"):
            gold = True
        res.append((tok.strip("*"), gold))
        if tok.endswith("*"):
            gold = False
    return res


_font_cache = {}


def font(path, size):
    k = (path, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(path, size)
    return _font_cache[k]


def layout_head(lines):
    """Groesse je Zeile: zweite (Gold-)Zeile groesser. Rueckgabe Liste (tokens, size, y)."""
    sizes = []
    for i, ln in enumerate(lines):
        target = 118 if i == 0 and len(lines) > 1 else 190
        txt = ln.replace("*", "")
        s = target
        while font(F_HEAD, s).getlength(txt) > HEAD_MAXW and s > 40:
            s -= 2
        sizes.append(s)
    gap = 12
    total = sum(int(s * 1.0) for s in sizes) + gap * (len(lines) - 1)
    y = (HEAD_TOP + HEAD_BOTTOM) / 2 - total / 2
    out = []
    for ln, s in zip(lines, sizes):
        out.append((parse(ln), s, y))
        y += s * 1.0 + gap
    return out


HEAD_LAYOUTS = [(f0, layout_head(lines)) for f0, lines in HEADS]


def draw_head(img_txt, img_glow, layout, t_in, alpha):
    """t_in: Frames seit Einblenden (gross = fertig); alpha 0..1 Gesamtdeckkraft."""
    d = ImageDraw.Draw(img_txt)
    dg = ImageDraw.Draw(img_glow)
    for li, (toks, size, y) in enumerate(layout):
        fnt = font(F_HEAD, size)
        k = ease_out((t_in - 3 * li) / 8.0)
        a = int(255 * alpha * k)
        if a <= 0:
            continue
        dy = (1 - k) * 34
        space = fnt.getlength(" ")
        widths = [fnt.getlength(t) for t, _ in toks]
        x = W / 2 - (sum(widths) + space * (len(toks) - 1)) / 2
        for (t, g), wdt in zip(toks, widths):
            col = GOLD if g else WHITE
            # Ankerhoehe: Anton-Oberlaenge -> obere Kante bei y
            pos = (x, y + dy - size * 0.18)
            d.text((pos[0] + 4, pos[1] + 6), t, font=fnt, fill=(0, 0, 0, int(a * 0.55)))   # Schatten
            d.text(pos, t, font=fnt, fill=(*col, a))
            if g:
                dg.text(pos, t, font=fnt, fill=(*GOLD, int(a * 0.9)))
            x += wdt + space


def head_at(f):
    """aktive Schlagzeile(n) mit Ueberblendung."""
    res = []
    for i, (f0, lay) in enumerate(HEAD_LAYOUTS):
        f1 = HEAD_LAYOUTS[i + 1][0] if i + 1 < len(HEAD_LAYOUTS) else N + 100
        if i == 0:
            t_in = 99            # Frame 0: sofort voll sichtbar (Hook + Loop)
        else:
            t_in = f - f0 - 4    # erst einblenden, wenn die alte Zeile weg ist
        if f0 <= f < f1 + 4:
            alpha = 1 - lin(f, f1, f1 + 4)
            res.append((lay, t_in, alpha))
    return res


# ------------------------------------------------------------------ Untertitel
SUB_Y = 1395          # Mitte der Untertitelzeile (px); unten bleibt Platz fuer die TikTok-UI
SUB_SIZE = 66
SUB_MAXW = 820
SUB_CX = 530


def chunks_for(s):
    """Satz -> Abschnitte (max. 4 Woerter, Schnitt nach Satzzeichen)."""
    ws = s["words"]
    out, cur = [], []
    for w in ws:
        cur.append(w)
        if (len(cur) >= 4 and len(ws) > 5) or w["w"][-1] in ".?!" or (w["w"][-1] == "," and len(cur) > 1):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    # zu kurze Reste (1 Wort ohne Satzzeichen) an den vorigen haengen
    merged = []
    for c in out:
        if merged and len(c) == 1 and c[0]["w"][-1] not in ".?!" and len(merged[-1]) < 5:
            merged[-1] += c
        else:
            merged.append(c)
    return merged


CHUNKS = []
for s in TL["sentences"]:
    for c in chunks_for(s):
        CHUNKS.append(c)
for i, c in enumerate(CHUNKS):
    st = fr(c[0]["start"]) - 3
    nxt = fr(CHUNKS[i + 1][0]["start"]) - 3 if i + 1 < len(CHUNKS) else N
    en = min(nxt, fr(c[-1]["end"]) + 14)
    CHUNKS[i] = {"words": c, "f0": st, "f1": en}


def draw_subs(img, f):
    d = ImageDraw.Draw(img)
    fnt = font(F_SUB, SUB_SIZE)
    for ch in CHUNKS:
        if not (ch["f0"] <= f < ch["f1"]):
            continue
        a_all = smooth(lin(f, ch["f0"], ch["f0"] + 3)) * (1 - lin(f, ch["f1"] - 3, ch["f1"]))
        toks = [w["w"] for w in ch["words"]]
        space = fnt.getlength(" ")
        widths = [fnt.getlength(t) for t in toks]
        total = sum(widths) + space * (len(toks) - 1)
        scale = min(1.0, SUB_MAXW / total)
        fnt2 = font(F_SUB, int(SUB_SIZE * scale)) if scale < 1 else fnt
        if scale < 1:
            space = fnt2.getlength(" ")
            widths = [fnt2.getlength(t) for t in toks]
            total = sum(widths) + space * (len(toks) - 1)
        x = SUB_CX - total / 2
        for w, t, wd in zip(ch["words"], toks, widths):
            ws, we = fr(w["start"]), fr(w["end"])
            spoken = f >= ws - 1
            current = ws - 1 <= f < max(we, ws + 4)
            if current:
                col, a = GOLD, 1.0
            elif spoken:
                col, a = WHITE, 1.0
            else:
                col, a = WHITE, 0.38
            pop = 1.0 + 0.04 * math.exp(-max(0.0, f - ws + 1) / 3.0) if spoken else 1.0
            ft = fnt2 if pop < 1.005 else font(F_SUB, int(fnt2.size * pop))
            ww = ft.getlength(t)
            yy = SUB_Y - ft.size * 0.62
            xx = x + wd / 2 - ww / 2
            A = int(255 * a * a_all)
            d.text((xx, yy), t, font=ft, fill=(*col, A), stroke_width=6, stroke_fill=(0, 0, 0, int(A * 0.85)))
            x += wd + space


# ------------------------------------------------------------------ Hintergrund, Bokeh, Staub
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - 540) / 1.0) ** 2 + ((yy - 900) / 1.15) ** 2)
BG = np.zeros((H, W, 3), np.float32)
base = np.array([4, 5, 8], np.float32) / 255
center = np.array([14, 15, 22], np.float32) / 255
k = np.clip(1 - r / 1250, 0, 1)[..., None] ** 1.6
BG[:] = base + (center - base) * k

rng = random.Random(42)


def disc_sprite(rad, color, rim=0.35):
    s = int(rad * 2 + 6)
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    d = np.sqrt((x - s / 2) ** 2 + (y - s / 2) ** 2) / rad
    body = np.clip((1 - d) * 6, 0, 1) * (0.55 + rim * np.clip((d - 0.7) / 0.3, 0, 1))
    return body[..., None] * (np.array(color, np.float32) / 255)


BOKEH = []
for i in range(24):
    rad = rng.uniform(18, 75)
    col = GOLD if rng.random() < 0.45 else (210, 220, 255)
    BOKEH.append({"spr": disc_sprite(rad, col), "x": rng.uniform(-40, W + 40), "y": rng.uniform(120, H - 200),
                  "ax": rng.uniform(15, 60), "ay": rng.uniform(15, 50), "ph": rng.uniform(0, 6.28),
                  "int": rng.uniform(0.05, 0.13), "tw": rng.uniform(0, 6.28)})
DUST = []
for i in range(170):
    DUST.append({"x": rng.uniform(0, W), "y": rng.uniform(0, H), "m": rng.choice([1, 1, 2]),
                 "wob": rng.uniform(4, 22), "ph": rng.uniform(0, 6.28), "b": rng.uniform(0.15, 0.7),
                 "sz": rng.choice([1, 1, 1, 2, 2, 3]), "gold": rng.random() < 0.3, "tw": rng.uniform(0, 6.28)})
DOT = {s: np.exp(-((np.mgrid[-6:7, -6:7] ** 2).sum(0)) / (2 * (0.6 + 0.55 * s) ** 2)).astype(np.float32) for s in (1, 2, 3)}


def add_sprite(img, spr, cx, cy, gain):
    h, w = spr.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    img[ya:yb, xa:xb] += spr[ya - y0:yb - y0, xa - x0:xb - x0] * gain


def particles(f):
    L = np.zeros((H, W, 3), np.float32)
    p = 2 * math.pi * f / N
    for b in BOKEH:
        cx = b["x"] + b["ax"] * math.sin(p + b["ph"])
        cy = b["y"] + b["ay"] * math.cos(p * 2 + b["ph"])
        g = b["int"] * (0.75 + 0.25 * math.sin(p * 3 + b["tw"]))
        add_sprite(L, b["spr"], cx, cy, g)
    for d in DUST:
        cy = (d["y"] - d["m"] * H * f / N) % H
        cx = d["x"] + d["wob"] * math.sin(p * 2 + d["ph"])
        g = d["b"] * (0.55 + 0.45 * math.sin(p * 7 + d["tw"]))
        col = np.array(GOLD if d["gold"] else (235, 238, 255), np.float32) / 255
        spr = DOT[d["sz"]][..., None] * col
        add_sprite(L, spr, cx, cy, g)
    return L


# ------------------------------------------------------------------ Blitz
FLASH_IMG = None


def flash_amount(f):
    a = 0.0
    if f >= NOW - 3:
        a = max(a, smooth(lin(f, NOW - 3, NOW)) * 0.75 * math.exp(-max(0.0, f - NOW) / 9.0))
    # Loop-Blitz: Gipfel bei N-10, klingt ueber den Schnitt in Frame 0..5 aus
    g = lambda x: smooth(lin(x, FLASH_PEAK - 6, FLASH_PEAK)) * math.exp(-max(0.0, x - FLASH_PEAK) / 4.0)
    a = max(a, 0.85 * g(f), 0.85 * g(f + N))
    return a


def flash_layer():
    rr = np.sqrt((xx - 540) ** 2 + (yy - 860) ** 2)
    core = np.exp(-(rr / 520) ** 2)[..., None]
    wide = np.exp(-(rr / 1300) ** 2)[..., None]
    return core * np.array([1.0, 0.95, 0.85], np.float32) + wide * np.array([1.0, 0.78, 0.38], np.float32) * 0.8


# ------------------------------------------------------------------ Compositing
def screen(a, b):
    return 1 - (1 - a) * (1 - b)


def load_render(rdir, f):
    p = Path(rdir) / f"f{f:05d}.png"
    im = Image.open(p).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def compose(rdir, f):
    global FLASH_IMG
    if FLASH_IMG is None:
        FLASH_IMG = flash_layer()
    img = BG + particles(f)
    rend = load_render(rdir, f)
    if NOW <= f < FLASH_PEAK:   # Outro: langsamer Push-in (Ruecksprung verdeckt der Loop-Blitz)
        z = 1 + 0.09 * smooth(lin(f, NOW, FLASH_PEAK))
        im = Image.fromarray((rend * 255).astype(np.uint8)).resize((int(W * z), int(H * z)), Image.BICUBIC)
        x0, y0 = (im.width - W) // 2, int((im.height - H) * 0.45)
        rend = np.asarray(im.crop((x0, y0, x0 + W, y0 + H)), np.float32) / 255
    img = screen(np.clip(img, 0, 1), rend)
    fa = flash_amount(f)
    if fa > 0.002:
        img = screen(img, np.clip(FLASH_IMG * fa, 0, 1))
    # Texte
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for lay, t_in, alpha in head_at(f):
        draw_head(txt, glow, lay, t_in, alpha)
    hb = txt.getbbox()
    draw_subs(txt, f)
    QA.append({"f": f, "head_bbox": hb, "all_bbox": txt.getbbox(),
               "subs": " ".join(w["w"] for ch in CHUNKS if ch["f0"] <= f < ch["f1"] for w in ch["words"])})
    # dunkler Halo hinter der Schlagzeile (Lesbarkeit ueber hellen Szenen)
    sh = np.asarray(txt.crop((0, 0, W, 700)).getchannel("A").filter(ImageFilter.GaussianBlur(22)), np.float32)[..., None] / 255
    img[:700] *= 1 - np.clip(sh * 1.6, 0, 0.75)
    g = np.asarray(glow.crop((0, 0, W, 700)).filter(ImageFilter.GaussianBlur(18)), np.float32) / 255
    gl = np.zeros((H, W, 3), np.float32)
    gl[:700] = g[..., :3] * g[..., 3:4] * 0.9
    img = screen(img, gl)
    t = np.asarray(txt, np.float32) / 255
    img = img * (1 - t[..., 3:4]) + t[..., :3] * t[..., 3:4]
    # leichtes Filmkorn
    nrng = np.random.default_rng(f)
    img = img + nrng.normal(0, 0.006, (H, W, 1)).astype(np.float32)
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


QA = []


def qa_report(path):
    """Text am Rand abgeschnitten? Leere Frames? Untertitel ohne Stimme?"""
    issues = []
    for q in QA:
        b = q["all_bbox"]
        if b and (b[0] < 24 or b[2] > W - 24 or b[1] < 120 or b[3] > 1560):
            issues.append(f"Frame {q['f']}: Text nahe/ueber Rand {b}")
    Path(path).write_text(json.dumps({"issues": issues, "frames": len(QA)}, indent=1))
    return issues


def main():
    rdir, out = sys.argv[1], sys.argv[2]
    frames = list(range(N))
    if "--frames" in sys.argv:
        frames = [int(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")]
        Path(out).mkdir(parents=True, exist_ok=True)
        for f in frames:
            Image.fromarray(compose(rdir, f)).save(Path(out) / f"c{f:05d}.png")
        return
    audio = sys.argv[sys.argv.index("--audio") + 1] if "--audio" in sys.argv else None
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-"]
    if audio:
        cmd += ["-i", audio, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "17", "-maxrate", "9M", "-bufsize", "18M",
            "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p", "-colorspace", "bt709",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(compose(rdir, f).tobytes())
        if f % 100 == 0:
            print("post", f, flush=True)
    p.stdin.close()
    p.wait()
    print("QA-Probleme:", qa_report(OUT / "qa_text.json")[:10])


if __name__ == "__main__":
    main()
