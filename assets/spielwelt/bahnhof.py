"""Bahnhof: Empfangsgebaeude mit Uhrturm (Bahnhofsuhr), Bahnsteig mit Dach und Gleisen ueber das Brett.
Zustaende: tag, abend. uhr_stellen(T, b, minuten_fn) bewegt die Zeiger."""
import math

import look as L
import spielwelt as SW

INFO = {"name": "bahnhof", "groesse": [7.0, 4.0, 4.0], "anker": "mitte_unten", "zustaende": ["tag", "abend"],
        "beschreibung": "Bahnhof mit Uhr, Bahnsteig und Gleisen (Gleise reichen bis zum Brettrand)"}


def bauen(coll, name, gleis_y=-2.6, **kw):
    root = L.empty(name, coll=coll)
    wand = SW.m("bhf", "#E29A68", 0.7)
    SW.rbox(f"{name}_b", (4.6, 1.8, 1.7), wand, root, (0, 0, 0.85), coll, r=0.1)
    L.poly_flat(f"{name}_d", [(-2.45, 0), (2.45, 0), (0, 0.8)], 2.0, SW.m("bhfdach", "#6A5A80", 0.6), root, (0, 0, 1.7), coll)
    SW.rbox(f"{name}_turm", (1.0, 1.0, 3.0), wand, root, (0, -0.2, 1.5), coll, r=0.08)
    L.cyl(f"{name}_turmd", 0.8, 0.8, 4, SW.m("bhfdach", "#6A5A80", 0.6), root, (0, -0.2, 3.4), coll, r2=0.0).rotation_euler = (0, 0, 0.785)
    uhr = L.empty(f"{name}_uhr", root, (0, -0.74, 2.45), coll)
    L.cyl(f"{name}_ub", 0.36, 0.08, 24, SW.m("weiss", "weiss", 0.5), uhr, (0, 0, 0), coll, axis="Y")
    L.torus(f"{name}_ur", 0.36, 0.04, 24, 4, SW.m("dunkel", "dunkel", 0.5), uhr, (0, 0, 0), coll, axis="Y")
    zh = L.empty(f"{name}_zh", uhr, (0, -0.06, 0), coll)
    L.box(f"{name}_zhm", (0.05, 0.02, 0.2), SW.m("dunkel", "dunkel", 0.5), zh, (0, 0, 0.09), coll)
    zm = L.empty(f"{name}_zm", uhr, (0, -0.07, 0), coll)
    L.box(f"{name}_zmm", (0.04, 0.02, 0.28), SW.m("dunkel", "dunkel", 0.5), zm, (0, 0, 0.13), coll)
    for x in (-1.6, -0.9, 0.9, 1.6):
        SW.rbox(f"{name}_f{x}", (0.4, 0.06, 0.6), SW.m("fenster", "#5A7FB0", 0.4), root, (x, -0.92, 0.8), coll, r=0.05)
    SW.rbox(f"{name}_schild", (1.6, 0.06, 0.32), SW.m("schild_navy", "#1E2A44", 0.5), root, (-1.25, -0.95, 1.45), coll, r=0.05)
    SW.text(f"{name}_t", "BAHNHOF", 0.22, SW.m("schild_weiss", "weiss", 0.5), root, (-1.25, -0.99, 1.38), coll)
    # Bahnsteig mit Dach
    SW.rbox(f"{name}_steig", (7.0, 1.0, 0.25), SW.m("steig", "#C9C2B4", 0.7), root, (0.6, gleis_y + 1.2, 0.12), coll, r=0.05)
    for x in (-2.0, 0.6, 3.2):
        L.box(f"{name}_st{x}", (0.1, 0.1, 1.2), SW.m("holz_d", "holz_d", 0.6), root, (x, gleis_y + 1.2, 0.85), coll)
    SW.rbox(f"{name}_sd", (6.8, 1.3, 0.12), SW.m("steigdach", "#8A6A9A", 0.6), root, (0.6, gleis_y + 1.2, 1.5), coll, r=0.04)
    # Gleise
    x0, x1 = -4.2, 6.3
    SW.rbox(f"{name}_bett", (x1 - x0, 1.2, 0.1), SW.m("schotter", "#9A8C7E", 0.8), root, ((x0 + x1) / 2, gleis_y, 0.05), coll, r=0.03)
    for sy in (-0.3, 0.3):
        L.box(f"{name}_sch{sy}", (x1 - x0, 0.07, 0.08), SW.m("schiene", "#D6D9E2", 0.3), root, ((x0 + x1) / 2, gleis_y + sy, 0.14), coll)
    for k in range(int((x1 - x0) / 0.5)):
        L.box(f"{name}_sw{k}", (0.15, 0.9, 0.05), SW.m("schwelle", "holz_d", 0.7), root, (x0 + 0.25 + 0.5 * k, gleis_y, 0.11), coll)
    return SW.P(root=root, uhr_h=zh, uhr_m=zm, gleis_y=gleis_y, gleis=(x0, x1))


def uhr_stellen(T, b, minuten_fn, f0, f1):
    T.set(b.uhr_m, "rotation_euler", lambda f: (0, (minuten_fn(f) % 60) / 60 * 2 * math.pi, 0), f0, f1)
    T.set(b.uhr_h, "rotation_euler", lambda f: (0, (minuten_fn(f) / 60 % 12) / 12 * 2 * math.pi, 0), f0, f1)
