"""Effekt Muenz-Pop: goldene Muenze springt aus der Kasse hoch, dreht sich, verschwindet (8-Bit-Pop im Ton).
Zustaende: einmalig je Ausloesung."""
import math

import look as L
import spielwelt as SW

INFO = {"name": "muenz_pop", "groesse": [0.3, 0.05, 0.3], "anker": "mitte", "zustaende": ["pop"], "beschreibung": "Effekt ueber der Kasse"}


def bauen(coll, name, n=8, **kw):
    root = L.empty(name, coll=coll)
    muenzen = []
    for k in range(n):
        o = L.cyl(f"{name}_{k}", 0.12, 0.03, 16, SW.m("gold_leucht", "gold", 0.3, emit="#FFE14D", strength=3.0), root, (0, 0, 0), coll,
                  axis="Y")
        o.scale = (0, 0, 0)
        muenzen.append(o)
    return SW.P(root=root, muenzen=muenzen)


def ausloesen(T, mp, frames, f0, f1):
    """frames: Ausloese-Zeitpunkte; Muenzen werden reihum benutzt."""
    for k, o in enumerate(mp.muenzen):
        eig = [x for i, x in enumerate(frames) if i % len(mp.muenzen) == k]

        def sc(f, eig=eig):
            for x in eig:
                if x <= f < x + 16:
                    t = (f - x) / 16
                    return (1.0 - 0.6 * t,) * 3
            return (0, 0, 0)

        def loc(f, eig=eig):
            for x in eig:
                if x <= f < x + 16:
                    t = (f - x) / 16
                    return (0.1 * math.sin(k), 0, 1.4 * math.sin(math.pi * min(1.0, t * 1.3)))
            return (0, 0, 0)
        T.set(o, "scale", sc, f0, f1)
        T.set(o, "location", loc, f0, f1)
        T.set(o, "rotation_euler", lambda f: (0, 0, f * 0.5), f0, f1)
