"""Spielbrett: Gelaende der Spielstadt mit Raster, Wegen, Strassen, Fluss mit Bruecke, Pflaster und Pfuetzen.
Plan nach dem Set 'stadtkarte' (x * 3, y * 7). Zustaende: trocken, nass (Pfuetzen wachsen bei Regen, Ringe)."""
import math
import random

from mathutils import Vector

import look as L
import spielwelt as SW

INFO = {"name": "spielbrett", "groesse": [24, 48, 0.6], "anker": "mitte_oben", "zustaende": ["trocken", "nass"],
        "beschreibung": "Gelaende mit Raster (1 Kachel = 1 m), Strassen, Fluss, Bruecke, Marktpflaster, Pfuetzen"}
FLUSS = [(-0.5, -2.7), (-0.32, -1.6), (-0.62, -0.5), (-0.45, 0.6), (-0.72, 1.6), (-0.55, 2.7)]
STRASSE_OW_Y = -0.25
STRASSE_NS_X = 0.35


def _s(x, y):
    return (x * SW.STADT_X, y * SW.STADT_Y)


def _band(name, a, b, breite, mat, parent, coll, z=0.0, dicke=0.04):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = L.box(name, (breite, d.length + breite * 0.3, dicke), mat, parent, ((a.x + b.x) / 2, (a.y + b.y) / 2, z), coll)
    o.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
    return o


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    W_, D_ = 22.0, 46.0
    SW.rbox(f"{name}_platte", (W_, D_, 0.5), SW.m("gras", "gras", 0.8), root, (0, 0, -0.25), coll, r=0.4, seg=3)
    SW.rbox(f"{name}_rand", (W_ + 0.3, D_ + 0.3, 0.6), SW.m("erde", "erde", 0.8), root, (0, 0, -0.42), coll, r=0.3)
    m_l = SW.m("raster", "#7CB85C", 0.8)
    for x in range(-10, 11, 2):
        L.box(f"{name}_rx{x}", (0.03, D_ - 0.6, 0.005), m_l, root, (x, 0, 0.003), coll)
    for y in range(-22, 23, 2):
        L.box(f"{name}_ry{y}", (W_ - 0.6, 0.03, 0.005), m_l, root, (0, y, 0.003), coll)
    # Fluss (gleicher Verlauf wie die Stadtkarte) mit Ufer und Wellen
    pts = [Vector(_s(*p)) for p in FLUSS]
    pts = [pts[0] + Vector((0, -4))] + pts + [pts[-1] + Vector((0, 4))]
    m_w = SW.m("wasser", "wasser", 0.25)
    m_u = SW.m("ufer", "#E9D3A0", 0.8)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        _band(f"{name}_ufer{i}", a, b, 2.4, m_u, root, coll, 0.01, 0.03)
        _band(f"{name}_fluss{i}", a, b, 1.8, m_w, root, coll, 0.025, 0.03)
    wellen = []
    rnd = random.Random(2)
    for k in range(14):
        a = pts[1 + k % (len(pts) - 3)]
        w = L.box(f"{name}_welle{k}", (0.5, 0.06, 0.01), SW.m("welle", "#BFE6FA", 0.3), root,
                  (a.x + rnd.uniform(-0.4, 0.4), a.y + rnd.uniform(-2, 2), 0.045), coll)
        wellen.append(w)
    # Strassen und Wege
    m_s = SW.m("strasse", "strasse", 0.7)
    m_mark = SW.m("markierung", "weiss", 0.6)
    y_ow = _s(0, STRASSE_OW_Y)[1]
    x_ns = _s(STRASSE_NS_X, 0)[0]
    _band(f"{name}_ow", (-11, y_ow), (11, y_ow), 1.4, m_s, root, coll, 0.02)
    _band(f"{name}_ns", (x_ns, -11.5), (x_ns, 17), 1.2, m_s, root, coll, 0.021)
    _band(f"{name}_nb", (x_ns, 6.0), (10.5, 6.0), 0.9, m_s, root, coll, 0.022)
    _band(f"{name}_nb2", (x_ns, 12.0), (8.5, 12.0), 0.9, m_s, root, coll, 0.022)
    for k in range(-10, 11):
        L.box(f"{name}_mk{k}", (0.5, 0.08, 0.005), m_mark, root, (k + 0.25, y_ow, 0.045), coll)
    m_weg = SW.m("weg", "weg", 0.8)
    _band(f"{name}_wegalt", (-4.5, y_ow), (-4.5, 3.5), 0.9, m_weg, root, coll, 0.015)
    _band(f"{name}_wegkalle", (-6.7, y_ow), (-6.7, -10.5), 0.8, m_weg, root, coll, 0.015)
    _band(f"{name}_wegkalle2", (-6.7, -10.5), (-3.6, -10.5), 0.8, m_weg, root, coll, 0.0155)
    _band(f"{name}_wegbhf", (x_ns, -6.0), (8.5, -6.0), 0.8, m_weg, root, coll, 0.016)
    # Bruecke
    br = L.empty(f"{name}_bruecke", root, (_s(-0.55, 0)[0], y_ow, 0), coll)
    SW.rbox(f"{name}_br_deck", (3.2, 1.6, 0.18), SW.m("bruecke", "holz", 0.6), br, (0, 0, 0.16), coll, r=0.06)
    for sy in (-1, 1):
        SW.rbox(f"{name}_br_gel{sy}", (3.2, 0.12, 0.22), SW.m("holz_d", "holz_d", 0.6), br, (0, sy * 0.75, 0.36), coll, r=0.04)
    # Pfuetzen (wachsen bei Regen) mit Ringen
    pf = []
    for k, (x, y) in enumerate([(-3.5, -1.0), (2.5, -1.2), (-5.5, 1.8), (1.8, 4.0), (-4.2, -6.0), (4.5, -6.8), (0.6, 9.5)]):
        o = L.cyl(f"{name}_pfuetze{k}", 0.45, 0.01, 16, SW.m("pfuetze", "#8FB8D8", 0.15), root, (x, y, 0.05), coll)
        o.scale = (0, 0, 0)
        ring = L.torus(f"{name}_ring{k}", 0.2, 0.012, 16, 4, SW.m("ring", "#D8ECFA", 0.2), root, (x, y, 0.06), coll)
        ring.scale = (0, 0, 0)
        pf.append((o, ring))
    return SW.P(root=root, wellen=wellen, pfuetzen=pf, y_ow=y_ow, x_ns=x_ns, wetter=lambda T, S, f0, f1: _wetter(T, S, pf,
                                                                                                                    wellen, f0, f1))


def _wetter(T, S, pf, wellen, f0, f1):
    for k, w in enumerate(wellen):
        x0, y0 = w.location.x, w.location.y
        T.set(w, "location", lambda f, x0=x0, y0=y0, k=k: (x0 + 0.15 * math.sin(f * 0.06 + k), y0 + ((f * 0.02 + k) % 1.5) - 0.75,
                                                         0.045), f0, f1)
    for k, (o, ring) in enumerate(pf):
        T.set(o, "scale", lambda f, k=k: ((1.0 + 0.3 * (k % 3)) * min(1.0, S.wetter_an("regen", f) * 1.2),) * 2 + (1,), f0, f1)
        T.set(ring, "scale", lambda f, k=k: ((0.3 + ((f * 0.04 + k * 0.37) % 1.0) * 1.6) * (S.wetter_an("regen", f) > 0.3),) * 2 + (1,),
              f0, f1)
