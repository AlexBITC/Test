"""2D-Ebene fuer das BNPL-Video: Schlagzeile (fett, Schluesselwort kursiv-serif in Gold #C9A54A),
Wortwechsel BUY<->PAY, gesperrte graue Labels an den Blender-Ankern, Zaehler $0 -> $21.3B mit
Quelle, wortgenaue Untertitel (aktuelles Wort weiss, Rest grau) in der TikTok-Safe-Zone.

  python3 -m bnpl.post <renderdir> <out.mp4> [--audio mix.wav] [--frames 0,100]
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
OUT = ROOT / "out" / "bnpl"
W, H = 1080, 1920
GOLD = (201, 165, 74)          # #C9A54A
WHITE = (255, 255, 255)
GREY = (140, 140, 140)
F_BOLD = str(HERE / "fonts" / "Inter-ExtraBold.otf")
F_SERIF = str(HERE / "fonts" / "DMSerifDisplay-Italic.ttf")
F_LABEL = str(HERE / "fonts" / "Inter-SemiBold.otf")
F_SUB = str(HERE / "fonts" / "Inter-SemiBold.otf")
F_NOTE = str(HERE / "fonts" / "Inter-Medium.otf")

TL = json.loads((OUT / "timeline.json").read_text())
AN = json.loads((OUT / "anchors.json").read_text())
EV = AN["events"]
FPS, N = TL["fps"], TL["n_frames"]
SENT = {s["id"]: s for s in TL["sentences"]}
SAFE_R = W - 150               # rechts 150 px frei
SAFE_B = H - 350               # unten 350 px frei
CXP = (60 + SAFE_R) / 2        # horizontale Mitte des sicheren Bereichs

# Texte der Daten-Szene (Quelle: Adobe-Pressemitteilung vom 28.09.2026, Adobe Analytics)
DATA_LABEL = "US ONLINE HOLIDAY BNPL SPENDING (FORECAST)"
DATA_NOTE = ["Forecast, Nov–Dec 2026. Not financial advice.",
             "Source: Adobe Analytics holiday forecast, Sep 2026."]
DATA_VALUE = 21.3


def fr(t):
    return t * FPS


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lin(f, a, b):
    return clamp((f - a) / (b - a)) if b != a else float(f >= b)


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def word_f(sid, word):
    for w in SENT[sid]["words"]:
        if w["w"].lower().strip(".,?!'\":…") == word:
            return fr(w["start"])
    raise KeyError(word)


_fc = {}


def font(path, size):
    k = (path, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]


# ------------------------------------------------------------------ Schlagzeilen
HEAD_SIZE = 92
HEAD_Y = [300, 410]            # Grundlinien-Mitte der zwei Zeilen
S = lambda i: fr(SENT[i]["start"])
SW0, SW1 = EV["swap"]
TAIL0 = EV["scenes"]["tail"]
HEADS = [
    (0, ["BUY NOW.", "PAY *LATER.*"]),
    (S(3) - 6, ["HOLIDAYS", "*ON CREDIT.*"]),
    (S(4) - 6, ["SMALL PAYMENTS.", "BIG *CHAINS.*"]),
    (S(6) - 6, "SWAP"),
    (S(8) - 6, ["DISCIPLINE TODAY.", "*FREEDOM* TOMORROW."]),
    (S(10) - 6, ["WHO WILL", "*PAY* FOR THIS?"]),
    (TAIL0 - 14, ["BUY NOW.", "PAY *LATER.*"]),     # bis zum letzten Frame voll sichtbar (= Frame 0)
]


def tokens(line):
    out, gold = [], False
    for tok in line.split(" "):
        if tok.startswith("*"):
            gold = True
        out.append((tok.replace("*", ""), gold))
        if tok.endswith("*") or tok.endswith("*."):
            gold = False
    return out


def tok_font(gold, size):
    return font(F_SERIF, size * 1.12) if gold else font(F_BOLD, size)


def line_layout(line, size):
    """-> Liste (text, gold, x, w) zentriert im sicheren Bereich; schrumpft bei Ueberbreite"""
    toks = tokens(line)
    while True:
        sp = font(F_BOLD, size).getlength(" ") * 1.1
        ws = [tok_font(g, size).getlength(t) for t, g in toks]
        tot = sum(ws) + sp * (len(toks) - 1)
        if tot <= SAFE_R - 60 - 20 or size < 50:
            break
        size -= 2
    x = CXP - tot / 2
    out = []
    for (t, g), w in zip(toks, ws):
        out.append((t, g, x, w))
        x += w + sp
    return out, size


def draw_tok(d, t, gold, x, y, size, alpha):
    if alpha < 0.004:          # PIL ueberschreibt Alpha: unsichtbare Woerter wuerden Loecher stanzen
        return
    f = tok_font(gold, size)
    col = GOLD if gold else WHITE
    # Grundlinie auf y ausrichten
    asc = f.getmetrics()[0]
    d.text((x, y - asc), t, font=f, fill=(*col, int(255 * alpha)))


def draw_head_lines(d, lines, t_in, alpha):
    size = HEAD_SIZE
    lays = [line_layout(l, size) for l in lines]
    size = min(s for _, s in lays)
    lays = [line_layout(l, size)[0] for l in lines]
    for li, lay in enumerate(lays):
        k = smooth((t_in - 5 * li) / 16.0)          # langsames Einblenden, Zeile 2 etwas spaeter
        if k <= 0:
            continue
        dy = (1 - k) * 14
        for t, g, x, w in lay:
            draw_tok(d, t, g, x, HEAD_Y[li] + dy, size, alpha * k)


def draw_swap(d, f, t_in, alpha):
    """'BUY NOW.' / 'PAY LATER.' -> BUY und PAY tauschen auf Boegen die Plaetze."""
    size = HEAD_SIZE
    A = [line_layout("BUY NOW.", size)[0], line_layout("PAY *LATER.*", size)[0]]
    B = [line_layout("PAY NOW.", size)[0], line_layout("BUY *LATER.*", size)[0]]
    u = smooth(lin(f, SW0, SW1))
    for li in range(2):
        k = smooth((t_in - 5 * li) / 16.0)
        if k <= 0:
            continue
        # feste Woerter (NOW. / LATER.) gleiten auf ihre neue x-Position
        t, g, xa, w = A[li][1]
        xb = B[li][1][2]
        draw_tok(d, t, g, xa + (xb - xa) * u, HEAD_Y[li], size, alpha * k)
    # BUY: Zeile 1 -> Zeile 2 (Bogen nach links), PAY: Zeile 2 -> Zeile 1 (Bogen nach rechts)
    k = min(smooth(t_in / 16.0), smooth((t_in - 5) / 16.0))
    # beide Boegen nach links aussen, unterschiedlich weit -> kein Zusammenstoss mit NOW./LATER.
    for word, (la, ia), (lb, ib), bulge in (("BUY", (0, 0), (1, 0), 265), ("PAY", (1, 0), (0, 0), 10)):
        xa, ya = A[la][ia][2], HEAD_Y[la]
        xb, yb = B[lb][ib][2], HEAD_Y[lb]
        sc = 1 - 0.3 * math.sin(math.pi * u)         # unterwegs kleiner, damit sich nichts beruehrt
        bulge = min(bulge, xa - 70)                  # Bogen bleibt in der Safe-Zone (links >= 60 px)
        x = xa + (xb - xa) * u - bulge * math.sin(math.pi * u)
        y = ya + (yb - ya) * u
        w0 = tok_font(False, size).getlength(word)
        w1 = tok_font(False, size * sc).getlength(word)
        draw_tok(d, word, False, x + (w0 - w1) / 2, y - (1 - sc) * size * 0.3, size * sc, alpha * (k if u == 0 else 1.0))


def draw_heads(d, f):
    for i, (f0, spec) in enumerate(HEADS):
        f1 = HEADS[i + 1][0] if i + 1 < len(HEADS) else N + 100
        if not (f0 <= f < f1 + 8):
            continue
        t_in = 99 if i == 0 else f - f0 - 4            # neue Zeile kurz nach dem Beginn des Ausblendens der alten
        alpha = 1 - smooth(lin(f, f1, f1 + 8))
        if spec == "SWAP":
            draw_swap(d, f, t_in, alpha)
        else:
            draw_head_lines(d, spec, t_in, alpha)


# ------------------------------------------------------------------ Labels (gesperrte Grossbuchstaben)
def spaced(d, text, cx, cy, size, col, alpha, track=0.22):
    f = font(F_LABEL, size)
    ws = [f.getlength(c) for c in text]
    gap = size * track
    tot = sum(ws) + gap * (len(text) - 1)
    x = cx - tot / 2
    asc = f.getmetrics()[0]
    if alpha < 0.004:
        return
    for c, w in zip(text, ws):
        d.text((x, cy - asc * 0.72), c, font=f, fill=(*col, int(255 * alpha)))
        x += w + gap


def draw_labels(d, f):
    for name, L in AN["labels"].items():
        tr = L["track"][f] if f < len(L["track"]) else None
        if not tr:
            continue
        x, y, a = tr
        spaced(d, L["text"], x, y, 20 if L["text"].startswith("PAYMENT") else 24, GREY, a)


# ------------------------------------------------------------------ Daten-Szene
def draw_data(d, f):
    b0, b1 = EV["scenes"]["B"]
    a = smooth(lin(f, b0 + 2, b0 + 16)) * (1 - smooth(lin(f, b1 - 12, b1 - 2)))
    if a <= 0.003:
        return
    c0, c1 = EV["cnt"]
    u = 1 - (1 - lin(f, c0, c1)) ** 2.2
    v = DATA_VALUE * u
    txt = "$0" if v < 0.05 else f"${v:.1f}B"
    fb = font(F_BOLD, 150)
    w = fb.getlength(txt)
    asc = fb.getmetrics()[0]
    d.text((CXP - w / 2, 900 - asc), txt, font=fb, fill=(*WHITE, int(255 * a)))
    spaced(d, DATA_LABEL, CXP, 1045, 22, GREY, a, track=0.18)
    fn = font(F_NOTE, 22)
    for k, line in enumerate(DATA_NOTE):
        lw = fn.getlength(line)
        d.text((CXP - lw / 2, 1300 + 32 * k), line, font=fn, fill=(*GREY, int(255 * a * 0.85)))


# ------------------------------------------------------------------ Untertitel
SUB_SIZE = 50
SUB_Y = 1478                   # Grundlinie; Unterlaengen bleiben ueber 1570 (unten 350 px frei)
SUB_MAXW = SAFE_R - 60 - 40


def chunks_for(s):
    ws = s["words"]
    out, cur = [], []
    for w in ws:
        cur.append(w)
        end = w["w"][-1] in ".?!" or w["w"].endswith("...") or w["w"].endswith(":")
        if end or (len(cur) >= 5 and len(ws) > 6) or (w["w"][-1] == "," and len(cur) > 2):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    merged = []
    for c in out:
        if merged and len(c) == 1 and c[0]["w"][-1] not in ".?!" and len(merged[-1]) < 5:
            merged[-1] += c
        else:
            merged.append(c)
    return merged


CHUNKS = []
for s in TL["sentences"]:
    CHUNKS += chunks_for(s)
for i, c in enumerate(CHUNKS):
    st = fr(c[0]["start"]) - 4
    nxt = fr(CHUNKS[i + 1][0]["start"]) - 4 if i + 1 < len(CHUNKS) else N
    CHUNKS[i] = {"words": c, "f0": st, "f1": min(nxt, fr(c[-1]["end"]) + 16)}


def draw_subs(d, f):
    for ch in CHUNKS:
        if not (ch["f0"] <= f < ch["f1"]):
            continue
        a_all = smooth(lin(f, ch["f0"], ch["f0"] + 5)) * (1 - smooth(lin(f, ch["f1"] - 5, ch["f1"])))
        if a_all < 0.004:
            continue
        toks = [w["w"] for w in ch["words"]]
        size = SUB_SIZE
        while True:
            fn = font(F_SUB, size)
            sp = fn.getlength(" ")
            ws = [fn.getlength(t) for t in toks]
            tot = sum(ws) + sp * (len(toks) - 1)
            if tot <= SUB_MAXW or size <= 36:
                break
            size -= 2
        x = CXP - tot / 2
        asc = fn.getmetrics()[0]
        for w, t, wd in zip(ch["words"], toks, ws):
            ws_, we_ = fr(w["start"]), fr(w["end"])
            cur = ws_ - 1 <= f < max(we_, ws_ + 5)
            col = WHITE if cur else GREY
            d.text((x, SUB_Y - asc), t, font=fn, fill=(*col, int(255 * a_all)))
            x += wd + sp


# ------------------------------------------------------------------ Compositing
QA = []


def compose(rdir, f):
    im = Image.open(Path(rdir) / f"f{f:05d}.png").convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    base = np.asarray(im, np.float32) / 255
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    draw_heads(d, f)
    draw_labels(d, f)
    draw_data(d, f)
    bb_main = txt.getbbox()
    draw_subs(d, f)
    sub_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    QA.append({"f": f, "bbox": txt.getbbox(), "main": bb_main})
    t = np.asarray(txt, np.float32) / 255
    img = base * (1 - t[..., 3:4]) + t[..., :3] * t[..., 3:4]
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def qa_report():
    issues = []
    for q in QA:
        b = q["bbox"]
        if b and (b[0] < 30 or b[2] > SAFE_R or b[1] < 150 or b[3] > SAFE_B):
            issues.append(f"Frame {q['f']}: Text ausserhalb der Safe-Zone {b}")
    (OUT / "qa_text.json").write_text(json.dumps({"issues": issues, "frames": len(QA)}, indent=1))
    return issues


def main():
    rdir, out = sys.argv[1], sys.argv[2]
    if "--frames" in sys.argv:
        Path(out).mkdir(parents=True, exist_ok=True)
        for f in [int(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")]:
            Image.fromarray(compose(rdir, f)).save(Path(out) / f"c{f:05d}.png")
        print("QA:", qa_report())
        return
    audio = sys.argv[sys.argv.index("--audio") + 1] if "--audio" in sys.argv else None
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-i", audio, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "6M", "-bufsize", "12M", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(N):
        p.stdin.write(compose(rdir, f).tobytes())
        if f % 100 == 0:
            print("post", f, flush=True)
    p.stdin.close()
    p.wait()
    print("QA-Probleme:", qa_report()[:10])


if __name__ == "__main__":
    main()
