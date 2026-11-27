"""Kirche mit Turm, Turmuhr und goldenem Kreuz (Altstadt). Zustand: tag."""
import math

import look as L
import spielwelt as SW

INFO = {"name": "kirche", "groesse": [2.4, 3.6, 6.2], "anker": "mitte_unten", "zustaende": ["tag"],
        "beschreibung": "Kirche der Altstadt mit Turmuhr"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    wand = SW.m("kirche", "#EFE6D6", 0.7)
    dach = SW.m("kirchdach", "#5E6A8C", 0.6)
    SW.rbox(f"{name}_schiff", (2.0, 3.0, 2.2), wand, root, (0, 0.6, 1.1), coll, r=0.1)
    L.poly_flat(f"{name}_sd", [(-1.15, 0), (1.15, 0), (0, 1.1)], 3.2, dach, root, (0, 0.6, 2.2), coll)
    SW.rbox(f"{name}_turm", (1.1, 1.1, 4.2), wand, root, (0, -1.2, 2.1), coll, r=0.08)
    sp = L.cyl(f"{name}_spitze", 0.85, 1.8, 4, dach, root, (0, -1.2, 5.1), coll, r2=0.0)
    sp.rotation_euler = (0, 0, math.pi / 4)
    L.cyl(f"{name}_uhr", 0.32, 0.06, 20, SW.m("weiss", "weiss", 0.5), root, (0, -1.78, 3.3), coll, axis="Y")
    L.box(f"{name}_zh", (0.05, 0.02, 0.2), SW.m("dunkel", "dunkel", 0.5), root, (0, -1.82, 3.37), coll)
    L.box(f"{name}_zm", (0.2, 0.02, 0.05), SW.m("dunkel", "dunkel", 0.5), root, (0.08, -1.82, 3.3), coll)
    L.box(f"{name}_kreuz", (0.08, 0.08, 0.5), SW.m("gold", "gold", 0.4), root, (0, -1.2, 6.2), coll)
    L.box(f"{name}_kreuz2", (0.3, 0.08, 0.08), SW.m("gold", "gold", 0.4), root, (0, -1.2, 6.3), coll)
    SW.rbox(f"{name}_tuer", (0.5, 0.06, 0.9), SW.m("tuer", "holz_d", 0.6), root, (0, -1.78, 0.45), coll, r=0.1)
    return SW.P(root=root)
