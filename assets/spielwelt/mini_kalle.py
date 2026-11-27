"""Mini-Kalle (Chibi): riesige Baeckermuetze, Schnurrbart, Schuerze. Animationen: laufen, backen, kassieren,
verzweifelt (sitzt auf dem Mehlsack, Haende am Kopf)."""
import math

import look as L
import spielwelt as SW
import _chibi as CH

INFO = {"name": "mini_kalle", "groesse": [0.6, 0.5, 1.4], "anker": "mitte_unten",
        "zustaende": ["stehen", "laufen", "backen", "kassieren", "verzweifelt"], "beschreibung": "Chibi-Kalle (Spielfigur)"}


def bauen(coll, name, h=1.0, **kw):
    d = CH.koerper(coll, name, "#7C8DB5", schuerze="#FBF8F0", h=h)
    k, s, kr = d["kopf"], d["s"], d["kr"]
    w = SW.m("muetze", "weiss", 0.6)
    L.cyl(f"{name}_mband", kr * 0.9, 0.16 * s, 14, w, k, (0, 0.02 * s, kr * 1.75), coll)
    for i, (x, y, z, r) in enumerate([(0, 0, 0.34, 0.3), (-0.17, 0, 0.28, 0.2), (0.17, 0, 0.28, 0.2), (0, -0.12, 0.3, 0.2)]):
        L.sphere(f"{name}_mp{i}", r * s, 10, 7, (1, 1, 0.8), w, k, (x * s, y * s, kr * 1.75 + z * s), coll)
    for sx in (-1, 1):
        b = L.sphere(f"{name}_bart{sx}", 0.09 * s, 8, 5, (1.4, 0.55, 0.5), SW.m("bart", "#3A2A22", 0.6), k,
                     (sx * 0.08 * s, -kr * 0.96, kr * 0.72), coll)
        b.rotation_euler = (0, sx * 0.3, 0)
    L.sphere(f"{name}_nase", 0.06 * s, 8, 5, (1, 1, 1), SW.m("nase", "#E89A78", 0.6), k, (0, -kr * 1.0, kr * 0.86), coll)
    return SW.P(**d)


def animation(T, o, art, f0, f1):
    """art: backen (Arme kneten), kassieren (Arm tippt), verzweifelt (sitzt, Haende am Kopf, wippt), jubel."""
    if art == "backen":
        for a, ph in ((o.arm_l, 0), (o.arm_r, math.pi)):
            T.set(a, "rotation_euler", lambda f, ph=ph: (-1.2 + 0.4 * math.sin(f * 0.5 + ph), 0, 0), f0, f1)
    elif art == "kassieren":
        T.set(o.arm_r, "rotation_euler", lambda f: (-1.3 + 0.5 * max(0.0, math.sin(f * 0.7)), 0, 0), f0, f1)
    elif art == "verzweifelt":
        T.set(o.body, "location", lambda f: (0, 0, -0.12 * o.s), f0, f1)
        for a, sx in ((o.arm_l, 1), (o.arm_r, -1)):
            T.set(a, "rotation_euler", lambda f, sx=sx: (-2.7, sx * 0.5, 0), f0, f1)
        T.set(o.kopf, "rotation_euler", lambda f: (0.25 + 0.06 * math.sin(f * 0.3), 0, 0.15 * math.sin(f * 0.2)), f0, f1)
        for b in (o.bein_l, o.bein_r):
            T.set(b, "rotation_euler", lambda f: (-1.3, 0, 0), f0, f1)
    elif art == "jubel":
        for a, sx in ((o.arm_l, 1), (o.arm_r, -1)):
            T.set(a, "rotation_euler", lambda f, sx=sx: (-2.9 + 0.2 * math.sin(f * 0.6), sx * 0.3, 0), f0, f1)
        T.set(o.body, "location", lambda f: (0, 0, 0.12 * o.s * abs(math.sin(f * 0.35))), f0, f1)
