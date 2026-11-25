"""Filiale 2 am Bahnhof (kleinere Variante von Kalles Laden): gleiches Brezel-Schild, Bahnhofsuhr ueber der Tuer.
Zustaende: bauplatz (Bauzaun, Schild 'ZU VERMIETEN'), baustelle (Kran, Staubwolke, 0,5 s), eroeffnet (Laden, Konfetti)."""
import math
import random

import look as L
import props as PR
import spielwelt as SW
import _zustand as Z
from anim import pop

INFO = {"name": "filiale", "groesse": [2.4, 2.0, 3.0], "anker": "mitte_unten", "zustaende": ["bauplatz", "baustelle", "eroeffnet"],
        "beschreibung": "Bahnhofs-Laden, entsteht im Spiel"}


def bauen(coll, name, **kw):
    import kalles_laden as KL
    root = L.empty(name, coll=coll)
    platz = L.empty(f"{name}_platz", root, (0, 0, 0), coll)
    L.box(f"{name}_sand", (2.6, 2.2, 0.06), SW.m("sand", "#E3C98E", 0.8), platz, (0, 0, 0.03), coll)
    for k in range(9):
        a = k / 9 * 2 * math.pi
        L.box(f"{name}_zaun{k}", (0.9, 0.06, 0.55), SW.m("zaun", "#F2C94C", 0.5), platz,
              (1.2 * math.cos(a) if abs(math.cos(a)) > 0.7 else 1.2 * math.copysign(1, math.cos(a)) * abs(math.cos(a)),
               1.0 * math.sin(a), 0.3), coll).rotation_euler = (0, 0, a + math.pi / 2)
    L.box(f"{name}_pfahl", (0.08, 0.08, 1.1), SW.m("holz_d", "holz_d", 0.6), platz, (0, -1.15, 0.55), coll)
    SW.rbox(f"{name}_vermieten", (1.6, 0.06, 0.45), SW.m("weiss", "weiss", 0.5), platz, (0, -1.2, 1.05), coll, r=0.05)
    SW.text(f"{name}_vt", "ZU VERMIETEN", 0.17, SW.m("rot", "rot", 0.5), platz, (0, -1.24, 0.99), coll)
    kran = L.empty(f"{name}_kran", root, (1.0, 0.6, 0), coll)
    L.box(f"{name}_km", (0.18, 0.18, 3.2), SW.m("kran", "#F2C94C", 0.5), kran, (0, 0, 1.6), coll)
    L.box(f"{name}_ka", (2.4, 0.14, 0.14), SW.m("kran", "#F2C94C", 0.5), kran, (-0.8, 0, 3.15), coll)
    kran.scale = (0, 0, 0)
    laden = L.empty(f"{name}_laden", root, (0, 0, 0), coll)
    w, d, h = 2.0, 1.7, 1.6
    SW.rbox(f"{name}_b", (w, d, h), SW.m("kalle_wand", "creme", 0.7), laden, (0, 0, h / 2), coll, r=0.1)
    L.poly_flat(f"{name}_dach", [(-w / 2 - 0.15, 0), (w / 2 + 0.15, 0), (0, 0.8)], d + 0.2, SW.m("kalle_dach", "dach2", 0.6),
                laden, (0, 0, h), coll)
    for s_ in range(8):
        st = L.box(f"{name}_mk{s_}", (0.25, 0.55, 0.04), SW.m(f"kmk{s_ % 2}", ["rot", "weiss"][s_ % 2], 0.55), laden,
                   (-0.875 + 0.25 * s_, -1.05, 1.15), coll)
        st.rotation_euler = (-0.42, 0, 0)
    SW.rbox(f"{name}_tuer", (0.5, 0.06, 0.9), SW.m("tuer_rot", "rot", 0.6), laden, (0, -d / 2 - 0.03, 0.45), coll, r=0.06)
    uhr = L.empty(f"{name}_uhr", laden, (0, -d / 2 - 0.06, 1.42), coll)
    L.cyl(f"{name}_ub", 0.2, 0.06, 20, SW.m("weiss", "weiss", 0.5), uhr, (0, 0, 0), coll, axis="Y")
    L.torus(f"{name}_ur", 0.2, 0.03, 20, 4, SW.m("dunkel", "dunkel", 0.5), uhr, (0, 0, 0), coll, axis="Y")
    L.box(f"{name}_uz", (0.03, 0.02, 0.13), SW.m("dunkel", "dunkel", 0.5), uhr, (0, -0.04, 0.05), coll)
    KL.brezel_schild(coll, f"{name}_brezel", laden, (1.15, -0.5, 1.9), 0.65)
    laden.scale = (0, 0, 0)
    return SW.P(root=root, platz=platz, kran=kran, laden=laden)


def zustand(T, o, plan, f0, f1, coll=None):
    T.set(o.platz, "scale", lambda f: (1, 1, 1) if Z.aktiv(plan, f) == "bauplatz" else (0, 0, 0), f0, f1)
    T.set(o.kran, "scale", lambda f: (1, 1, 1) if Z.aktiv(plan, f) == "baustelle" else (0, 0, 0), f0, f1)
    T.set(o.kran, "rotation_euler", lambda f: (0, 0, 0.6 * math.sin(f * 0.3)), f0, f1)

    def lad(f):
        if Z.aktiv(plan, f) != "eroeffnet":
            return (0, 0, 0)
        return (pop(f, f - Z.seit(plan, f), 10),) * 3
    T.set(o.laden, "scale", lad, f0, f1)
    if coll is not None:
        for fr, z in plan:
            if z == "baustelle":
                PR.burst(T, coll, f"{o.root.name}_staub{fr}", "puff", tuple(o.root.location + SW.Vector((0, 0, 0.6))), fr, 22,
                         fr, speed=(1.0, 2.2), up=0.6, gravity=-0.3, life=(14, 20), size=(2.0, 3.5), drag=2.5, ring=True)
            if z == "eroeffnet":
                PR.burst(T, coll, f"{o.root.name}_konf{fr}", "confetti_#E2483F", tuple(o.root.location + SW.Vector((0, 0, 2.5))), fr + 2, 50,
                         fr + 7, speed=(2.0, 3.6), up=1.4, spread=1.2, gravity=-3.0, life=(30, 44), size=(2.0, 3.0), drag=1.4,
                         spin=10.0, flutter=0.6, wobble=0.04,
                         kinds=["confetti_#E2483F", "confetti_#FFD23F", "confetti_#3DDC84", "confetti_#3D7BD9", "confetti_#FBF8F0"])
