"""Requisiten fuer 'Das Geheimnis in Kalles Haenden' (folge-10-brezel-geheimnis).

Gleicher Low-Poly-Stil wie engine/props.py (Vorderseite -Y). Leuchten fuer Workbench ueber diffuse_color.
Wiederverwendet: brezelblech und mini_kamera/rec_blink (assets/props/viral.py), wanduhr_backstube und uhr_stellen
(assets/props/nachtschicht.py), Mehlwolke (engine/props.burst 'puff'), Kundin (engine/props.customer),
Bewegungsbahn (engine/ar.bahn), AR-Brille (engine/lea.Lea.brille).
"""
import math
import random

from mathutils import Vector

import look as L
import props as PR
from anim import ease_in_out, ease_out, ease_out_back, pop, unpop, clamp01, window

FPS = 30
P = PR.P
GOLD = "#F2B45A"
TURQ = "#2EE6D6"
NAVY = "#141228"
TEIG = "#EBCB9C"
TEIG2 = "#E2BC88"
LAUGE = "#7A3E17"


def _text(name, s, size, mat, parent, loc, coll, rot=(math.pi / 2, 0, 0), extrude=0.003, align="CENTER"):
    return L.text(name, s, size, mat, parent, loc, coll, extrude=extrude, rot=rot, font=L.font(), align=align)


def _strang(name, pts, r_fn, mat, parent, coll, step=0.018):
    """Teig als Perlenkette aus Kugeln entlang einer Linie (Punkte in der XY-Ebene, z = Hoehe)."""
    out = []
    pts = [Vector(p) for p in pts]
    k = 0
    for a, b in zip(pts, pts[1:]):
        n = max(1, int((b - a).length / step))
        for j in range(n):
            t = j / n
            p = a.lerp(b, t)
            u = (k + j) / max(1, sum(max(1, int((bb - aa).length / step)) for aa, bb in zip(pts, pts[1:])))
            r = r_fn(u)
            out.append(L.sphere(f"{name}_{k + j}", r, 8, 5, (1, 1, 0.8), mat, parent, (p.x, p.y, p.z + r * 0.8), coll))
        k += n
    return out


def _brezel_pts(s=1.0, z=0.0):
    """Klassische Brezel (Draufsicht): Bauch unten, zwei Aermchen gekreuzt, Enden am Bauch."""
    pts = []
    for k in range(25):                                    # Bauch: Bogen von links ueber unten nach rechts
        a = math.pi * (0.95 + 1.1 * k / 24)
        pts.append((0.15 * math.cos(a) * s, 0.12 * math.sin(a) * s - 0.02 * s, z))
    # rechtes Aermchen hoch, Kreuzung, runter zum linken Bauch
    pts += [(0.15 * s, 0.03 * s, z), (0.08 * s, 0.1 * s, z), (0.0, 0.07 * s, z), (-0.05 * s, 0.0, z), (-0.1 * s, -0.08 * s, z)]
    return pts


def _brezel_pts_links(s=1.0, z=0.0):
    return [(-0.15 * s, 0.03 * s, z), (-0.08 * s, 0.1 * s, z), (0.0, 0.07 * s, z), (0.05 * s, 0.0, z), (0.1 * s, -0.08 * s, z)]


# ------------------------------------------------------------------ missglueckte Brezeln (9 Varianten)
VARIANTEN = ["knoten", "acht", "klumpen", "herz", "brille", "schlange", "spirale", "doppelknoten", "ohr"]


def brezel_missglueckt(coll, name, variante, s=1.0):
    """Missglueckte Brezel (roh): knoten, acht, klumpen, herz, brille (Brillengestell), schlange, spirale,
    doppelknoten, ohr (eine Seite riesig)."""
    root = L.empty(name, coll=coll)
    m = L.mat("bg_teig", TEIG, 0.75)
    r0 = 0.022 * s
    if variante == "klumpen":
        L.ico(f"{name}_k", 0.08 * s, 1, (1.2, 1.0, 0.55), m, root, (0, 0, 0.04 * s), coll)
        L.ico(f"{name}_k2", 0.045 * s, 1, (1, 1, 0.6), m, root, (0.07 * s, 0.03 * s, 0.05 * s), coll)
        _strang(f"{name}_arm", [(0.06 * s, -0.04 * s, 0), (0.16 * s, -0.09 * s, 0)], lambda u: r0 * 0.7, m, root, coll)
        return P(root=root)
    pts = []
    if variante == "knoten":
        for k in range(30):
            a = 2 * math.pi * k / 30
            pts.append((0.08 * s * math.cos(a) + 0.03 * s * math.cos(3 * a), 0.08 * s * math.sin(a) - 0.03 * s * math.sin(3 * a), 0))
        L.ico(f"{name}_knot", 0.04 * s, 1, (1, 1, 0.8), m, root, (0, 0, 0.03 * s), coll)
    elif variante == "acht":
        for k in range(41):
            a = 2 * math.pi * k / 40
            pts.append((0.14 * s * math.sin(a), 0.07 * s * math.sin(2 * a), 0))
    elif variante == "herz":
        for k in range(41):
            t = 2 * math.pi * k / 40
            pts.append((0.009 * s * 16 * math.sin(t) ** 3,
                        0.009 * s * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)), 0))
    elif variante == "brille":
        for cx in (-0.075, 0.075):
            ring = [(cx * s + 0.055 * s * math.cos(2 * math.pi * k / 20), 0.05 * s * math.sin(2 * math.pi * k / 20), 0)
                    for k in range(21)]
            _strang(f"{name}_r{cx}", ring, lambda u: r0 * 0.9, m, root, coll)
        _strang(f"{name}_steg", [(-0.02 * s, 0.01 * s, 0), (0.02 * s, 0.01 * s, 0)], lambda u: r0 * 0.8, m, root, coll)
        for sx in (-1, 1):
            _strang(f"{name}_b{sx}", [(sx * 0.13 * s, 0.0, 0), (sx * 0.2 * s, 0.06 * s, 0)], lambda u: r0 * 0.7, m, root, coll)
        return P(root=root)
    elif variante == "schlange":
        pts = [(-0.18 * s + 0.36 * s * k / 20, 0.03 * s * math.sin(k * 0.9), 0) for k in range(21)]
    elif variante == "spirale":
        pts = [(0.012 * s * k * math.cos(k * 0.45), 0.012 * s * k * math.sin(k * 0.45), 0) for k in range(1, 15)]
    elif variante == "doppelknoten":
        for cx in (-0.06, 0.06):
            ring = [(cx * s + 0.05 * s * math.cos(2 * math.pi * k / 16), 0.05 * s * math.sin(2 * math.pi * k / 16), 0)
                    for k in range(17)]
            _strang(f"{name}_d{cx}", ring, lambda u: r0, m, root, coll)
            L.ico(f"{name}_dk{cx}", 0.03 * s, 1, (1, 1, 0.8), m, root, (cx * s, 0, 0.03 * s), coll)
        return P(root=root)
    elif variante == "ohr":
        pts = _brezel_pts(s * 0.8)
        big = [(-0.09 * s + 0.11 * s * math.cos(2 * math.pi * k / 20), 0.05 * s + 0.11 * s * math.sin(2 * math.pi * k / 20), 0)
               for k in range(21)]
        _strang(f"{name}_ohr", big, lambda u: r0, m, root, coll)
    _strang(f"{name}_s", pts, lambda u: r0 * (1.0 + 0.25 * math.sin(u * 7)), m, root, coll)
    return P(root=root)


def reihe_missglueckt(coll, name, start, richtung=Vector((0.26, 0, 0)), s=1.0):
    """Die Reihe der neun missglueckten Brezeln (Running Gag), Rueckgabe: Liste P(root)."""
    out = []
    for k, v in enumerate(VARIANTEN):
        b = brezel_missglueckt(coll, f"{name}{k}", v, s)
        b.root.location = Vector(start) + richtung * k
        b.root.rotation_euler = (0, 0, random.Random(k).uniform(-0.4, 0.4))
        out.append(b)
    return out


# ------------------------------------------------------------------ perfekte Brezel (roh) und gebacken
def brezel_roh_perfekt(coll, name, s=1.0):
    """Lehrbuch-Brezel, roh: dicker Bauch, duenne Aermchen, sauber geschlungen."""
    root = L.empty(name, coll=coll)
    m = L.mat("bg_teig_perfekt", "#F0D3A6", 0.7)
    _strang(f"{name}_bauch", _brezel_pts(s)[:25], lambda u: 0.034 * s * (0.65 + 0.35 * math.sin(math.pi * u)), m, root, coll)
    _strang(f"{name}_ar", _brezel_pts(s)[25:], lambda u: 0.016 * s, m, root, coll)
    _strang(f"{name}_al", _brezel_pts_links(s), lambda u: 0.016 * s, m, root, coll)
    return P(root=root)


def brezel_gebacken(coll, name, s=1.0):
    """Gebackene Brezel: glaenzend braun (Lauge), Glanzlichter, Salzkoerner; aufgeplatzter Bauch hell."""
    root = L.empty(name, coll=coll)
    m = L.mat("bg_lauge", "#8A4519", 0.35)
    _strang(f"{name}_bauch", _brezel_pts(s)[:25], lambda u: 0.036 * s * (0.65 + 0.35 * math.sin(math.pi * u)), m, root, coll)
    _strang(f"{name}_ar", _brezel_pts(s)[25:], lambda u: 0.017 * s, m, root, coll)
    _strang(f"{name}_al", _brezel_pts_links(s), lambda u: 0.017 * s, m, root, coll)
    L.box(f"{name}_riss", (0.12 * s, 0.012 * s, 0.006 * s), L.mat("bg_riss", "#E8C28A", 0.6), root,
          (0, -0.13 * s, 0.05 * s), coll).rotation_euler = (0.4, 0, 0)
    glanz = L.mat("bg_glanz", "#FFE3B8", 0.2, emit="#FFF1D8", strength=2.5)
    for k, (x, y) in enumerate([(-0.1, -0.08), (0.08, -0.1), (0.0, 0.08)]):
        L.sphere(f"{name}_gl{k}", 0.01 * s, 6, 4, (2.0, 0.8, 0.5), glanz, root, (x * s, y * s, 0.065 * s), coll)
    salz = []
    m_s = L.mat("bg_salz", "#FFFFFF", 0.2, emit="#FFFFFF", strength=3.0)
    rnd = random.Random(5)
    for k in range(12):
        a = rnd.uniform(0.9, 2.05) * math.pi
        salz.append(L.ico(f"{name}_sz{k}", 0.007 * s, 0, (1, 1, 1), m_s, root,
                          (0.15 * s * math.cos(a), 0.12 * s * math.sin(a) - 0.02 * s, 0.065 * s), coll))
    return P(root=root, salz=salz)


def salz_glitzern(T, b, f0, f1):
    for k, o in enumerate(b.salz):
        T.set(o, "scale", lambda f, k=k: ((0.7 + 1.1 * max(0.0, math.sin(f * 0.4 + k * 2.3)) ** 4),) * 3, f0, f1)


# ------------------------------------------------------------------ Teigstrang (rollbar, dreht sich in der Luft)
def teigstrang(coll, name, n=16, laenge=0.5, r=0.022):
    """Teigstrang aus n Perlen; form(f) bestimmt die Lage (teigstrang_form). Lokale Punkte, Root = Mitte."""
    root = L.empty(name, coll=coll)
    m = L.mat("bg_teig", TEIG, 0.75)
    perlen = [L.sphere(f"{name}_{k}", r, 8, 5, (1, 1, 1), m, root, (-laenge / 2 + laenge * k / (n - 1), 0, r), coll)
              for k in range(n)]
    return P(root=root, perlen=perlen, n=n, laenge=laenge, r=r)


def teigstrang_form(T, ts, form, f0, f1, dicke=None):
    """form(f, u) -> lokaler Punkt fuer Parameter u in 0..1 (z. B. gerade, Bogen, Brezel). dicke(f, u) -> Faktor."""
    for k, o in enumerate(ts.perlen):
        u = k / (ts.n - 1)
        T.set(o, "location", lambda f, u=u: tuple(form(f, u)), f0, f1)
        if dicke:
            T.set(o, "scale", lambda f, u=u: (dicke(f, u),) * 3, f0, f1)


def form_gerade(laenge, z=0.022):
    return lambda f, u: Vector((-laenge / 2 + laenge * u, 0, z))


def form_brezel(s=1.0, z=0.03):
    """Brezelform ueber u (Bauch 0..0.6, Aermchen 0.6..1)."""
    bauch = _brezel_pts(s, z)[:25]
    arm_r = _brezel_pts(s, z)[25:]
    arm_l = list(reversed(_brezel_pts_links(s, z)))
    pts = [Vector(p) for p in arm_l + bauch + arm_r]

    def fn(f, u):
        x = u * (len(pts) - 1)
        i = min(len(pts) - 2, int(x))
        return pts[i].lerp(pts[i + 1], x - i)
    return fn


def form_mischen(a, b, t_fn):
    """Zwischen zwei Formen ueberblenden: t_fn(f) 0..1."""
    return lambda f, u: a(f, u).lerp(b(f, u), max(0.0, min(1.0, t_fn(f))))


def form_schwung(basis, mitte_fn, hoehe=0.18, dreh=1.0):
    """Strang wird angehoben und dreht sich in der Luft (Schwung): mitte_fn(f) 0..1 = Phase."""
    def fn(f, u):
        p = basis(f, u)
        ph = max(0.0, min(1.0, mitte_fn(f)))
        lift = math.sin(math.pi * ph) * hoehe * (0.4 + 0.6 * math.sin(math.pi * u))
        a = dreh * math.pi * ph * (u - 0.5)
        return Vector((p.x * math.cos(a), p.y + 0.05 * math.sin(a), p.z + lift))
    return fn


# ------------------------------------------------------------------ Kamera an der Antenne
def kamera_antenne(coll, name, byte):
    """Kleine Kamera mit rotem REC-Licht, klappt aus Bytes Antenne (Pivot an der Antennenspitze)."""
    import viral as VP
    piv = L.empty(f"{name}_piv", byte.ant, (0, 0, 0.12), coll)
    cam = VP.mini_kamera(coll, name)
    cam.root.parent = piv
    cam.root.location = (0, -0.06, 0.02)
    cam.root.rotation_euler = (math.pi / 2, 0, 0)
    piv.scale = (0, 0, 0)
    return P(root=piv, cam=cam)


def kamera_ausklappen(T, ka, f_in, f_out=None):
    T.set(ka.root, "scale", lambda f: ((pop(f, f_in, 8) * (unpop(f, f_out, 6) if f_out is not None and f > f_out else 1)),) * 3,
          f_in - 1, (f_out + 7) if f_out is not None else f_in + 9)
    T.set(ka.root, "rotation_euler", lambda f: (-1.2 * (1 - ease_out_back(clamp01((f - f_in) / 10), 2.0)), 0, 0), f_in - 1, f_in + 11)


# ------------------------------------------------------------------ Hand-Standbilder (5, nummeriert, beschriftet)
def hand_standbild_3d(coll, name, nummer, label, pose=0.0):
    """Leuchtendes 3D-Standbild von Kalles Haenden mit Teig: Glas-Sockel, Haende (warm leuchtend), Nummer im Kreis,
    Beschriftung. pose 0..1 waehlt die Handhaltung (rollen -> ablegen)."""
    root = L.empty(name, coll=coll)
    m_glas = L.mat("bg_sb_glas", "#BFF7F2", 0.2, alpha=0.25)
    m_rand = L.mat("bg_sb_rand", TURQ, 0.3, emit=TURQ, strength=3.0)
    m_hand = L.mat("bg_sb_hand", "#F4C8A6", 0.4, emit="#FFD9B8", strength=1.2)
    m_teig = L.mat("bg_teig", TEIG, 0.75)
    L.box(f"{name}_glas", (0.42, 0.42, 0.5), m_glas, root, (0, 0, 0.25), coll)
    L.box(f"{name}_sockel", (0.46, 0.46, 0.04), m_rand, root, (0, 0, 0.0), coll)
    for sx in (-1, 1):
        a = pose * 1.2
        h = L.empty(f"{name}_h{sx}", root, (sx * (0.1 - 0.05 * pose), 0, 0.22 + 0.08 * math.sin(math.pi * pose)), coll)
        h.rotation_euler = (0.4 + 0.5 * pose, sx * a * 0.6, sx * a)
        L.sphere(f"{name}_palm{sx}", 0.055, 8, 6, (0.9, 0.7, 1.0), m_hand, h, (0, 0, 0), coll)
        for j in range(4):
            L.cyl(f"{name}_f{sx}{j}", 0.011, 0.06, 6, m_hand, h, (-0.025 + 0.017 * j, -0.01, -0.06), coll)
        L.sphere(f"{name}_d{sx}", 0.02, 6, 4, (1, 1, 1.5), m_hand, h, (-sx * 0.05, -0.02, 0.0), coll)
    L.cyl(f"{name}_strang", 0.014, 0.28 - 0.1 * pose, 8, m_teig, root, (0, -0.02, 0.15), coll, axis="X")
    kreis = L.empty(f"{name}_kreis", root, (0, -0.22, 0.6), coll)
    L.torus(f"{name}_ring", 0.07, 0.01, 24, 5, m_rand, kreis, (0, 0, 0), coll, axis="Y")
    L.cyl(f"{name}_disc", 0.064, 0.006, 24, L.mat("bg_disc", NAVY, 0.4), kreis, (0, 0.004, 0), coll, axis="Y")
    _text(f"{name}_n", str(nummer), 0.09, m_rand, kreis, (0, -0.006, -0.03), coll)
    L.box(f"{name}_lbg", (0.36, 0.02, 0.09), L.mat("bg_lbg", NAVY, 0.5), root, (0, -0.22, -0.08), coll, bevel=0.02)
    _text(f"{name}_l", label, 0.06, L.mat("bg_lweiss", "#FFFFFF", 0.5), root, (0, -0.235, -0.1), coll)
    root.scale = (0, 0, 0)
    return P(root=root, kreis=kreis)


# ------------------------------------------------------------------ Eisberg des Wissens
def eisberg_wissen(coll, name, oben="WAS KALLE SAGT", schild="Bauch dick, Ärmchen dünn", unten="WAS KALLE KANN"):
    """Low-Poly-Eisberg: kleiner Gipfel ueber der Wasserlinie (Schild), riesiger Teil darunter mit leuchtenden
    Symbolen (Handgelenk-Schwung, Gefuehl fuer den Teig, Takt). Vorderseite -Y."""
    root = L.empty(name, coll=coll)
    m_eis = L.mat("bg_eis", "#E8F6FF", 0.4)
    m_eis2 = L.mat("bg_eis_unter", "#7FC4E6", 0.4)
    m_wasser = L.mat("bg_wasser", "#2E6FA8", 0.2, alpha=0.45)
    rnd = random.Random(3)
    L.ico(f"{name}_gipfel", 0.32, 1, (1.0, 0.8, 0.9), m_eis, root, (0, 0, 0.2), coll)
    L.ico(f"{name}_gipfel2", 0.18, 1, (1, 1, 1.2), m_eis, root, (0.12, 0.05, 0.38), coll)
    L.ico(f"{name}_unter", 1.0, 1, (1.15, 0.8, 0.95), m_eis2, root, (0, 0.1, -1.05), coll)
    for k in range(5):
        L.ico(f"{name}_u{k}", rnd.uniform(0.3, 0.5), 1, (1, 1, 1), m_eis2, root,
              (rnd.uniform(-0.9, 0.9), 0.15, rnd.uniform(-1.6, -0.5)), coll)
    L.box(f"{name}_wasser", (4.0, 3.0, 0.01), m_wasser, root, (0, 0.5, 0.0), coll)
    L.box(f"{name}_linie", (4.0, 0.02, 0.012), L.mat("bg_wlinie", "#BFE8FF", 0.3, emit="#BFE8FF", strength=2.0), root,
          (0, -1.0, 0.003), coll)
    weiss = L.mat("bg_lweiss", "#FFFFFF", 0.5)
    L.box(f"{name}_ob", (1.1, 0.02, 0.13), L.mat("bg_lbg", NAVY, 0.5), root, (0, -0.42, 0.85), coll, bevel=0.03)
    _text(f"{name}_ot", oben, 0.085, weiss, root, (0, -0.435, 0.82), coll)
    L.box(f"{name}_sb", (1.15, 0.03, 0.16), L.mat("bg_holz", "#C08A55", 0.6), root, (0, -0.36, 0.6), coll, bevel=0.02)
    L.box(f"{name}_sp", (0.03, 0.03, 0.3), L.mat("bg_holz_d", "#5E3E2B", 0.6), root, (0, -0.33, 0.42), coll)
    _text(f"{name}_st", schild, 0.07, L.mat("bg_ink", NAVY, 0.5), root, (0, -0.38, 0.575), coll)
    L.box(f"{name}_ub", (1.1, 0.02, 0.13), L.mat("bg_lbg", NAVY, 0.5), root, (0, -0.75, -0.35), coll, bevel=0.03)
    _text(f"{name}_ut", unten, 0.085, L.mat("bg_gold", GOLD, 0.4, emit=GOLD, strength=2.0), root, (0, -0.765, -0.38), coll)
    sym = []
    m_sym = L.mat("bg_sym", TURQ, 0.3, emit=TURQ, strength=3.0)
    for k, (x, z, txt) in enumerate([(-0.55, -0.85, "Schwung"), (0.0, -1.15, "Gefühl"), (0.55, -0.85, "Takt")]):
        s = L.empty(f"{name}_sym{k}", root, (x, -0.75, z), coll)
        if k == 0:
            for j in range(8):
                a = math.pi * (0.15 + 0.7 * j / 7)
                L.sphere(f"{name}_sw{j}", 0.025, 6, 4, (1, 1, 1), m_sym, s, (0.13 * math.cos(a), 0, 0.13 * math.sin(a) - 0.05), coll)
        elif k == 1:
            L.sphere(f"{name}_hz", 0.07, 8, 6, (1.2, 0.5, 1.0), m_sym, s, (0, 0, 0.02), coll)
        else:
            for j in range(3):
                L.box(f"{name}_tk{j}", (0.03, 0.02, 0.05 + 0.05 * j), m_sym, s, (-0.06 + 0.06 * j, 0, 0.0), coll)
        _text(f"{name}_symt{k}", txt, 0.06, weiss, s, (0, -0.01, -0.14), coll)
        sym.append(s)
    root.scale = (0, 0, 0)
    return P(root=root, symbole=sym)


# ------------------------------------------------------------------ Siegerpodest, Mehlspuren, Schildchen, Tuete, Auslage
def siegerpodest_mini(coll, name):
    root = L.empty(name, coll=coll)
    m = L.mat("bg_podest", "#F5F1E8", 0.6)
    m_g = L.mat("bg_gold", GOLD, 0.4, emit=GOLD, strength=2.0)
    for x, h, n in ((-0.16, 0.06, "2"), (0.0, 0.1, "1"), (0.16, 0.045, "3")):
        L.box(f"{name}_{n}", (0.15, 0.14, h), m, root, (x, 0, h / 2), coll)
        _text(f"{name}_t{n}", n, 0.05, m_g if n == "1" else L.mat("bg_ink", NAVY, 0.5), root, (x, -0.072, h / 2 - 0.018), coll)
    return P(root=root, top=(0.0, 0.0, 0.1))


def mehlstrich_stirn(T, lea, f_in, s=1.0):
    """Mehlstrich auf Leas Stirn (bleibt ab f_in sichtbar), erscheint mit dem Wisch der Hand."""
    m = L.mat("bg_mehl", "#FFFFFF", 0.9)
    o = L.sphere("lea_mehlstrich", 0.05, 8, 5, (1.6, 0.2, 0.3), m, lea.head, (0.1, -0.235, 0.405), lea.coll)
    o.rotation_euler = (0.35, -0.35, 0.25)
    T.set(o, "scale", lambda f: (clamp01((f - f_in) / 4),) * 3 if f >= f_in else (0, 0, 0), 0, f_in + 5)
    return o


def mehlfleck_schuerze(T, lea, f_in):
    """Erster Mehlfleck auf Leas sauberer Schuerze (Handabdruck) ab f_in."""
    m = L.mat("bg_mehl2", "#EDE4D2", 0.85)
    piv = L.empty("lea_mehlfleck", lea.apron_anchor, (0, 0, 0), lea.coll)
    L.sphere("lea_fleck_m", 0.06, 8, 5, (1.0, 0.12, 0.85), m, piv, (0, 0, 0), lea.coll)
    for j in range(4):
        L.sphere(f"lea_fleck_f{j}", 0.018, 6, 4, (0.7, 0.12, 1.6), m, piv, (-0.04 + 0.027 * j, 0.0, 0.07), lea.coll)
    T.set(piv, "scale", lambda f: (ease_out(clamp01((f - f_in) / 5)),) * 3 if f >= f_in else (0, 0, 0), 0, f_in + 6)
    return piv


def schildchen_handschrift(coll, name, text="VON LEA"):
    """Kleines handgeschriebenes Schildchen (Karte im Halter), leicht schief."""
    root = L.empty(name, coll=coll)
    L.box(f"{name}_k", (0.26, 0.01, 0.12), L.mat("bg_karte", "#FFF8E6", 0.7), root, (0, 0, 0.1), coll)
    L.box(f"{name}_h", (0.04, 0.04, 0.05), L.mat("bg_halter", "#5E3E2B", 0.6), root, (0, 0.01, 0.025), coll)
    t = _text(f"{name}_t", text, 0.055, L.mat("bg_kuli", "#2B3F8F", 0.5), root, (0, -0.008, 0.085), coll, extrude=0.001)
    t.rotation_euler = (math.pi / 2, -0.06, 0)
    root.rotation_euler = (0, 0, 0.08)
    return P(root=root)


def papiertuete(coll, name):
    root = L.empty(name, coll=coll)
    m = L.mat("bg_tuete", "#D9B98C", 0.8)
    L.box(f"{name}_b", (0.2, 0.1, 0.26), m, root, (0, 0, 0.13), coll)
    L.box(f"{name}_f", (0.2, 0.11, 0.04), L.mat("bg_tuete2", "#C9A878", 0.8), root, (0, 0, 0.27), coll).rotation_euler = (0.3, 0, 0)
    _text(f"{name}_t", "KALLE", 0.04, L.mat("bg_tueteink", "#8A4519", 0.6), root, (0, -0.052, 0.14), coll, extrude=0.001)
    return P(root=root)


def auslage_theke(coll, name, breite=1.4):
    """Auslage hinter dem Schaufenster: Holzsockel, Glasfront, zwei Boeden mit Gebaeck."""
    root = L.empty(name, coll=coll)
    L.box(f"{name}_sockel", (breite, 0.5, 0.7), L.mat("bg_ausl_holz", "#9A6A43", 0.6), root, (0, 0, 0.35), coll)
    L.box(f"{name}_boden", (breite - 0.06, 0.46, 0.02), L.mat("bg_ausl_boden", "#F5F1E8", 0.6), root, (0, 0, 0.71), coll)
    L.box(f"{name}_glas", (breite, 0.02, 0.32), L.mat("bg_ausl_glas", "#D9F0FA", 0.1, alpha=0.18), root, (0, -0.24, 0.87), coll)
    L.box(f"{name}_deckel", (breite, 0.5, 0.02), L.mat("bg_ausl_glas", "#D9F0FA", 0.1, alpha=0.18), root, (0, 0, 1.03), coll)
    for k, kind in enumerate(["broetchen", "croissant", "schnecke", "broetchen", "croissant"]):
        PR.pastry(coll, f"{name}_p{k}", kind, root, (-breite / 2 + 0.2 + 0.22 * k, 0.12, 0.72), 0.8)
    return P(root=root, platz=(breite / 2 - 0.25, -0.05, 0.72))


def mehl_puder(T, coll, name, ort, f, n=14, seed=1):
    """Kleine Mehlwolke (engine/props.burst 'puff'), z. B. beim Haare-Raufen oder Schulter-Klopfen."""
    PR.burst(T, coll, name, "puff", tuple(ort), f, n, seed, speed=(0.3, 0.8), up=0.4, gravity=-0.3,
             life=(16, 26), size=(0.5, 1.0), drag=3.0, ring=True)


__all__ = ["brezel_missglueckt", "reihe_missglueckt", "brezel_roh_perfekt", "brezel_gebacken", "salz_glitzern",
           "teigstrang", "teigstrang_form", "form_gerade", "form_brezel", "form_mischen", "form_schwung",
           "kamera_antenne", "kamera_ausklappen", "hand_standbild_3d", "eisberg_wissen", "siegerpodest_mini",
           "mehlstrich_stirn", "mehlfleck_schuerze", "schildchen_handschrift", "papiertuete", "auslage_theke",
           "mehl_puder", "ease_in_out", "window"]
