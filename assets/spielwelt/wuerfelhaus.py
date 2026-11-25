"""Weisses Wuerfelhaus im Neubaugebiet mit Flachdach, Rasen und Hecke. Zustaende: tag, abend."""
import look as L
import spielwelt as SW

INFO = {"name": "wuerfelhaus", "groesse": [2.2, 2.2, 1.6], "anker": "mitte_unten", "zustaende": ["tag", "abend"],
        "beschreibung": "gleichfoermiges Neubau-Haus mit Garten"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_rasen", (2.4, 2.4, 0.04), SW.m("rasen", "#A3D67E", 0.8), root, (0, 0, 0.02), coll)
    SW.rbox(f"{name}_b", (1.3, 1.2, 1.2), SW.m("weiss", "weiss", 0.7), root, (0, 0.2, 0.6), coll, r=0.08)
    SW.rbox(f"{name}_d", (1.4, 1.3, 0.1), SW.m("flachdach", "#C9CCD8", 0.7), root, (0, 0.2, 1.24), coll, r=0.04)
    for x in (-0.3, 0.3):
        SW.rbox(f"{name}_f{x}", (0.3, 0.05, 0.3), SW.m("fenster", "#5A7FB0", 0.4), root, (x, -0.42, 0.75), coll, r=0.04)
    SW.rbox(f"{name}_hecke", (2.2, 0.25, 0.3), SW.m("hecke", "laub2", 0.8), root, (0, -1.05, 0.15), coll, r=0.1)
    return SW.P(root=root)
