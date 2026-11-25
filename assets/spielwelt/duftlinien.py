"""Effekt Duftlinien: drei geschwungene, helle Linien steigen ueber fertiger Ware auf. Zustaende: aus, an."""
import math

import look as L
import spielwelt as SW

INFO = {"name": "duftlinien", "groesse": [0.4, 0.1, 0.6], "anker": "mitte_unten", "zustaende": ["aus", "an"],
        "beschreibung": "ueber fertiger Ware"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    linien = []
    for j in range(3):
        p = L.empty(f"{name}_l{j}", root, (-0.15 + 0.15 * j, 0, 0), coll)
        for k in range(5):
            L.sphere(f"{name}_d{j}{k}", 0.03, 6, 4, (1, 1, 1), SW.m("duft", "#FFF6E0", 0.4, alpha=0.8), p,
                     (0.05 * math.sin(k * 1.3), 0, 0.1 * k), coll)
        linien.append(p)
    root.scale = (0, 0, 0)
    return SW.P(root=root, linien=linien)


def an(T, d, f_an, f_aus, f0, f1):
    T.set(d.root, "scale", lambda f: (1, 1, 1) if f_an <= f < f_aus else (0, 0, 0), f0, f1)
    for j, p in enumerate(d.linien):
        T.set(p, "location", lambda f, j=j: (-0.15 + 0.15 * j + 0.04 * math.sin(f * 0.2 + j), 0, (f * 0.01 + j * 0.1) % 0.3), f0, f1)
