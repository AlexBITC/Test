"""Bushaltestelle mit Glasdach, Bank und gelbem 'H'-Schild. Zustand: tag."""
import look as L
import spielwelt as SW

INFO = {"name": "bushaltestelle", "groesse": [1.6, 0.8, 1.6], "anker": "mitte_unten", "zustaende": ["tag"],
        "beschreibung": "Haltestelle am Bahnhof"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    SW.rbox(f"{name}_dach", (1.6, 0.8, 0.08), SW.m("glasdach", "#AED8F2", 0.3), root, (0, 0, 1.3), coll, r=0.03)
    for x in (-0.7, 0.7):
        L.box(f"{name}_p{x}", (0.06, 0.06, 1.3), SW.m("metall", "#8A8EA6", 0.4), root, (x, 0.3, 0.65), coll)
    SW.rbox(f"{name}_bank", (1.2, 0.3, 0.1), SW.m("holz", "holz", 0.6), root, (0, 0.15, 0.45), coll, r=0.04)
    L.box(f"{name}_mast", (0.06, 0.06, 1.7), SW.m("metall", "#8A8EA6", 0.4), root, (0.95, -0.3, 0.85), coll)
    L.cyl(f"{name}_schild", 0.24, 0.06, 18, SW.m("bus_gelb", "#F2C94C", 0.5), root, (0.95, -0.34, 1.6), coll, axis="Y")
    SW.text(f"{name}_h", "H", 0.3, SW.m("bus_gruen", "#2E7D32", 0.5), root, (0.95, -0.4, 1.5), coll)
    return SW.P(root=root)
