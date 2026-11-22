"""Requisiten fuer 'Kalles Ausgaben-Dashboard' (folge-07-dashboard).

Gleicher Low-Poly-Stil wie engine/props.py (Vorderseite -Y). Leuchten/Transparenz fuer Workbench ueber diffuse_color.
Wiederverwendet aus engine/props.py: coin_column (Muenzsaeule), stempel (Stempel), envelope (Briefumschlag-Grundform),
burst (Partikel).
"""
import math
import random

import bmesh
from mathutils import Vector

import look as L
import props as PR
from anim import ease_in, ease_in_out, ease_out, ease_out_back, window, pop, unpop, spring

FPS = 30
P = PR.P
GHOST = "#7CC8FF"
RED = "#FF4D5A"


def _ghost_mat(name, alpha=0.5):
    return L.unique_mat(L.mat("geist", GHOST, 0.3, emit=GHOST, strength=2.0, alpha=alpha), f"{name}_geistmat")


# ------------------------------------------------------------------ Geister-Kaffeemaschine
def geister_kaffeemaschine(coll, name, preis="49 €/Monat"):
    """Halbdurchsichtig, blaeulich schimmernd, mit Ketten und beschriftbarem Preisschild."""
    root = L.empty(name, coll=coll)
    body = L.empty(f"{name}_body", root, (0, 0, 0), coll)
    m = _ghost_mat(name)
    m2 = L.unique_mat(L.mat("geist2", "#D8F2FF", 0.3, emit="#D8F2FF", strength=3.0, alpha=0.55), f"{name}_geistmat2")
    L.box(f"{name}_base", (0.42, 0.34, 0.06), m, body, (0, 0, 0.03), coll, bevel=0.015)
    L.box(f"{name}_tower", (0.42, 0.3, 0.5), m, body, (0, 0.04, 0.31), coll, bevel=0.03)
    L.box(f"{name}_head", (0.3, 0.2, 0.08), m, body, (0, -0.12, 0.48), coll, bevel=0.02)
    L.cyl(f"{name}_carafe", 0.09, 0.2, 12, m2, body, (0, -0.12, 0.17), coll, r2=0.075)
    L.cyl(f"{name}_spout", 0.02, 0.06, 8, m2, body, (0, -0.12, 0.41), coll)
    for k in range(2):
        L.cyl(f"{name}_btn{k}", 0.025, 0.02, 10, m2, body, (-0.1 + 0.2 * k, -0.11, 0.5), coll, axis="Y")
    # Geister-Schweif unten (Low-Poly-Kegel)
    tail = L.cyl(f"{name}_tail", 0.2, 0.32, 10, m, body, (0, 0.03, -0.15), coll, r2=0.02)
    # Ketten: Glieder an Pivots, schwingen
    m_ch = L.unique_mat(L.mat("kette", "#C9D6E8", 0.35, metallic=0.6, alpha=0.75), f"{name}_kettemat")
    chains = []
    for sx in (-1, 1):
        piv = L.empty(f"{name}_chain{sx}", body, (sx * 0.2, -0.05, 0.12), coll)
        for j in range(6):
            lk = L.torus(f"{name}_link{sx}_{j}", 0.028, 0.008, 10, 4, m_ch, piv, (0, 0, -0.045 * j), coll,
                         axis="X" if j % 2 else "Y")
        L.box(f"{name}_ball{sx}", (0.07, 0.07, 0.07), m_ch, piv, (0, 0, -0.3), coll, bevel=0.015)
        chains.append(piv)
    # Preisschild an einer Schnur
    tag = L.empty(f"{name}_tag", body, (0.16, -0.18, 0.56), coll)
    L.cyl(f"{name}_string", 0.004, 0.12, 4, L.mat("schnur", "#E9DFCC", 0.7), tag, (0, 0, -0.04), coll)
    L.box(f"{name}_card", (0.34, 0.01, 0.14), L.mat("tag_paper", "#F5F1E8", 0.6), tag, (0, 0, -0.17), coll, bevel=0.01)
    L.text(f"{name}_preis", preis, 0.07, L.mat("tag_ink", "#C0392B", 0.5), tag, (0, -0.008, -0.17), coll, extrude=0.003,
           font=L.font())
    return P(root=root, body=body, mat=m, mat2=m2, chains=chains, tag=tag, mats=[m, m2, m_ch])


def geist_schweben(T, g, f0, f1, seed=0, amp=0.06):
    """Schweben, Schimmern (Transparenz pulsiert), Ketten rasseln, Schild baumelt."""
    ph = random.Random(seed).uniform(0, 6.28)
    T.add(g.body, "location", lambda f: (0.02 * math.sin(f * 0.09 + ph), 0, amp * math.sin(f * 0.13 + ph)), f0, f1)
    T.add(g.body, "rotation_euler", lambda f: (0.05 * math.sin(f * 0.11 + ph), 0.06 * math.sin(f * 0.07 + ph), 0), f0, f1)
    for k, piv in enumerate(g.chains):
        T.add(piv, "rotation_euler", lambda f, k=k: (0.35 * math.sin(f * 0.5 + k * 2 + ph) + 0.12 * math.sin(f * 1.7 + k),
                                                     0.25 * math.sin(f * 0.37 + k + ph), 0), f0, f1)
    T.add(g.tag, "rotation_euler", lambda f: (0.2 * math.sin(f * 0.3 + ph), 0.25 * math.sin(f * 0.21 + ph), 0), f0, f1)
    for m in g.mats[:2]:
        base = tuple(m.diffuse_color)
        T.set(m, "diffuse_color", lambda f, base=base: tuple(base[:3]) + (base[3] * (0.8 + 0.3 * math.sin(f * 0.23 + ph)),),
              f0, f1)


def glitzer(T, coll, name, origin, f0, n=26, seed=0, scale=1.0):
    """glitzer_partikel: goldene und tuerkise Funken, die nach oben stieben und verlöschen."""
    PR.burst(T, coll, f"{name}_g", "spark", origin, f0, n // 2, seed, speed=(0.6, 1.4), up=1.0, spread=1.0,
             gravity=-0.6, life=(16, 28), size=(0.7 * scale, 1.3 * scale), drag=1.5)
    PR.burst(T, coll, f"{name}_t", "sparkt", origin, f0 + 1, n - n // 2, seed + 1, speed=(0.5, 1.2), up=1.0,
             spread=1.0, gravity=-0.5, life=(16, 28), size=(0.7 * scale, 1.3 * scale), drag=1.5)


def aufloesen(T, coll, obj, f, loc, base=1.0, name="aufl", seed=0):
    """Objekt loest sich in Glitzer auf (schrumpft in 8 Frames)."""
    T.set(obj, "scale", lambda x: (base * (1 - ease_in((x - f) / 8)) * (1 + 0.15 * math.sin((x - f) * 1.5)),) * 3
          if x >= f else (base,) * 3, f - 1, f + 9)
    glitzer(T, coll, name, tuple(loc), f, 28, seed)


# ------------------------------------------------------------------ Ordner 'KONTOAUSZUEGE 2026'
def ordner_kontoauszuege(coll, name):
    root = L.empty(name, coll=coll)
    m = L.mat("ordner", "#2E5FA8", 0.55)
    L.box(f"{name}_cover", (0.36, 0.09, 0.46), m, root, (0, 0, 0.23), coll, bevel=0.01)
    L.box(f"{name}_pages", (0.33, 0.075, 0.43), L.mat("paper", "#F5F1E8", 0.7), root, (0.012, -0.005, 0.23), coll)
    L.box(f"{name}_label", (0.3, 0.012, 0.16), L.mat("ordner_label", "#F5F1E8", 0.6), root, (0, -0.048, 0.27), coll)
    L.text(f"{name}_t1", "KONTOAUSZÜGE", 0.042, L.mat("ordner_ink", "#141228", 0.5), root, (0, -0.056, 0.295), coll,
           extrude=0.002, font=L.font())
    L.text(f"{name}_t2", "2026", 0.06, L.mat("ordner_ink", "#141228", 0.5), root, (0, -0.056, 0.235), coll,
           extrude=0.002, font=L.font())
    L.cyl(f"{name}_ring", 0.022, 0.012, 10, L.mat("metal", L.METAL, 0.4, metallic=0.6), root, (0, -0.046, 0.08), coll,
          axis="Y")
    return P(root=root)


def blaetter_einsaugen(T, coll, name, start_fn, target, f0, n=10, seed=3, dur=12):
    """Blaetter fliegen aus dem Ordner und werden in den Bildschirm gesaugt (schrumpfen, beschleunigen)."""
    r = random.Random(seed)
    m = L.mat("paper", "#F5F1E8", 0.7)
    m_l = L.mat("paperline", "#9AA0B8", 0.6)
    for i in range(n):
        o = L.empty(f"{name}{i}", None, (0, 0, -50), coll)
        L.box(f"{name}{i}_m", (0.16, 0.004, 0.21), m, o, (0, 0, 0), coll)
        for j in range(3):
            L.box(f"{name}{i}_l{j}", (0.11, 0.006, 0.012), m_l, o, (0, -0.003, 0.05 - 0.04 * j), coll)
        t0 = f0 + i * 1.6
        bend = Vector((r.uniform(-0.25, 0.25), r.uniform(-0.2, 0.0), r.uniform(0.15, 0.45)))
        spin = r.uniform(-6, 6)

        def loc(f, t0=t0, bend=bend):
            t = ease_in(min(1.0, max(0.0, (f - t0) / dur)))
            a = Vector(start_fn(t0))
            b = Vector(target)
            return tuple(a.lerp(b, t) + bend * math.sin(math.pi * t))
        T.set(o, "location", loc, t0 - 1, t0 + dur + 1)
        T.set(o, "rotation_euler", lambda f, t0=t0, spin=spin: (0.4 * math.sin(f * 0.5), spin * (f - t0) * 0.05, spin * (f - t0) * 0.03),
              t0 - 1, t0 + dur + 1)
        T.set(o, "scale", lambda f, t0=t0: ((1 - 0.9 * ease_in((f - t0) / dur)) * pop(f, t0, 3),) * 3 if t0 <= f <= t0 + dur
              else (0, 0, 0), t0 - 1, t0 + dur + 1)
        T.set(o, "scale", lambda f: (0, 0, 0), 0, 1)


# ------------------------------------------------------------------ Kategorien-Faecher
KATEGORIEN = ["MEHL & ZUTATEN", "PERSONAL", "ENERGIE", "MIETE", "ABOS & VERTRÄGE"]
FARBEN = ["#F2B45A", "#6B55C9", "#FFE14D", "#2E8CDC", "#2EE6D6"]


def kategorien_faecher(coll, name, labels=KATEGORIEN, pitch=0.62):
    root = L.empty(name, coll=coll)
    tops = []
    m_box = L.mat("fach", "#2B2750", 0.5)
    n = len(labels)
    for k, (lab, col) in enumerate(zip(labels, FARBEN)):
        x = (k - (n - 1) / 2) * pitch
        b = L.empty(f"{name}_fach{k}", root, (x, 0, 0), coll)
        L.box(f"{name}_back{k}", (0.52, 0.04, 0.42), m_box, b, (0, 0.2, 0.21), coll)
        L.box(f"{name}_bottom{k}", (0.52, 0.42, 0.04), m_box, b, (0, 0, 0.02), coll)
        for sx in (-1, 1):
            L.box(f"{name}_side{k}{sx}", (0.04, 0.42, 0.42), m_box, b, (sx * 0.26, 0, 0.21), coll)
        L.box(f"{name}_front{k}", (0.52, 0.04, 0.16), m_box, b, (0, -0.2, 0.08), coll)
        L.box(f"{name}_stripe{k}", (0.52, 0.045, 0.03), L.mat(f"fachstreif{col}", col, 0.4, emit=col, strength=2.5), b,
              (0, -0.2, 0.17), coll)
        plate = L.box(f"{name}_plate{k}", (0.58, 0.03, 0.15), L.mat("fachschild", "#F5F1E8", 0.6), b, (0, -0.24, -0.06),
                      coll, bevel=0.01)
        lines = lab.split(" & ") if " & " in lab else [lab]
        sz = 0.06 if len(lab) < 10 else 0.05
        if len(lines) == 2:
            L.text(f"{name}_lab{k}a", lines[0] + " &", 0.048, L.mat("fachink", "#141228", 0.5), b, (0, -0.258, -0.04),
                   coll, extrude=0.002, font=L.font())
            L.text(f"{name}_lab{k}b", lines[1], 0.048, L.mat("fachink", "#141228", 0.5), b, (0, -0.258, -0.09), coll,
                   extrude=0.002, font=L.font())
        else:
            L.text(f"{name}_lab{k}", lab, sz, L.mat("fachink", "#141228", 0.5), b, (0, -0.258, -0.065), coll,
                   extrude=0.002, font=L.font())
        tops.append(b)
    return P(root=root, faecher=tops)


def kaertchen_tornado(T, coll, name, center, f0, f_split, ziele, n=90, seed=5, f_end=None, radius=0.8):
    """buchungs_kaertchen: Schwarm kleiner Karten wirbelt wie ein Tornado um center und fliegt dann in die Faecher."""
    r = random.Random(seed)
    c = Vector(center)
    mats = [L.mat(f"karte{col}", "#F5F1E8", 0.6) for col in FARBEN]
    m_str = [L.mat(f"kartestreif{col}", col, 0.5, emit=col, strength=1.5) for col in FARBEN]
    for i in range(n):
        k = i % 5
        o = L.empty(f"{name}{i}", None, (0, 0, -50), coll)
        L.box(f"{name}{i}_m", (0.07, 0.003, 0.045), mats[k], o, (0, 0, 0), coll)
        L.box(f"{name}{i}_s", (0.07, 0.005, 0.01), m_str[k], o, (0, -0.002, 0.016), coll)
        a0 = r.uniform(0, 6.28)
        h = r.uniform(-0.9, 0.9)
        rad = radius * (0.55 + 0.45 * (h + 0.9) / 1.8) * r.uniform(0.85, 1.15)
        sp = r.uniform(0.25, 0.38)
        t_in = f0 + r.uniform(0, 10)
        t_go = f_split + (i % 18) * 0.9
        dst = Vector(ziele[k]) + Vector((r.uniform(-0.15, 0.15), r.uniform(-0.1, 0.1), r.uniform(0.0, 0.15)))

        def orbit(f, a0=a0, h=h, rad=rad, sp=sp):
            a = a0 + sp * (f - f0)
            return c + Vector((rad * math.cos(a), rad * 0.8 * math.sin(a), h + 0.05 * math.sin(f * 0.3 + a0)))

        def loc(f, t_go=t_go, dst=dst, orbit=orbit):
            if f < t_go:
                return tuple(orbit(f))
            t = ease_in_out(min(1.0, (f - t_go) / 12))
            p = orbit(t_go).lerp(dst, t)
            p.z += 0.4 * math.sin(math.pi * t)
            return tuple(p)
        end = f_end if f_end is not None else t_go + 40
        T.set(o, "location", loc, t_in - 1, t_go + 14)
        T.set(o, "rotation_euler", lambda f, a0=a0: (f * 0.21 + a0, f * 0.13, f * 0.3 + a0), t_in - 1, t_go + 14)
        T.set(o, "scale", lambda f, t_in=t_in, t_go=t_go, end=end: (pop(f, t_in, 5) * (1 if f < t_go + 12 else unpop(f, t_go + 12, 5)),) * 3
              if f < end else (0, 0, 0), t_in - 1, t_go + 20)
        T.set(o, "scale", lambda f: (0, 0, 0), 0, 1)


# ------------------------------------------------------------------ Warnpunkt (pulsiert, platzt auf)
def warnpunkt_rot(coll, name):
    root = L.empty(name, coll=coll)
    m = L.unique_mat(L.mat("warn", RED, 0.35, emit=RED, strength=5.0), f"{name}_mat")
    core = L.ico(f"{name}_core", 0.11, 2, (1, 1, 1), m, root, (0, 0, 0), coll)
    halo = L.ico(f"{name}_halo", 0.17, 2, (1, 1, 1), L.mat("warnhalo", RED, 0.3, emit=RED, strength=2.0, alpha=0.25), root,
                 (0, 0, 0), coll)
    L.text(f"{name}_bang", "!", 0.13, L.mat("warnink", "#FFFFFF", 0.4, emit="#FFFFFF", strength=3.0), root,
           (0, -0.115, -0.045), coll, extrude=0.01, font=L.font())
    return P(root=root, core=core, halo=halo, mat=m)


def warnpunkt_pulsieren(T, w, f0, f1, seed=0):
    ph = random.Random(seed).uniform(0, 6.28)
    T.set(w.halo, "scale", lambda f: (1 + 0.35 * (0.5 + 0.5 * math.sin(f * 0.45 + ph)),) * 3, f0, f1)
    T.set(w.core, "scale", lambda f: (1 + 0.08 * math.sin(f * 0.45 + ph),) * 3, f0, f1)


def warnpunkt_platzen(T, coll, w, f, loc, seed=0):
    T.set(w.root, "scale", lambda x: ((1 + 0.6 * ease_out((x - f) / 4)) * (1 - ease_in((x - f) / 5)),) * 3 if x >= f else (1, 1, 1),
          f - 1, f + 6)
    PR.burst(T, coll, f"{w.root.name}_pl", "spark", tuple(loc), f + 1, 14, 700 + seed, speed=(1.0, 2.0), up=0.4,
             gravity=-1.5, life=(10, 16), size=(0.8, 1.2))
    PR.shock_ring(T, coll, f"{w.root.name}_ring", tuple(loc), f + 1, dur=10, r_end=0.6, axis="Y", color=RED)


# ------------------------------------------------------------------ Software-Box 'KASSE PRO'
def software_box(coll, name, text="KASSE PRO", geist=False):
    root = L.empty(name, coll=coll)
    if geist:
        m = _ghost_mat(name, 0.5)
        m_s = m
        m_t = L.unique_mat(L.mat("geist2", "#D8F2FF", 0.3, emit="#D8F2FF", strength=3.0, alpha=0.6), f"{name}_tmat")
    else:
        m = L.mat("swbox", "#2E8CDC", 0.45)
        m_s = L.mat("swbox_stripe", "#FFE14D", 0.45, emit="#FFE14D", strength=1.5)
        m_t = L.mat("swbox_ink", "#FFFFFF", 0.4, emit="#FFFFFF", strength=1.5)
    L.box(f"{name}_box", (0.34, 0.1, 0.46), m, root, (0, 0, 0.23), coll, bevel=0.012)
    L.box(f"{name}_stripe", (0.34, 0.105, 0.06), m_s, root, (0, 0, 0.38), coll)
    L.text(f"{name}_t1", text, 0.06, m_t, root, (0, -0.056, 0.25), coll, extrude=0.003, font=L.font())
    L.cyl(f"{name}_disc", 0.07, 0.006, 16, m_t if geist else L.mat("swdisc", "#C9D6E8", 0.3, metallic=0.6), root,
          (0, -0.053, 0.11), coll, axis="Y")
    return P(root=root, mats=[m] if geist else [])


# ------------------------------------------------------------------ Stromzaehler (dreht schnell, Stempel)
def stromzaehler(coll, name, stempel_text="AUTOMATISCH VERLÄNGERT"):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_case", (0.4, 0.16, 0.56), L.mat("zaehler_case", "#D9D6CF", 0.55), root, (0, 0, 0.28), coll, bevel=0.02)
    L.box(f"{name}_window", (0.32, 0.02, 0.22), L.mat("zaehler_glass", "#1B1830", 0.3), root, (0, -0.08, 0.38), coll)
    disc = L.empty(f"{name}_disc", root, (0, -0.06, 0.32), coll)
    L.cyl(f"{name}_discm", 0.13, 0.012, 20, L.mat("zaehler_disc", "#C9D6E8", 0.35, metallic=0.6), disc, (0, 0, 0), coll)
    L.box(f"{name}_mark", (0.03, 0.02, 0.014), L.mat("zaehler_mark", RED, 0.4, emit=RED, strength=2.0), disc, (0.11, 0, 0.004),
          coll)
    L.text(f"{name}_kwh", "kWh", 0.05, L.mat("zaehler_ink", "#141228", 0.5), root, (0, -0.082, 0.18), coll, extrude=0.002,
           font=L.font())
    L.text(f"{name}_digits", "0 4 7 3 9", 0.06, L.mat("zaehler_dig", "#FFFFFF", 0.4, emit="#FFFFFF", strength=2.0), root,
           (0, -0.092, 0.44), coll, extrude=0.002, font=L.font())
    imp = L.empty(f"{name}_abdruck", root, (0, -0.085, 0.1), coll)
    imp.rotation_euler = (0, math.radians(-12), 0)
    m_ink = L.mat("stempelrot", "#E0303C", 0.5, emit="#E0303C", strength=1.0)
    L.box(f"{name}_rahmen", (0.46, 0.004, 0.12), m_ink, imp, (0, 0, 0), coll)
    L.box(f"{name}_innen", (0.43, 0.006, 0.09), L.mat("stempelpapier", "#F5F1E8", 0.6), imp, (0, -0.002, 0), coll)
    lines = stempel_text.split(" ")
    L.text(f"{name}_st1", lines[0], 0.036, m_ink, imp, (0, -0.006, 0.018), coll, extrude=0.002, font=L.font())
    L.text(f"{name}_st2", " ".join(lines[1:]), 0.036, m_ink, imp, (0, -0.006, -0.024), coll, extrude=0.002, font=L.font())
    return P(root=root, disc=disc, abdruck=imp)


def zaehler_drehen(T, sz, f0, f1, speed=0.9):
    T.set(sz.disc, "rotation_euler", lambda f: (0, 0, speed * (f - f0) * (1 + 0.5 * min(1, (f - f0) / 20))), f0, f1)


# ------------------------------------------------------------------ Briefumschlag 'KUENDIGUNG'
def briefumschlag_kuendigung(coll, name):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_env", (0.3, 0.012, 0.19), L.mat("env_paper", "#F5F1E8", 0.6), root, (0, 0, 0), coll)
    L.poly_flat(f"{name}_flap", [(-0.15, 0.095), (0.15, 0.095), (0, -0.01)], 0.004, L.mat("env_flap", "#E3D8C3", 0.6), root,
                (0, -0.008, 0), coll)
    L.text(f"{name}_lab", "KÜNDIGUNG", 0.042, L.mat("env_ink", "#C0392B", 0.5), root, (0, -0.012, -0.055), coll,
           extrude=0.002, font=L.font())
    return P(root=root)


def umschlag_fliegen(T, u, start, ziel, f0, dur=22, seed=0):
    r = random.Random(seed)
    up = r.uniform(0.3, 0.6)

    def loc(f):
        t = ease_out(min(1.0, max(0.0, (f - f0) / dur)))
        p = Vector(start).lerp(Vector(ziel), t)
        p.z += up * math.sin(math.pi * t)
        return tuple(p)
    T.set(u.root, "location", loc, f0 - 1, f0 + dur + 1)
    T.set(u.root, "rotation_euler", lambda f: (0.3 * math.sin(f * 0.4 + seed), 0.5 * math.sin(f * 0.3), 0.2 * math.sin(f * 0.25)),
          f0 - 1, f0 + dur + 1)


# ------------------------------------------------------------------ Kaffeetasse (faellt, Kaffee spritzt)
def kaffeetasse(coll, name):
    root = L.empty(name, coll=coll)
    m = L.mat("tasse", "#F0EADD", 0.5)
    L.cyl(f"{name}_cup", 0.06, 0.1, 14, m, root, (0, 0, 0.05), coll, r2=0.07)
    L.torus(f"{name}_handle", 0.035, 0.012, 10, 4, m, root, (0.075, 0, 0.055), coll, axis="Y")
    coffee = L.cyl(f"{name}_coffee", 0.064, 0.008, 14, L.mat("kaffee", "#3B2416", 0.4), root, (0, 0, 0.092), coll)
    L.box(f"{name}_logo", (0.05, 0.004, 0.035), L.mat("tasse_logo", "#C0392B", 0.5), root, (0, -0.066, 0.05), coll)
    return P(root=root, coffee=coffee)


def kaffee_spritzer(T, coll, name, origin, f0, n=22, seed=0, slow=0.4, richtung=(0, -1, 0.6)):
    """Kaffeetropfen spritzen in Zeitlupe (slow < 1) aus origin."""
    r = random.Random(seed)
    m = L.mat("kaffeetropfen", "#5A341C", 0.35)
    d0 = Vector(richtung).normalized()
    for i in range(n):
        o = L.sphere(f"{name}{i}", r.uniform(0.012, 0.026), 6, 4, (1, 1, r.uniform(1.0, 1.6)), m, None, (0, 0, -50), coll)
        v = (d0 + Vector((r.uniform(-0.6, 0.6), r.uniform(-0.3, 0.3), r.uniform(-0.2, 0.5)))) * r.uniform(1.2, 2.4)
        life = r.uniform(26, 40)

        def loc(f, v=v):
            t = max(0.0, (f - f0) / FPS) * slow
            p = Vector(origin) + v * t + Vector((0, 0, -4.9 * t * t))
            return tuple(p)
        T.set(o, "location", loc, f0 - 1, f0 + life + 1)
        T.set(o, "scale", lambda f, life=life: (pop(f, f0, 3) * (1 if f < f0 + life - 6 else unpop(f, f0 + life - 6, 6)),) * 3,
              f0 - 1, f0 + life + 1)
        T.set(o, "scale", lambda f: (0, 0, 0), 0, 1)


# ------------------------------------------------------------------ Ladenfront (Hintergrund fuer Schulterblick)
def ladenfront(coll, name, breite=7.0, hoehe=4.2):
    """Vorderwand des Ladens (Blick von hinter der Theke): Fliesen-Farbe wie die Rueckwand, Schaufenster mit
    Tageslicht, Tuer mit Schild 'OFFEN'. Nur sichtbar, wenn die Kamera hinter Kalle steht."""
    root = L.empty(name, coll=coll)
    m_wall = L.mat("front_wall", "#DCCFB9", 0.6)
    m_wood = L.mat("wood_dark", L.WOOD_DARK, 0.65)
    m_glass = L.mat("door_glass", "#FFE7BF", 0.4, emit="#FFE7BF", strength=1.5)
    L.box(f"{name}_wall_l", (breite / 2 - 1.4, 0.1, hoehe), m_wall, root, (-(breite / 2 + 1.4) / 2, 0, hoehe / 2), coll)
    L.box(f"{name}_wall_r", (breite / 2 - 1.4, 0.1, hoehe), m_wall, root, ((breite / 2 + 1.4) / 2, 0, hoehe / 2), coll)
    L.box(f"{name}_wall_t", (2.8, 0.1, 1.2), m_wall, root, (0, 0, hoehe - 0.6), coll)
    L.box(f"{name}_wall_b", (2.8, 0.1, 0.7), L.mat("wainscot", "#3F5A78", 0.62), root, (0, 0, 0.35), coll)
    L.box(f"{name}_window", (2.8, 0.06, hoehe - 1.9), m_glass, root, (0, 0.02, 0.7 + (hoehe - 1.9) / 2), coll)
    for x in (-1.4, 0, 1.4):
        L.box(f"{name}_mull{x}", (0.08, 0.1, hoehe - 1.9), m_wood, root, (x, -0.02, 0.7 + (hoehe - 1.9) / 2), coll)
    L.box(f"{name}_sign", (0.9, 0.04, 0.3), L.mat("offen_sign", "#3DDC84", 0.4, emit="#3DDC84", strength=2.0), root,
          (-0.7, 0.05, 2.0), coll)
    L.text(f"{name}_offen", "OFFEN", 0.18, L.mat("offen_ink", "#FFFFFF", 0.4, emit="#FFFFFF", strength=2.0), root,
           (-0.7, 0.08, 1.99), coll, extrude=0.006, rot=(math.pi / 2, 0, math.pi), font=L.font())
    L.text(f"{name}_name", "BÄCKEREI KALLE", 0.2, L.mat("front_ink", "#5E3E2B", 0.6), root, (0.6, 0.08, 2.3), coll,
           extrude=0.008, rot=(math.pi / 2, 0, math.pi), font=L.font())
    return P(root=root)
