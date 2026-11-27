"""Requisiten fuer 'Bytes Nachtschicht' (folge-08-nachtschicht).

Gleicher Low-Poly-Stil wie engine/props.py (Vorderseite -Y). Leuchten fuer Workbench ueber diffuse_color.
Wiederverwendet: stempel, flour_sack (Mehlsack), preisschild (engine/props.py), brezelblech (assets/props/viral.py).
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
GOLD = "#F2B45A"


def _text(name, s, size, mat, parent, loc, coll, rot=(math.pi / 2, 0, 0)):
    return L.text(name, s, size, mat, parent, loc, coll, extrude=0.003, rot=rot, font=L.font())


# ------------------------------------------------------------------ Bewerbungsmappe (grau zuklappen / golden leuchten)
_MAPPE_MATS = {}


def bewerbungsmappe(coll, name, text="BEWERBUNG", gold=False):
    """Mappe mit aufklappbarem Deckel (Pivot an der linken Kante). gold=True: eigenes Material, das golden leuchten
    kann, Haekchen und Aufschrift 'Gespraech mit Kalle' (zuschaltbar)."""
    root = L.empty(name, coll=coll)
    if gold:
        m = L.unique_mat(L.mat("mappe_blau", "#3D6FC2", 0.5), f"{name}_mat")
    else:
        if "blau" not in _MAPPE_MATS:
            _MAPPE_MATS["blau"] = L.unique_mat(L.mat("mappe_blau", "#3D6FC2", 0.5), "mappe_blau_alle")
        m = _MAPPE_MATS["blau"]
    L.box(f"{name}_back", (0.24, 0.012, 0.32), m, root, (0, 0.012, 0), coll)
    L.box(f"{name}_paper", (0.22, 0.01, 0.3), L.mat("paper", "#F5F1E8", 0.7), root, (0.005, 0.0, 0), coll)
    lid = L.empty(f"{name}_lid", root, (-0.12, -0.008, 0), coll)
    L.box(f"{name}_front", (0.24, 0.01, 0.32), m, lid, (0.12, 0, 0), coll)
    L.box(f"{name}_label", (0.16, 0.004, 0.06), L.mat("mappe_label", "#F5F1E8", 0.6), lid, (0.12, -0.007, 0.07), coll)
    _text(f"{name}_t", text, 0.026, L.mat("mappe_ink", "#141228", 0.5), lid, (0.12, -0.01, 0.065), coll)
    check = L.empty(f"{name}_check", root, (0.0, -0.04, -0.04), coll)
    gesp = L.empty(f"{name}_gesp", root, (0.0, -0.04, -0.03), coll)
    if gold:
        m_ok = L.mat("haken_gruen", "#3DDC84", 0.4, emit="#3DDC84", strength=3.0)
        L.poly_flat(f"{name}_checkm", [(-0.06, 0.0), (-0.02, -0.04), (0.07, 0.06), (0.05, 0.08), (-0.02, 0.0), (-0.045, 0.02)],
                    0.01, m_ok, check, (0, 0, 0), coll)
        L.box(f"{name}_gespbg", (0.22, 0.006, 0.07), L.mat("gesp_bg", "#141228", 0.5), gesp, (0, 0, 0), coll)
        _text(f"{name}_gesp1", "Gespräch", 0.03, L.mat("gesp_ink", GOLD, 0.4, emit=GOLD, strength=2.0), gesp,
              (0, -0.006, 0.012), coll)
        _text(f"{name}_gesp2", "mit Kalle", 0.03, L.mat("gesp_ink", GOLD, 0.4, emit=GOLD, strength=2.0), gesp,
              (0, -0.006, -0.02), coll)
    check.scale = (0, 0, 0)
    gesp.scale = (0, 0, 0)
    return P(root=root, lid=lid, mat=m, check=check, gesp=gesp)


def mappe_grau(T, mp, f):
    """Mappe klappt grau zu (Material der normalen Mappen wird grau)."""
    T.set(mp.lid, "rotation_euler", lambda x: (0, 0, -1.2 * (1 - ease_in_out((x - f) / 6))) if x >= f else (0, 0, -1.2), f - 1, f + 7)


def mappe_gold(T, mp, f):
    gold = L.srgb(GOLD)
    base = tuple(mp.mat.diffuse_color)
    hi = tuple(min(1.0, g * 1.25 + 0.1) for g in gold[:3]) + (1.0,)
    T.set(mp.mat, "diffuse_color", lambda x: tuple(b + (h - b) * ease_out((x - f) / 6) for b, h in zip(base, hi))
          if x >= f else base, 0, 10 ** 5)
    T.set(mp.check, "scale", lambda x: (1.4 * pop(x, f + 4, 6),) * 3 if x >= f + 3 else (0, 0, 0), 0, 10 ** 5)


# ------------------------------------------------------------------ Ermittlungs-Pinnwand
def ermittlungs_pinnwand(coll, name, foto="BÄCKEREI AM MARKTPLATZ", zettel=("Preise", "Öffnungszeiten", "Sortiment")):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_frame", (1.5, 0.06, 1.05), L.mat("wood_dark", L.WOOD_DARK, 0.65), root, (0, 0.02, 0), coll)
    L.box(f"{name}_cork", (1.4, 0.06, 0.95), L.mat("cork", "#B8895A", 0.85), root, (0, 0, 0), coll)
    # Low-Poly-Foto der Konkurrenz: Fassade mit Markise
    ph = L.empty(f"{name}_foto", root, (-0.28, -0.04, 0.12), coll)
    L.box(f"{name}_fotobg", (0.62, 0.01, 0.5), L.mat("foto_rand", "#F5F1E8", 0.6), ph, (0, 0, 0), coll)
    L.box(f"{name}_sky", (0.56, 0.012, 0.26), L.mat("foto_sky", "#9FD3EA", 0.6), ph, (0, -0.002, 0.08), coll)
    L.box(f"{name}_house", (0.4, 0.014, 0.28), L.mat("foto_house", "#E3B07A", 0.6), ph, (0, -0.004, -0.04), coll)
    for k in range(4):
        L.box(f"{name}_awning{k}", (0.1, 0.016, 0.06), L.mat(f"foto_awn{k % 2}", "#C0392B" if k % 2 else "#F5F1E8", 0.6),
              ph, (-0.15 + 0.1 * k, -0.006, 0.07), coll)
    L.box(f"{name}_door", (0.08, 0.016, 0.12), L.mat("foto_door", "#5E3E2B", 0.6), ph, (0, -0.006, -0.12), coll)
    L.box(f"{name}_caption", (0.6, 0.012, 0.09), L.mat("foto_cap", "#141228", 0.5), ph, (0, -0.004, -0.2), coll)
    _text(f"{name}_captxt", foto, 0.036, L.mat("foto_capink", "#FFFFFF", 0.4, emit="#FFFFFF", strength=1.5), ph,
          (0, -0.012, -0.2), coll)
    notes = []
    for k, z in enumerate(zettel):
        npiv = L.empty(f"{name}_note{k}", root, (0.42, -0.04, 0.3 - 0.3 * k), coll)
        L.box(f"{name}_notem{k}", (0.42, 0.01, 0.2), L.mat(f"note{k}", ["#F6E3B0", "#CDEFEA", "#F7D2C9"][k], 0.7), npiv,
              (0, 0, 0), coll)
        _text(f"{name}_notet{k}", z, 0.045, L.mat("note_ink", "#141228", 0.5), npiv, (0, -0.008, -0.01), coll)
        L.sphere(f"{name}_pinn{k}", 0.018, 6, 4, (1, 1, 1), L.mat("pinred", L.RED, 0.5), npiv, (-0.16, -0.012, 0.07), coll)
        notes.append(npiv)
    L.sphere(f"{name}_pinf", 0.02, 6, 4, (1, 1, 1), L.mat("pinred", L.RED, 0.5), root, (-0.04, -0.06, 0.34), coll)
    # rote Faeden vom Foto zu den Zetteln (Pivots, schwingen leicht)
    threads = []
    m_t = L.mat("faden_rot", "#E0303C", 0.5, emit="#E0303C", strength=1.0)
    a = Vector((-0.04, -0.06, 0.34))
    for k in range(3):
        b = Vector((0.26, -0.06, 0.37 - 0.3 * k))
        d = b - a
        piv = L.empty(f"{name}_thpiv{k}", root, tuple(a), coll)
        piv.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        L.cyl(f"{name}_thread{k}", 0.006, d.length, 4, m_t, piv, (0, 0, d.length / 2), coll)
        threads.append(piv)
    # Preisschild '1,10 €' (steckt am Foto, Byte zieht es heraus)
    tag = L.empty(f"{name}_tag", root, (-0.05, -0.07, -0.05), coll)
    L.box(f"{name}_tagm", (0.24, 0.01, 0.12), L.mat("tag_paper", "#F5F1E8", 0.6), tag, (0, 0, 0), coll, bevel=0.01)
    _text(f"{name}_tagt", "1,10 €", 0.07, L.mat("tag_ink", "#C0392B", 0.5), tag, (0, -0.008, -0.02), coll)
    return P(root=root, threads=threads, notes=notes, tag=tag)


def faeden_schwingen(T, pw, f0, f1, amp=0.04):
    for k, th in enumerate(pw.threads):
        T.add(th, "rotation_euler", lambda f, k=k: (amp * math.sin(f * 0.17 + k), amp * math.sin(f * 0.13 + 2 * k), 0), f0, f1)
    for k, n in enumerate(pw.notes):
        T.add(n, "rotation_euler", lambda f, k=k: (0, 0.03 * math.sin(f * 0.11 + k), 0), f0, f1)


def pinzette(coll, name):
    root = L.empty(name, coll=coll)
    m = L.mat("metal", L.METAL, 0.4, metallic=0.6)
    for sx in (-1, 1):
        o = L.box(f"{name}_arm{sx}", (0.012, 0.012, 0.16), m, root, (sx * 0.012, 0, 0.08), coll)
        o.rotation_euler = (0, sx * 0.08, 0)
    return P(root=root)


# ------------------------------------------------------------------ Sterne-Leiste (fuellt sich, Wert einstellbar)
def _stern_pts(r=0.07, ri=0.03):
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else ri
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return pts


def sterne_leiste(coll, name, label="Kalle", n=5):
    root = L.empty(name, coll=coll)
    m_leer = L.mat("stern_leer", "#4A4664", 0.5)
    m_gold = L.mat("stern_gold", "#FFD24D", 0.35, emit="#FFD24D", strength=3.0)
    L.box(f"{name}_bg", (0.92, 0.03, 0.3), L.mat("sterne_bg", "#1F1B3A", 0.5), root, (0.12, 0.03, 0), coll, bevel=0.03)
    fills = []
    for k in range(n):
        x = -0.24 + k * 0.17
        L.poly_flat(f"{name}_leer{k}", _stern_pts(), 0.02, m_leer, root, (x, 0, 0), coll)
        fp = L.empty(f"{name}_fillpiv{k}", root, (x - 0.07, -0.012, 0), coll)
        L.poly_flat(f"{name}_gold{k}", [(px + 0.07, pz) for px, pz in _stern_pts(0.074, 0.032)], 0.02, m_gold, fp, (0, 0, 0), coll)
        fp.scale = (0, 1, 1)
        fills.append(fp)
    _text(f"{name}_lab", label, 0.08, L.mat("sterne_lab", "#FFFFFF", 0.4, emit="#FFFFFF", strength=1.5), root,
          (-0.58, -0.02, -0.03), coll, rot=(math.pi / 2, 0, 0))
    return P(root=root, fills=fills)


def sterne_fuellen(T, sl, wert, f0, dt=7, cue=None):
    """Sterne fuellen sich nacheinander bis 'wert' (z. B. 4,8 -> vier volle, der fuenfte zu 80 %).
    cue(f) wird fuer jeden Stern aufgerufen (Pop)."""
    for k, fp in enumerate(sl.fills):
        anteil = max(0.0, min(1.0, wert - k))
        if anteil <= 0:
            continue
        fk = f0 + k * dt
        T.set(fp, "scale", lambda f, fk=fk, a=anteil: (a * ease_out_back(min(1.0, max(0.0, (f - fk) / 6)), 2.0), 1,
                                                       1 + 0.25 * window(f, fk, fk + 8, 2, 6)), fk - 1, fk + 9)
        T.set(fp, "scale", lambda f: (0, 1, 1), 0, 1)
        if cue:
            cue(fk + 2)


# ------------------------------------------------------------------ Auftrags-Papierflieger mit Stempel
def auftrags_papierflieger(coll, name):
    root = L.empty(name, coll=coll)
    m = L.mat("paper", "#F5F1E8", 0.7)
    body = L.empty(f"{name}_body", root, (0, 0, 0), coll)
    for sx in (-1, 1):
        L.poly_flat(f"{name}_wing{sx}", [(0, 0.16), (sx * 0.1, -0.1), (0, -0.06)], 0.004, m, body, (0, 0, 0), coll,
                    plane="XY")
    stamp = L.empty(f"{name}_stamp", body, (0.045, -0.02, 0.006), coll)
    L.box(f"{name}_stampm", (0.08, 0.05, 0.003), L.mat("stamp_gruen", "#2FB36A", 0.5, emit="#2FB36A", strength=1.0), stamp,
          (0, 0, 0), coll)
    L.text(f"{name}_stampt", "BESTÄTIGT", 0.012, L.mat("stamp_gruen_ink", "#FFFFFF", 0.4), stamp, (0, 0, 0.003), coll,
           extrude=0.001, rot=(0, 0, math.pi / 2), font=L.font())
    stamp.scale = (0, 0, 0)
    return P(root=root, body=body, stamp=stamp)


def auftrags_stapel(coll, name, n=12, label="AUFTRÄGE"):
    root = L.empty(name, coll=coll)
    r = random.Random(3)
    for k in range(n):
        o = L.box(f"{name}_b{k}", (0.24, 0.32, 0.012), L.mat("paper", "#F5F1E8", 0.7), root, (r.uniform(-0.01, 0.01),
                                                                                           r.uniform(-0.01, 0.01), 0.006 + 0.013 * k), coll)
        o.rotation_euler = (0, 0, r.uniform(-0.08, 0.08))
    lab = L.empty(f"{name}_lab", root, (0, -0.17, 0.08), coll)
    L.box(f"{name}_labbg", (0.26, 0.006, 0.07), L.mat("stack_label", "#2FB36A", 0.5), lab, (0, 0, 0), coll)
    _text(f"{name}_labt", label, 0.035, L.mat("stack_ink", "#FFFFFF", 0.4), lab, (0, -0.005, -0.01), coll)
    return P(root=root, lab=lab)


def mappen_stapel(coll, name, n=14, label="BEWERBUNGEN"):
    root = L.empty(name, coll=coll)
    r = random.Random(7)
    cols = ["#3D6FC2", "#C0392B", "#2FB36A", "#F2B45A", "#6C5BA8"]
    for k in range(n):
        o = L.box(f"{name}_b{k}", (0.25, 0.34, 0.025), L.mat(f"mappe_{cols[k % 5]}", cols[k % 5], 0.55), root,
                  (r.uniform(-0.015, 0.015), r.uniform(-0.015, 0.015), 0.0125 + 0.027 * k), coll)
        o.rotation_euler = (0, 0, r.uniform(-0.1, 0.1))
    lab = L.empty(f"{name}_lab", root, (0, -0.18, 0.1), coll)
    L.box(f"{name}_labbg", (0.3, 0.006, 0.07), L.mat("stack_label2", "#3D6FC2", 0.5), lab, (0, 0, 0), coll)
    _text(f"{name}_labt", label, 0.032, L.mat("stack_ink", "#FFFFFF", 0.4), lab, (0, -0.005, -0.01), coll)
    return P(root=root)


# ------------------------------------------------------------------ Thermoskanne
def thermoskanne(coll, name):
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_body", 0.06, 0.3, 12, L.mat("thermos", "#2E8C88", 0.4, metallic=0.3), root, (0, 0, 0.15), coll)
    L.cyl(f"{name}_cup", 0.065, 0.08, 12, L.mat("thermos_cup", "#C9CED8", 0.4, metallic=0.5), root, (0, 0, 0.34), coll)
    L.box(f"{name}_lab", (0.08, 0.004, 0.1), L.mat("thermos_lab", "#F5F1E8", 0.6), root, (0, -0.062, 0.15), coll)
    _text(f"{name}_labt", "KAFFEE", 0.022, L.mat("thermos_ink", "#141228", 0.5), root, (0, -0.066, 0.15), coll)
    return P(root=root)


# ------------------------------------------------------------------ Wanduhr (Backstube) mit '4:12'
def wanduhr_backstube(coll, name):
    clk = PR.wall_clock(coll, name, r=0.34)
    dig = L.empty(f"{name}_dig", clk.root, (0, -0.06, -0.5), coll)
    L.box(f"{name}_digbg", (0.42, 0.03, 0.16), L.mat("dig_bg", "#141228", 0.5), dig, (0, 0, 0), coll, bevel=0.02)
    t1 = _text(f"{name}_digt", "4:12", 0.12, L.mat("dig_rot", "#FF4D5A", 0.4, emit="#FF4D5A", strength=4.0), dig,
               (0, -0.02, -0.04), coll)
    t2 = _text(f"{name}_digt2", "18:00", 0.11, L.mat("dig_rot", "#FF4D5A", 0.4, emit="#FF4D5A", strength=4.0), dig,
               (0, -0.02, -0.04), coll)
    t2.scale = (0, 0, 0)
    return P(root=clk.root, hands=clk.hands, t412=t1, tnach=t2)


def uhr_stellen(T, u, fn, f0, f1):
    """fn(f) -> Minuten seit Mitternacht. Zeiger: Stunde und Minute (Grad im Uhrzeigersinn ab 12)."""
    T.set(u.hands[0], "rotation_euler", lambda f: (0, math.radians((fn(f) / 60.0) % 12 * 30), 0), f0, f1)
    T.set(u.hands[1], "rotation_euler", lambda f: (0, math.radians(fn(f) % 60 * 6), 0), f0, f1)


# ------------------------------------------------------------------ Bewertungskarte
def bewertungskarte(coll, name, zeilen=("Die Brezeln von Kalle", "schmecken wie früher", "bei Oma.")):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_card", (0.62, 0.012, 0.4), L.mat("karte_weiss", "#FFFFFF", 0.5), root, (0, 0, 0), coll, bevel=0.015)
    m_g = L.mat("stern_gold", "#FFD24D", 0.35, emit="#FFD24D", strength=3.0)
    for k in range(5):
        L.poly_flat(f"{name}_st{k}", _stern_pts(0.035, 0.015), 0.006, m_g, root, (-0.16 + k * 0.08, -0.01, 0.13), coll)
    for k, z in enumerate(zeilen):
        _text(f"{name}_z{k}", z, 0.045, L.mat("karte_ink", "#141228", 0.5), root, (0, -0.009, 0.03 - 0.075 * k), coll)
    return P(root=root)


# ------------------------------------------------------------------ Teigklumpen (kippt um)
def teigklumpen(coll, name):
    root = L.empty(name, coll=coll)
    body = L.empty(f"{name}_body", root, (0, 0, 0), coll)
    m = L.mat("dough", "#EBD3A8", 0.7)
    r = random.Random(4)
    L.sphere(f"{name}_m", 0.08, 10, 6, (1.1, 0.9, 1.3), m, body, (0.0, 0, 0.1), coll)
    for k in range(4):
        L.sphere(f"{name}_b{k}", r.uniform(0.035, 0.05), 8, 5, (1, 1, 1), m, body,
                 (r.uniform(-0.06, 0.06), r.uniform(-0.04, 0.04), r.uniform(0.08, 0.2)), coll)
    return P(root=root, body=body)


def klumpen_kippen(T, kl, f):
    T.set(kl.body, "rotation_euler", lambda x: (0, 1.4 * ease_in(min(1.0, (x - f) / 10)) * (1 + 0.08 * spring((x - f - 10) / FPS, 4, 0.3)
                                                                                           if x > f + 10 else 1), 0),
          f - 1, f + 30)
    T.set(kl.body, "scale", lambda x: (1 + 0.15 * window(x, f + 9, f + 18, 1, 6), 1, 1 - 0.15 * window(x, f + 9, f + 18, 1, 6)),
          f + 8, f + 19)


# ------------------------------------------------------------------ Holzscheit, Schuerzenhaken, Schluesselbund
def holzscheit(coll, name):
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_m", 0.065, 0.45, 7, L.mat("log", "#8A5A3A", 0.7), root, (0, 0, 0), coll, axis="X")
    for sx in (-1, 1):
        L.cyl(f"{name}_end{sx}", 0.06, 0.005, 7, L.mat("log_end", "#D9A866", 0.7), root, (sx * 0.226, 0, 0), coll, axis="X")
    return P(root=root)


def schuerzenhaken(coll, name, mit_schuerze=True):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_board", (0.5, 0.04, 0.12), L.mat("wood_dark", L.WOOD_DARK, 0.65), root, (0, 0, 0), coll, bevel=0.01)
    m_met = L.mat("metal", L.METAL, 0.4, metallic=0.6)
    for k in range(3):
        L.cyl(f"{name}_hook{k}", 0.012, 0.08, 6, m_met, root, (-0.15 + 0.15 * k, -0.05, 0), coll, axis="Y")
    _text(f"{name}_lab", "SCHÜRZEN", 0.035, L.mat("hook_ink", "#F5F1E8", 0.5), root, (0, -0.025, 0.035), coll)
    apron = L.empty(f"{name}_apron", root, (0, -0.07, -0.02), coll)
    m_a = L.mat("apron", L.APRON, 0.66)
    L.box(f"{name}_apronm", (0.42, 0.02, 0.62), m_a, apron, (0, 0, -0.36), coll, bevel=0.02)
    L.box(f"{name}_apronbib", (0.26, 0.02, 0.22), m_a, apron, (0, 0, -0.05), coll)
    L.box(f"{name}_apronpocket", (0.16, 0.022, 0.1), L.mat("apron_pocket", "#E3D8C3", 0.6), apron, (0.08, -0.004, -0.4), coll)
    apron.scale = (1, 1, 1) if mit_schuerze else (0, 0, 0)
    return P(root=root, apron=apron)


def schluesselbund(coll, name):
    root = L.empty(name, coll=coll)
    m = L.mat("metal_gold", L.GOLD, 0.4, metallic=0.7)
    L.torus(f"{name}_ring", 0.03, 0.005, 10, 4, m, root, (0, 0, 0), coll, axis="Y")
    for k in range(3):
        o = L.box(f"{name}_key{k}", (0.016, 0.006, 0.07), m, root, (-0.02 + 0.02 * k, 0, -0.06), coll)
        o.rotation_euler = (0, -0.3 + 0.3 * k, 0)
    return P(root=root)
