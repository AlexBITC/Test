"""Requisiten fuer 'Wo kommt Filiale Nr. 2 hin?' (folge-09-filiale).

Gleicher Low-Poly-Stil wie engine/props.py (Vorderseite -Y). Leuchten fuer Workbench ueber diffuse_color.
Datenebenen der Stadtkarte (Pins, Konkurrenz-Marker, Info-Karten, Personen-Lichtpunkte, Heatmap) liegen in
engine/stadtkarte.py (Engine 2.3) und werden hier nur benutzt. Wiederverwendet: brezel (engine/props.pastry),
brezelblech (assets/props/viral.py), laptop (engine/props.py).
"""
import math
import random

import bpy
from mathutils import Vector

import look as L
import props as PR
from anim import ease_in_out, ease_out_back, pop, unpop, clamp01

FPS = 30
P = PR.P
GOLD = "#F2B45A"
TURQ = "#2EE6D6"
NAVY = "#141228"
WEISS = "#F4F2EC"


def _text(name, s, size, mat, parent, loc, coll, rot=(math.pi / 2, 0, 0), extrude=0.003):
    return L.text(name, s, size, mat, parent, loc, coll, extrude=extrude, rot=rot, font=L.font())


# ------------------------------------------------------------------ Stadtplan-Rolle (rollt auf und zusammen)
def stadtplan_rolle(coll, name, laenge=0.9, breite=0.5):
    """Stadtplan: Blatt (Pivot an der linken Kante) und Rolle am rechten Ende. rollen(T, sp, fn) mit fn(f) 0..1
    (0 = zusammengerollt, 1 = ganz offen). Aufdruck: Fluss, Strassen, drei Viertel, roter Brezel-Punkt, 'STADTPLAN'."""
    root = L.empty(name, coll=coll)
    blatt = L.empty(f"{name}_blatt", root, (0, 0, 0), coll)
    papier = L.mat("fp_papier", "#F3EBD6", 0.7)
    L.box(f"{name}_p", (laenge, breite, 0.004), papier, blatt, (laenge / 2, 0, 0.002), coll)
    gr = L.mat("fp_gruen", "#9CCB7A", 0.7)
    for k, (x, y, w, d) in enumerate([(0.18, 0.05, 0.22, 0.3), (0.62, 0.12, 0.26, 0.2), (0.6, -0.14, 0.2, 0.12)]):
        L.box(f"{name}_g{k}", (w * laenge / 0.9, d, 0.002), gr, blatt, (x * laenge / 0.9, y, 0.0045), coll)
    L.box(f"{name}_fluss", (0.05, breite * 0.95, 0.002), L.mat("fp_fluss", "#5AA8E0", 0.5), blatt,
          (laenge * 0.4, 0, 0.005), coll).rotation_euler = (0, 0, 0.18)
    st = L.mat("fp_strasse", "#B9B4A6", 0.7)
    L.box(f"{name}_s1", (laenge * 0.96, 0.018, 0.002), st, blatt, (laenge / 2, -0.03, 0.0055), coll)
    L.box(f"{name}_s2", (0.018, breite * 0.9, 0.002), st, blatt, (laenge * 0.68, 0, 0.0055), coll)
    L.cyl(f"{name}_pin", 0.022, 0.004, 12, L.mat("fp_rot", "#E5484D", 0.5), blatt, (laenge * 0.16, -0.14, 0.007), coll)
    _text(f"{name}_t", "STADTPLAN", 0.05, L.mat("fp_ink", NAVY, 0.5), blatt, (laenge * 0.5, breite * 0.36, 0.008), coll,
          rot=(0, 0, 0), extrude=0.001)
    rolle = L.empty(f"{name}_rolle", root, (laenge, 0, 0.03), coll)
    L.cyl(f"{name}_r", 0.03, breite, 14, papier, rolle, (0, 0, 0), coll, axis="Y")
    L.cyl(f"{name}_rk", 0.031, breite * 0.98, 14, L.mat("fp_rand", "#D9C9A6", 0.7), rolle, (0, 0, 0), coll, axis="Y",
          cap=False)
    L.torus(f"{name}_band", 0.033, 0.006, 14, 4, L.mat("fp_rot", "#E5484D", 0.5), rolle, (0, 0, 0), coll, axis="Y")
    return P(root=root, blatt=blatt, rolle=rolle, laenge=laenge)


def rollen(T, sp, fn, f0, f1):
    """fn(f) 0..1: Blatt skaliert in x, Rolle wandert mit und dreht sich."""
    T.set(sp.blatt, "scale", lambda f: (max(0.02, fn(f)), 1, 1), f0, f1)
    T.set(sp.rolle, "location", lambda f: (sp.laenge * max(0.02, fn(f)), 0, 0.03), f0, f1)
    T.set(sp.rolle, "rotation_euler", lambda f: (0, fn(f) * sp.laenge / 0.03, 0), f0, f1)


# ------------------------------------------------------------------ Lichtwirbel-Portal
def lichtwirbel_portal(coll, name, n=7):
    """Spiral-Wirbel aus leuchtenden Ringen und Funken (tuerkis/violett), steigt nach oben."""
    root = L.empty(name, coll=coll)
    ringe, funken = [], []
    for k in range(n):
        col = TURQ if k % 2 == 0 else "#8C7BFF"
        r = L.torus(f"{name}_ring{k}", 0.12 + 0.05 * k, 0.012, 24, 4, L.mat(f"fp_wirbel{k % 2}", col, 0.3, emit=col,
                                                                              strength=3.0), root, (0, 0, 0.12 * k), coll)
        ringe.append(r)
    for k in range(18):
        funken.append(L.ico(f"{name}_f{k}", 0.018, 0, (1, 1, 1), L.mat("fp_funke", "#E9FFFD", 0.3, emit="#E9FFFD",
                                                                          strength=4.0), root, (0, 0, 0), coll))
    root.scale = (0, 0, 0)
    return P(root=root, ringe=ringe, funken=funken)


def wirbel(T, pw, f0, f1, hoehe=1.6):
    """Wirbel waechst auf (f0), dreht und steigt, verschwindet zum Ende (f1)."""
    T.set(pw.root, "scale", lambda f: ((pop(f, f0, 8) * (1 - clamp01((f - (f1 - 8)) / 8))),) * 3, f0 - 1, f1 + 1)
    for k, r in enumerate(pw.ringe):
        T.set(r, "rotation_euler", lambda f, k=k: (0.35 * math.sin(f * 0.2 + k), 0.35 * math.cos(f * 0.2 + k), f * 0.3), f0, f1)
        T.set(r, "location", lambda f, k=k: (0.04 * math.sin(f * 0.4 + k), 0.04 * math.cos(f * 0.4 + k),
                                            0.12 * k * (1 + 1.5 * clamp01((f - f0) / max(1, f1 - f0)))), f0, f1)
    rnd = random.Random(7)
    for k, fk in enumerate(pw.funken):
        ph, sp = rnd.uniform(0, 6.28), rnd.uniform(0.04, 0.08)

        def pos(f, ph=ph, sp=sp):
            t = (f - f0) * sp
            z = (t * 0.6) % hoehe
            r = 0.1 + 0.35 * z / hoehe
            return (r * math.cos(ph + t * 3), r * math.sin(ph + t * 3), z)
        T.set(fk, "location", pos, f0, f1)


# ------------------------------------------------------------------ Schwebender Zaehler
def zaehler_schwebend(coll, name, breite=1.3):
    """Dunkle Tafel mit leuchtendem Rand fuer einen Zaehler; die Ziffern kommen gestochen scharf als Overlay
    (W.labels, Anker S.objs['anker']). Kleine Aufschrift 'PASSANTEN / MORGEN'."""
    root = L.empty(name, coll=coll)
    L.box(f"{name}_rand", (breite + 0.05, 0.03, 0.47), L.mat("fp_zrand", GOLD, 0.4, emit=GOLD, strength=2.0), root,
          (0, 0.008, 0), coll, bevel=0.05, seg=2)
    L.box(f"{name}_bg", (breite, 0.035, 0.42), L.mat("fp_zbg", NAVY, 0.5), root, (0, 0, 0), coll, bevel=0.04, seg=2)
    _text(f"{name}_t", "PASSANTEN / MORGEN", 0.075, L.mat("fp_zink", WEISS, 0.5), root, (0, -0.02, -0.15), coll)
    anker = L.empty(f"{name}_anker", root, (0, -0.03, 0.05), coll)
    root.scale = (0, 0, 0)
    return P(root=root, anker=anker)


# ------------------------------------------------------------------ Punktraster 100 (3 golden)
def punktraster_100(coll, name, golden=(23, 56, 87), text=False):
    """10 x 10 Punkte auf dunkler Tafel, drei golden. Optional Aufschrift '3 von 100' (text=True)."""
    root = L.empty(name, coll=coll)
    tafel = L.empty(f"{name}_tafel", root, (0, 0, 0), coll)
    L.box(f"{name}_bg", (1.2, 0.02, 1.38), L.mat("fp_rbg", NAVY, 0.5), tafel, (0, 0.01, -0.05), coll, bevel=0.05, seg=2)
    L.box(f"{name}_rand", (1.25, 0.015, 1.43), L.mat("fp_rrand", TURQ, 0.4, emit=TURQ, strength=1.5), tafel,
          (0, 0.02, -0.05), coll, bevel=0.05, seg=2)
    m_w = L.mat("fp_rweiss", "#C9CBE0", 0.5)
    m_g = L.mat("fp_rgold", GOLD, 0.3, emit=GOLD, strength=3.0)
    punkte, gold = [], []
    for k in range(100):
        x, z = -0.45 + (k % 10) * 0.1, 0.55 - (k // 10) * 0.1
        g = k in golden
        o = L.cyl(f"{name}_p{k}", 0.033 if not g else 0.042, 0.02, 12, m_g if g else m_w, tafel, (x, -0.005, z), coll,
                  axis="Y")
        (gold if g else punkte).append(o)
    if text:
        _text(f"{name}_t", "3 von 100", 0.17, L.mat("fp_rink", GOLD, 0.4, emit=GOLD, strength=2.0), tafel, (0, -0.02, -0.6),
              coll)
    root.scale = (0, 0, 0)
    return P(root=root, tafel=tafel, gold=gold, punkte=punkte)


# ------------------------------------------------------------------ Goldene Kundenschlange
def kundenschlange_gold(T, S, coll, name, start_fn, ziel_pfad, n, f0, f1, r=0.03):
    """n goldene Punkte fliegen von start_fn(k, f0) (Weltposition) zusammen und reihen sich entlang ziel_pfad
    (lokale (x, y)-Punkte der Stadtkarte, Ende = Ladentuer) ein; danach ruecken sie langsam nach."""
    mat = L.mat("fp_schlange", GOLD, 0.3, emit=GOLD, strength=3.5)
    segs = [(Vector(ziel_pfad[i]), Vector(ziel_pfad[i + 1])) for i in range(len(ziel_pfad) - 1)]
    total = sum((b - a).length for a, b in segs)

    def auf_pfad(d):
        d = max(0.0, min(total, d))
        for a, b in segs:
            ln = (b - a).length
            if d <= ln:
                return a + (b - a) * (d / max(1e-6, ln))
            d -= ln
        return segs[-1][1]
    out = []
    for k in range(n):
        o = L.ico(f"{name}{k}", r, 1, (1, 1, 1), mat, None, (0, 0, 0), coll)
        start = Vector(start_fn(k, f0))
        fa = f0 + k * 0.8

        def pos(f, k=k, start=start, fa=fa):
            slot = total - 0.06 * (k + 1) + 0.04 * clamp01((f - fa - 30) / 60)
            q = auf_pfad(slot)
            ziel = S.welt(q.x, q.y, 0.04 + 0.01 * math.sin(f * 0.3 + k), f)
            t = ease_in_out(clamp01((f - fa) / 22))
            mid = start.lerp(ziel, 0.5) + Vector((0, 0, 0.35))
            a = start.lerp(mid, t)
            b = mid.lerp(ziel, t)
            return a.lerp(b, t)
        T.set(o, "location", lambda f, pos=pos: tuple(pos(f)), f0, f1)
        out.append(o)
    return out


# ------------------------------------------------------------------ Schild 'FILIALE 2?'
def schild_filiale(coll, name):
    """Klappschild (Pivot unten), Aufschrift 'FILIALE 2?'; aufklappen(T, sch, f)."""
    root = L.empty(name, coll=coll)
    klappe = L.empty(f"{name}_klappe", root, (0, 0, 0), coll)
    L.box(f"{name}_rand", (0.62, 0.025, 0.22), L.mat("fp_srand", "#3DDC84", 0.4, emit="#3DDC84", strength=2.0), klappe,
          (0, 0.006, 0.11), coll, bevel=0.03, seg=2)
    L.box(f"{name}_bg", (0.58, 0.03, 0.18), L.mat("fp_sbg", WEISS, 0.5), klappe, (0, 0, 0.11), coll, bevel=0.02, seg=2)
    _text(f"{name}_t", "FILIALE 2?", 0.11, L.mat("fp_sink", NAVY, 0.5), klappe, (0, -0.018, 0.07), coll)
    for sx in (-0.22, 0.22):
        L.box(f"{name}_st{sx}", (0.02, 0.02, 0.12), L.mat("fp_metall", "#7E8299", 0.4), root, (sx, 0.02, -0.06), coll)
    root.scale = (0, 0, 0)
    return P(root=root, klappe=klappe)


def aufklappen(T, sch, f_in, s=1.0, f1=None):
    T.set(sch.root, "scale", lambda f: (s,) * 3 if f >= f_in else (0,) * 3, f_in - 1, f_in + 1)
    T.set(sch.klappe, "rotation_euler", lambda f: (-math.pi / 2 * (1 - ease_out_back(clamp01((f - f_in) / 10), 2.5)), 0, 0),
          f_in - 1, f_in + 12)


# ------------------------------------------------------------------ Kiosk-Hologramm
def kiosk_hologramm(coll, name):
    """Halbtransparenter tuerkiser Mini-Kiosk mit Schild 'KIOSK', Fenster (Broetchen schaut heraus) und Scanlinien."""
    root = L.empty(name, coll=coll)
    holo = L.mat("fp_holo", "#2EE6D6", 0.3, alpha=0.45)
    kante = L.mat("fp_holo_kante", "#9FFFF7", 0.3, emit="#9FFFF7", strength=3.0)
    L.box(f"{name}_b", (0.36, 0.26, 0.28), holo, root, (0, 0, 0.14), coll)
    L.box(f"{name}_d", (0.42, 0.32, 0.03), kante, root, (0, 0, 0.295), coll)
    L.box(f"{name}_boden", (0.42, 0.32, 0.01), kante, root, (0, 0, 0.0), coll)
    L.box(f"{name}_fen", (0.22, 0.01, 0.1), L.mat("fp_holo_fen", "#0E3A44", 0.4), root, (0, -0.132, 0.16), coll)
    L.box(f"{name}_sbg", (0.3, 0.01, 0.075), L.mat("fp_holo_s", NAVY, 0.5), root, (0, -0.14, 0.355), coll)
    _text(f"{name}_t", "KIOSK", 0.06, kante, root, (0, -0.147, 0.337), coll, extrude=0.002)
    scan = []
    for k in range(5):
        scan.append(L.box(f"{name}_scan{k}", (0.37, 0.27, 0.004), kante, root, (0, 0, 0.05 + 0.05 * k), coll))
    root.scale = (0, 0, 0)
    return P(root=root, scan=scan)


def holo_an(T, kh, f_in, f_out, s=1.0):
    T.set(kh.root, "scale", lambda f: (s * pop(f, f_in, 8) * (unpop(f, f_out, 6) if f > f_out else 1)
                                       * (1.0 if (f - f_in) % 17 != 3 else 0.92),) * 3, f_in - 1, f_out + 7)
    for k, sl in enumerate(kh.scan):
        T.set(sl, "location", lambda f, k=k: (0, 0, 0.02 + ((f * 0.008 + k * 0.06) % 0.28)), f_in, f_out + 7)


# ------------------------------------------------------------------ Broetchen in Plastikfolie
def broetchen_plastik(coll, name):
    """Blasses, plattgedruecktes Aufback-Broetchen in Plastikfolie mit Etikett 'AUFGEBACKEN'."""
    root = L.empty(name, coll=coll)
    L.sphere(f"{name}_m", 0.1, 10, 6, (1.25, 1.0, 0.42), L.mat("fp_blass", "#E9D9B4", 0.75), root, (0, 0, 0.0), coll)
    L.box(f"{name}_cut", (0.12, 0.012, 0.01), L.mat("fp_blass_cut", "#F3E8CC", 0.7), root, (0, -0.02, 0.04), coll)
    L.box(f"{name}_folie", (0.28, 0.23, 0.11), L.mat("fp_folie", "#DDEBFA", 0.15, alpha=0.35), root, (0, 0, 0.0), coll)
    for sx in (-1, 1):
        L.box(f"{name}_naht{sx}", (0.03, 0.235, 0.004), L.mat("fp_naht", "#C9DDF2", 0.3, alpha=0.6), root,
              (sx * 0.15, 0, 0.0), coll)
    L.box(f"{name}_etikett", (0.16, 0.004, 0.05), L.mat("fp_etikett", "#FFE14D", 0.5), root, (0, -0.118, 0.0), coll)
    _text(f"{name}_et", "AUFGEBACKEN", 0.02, L.mat("fp_etink", NAVY, 0.5), root, (0, -0.122, -0.007), coll, extrude=0.001)
    return P(root=root)


# ------------------------------------------------------------------ Glaenzende Brezel
def brezel_glaenzend(coll, name, s=1.6):
    """Frische Brezel (engine/props.pastry) mit Glanzlichtern und glitzernden Salzkoernern."""
    root = L.empty(name, coll=coll)
    PR.pastry(coll, f"{name}_b", "brezel", root, (0, 0, -0.07 * s), s)
    glanz = L.mat("fp_glanz", "#FFE3B8", 0.2, emit="#FFF1D8", strength=2.5)
    for k, (x, z) in enumerate([(-0.09, 0.07), (0.06, 0.08), (0.0, -0.02)]):
        L.sphere(f"{name}_gl{k}", 0.012 * s, 8, 4, (2.2, 0.6, 0.8), glanz, root, (x * s, -0.03 * s, z * s), coll)
    salz = []
    m_s = L.mat("fp_salz", "#FFFFFF", 0.2, emit="#FFFFFF", strength=4.0)
    rnd = random.Random(9)
    for k in range(10):
        salz.append(L.ico(f"{name}_sz{k}", 0.008 * s, 0, (1, 1, 1), m_s, root,
                          (rnd.uniform(-0.14, 0.14) * s, -0.035 * s, rnd.uniform(-0.04, 0.09) * s), coll))
    return P(root=root, salz=salz)


def glitzern(T, bz, f0, f1):
    for k, o in enumerate(bz.salz):
        T.set(o, "scale", lambda f, k=k: ((0.6 + 1.2 * max(0.0, math.sin(f * 0.45 + k * 2.1)) ** 4),) * 3, f0, f1)


# ------------------------------------------------------------------ Bildschirm-Tafel in der Stadt
def screen_tafel(coll, name, breite=1.6, aspect=1280 / 720):
    """Schwebende Tafel, auf der die Bildschirm-Bildfolge (screen_display, assets/screens/filiale.py) laeuft."""
    root = L.empty(name, coll=coll)
    h = breite / aspect
    L.box(f"{name}_rand", (breite + 0.06, 0.03, h + 0.06), L.mat("fp_trand", TURQ, 0.4, emit=TURQ, strength=2.0), root,
          (0, 0.01, 0), coll, bevel=0.03, seg=2)
    disp = L.box(f"{name}_disp", (breite, 0.02, h), L.mat("fp_tbg", NAVY, 0.5), root, (0, -0.01, 0), coll)
    m = bpy.data.materials.get("screen_display")
    if m is not None:
        me = disp.data
        me.materials.clear()
        me.materials.append(m)
        uv = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv = (0.5 + v.x / breite, 0.5 + v.z / h)
    root.scale = (0, 0, 0)
    return P(root=root, disp=disp, h=h)
