"""Theke mit Glasauslage: 3 Faecher (Brezel, Broetchen, Stollen), jedes zeigt die aktuelle Menge als kleine Stapel,
Preisschildchen an jedem Fach (Text aus der Regie), Klappschild '½ PREIS'. Zustaende: menge je Fach, halbpreis (aus/an)."""
import math

import look as L
import spielwelt as SW
import ware as WA
from anim import pop

INFO = {"name": "theke_auslage", "groesse": [3.6, 1.0, 1.3], "anker": "mitte_unten", "zustaende": ["menge(0-12 je Fach)", "halbpreis"],
        "beschreibung": "gleiche Theke wie in der echten Welt (Holz, Glas), 3 Faecher"}
FAECHER = ["brezel", "broetchen", "stollen"]


def bauen(coll, name, preise=("1,20 €", "0,40 €", "2,50 €"), **kw):
    root = L.empty(name, coll=coll)
    SW.rbox(f"{name}_korpus", (3.6, 0.9, 0.95), SW.m("theke_holz", "holz", 0.6), root, (0, 0, 0.48), coll, r=0.06)
    for x in (-1.2, 0, 1.2):
        L.box(f"{name}_paneel{x}", (1.0, 0.05, 0.6), SW.m("theke_front", "#F2E6CE", 0.6), root, (x, -0.47, 0.45), coll)
    SW.rbox(f"{name}_platte", (3.7, 1.0, 0.08), SW.m("theke_platte", "#B07A4A", 0.5), root, (0, 0, 0.98), coll, r=0.03)
    L.box(f"{name}_glas", (3.5, 0.04, 0.42), SW.m("glas", "#D9F0FA", 0.1, alpha=0.3), root, (0, -0.4, 1.23), coll)
    L.box(f"{name}_glasd", (3.5, 0.8, 0.03), SW.m("glas", "#D9F0FA", 0.1, alpha=0.3), root, (0, 0, 1.45), coll)
    stapel, schilder = [], []
    for j, art in enumerate(FAECHER):
        x = -1.2 + 1.2 * j
        L.box(f"{name}_trenn{j}", (0.04, 0.8, 0.44), SW.m("glas", "#D9F0FA", 0.1, alpha=0.3), root, (x + 0.6, 0, 1.24), coll)
        st = []
        for k in range(12):
            w = WA.bauen(coll, f"{name}_w{j}_{k}", art=art, s=1.1)
            w.root.parent = root
            w.root.location = (x - 0.3 + 0.3 * (k % 3), -0.15 + 0.25 * ((k // 3) % 2), 1.02 + 0.11 * (k // 6))
            st.append(w)
        stapel.append(st)
        sch = L.empty(f"{name}_ps{j}", root, (x, -0.46, 1.08), coll)
        SW.rbox(f"{name}_psb{j}", (0.62, 0.04, 0.24), SW.m("preisschild", "weiss", 0.5), sch, (0, 0, 0), coll, r=0.04)
        SW.text(f"{name}_pst{j}", preise[j], 0.15, SW.m("preis_ink", "#1E2A44", 0.5), sch, (0, -0.03, -0.05), coll)
        schilder.append(sch)
    hp = L.empty(f"{name}_halbpreis", root, (0, -0.48, 1.55), coll)
    SW.rbox(f"{name}_hpb", (1.2, 0.05, 0.4), SW.m("halbpreis", "gold", 0.4), hp, (0, 0, 0.2), coll, r=0.05)
    SW.text(f"{name}_hpt", "½ PREIS", 0.26, SW.m("halbpreis_ink", "#7A2E18", 0.5), hp, (0, -0.04, 0.11), coll)
    hp.scale = (0, 0, 0)
    return SW.P(root=root, stapel=stapel, schilder=schilder, halbpreis=hp)


def menge(T, a, fach, fn, f0, f1):
    """Fach 0..2 zeigt fn(f) Stueck (0..12) als Stapel."""
    for k, w in enumerate(a.stapel[fach]):
        T.set(w.root, "scale", lambda f, k=k: (1.1,) * 3 if k < round(fn(f)) else (0, 0, 0), f0, f1)


def halbpreis(T, a, f_an, f0, f1):
    T.set(a.halbpreis, "scale", lambda f: (1, 1, 1) if f >= f_an + 8 else ((pop(f, f_an, 8),) * 3 if f >= f_an else (0, 0, 0)), f0, f1)
    T.set(a.halbpreis, "rotation_euler", lambda f: (-math.pi / 2 * (1 - min(1.0, max(0.0, (f - f_an) / 10))), 0, 0), f0, f1)


def zustand(T, a, plan, f0, f1):
    """plan: {'mengen': [fn0, fn1, fn2], 'halbpreis': frame oder None}"""
    for j, fn in enumerate(plan.get("mengen", [])):
        menge(T, a, j, fn, f0, f1)
    if plan.get("halbpreis") is not None:
        halbpreis(T, a, plan["halbpreis"], f0, f1)
    else:
        a.halbpreis.scale = (0, 0, 0)
