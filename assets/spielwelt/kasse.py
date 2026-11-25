"""Kasse: Schublade springt bei jedem Verkauf auf (Liste von Frames), kleines Display. Zustaende: zu, auf."""
import math

import look as L
import spielwelt as SW

INFO = {"name": "kasse", "groesse": [0.7, 0.6, 0.6], "anker": "mitte_unten", "zustaende": ["zu", "auf"],
        "beschreibung": "Ladenkasse auf der Theke"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    SW.rbox(f"{name}_k", (0.62, 0.5, 0.32), SW.m("kasse", "#3E4A6A", 0.5), root, (0, 0, 0.26), coll, r=0.06)
    SW.rbox(f"{name}_disp", (0.4, 0.06, 0.18), SW.m("kasse_disp", "#7FE8C8", 0.3), root, (0, 0.05, 0.53), coll, r=0.03).rotation_euler = (0.4, 0, 0)
    for k in range(6):
        L.box(f"{name}_t{k}", (0.08, 0.08, 0.03), SW.m("weiss", "weiss", 0.5), root, (-0.15 + 0.1 * (k % 3), -0.1 - 0.1 * (k // 3), 0.43), coll)
    sch = L.empty(f"{name}_schub", root, (0, 0, 0), coll)
    SW.rbox(f"{name}_s", (0.56, 0.42, 0.1), SW.m("kasse_s", "#5A6688", 0.5), sch, (0, -0.02, 0.06), coll, r=0.03)
    for k in range(4):
        L.cyl(f"{name}_m{k}", 0.04, 0.02, 10, SW.m("gold", "gold", 0.4), sch, (-0.18 + 0.12 * k, -0.05, 0.12), coll)
    return SW.P(root=root, schub=sch)


def verkaeufe(T, k, frames, f0, f1):
    def y(f):
        a = max([max(0.0, 1 - abs(f - x - 4) / 6) for x in frames if x - 2 <= f <= x + 12] + [0.0])
        return (0, -0.32 * a, 0)
    T.set(k.schub, "location", y, f0, f1)
