"""Mini-Lea (Chibi): Zopf, Kaeppi, Schuerze mit Mehlfleck. Animationen: laufen, backen, kassieren, daumen_hoch."""
import math

import look as L
import spielwelt as SW
import _chibi as CH

INFO = {"name": "mini_lea", "groesse": [0.6, 0.5, 1.2], "anker": "mitte_unten",
        "zustaende": ["stehen", "laufen", "backen", "kassieren", "daumen_hoch"], "beschreibung": "Chibi-Lea (Spielfigur)"}


def bauen(coll, name, h=0.95, **kw):
    d = CH.koerper(coll, name, "#6E9FB0", schuerze="#FBF8F0", h=h, haut="#F2C3A0")
    k, s, kr = d["kopf"], d["s"], d["kr"]
    haar = SW.m("lea_haar", "#4A2E22", 0.6)
    L.sphere(f"{name}_haar", kr * 1.04, 14, 8, (1, 1, 0.75), haar, k, (0, 0.04 * s, kr * 1.35), coll)
    for j in range(3):
        L.sphere(f"{name}_zopf{j}", (0.08 - 0.012 * j) * s, 8, 5, (1, 1, 1.2), haar, k, (-0.2 * s, 0.2 * s, kr * (0.9 - 0.35 * j)), coll)
    L.cyl(f"{name}_kaeppi", kr * 0.85, 0.1 * s, 14, SW.m("muetze", "weiss", 0.6), k, (0, 0.05 * s, kr * 1.85), coll)
    L.sphere(f"{name}_fleck", 0.06 * s, 8, 5, (1.2, 0.2, 1), SW.m("mehlfleck", "#E7DCC8", 0.8), d["body"], (0.06 * s, -0.16 * s, 0.42 * s),
             coll)
    L.sphere(f"{name}_mund", 0.035 * s, 8, 5, (1.4, 0.5, 0.6), SW.m("mund", "#B5484F", 0.6), k, (0, -kr * 0.96, kr * 0.7), coll)
    return SW.P(**d)


def animation(T, o, art, f0, f1):
    if art == "backen":
        for a, ph in ((o.arm_l, 0), (o.arm_r, math.pi)):
            T.set(a, "rotation_euler", lambda f, ph=ph: (-1.2 + 0.4 * math.sin(f * 0.5 + ph), 0, 0), f0, f1)
    elif art == "kassieren":
        T.set(o.arm_r, "rotation_euler", lambda f: (-1.3 + 0.5 * max(0.0, math.sin(f * 0.7)), 0, 0), f0, f1)
    elif art == "daumen_hoch":
        T.set(o.arm_r, "rotation_euler", lambda f: (-2.0, -0.3, 0), f0, f1)
        T.set(o.body, "location", lambda f: (0, 0, 0.06 * o.s * abs(math.sin(f * 0.3))), f0, f1)
    elif art == "jubel":
        for a, sx in ((o.arm_l, 1), (o.arm_r, -1)):
            T.set(a, "rotation_euler", lambda f, sx=sx: (-2.9 + 0.2 * math.sin(f * 0.6), sx * 0.3, 0), f0, f1)
        T.set(o.body, "location", lambda f: (0, 0, 0.12 * o.s * abs(math.sin(f * 0.35))), f0, f1)
