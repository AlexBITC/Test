"""Bildschirm-Ebenen fuer 'Kalles Ausgaben-Dashboard' (folge-07-dashboard), 1280x720 pro Frame.

Wird von engine/overlays.screen_frame geladen. Theke: Laptop-Display (per UV), Studio: grosser Screen.
Aufbaustufen (siehe assets/props/screen_dashboard.py):
  Szene 3 upload_ablage | 4 Zaehler 1.200 + Ring | 5 leere Karte GELDFRESSER | 6 Zeile 1 | 8 Zeilen 2+3 |
  9 Kacheln, komplett | 10 rote Kachel pulsiert | 11 Knoepfe -> Haekchen | 12 Ersparnis zaehlt bis 1.656 € | 13 fertig.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "props"))
import screen_dashboard as D  # noqa: E402

W, H = D.W, D.H


def _wf(s, core, default=None):
    for w in s["words"]:
        if w["w"].strip(".,!?:…").lower() == core.lower():
            return w["f0"]
    return default if default is not None else s["f0"] + 6


def _glow(img, a):
    if a <= 0:
        return img
    ov = Image.new("RGB", (W, H), (190, 255, 250))
    return Image.blend(img.convert("RGB"), ov, min(1.0, a)).convert("RGBA")


def _idle():
    img = Image.new("RGBA", (W, H), D.BG + (255,))
    d = ImageDraw.Draw(img)
    D.byte_icon(d, W / 2, H / 2 + 10, 90)
    return img


def zustand(tl, i, f):
    """Dashboard-Zustand fuer Szene i (0-basiert) im Frame f."""
    sc = tl["scenes"]
    s = sc[i]
    eo = D.eo
    if i == 3:
        hit = _wf(s, "buchungen")
        z = 1200 * eo((f - s["f0"] - 2) / max(1, hit - s["f0"] - 2))
        return {"zaehler": z, "ring": D.c01((f - _wf(s, "in") + 4) / 28)}
    if i == 4:
        return {"zaehler": 1200, "ring": 1, "karte": D.c01((f - s["f0"] - 2) / 8)}
    if i in (5, 6):
        f_r1 = _wf(sc[5], "49") + 4
        return {"zaehler": 1200, "ring": 1, "karte": 1, "zeilen": [D.c01((f - f_r1) / 8), 0, 0]}
    if i == 7:
        r2, r3 = _wf(s, "29") + 2, _wf(s, "60") + 2
        return {"zaehler": 1200, "ring": 1, "karte": 1, "zeilen": [1, D.c01((f - r2) / 8), D.c01((f - r3) / 8)]}
    if i == 8:
        k = _wf(s, "dashboard") - 6
        if f < k:
            return {"zaehler": 1200, "ring": 1, "karte": 1, "zeilen": [1, 1, 1]}
        return {"kacheln": D.c01((f - k) / 8)}
    if i == 9:
        return {"kacheln": 1, "rot_puls": 0.5 + 0.5 * math.sin((f - s["f0"]) * 0.35)}
    if i == 10:
        t = haken_frames(tl)
        return {"kacheln": 1, "haken": [D.c01((f - x) / 8) for x in t]}
    if i == 11:
        f_a = s["f0"] + 8
        f_b = _wf(s, "euro")
        v = 1656 * eo((f - f_a) / max(1, f_b - f_a))
        return {"ersparnis": v, "rechnung": D.c01((f - s["f0"] - 2) / 8),
                "ersparnis_peak": math.sin(math.pi * D.c01((f - f_b) / 8)) if f >= f_b else 0.0}
    if i == 12:
        return {"kacheln": 1, "haken": [1, 1, 1]}
    return None


def haken_frames(tl):
    """Frames, an denen die drei Knoepfe zu Haekchen werden (Szene 11, nach dem Klick)."""
    s = tl["scenes"][10]
    klick = _wf(s, "klick")
    return [klick + 8, klick + 22, klick + 36]


def frame(tl, s, f):
    i = s["i"]
    N = tl["frames"]
    if s["set"] not in ("theke", "studio"):
        return None
    if i in (0, 1):
        img = _idle()
    elif i == 2:
        t0 = _wf(s, "zieh") + 16
        img = D.upload_ablage(D.c01((f - t0) / 30))
    else:
        z = zustand(tl, i, f)
        img = D.render(z) if z is not None else _idle()
    g = max(1 - f / 10, (f - (N - 12)) / 11 if f >= N - 12 else 0.0)
    return _glow(img, 0.85 * g)
