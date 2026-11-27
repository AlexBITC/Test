"""Lagerregal mit Mehlsaecken 'WEIZEN 550' (Anzahl sichtbar, leert sich). Zustand: anzahl (0-6)."""
import look as L
import spielwelt as SW

INFO = {"name": "lagerregal", "groesse": [1.2, 0.7, 1.8], "anker": "mitte_unten", "zustaende": ["anzahl(0-6)"],
        "beschreibung": "Mehlsaecke wie in der echten Backstube"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    for z in (0.05, 0.85, 1.65):
        SW.rbox(f"{name}_b{z}", (1.2, 0.6, 0.06), SW.m("holz", "holz", 0.6), root, (0, 0, z), coll, r=0.02)
    for x in (-0.58, 0.58):
        L.box(f"{name}_p{x}", (0.06, 0.6, 1.7), SW.m("holz_d", "holz_d", 0.6), root, (x, 0, 0.85), coll)
    saecke = []
    for k in range(6):
        x, z = -0.32 + 0.32 * (k % 3), 0.38 + 0.8 * (k // 3)
        s = L.empty(f"{name}_sack{k}", root, (x, 0, z), coll)
        SW.rbox(f"{name}_sm{k}", (0.28, 0.25, 0.5), SW.m("sack", "#E3CFA4", 0.8), s, (0, 0, -0.06), coll, r=0.09)
        SW.text(f"{name}_st{k}", "550", 0.08, SW.m("sack_ink", "#8A5A2E", 0.6), s, (0, -0.13, -0.08), coll)
        saecke.append(s)
    return SW.P(root=root, saecke=saecke)


def anzahl(T, r, fn, f0, f1):
    for k, s in enumerate(r.saecke):
        T.set(s, "scale", lambda f, k=k: (1, 1, 1) if k < round(fn(f)) else (0, 0, 0), f0, f1)
