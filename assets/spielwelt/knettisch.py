"""Knettisch der Backstube mit Teigkugel, Mehl und Nudelholz. Zustand: tag."""
import look as L
import spielwelt as SW

INFO = {"name": "knettisch", "groesse": [2.0, 1.0, 1.0], "anker": "mitte_unten", "zustaende": ["tag"], "beschreibung": "Arbeitstisch"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    SW.rbox(f"{name}_p", (2.0, 0.9, 0.1), SW.m("holz_hell", "#E0B27A", 0.6), root, (0, 0, 0.9), coll, r=0.04)
    for dx in (-0.9, 0.9):
        for dy in (-0.38, 0.38):
            L.box(f"{name}_b{dx}{dy}", (0.08, 0.08, 0.88), SW.m("holz_d", "holz_d", 0.6), root, (dx, dy, 0.44), coll)
    L.sphere(f"{name}_teig", 0.22, 10, 7, (1.2, 1, 0.6), SW.m("teig", "teig", 0.7), root, (-0.4, 0, 1.05), coll)
    L.cyl(f"{name}_mehl", 0.3, 0.01, 12, SW.m("mehl", "weiss", 0.9), root, (0.3, 0.1, 0.96), coll)
    L.cyl(f"{name}_holz", 0.06, 0.6, 10, SW.m("holz", "holz", 0.6), root, (0.4, -0.2, 1.0), coll, axis="X")
    return SW.P(root=root)
