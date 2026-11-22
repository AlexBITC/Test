"""Requisiten fuer die Folge 'Byte macht Kalle viral' (folge-06-viral).

Gleicher Low-Poly-Stil wie engine/props.py (look.py-Materialien, Vorderseite -Y). Leuchtende Teile werden in
Workbench ueber die Objektfarbe (diffuse_color) geschaltet, Emission allein waere dort unsichtbar.
Wiederverwendet aus engine/props.py: wall_clock (Wanduhr), pastry (Brezel), coin_small/burst 'coinp' (Muenzen),
burst 'puff'/'flourdust' (Mehlwolke).
"""
import math
import random

import bmesh
from mathutils import Vector

import look as L
import props as PR
from anim import ease_in_out, ease_out, ease_out_back, window, pop, unpop, spring

FPS = 30
P = PR.P
REC_RED = "#FF3B4A"


def _on_off(T, mat, f_on, f_off=None, c_on=None, c_off=None):
    """Schaltet die Objektfarbe eines Materials (Workbench) zwischen aus und an."""
    on = c_on or tuple(mat.diffuse_color)
    off = c_off or tuple(x * 0.28 for x in on[:3]) + (1.0,)
    T.set(mat, "diffuse_color", lambda f: on if (f >= f_on and (f_off is None or f < f_off)) else off, 0, 10 ** 5)


# ------------------------------------------------------------------ Mini-Kamera (REC-Licht blinkt)
def mini_kamera(coll, name):
    root = L.empty(name, coll=coll)
    m_body = L.mat("cam_body", "#2A2638", 0.45)
    L.box(f"{name}_body", (0.13, 0.08, 0.085), m_body, root, (0, 0.01, 0), coll, bevel=0.012)
    L.cyl(f"{name}_lensbarrel", 0.032, 0.05, 14, L.mat("cam_barrel", "#46496E", 0.4, metallic=0.4), root,
          (0.01, -0.045, 0), coll, axis="Y")
    L.cyl(f"{name}_glass", 0.024, 0.01, 14, L.mat("cam_glass", "#5FD3E8", 0.2, emit="#5FD3E8", strength=1.5), root,
          (0.01, -0.071, 0), coll, axis="Y")
    L.box(f"{name}_grip", (0.03, 0.06, 0.05), m_body, root, (-0.07, 0.0, -0.02), coll, bevel=0.01)
    L.box(f"{name}_top", (0.05, 0.04, 0.015), m_body, root, (0.025, 0.02, 0.05), coll)
    m_rec = L.unique_mat(L.mat("cam_rec", REC_RED, 0.4, emit=REC_RED, strength=6.0), f"{name}_recmat")
    rec = L.sphere(f"{name}_rec", 0.012, 8, 5, (1, 1, 1), m_rec, root, (-0.045, -0.032, 0.03), coll)
    L.text(f"{name}_reclab", "REC", 0.022, L.mat("cam_label", "#FFFFFF", 0.5), root, (-0.02, -0.031, 0.03), coll,
           extrude=0.002, font=L.font())
    return P(root=root, rec=rec, m_rec=m_rec)


def rec_blink(T, cam, f0, f1, period=16):
    on = tuple(cam.m_rec.diffuse_color)
    off = tuple(x * 0.25 for x in on[:3]) + (1.0,)
    T.set(cam.m_rec, "diffuse_color", lambda f: on if ((f - f0) % period) < period * 0.55 else off, f0, f1)
    T.set(cam.rec, "scale", lambda f: (1.25,) * 3 if ((f - f0) % period) < period * 0.55 else (0.85,) * 3, f0, f1)


# ------------------------------------------------------------------ Mini-Headset (Byte und Kalle)
def headset_mini(coll, name):
    """Masse fuer Byte (Kopfradius 0,22). Fuer Kalle mit root.scale ~1,45 skalieren.
    Buegel ueber den Kopf (Achse X), Muscheln links/rechts, Mikrofonarm von der rechten Muschel nach vorn."""
    root = L.empty(name, coll=coll)
    m_band = L.mat("hs_band", "#2A2638", 0.45)
    m_cup = L.mat("hs_cup", "#FF7A3D", 0.5)
    m_pad = L.mat("hs_pad", "#1B1830", 0.7)
    bm = bmesh.new()
    R, r = 0.245, 0.016
    n, tseg = 18, 6
    rings = []
    for i in range(n + 1):
        a = math.pi * i / n
        c = Vector((R * math.cos(a), 0, R * math.sin(a)))
        ring = []
        for j in range(tseg):
            b = 2 * math.pi * j / tseg
            nrm = Vector((math.cos(a), 0, math.sin(a)))
            off = nrm * (r * math.cos(b)) + Vector((0, r * math.sin(b) * 1.6, 0))
            ring.append(bm.verts.new(c + off))
        rings.append(ring)
    for i in range(n):
        for j in range(tseg):
            bm.faces.new((rings[i][j], rings[i + 1][j], rings[i + 1][(j + 1) % tseg], rings[i][(j + 1) % tseg]))
    L.from_bm(f"{name}_band", bm, m_band, root, (0, 0, 0), coll)
    for sx in (-1, 1):
        L.cyl(f"{name}_cup{sx}", 0.065, 0.04, 16, m_cup, root, (sx * 0.252, 0, -0.01), coll, axis="X")
        L.cyl(f"{name}_pad{sx}", 0.052, 0.02, 14, m_pad, root, (sx * 0.228, 0, -0.01), coll, axis="X")
    boom = L.empty(f"{name}_boom", root, (-0.26, -0.02, -0.04), coll)
    boom.rotation_euler = (math.radians(-80), 0, math.radians(-38))
    L.cyl(f"{name}_boomrod", 0.007, 0.2, 6, m_band, boom, (0, 0, 0.1), coll)
    L.sphere(f"{name}_mic", 0.02, 8, 6, (1, 1, 1.3), L.mat("hs_mic", "#111018", 0.6), boom, (0, 0, 0.205), coll)
    return P(root=root)


# ------------------------------------------------------------------ Ringlicht (schaltet sich ein)
def ringlicht(coll, name):
    root = L.empty(name, coll=coll)
    m_dark = L.mat("rl_dark", "#2A2638", 0.45)
    L.cyl(f"{name}_foot", 0.07, 0.02, 12, m_dark, root, (0, 0, 0.01), coll)
    for k in range(3):
        a = 2 * math.pi * k / 3
        leg = L.cyl(f"{name}_leg{k}", 0.006, 0.12, 5, m_dark, root, (0.04 * math.cos(a), 0.04 * math.sin(a), 0.05),
                    coll)
        leg.rotation_euler = (0.5 * math.sin(a), -0.5 * math.cos(a), 0)
    L.cyl(f"{name}_pole", 0.008, 0.3, 6, m_dark, root, (0, 0, 0.25), coll)
    head = L.empty(f"{name}_head", root, (0, 0, 0.47), coll)
    L.torus(f"{name}_housing", 0.12, 0.022, 28, 6, m_dark, head, (0, 0.006, 0), coll, axis="Y")
    m_ring = L.unique_mat(L.mat("rl_ring", "#FFF6DC", 0.3, emit="#FFF6DC", strength=8.0), f"{name}_ringmat")
    ring = L.torus(f"{name}_ring", 0.12, 0.014, 28, 6, m_ring, head, (0, -0.01, 0), coll, axis="Y")
    L.box(f"{name}_phonemount", (0.07, 0.01, 0.12), m_dark, head, (0, -0.005, 0), coll, bevel=0.006)
    m_glow = L.unique_mat(L.mat("rl_glow", "#FFF2C8", 0.3, emit="#FFF2C8", strength=1.0, alpha=0.16),
                          f"{name}_glowmat")
    glow = L.torus(f"{name}_glow", 0.12, 0.05, 28, 6, m_glow, head, (0, -0.02, 0), coll, axis="Y")
    glow.scale = (0, 0, 0)
    return P(root=root, head=head, ring=ring, m_ring=m_ring, glow=glow)


def ringlicht_an(T, rl, f_on, f_off=None):
    _on_off(T, rl.m_ring, f_on, f_off)
    T.set(rl.glow, "scale", lambda f: ((1 + 0.15 * spring((f - f_on) / FPS, 3, 0.4)) * pop(f, f_on, 4),) * 3
          if f >= f_on and (f_off is None or f < f_off) else (0, 0, 0), 0, 10 ** 5)


# ------------------------------------------------------------------ Mini-Regieklappe
def regieklappe_mini(coll, name, text="KALLE · TAKE 1"):
    root = L.empty(name, coll=coll)
    m_b = L.mat("rk_black", "#1B1830", 0.5)
    m_w = L.mat("rk_white", "#F5F1E8", 0.6)
    L.box(f"{name}_board", (0.2, 0.012, 0.14), m_b, root, (0, 0, 0.07), coll, bevel=0.004)
    L.text(f"{name}_txt", text, 0.024, m_w, root, (0, -0.008, 0.075), coll, extrude=0.002, font=L.font())
    L.box(f"{name}_line", (0.17, 0.004, 0.004), m_w, root, (0, -0.007, 0.045), coll)
    L.box(f"{name}_base", (0.2, 0.014, 0.03), m_b, root, (0, 0, 0.155), coll)
    for k in range(5):
        L.box(f"{name}_bs{k}", (0.018, 0.016, 0.03), m_w, root, (-0.08 + k * 0.04, -0.001, 0.155), coll).rotation_euler = (0, 0.6, 0)
    stick = L.empty(f"{name}_stick", root, (-0.1, 0, 0.172), coll)
    L.box(f"{name}_top", (0.2, 0.014, 0.03), m_b, stick, (0.1, 0, 0.015), coll)
    for k in range(5):
        L.box(f"{name}_ts{k}", (0.018, 0.016, 0.03), m_w, stick, (0.02 + k * 0.04, -0.001, 0.015), coll).rotation_euler = (0, -0.6, 0)
    return P(root=root, stick=stick)


def klappe(T, rk, f_open, f_clap):
    """Klappe oeffnet (f_open) und schlaegt bei f_clap zu."""
    def ang(f):
        if f < f_open:
            return 0.0
        if f < f_clap - 3:
            return 0.55 * ease_out((f - f_open) / 5)
        if f < f_clap:
            return 0.55 * (1 - (f - (f_clap - 3)) / 3)
        return -0.06 * spring((f - f_clap) / FPS, 6, 0.3)
    T.set(rk.stick, "rotation_euler", lambda f: (0, -ang(f), 0), f_open - 1, f_clap + 12)


# ------------------------------------------------------------------ Posten-Knopf (leuchtet, wird gedrueckt)
def posten_knopf(coll, name):
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_base", 0.2, 0.08, 24, L.mat("pk_base", "#2A2638", 0.45), root, (0, 0, 0.04), coll)
    L.torus(f"{name}_rim", 0.18, 0.015, 24, 5, L.mat("pk_rim", L.TURQ, 0.4, emit=L.TURQ, strength=3.0), root,
            (0, 0, 0.082), coll)
    cap = L.empty(f"{name}_cap", root, (0, 0, 0.08), coll)
    m_cap = L.unique_mat(L.mat("pk_cap", "#FF3B6B", 0.35, emit="#FF3B6B", strength=4.0), f"{name}_capmat")
    L.cyl(f"{name}_capm", 0.15, 0.07, 24, m_cap, cap, (0, 0, 0.035), coll, r2=0.14)
    lab = L.text(f"{name}_lab", "POSTEN", 0.07, L.mat("pk_lab", "#FFFFFF", 0.4, emit="#FFFFFF", strength=2.0), cap,
                 (0, 0, 0.072), coll, extrude=0.004, rot=(0, 0, 0), font=L.font())
    sign = L.text(f"{name}_sign", "POSTEN", 0.09, L.mat("pk_lab", "#FFFFFF", 0.4, emit="#FFFFFF", strength=2.0), root,
                  (0, -0.205, 0.04), coll, extrude=0.004, font=L.font())
    return P(root=root, cap=cap, m_cap=m_cap, lab=lab)


def knopf_druecken(T, pk, f_press):
    T.set(pk.cap, "location", lambda f: (0, 0, 0.08 - 0.045 * window(f, f_press, f_press + 8, 2, 5)), f_press - 1,
          f_press + 9)
    on = tuple(pk.m_cap.diffuse_color)
    hi = tuple(min(1.0, x * 1.6 + 0.15) for x in on[:3]) + (1.0,)
    T.set(pk.m_cap, "diffuse_color", lambda f: hi if f_press <= f < f_press + 10 else on, 0, 10 ** 5)


# ------------------------------------------------------------------ Mechanischer Aufrufzaehler
def aufrufzaehler(coll, name, stellen=5):
    """Gehaeuse mit Zahlenwalzen (Achse X), Punkt nach der Tausenderstelle, Schild 'AUFRUFE'.
    Lippen vor den Walzen verdecken alles ausser der vorderen Ziffer."""
    root = L.empty(name, coll=coll)
    m_case = L.mat("az_case", "#C0392B", 0.45)
    m_dark = L.mat("az_dark", "#141228", 0.5)
    m_gold = L.mat("az_gold", L.GOLD, 0.4, metallic=0.6)
    m_drum = L.mat("az_drum", "#F5F1E8", 0.55)
    m_dig = L.mat("az_digit", "#141228", 0.5)
    pitch = 0.15
    xs = []
    total_w = stellen * pitch + 0.08
    L.box(f"{name}_case", (total_w + 0.16, 0.36, 0.5), m_case, root, (0, 0.12, 0), coll, bevel=0.03)
    L.box(f"{name}_window", (total_w + 0.02, 0.05, 0.2), m_dark, root, (0, -0.05, 0), coll)
    r = 0.17
    drums = []
    xi = -total_w / 2 + 0.04 + pitch / 2
    for k in range(stellen):           # k = 0 links (hoechste Stelle)
        x = xi + k * pitch + (0.06 if k >= stellen - 3 else 0)
        xs.append(x)
        d = L.empty(f"{name}_drum{k}", root, (x, -0.1 - r + 0.02, 0), coll)
        L.cyl(f"{name}_drumm{k}", r, 0.12, 20, m_drum, d, (0, 0, 0), coll, axis="X")
        for j in range(10):
            a = 2 * math.pi * j / 10
            t = L.text(f"{name}_d{k}_{j}", str(j), 0.12, m_dig, d, (0, -r * math.cos(a) - 0.002, r * math.sin(a)), coll,
                       extrude=0.004, rot=(math.pi / 2 - a, 0, 0), font=L.font())
            t.data.align_y = "CENTER"
        drums.append(d)
    # Lippen: oben und unten vor den Walzen
    for sz in (1, -1):
        L.box(f"{name}_lip{sz}", (total_w + 0.16, 0.24, 0.18), m_case, root, (0, -0.33, sz * 0.16), coll, bevel=0.02)
    L.box(f"{name}_dot", (0.03, 0.02, 0.03), m_gold, root, ((xs[stellen - 4] + xs[stellen - 3]) / 2 + 0.03, -0.43, -0.05),
          coll)
    L.box(f"{name}_plate", (0.6, 0.02, 0.1), m_gold, root, (0, -0.46, 0.16), coll, bevel=0.01)
    L.text(f"{name}_lab", "AUFRUFE", 0.075, m_dark, root, (0, -0.475, 0.157), coll, extrude=0.004, font=L.font())
    crank = L.empty(f"{name}_crank", root, (total_w / 2 + 0.09, 0.12, 0), coll)
    L.cyl(f"{name}_crankaxle", 0.02, 0.06, 8, m_gold, crank, (0.03, 0, 0), coll, axis="X")
    L.box(f"{name}_crankarm", (0.02, 0.02, 0.16), m_gold, crank, (0.06, 0, 0.07), coll)
    L.sphere(f"{name}_crankknob", 0.03, 8, 5, (1, 1, 1), L.mat("az_knob", "#1B1830", 0.5), crank, (0.06, 0, 0.15), coll)
    return P(root=root, drums=drums, crank=crank, stellen=stellen)


def zaehler_laufen(T, az, value_fn, f0, f1):
    """Walzen wie ein Kilometerzaehler: Einerstelle laeuft stetig, hoehere Stellen rollen beim Uebertrag."""
    n = az.stellen

    def angle(f, k):
        v = max(0.0, value_fn(f))
        p = 10 ** (n - 1 - k)
        if p == 1:
            pos = v
        else:
            low = (v % p) / p
            pos = math.floor(v / p) + (max(0.0, (low - 0.9) * 10) if low > 0.9 else 0.0)
        return 2 * math.pi * pos / 10
    for k, d in enumerate(az.drums):
        T.set(d, "rotation_euler", lambda f, k=k: (angle(f, k), 0, 0), f0, f1)
    T.set(az.crank, "rotation_euler", lambda f: (-0.4 * (value_fn(f) / 1500.0), 0, 0), f0, f1)


# ------------------------------------------------------------------ Herzchen-Partikel
def _heart_mesh(name, coll, color="#FF4F7B"):
    pts = []
    for k in range(32):
        t = 2 * math.pi * k / 32
        x = 16 * math.sin(t) ** 3
        z = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x / 17 * 0.08, z / 17 * 0.08))
    return L.poly_flat(name, pts, 0.03, L.mat(f"heart_{color}", color, 0.4, emit=color, strength=3.0), None, (0, 0, -50),
                       coll)


def herzchen(T, coll, name, origin, f0, count, seed, f_end=None, rise=(0.8, 1.4), spread=0.9):
    """Herzchen steigen wie Seifenblasen auf: schaukeln seitlich, ploppen am Ende."""
    r = random.Random(seed)
    o0 = Vector(origin)
    objs = []
    cols = ["#FF4F7B", "#FF7A9C", "#FF3B6B"]
    for i in range(count):
        h = _heart_mesh(f"{name}_{i}", coll, cols[i % 3])
        t0 = f0 + r.uniform(0, 26) + i * 1.2
        life = r.uniform(30, 46)
        if f_end is not None:
            life = min(life, f_end - t0)
        start = o0 + Vector((r.uniform(-spread, spread) * 0.5, r.uniform(-0.15, 0.15), r.uniform(-0.1, 0.1)))
        vz = r.uniform(*rise)
        ph = r.uniform(0, 6.28)
        sz = r.uniform(0.8, 1.4)

        def loc(f, t0=t0, start=start, vz=vz, ph=ph):
            t = max(0.0, (f - t0) / FPS)
            return tuple(start + Vector((0.12 * math.sin(4.0 * t + ph), 0, vz * t)))

        def scl(f, t0=t0, life=life, sz=sz):
            if f < t0:
                return (0, 0, 0)
            s = sz * pop(f, t0, 6, 1.25)
            if f > t0 + life - 5:
                s *= unpop(f, t0 + life - 5, 5)
            return (s, s, s)
        T.set(h, "location", loc, t0 - 1, t0 + life + 1)
        T.set(h, "scale", scl, t0 - 1, t0 + life + 1)
        T.set(h, "scale", lambda f: (0, 0, 0), 0, 1)
        T.set(h, "rotation_euler", lambda f, ph=ph: (0, 0.25 * math.sin(f * 0.2 + ph), 0), t0 - 1, t0 + life + 1)
        objs.append((h, t0))
    return objs


# ------------------------------------------------------------------ Kundenschlange (Low-Poly, Handys hoch)
def kunde_mit_handy(coll, name, color, s=1.0, seed=0, handy=True):
    r = random.Random(seed)
    root = L.empty(name, coll=coll)
    root.scale = (s, s, s)
    body = L.empty(f"{name}_body", root, (0, 0, 0), coll)
    m_c = L.mat(f"kd_{color}", color, 0.6)
    L.cyl(f"{name}_torso", 0.2, 0.62, 8, m_c, body, (0, 0, 1.12), coll, r2=0.15)
    L.cyl(f"{name}_legs", 0.15, 0.82, 8, L.mat("kd_legs", "#34497A", 0.6), body, (0, 0, 0.41), coll, r2=0.13)
    skin = r.choice(["#E7B08A", "#C98E68", "#F1C6A4", "#9B6A4A"])
    head = L.empty(f"{name}_headpiv", body, (0, 0, 1.6), coll)
    L.sphere(f"{name}_head", 0.16, 10, 7, (1, 1, 1.08), L.mat(f"kd_skin{skin}", skin, 0.62), head, (0, 0, 0), coll)
    hair = r.choice(["#3A2A22", "#C9944A", "#6B4A3A", "#1B1830", "#A9A5A0"])
    L.sphere(f"{name}_hair", 0.165, 10, 6, (1, 1, 0.6), L.mat(f"kd_hair{hair}", hair, 0.7), head, (0, 0.03, 0.08), coll)
    for sx in (-1, 1):
        L.sphere(f"{name}_eye{sx}", 0.022, 6, 4, (1, 1, 1), L.mat("kd_eye", "#17142a", 0.5), head,
                 (sx * 0.06, -0.145, 0.02), coll)
    arm = L.empty(f"{name}_arm", body, (-0.2, 0, 1.38), coll)
    L.cyl(f"{name}_armm", 0.055, 0.42, 6, m_c, arm, (0, 0, -0.2), coll)
    phone = None
    if handy:
        arm.rotation_euler = (math.radians(-150), 0, math.radians(10))
        phone = L.empty(f"{name}_phone", arm, (0, 0, -0.45), coll)
        L.box(f"{name}_phonem", (0.12, 0.02, 0.22), L.mat("kd_phone", "#1B1830", 0.4), phone, (0, 0, 0), coll, bevel=0.01)
        L.box(f"{name}_phonescr", (0.1, 0.004, 0.19), L.mat("kd_screen", "#9FF6EE", 0.3, emit="#9FF6EE", strength=3.0),
              phone, (0, 0.012, 0), coll)
        L.sphere(f"{name}_phonerec", 0.012, 6, 4, (1, 1, 1), L.mat("cam_rec", REC_RED, 0.4, emit=REC_RED, strength=6.0),
                 phone, (0.035, -0.012, 0.08), coll)
        phone.rotation_euler = (math.radians(-60), 0, 0)
    else:
        arm.rotation_euler = (0.1, 0, 0.15)
    arm2 = L.empty(f"{name}_arm2", body, (0.2, 0, 1.38), coll)
    L.cyl(f"{name}_arm2m", 0.055, 0.42, 6, m_c, arm2, (0, 0, -0.2), coll)
    arm2.rotation_euler = (0.1, 0, -0.15)
    return P(root=root, body=body, head=head, arm=arm, phone=phone)


def kunden_schlange(coll, name, pts, seed=12, s=0.95, handy_quote=0.75):
    """pts: Liste von Standpunkten (Vector). Kunden schauen nach +Y (zur Theke)."""
    r = random.Random(seed)
    cols = ["#E0703D", "#3E8E6A", "#6C5BA8", "#C9944A", "#2E8C88", "#B5524F", "#4E6B8A", "#D9A866"]
    out = []
    for i, p in enumerate(pts):
        k = kunde_mit_handy(coll, f"{name}{i}", cols[i % len(cols)], s=s * r.uniform(0.92, 1.06), seed=seed + i,
                            handy=r.random() < handy_quote or i < 2)
        k.root.location = p
        k.root.rotation_euler = (0, 0, math.pi + r.uniform(-0.25, 0.25))
        out.append(k)
    return out


# ------------------------------------------------------------------ Fenster mit Tageszeit
def fenster_tageszeit(coll, name, w=1.2, h=1.2):
    """Fenster (Front -Y): Himmel-Platte mit animierbarer Farbe, Mond, Sterne, Morgensonne, Fensterkreuz."""
    root = L.empty(name, coll=coll)
    m_frame = L.mat("fz_frame", "#F0EADD", 0.6)
    m_sky = L.unique_mat(L.mat("fz_sky", "#101A3C", 0.6, emit="#101A3C", strength=1.0), f"{name}_skymat")
    L.box(f"{name}_sky", (w, 0.02, h), m_sky, root, (0, 0.03, 0), coll)
    night = L.empty(f"{name}_night", root, (0, 0, 0), coll)
    m_moon = L.mat("fz_moon", "#FFF3C4", 0.4, emit="#FFF3C4", strength=5.0)
    L.cyl(f"{name}_moon", 0.13, 0.01, 20, m_moon, night, (w * 0.22, 0.015, h * 0.22), coll, axis="Y")
    L.cyl(f"{name}_moonbite", 0.12, 0.012, 20, m_sky, night, (w * 0.22 + 0.07, 0.01, h * 0.22 + 0.04), coll, axis="Y")
    r = random.Random(4)
    m_star = L.mat("fz_star", "#FFFFFF", 0.4, emit="#FFFFFF", strength=5.0)
    for k in range(14):
        L.ico(f"{name}_star{k}", r.uniform(0.008, 0.016), 0, (1, 1, 1), m_star, night,
              (r.uniform(-w / 2 + 0.06, w / 2 - 0.06), 0.012, r.uniform(-h / 2 + 0.06, h / 2 - 0.06)), coll)
    sun = L.empty(f"{name}_sun", root, (-w * 0.2, 0.012, -h * 0.32), coll)
    L.cyl(f"{name}_sunm", 0.17, 0.01, 24, L.mat("fz_sun", "#FFD36B", 0.4, emit="#FFD36B", strength=5.0), sun,
          (0, 0, 0), coll, axis="Y")
    sun.scale = (0, 0, 0)
    t = 0.06
    L.box(f"{name}_frameT", (w + 2 * t, 0.09, t), m_frame, root, (0, -0.01, h / 2 + t / 2), coll)
    L.box(f"{name}_frameB", (w + 2 * t, 0.12, t), m_frame, root, (0, -0.03, -h / 2 - t / 2), coll)
    L.box(f"{name}_frameL", (t, 0.09, h), m_frame, root, (-w / 2 - t / 2, -0.01, 0), coll)
    L.box(f"{name}_frameR", (t, 0.09, h), m_frame, root, (w / 2 + t / 2, -0.01, 0), coll)
    L.box(f"{name}_crossV", (0.035, 0.06, h), m_frame, root, (0, -0.01, 0), coll)
    L.box(f"{name}_crossH", (w, 0.06, 0.035), m_frame, root, (0, -0.01, 0), coll)
    return P(root=root, m_sky=m_sky, night=night, sun=sun)


SKY = {"nacht": "#101A3C", "daemmerung": "#5B4E8C", "morgen": "#F6B98A", "tag": "#BFE3F2"}


def tageszeit(T, fz, keys):
    """keys: [(frame, 'nacht'|'daemmerung'|'morgen'|'tag'), ...] -> Himmelfarbe, Mond/Sterne, Sonne."""
    keys = sorted(keys)
    cols = {k: L.srgb(v) for k, v in SKY.items()}

    def mix(f):
        if f <= keys[0][0]:
            return cols[keys[0][1]], keys[0][1], keys[0][1], 0.0
        for (fa, a), (fb, b) in zip(keys, keys[1:]):
            if fa <= f < fb:
                t = ease_in_out((f - fa) / max(1, fb - fa))
                return tuple(x + (y - x) * t for x, y in zip(cols[a], cols[b])), a, b, t
        return cols[keys[-1][1]], keys[-1][1], keys[-1][1], 1.0
    T.set(fz.m_sky, "diffuse_color", lambda f: tuple(mix(f)[0][:3]) + (1.0,), 0, 10 ** 5)

    def night_s(f):
        c, a, b, t = mix(f)
        w = {"nacht": 1.0, "daemmerung": 0.5}.get(a, 0.0) * (1 - t) + {"nacht": 1.0, "daemmerung": 0.5}.get(b, 0.0) * t
        return (w,) * 3

    def sun_s(f):
        c, a, b, t = mix(f)
        w = {"morgen": 1.0, "tag": 1.0}.get(a, 0.0) * (1 - t) + {"morgen": 1.0, "tag": 1.0}.get(b, 0.0) * t
        return (w,) * 3
    T.set(fz.night, "scale", night_s, 0, 10 ** 5)
    T.set(fz.sun, "scale", sun_s, 0, 10 ** 5)


# ------------------------------------------------------------------ Schreibtischlampe
def schreibtischlampe(coll, name):
    root = L.empty(name, coll=coll)
    m_met = L.mat("sl_metal", "#2E8C88", 0.45, metallic=0.3)
    L.cyl(f"{name}_base", 0.11, 0.035, 14, m_met, root, (0, 0, 0.018), coll)
    a1 = L.empty(f"{name}_a1", root, (0, 0, 0.035), coll)
    a1.rotation_euler = (0, math.radians(-25), 0)
    L.cyl(f"{name}_arm1", 0.014, 0.32, 6, m_met, a1, (0, 0, 0.16), coll)
    a2 = L.empty(f"{name}_a2", a1, (0, 0, 0.32), coll)
    a2.rotation_euler = (0, math.radians(95), 0)
    L.sphere(f"{name}_joint", 0.025, 8, 5, (1, 1, 1), m_met, a2, (0, 0, 0), coll)
    L.cyl(f"{name}_arm2", 0.012, 0.26, 6, m_met, a2, (0, 0, 0.13), coll)
    shade = L.empty(f"{name}_shade", a2, (0, 0, 0.27), coll)
    shade.rotation_euler = (0, math.radians(55), 0)
    L.cyl(f"{name}_shadem", 0.06, 0.15, 14, m_met, shade, (0, 0, -0.04), coll, r2=0.13)
    m_bulb = L.unique_mat(L.mat("sl_bulb", "#FFE7A8", 0.3, emit="#FFE7A8", strength=8.0), f"{name}_bulbmat")
    L.sphere(f"{name}_bulb", 0.045, 10, 6, (1, 1, 1), m_bulb, shade, (0, 0, -0.1), coll)
    m_cone = L.mat("sl_cone", "#FFE7A8", 0.3, emit="#FFE7A8", strength=1.0, alpha=0.13)
    cone = L.cyl(f"{name}_cone", 0.13, 0.7, 16, m_cone, shade, (0, 0, -0.47), coll, r2=0.42, cap=False)
    lp = L.light(f"{name}_light", "SPOT", 80, "#FFD8A0", (0, 0, -0.1), (math.pi, 0, 0), size=0.1, parent=shade,
                 coll=coll, cutoff=6, spot=1.2)
    return P(root=root, m_bulb=m_bulb, cone=cone, light=lp)


# ------------------------------------------------------------------ Brezelblech
def brezelblech(coll, name, n=6):
    root = L.empty(name, coll=coll)
    m_tray = L.mat("bb_tray", "#8E93A8", 0.4, metallic=0.6)
    L.box(f"{name}_tray", (0.62, 0.42, 0.015), m_tray, root, (0, 0, 0.008), coll)
    for sx, sz in ((1, 0), (-1, 0)):
        L.box(f"{name}_rimx{sx}", (0.015, 0.42, 0.03), m_tray, root, (sx * 0.31, 0, 0.02), coll)
        L.box(f"{name}_rimy{sx}", (0.62, 0.015, 0.03), m_tray, root, (0, sx * 0.21, 0.02), coll)
    brez = []
    for i in range(n):
        x = -0.2 + (i % 3) * 0.2
        y = -0.1 + (i // 3) * 0.2
        b = PR.pastry(coll, f"{name}_b{i}", "brezel", root, (x, y, 0.012), 0.75)
        b.rotation_euler = (math.pi / 2 - 0.15, 0, 0) if False else (0, 0, 0)
        brez.append(b)
    return P(root=root, brez=brez)
