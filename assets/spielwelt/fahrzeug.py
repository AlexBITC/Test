"""Kleine Autos und Busse (rund, Spielzeug-Look). typ: auto (Farbe als Parameter), bus. Zustand: faehrt (auf Wegpunkten)."""
import look as L
import spielwelt as SW

INFO = {"name": "fahrzeug", "groesse": [1.2, 0.6, 0.6], "anker": "mitte_unten", "zustaende": ["faehrt"],
        "beschreibung": "Auto oder Bus, faehrt mit spielwelt.laufen auf Wegpunkten"}


def bauen(coll, name, typ="auto", farbe="#E2483F", **kw):
    root = L.empty(name, coll=coll)
    if typ == "bus":
        SW.rbox(f"{name}_b", (0.9, 2.4, 0.95), SW.m("bus", "#F2C94C", 0.5), root, (0, 0, 0.62), coll, r=0.18, seg=3)
        for k in range(4):
            SW.rbox(f"{name}_f{k}", (0.92, 0.38, 0.28), SW.m("zugfenster", "#3E5A86", 0.3), root, (0, -0.8 + 0.53 * k, 0.82), coll, r=0.06)
        rad_y = (-0.8, 0.8)
    else:
        SW.rbox(f"{name}_b", (0.62, 1.1, 0.38), SW.m(f"auto{farbe}", farbe, 0.45), root, (0, 0, 0.32), coll, r=0.14, seg=3)
        SW.rbox(f"{name}_k", (0.5, 0.6, 0.3), SW.m(f"auto{farbe}", farbe, 0.45), root, (0, 0.05, 0.62), coll, r=0.12, seg=3)
        SW.rbox(f"{name}_s", (0.52, 0.5, 0.18), SW.m("zugfenster", "#3E5A86", 0.3), root, (0, 0.05, 0.64), coll, r=0.06)
        rad_y = (-0.35, 0.35)
    for y in rad_y:
        for x in (-0.33, 0.33) if typ != "bus" else (-0.48, 0.48):
            L.cyl(f"{name}_r{x}{y}", 0.13, 0.08, 10, SW.m("reifen", "#2E2A33", 0.6), root, (x, y, 0.13), coll, axis="X")
    return SW.P(root=root)
