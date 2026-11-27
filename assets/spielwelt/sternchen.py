"""Effekt Sternchen (Level-Up): goldene Sterne funkeln auf und drehen sich. Zustaende: aus, an."""
import math
import random

import look as L
import spielwelt as SW

INFO = {"name": "sternchen", "groesse": [3.0, 3.0, 3.0], "anker": "mitte", "zustaende": ["aus", "an"], "beschreibung": "Level-Up"}


def bauen(coll, name, n=14, **kw):
    root = L.empty(name, coll=coll)
    rnd = random.Random(8)
    sterne = []
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        r = 0.2 if k % 2 == 0 else 0.08
        pts.append((r * math.cos(a), r * math.sin(a)))
    for k in range(n):
        o = L.poly_flat(f"{name}_{k}", pts, 0.03, SW.m("gold_leucht", "gold", 0.3, emit="#FFE14D", strength=3.0), root,
                        (rnd.uniform(-1.5, 1.5), 0, rnd.uniform(0, 2.5)), coll)
        sterne.append(o)
    root.scale = (0, 0, 0)
    return SW.P(root=root, sterne=sterne)


def an(T, s, f_an, f_aus, f0, f1):
    T.set(s.root, "scale", lambda f: (1, 1, 1) if f_an <= f < f_aus else (0, 0, 0), f0, f1)
    for k, o in enumerate(s.sterne):
        T.set(o, "scale", lambda f, k=k: ((0.4 + 0.8 * max(0.0, math.sin(f * 0.3 + k))),) * 3, f0, f1)
        T.set(o, "rotation_euler", lambda f, k=k: (0, f * 0.1 + k, 0), f0, f1)
