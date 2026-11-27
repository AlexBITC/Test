"""Fachwerkhaus der Altstadt (Spiel-Look): runde Kanten, Balken, Satteldach, Fensterlaeden. Zustaende: tag, abend
(Fenster leuchten warm)."""
import math

import look as L
import spielwelt as SW

INFO = {"name": "fachwerkhaus", "groesse": [1.8, 1.6, 2.4], "anker": "mitte_unten", "zustaende": ["tag", "abend"],
        "beschreibung": "Fachwerkhaus, Farbe und Hoehe als Parameter"}
WAENDE = ["#F7E6C8", "#F2D7B0", "#FBEBD6", "#EED2A6"]
DAECHER = ["dach", "dach2", "#C8573E"]


def bauen(coll, name, farbe=0, hoehe=1.6, **kw):
    root = L.empty(name, coll=coll)
    w, d = 1.6, 1.4
    SW.rbox(f"{name}_b", (w, d, hoehe), SW.m(f"wand{farbe % 4}", WAENDE[farbe % 4], 0.7), root, (0, 0, hoehe / 2), coll, r=0.08)
    L.poly_flat(f"{name}_dach", [(-w / 2 - 0.15, 0), (w / 2 + 0.15, 0), (0, 0.9)], d + 0.2,
                SW.m(f"dach{farbe % 3}", DAECHER[farbe % 3], 0.6), root, (0, 0, hoehe), coll)
    mb = SW.m("balken", "holz_d", 0.6)
    for x in (-0.75, 0, 0.75):
        L.box(f"{name}_p{x}", (0.08, 0.04, hoehe), mb, root, (x, -d / 2 - 0.02, hoehe / 2), coll)
    for z in (hoehe * 0.5, hoehe - 0.05):
        L.box(f"{name}_h{z:.2f}", (w, 0.04, 0.08), mb, root, (0, -d / 2 - 0.02, z), coll)
    fen = []
    m_f = L.unique_mat(SW.m("fenster", "#5A7FB0", 0.4), f"sw_fenster_{name}")
    for x in (-0.38, 0.38):
        for z in (0.45, hoehe * 0.5 + 0.35):
            fen.append(SW.rbox(f"{name}_f{x}{z:.2f}", (0.32, 0.05, 0.34), m_f, root, (x, -d / 2 - 0.03, z), coll, r=0.04))
            L.box(f"{name}_fl{x}{z:.2f}", (0.08, 0.05, 0.36), SW.m("laden_gruen", "#4E8A5A", 0.6), root,
                  (x - 0.22, -d / 2 - 0.035, z), coll)
    SW.rbox(f"{name}_tuer", (0.36, 0.06, 0.6), SW.m("tuer", "holz_d", 0.6), root, (0, -d / 2 - 0.03, 0.3), coll, r=0.05)
    return SW.P(root=root, m_fenster=m_f, wetter=lambda T, S, f0, f1: _abend(T, S, m_f, f0, f1))


def _abend(T, S, m_f, f0, f1):
    tag, nacht = L.srgb("#5A7FB0"), L.srgb("#FFD27A")
    T.set(m_f, "diffuse_color", lambda f: tuple(tag[i] + (nacht[i] - tag[i]) * max(S.wetter_an("abend", f), S.wetter_an("nacht", f))
                                                for i in range(3)) + (1,), f0, f1)
