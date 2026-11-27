"""Gedankenblase ueber Kunden: brezel (will kaufen), herz (zufrieden), wolke (unzufrieden, geht weg), schirm (bleibt wegen
Regen weg). Zeigt immer zur Iso-Kamera."""
import math

import look as L
import spielwelt as SW
import _zustand as Z

SYMBOLE = ["brezel", "herz", "wolke", "schirm"]
INFO = {"name": "gedankenblase", "groesse": [0.6, 0.1, 0.6], "anker": "mitte_unten", "zustaende": SYMBOLE,
        "beschreibung": "Blase mit Symbol, symbol als Parameter"}


def bauen(coll, name, symbol="brezel", s=1.0, **kw):
    root = L.empty(name, coll=coll)
    face = L.empty(f"{name}_face", root, (0, 0, 0), coll)
    Z.zur_kamera(face)
    face.scale = (s, s, s)
    w = SW.m("blase", "weiss", 0.5)
    L.cyl(f"{name}_b", 0.28, 0.06, 20, w, face, (0, 0, 0.42), coll, axis="Y")
    L.cyl(f"{name}_d1", 0.07, 0.05, 10, w, face, (-0.12, 0, 0.12), coll, axis="Y")
    L.cyl(f"{name}_d2", 0.04, 0.05, 10, w, face, (-0.18, 0, 0.02), coll, axis="Y")
    if symbol == "brezel":
        m = SW.m("brezel_b", "#9A5420", 0.5)
        L.torus(f"{name}_sb", 0.12, 0.03, 14, 5, m, face, (0, -0.04, 0.39), coll, axis="Y").scale = (1.2, 1, 0.75)
        for sx in (-1, 1):
            L.torus(f"{name}_so{sx}", 0.06, 0.025, 10, 5, m, face, (sx * 0.06, -0.04, 0.46), coll, axis="Y")
    elif symbol == "herz":
        pts = [(0.012 * 16 * math.sin(t) ** 3, 0.012 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)))
               for t in [2 * math.pi * k / 30 for k in range(30)]]
        L.poly_flat(f"{name}_h", pts, 0.03, SW.m("herz", "#E2483F", 0.5), face, (0, -0.04, 0.42), coll)
    elif symbol == "wolke":
        for j, (x, z, r) in enumerate([(-0.08, 0.38, 0.08), (0.03, 0.43, 0.1), (0.12, 0.38, 0.07)]):
            L.cyl(f"{name}_w{j}", r, 0.04, 12, SW.m("wolke_g", "#8A8EA6", 0.6), face, (x, -0.04, z), coll, axis="Y")
    elif symbol == "schirm":
        L.poly_flat(f"{name}_s", [(-0.14, 0), (0.14, 0), (0, 0.12)], 0.03, SW.m("schirm", "#3D7BD9", 0.5), face, (0, -0.04, 0.38), coll)
        L.box(f"{name}_ss", (0.02, 0.03, 0.14), SW.m("dunkel", "dunkel", 0.5), face, (0, -0.04, 0.32), coll)
    root.scale = (0, 0, 0)
    return SW.P(root=root, face=face, symbol=symbol)


def zeigen(T, gb, pos_fn, f_an, f_aus, f0, f1):
    from anim import pop, unpop
    T.set(gb.root, "location", lambda f: tuple(pos_fn(f)), f0, f1)
    T.set(gb.root, "scale", lambda f: ((pop(f, f_an, 6) * (unpop(f, f_aus, 5) if f > f_aus else 1)) if f_an <= f < f_aus + 6 else 0,) * 3,
          f0, f1)
