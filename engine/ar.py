"""Ebene [AR] (Engine 2.4): Einblendungen, die man durch Leas AR-Brille sieht.

Aufruf im Feld 'visual' mit [AR] … [/AR] (ar_text liest den Abschnitt). 3D-Elemente (die Regie setzt sie):
  holo_haende   tuerkise, halbtransparente Hand (Handflaeche, Daumen, vier Finger) mit Glueh-Huelle;
                holo_bewegen fuehrt sie ueber eine Bahn (macht die Bewegung vor)
  pfeil         leuchtender Pfeil (flach, mit Glueh-Rand)
  schritt_kreis Schritt-Nummer im Kreis (Ring + Zahl), dreht sich zur Kamera
  bahn          duenne Bewegungsbahn (Roehre entlang Punkten), zeichnet sich fortlaufend (bahn_zeichnen)
Leichtes Gluehen (heller Kern + transparente Huelle), keine flackernden Werte. Die 2D-Ebene (ganz dezente Scanlines
und tuerkiser Randschimmer) zeichnet engine/overlays.draw_ar fuer alle Frames einer Szene mit [AR] im 'visual'.
"""
import math
import re

from mathutils import Vector

import look as L
from anim import pop, unpop, clamp01

TURQ = "#2EE6D6"
KERN = "#BFFFF8"


def ar_text(visual: str):
    """Text zwischen [AR] und [/AR] (oder None)."""
    m = re.search(r"\[AR\](.*?)\[/AR\]", visual or "", re.S)
    return m.group(1).strip() if m else None


def _mats():
    return (L.mat("ar_kern", KERN, 0.3, emit=TURQ, strength=3.0, alpha=0.62),
            L.mat("ar_huelle", TURQ, 0.3, emit=TURQ, strength=2.0, alpha=0.16),
            L.mat("ar_linie", TURQ, 0.3, emit=TURQ, strength=4.0))


class P:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def holo_haende(coll, name, seite="R", s=1.0):
    """Halbtransparente Holo-Hand (wie Kalles Hand, etwas groesser), Vorderseite -Y, Finger nach -Z."""
    kern, huelle, _ = _mats()
    root = L.empty(name, coll=coll)
    hand = L.empty(f"{name}_hand", root, (0, 0, 0), coll)
    hand.scale = (s, s, s)
    sx = -1 if seite == "R" else 1
    for mat, k in ((kern, 1.0), (huelle, 1.22)):
        L.sphere(f"{name}_palm{k}", 0.1 * k, 10, 7, (0.9, 0.55, 1.0), mat, hand, (0, 0, 0), coll)
        L.sphere(f"{name}_thumb{k}", 0.036 * k, 6, 4, (1, 1, 1.6), mat, hand, (-sx * 0.085, -0.03, 0.01), coll)
        for j in range(4):
            x = -0.05 + 0.033 * j
            L.cyl(f"{name}_f{j}_{k}", 0.019 * k, 0.11 + 0.02 * (j in (1, 2)), 6, mat, hand, (x, -0.005, -0.12), coll)
    return P(root=root, hand=hand)


def holo_bewegen(T, hh, pos_fn, rot_fn, f0, f1, f_in=None, f_out=None):
    """Holo-Hand folgt pos_fn(f) / rot_fn(f) (Welt), blendet mit Pop ein und aus."""
    fi = f_in if f_in is not None else f0
    T.set(hh.root, "location", lambda f: tuple(pos_fn(f)), f0, f1)
    T.set(hh.root, "rotation_euler", lambda f: tuple(rot_fn(f)), f0, f1)
    T.set(hh.root, "scale", lambda f: ((pop(f, fi, 8) * (unpop(f, f_out, 6) if f_out is not None and f > f_out else 1)),) * 3,
          f0, f1)


def pfeil(coll, name, laenge=0.25, breite=0.06):
    """Leuchtender Pfeil in der XZ-Ebene (zeigt nach +X)."""
    kern, huelle, linie = _mats()
    root = L.empty(name, coll=coll)
    h = breite * 1.8
    pts = [(0, -breite / 2), (laenge - h, -breite / 2), (laenge - h, -h / 2), (laenge, 0), (laenge - h, h / 2),
           (laenge - h, breite / 2), (0, breite / 2)]
    L.poly_flat(f"{name}_k", pts, 0.008, linie, root, (0, 0, 0), coll)
    big = [(x * 1.0, z * 1.6) for x, z in pts]
    L.poly_flat(f"{name}_h", big, 0.004, huelle, root, (0, 0.006, 0), coll)
    root.scale = (0, 0, 0)
    return P(root=root)


def schritt_kreis(coll, name, nummer, r=0.07):
    """Schritt-Nummer im Kreis: leuchtender Ring, dunkle Scheibe, helle Zahl. Vorderseite -Y."""
    kern, huelle, linie = _mats()
    root = L.empty(name, coll=coll)
    L.torus(f"{name}_ring", r, r * 0.12, 24, 5, linie, root, (0, 0, 0), coll, axis="Y")
    L.cyl(f"{name}_disc", r * 0.92, 0.006, 24, L.mat("ar_disc", "#0E2A33", 0.4, alpha=0.75), root, (0, 0.003, 0), coll,
          axis="Y")
    L.cyl(f"{name}_glow", r * 1.35, 0.004, 24, huelle, root, (0, 0.006, 0), coll, axis="Y")
    L.text(f"{name}_n", str(nummer), r * 1.25, linie, root, (0, -0.006, -r * 0.42), coll, extrude=0.002, font=L.font())
    root.scale = (0, 0, 0)
    return P(root=root)


def bahn(coll, name, punkte, r=0.006, farbe=TURQ, glow=True):
    """Duenne Bewegungsbahn aus Segmenten (Weltpunkte). farbe '#2EE6D6' tuerkis, z. B. '#9A9CAB' grau."""
    if farbe == TURQ:
        linie = L.mat("ar_linie", TURQ, 0.3, emit=TURQ, strength=4.0)
        huelle = L.mat("ar_huelle", TURQ, 0.3, emit=TURQ, strength=2.0, alpha=0.16)
    else:
        linie = L.mat(f"ar_linie{farbe}", farbe, 0.4)
        huelle = L.mat(f"ar_huelle{farbe}", farbe, 0.4, alpha=0.2)
    root = L.empty(name, coll=coll)
    segs = []
    pts = [Vector(p) for p in punkte]
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        d = b - a
        mid = (a + b) / 2
        piv = L.empty(f"{name}_s{i}", root, tuple(mid), coll)
        piv.rotation_mode = "QUATERNION"
        piv.rotation_quaternion = d.normalized().to_track_quat("Z", "Y")
        L.cyl(f"{name}_c{i}", r, d.length + r, 6, linie, piv, (0, 0, 0), coll)
        if glow:
            L.cyl(f"{name}_g{i}", r * 2.6, d.length + r, 6, huelle, piv, (0, 0, 0), coll)
        segs.append(piv)
    return P(root=root, segs=segs)


def bahn_zeichnen(T, bh, f0, dauer, f_out=None):
    """Bahn zeichnet sich Segment fuer Segment (dauer Frames), blendet ab f_out aus."""
    n = len(bh.segs)
    for i, sg in enumerate(bh.segs):
        a = f0 + dauer * i / n

        def sc(f, a=a):
            v = clamp01((f - a) / max(1.0, dauer / n))
            if f_out is not None and f > f_out:
                v *= 1 - clamp01((f - f_out) / 8)
            return (v, v, v)
        T.set(sg, "scale", sc, f0 - 1, (f_out + 9) if f_out is not None else f0 + dauer + 1)


def einblenden(T, obj, f_in, f_out=None, s=1.0, dur=8):
    end = (f_out + dur) if f_out is not None else f_in + dur + 1
    T.set(obj, "scale", lambda f: ((s * pop(f, f_in, dur) * (unpop(f, f_out, 6) if f_out is not None and f > f_out else 1)),) * 3,
          f_in - 1, end)


def bogen_punkte(mitte, radius, a0, a1, n=16, ebene="XZ", hub=0.0):
    """Punkte eines Bogens (fuer den Schwung aus dem Handgelenk)."""
    out = []
    for k in range(n + 1):
        t = a0 + (a1 - a0) * k / n
        if ebene == "XZ":
            out.append(Vector(mitte) + Vector((radius * math.cos(t), hub * math.sin(math.pi * k / n), radius * math.sin(t))))
        else:
            out.append(Vector(mitte) + Vector((radius * math.cos(t), radius * math.sin(t), hub * math.sin(math.pi * k / n))))
    return out
