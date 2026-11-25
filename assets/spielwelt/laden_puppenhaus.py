"""Kalles Laden als Puppenhaus (Dach und Vorderwand weg, schraeg von oben hinein): Holzboden mit Raster, Rueck- und
Seitenwaende (angeschnitten), Trennwand mit Durchgang zur Backstube, Eingangstuer mit Gloeckchen (links), Ladenschild in
Brezelform, Fenster, Lampen, Buero-Eck hinten rechts. Zustaende: tag, abend (Lampen an), tuer_auf (Gloeckchen schwingt)."""
import math

import look as L
import spielwelt as SW
import _zustand as Z

INFO = {"name": "laden_puppenhaus", "groesse": [8.0, 7.0, 3.2], "anker": "mitte_unten", "zustaende": ["tag", "abend", "tuer_auf"],
        "beschreibung": "Puppenhaus-Ansicht: Verkaufsraum vorn, Backstube hinten, Buero-Eck"}


def bauen(coll, name, breite=8.0, tiefe=7.0, filiale=False, **kw):
    import kalles_laden as KL
    root = L.empty(name, coll=coll)
    B, D = breite, tiefe
    SW.rbox(f"{name}_sockel", (B + 0.6, D + 0.6, 0.4), SW.m("erde", "erde", 0.8), root, (0, 0, -0.2), coll, r=0.15)
    L.box(f"{name}_boden", (B, D, 0.06), SW.m("dielen", "#D9A46A", 0.7), root, (0, 0, 0.03), coll)
    for k in range(int(B) + 1):
        L.box(f"{name}_fuge{k}", (0.02, D, 0.005), SW.m("fuge", "#B88450", 0.7), root, (-B / 2 + k, 0, 0.065), coll)
    L.box(f"{name}_fliesen", (B, D * 0.42, 0.065), SW.m("fliesen_bs", "#E8DCC6", 0.7), root, (0, D * 0.29, 0.035), coll)
    wand = SW.m("ladenwand", "#F4E3C3", 0.7)
    SW.rbox(f"{name}_rueck", (B, 0.25, 2.8), wand, root, (0, D / 2, 1.4), coll, r=0.06)
    SW.rbox(f"{name}_links", (0.25, D, 2.8), wand, root, (-B / 2, 0, 1.4), coll, r=0.06)
    SW.rbox(f"{name}_rechts", (0.25, D, 1.0), wand, root, (B / 2, 0, 0.5), coll, r=0.06)
    SW.rbox(f"{name}_trenn_l", (B * 0.36, 0.2, 1.1), wand, root, (-B * 0.32, D * 0.08, 0.55), coll, r=0.05)
    SW.rbox(f"{name}_trenn_r", (B * 0.36, 0.2, 1.1), wand, root, (B * 0.32, D * 0.08, 0.55), coll, r=0.05)
    L.box(f"{name}_sockelleiste", (B, 0.27, 0.15), SW.m("holz_d", "holz_d", 0.6), root, (0, D / 2 - 0.02, 0.08), coll)
    for x in (-B * 0.25, B * 0.25):
        SW.rbox(f"{name}_fenster{x}", (1.3, 0.28, 0.9), SW.m("fenster_hell", "#BFE3F7", 0.3), root, (x, D / 2, 1.8), coll, r=0.06)
    # Eingangstuer links mit Gloeckchen, Schild aussen
    tuer = L.empty(f"{name}_tuer", root, (-B / 2, -D * 0.25, 0), coll)
    SW.rbox(f"{name}_tuerblatt", (0.3, 1.0, 2.0), SW.m("tuer_rot", "rot", 0.6), tuer, (0, 0, 1.0), coll, r=0.06)
    gl = L.empty(f"{name}_gloeckchen", root, (-B / 2 + 0.3, -D * 0.25, 2.25), coll)
    L.cyl(f"{name}_glk", 0.12, 0.16, 10, SW.m("gold", "gold", 0.4), gl, (0, 0, -0.1), coll, r2=0.04)
    KL.brezel_schild(coll, f"{name}_schild", root, (-B / 2 - 0.35, -D * 0.25, 2.6), 0.9)
    # Lampen
    m_l = L.unique_mat(SW.m("lampe", "#F2E2B8", 0.3), f"sw_licht_lampe_{name}")
    for x in (-B * 0.25, B * 0.25):
        L.cyl(f"{name}_lampe{x}", 0.3, 0.2, 12, m_l, root, (x, -D * 0.15, 2.6), coll, r2=0.1)
        L.cyl(f"{name}_kabel{x}", 0.015, 0.6, 6, SW.m("dunkel", "dunkel", 0.5), root, (x, -D * 0.15, 3.0), coll)
    # Kassentisch rechts neben der Theke, Buero-Eck vorn rechts (kleiner Tisch fuer den Laptop)
    SW.rbox(f"{name}_kt", (1.0, 0.9, 1.0), SW.m("theke_holz", "holz", 0.6), root, (B * 0.25, -D * 0.12, 0.5), coll, r=0.06)
    bx, by = B / 2 - 0.9, -D / 2 + 0.8
    SW.rbox(f"{name}_bt", (1.2, 0.8, 0.08), SW.m("holz", "holz", 0.6), root, (bx, by, 0.75), coll, r=0.03)
    for dx in (-0.5, 0.5):
        for dy in (-0.3, 0.3):
            L.box(f"{name}_bb{dx}{dy}", (0.06, 0.06, 0.72), SW.m("holz_d", "holz_d", 0.6), root, (bx + dx, by + dy, 0.36), coll)
    if filiale:
        uhr = L.empty(f"{name}_bhfuhr", root, (-B / 2 - 0.15, -D * 0.25, 2.3), coll)
        uhr.rotation_euler = (0, 0, -math.pi / 2)
        L.cyl(f"{name}_ub", 0.25, 0.06, 20, SW.m("weiss", "weiss", 0.5), uhr, (0, 0, 0), coll, axis="Y")
    return SW.P(root=root, tuer=tuer, gloeckchen=gl, m_lampe=m_l, platz={
        "theke": (-B * 0.075, -D * 0.12), "kasse": (B * 0.25, -D * 0.12, 1.0), "ofen": (-B * 0.31, D * 0.34),
        "knettisch": (-B * 0.075, D * 0.23), "blechwagen": (B * 0.11, D * 0.4), "lager": (B * 0.33, D * 0.4),
        "tonne": (B * 0.42, -D * 0.03), "buero": (bx, by, 0.79), "eingang": (-B / 2 + 0.5, -D * 0.25)})


def gloeckchen(T, p, f_auf_liste, f0, f1):
    """Tuer schwingt auf, Gloeckchen bimmelt bei jedem Frame aus f_auf_liste."""
    def tr(f):
        a = max([math.exp(-(f - x) / 8) * math.sin((f - x) * 0.6) for x in f_auf_liste if f >= x] + [0.0])
        return (a * 0.5, 0, 0)
    T.set(p.gloeckchen, "rotation_euler", tr, f0, f1)
    T.set(p.tuer, "rotation_euler", lambda f: (0, 0, -1.2 * max([max(0.0, 1 - abs(f - x - 10) / 12) for x in f_auf_liste] + [0.0])),
          f0, f1)
