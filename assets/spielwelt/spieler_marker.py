"""Spieler-Marker: schwebender tuerkiser Pfeil mit Ring am Boden. Zustaende: aus, schwebt, senkt (setzt sich auf ein Ziel)."""
import math

import look as L
import spielwelt as SW
import _zustand as Z

INFO = {"name": "spieler_marker", "groesse": [1.0, 1.0, 1.6], "anker": "spitze_unten", "zustaende": ["aus", "schwebt", "senkt"],
        "beschreibung": "zeigt auf Kalles Laden (Spiel-Oberflaeche, Tuerkis)"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    m = SW.m("tuerkis", "tuerkis", 0.3, emit="#2EE6D6", strength=2.5)
    pf = L.empty(f"{name}_pfeil", root, (0, 0, 2.2), coll)
    L.cyl(f"{name}_spitze", 0.45, 0.6, 4, m, pf, (0, 0, -0.3), coll, r2=0.0).rotation_euler = (math.pi, 0, math.pi / 4)
    SW.rbox(f"{name}_schaft", (0.32, 0.32, 0.55), m, pf, (0, 0, 0.27), coll, r=0.06)
    ring = L.torus(f"{name}_ring", 0.9, 0.06, 32, 4, m, root, (0, 0, 0.1), coll)
    root.scale = (0, 0, 0)
    return SW.P(root=root, pfeil=pf, ring=ring)


def zustand(T, o, plan, f0, f1):
    def sc(f):
        z = Z.aktiv(plan, f, "aus")
        return (0, 0, 0) if z == "aus" else (1, 1, 1)
    T.set(o.root, "scale", sc, f0, f1)

    def hoehe(f):
        z = Z.aktiv(plan, f, "aus")
        t = Z.seit(plan, f)
        basis = 2.2 if z == "schwebt" else 2.2 + 3.0 * max(0.0, 1 - t / 18) ** 2
        return (0, 0, basis + 0.18 * math.sin(f * 0.15))
    T.set(o.pfeil, "location", hoehe, f0, f1)
    T.set(o.pfeil, "rotation_euler", lambda f: (0, 0, f * 0.04), f0, f1)
    T.set(o.ring, "scale", lambda f: ((0.85 + 0.15 * math.sin(f * 0.2)),) * 3, f0, f1)
