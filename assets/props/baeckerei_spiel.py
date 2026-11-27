"""Requisiten fuer 'Diese Stadt ist ein Spiel' (folge-11-baeckerei-spiel).

Gleicher Low-Poly-Stil wie engine/props.py (Vorderseite -Y). Leuchten fuer Workbench ueber diffuse_color.
Wiederverwendet: schreibtischlampe und fenster_tageszeit (assets/props/viral.py), Spielwelt-Katalog (assets/spielwelt)
fuer das Studio-Modell.

  controller(coll, name)                 Gamepad (Griffe, Steuerkreuz, 4 Knoepfe, 2 Sticks); vibrieren(), verkehrt herum
                                         haltbar (Drehung um die Laengsachse, siehe halten())
  monitor_buero(coll, name)              Monitor auf Standfuss; das Display zeigt die Bildfolge der Screen-Ebene
                                         (assets/screens/baeckerei_spiel.py) per UV, wie laptop_display in viral.py
  schild_offen(coll, name)               Haengeschild an Kette, dreht sich zwischen 'GESCHLOSSEN' und 'OFFEN'
  spielstadt_modell(coll, name)          Studio-Fassung der Spielwelt: kleine Stadtplatte mit Kalles Laden, Kasse, Tonne
                                         'RESTE', rotem 'PLEITE'-Schild und Knopf 'NOCHMAL'; rueckspulen() setzt alles zurueck
"""
import math

import bpy
from mathutils import Vector

import look as L
import props as PR
from anim import ease_in_out, ease_out_back, clamp01, window

FPS = 30
P = PR.P
TURQ = "#2EE6D6"
NAVY = "#141228"
ROT = "#E2483F"


def _text(name, s, size, mat, parent, loc, coll, rot=(math.pi / 2, 0, 0), extrude=0.003, align="CENTER"):
    return L.text(name, s, size, mat, parent, loc, coll, extrude=extrude, rot=rot, font=L.font(), align=align)


# ------------------------------------------------------------------ Controller
def controller(coll, name):
    """Gamepad, Mitte im Ursprung, Oberseite +Z, Griffe nach -Y (zum Spieler)."""
    root = L.empty(name, coll=coll)
    body = L.empty(f"{name}_body", root, (0, 0, 0), coll)
    m = L.mat("ctrl_body", "#2B2E3E", 0.5)
    L.box(f"{name}_mitte", (0.15, 0.075, 0.035), m, body, (0, 0.0, 0), coll, bevel=0.015, seg=2)
    for sx in (-1, 1):
        g = L.sphere(f"{name}_griff{sx}", 0.045, 12, 8, (1.0, 1.35, 0.7), m, body, (sx * 0.068, -0.025, -0.004), coll)
        g.rotation_euler = (0, 0, sx * 0.35)
    m_dp = L.mat("ctrl_dpad", "#11131C", 0.5)
    L.box(f"{name}_dp1", (0.034, 0.011, 0.008), m_dp, body, (-0.05, 0.008, 0.02), coll)
    L.box(f"{name}_dp2", (0.011, 0.034, 0.008), m_dp, body, (-0.05, 0.008, 0.02), coll)
    knoepfe = []
    for k, (dx, dy, col) in enumerate([(0.05, 0.022, "#3DDC84"), (0.066, 0.008, "#E2483F"), (0.05, -0.006, "#3D7BD9"),
                                       (0.034, 0.008, "#F2C94C")]):
        knoepfe.append(L.cyl(f"{name}_kn{k}", 0.0075, 0.008, 10, L.mat(f"ctrl_kn{col}", col, 0.4), body, (dx, dy, 0.021), coll))
    for sx in (-1, 1):
        L.cyl(f"{name}_stick{sx}", 0.011, 0.014, 10, m_dp, body, (sx * 0.022, -0.022, 0.022), coll)
    led = L.box(f"{name}_led", (0.03, 0.004, 0.004), L.mat("ctrl_led", TURQ, 0.3, emit=TURQ, strength=2.5), body,
                (0, 0.038, 0.012), coll)
    return P(root=root, body=body, knoepfe=knoepfe, led=led)


def vibrieren(T, c, f0, dur=12, amp=0.006):
    """Kurzes Vibrieren (Rumpeln) ab f0."""
    T.add(c.body, "location", lambda f: (amp * math.sin(f * 4.1) * (1 - (f - f0) / dur), amp * 0.7 * math.cos(f * 5.3) * (1 - (f - f0) / dur),
                                         0), f0, f0 + dur)
    T.add(c.body, "rotation_euler", lambda f: (0, 0, 0.05 * math.sin(f * 4.7) * (1 - (f - f0) / dur)), f0, f0 + dur)


def knopf_druck(T, c, f, k=0):
    kn = c.knoepfe[k]
    T.add(kn, "location", lambda x: (0, 0, -0.004 * window(x, f, f + 5, 1, 2)), f - 1, f + 6)


def halten(T, c, hand_fn, f0, f1, verkehrt_fn=lambda f: 0.0, neigung=0.5):
    """Controller folgt hand_fn(f) (Weltposition zwischen den Haenden); verkehrt_fn(f) 0..1 dreht ihn um die
    Laengsachse (1 = Knoepfe nach unten, verkehrt herum)."""
    T.set(c.root, "location", lambda f: tuple(hand_fn(f)), f0, f1)
    T.set(c.root, "rotation_euler", lambda f: (neigung + math.pi * verkehrt_fn(f), 0, 0), f0, f1)


# ------------------------------------------------------------------ Monitor im Buero
def monitor_buero(coll, name, breite=0.78, aspect=1280 / 720):
    """Flachbildschirm auf Standfuss (Display -Y). Das Display bekommt das Material 'screen_display' (Bildfolge der
    Screen-Ebene) mit passender UV, falls vorhanden, sonst ein dunkles Glas."""
    root = L.empty(name, coll=coll)
    h = breite / aspect
    m = L.mat("mon_body", "#1E2130", 0.45)
    L.box(f"{name}_fuss", (0.26, 0.2, 0.02), m, root, (0, 0.04, 0.01), coll, bevel=0.008)
    L.box(f"{name}_hals", (0.05, 0.03, 0.26), m, root, (0, 0.06, 0.14), coll)
    kopf = L.empty(f"{name}_kopf", root, (0, 0.03, 0.28 + h / 2), coll)
    L.box(f"{name}_rahmen", (breite + 0.04, 0.035, h + 0.04), m, kopf, (0, 0.0, 0), coll, bevel=0.01)
    disp = L.box(f"{name}_display", (breite, 0.004, h), L.mat("mon_glas", "#0D1020", 0.2), kopf, (0, -0.019, 0), coll)
    L.box(f"{name}_led", (0.012, 0.004, 0.006), L.mat("mon_led", TURQ, 0.3, emit=TURQ, strength=2.5), kopf,
          (breite / 2 - 0.02, -0.02, -h / 2 - 0.012), coll)
    sm = bpy.data.materials.get("screen_display")
    if sm is not None:
        me = disp.data
        me.materials.clear()
        me.materials.append(sm)
        uv = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv = (0.5 + v.x / breite, 0.5 + v.z / h)
    return P(root=root, kopf=kopf, display=disp, breite=breite, hoehe=h)


def display_mitte(mon):
    """Weltposition der Display-Mitte und Normale (zur Kamera) fuer kameras.ins_spiel/aus_spiel."""
    mw = mon.display.matrix_world
    return mw.translation.copy(), (mw.to_3x3() @ Vector((0, -1, 0))).normalized()


# ------------------------------------------------------------------ Schild GESCHLOSSEN / OFFEN
def schild_offen(coll, name):
    """Haengeschild (Kette oben), Vorderseite -Y 'GESCHLOSSEN', Rueckseite 'OFFEN'. drehen() wendet es."""
    root = L.empty(name, coll=coll)
    m_k = L.mat("so_kette", "#8A8EA6", 0.4, metallic=0.4)
    for sx in (-1, 1):
        k = L.cyl(f"{name}_kette{sx}", 0.004, 0.16, 6, m_k, root, (sx * 0.07, 0, -0.07), coll)
        k.rotation_euler = (0, sx * 0.45, 0)
    L.sphere(f"{name}_haken", 0.012, 8, 5, (1, 1, 1), m_k, root, (0, 0, 0), coll)
    brett = L.empty(f"{name}_brett", root, (0, 0, -0.2), coll)
    L.box(f"{name}_b", (0.36, 0.014, 0.13), L.mat("so_holz", "#7A4E2E", 0.6), brett, (0, 0, 0), coll, bevel=0.008)
    L.box(f"{name}_vf", (0.33, 0.004, 0.1), L.mat("so_rot", "#C9473F", 0.5), brett, (0, -0.0085, 0), coll)
    L.box(f"{name}_rf", (0.33, 0.004, 0.1), L.mat("so_gruen", "#3E9A5E", 0.5), brett, (0, 0.0085, 0), coll)
    _text(f"{name}_t_zu", "GESCHLOSSEN", 0.04, L.mat("so_ink", "#FBF8F0", 0.5), brett, (0, -0.011, -0.014), coll)
    _text(f"{name}_t_auf", "OFFEN", 0.06, L.mat("so_ink", "#FBF8F0", 0.5), brett, (0, 0.011, -0.02), coll,
          rot=(math.pi / 2, 0, math.pi))
    return P(root=root, brett=brett)


def drehen(T, s, f0, dur=16, f1=None):
    """Schild um 180 Grad wenden (GESCHLOSSEN -> OFFEN), mit Nachschwingen."""
    def rz(f):
        t = clamp01((f - f0) / dur)
        nach = 0.18 * math.sin((f - f0 - dur) * 0.5) * math.exp(-(f - f0 - dur) / 10) if f > f0 + dur else 0.0
        return (0, 0, math.pi * ease_out_back(t, 1.4) + nach)
    T.set(s.brett, "rotation_euler", rz, f0 - 1, f1 if f1 is not None else f0 + dur + 40)


# ------------------------------------------------------------------ Studio-Modell der Spielstadt
def spielstadt_modell(coll, name, s=0.06):
    """Kleine schwebende Spielstadt (Massstab s) aus dem Spielwelt-Katalog, ohne Outlines (das Studio rendert ohne
    Spiel-Stil). Dazu rotes 'PLEITE'-Schild und Knopf 'NOCHMAL'. Rueckgabe mit Teilen fuer rueckspulen()."""
    import spielwelt as SW
    root = L.empty(name, coll=coll)
    welt = L.empty(f"{name}_welt", root, (0, 0, 0), coll)
    welt.scale = (s, s, s)
    SW.rbox(f"{name}_platte", (14, 12, 0.6), SW.m("gras", "gras", 0.8), welt, (0, 0, -0.3), coll, r=0.5, seg=3)
    SW.rbox(f"{name}_rand", (14.4, 12.4, 0.8), SW.m("erde", "erde", 0.8), welt, (0, 0, -0.62), coll, r=0.4)
    L.box(f"{name}_fluss", (2.0, 12.2, 0.06), SW.m("wasser", "wasser", 0.25), welt, (1.6, 0, 0.02), coll)
    L.box(f"{name}_strasse", (14, 1.3, 0.05), SW.m("strasse", "strasse", 0.7), welt, (0, -1.6, 0.025), coll)
    kl = SW.katalog("kalles_laden").bauen(coll, f"{name}_laden")
    kl.root.parent = welt
    kl.root.location = (-3.2, -3.8, 0)
    for k, (x, y) in enumerate([(-5.0, 2.5), (-2.8, 3.2), (-0.6, 2.6)]):
        h = SW.katalog("fachwerkhaus").bauen(coll, f"{name}_fw{k}", farbe=k, hoehe=1.5 + 0.2 * k)
        h.root.parent = welt
        h.root.location = (x, y, 0)
    for k, (x, y) in enumerate([(4.4, 2.6), (4.6, -3.6)]):
        h = SW.katalog("wuerfelhaus").bauen(coll, f"{name}_wh{k}")
        h.root.parent = welt
        h.root.location = (x, y, 0)
    for k, (x, y) in enumerate([(-5.8, -4.6), (5.8, 0.2), (3.2, 4.6), (-1.2, -4.8)]):
        b = SW.katalog("baum").bauen(coll, f"{name}_baum{k}", s=0.9)
        b.root.parent = welt
        b.root.location = (x, y, 0)
    to = SW.katalog("tonne_reste").bauen(coll, f"{name}_tonne")
    to.root.parent = welt
    to.root.location = (-0.8, -3.6, 0)
    to.root.scale = (1.4, 1.4, 1.4)
    ka = SW.katalog("kasse").bauen(coll, f"{name}_kasse")
    ka.root.parent = welt
    ka.root.location = (0.4, -3.9, 0)
    ka.root.scale = (1.6, 1.6, 1.6)
    mz = SW.katalog("muenz_pop").bauen(coll, f"{name}_muenzen", n=6)
    mz.root.parent = welt
    mz.root.location = (0.4, -3.9, 1.0)
    for teil in [kl, to, ka] + [o for o in []]:
        SW.zusammenfassen(teil)
    for o in list(welt.children):                     # Haeuser und Baeume (nur statische Teile)
        if o.name.startswith((f"{name}_fw", f"{name}_wh", f"{name}_baum")) and o.type == "EMPTY":
            SW.zusammenfassen(SW.P(root=o))
    # rotes Schild 'PLEITE' auf Stange, Knopf 'NOCHMAL'
    sch = L.empty(f"{name}_pleite", root, (0.0, 0.05, 0.36), coll)
    L.box(f"{name}_pl_b", (0.5, 0.02, 0.15), L.mat("mod_rot", ROT, 0.45, emit=ROT, strength=1.2), sch, (0, 0, 0), coll, bevel=0.02)
    _text(f"{name}_pl_t", "PLEITE", 0.1, L.mat("mod_weiss", "#FFFFFF", 0.4), sch, (0, -0.013, -0.033), coll)
    L.cyl(f"{name}_pl_st", 0.006, 0.3, 6, L.mat("mod_stange", "#8A8EA6", 0.4), sch, (0, 0.012, -0.2), coll)
    kn = L.empty(f"{name}_knopf", root, (0.33, -0.36, 0.06), coll)
    L.cyl(f"{name}_kn_s", 0.1, 0.035, 20, L.mat("mod_knsockel", "#1E2130", 0.5), kn, (0, 0, 0), coll)
    kp = L.cyl(f"{name}_kn_k", 0.08, 0.04, 20, L.mat("mod_gruen", "#3DDC84", 0.4, emit="#3DDC84", strength=1.2), kn,
               (0, 0, 0.03), coll)
    _text(f"{name}_kn_t", "NOCHMAL", 0.045, L.mat("mod_weiss", "#FFFFFF", 0.4), kn, (0, -0.105, -0.01), coll,
          rot=(math.pi / 2 - 0.5, 0, 0))
    # Rueckspul-Ring (tuerkis, nur waehrend des Zuruecksetzens)
    ring = L.empty(f"{name}_ring", root, (0, 0, 0.05), coll)
    m_r = L.mat("mod_ring", TURQ, 0.3, emit=TURQ, strength=2.5)
    L.torus(f"{name}_ring_t", 0.5, 0.008, 48, 4, m_r, ring, (0, 0, 0), coll)
    for k in range(3):
        a = k * 2 * math.pi / 3
        pf = L.cyl(f"{name}_ring_p{k}", 0.03, 0.06, 3, m_r, ring, (0.5 * math.cos(a), 0.5 * math.sin(a), 0), coll, r2=0.0)
        pf.rotation_euler = (math.pi / 2, 0, a + math.pi)
    ring.scale = (0, 0, 0)
    return P(root=root, welt=welt, tonne=to, kasse=ka, muenzen=mz, schild=sch, knopf=kn, knopf_kappe=kp, ring=ring)


def rueckspulen(T, mo, f_druck, dauer=24, f0=0, f1=None):
    """Knopf 'NOCHMAL' wird gedrueckt (f_druck): Rueckspul-Ring dreht sich rueckwaerts, die Tonne leert sich, Muenzen
    fliegen zurueck in die Kasse, das 'PLEITE'-Schild klappt weg. Vorher: Tonne voll, Deckel offen."""
    import spielwelt as SW
    f1 = f1 if f1 is not None else f_druck + dauer + 60
    voll = lambda f: 1.0 if f < f_druck + 4 else max(0.0, 1 - (f - f_druck - 4) / (dauer * 0.7))
    SW.katalog("tonne_reste").fuellstand(T, mo.tonne, voll, f0, f1)
    T.add(mo.knopf_kappe, "location", lambda f: (0, 0, -0.018 * window(f, f_druck - 2, f_druck + 6, 2, 4)), f_druck - 3, f_druck + 8)
    T.set(mo.ring, "scale", lambda f: (1, 1, 1) if f_druck + 2 <= f < f_druck + dauer + 6 else (0, 0, 0), f0, f1)
    T.set(mo.ring, "rotation_euler", lambda f: (0, 0, -(f - f_druck) * 0.35), f0, f1)
    T.set(mo.schild, "rotation_euler", lambda f: (-math.pi / 2 * ease_in_out(clamp01((f - f_druck - dauer * 0.5) / 8)), 0, 0), f0, f1)
    T.set(mo.schild, "scale", lambda f: (1, 1, 1) if f < f_druck + dauer * 0.5 + 8 else (0, 0, 0), f0, f1)
    # Muenzen fliegen rueckwaerts (von oben zurueck in die Kasse)
    for k, o in enumerate(mo.muenzen.muenzen):
        st = f_druck + 4 + 2 * k

        def loc(f, st=st, k=k):
            t = clamp01((f - st) / 10)
            return (0.6 * math.sin(k * 1.7) * (1 - t), 0.4 * math.cos(k * 1.3) * (1 - t), 2.2 * (1 - t))
        T.set(o, "location", loc, f0, f1)
        T.set(o, "scale", lambda f, st=st: (2.0, 2.0, 2.0) if st - 6 <= f < st + 10 else (0, 0, 0), f0, f1)
        T.set(o, "rotation_euler", lambda f: (0, 0, -f * 0.5), f0, f1)
    # die ganze Welt ruckelt beim Zuruecksetzen kurz (Rueckspul-Effekt)
    T.add(mo.welt, "location", lambda f: (0.004 * math.sin(f * 3.1), 0, 0.003 * math.sin(f * 4.3)), f_druck + 2, f_druck + dauer)
