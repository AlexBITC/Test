"""Effekt Rauchwolke (schwarz, bei 'verbrannt' oder Pleite): Kugeln steigen und wachsen. Zustaende: aus, an."""
import math

import look as L
import spielwelt as SW

INFO = {"name": "rauchwolke", "groesse": [1.0, 1.0, 2.0], "anker": "mitte_unten", "zustaende": ["aus", "an"],
        "beschreibung": "Rauch ueber dem Ofen"}


def bauen(coll, name, n=7, **kw):
    root = L.empty(name, coll=coll)
    puffs = [L.ico(f"{name}_{k}", 0.25, 1, (1, 1, 1), SW.m("rauch", "#2E2A33", 0.8), root, (0, 0, 0), coll) for k in range(n)]
    root.scale = (0, 0, 0)
    return SW.P(root=root, puffs=puffs)


def an(T, r, f_an, f_aus, f0, f1):
    T.set(r.root, "scale", lambda f: (1, 1, 1) if f_an <= f < f_aus else (0, 0, 0), f0, f1)
    for k, o in enumerate(r.puffs):
        T.set(o, "location", lambda f, k=k: (0.2 * math.sin(f * 0.1 + k), 0, (f * 0.03 + k * 0.3) % 2.0), f0, f1)
        T.set(o, "scale", lambda f, k=k: ((0.5 + (f * 0.03 + k * 0.3) % 2.0),) * 3, f0, f1)
