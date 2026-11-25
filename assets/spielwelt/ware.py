"""Waren: brezel, broetchen, stollen. Gleiche Zustaende fuer alle: teig (blass), im_ofen, fertig (goldbraun, Dampflinien),
in_auslage, verkauft (springt mit Muenz-Pop in eine Tuete), rest (abends grau), muell (fliegt in die Tonne 'RESTE')."""
import math

import look as L
import spielwelt as SW
import _zustand as Z

ARTEN = ["brezel", "broetchen", "stollen"]
ZUSTAENDE = ["teig", "im_ofen", "fertig", "in_auslage", "verkauft", "rest", "muell"]
INFO = {"name": "ware", "groesse": [0.3, 0.3, 0.12], "anker": "mitte_unten", "zustaende": ZUSTAENDE, "arten": ARTEN,
        "beschreibung": "Backware, art als Parameter"}
FARBEN = {"teig": "#F2DDB5", "im_ofen": "#E9B870", "fertig": "#B8692A", "in_auslage": "#B8692A", "verkauft": "#B8692A",
          "rest": "#8E8A86", "muell": "#7A7672"}


def bauen(coll, name, art="brezel", s=1.0, **kw):
    root = L.empty(name, coll=coll)
    root.scale = (s, s, s)
    m = L.unique_mat(SW.m("ware", FARBEN["fertig"], 0.5), f"sw_ware_{name}")
    if art == "brezel":
        L.torus(f"{name}_b", 0.11, 0.035, 12, 5, m, root, (0, 0, 0.04), coll).scale = (1.2, 0.8, 1)
        for sx in (-1, 1):
            L.torus(f"{name}_o{sx}", 0.05, 0.03, 10, 5, m, root, (sx * 0.05, 0.04, 0.05), coll)
    elif art == "broetchen":
        L.sphere(f"{name}_b", 0.1, 10, 6, (1.2, 1, 0.7), m, root, (0, 0, 0.06), coll)
    else:
        SW.rbox(f"{name}_b", (0.28, 0.13, 0.1), m, root, (0, 0, 0.06), coll, r=0.04)
        SW.rbox(f"{name}_z", (0.26, 0.12, 0.03), SW.m("zucker", "weiss", 0.6), root, (0, 0, 0.11), coll, r=0.01)
    return SW.P(root=root, mat=m, art=art)


def farbe(T, w, plan, f0, f1):
    """Farbe nach Zustand (weicher Uebergang 8 Frames)."""
    cols = {k: L.srgb(v) for k, v in FARBEN.items()}

    def col(f):
        z = Z.aktiv(plan, f, "teig")
        t = min(1.0, Z.seit(plan, f) / 8)
        prev = Z.aktiv(plan, f - Z.seit(plan, f) - 1, "teig") if Z.seit(plan, f) < 10 ** 5 else z
        a, b = cols[prev], cols[z]
        return tuple(a[i] + (b[i] - a[i]) * t for i in range(3)) + (1,)
    T.set(w.mat, "diffuse_color", col, f0, f1)


def flug(T, w, von, nach, f_start, dauer=12, hoehe=0.8, f0=None, f1=None):
    """Bogenflug von 'von' nach 'nach' (Weltpunkte), z. B. in die Tuete oder in die Tonne."""
    from mathutils import Vector
    a, b = Vector(von), Vector(nach)

    def loc(f):
        t = max(0.0, min(1.0, (f - f_start) / dauer))
        p = a.lerp(b, t)
        return tuple(p + Vector((0, 0, hoehe * 4 * t * (1 - t))))
    T.set(w.root, "location", loc, f0 if f0 is not None else f_start - 1, f1 if f1 is not None else f_start + dauer + 1)
