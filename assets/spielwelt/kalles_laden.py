"""Kalles Laden (Aussenansicht in der Altstadt): rote Markise, Ladenschild in Brezelform, Schaufenster mit Theke,
Mehlsaecke 'WEIZEN 550' vor der Tuer. Zustaende: tag, abend (Schaufenster leuchtet), geschlossen."""
import math

import look as L
import spielwelt as SW

INFO = {"name": "kalles_laden", "groesse": [2.6, 2.2, 3.4], "anker": "mitte_unten", "zustaende": ["tag", "abend", "geschlossen"],
        "beschreibung": "Kalles Baeckerei, Ladenschild = Brezel, rote Markise"}


def brezel_schild(coll, name, parent, loc, s=1.0, farbe="rot"):
    """Ladenschild in Brezelform (auch fuer Filiale 2 und den Puppenhaus-Laden)."""
    o = L.empty(name, parent, loc, coll)
    o.scale = (s, s, s)
    m = SW.m(f"brezelschild_{farbe}", farbe, 0.45)
    t = L.torus(f"{name}_bauch", 0.42, 0.09, 18, 6, m, o, (0, 0, -0.05), coll, axis="Y")
    t.scale = (1.15, 1, 0.75)
    for sx in (-1, 1):
        oh = L.torus(f"{name}_ohr{sx}", 0.22, 0.08, 14, 6, m, o, (sx * 0.19, 0, 0.17), coll, axis="Y")
        oh.rotation_euler = (0, sx * 0.5, 0)
    L.box(f"{name}_arm", (0.05, 0.05, 0.4), SW.m("holz_d", "holz_d", 0.6), o, (0, 0.05, 0.5), coll)
    return o


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    w, d, h = 2.4, 2.0, 1.9
    SW.rbox(f"{name}_b", (w, d, h), SW.m("kalle_wand", "creme", 0.7), root, (0, 0, h / 2), coll, r=0.1)
    L.poly_flat(f"{name}_dach", [(-w / 2 - 0.18, 0), (w / 2 + 0.18, 0), (0, 1.1)], d + 0.25, SW.m("kalle_dach", "dach2", 0.6),
                root, (0, 0, h), coll)
    for s_ in range(10):
        st = L.box(f"{name}_mk{s_}", (0.24, 0.7, 0.04), SW.m(f"kmk{s_ % 2}", ["rot", "weiss"][s_ % 2], 0.55), root,
                   (-1.08 + 0.24 * s_, -1.25, 1.35), coll)
        st.rotation_euler = (-0.42, 0, 0)
    m_sf = L.unique_mat(SW.m("schaufenster", "#9FD0EE", 0.3), f"sw_schaufenster_{name}")
    SW.rbox(f"{name}_sf", (1.2, 0.06, 0.8), m_sf, root, (-0.45, -d / 2 - 0.03, 0.75), coll, r=0.05)
    SW.rbox(f"{name}_tuer", (0.55, 0.06, 1.0), SW.m("tuer_rot", "rot", 0.6), root, (0.75, -d / 2 - 0.03, 0.5), coll, r=0.06)
    SW.rbox(f"{name}_tafel", (1.3, 0.06, 0.32), SW.m("schild_navy", "#1E2A44", 0.5), root, (0, -d / 2 - 0.04, 1.65), coll, r=0.05)
    SW.text(f"{name}_t", "KALLE", 0.24, SW.m("gold", "gold", 0.4), root, (0, -d / 2 - 0.08, 1.58), coll)
    brezel_schild(coll, f"{name}_brezel", root, (1.45, -0.6, 2.2), 0.8)
    for k in range(2):
        sack = SW.rbox(f"{name}_sack{k}", (0.42, 0.32, 0.55), SW.m("sack", "#E3CFA4", 0.8), root, (-1.4 + 0.45 * k, -1.35, 0.28),
                       coll, r=0.12)
        SW.text(f"{name}_sackt{k}", "WEIZEN", 0.07, SW.m("sack_ink", "#8A5A2E", 0.6), root, (-1.4 + 0.45 * k, -1.52, 0.34), coll)
        SW.text(f"{name}_sackn{k}", "550", 0.09, SW.m("sack_ink", "#8A5A2E", 0.6), root, (-1.4 + 0.45 * k, -1.52, 0.22), coll)
    return SW.P(root=root, m_sf=m_sf)
