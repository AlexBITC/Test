"""Marktplatz der Altstadt: rundes Pflaster, Brunnenrand und Weihnachtsbaum mit funkelnder Lichterkette.
Zustaende: tag, abend (Lichter heller)."""
import math
import random

import look as L
import spielwelt as SW

INFO = {"name": "marktplatz", "groesse": [4.6, 4.6, 3.0], "anker": "mitte_unten", "zustaende": ["tag", "abend"],
        "beschreibung": "Marktplatz mit Weihnachtsbaum (wie in der Stadtkarte)"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_pflaster", 2.3, 0.06, 32, SW.m("pflaster", "#D8C29A", 0.8), root, (0, 0, 0.03), coll)
    L.torus(f"{name}_ring", 1.7, 0.06, 32, 4, SW.m("pflaster2", "#C2AA80", 0.8), root, (0, 0, 0.07), coll)
    baum = L.empty(f"{name}_baum", root, (0, 0, 0.06), coll)
    m_t = SW.m("tanne", "#2F8A4E", 0.7)
    for j, (r, z) in enumerate([(0.9, 0.5), (0.7, 1.15), (0.48, 1.75)]):
        L.cyl(f"{name}_t{j}", r, 0.9, 8, m_t, baum, (0, 0, z), coll, r2=0.0)
    L.cyl(f"{name}_stamm", 0.12, 0.3, 8, SW.m("holz_d", "holz_d", 0.6), baum, (0, 0, 0.1), coll)
    L.ico(f"{name}_stern", 0.18, 0, (1, 1, 1), SW.m("gold_leucht", "gold", 0.3, emit="#FFE14D", strength=3.0), baum, (0, 0, 2.3), coll)
    lichter = []
    rnd = random.Random(4)
    for k in range(18):
        a = rnd.uniform(0, 6.28)
        z = rnd.uniform(0.2, 1.9)
        rr = 0.85 * (1 - z / 2.3) + 0.05
        col = ["#FF5A5F", "#FFE14D", "#FFFFFF"][k % 3]
        lichter.append(L.ico(f"{name}_l{k}", 0.07, 0, (1, 1, 1), SW.m(f"licht{k % 3}", col, 0.3, emit=col, strength=3.0), baum,
                             (rr * math.cos(a), rr * math.sin(a), z), coll))
    for k in range(6):
        a = k * math.pi / 3
        SW.rbox(f"{name}_bank{k}", (0.7, 0.25, 0.25), SW.m("holz", "holz", 0.6), root,
                (2.0 * math.cos(a), 2.0 * math.sin(a), 0.15), coll, r=0.05).rotation_euler = (0, 0, a + math.pi / 2)
    return SW.P(root=root, lichter=lichter, wetter=lambda T, S, f0, f1: _funkeln(T, lichter, f0, f1))


def _funkeln(T, lichter, f0, f1):
    for k, o in enumerate(lichter):
        T.set(o, "scale", lambda f, k=k: ((0.7 + 0.5 * max(0.0, math.sin(f * 0.22 + k * 1.9))),) * 3, f0, f1)
