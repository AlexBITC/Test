"""Laubbaum (rund, verspielt), wiegt sich im Wind. Zustaende: ruhig, wiegen."""
import math
import random

import look as L
import spielwelt as SW

INFO = {"name": "baum", "groesse": [1.2, 1.2, 2.2], "anker": "mitte_unten", "zustaende": ["ruhig", "wiegen"],
        "beschreibung": "Baum, Krone wiegt sich"}


def bauen(coll, name, s=1.0, **kw):
    root = L.empty(name, coll=coll)
    root.scale = (s, s, s)
    L.cyl(f"{name}_stamm", 0.12, 0.8, 7, SW.m("holz_d", "holz_d", 0.7), root, (0, 0, 0.4), coll, r2=0.09)
    krone = L.empty(f"{name}_krone", root, (0, 0, 0.75), coll)
    col = random.Random(name).choice(["laub", "laub2", "#6DB656"])
    L.ico(f"{name}_k1", 0.55, 1, (1, 1, 1.05), SW.m(f"laub_{col}", col, 0.75), krone, (0, 0, 0.55), coll)
    L.ico(f"{name}_k2", 0.36, 1, (1, 1, 1), SW.m(f"laub_{col}", col, 0.75), krone, (0.3, -0.1, 0.95), coll)
    return SW.P(root=root, krone=krone)


def wiegen(T, b, f0, f1, staerke=1.0):
    ph = random.Random(b.root.name).uniform(0, 6.28)
    T.set(b.krone, "rotation_euler", lambda f: (0.05 * staerke * math.sin(f * 0.07 + ph), 0.06 * staerke * math.sin(f * 0.05 + ph * 2), 0),
          f0, f1)
