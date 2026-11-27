"""Mini-Byte: schwebendes Helfer-Symbol (tuerkise Kugel mit Display-Augen) mit Zeigepfeil. Zustaende: schweben, zeigen."""
import math

from mathutils import Vector

import look as L
import spielwelt as SW

INFO = {"name": "mini_byte", "groesse": [0.6, 0.6, 0.6], "anker": "mitte", "zustaende": ["schweben", "zeigen"],
        "beschreibung": "Helfer ueber der Szene, zeigt mit Pfeil auf Wichtiges"}


def bauen(coll, name, s=1.0, **kw):
    root = L.empty(name, coll=coll)
    body = L.empty(f"{name}_body", root, (0, 0, 0), coll)
    body.scale = (s, s, s)
    m_t = SW.m("tuerkis", "tuerkis", 0.3, emit="#2EE6D6", strength=2.5)
    L.ico(f"{name}_kugel", 0.28, 2, (1, 1, 1), m_t, body, (0, 0, 0), coll)
    L.cyl(f"{name}_disp", 0.2, 0.05, 20, SW.m("byte_disp", "#141228", 0.4), body, (0, -0.25, 0), coll, axis="Y")
    for sx in (-1, 1):
        L.sphere(f"{name}_auge{sx}", 0.05, 8, 5, (1, 0.4, 1.3), m_t, body, (sx * 0.07, -0.29, 0.02), coll)
    L.cyl(f"{name}_ant", 0.02, 0.2, 6, SW.m("metall", "#8A8EA6", 0.4), body, (0, 0, 0.36), coll)
    L.ico(f"{name}_antk", 0.05, 1, (1, 1, 1), SW.m("gold_leucht", "gold", 0.3, emit="#FFE14D", strength=3.0), body, (0, 0, 0.48), coll)
    pfeil = L.empty(f"{name}_pfeil", root, (0, 0, -0.5), coll)
    L.cyl(f"{name}_ps", 0.12, 0.35, 4, m_t, pfeil, (0, 0, -0.1), coll, r2=0.0).rotation_euler = (math.pi, 0, 0.785)
    pfeil.scale = (0, 0, 0)
    return SW.P(root=root, body=body, pfeil=pfeil)


def schweben(T, b, pos_fn, f0, f1, zeigen=None):
    """pos_fn(f) -> Weltposition; zeigen: (f_an, f_aus) blendet den Pfeil nach unten ein."""
    T.set(b.root, "location", lambda f: tuple(Vector(pos_fn(f)) + Vector((0, 0, 0.12 * math.sin(f * 0.12)))), f0, f1)
    T.set(b.body, "rotation_euler", lambda f: (0, 0.1 * math.sin(f * 0.08), 0.25), f0, f1)
    if zeigen:
        a, z = zeigen
        T.set(b.pfeil, "scale", lambda f: (1, 1, 1) if a <= f < z else (0, 0, 0), f0, f1)
        T.set(b.pfeil, "location", lambda f: (0, 0, -0.5 - 0.1 * abs(math.sin(f * 0.25))), f0, f1)
