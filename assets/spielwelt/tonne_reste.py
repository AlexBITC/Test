"""Muelltonne 'RESTE': fuellt sich sichtbar (Haufen grauer Waren waechst), Deckel springt auf, wenn voll.
Zustaende: leer, fuellstand (0..1), voll (Deckel auf)."""
import math

import look as L
import spielwelt as SW

INFO = {"name": "tonne_reste", "groesse": [0.9, 0.9, 1.3], "anker": "mitte_unten", "zustaende": ["leer", "fuellstand", "voll"],
        "beschreibung": "Running Gag der Folge (voll / leer / zurueckgesetzt)"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    m = SW.m("tonne", "#4E7A5A", 0.6)
    L.cyl(f"{name}_k", 0.42, 1.0, 16, m, root, (0, 0, 0.5), coll, r2=0.38)
    SW.rbox(f"{name}_schild", (0.6, 0.05, 0.24), SW.m("weiss", "weiss", 0.5), root, (0, -0.42, 0.62), coll, r=0.04)
    SW.text(f"{name}_t", "RESTE", 0.15, SW.m("tonne_ink", "#2A3A2E", 0.5), root, (0, -0.46, 0.56), coll)
    haufen = L.empty(f"{name}_haufen", root, (0, 0, 0.95), coll)
    for k in range(7):
        a = k * 0.9
        L.ico(f"{name}_h{k}", 0.16, 1, (1.2, 1, 0.7), SW.m("rest_grau", "#8E8A86", 0.7), haufen,
              (0.2 * math.cos(a) * (k > 0), 0.2 * math.sin(a) * (k > 0), 0.05 + 0.12 * (k == 0)), coll)
    haufen.scale = (0, 0, 0)
    deckel = L.empty(f"{name}_deckelp", root, (0, 0.42, 1.02), coll)
    L.cyl(f"{name}_d", 0.46, 0.08, 16, m, deckel, (0, -0.42, 0), coll)
    return SW.P(root=root, haufen=haufen, deckel=deckel)


def fuellstand(T, t, fn, f0, f1):
    """fn(f) 0..1; ab 0,95 springt der Deckel auf und wackelt."""
    T.set(t.haufen, "scale", lambda f: (1.0, 1.0, max(0.0, min(1.3, fn(f)))) if fn(f) > 0.02 else (0, 0, 0), f0, f1)
    T.set(t.haufen, "location", lambda f: (0, 0, 0.6 + 0.4 * min(1.0, fn(f))), f0, f1)
    T.set(t.deckel, "rotation_euler", lambda f: (-1.6 - 0.15 * math.sin(f * 0.8) if fn(f) >= 0.95 else 0.0, 0, 0), f0, f1)
