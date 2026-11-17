"""2D-Compose: setzt eine Episode aus vorgerenderten Assets zusammen – ohne Blender.

  Set-Plate (Hintergrund) -> Studio-Screen -> Kalle-Clip (+ Mund-Viseme) -> Vordergrund -> Byte-Clip
  -> Zahlen-Pop -> Overlays (Hook, Kapitel, Begriff, Untertitel) -> Whip-Pan-Unschärfe, Vignette, Korn

Kamera: virtuelle 2D-Kamera auf der Plate (Overscan 1,5x): Push-in pro Szene, Handheld-Drift,
Punch-ins auf Highlight-Wörtern, Whip-Pans bei Set-Wechsel.

Cache: cache/voices (Stimmen nach Text-Hash), cache/scenes/<hash>.mp4 (fertige Szenen, ohne Ton).
Eine geänderte Zeile rendert nur ihre Szene (und ggf. die Nachbarn bei geändertem Übergang) neu.

Aufruf:  npm run compose -- episodes/<datei>.json [--tts auto|elevenlabs|piper] [--stills 0,120] [--workers 4]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import overlays as OV
from . import composite as CP

ROOT = Path(__file__).resolve().parent.parent
ENGINE = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
CACHE = ROOT / "cache"
W, H, FPS = 1080, 1920, 30
LEAD, TAIL = 0.08, 0.25        # Stille vor/nach jeder Zeile (s)
REACT_PEAK = 6                 # Frame im 'in'-Teil eines Reaktions-Clips mit dem Hauptakzent
XFADE = 4                      # Überblendung beim Clip-Wechsel (Frames)
# Feinjustage der Figurenplätze pro Set: (dx, dz) in Metern und Größenfaktor (Tiefe)
LAYOUT = {"theke": {"kalle": (0.0, 0.0, 1.0), "byte": (-0.05, 0.0, 1.0)},
          "buero": {"kalle": (0.0, 0.0, 1.0), "byte": (0.15, -0.1, 1.0)},
          "studio": {"kalle": (0.22, 0.62, 0.74), "byte": (0.5, 0.1, 0.85)}}
ZOOM = (1.0, 1.12)             # Push-in pro Szene (1 = ganze Plate-Breite, 28 mm)
# leichte Farbanpassung der Figuren an das Set-Licht (RGB-Multiplikator)
TINT = {"theke": (1.0, 0.97, 0.93), "buero": (0.99, 0.98, 0.97), "studio": (0.93, 0.95, 1.04)}
VIS_ORDER = ("zu", "halb", "auf")


def log(*a):
    print("[compose]", *a, flush=True)


def _core(w: str) -> str:
    return re.sub(r"^[^\w]+|[^\w]+$", "", w).lower()


def ease_out(t):
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# ================================================================== Assets
@lru_cache(maxsize=None)
def clip_meta(name):
    d = ASSETS / "clips" / name
    m = json.loads((d / "meta.json").read_text())
    m["visemes"] = {}
    for v in VIS_ORDER:
        bp = d / f"mund_{v}" / "boxes.json"
        if bp.exists():
            m["visemes"][v] = json.loads(bp.read_text())
    return m


@lru_cache(maxsize=1200)
def _img(path):
    im = Image.open(path)
    im.load()
    return im


def clip_frame(name, part, i, viseme=None):
    d = ASSETS / "clips" / name
    im = _img(str(d / f"{part}_{i:04d}.webp"))
    if viseme is None:
        return im
    m = clip_meta(name)
    vm = m["visemes"].get(viseme)
    if vm is None:
        return im
    crop = _img(str(d / f"mund_{viseme}" / f"{part}_{i:04d}.webp"))
    x0, y0 = vm["boxes"][part][i]
    out = im.copy()
    region = out.crop((int(x0), int(y0), int(x0) + crop.size[0], int(y0) + crop.size[1]))
    out.paste(Image.composite(crop, region, _feather(crop.size)), (int(x0), int(y0)))
    return out


@lru_cache(maxsize=8)
def _feather(size, edge=10):
    """Maske mit weichem Rand: Mund-Ausschnitt ohne sichtbare Kante einsetzen."""
    w, h = size
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rectangle((edge, edge, w - 1 - edge, h - 1 - edge), fill=255)
    return m.filter(ImageFilter.GaussianBlur(edge / 2))


PAD_TOP = {"studio": 420}      # Plate oben verlängern (Wandfarbe), damit der Screen unter die Overlays passt


@lru_cache(maxsize=None)
def plate(name):
    d = ASSETS / "sets" / name
    meta = json.loads((d / "meta.json").read_text())
    bg = Image.open(d / "bg.webp").convert("RGB")
    fg = Image.open(d / "fg.webp").convert("RGBA") if (d / "fg.webp").exists() else None
    pad = PAD_TOP.get(name, 0)
    if pad:
        a = np.asarray(bg)
        top = np.repeat(a[:24].mean(axis=0, keepdims=True), pad, axis=0)
        top = np.asarray(Image.fromarray(top.astype(np.uint8)).filter(ImageFilter.GaussianBlur(24)))
        fade = np.linspace(0.82, 1.0, pad)[:, None, None]       # nach oben leicht dunkler
        bg = Image.fromarray(np.concatenate([(top * fade).astype(np.uint8), a], axis=0))
        if fg is not None:
            nfg = Image.new("RGBA", (fg.size[0], fg.size[1] + pad), (0, 0, 0, 0))
            nfg.paste(fg, (0, pad))
            fg = nfg
        meta = json.loads(json.dumps(meta))
        meta["size"] = [bg.size[0], bg.size[1]]
        for who in ("kalle", "byte"):
            meta[who]["anchor"][1] += pad
        if "screen" in meta:
            meta["screen"] = [[x, y + pad] for x, y in meta["screen"]]
    return meta, bg, fg


def assets_version() -> str:
    p = ASSETS / "manifest.json"
    return json.loads(p.read_text())["version"] if p.exists() else "none"


def code_version() -> str:
    h = hashlib.sha256()
    for f in ("compose.py", "overlays.py", "composite.py"):
        h.update((ENGINE / f).read_bytes())
    return h.hexdigest()[:12]


# ================================================================== Timeline
def envelope(wav: Path, n_frames: int, lead_s: float):
    import soundfile as sf
    y, sr = sf.read(str(wav), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    hop = sr // FPS
    pad = np.concatenate([np.zeros(int(lead_s * sr), np.float32), y, np.zeros(sr, np.float32)])
    amp = np.array([float(np.sqrt(np.mean(pad[f * hop: f * hop + hop * 2] ** 2))) for f in range(n_frames)])
    ref = np.percentile(amp[amp > 1e-4], 95) if np.any(amp > 1e-4) else 1
    return np.clip(amp / ref, 0, 1.3).round(3).tolist()


def build_timeline(ep: dict, lines: list) -> dict:
    scenes, f = [], 0
    prev_react = "neutral"
    for i, (sz, l) in enumerate(zip(ep["szenen"], lines)):
        n = int(round((LEAD + l["dur"] + TAIL) * FPS))
        hl = {h.lower() for h in sz.get("highlight", [])}
        words = []
        for w in l["words"]:
            words.append({"w": w["w"], "start": w["start"] + LEAD, "end": w["end"] + LEAD,
                          "f0": f + int(round((w["start"] + LEAD) * FPS)), "f1": f + int(round((w["end"] + LEAD) * FPS)),
                          "hl": _core(w["w"]) in hl or w["w"].strip(".,!?:").lower() in hl})
        beats = {}
        phrases = re.findall(r"Beat bei '([^']+)'", sz.get("visual", "")) + sz.get("highlight", []) + \
            ([ep["begriff"]] if ep.get("begriff") else [])
        for phrase in phrases:
            toks = [_core(t) for t in phrase.split()]
            for k in range(len(words)):
                if [_core(x["w"]) for x in words[k:k + len(toks)]] == toks:
                    beats.setdefault(phrase, words[k]["f0"] - 3)
                    break
        react = sz.get("reaktion", "neutral") or "neutral"
        hlw = [w for w in words if w["hl"]]
        trig = (hlw[0]["f0"] if hlw else f + 10) - REACT_PEAK
        scenes.append({"i": i, "sprecher": sz["sprecher"], "text": sz["text"], "highlight": sz.get("highlight", []),
                       "reaktion": react, "prev_reaktion": prev_react, "react_f": max(f, trig), "set": sz["set"],
                       "kapitel": sz.get("kapitel"), "visual": sz.get("visual", ""), "f0": f, "f1": f + n, "n": n,
                       "audio_start": f / FPS + LEAD, "wav": l["wav"], "dur": l["dur"], "words": words,
                       "beats": beats, "amp": envelope(ROOT / l["wav"], n, LEAD)})
        prev_react = react
        f += n
    whips = [[s["f0"], 1 if k % 2 else -1] for k, s in enumerate(scenes) if k and scenes[k - 1]["set"] != s["set"]]
    return {"slug": ep["slug"], "titel": ep["titel"], "hook": ep.get("hook", ""), "begriff": ep.get("begriff", ""),
            "kapitel": ep.get("kapitel", []), "fps": FPS, "width": W, "height": H, "frames": f, "scenes": scenes,
            "whips": whips}


def scene_at(tl, f):
    for s in tl["scenes"]:
        if s["f0"] <= f < s["f1"]:
            return s
    return tl["scenes"][-1] if f >= tl["frames"] else tl["scenes"][0]


# ================================================================== Kamera
class Noise:
    def __init__(self, seed, octaves=3, base=0.25):
        r = np.random.default_rng(seed)
        self.p = [(base * 1.9 ** k * r.uniform(0.8, 1.25), r.uniform(0, 2 * math.pi), 0.55 ** k) for k in range(octaves)]
        self.norm = sum(a for _, _, a in self.p)

    def __call__(self, t):
        return sum(a * math.sin(2 * math.pi * fr * t + ph) for fr, ph, a in self.p) / self.norm


DRIFT = (Noise(101), Noise(202), Noise(303))


def char_pos(meta, who, set_name):
    """Plate-Pixel des Ankers und Pixel/Meter (mit LAYOUT-Feinjustage)."""
    a = meta[who]["anchor"]
    ppm = meta[who]["ppm"]
    dx, dz, k = LAYOUT.get(set_name, {}).get(who, (0, 0, 1.0))
    return a[0] + dx * ppm, a[1] - dz * ppm, ppm * k


def camera(tl, s, f):
    """(x0, y0, s): Plate-Ausschnitt oben links und Maßstab Ausgabe-px pro Plate-px."""
    meta, bg, _ = plate(s["set"])
    pw, ph = meta["size"]
    base = W / pw                       # Zoom 1 = ganze Plate-Breite
    t = ease_out((f - s["f0"]) / max(1, s["n"]))
    z = ZOOM[0] + (ZOOM[1] - ZOOM[0]) * t      # Push-in pro Szene
    for w in s["words"]:                # Punch-in 4 % auf Highlights
        if w["hl"]:
            k = f - (w["f0"] - 1)
            if 0 <= k < 12:
                z *= 1 + 0.04 * (ease_out(k / 3) if k < 3 else 1 - ease_in_out((k - 3) / 9))
    sc = base * z
    kx, ky, kppm = char_pos(meta, "kalle", s["set"])
    bx, by, _ = char_pos(meta, "byte", s["set"])
    head_y = ky - 2.05 * kppm
    fx, fy = 0.55 * kx + 0.45 * bx, 0.6 * head_y + 0.4 * by
    tt = f / FPS
    fx += 9 * DRIFT[0](tt) / sc * 0.6
    fy += 6 * DRIFT[1](tt) / sc * 0.6
    x0, y0 = fx - W * 0.5 / sc, fy - H * 0.42 / sc
    if "screen" in meta:                # Studio: Screen-Oberkante unter Banner + Kapitel-Leiste (Ausgabe-y 405)
        top = min(p[1] for p in meta["screen"]) - 18
        y0 = top - 400 / sc
        x0 = sum(p[0] for p in meta["screen"]) / 4 - W * 0.5 / sc + 9 * DRIFT[0](tt) / sc * 0.6
    # Whip-Pan: Ausschnitt ruckt seitlich (4 Frames raus, 4 rein); die Unschärfe macht den Rest
    for wb, d in tl["whips"]:
        k = f - wb
        if -4 <= k < 0:
            x0 += d * 0.12 * W / sc * ease_out((k + 5) / 4) ** 2
        elif 0 <= k < 4:
            x0 -= d * 0.12 * W / sc * (1 - ease_out((k + 1) / 4))
    x0 = min(max(0, x0), pw - W / sc)
    y0 = min(max(0, y0), ph - H / sc)
    roll = 0.15 * DRIFT[2](tt)
    return x0, y0, sc, roll


def affine_layer(img, k, src_anchor, dst_xy, tint=None):
    """Skaliert img um k und legt src_anchor auf dst_xy (Subpixel). -> (Bild, (x, y)) für alpha_composite."""
    w, h = img.size
    ox = dst_xy[0] - src_anchor[0] * k
    oy = dst_xy[1] - src_anchor[1] * k
    ix, iy = math.floor(ox), math.floor(oy)
    fx, fy = ox - ix, oy - iy
    ow, oh = int(math.ceil(w * k + 2)), int(math.ceil(h * k + 2))
    out = img.transform((ow, oh), Image.AFFINE, (1 / k, 0, -fx / k, 0, 1 / k, -fy / k), resample=Image.BILINEAR)
    if tint:
        r, g, b, a = out.split()
        r = r.point(lambda v: min(255, int(v * tint[0])))
        g = g.point(lambda v: min(255, int(v * tint[1])))
        b = b.point(lambda v: min(255, int(v * tint[2])))
        out = Image.merge("RGBA", (r, g, b, a))
    return out, (ix, iy)


def paste(canvas, layer, xy):
    """alpha_composite mit Beschnitt an den Rändern (auch negative Positionen)."""
    x, y = xy
    lw, lh = layer.size
    cx0, cy0 = max(0, x), max(0, y)
    cx1, cy1 = min(canvas.size[0], x + lw), min(canvas.size[1], y + lh)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    canvas.alpha_composite(layer, (cx0, cy0), (cx0 - x, cy0 - y, cx1 - x, cy1 - y))


# ================================================================== Figuren
@lru_cache(maxsize=None)
def clip_name(who, kind):
    """Fehlt ein Clip in der Bibliothek, nimm neutral (mit Warnung) – compose läuft auch mit Teil-Bibliothek."""
    name = f"{who}_{kind}"
    if (ASSETS / "clips" / name / "meta.json").exists():
        return name
    log(f"WARNUNG: Clip {name} fehlt – nehme {who}_neutral")
    return f"{who}_neutral"


def kalle_state(tl, s, f):
    """-> (clip, part, index, nächster Zustand für Überblendung oder None)."""
    def frame_of(kind, start, carry):
        name = clip_name("kalle", kind)
        m = clip_meta(name)
        t = f - start
        if not carry and t < m["n_in"]:
            return name, "in", max(0, t)
        return name, "loop", (t - (0 if carry else m["n_in"])) % m["n_loop"]
    prev, cur, rf = s["prev_reaktion"], s["reaktion"], s["react_f"]
    if cur == prev or f < rf:
        return frame_of(prev, s["f0"] - 10 ** 4 if f < rf else s["f0"], True), None
    new = frame_of(cur, rf, cur == "neutral")
    if f - rf < XFADE:
        return new, (frame_of(prev, s["f0"], True), (f - rf + 1) / (XFADE + 1))
    return new, None


def kalle_viseme(s, f):
    if s["sprecher"] != "kalle":
        return None
    sp = [w for w in s["words"] if re.search(r"\w", w["w"])]
    if not sp or not (sp[0]["f0"] - 2 <= f <= sp[-1]["f1"] + 2):
        return None
    i = f - s["f0"]
    a = s["amp"]
    v = sum(a[j] for j in range(max(0, i - 1), min(len(a), i + 2))) / 3
    return "zu" if v < 0.12 else "halb" if v < 0.45 else "auf"


def kalle_image(tl, s, f):
    (name, part, i), blend = kalle_state(tl, s, f)
    vis = kalle_viseme(s, f)
    im = clip_frame(name, part, i, vis)
    if blend:
        (n2, p2, i2), a = blend
        old = clip_frame(n2, p2, i2, vis)
        im = Image.blend(old, im, a)
    return im, clip_meta(name)


def byte_image(tl, s, f):
    talking = False
    if s["sprecher"] == "byte":
        i = f - s["f0"]
        talking = 0 <= i < len(s["amp"]) and s["amp"][i] > 0.06
    name = "byte_sprechen" if talking else "byte_schweben"
    m = clip_meta(name)
    im = clip_frame(name, "loop", f % m["n_loop"])
    pulse = 1.0
    if s["sprecher"] == "byte":
        for w in s["words"]:
            if w["hl"] and 0 <= f - (w["f0"] - 2) < 12:
                k = f - (w["f0"] - 2)
                pulse = max(pulse, 1 + 0.1 * math.sin(math.pi * k / 12))
    return im, m, pulse


def shadow(canvas, cx, cy, rx, ry, alpha=0.35):
    lay = Image.new("L", (int(rx * 2 + 40), int(ry * 2 + 40)), 0)
    ImageDraw.Draw(lay).ellipse((20, 20, 20 + 2 * rx, 20 + 2 * ry), fill=int(255 * alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(10))
    sh = Image.new("RGBA", lay.size, (10, 8, 20, 0))
    sh.putalpha(lay)
    paste(canvas, sh, (int(cx - rx - 20), int(cy - ry - 20)))


# ================================================================== Screen & Zahlen
def _perspective_coeffs(dst, src):
    """Koeffizienten für Image.PERSPECTIVE: Ausgabe-Punkt (dst) -> Quell-Punkt (src)."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def generic_screen(tl, s, f):
    """Screen für Szenen ohne eigenes Layout: Highlight-Wörter erscheinen groß beim Sprechen."""
    img = OV._screen_bg(f)
    hl = [w for w in s["words"] if w["hl"]]
    y = 250
    for w in hl[:3]:
        a = ease_out((f - (w["f0"] - 4)) / 7)
        if a <= 0:
            continue
        txt = w["w"].strip(".,!?:;")
        col = OV.GOLD if any(ch.isdigit() for ch in txt) else OV.TURQ
        OV._t(img, (OV.SW / 2, y - 30 * (1 - a)), txt, 150 if len(txt) < 10 else 100, col, a, anchor="mm")
        y += 170
    return img


def draw_screen(canvas, tl, s, f, cam):
    meta, _, _ = plate(s["set"])
    if "screen" not in meta:
        return
    tex = OV.screen_frame(tl, f)
    if tex is None or not _known_screen(s):
        tex = generic_screen(tl, s, f)
    x0, y0, sc, _ = cam
    pts = [((x - x0) * sc, (y - y0) * sc) for x, y in meta["screen"]]
    bx0, by0 = int(min(p[0] for p in pts)) - 1, int(min(p[1] for p in pts)) - 1
    bx1, by1 = int(max(p[0] for p in pts)) + 2, int(max(p[1] for p in pts)) + 2
    if bx1 < 0 or by1 < 0 or bx0 > W or by0 > H:
        return
    loc = [(x - bx0, y - by0) for x, y in pts]
    tw, th = tex.size
    co = _perspective_coeffs(loc, [(0, 0), (tw, 0), (tw, th), (0, th)])
    layer = tex.convert("RGBA").transform((bx1 - bx0, by1 - by0), Image.PERSPECTIVE, co, resample=Image.BILINEAR)
    mask = Image.new("L", layer.size, 0)
    ImageDraw.Draw(mask).polygon(loc, fill=255)
    layer.putalpha(mask)
    paste(canvas, layer, (bx0, by0))


def _known_screen(s):
    b = s["beats"]
    return ("18" in b and "15,50" in b) or ("2,50" in b and "60" in b) or "schreibt" in b or "1.800" in b


def _num_value(txt):
    t = txt.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def draw_numbers(img, tl, s, f, byte_xy):
    """Zahlen-Pop (außerhalb des Studios, dort zeigt der Screen die Zahlen): goldene Zahl über Byte, zählt hoch."""
    if s["set"] == "studio":
        return
    for w in s["words"]:
        txt = w["w"].strip(".,!?:;")
        if not (w["hl"] and any(ch.isdigit() for ch in txt)):
            continue
        k = f - (w["f0"] - 3)
        if not (0 <= k < 46):
            continue
        a = min(1.0, k / 3) * (1 - max(0.0, (k - 38) / 8))
        val = _num_value(txt)
        if val is not None and val >= 10 and "," not in txt:
            shown = OV.fmt_num(round(val * ease_out(k / 12)))
        else:
            shown = txt
        unit = " €" if re.search(r"\b" + re.escape(txt) + r"\s*(Euro|€)", s["text"]) else ""
        x = max(OV.X0 + 160, min(OV.X1 - 160, byte_xy[0]))
        y = max(OV.TOP + 140, min(1120, byte_xy[1] - 190))
        sc = 0.6 + 0.4 * OV.ease_out_back(min(1.0, k / 7), 2.6)
        OV.text_center(img, (x, y), shown + unit, 130, OV.GOLD, a, stroke=10, stroke_fill=OV.NAVY, scale=sc)


# ================================================================== Frame
def render_frame(tl, f):
    s = scene_at(tl, f)
    meta, bg, fg = plate(s["set"])
    cam = camera(tl, s, f)
    x0, y0, sc, roll = cam
    aff = (1 / sc, 0, x0, 0, 1 / sc, y0)
    canvas = bg.transform((W, H), Image.AFFINE, aff, resample=Image.BILINEAR).convert("RGBA")
    draw_screen(canvas, tl, s, f, cam)
    tint = TINT.get(s["set"])
    # Kalle
    kx, ky, kppm = char_pos(meta, "kalle", s["set"])
    kim, km = kalle_image(tl, s, f)
    k = kppm / km["ppm"] * sc
    kdst = ((kx - x0) * sc, (ky - y0) * sc)
    shadow(canvas, kdst[0], kdst[1] - 0.02 * kppm * sc, 0.42 * kppm * sc, 0.09 * kppm * sc)
    layer, xy = affine_layer(kim, k, km["anchor"][:2], kdst, tint)
    paste(canvas, layer, xy)
    # Vordergrund (Theke, Schreibtisch)
    if fg is not None:
        paste(canvas, fg.transform((W, H), Image.AFFINE, aff, resample=Image.BILINEAR), (0, 0))
    # Byte
    bx, by, bppm = char_pos(meta, "byte", s["set"])
    bim, bm, pulse = byte_image(tl, s, f)
    bdst = ((bx - x0) * sc, (by - y0) * sc)
    layer, xy = affine_layer(bim, bppm / bm["ppm"] * sc * pulse, bm["anchor"][:2], bdst)
    paste(canvas, layer, xy)
    if abs(roll) > 0.01:
        canvas = canvas.rotate(roll, resample=Image.BILINEAR, center=(W / 2, H / 2), fillcolor=(27, 24, 48, 255))
    # Whip-Unschärfe, Vignette, Korn
    a = np.asarray(canvas.convert("RGB"), dtype=np.float32)
    amt = CP.whip_amount(f, tl["whips"])
    if amt > 0:
        a = CP.hblur(a, int(90 * amt))
    a = a * CP._vignette()
    g = np.random.default_rng(1000 + f).normal(0, CP.GRAIN, (H // 2, W // 2)).astype(np.float32)
    a = np.clip(a + np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None], 0, 255)
    base = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    ov = OV.overlay_frame(tl, f, None)
    draw_numbers(ov, tl, s, f, bdst)
    base.alpha_composite(ov)
    return base.convert("RGB")


# ================================================================== Szenen-Cache
def scene_key(tl, s):
    i = s["i"]
    sc = tl["scenes"]
    rel = lambda v: v - s["f0"]  # noqa: E731
    wav_h = hashlib.sha256((ROOT / s["wav"]).read_bytes()).hexdigest()[:16]
    data = {"code": code_version(), "assets": assets_version(), "i": i, "set": s["set"], "sprecher": s["sprecher"],
            "text": s["text"], "n": s["n"], "reaktion": s["reaktion"], "prev": s["prev_reaktion"],
            "react_f": rel(s["react_f"]), "kapitel": s["kapitel"], "highlight": s["highlight"], "wav": wav_h,
            "words": [[w["w"], rel(w["f0"]), rel(w["f1"]), w["hl"]] for w in s["words"]],
            "beats": {k: rel(v) for k, v in s["beats"].items()},
            "nachbarn": [sc[i - 1]["set"] if i else None, sc[i + 1]["set"] if i + 1 < len(sc) else None,
                         sc[i + 1]["kapitel"] if i + 1 < len(sc) else None, sc[i - 1]["kapitel"] if i else None],
            "episode": [tl["hook"] if i == 0 else "", tl["begriff"], tl["kapitel"],
                        [(x["kapitel"], x["reaktion"]) for x in sc]],
            "phase": [s["f0"] % 75]}       # Loop-Phase von Byte hängt am absoluten Frame
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]


_G = {}


def _init(tl):
    _G["tl"] = tl


def _work(f):
    return render_frame(_G["tl"], f).tobytes()


def encode_scene(tl, s, out: Path, workers: int):
    tmp = out.with_suffix(".part.mp4")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "19",
           "-preset", "veryfast", "-g", "60", "-movflags", "+faststart", str(tmp)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = range(s["f0"], s["f1"])
    if workers > 1:
        with Pool(workers, initializer=_init, initargs=(tl,)) as pool:
            for buf in pool.imap(_work, frames, chunksize=4):
                p.stdin.write(buf)
    else:
        for f in frames:
            p.stdin.write(render_frame(tl, f).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg-Encoding fehlgeschlagen")
    os.replace(tmp, out)


# ================================================================== Ton
def cues(tl):
    c = []
    for wb, _ in tl["whips"]:
        c.append([wb - 5, "whoosh", 0.9])
    for s in tl["scenes"]:
        for w in s["words"]:
            if w["hl"]:
                c.append([w["f0"] - 2, "pop", 0.8])
        if s["reaktion"] != s["prev_reaktion"]:
            kind = {"staunen": "ding", "jubel": "ding", "schock": "buzz", "zweifel": "buzz"}.get(s["reaktion"])
            if kind:
                c.append([s["react_f"] + REACT_PEAK, kind, 0.6 if kind == "buzz" else 0.8])
    return c


def build_audio(tl, work: Path) -> Path:
    from . import sfx
    return sfx.build_mix(tl, work, cue_list=cues(tl))


# ================================================================== Haupt
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--tts", default=os.environ.get("TTS", "auto"), choices=["auto", "elevenlabs", "piper"])
    ap.add_argument("--workers", type=int, default=int(os.environ.get("COMPOSE_WORKERS", os.cpu_count() or 4)))
    ap.add_argument("--stills", default="", help="nur diese Frames als PNG nach out/work/<slug>/ (Kontrolle)")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    if not (ASSETS / "manifest.json").exists():
        sys.exit("Assets fehlen: zuerst  npm run assets  (rendert Clips und Sets einmalig in Blender)")

    from . import voice
    ep_path = Path(args.episode) if os.path.isabs(args.episode) else ROOT / args.episode
    ep = json.loads(ep_path.read_text())
    work = ROOT / "out" / "work" / ep["slug"]
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    lines = voice.lines(ep, args.tts)
    tl = build_timeline(ep, lines)
    (work / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False))
    log(f"Timeline: {tl['frames']} Frames = {tl['frames'] / FPS:.2f} s, {len(tl['scenes'])} Szenen")
    if args.stills:
        for f in [int(x) for x in args.stills.split(",")]:
            p = work / f"still_{f:05d}.png"
            render_frame(tl, f).save(p)
            log("Still:", p)
        return
    sdir = CACHE / "scenes"
    sdir.mkdir(parents=True, exist_ok=True)
    parts = []
    for s in tl["scenes"]:
        key = scene_key(tl, s)
        out = sdir / f"{key}.mp4"
        if out.exists():
            log(f"Szene {s['i'] + 1}: Cache ({key})")
        else:
            ts = time.time()
            encode_scene(tl, s, out, args.workers)
            log(f"Szene {s['i'] + 1}: {s['n']} Frames gerendert in {time.time() - ts:.1f}s ({key})")
        parts.append(out)
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    mix = build_audio(tl, work)
    out_mp4 = Path(args.out) if args.out else ROOT / "out" / f"{ep_path.stem}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(mix),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", str(out_mp4)], check=True)
    log(f"FERTIG: {out_mp4} ({out_mp4.stat().st_size / 1e6:.1f} MB) in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
