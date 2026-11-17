"""Compositing: 3D-Frame (hochskaliert) + Whip-Pan-Unschaerfe + Vignette + Filmkorn + Overlay,
Encoding mit ffmpeg (libx264 high, yuv420p, crf 20, veryfast, faststart) und AAC 160 kbit/s 48 kHz."""
from __future__ import annotations

import json
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


def compose_one(tl, f, frames_dir, overlay_dir, out_path=None, scale=None, whips=()):
    img = Image.open(Path(frames_dir) / f"{f:05d}.png").convert("RGB")
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))
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


def _init(tl, fd, od, whips):
    _G.update(tl=tl, fd=fd, od=od, whips=whips)


def _work(f):
    return compose_one(_G["tl"], f, _G["fd"], _G["od"], whips=_G["whips"]).tobytes()


def encode(tl, frames_dir, overlay_dir, audio, out_mp4, scale, procs=4):
    anchors = json.loads((Path(frames_dir).parent / "anchors.json").read_text())
    whips = anchors.get("whips", [])
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", str(audio), "-map", "0:v", "-map", "1:a", "-vf", DENOISE,
           "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "veryfast",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out_mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(procs, initializer=_init, initargs=(tl, str(frames_dir), str(overlay_dir), whips)) as pool:
        for buf in pool.imap(_work, range(tl["frames"]), chunksize=4):
            p.stdin.write(buf)
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg-Encoding fehlgeschlagen")
