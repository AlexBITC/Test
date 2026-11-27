"""Blechwagen mit vier Blechen (Waren sichtbar). Zustand: tag."""
import look as L
import spielwelt as SW
import ware as WA

INFO = {"name": "blechwagen", "groesse": [0.9, 0.7, 1.6], "anker": "mitte_unten", "zustaende": ["tag"], "beschreibung": "Rollwagen"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    for x in (-0.4, 0.4):
        L.box(f"{name}_p{x}", (0.05, 0.6, 1.5), SW.m("metall", "#8A8EA6", 0.4), root, (x, 0, 0.8), coll)
    for k in range(4):
        z = 0.4 + 0.33 * k
        L.box(f"{name}_blech{k}", (0.8, 0.6, 0.03), SW.m("blech", "#B9BCCB", 0.3), root, (0, 0, z), coll)
        for j in range(3):
            w = WA.bauen(coll, f"{name}_w{k}{j}", art="brezel", s=0.9)
            w.root.parent = root
            w.root.location = (-0.25 + 0.25 * j, 0, z + 0.02)
    return SW.P(root=root)
