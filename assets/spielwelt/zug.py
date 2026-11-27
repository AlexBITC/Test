"""Zug (drei Wagen, rot-weiss, runde Kanten). Zustaende: weg, einfahren, steht, ausfahren."""
import look as L
import spielwelt as SW
from anim import ease_out, clamp01

INFO = {"name": "zug", "groesse": [7.5, 1.0, 1.1], "anker": "mitte_unten", "zustaende": ["weg", "einfahren", "steht", "ausfahren"],
        "beschreibung": "Regionalzug auf den Bahnhofsgleisen"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    for w in range(3):
        x = w * 2.5
        SW.rbox(f"{name}_w{w}", (2.35, 0.9, 0.95), SW.m("zug", "weiss", 0.5), root, (x, 0, 0.62), coll, r=0.18, seg=3)
        L.box(f"{name}_s{w}", (2.37, 0.92, 0.18), SW.m("zugrot", "rot", 0.5), root, (x, 0, 0.36), coll)
        for k in range(4):
            SW.rbox(f"{name}_f{w}{k}", (0.36, 0.93, 0.28), SW.m("zugfenster", "#3E5A86", 0.3), root, (x - 0.8 + 0.53 * k, 0, 0.82),
                    coll, r=0.06)
    SW.rbox(f"{name}_nase", (0.4, 0.86, 0.7), SW.m("zugrot", "rot", 0.5), root, (-1.3, 0, 0.55), coll, r=0.2)
    return SW.P(root=root)


def fahrt(T, z, y, x_weg, x_halt, f_ein, f_halt, f0, f1, z0=0.15):
    """Zug faehrt von x_weg ein (ease out) und haelt bei x_halt."""
    def x(f):
        if f < f_ein:
            return x_weg
        return x_weg + (x_halt - x_weg) * ease_out(clamp01((f - f_ein) / max(1, f_halt - f_ein)))
    T.set(z.root, "location", lambda f: (x(f), y, z0), f0, f1)
    return x
