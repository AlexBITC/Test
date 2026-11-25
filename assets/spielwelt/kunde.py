"""Kunden in 5 Typen mit eigener Silhouette: pendler (Aktentasche, Kaffeebecher), oma (Einkaufstrolley, Dutt),
schueler (Rucksack, Kappe), joggerin (Stirnband, Pferdeschwanz), familie (zwei Grosse, ein Kind).
Laufen auf Wegpunkten (Gehweg -> Tuer -> Theke -> raus). Zustaende: laufen, warten, schirm (bei Regen)."""
import math

import look as L
import spielwelt as SW
import _chibi as CH

TYPEN = ["pendler", "oma", "schueler", "joggerin", "familie"]
INFO = {"name": "kunde", "groesse": [0.7, 0.5, 1.0], "anker": "mitte_unten", "zustaende": ["laufen", "warten", "schirm"],
        "typen": TYPEN, "beschreibung": "Kunde (typ als Parameter)"}


def _schirm(coll, name, parent, h):
    s = L.empty(f"{name}_schirm", parent, (0.12 * h, 0, 1.05 * h), coll)
    L.cyl(f"{name}_sd", 0.38 * h, 0.12 * h, 10, SW.m("schirm", "#3D7BD9", 0.5), s, (0, 0, 0.1 * h), coll, r2=0.05 * h)
    L.cyl(f"{name}_ss", 0.015 * h, 0.5 * h, 6, SW.m("dunkel", "dunkel", 0.5), s, (0, 0, -0.15 * h), coll)
    s.scale = (0, 0, 0)
    return s


def bauen(coll, name, typ="pendler", h=0.9, **kw):
    if typ == "familie":
        root = L.empty(name, coll=coll)
        teile = []
        for j, (dx, hh, hemd, haar, stil) in enumerate([(-0.34, h * 1.05, "#4E7AB8", "#4A3426", "kurz"),
                                                         (0.34, h * 0.98, "#D9824A", "#8A4A2A", "lang"),
                                                         (0.0, h * 0.62, "#F2C94C", "#E0B24A", "zoepfe")]):
            d = CH.koerper(coll, f"{name}_{j}", hemd, h=hh)
            CH.haar(coll, f"{name}_{j}", d, haar, stil)
            d["root"].parent = root
            d["root"].location = (dx, -0.08 * (j == 2), 0)
            teile.append(d)
        # Familie haelt sich an den Haenden: Kind in der Mitte, Arme leicht nach innen
        teile[0]["arm_l"].rotation_euler = (0, -0.5, 0)
        teile[1]["arm_r"].rotation_euler = (0, 0.5, 0)
        schirm = _schirm(coll, name, root, h)
        return SW.P(root=root, teile=teile, beine=[t["bein_l"] for t in teile] + [t["bein_r"] for t in teile], schirm=schirm, typ=typ)
    farben = {"pendler": "#5A6478", "oma": "#9A5BA8", "schueler": "#E2483F", "joggerin": "#F25C9A"}
    d = CH.koerper(coll, name, farben[typ], h=h, hose={"pendler": "#3A4050", "oma": "#6A5A7A", "schueler": "#3B4A6E",
                                                         "joggerin": "#2E2A33"}[typ])
    k, s, kr = d["kopf"], d["s"], d["kr"]
    if typ == "pendler":
        SW.rbox(f"{name}_tasche", (0.24 * s, 0.07 * s, 0.17 * s), SW.m("leder", "#6A4228", 0.6), d["arm_r"], (0, 0, -0.32 * s), coll, r=0.02)
        L.cyl(f"{name}_becher", 0.04 * s, 0.1 * s, 8, SW.m("becher", "#F5F1E8", 0.6), d["arm_l"], (0, -0.04 * s, -0.27 * s), coll)
        CH.haar(coll, name, d, "#3A2A22", "kurz")
        SW.rbox(f"{name}_kragen", (0.2 * s, 0.03 * s, 0.12 * s), SW.m("weiss", "weiss", 0.5), d["body"], (0, -0.135 * s, 0.55 * s), coll,
                r=0.02)
    elif typ == "oma":
        CH.haar(coll, name, d, "#E6E2E8", "dutt")
        for sx in (-1, 1):
            L.torus(f"{name}_brille{sx}", 0.05 * s, 0.008 * s, 12, 4, SW.m("brille", "#3A2A22", 0.5), k,
                    (sx * 0.11 * s, -kr * 0.98, kr * 1.05), coll, axis="Y")
        tr = L.empty(f"{name}_trolley", d["root"], (0.32 * s, -0.05 * s, 0), coll)
        SW.rbox(f"{name}_tb", (0.22 * s, 0.18 * s, 0.32 * s), SW.m("trolley", "#4E8A5A", 0.6), tr, (0, 0, 0.26 * s), coll, r=0.05)
        L.box(f"{name}_tg", (0.03 * s, 0.03 * s, 0.4 * s), SW.m("metall", "#8A8EA6", 0.4), tr, (0, 0.08 * s, 0.4 * s), coll)
        for x in (-0.08, 0.08):
            L.cyl(f"{name}_tr{x}", 0.05 * s, 0.03 * s, 8, SW.m("reifen", "#2E2A33", 0.6), tr, (x * s, 0, 0.05 * s), coll, axis="X")
    elif typ == "schueler":
        SW.rbox(f"{name}_rucksack", (0.42 * s, 0.22 * s, 0.4 * s), SW.m("rucksack", "#2EA36B", 0.6), d["body"], (0, 0.22 * s, 0.46 * s),
                coll, r=0.07)
        for sx in (-1, 1):
            L.box(f"{name}_gurt{sx}", (0.05 * s, 0.02 * s, 0.3 * s), SW.m("rucksack", "#2EA36B", 0.6), d["body"],
                  (sx * 0.1 * s, -0.135 * s, 0.47 * s), coll)
        CH.haar(coll, name, d, "#5A3A22", "kurz")
        L.sphere(f"{name}_kappe", kr * 1.1, 12, 6, (1, 1, 0.55), SW.m("kappe", "#3D7BD9", 0.6), k, (0, 0.02 * s, kr * 1.5), coll)
        L.box(f"{name}_schirmk", (0.22 * s, 0.18 * s, 0.03 * s), SW.m("kappe", "#3D7BD9", 0.6), k, (0, -kr * 0.95, kr * 1.55), coll)
    elif typ == "joggerin":
        CH.haar(coll, name, d, "#C99A4A", "kurz")
        L.torus(f"{name}_band", kr * 0.98, 0.03 * s, 16, 4, SW.m("stirnband", "#FFD23F", 0.5), k, (0, 0, kr * 1.45), coll)
        L.sphere(f"{name}_pferd", 0.08 * s, 8, 5, (1, 1, 1.8), SW.m("haar_b", "#C99A4A", 0.6), k, (0, kr * 0.95, kr * 1.3), coll)
    schirm = _schirm(coll, name, d["root"], h)
    return SW.P(root=d["root"], body=d["body"], beine=[d["bein_l"], d["bein_r"]], schirm=schirm, typ=typ)


def schirm_bei_regen(T, k, S, f0, f1):
    T.set(k.schirm, "scale", lambda f: (1, 1, 1) if S.wetter_an("regen", f) > 0.5 else (0, 0, 0), f0, f1)
