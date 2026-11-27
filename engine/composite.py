"""Compositing: 3D-Frame (hochskaliert) + Whip-Pan-Unschaerfe + Vignette + Filmkorn + Overlay,
Encoding mit ffmpeg (libx264 high, yuv420p, crf 20, veryfast, faststart) und AAC 160 kbit/s 48 kHz."""
from __future__ import annotations

import json
import math
import subprocess
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

W, H, FPS = 1080, 1920, 30
GRAIN = 1.1          # sehr leichtes Filmkorn (Standardabweichung in 8-bit-Stufen)
DENOISE = "hqdn3d=2.0:1.5:4:3"   # entfernt Eevee-Sampling-Rauschen vor dem Encoding (Dateigroesse)
_V = {}


def _vignette():
    if "v" not in _V:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        nx, ny = (x - W / 2) / (W / 2), (y - H / 2) / (H / 2)
        r = np.sqrt(nx ** 2 * 1.0 + ny ** 2 * 0.85)
        _V["v"] = (1 - 0.32 * np.clip((r - 0.55) / 0.75, 0, 1) ** 1.6)[..., None].astype(np.float32)
    return _V["v"]


def whip_amount(f, whips):
    """0..1 Staerke der horizontalen Bewegungsunschaerfe an Whip-Pan-Grenzen (8 Frames)."""
    best = 0.0
    for wb, _d in whips:
        k = f - wb
        if -4 <= k < 4:
            best = max(best, [0.25, 0.55, 0.85, 1.0, 1.0, 0.85, 0.55, 0.25][k + 4])
    return best


def hblur(a, radius):
    if radius < 1:
        return a
    k = 2 * radius + 1
    pad = np.pad(a, ((0, 0), (radius + 1, radius), (0, 0)), mode="edge")
    c = np.cumsum(pad, axis=1, dtype=np.float32)
    return (c[:, k:] - c[:, :-k]) / k


def _frame3d(frames_dir, f):
    img = Image.open(Path(frames_dir) / f"{f:05d}.png").convert("RGB")
    sub = Path(frames_dir) / f"{f:05d}_b.png"
    if sub.exists():                                   # Motion Blur: Unterbilder mitteln
        img = Image.blend(img, Image.open(sub).convert("RGB"), 0.5)
    return img


def blend_state(f, blenden):
    """2.4: weiche Ueberblendung an einer Schnittgrenze fb ueber dur Frames (Regie: W.cam.blenden = [(fb, dur)]).
    Rueckgabe (Frame A, Frame B, Anteil B) oder None. Vor der Grenze steht das erste Bild der neuen Einstellung,
    danach das letzte der alten (beide Einstellungen sind nur auf ihrer Seite gerendert)."""
    for fb, dur in blenden:
        h = dur // 2
        if fb - h <= f < fb + dur - h:
            t = (f - (fb - h) + 0.5) / dur
            t = t * t * (3 - 2 * t)
            return (min(f, fb - 1), max(f, fb), t)
    return None


# ------------------------------------------------------------------ 2.5: Spielwelt-Effekte
FACECAM = (60, 716, 384, 1116)
_EX = {}


def _extras(frames_dir):
    """Effekt-Eintraege aus anchors.json (nur vorhanden, wenn eine Folge sie nutzt)."""
    p = Path(frames_dir).parent / "anchors.json"
    key = (str(p), p.stat().st_mtime if p.exists() else 0)
    if key not in _EX:
        d = json.loads(p.read_text()) if p.exists() else {}
        _EX.clear()
        _EX[key] = {k: d.get(k) or [] for k in ("uebergaenge", "facecam", "morph", "wackeln")}
    return _EX[key]


def _voll(img):
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))
    return img


def morph_kacheln(a_img, b_img, t, n_x=12, n_y=21):
    """Kacheln klappen von unten nach oben (diagonal versetzt) um: vorne Bild A, nach dem Umklappen Bild B.
    t 0..1 ueber die Morph-Dauer; jede Kachel klappt in 35 % der Zeit."""
    out = a_img.copy()
    tw, th = W / n_x, H / n_y
    for j in range(n_y):
        for i in range(n_x):
            start = 0.65 * ((n_y - 1 - j) / (n_y - 1) * 0.75 + i / (n_x - 1) * 0.25)
            k = (t - start) / 0.35
            if k <= 0:
                continue
            box = (int(i * tw), int(j * th), int((i + 1) * tw), int((j + 1) * th))
            if k >= 1:
                out.paste(b_img.crop(box), box)
                continue
            src = a_img if k < 0.5 else b_img
            breite = abs(math.cos(math.pi * k))
            bw = max(1, int((box[2] - box[0]) * breite))
            teil = src.crop(box).resize((bw, box[3] - box[1]), Image.BILINEAR)
            hell = 1.0 - 0.45 * (1 - breite)
            teil = Image.eval(teil, lambda v, h=hell: int(v * h))
            mit = src.crop(box).resize((1, 1), Image.BOX).getpixel((0, 0))
            out.paste(tuple(int(v * 0.55) for v in mit[:3]), box)        # Kachel-Rueckseite: abgedunkelte Mittelfarbe
            out.paste(teil, (box[0] + ((box[2] - box[0]) - bw) // 2, box[1]))
    return out


def pixel_blitz(img, k):
    """Pixel- und Scanline-Blitz (k 0..1, Spitze am Schnitt): Verpixeln, Scanlines, kurzer heller Blitz."""
    if k <= 0:
        return img
    blk = int(4 + 44 * k)
    small = img.resize((max(1, W // blk), max(1, H // blk)), Image.BILINEAR)
    img = small.resize((W, H), Image.NEAREST)
    a = np.asarray(img, dtype=np.float32)
    a[::4] *= 1 - 0.45 * k
    a = a * (1 - 0.5 * k ** 3) + np.array([200, 255, 250], np.float32) * 0.5 * k ** 3
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def _rund_maske(w, h, r):
    m = Image.new("L", (w, h), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


def compose_one(tl, f, frames_dir, overlay_dir, out_path=None, scale=None, whips=(), blenden=()):
    ex = _extras(frames_dir)
    bs = blend_state(f, blenden) if blenden else None
    if bs:
        img = Image.blend(_frame3d(frames_dir, bs[0]), _frame3d(frames_dir, bs[1]), bs[2])
    else:
        img = _frame3d(frames_dir, f)
    img = _voll(img)
    for m in ex["morph"]:                                # 2.5: echte Welt -> Spielstadt (Kacheln klappen um)
        zw = Path(frames_dir) / f"{f:05d}_zw.png"
        if f >= m["f0"] and zw.exists():
            t = (f - m["f0"] + 1) / m["dauer"]
            b = _voll(Image.open(zw).convert("RGB"))
            img = b if t >= 1 else morph_kacheln(img, b, t)
    for wf, amp, dur in ex["wackeln"]:                   # 2.5: kleiner Screen-Shake (PLEITE)
        if wf <= f < wf + dur:
            k = 1 - (f - wf) / dur
            dx, dy = int(amp * k * math.sin(f * 2.9)), int(amp * 0.6 * k * math.cos(f * 3.7))
            img = img.transform(img.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BILINEAR, fillcolor=None)
    for fb, _art in ex["uebergaenge"]:                   # 2.5: Pixel-/Scanline-Blitz ins Spiel / aus dem Spiel (0,6 s)
        if fb - 9 <= f < fb + 9:
            img = pixel_blitz(img, 1 - abs(f - fb + 0.5) / 9.5)
    for f0, f1 in ex["facecam"]:                         # 2.5: Facecam-Fenster mit der echten Figur
        fc = Path(frames_dir) / f"{f:05d}_fc.png"
        if f0 <= f < f1 and fc.exists():
            x0, y0, x1, y1 = FACECAM
            win = Image.open(fc).convert("RGB").resize((x1 - x0, y1 - y0), Image.LANCZOS)
            al = min(1.0, (f - f0 + 1) / 6, (f1 - f) / 6)
            mask = _rund_maske(x1 - x0, y1 - y0, 28).point(lambda v: int(v * al))
            img.paste(win, (x0, y0), mask)
    a = np.asarray(img, dtype=np.float32)
    amt = whip_amount(f, whips)
    if amt > 0:
        a = hblur(a, int(90 * amt))
    a = a * _vignette()
    rng = np.random.default_rng(1000 + f)
    g = rng.normal(0, GRAIN, (H // 2, W // 2)).astype(np.float32)
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    a = np.clip(a + g, 0, 255)
    base = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    ov = Path(overlay_dir) / f"{f:05d}.png"
    if ov.exists():
        base.alpha_composite(Image.open(ov))
    out = base.convert("RGB")
    if out_path:
        out.save(out_path)
    return out


_G = {}


def _init(tl, fd, od, whips, blenden=()):
    _G.update(tl=tl, fd=fd, od=od, whips=whips, blenden=blenden)


def _work(f):
    return compose_one(_G["tl"], f, _G["fd"], _G["od"], whips=_G["whips"], blenden=_G.get("blenden", ())).tobytes()


def encode(tl, frames_dir, overlay_dir, audio, out_mp4, scale, procs=4):
    anchors = json.loads((Path(frames_dir).parent / "anchors.json").read_text())
    whips = anchors.get("whips", [])
    blenden = anchors.get("blenden", [])
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", str(audio), "-map", "0:v", "-map", "1:a", "-vf", DENOISE,
           "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "veryfast",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out_mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(procs, initializer=_init, initargs=(tl, str(frames_dir), str(overlay_dir), whips, blenden)) as pool:
        for buf in pool.imap(_work, range(tl["frames"]), chunksize=4):
            p.stdin.write(buf)
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg-Encoding fehlgeschlagen")
