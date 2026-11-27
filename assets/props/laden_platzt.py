"""Requisiten fuer 'Ein Video – und der Laden platzt' (folge-13-laden-platzt).

Gleicher Low-Poly-Stil wie engine/props.py (Vorderseite -Y). Leuchten fuer Workbench ueber diffuse_color, keine Logos,
keine Markennamen.
Wiederverwendet: Kunde mit Handy (assets/props/viral.py: kunde_mit_handy), Herzchen (viral.herzchen), Papiertuete
(brezel_geheimnis.papiertuete), Squash & Stretch, Dampf, Mehlstaub, Lichtring, Byte-Lichtschein, Haken
(kalle_vermieter.py), Brezel und Partikel (props.pastry, props.burst).

  ladenseite          rechte Ladenwand mit offener Tuer und Schaufenster, draussen Gehweg, Strasse, Haeuser, Himmel
  kundenschlange      Low-Poly-Kunden auf einem Pfad (Theke -> Tuer -> Gehweg), wippen, einige mit Handy; koennen
                      rueckwaerts verschwinden und wieder hereinstroemen (schlange_bewegen)
  tuerglocke          Ladenglocke an Feder, bimmelt (bimmeln) oder haengt still
  kameralinse_byte    runde Linse vor Bytes Gesicht, Blende klappt auf, roter REC-Punkt blinkt
  brezel_schlingen    Teigstrang fliegt im Bogen, dreht sich in Zeitlupe, landet als Brezel (Mehlwolke, Glitzern)
  zeitleiste_clips    Filmstreifen mit Clip-Kacheln: Lichtschnitt, graue Kacheln fallen, drei rasten ein
  handy_hochkant      grosses Hochkant-Handy ohne Logo: Brezel-Video, Untertitel Wort fuer Wort, Noten, Titelzeile
  papierflieger_licht leuchtender Papierflieger (Flug mit Schraeglage, Lichtspur in der Regie)
  handy_vibriert      Handy flach auf dem Tisch, vibriert und wandert
  sprechblasen        kleine Sprechblasen steigen auf (zu viral.herzchen)
  wellenringe         mehrere tuerkise Lichtringe nacheinander
  mini_baeckerei      kleine Low-Poly-Baeckerei mit Markise und Brezelschild
  figuren_feld        kleine Figuren, poppen auf und drehen sich zur Baeckerei
  stempel             Stempel 'GESTERN' / 'HEUTE', klappt auf (Position in der Regie relativ zur Kamera)
  fragezeichen        graues Fragezeichen, poppt auf und loest sich auf
"""
import math
import random

from mathutils import Vector

import look as L
import props as PR
from anim import ease_in, ease_in_out, ease_out, ease_out_back, pop, unpop, clamp01, window, lerp

import viral as VP
import kalle_vermieter as KV

FPS = 30
P = PR.P
TURQ = "#2EE6D6"
GRUEN = "#3DDC84"
ROT = "#E5484D"
GOLD = "#F2B45A"
NAVY = "#141228"
WEISS = "#FBF8F0"
landen = KV.landen


def _text(name, s, size, mat, parent, loc, coll, rot=(math.pi / 2, 0, 0), extrude=0.004, align="CENTER"):
    return L.text(name, s, size, mat, parent, loc, coll, extrude=extrude, rot=rot, font=L.font(), align=align)


# ------------------------------------------------------------------ Ladenseite mit Tuer und Schaufenster
def ladenseite(coll, name, S, X=2.45):
    """Rechte Seitenwand der Theke bei x = X (Set-Koordinaten). Oeffnungen: Tuer y -1,9..-0,9 (h 2,35),
    Schaufenster y -0,6..1,7 (z 0,9..2,5). Draussen (x > X): Gehweg, Bordstein, Strasse, Haeuser, Himmel."""
    root = L.empty(name, coll=coll)
    root.location = S.p(0, 0, 0)
    import bpy
    tiles = bpy.data.materials.get("wall_tiles") or L.mat("lp_wand", "#DCCFB9", 0.55)
    wdark = L.mat("wood_dark", L.WOOD_DARK, 0.65)
    wain = L.mat("wainscot", "#3F5A78", 0.62)
    d = 0.14
    H = 8.0

    def wand(y0, y1, z0, z1, nm):
        L.box(f"{name}_{nm}", (d, y1 - y0, z1 - z0), tiles, root, (X, (y0 + y1) / 2, (z0 + z1) / 2), coll)

    wand(-6.5, -1.9, 0, H, "a")
    wand(-1.9, -0.9, 2.35, H, "sturz")
    wand(-0.9, -0.6, 0, H, "pfeiler")
    wand(-0.6, 1.7, 0, 0.9, "bruest")
    wand(-0.6, 1.7, 2.5, H, "oben")
    wand(1.7, 2.5, 0, H, "e")
    L.box(f"{name}_rueckwand_oben", (14, 0.05, 4.0), tiles, root, (0, 2.47, 7.9), coll)   # Rueckwand nach oben verlaengert
    # Lambris innen (wie die Rueckwand)
    for y0, y1 in ((-6.5, -1.9), (-0.9, -0.6), (-0.6, 1.7), (1.7, 2.45)):
        L.box(f"{name}_lam{y0}", (0.04, y1 - y0, 0.9), wain, root, (X - d / 2 - 0.02, (y0 + y1) / 2, 0.45), coll)
    # Tuerrahmen und offener Tuerfluegel (nach aussen geschwungen)
    for nm, sz, lo in (("tl", (0.2, 0.1, 2.45), (X, -1.95, 1.225)), ("tr", (0.2, 0.1, 2.45), (X, -0.85, 1.225)),
                       ("tt", (0.2, 1.2, 0.12), (X, -1.4, 2.4))):
        L.box(f"{name}_{nm}", sz, wdark, root, lo, coll)
    tuer = L.empty(f"{name}_tuer", root, (X + 0.08, -1.9, 0), coll)
    L.box(f"{name}_tuerb", (0.06, 0.95, 2.3), L.mat("door_panel", "#4E6B8A", 0.6), tuer, (0, 0.475, 1.16), coll, bevel=0.01)
    L.box(f"{name}_tuerg", (0.07, 0.62, 1.1), L.mat("lp_glas", "#CFEFF7", 0.1, emit="#CFEFF7", strength=0.3, alpha=0.35),
          tuer, (0, 0.475, 1.55), coll)
    tuer.rotation_euler = (0, 0, math.radians(-100))      # nach aussen offen, Scharnier vorn
    L.box(f"{name}_schwelle", (0.3, 1.0, 0.03), wdark, root, (X, -1.4, 0.015), coll)
    # Schaufenster: Rahmen, Sprosse, Glas, Fensterbank mit zwei Broten
    for nm, sz, lo in (("fu", (0.2, 2.4, 0.08), (X, 0.55, 0.9)), ("fo", (0.2, 2.4, 0.08), (X, 0.55, 2.5)),
                       ("fs", (0.18, 0.06, 1.6), (X, 0.55, 1.7)), ("fl", (0.2, 0.08, 1.68), (X, -0.6, 1.7)),
                       ("fr", (0.2, 0.08, 1.68), (X, 1.7, 1.7))):
        L.box(f"{name}_{nm}", sz, wdark, root, lo, coll)
    m_glas = L.unique_mat(L.mat("lp_scheibe", "#D9F2FA", 0.08, emit="#D9F2FA", strength=0.2, alpha=0.16), f"{name}_glasm")
    glas = L.box(f"{name}_glas", (0.02, 2.3, 1.6), m_glas, root, (X, 0.55, 1.7), coll)
    for q in range(3):                                    # Spiegelstreifen
        st = L.box(f"{name}_spiegel{q}", (0.005, 0.12, 1.7), L.mat("lp_spiegel", "#FFFFFF", 0.1, emit="#FFFFFF", strength=0.6, alpha=0.18),
                   root, (X - 0.012, 0.05 + q * 0.55, 1.7), coll)
        st.rotation_euler = (0.5, 0, 0)
    L.box(f"{name}_bank", (0.45, 2.3, 0.05), L.mat("wood_light", L.WOOD_LIGHT, 0.6), root, (X - 0.2, 0.55, 0.93), coll)
    for q, y in enumerate((0.0, 0.9)):
        L.sphere(f"{name}_brot{q}", 0.13, 10, 6, (1.4, 1.0, 0.8), L.mat("crust", L.CRUST, 0.65), root, (X - 0.22, y, 1.05), coll)

    # Draussen: Gehweg, Bordstein, Strasse, gegenueber Haeuser, Himmel
    out = L.empty(f"{name}_aussen", root, (0, 0, 0), coll)
    L.box(f"{name}_gehweg", (3.2, 14, 0.06), L.mat("lp_gehweg", "#B9B4AA", 0.8), out, (X + 1.6, -1.0, 0.0), coll)
    for q in range(14):
        L.box(f"{name}_fuge{q}", (3.2, 0.02, 0.062), L.mat("lp_fuge", "#9E998F", 0.8), out, (X + 1.6, -7.5 + q * 1.0, 0.0), coll)
    L.box(f"{name}_bord", (0.18, 14, 0.16), L.mat("lp_bord", "#D6D2C8", 0.7), out, (X + 3.25, -1.0, 0.02), coll)
    L.box(f"{name}_strasse", (5.0, 14, 0.02), L.mat("lp_strasse", "#4A4B57", 0.85), out, (X + 5.8, -1.0, 0.0), coll)
    for q in range(5):
        L.box(f"{name}_mark{q}", (0.12, 0.9, 0.025), L.mat("lp_mark", "#F2EFE6", 0.6), out, (X + 5.8, -6 + q * 2.6, 0.005), coll)
    cols = ["#E6B87A", "#C97B5A", "#9FC2B8", "#E8D7B5", "#B98FB0"]
    for q in range(5):
        yy = -6.2 + q * 2.4
        h = 3.6 + 0.8 * (q % 2)
        L.box(f"{name}_haus{q}", (1.2, 2.3, h), L.mat(f"lp_haus{q}", cols[q], 0.7), out, (X + 9.0, yy, h / 2), coll)
        L.box(f"{name}_dach{q}", (1.3, 2.4, 0.18), L.mat("lp_dach", "#8E3B2E", 0.7), out, (X + 9.0, yy, h + 0.09), coll)
        for r_ in range(2):
            for c_ in range(2):
                L.box(f"{name}_hf{q}{r_}{c_}", (0.05, 0.42, 0.6), L.mat("lp_hfenster", "#5F7FA8", 0.3, emit="#9FC7EA", strength=0.4),
                      out, (X + 8.38, yy - 0.5 + c_ * 1.0, 1.1 + r_ * 1.3), coll)
    L.box(f"{name}_nachbar", (12.0, 0.12, 7.0), L.mat("lp_nachbar", "#C9A27E", 0.75), out, (X + 6.0, 2.3, 3.5), coll)
    L.box(f"{name}_himmel", (0.1, 40, 14), L.mat("lp_himmel", "#BFE3F2", 0.5, emit="#BFE3F2", strength=0.9), out,
          (X + 14.0, -1.0, 5.0), coll)
    for q, (yy, zz, s) in enumerate(((-3.5, 6.2, 1.0), (2.0, 6.8, 0.8), (-0.5, 7.4, 0.6))):
        wo = L.empty(f"{name}_wolke{q}", out, (X + 13.8, yy, zz), coll)
        for j in range(3):
            L.sphere(f"{name}_wk{q}{j}", 0.5 * s, 10, 6, (0.3, 1.4, 0.8), L.mat("lp_wolke", "#FFFFFF", 0.6, emit="#FFFFFF", strength=1.0),
                     wo, (0, (j - 1) * 0.55 * s, 0.1 * (j % 2)), coll)
    # Laterne und Baum auf dem Gehweg (Nebenbewegung: Baum wiegt sich in der Regie)
    L.cyl(f"{name}_lat", 0.04, 3.0, 8, L.mat("lp_lat", "#2A2638", 0.5), out, (X + 2.9, -4.4, 1.5), coll)
    L.sphere(f"{name}_latk", 0.16, 10, 6, (1, 1, 1.2), L.mat("lp_latk", "#FFF1C4", 0.4, emit="#FFF1C4", strength=0.8), out,
             (X + 2.9, -4.4, 3.05), coll)
    baum = L.empty(f"{name}_baum", out, (X + 2.8, 1.6, 0), coll)
    L.cyl(f"{name}_stamm", 0.09, 1.8, 8, L.mat("lp_stamm", "#7A5236", 0.7), baum, (0, 0, 0.9), coll)
    krone = L.empty(f"{name}_krone", baum, (0, 0, 1.8), coll)
    for j, (dx, dz, r) in enumerate(((0, 0.5, 0.75), (0.3, 0.2, 0.55), (-0.35, 0.25, 0.55))):
        L.ico(f"{name}_kr{j}", r, 1, (1, 1, 0.9), L.mat("lp_laub", "#6FA65A", 0.7), krone, (0, dx, dz), coll)
    w = S.p(0, 0, 0)
    return P(root=root, tuer=tuer, glas=glas, m_glas=m_glas, krone=krone, out=out,
             tuer_mitte=w + Vector((X, -1.4, 0)), fenster_mitte=w + Vector((X, 0.55, 1.7)), X=X)


# ------------------------------------------------------------------ Pfad (Polylinie) fuer Schlange und Passanten
def pfad(pts):
    """pts: Liste von Vektoren. Rueckgabe: (pos(s), richtung(s), laenge) entlang der Polylinie (s in Metern)."""
    pts = [Vector(p) for p in pts]
    seg = [(a, b, (b - a).length) for a, b in zip(pts, pts[1:])]
    total = sum(s[2] for s in seg)

    def pos(s):
        s = max(0.0, s)
        for a, b, ln in seg:
            if s <= ln:
                return a.lerp(b, s / max(1e-6, ln))
            s -= ln
        a, b, ln = seg[-1]
        return b + (b - a).normalized() * s

    def richt(s):
        s = max(0.0, s)
        for a, b, ln in seg:
            if s <= ln:
                return (b - a).normalized()
            s -= ln
        a, b, ln = seg[-1]
        return (b - a).normalized()
    return pos, richt, total


# ------------------------------------------------------------------ Kundenschlange
def kundenschlange(coll, name, n, seed=13, s=0.92, handy_quote=0.6):
    """n Kunden (viral.kunde_mit_handy), Positionen setzt schlange_bewegen."""
    r = random.Random(seed)
    cols = ["#E0703D", "#3E8E6A", "#6C5BA8", "#C9944A", "#2E8C88", "#B5524F", "#4E6B8A", "#D9A866", "#7A9E3E", "#C25E86"]
    out = []
    for i in range(n):
        k = VP.kunde_mit_handy(coll, f"{name}{i}", cols[i % len(cols)], s=s * r.uniform(0.9, 1.06), seed=seed + i,
                               handy=(r.random() < handy_quote) and i > 0)
        k.s0 = k.root.scale[0]
        k.ph = r.uniform(0, 6.28)
        out.append(k)
    return out


def schlange_bewegen(T, kunden, pos, richt, s_fn, f0, f1, s_weg=99.0):
    """s_fn(i, f) -> Bogenlaenge des Kunden i auf dem Pfad (None = nicht da). Kunden schauen zur Theke (Pfad-Anfang),
    wippen ungeduldig, beim Gehen staerker (Schritt-Hopser). Ab s_weg ausgeblendet."""
    for i, k in enumerate(kunden):
        def loc(f, i=i):
            s = s_fn(i, f)
            return tuple(pos(s if s is not None else s_weg))

        def rot(f, i=i):
            s = s_fn(i, f)
            d = -richt(s if s is not None else 0)
            return (0, 0, math.atan2(d.x, -d.y))

        def scl(f, i=i, k=k):
            s = s_fn(i, f)
            return (k.s0,) * 3 if s is not None and s < s_weg else (0, 0, 0)

        def geht(f, i=i):
            a, b = s_fn(i, f - 1), s_fn(i, f + 1)
            if a is None or b is None:
                return 0.0
            return min(1.0, abs(b - a) * 6)

        T.set(k.root, "location", loc, f0, f1)
        T.set(k.root, "rotation_euler", rot, f0, f1)
        T.set(k.root, "scale", scl, f0, f1)
        T.add(k.body, "location", lambda f, k=k, geht=geht: (0, 0, 0.025 * max(0.0, math.sin(f * 0.33 + k.ph)) +
                                                          0.07 * geht(f) * abs(math.sin(f * 0.6 + k.ph))), f0, f1)
        T.add(k.body, "rotation_euler", lambda f, k=k, geht=geht: (0.03 * math.sin(f * 0.17 + k.ph), 0.05 * math.sin(f * 0.21 + k.ph) +
                                                                0.12 * geht(f) * math.sin(f * 0.6 + k.ph), 0), f0, f1)
        T.add(k.head, "rotation_euler", lambda f, k=k: (0.06 * math.sin(f * 0.11 + k.ph), 0, 0.25 * math.sin(f * 0.05 + 2 * k.ph)), f0, f1)
        if k.phone is not None:
            T.add(k.arm, "rotation_euler", lambda f, k=k: (0.1 * math.sin(f * 0.23 + k.ph), 0, 0.05 * math.sin(f * 0.31 + k.ph)), f0, f1)


# ------------------------------------------------------------------ Tuerglocke
def tuerglocke(coll, name):
    root = L.empty(name, coll=coll)
    m_met = L.mat("tg_halter", "#2A2638", 0.45, metallic=0.4)
    L.box(f"{name}_halter", (0.04, 0.28, 0.04), m_met, root, (0, 0, 0), coll)
    feder = L.empty(f"{name}_feder", root, (0, -0.12, 0), coll)
    for q in range(5):
        L.torus(f"{name}_fd{q}", 0.018, 0.005, 10, 4, m_met, feder, (0, 0, -0.02 - 0.018 * q), coll)
    glocke = L.empty(f"{name}_glocke", feder, (0, 0, -0.11), coll)
    m_gold = L.mat("tg_gold", L.GOLD, 0.3, metallic=0.8, emit="#F2C46A", strength=0.4)
    L.cyl(f"{name}_mantel", 0.04, 0.11, 16, m_gold, glocke, (0, 0, -0.055), coll, r2=0.085)
    L.torus(f"{name}_rand", 0.085, 0.01, 16, 4, m_gold, glocke, (0, 0, -0.11), coll)
    kloeppel = L.empty(f"{name}_kl", glocke, (0, 0, -0.03), coll)
    L.cyl(f"{name}_klst", 0.005, 0.08, 6, m_met, kloeppel, (0, 0, -0.04), coll)
    L.sphere(f"{name}_klk", 0.016, 8, 5, (1, 1, 1), m_gold, kloeppel, (0, 0, -0.085), coll)
    return P(root=root, feder=feder, glocke=glocke, kloeppel=kloeppel)


def bimmeln(T, g, staerke_fn, f0, f1):
    """staerke_fn(f) 0..1: wildes Schwingen (1) bis Stillstand (0). Kloeppel schlaegt verzoegert gegen."""
    T.set(g.feder, "rotation_euler", lambda f: (0.55 * staerke_fn(f) * math.sin(f * 0.9), 0.25 * staerke_fn(f) * math.sin(f * 0.53), 0), f0, f1)
    T.set(g.kloeppel, "rotation_euler", lambda f: (-0.7 * staerke_fn(f) * math.sin(f * 0.9 - 0.9), 0, 0), f0, f1)
    T.set(g.glocke, "scale", lambda f: (1 + 0.06 * staerke_fn(f) * max(0.0, math.sin(f * 1.8)),) * 3, f0, f1)


# ------------------------------------------------------------------ Kameralinse vor Bytes Gesicht
def kameralinse_byte(coll, name):
    """Linse (Vorderseite -Y). root sitzt vor dem Gesicht; klappe = Gehaeuse, das von oben herunterklappt."""
    root = L.empty(name, coll=coll)
    klappe = L.empty(f"{name}_klappe", root, (0, 0, 0.0), coll)
    m_dark = L.mat("kl_gehaeuse", "#22203A", 0.4, metallic=0.3)
    L.cyl(f"{name}_tubus", 0.075, 0.06, 24, m_dark, klappe, (0, 0, 0), coll, axis="Y")
    L.torus(f"{name}_ring", 0.075, 0.012, 24, 5, L.mat("kl_ring", TURQ, 0.3, emit=TURQ, strength=3.0), klappe, (0, -0.032, 0), coll, axis="Y")
    m_glas = L.mat("kl_glas", "#3A6FD8", 0.1, emit="#7FB8FF", strength=1.2)
    L.cyl(f"{name}_glas", 0.055, 0.01, 24, m_glas, klappe, (0, -0.03, 0), coll, axis="Y")
    L.sphere(f"{name}_reflex", 0.014, 8, 5, (1, 0.4, 1), L.mat("kl_reflex", "#FFFFFF", 0.2, emit="#FFFFFF", strength=4.0), klappe,
             (-0.02, -0.04, 0.022), coll)
    blende = []
    m_bl = L.mat("kl_blende", "#15132A", 0.5)
    for q in range(6):
        piv = L.empty(f"{name}_blp{q}", klappe, (0, -0.037, 0), coll, rot=(0, 2 * math.pi * q / 6, 0))
        L.poly_flat(f"{name}_bl{q}", [(0.0, 0.0), (0.06, 0.012), (0.03, 0.05)], 0.004, m_bl, piv, (0, 0, 0), coll)
        blende.append(piv)
    m_rec = L.unique_mat(L.mat("kl_rec", "#FF3B4A", 0.4, emit="#FF3B4A", strength=6.0), f"{name}_recm")
    rec = L.sphere(f"{name}_rec", 0.022, 10, 6, (1, 0.7, 1), m_rec, root, (0.12, -0.02, 0.07), coll)
    root.scale = (0, 0, 0)
    return P(root=root, klappe=klappe, blende=blende, rec=rec, m_rec=m_rec)


def linse_aufklappen(T, l, f, f_aus=None, f_ende=10 ** 5):
    """Linse poppt auf, Gehaeuse klappt mit Ueberschwingen herunter, Blende oeffnet sich, REC blinkt."""
    T.set(l.root, "scale", lambda x: (pop(x, f, 7, 1.25) * (unpop(x, f_aus, 6) if f_aus is not None and x > f_aus else 1),) * 3,
          f - 1, (f_aus + 7) if f_aus is not None else f + 8)
    T.set(l.klappe, "rotation_euler", lambda x: (-math.pi / 2 * (1 - ease_out_back(clamp01((x - f) / 9), 2.6)), 0, 0), f - 1, f + 10)
    for q, piv in enumerate(l.blende):
        T.set(piv, "scale", lambda x: (1 - 0.85 * ease_out(clamp01((x - f - 6) / 8)),) * 3, f + 5, f + 15)
    on = tuple(l.m_rec.diffuse_color)
    off = tuple(c * 0.25 for c in on[:3]) + (1.0,)
    T.set(l.m_rec, "diffuse_color", lambda x: on if x >= f + 6 and ((x - f) % 16) < 9 else off, f, f_ende)
    T.set(l.rec, "scale", lambda x: (1.3,) * 3 if x >= f + 6 and ((x - f) % 16) < 9 else (0.85,) * 3, f, f_ende)


# ------------------------------------------------------------------ Teigstrang -> Brezel
def teigstrang(coll, name, laenge=0.62):
    root = L.empty(name, coll=coll)
    m = L.mat("lp_teig", "#EBD3A8", 0.7)
    n = 7
    for q in range(n):
        x = -laenge / 2 + laenge * (q + 0.5) / n
        r = 0.032 * (0.75 + 0.25 * math.sin(math.pi * (q + 0.5) / n))
        L.sphere(f"{name}_s{q}", r, 10, 6, (laenge / n / (2 * r) * 1.25, 1, 1), m, root, (x, 0, 0), coll)
    return P(root=root)


def brezel_schlingen(T, coll, name, start, ziel, f0, dauer, s=1.6, hoehe=0.75, seed=5):
    """Teigstrang fliegt im Bogen von start nach ziel (Zeitlupe in der Mitte), dreht sich und wird bei der Landung zur
    Brezel (pop, Squash & Stretch, Mehlwolke mit Glitzern). Rueckgabe: (strang, brezel, f_landung)."""
    st = teigstrang(coll, f"{name}_strang")
    brz = PR.pastry(coll, f"{name}_brezel", "brezel", None, tuple(ziel), s)
    a, b = Vector(start), Vector(ziel)
    f_land = f0 + dauer

    def u(f):                                       # Zeitlupe: Mitte langsam
        t = clamp01((f - f0) / dauer)
        return 0.5 + 0.5 * math.copysign(abs(2 * t - 1) ** 0.6, 2 * t - 1)

    def loc(f):
        t = u(f)
        return tuple(a.lerp(b, t) + Vector((0, 0, hoehe * math.sin(math.pi * t))))
    T.set(st.root, "location", loc, f0 - 1, f_land + 1)
    T.set(st.root, "rotation_euler", lambda f: (0.6 * math.sin(math.pi * u(f)), 2.2 * math.pi * u(f), 0.8 * u(f)), f0 - 1, f_land + 1)
    T.set(st.root, "scale", lambda f: (1.0 - 0.6 * clamp01((f - f_land + 6) / 6),) * 3 if f0 - 1 <= f < f_land else (0, 0, 0), 0, 10 ** 5)
    T.set(brz, "scale", lambda f: (s * pop(f, f_land - 2, 7, 1.3),) * 3 if f >= f_land - 2 else (0, 0, 0), 0, 10 ** 5)
    landen(T, brz, f_land + 2, staerke=0.35, dauer=10)
    PR.burst(T, coll, f"{name}_wolke", "puff", tuple(b + Vector((0, 0, 0.03))), f_land, 14, seed, speed=(0.4, 1.0), up=0.5,
             gravity=-0.3, life=(20, 30), size=(0.8, 1.4), drag=3.0, ring=True)
    PR.burst(T, coll, f"{name}_glitzer", "sparkt", tuple(b + Vector((0, 0, 0.1))), f_land + 1, 16, seed + 1, speed=(0.4, 1.0), up=0.8,
             gravity=-0.6, life=(16, 26), size=(0.6, 1.0))
    return st, brz, f_land


# ------------------------------------------------------------------ Zeitleiste mit Clip-Kacheln
def zeitleiste_clips(coll, name, n=12, gute=(3, 7, 10), breite=0.34):
    """Filmstreifen (Achse X, Vorderseite -Y) mit n Clip-Kacheln. Gute Kacheln: Brezel-Motiv, leuchten warm;
    langweilige: Kalle kratzt sich / wartet (Uhr), werden beim Schnitt grau und fallen."""
    root = L.empty(name, coll=coll)
    L_ = n * breite + 0.1
    m_film = L.mat("zl_film", "#1B1830", 0.5)
    streifen = L.empty(f"{name}_streifen", root, (0, 0, 0), coll)
    L.box(f"{name}_film", (L_, 0.02, 0.36), m_film, streifen, (0, 0.02, 0), coll)
    for q in range(int(L_ / 0.09)):
        for sz in (-1, 1):
            L.box(f"{name}_loch{q}{sz}", (0.035, 0.03, 0.025), L.mat("zl_loch", "#EDE6D6", 0.5), streifen,
                  (-L_ / 2 + 0.05 + q * 0.09, 0.0, sz * 0.15), coll)
    kacheln = []
    r = random.Random(3)
    for i in range(n):
        x = -L_ / 2 + 0.05 + breite * (i + 0.5)
        k = L.empty(f"{name}_k{i}", root, (x, -0.01, 0), coll)
        gut = i in gute
        farbe = "#F2B45A" if gut else r.choice(["#8C7B6A", "#7D8A96", "#94806E"])
        m = L.unique_mat(L.mat("zl_kachel", farbe, 0.45, emit=farbe, strength=1.2 if gut else 0.3), f"{name}_m{i}")
        L.box(f"{name}_kb{i}", (breite - 0.04, 0.025, 0.24), m, k, (0, 0, 0), coll, bevel=0.01)
        m_ic = L.mat("zl_icon", "#FBF8F0", 0.5, emit="#FBF8F0", strength=0.8)
        if gut:
            PR.pastry(coll, f"{name}_bz{i}", "brezel", k, (0, -0.02, -0.01), 0.55).rotation_euler = (math.pi / 2, 0, 0)
        elif i % 2:                                       # Kalle kratzt sich: Kopf mit Muetze und erhobene Hand
            L.sphere(f"{name}_kopf{i}", 0.045, 8, 5, (1, 0.6, 1), m_ic, k, (0, -0.02, -0.02), coll)
            L.box(f"{name}_muetze{i}", (0.07, 0.02, 0.05), m_ic, k, (0, -0.02, 0.045), coll)
            L.box(f"{name}_hand{i}", (0.02, 0.02, 0.07), m_ic, k, (0.07, -0.02, 0.03), coll).rotation_euler = (0, 0.5, 0)
        else:                                             # Kalle wartet: Uhr
            L.torus(f"{name}_uhr{i}", 0.06, 0.008, 16, 4, m_ic, k, (0, -0.02, 0), coll, axis="Y")
            L.box(f"{name}_zg{i}", (0.008, 0.01, 0.05), m_ic, k, (0, -0.025, 0.02), coll)
            L.box(f"{name}_zg2{i}", (0.035, 0.01, 0.008), m_ic, k, (0.015, -0.025, 0), coll)
        kacheln.append(P(root=k, m=m, gut=gut, x=x))
    m_cut = L.unique_mat(L.mat("zl_schnitt", TURQ, 0.3, emit=TURQ, strength=6.0, alpha=0.85), f"{name}_cutm")
    schnitt = L.box(f"{name}_schnitt", (0.025, 0.06, 0.62), m_cut, root, (-L_ / 2, -0.04, 0), coll)
    schnitt_glow = L.box(f"{name}_schnittg", (0.14, 0.04, 0.7), L.mat("zl_schnittg", TURQ, 0.3, emit=TURQ, strength=1.0, alpha=0.2),
                         schnitt, (0, 0.01, 0), coll)
    schnitt.scale = (0, 0, 0)
    return P(root=root, streifen=streifen, kacheln=kacheln, schnitt=schnitt, laenge=L_, breite=breite, gute=gute)


def zeitleiste_schneiden(T, z, f_cut, dauer, boden_z, f_rast, s_root=1.0):
    """Lichtschnitt faehrt von links nach rechts (f_cut .. f_cut+dauer). Langweilige Kacheln werden grau, fallen mit
    Drehung zu Boden (Squash beim Aufprall); ab f_rast gleiten die drei guten Kacheln zusammen und rasten mit Pop ein.
    boden_z: Bodenhoehe in lokalen Koordinaten der Zeitleiste. Rueckgabe: Liste der Pop-Frames (Einrasten)."""
    L_ = z.laenge
    T.set(z.schnitt, "scale", lambda f: (1, 1, 1) if f_cut <= f < f_cut + dauer + 4 else (0, 0, 0), 0, 10 ** 5)
    T.set(z.schnitt, "location", lambda f: (-L_ / 2 + L_ * ease_in_out(clamp01((f - f_cut) / dauer)), -0.04, 0), f_cut - 1, f_cut + dauer + 1)
    rnd = random.Random(8)
    gute = [k for k in z.kacheln if k.gut]
    mitte = sum(k.x for k in gute) / len(gute)
    pops = []
    for i, k in enumerate(z.kacheln):
        t_pass = f_cut + int(dauer * clamp01((k.x + L_ / 2) / L_))
        if k.gut:
            j = gute.index(k)
            x_end = (j - 1) * (z.breite - 0.035)
            f_k = f_rast + 4 * j
            pops.append(f_k + 8)
            T.set(k.root, "location", lambda f, k=k, x_end=x_end, f_k=f_k: (lerp(k.x, x_end, ease_out_back(clamp01((f - f_k) / 9), 1.4)),
                                                                            -0.01 - 0.06 * window(f, t_pass, f_rast + 14, 3, 6), 0),
                  t_pass - 1, 10 ** 5)
            landen(T, k.root, f_k + 9, staerke=0.25, dauer=8)
            hell = tuple(k.m.diffuse_color)
            heller = tuple(min(1.0, c * 1.35 + 0.08) for c in hell[:3]) + (1.0,)
            T.set(k.m, "diffuse_color", lambda f, hell=hell, heller=heller, tp=t_pass: heller if tp <= f < tp + 8 else hell, 0, 10 ** 5)
        else:
            vx, rz = rnd.uniform(-0.25, 0.25), rnd.uniform(-2.5, 2.5)
            t_fall = 0.75 * math.sqrt(2 * 1.0)                # ~1 m Fallhoehe
            boden = boden_z + 0.02

            def loc(f, k=k, tp=t_pass, vx=vx):
                t = max(0.0, (f - tp) / FPS)
                z_ = -4.9 * t * t
                return (k.x + vx * t, -0.01 - 0.15 * min(t, 0.6), max(boden, z_))
            T.set(k.root, "location", loc, t_pass - 1, t_pass + 60)
            T.set(k.root, "rotation_euler", lambda f, tp=t_pass, rz=rz: (min(1.0, max(0.0, (f - tp) / 18)) * -1.45,
                                                                        rz * min(1.0, max(0.0, (f - tp) / 18)), 0), t_pass - 1, t_pass + 60)
            grau = L.srgb("#5A5A60")
            alt = tuple(k.m.diffuse_color)
            T.set(k.m, "diffuse_color", lambda f, alt=alt, tp=t_pass: tuple(lerp(a, b, clamp01((f - tp) / 5)) for a, b in zip(alt[:3], grau[:3])) + (1.0,),
                  t_pass - 1, t_pass + 6)
            f_auf = t_pass + int(FPS * math.sqrt(max(0.01, (0 - boden)) / 4.9)) if boden < 0 else t_pass + 8
            landen(T, k.root, f_auf, staerke=0.3, dauer=8)
    return pops


# ------------------------------------------------------------------ Hochkant-Handy ohne Logo
def handy_hochkant(coll, name, h=1.5, titel="Brezel in 3 Sekunden?", woerter=("Ein", "Schwung", "…", "fertig!")):
    """Grosses Hochkant-Handy (Vorderseite -Y). Bildschirm: warmes Video mit Brezel und Mini-Kalle, Untertitel-Woerter
    (je ein Objekt), Titelzeile oben, Fortschrittsbalken; Notensymbole am Rand (separat steuerbar)."""
    root = L.empty(name, coll=coll)
    w = h * 0.5
    L.box(f"{name}_gehaeuse", (w, 0.05, h), L.mat("hh_gehaeuse", "#1E1C2E", 0.35, metallic=0.3), root, (0, 0, 0), coll, bevel=0.05, seg=3)
    scr = L.empty(f"{name}_scr", root, (0, -0.027, 0), coll)
    L.box(f"{name}_bg", (w - 0.06, 0.006, h - 0.08), L.mat("hh_bg", "#F3D9B1", 0.5, emit="#F3D9B1", strength=0.9), scr, (0, 0, 0), coll)
    L.box(f"{name}_bg2", (w - 0.06, 0.007, h * 0.3), L.mat("hh_bg2", "#C98A4E", 0.5, emit="#C98A4E", strength=0.6), scr, (0, -0.001, -h * 0.26), coll)
    # Mini-Kalle im Video
    mk = L.empty(f"{name}_mk", scr, (0, -0.006, 0.02), coll)
    L.sphere(f"{name}_mkkopf", 0.075, 10, 6, (1, 0.5, 1), L.mat("hh_haut", "#F0C29C", 0.5, emit="#F0C29C", strength=0.6), mk, (0, 0, 0.12), coll)
    L.box(f"{name}_mkmuetze", (0.12, 0.02, 0.09), L.mat("hh_weiss", "#FFFFFF", 0.5, emit="#FFFFFF", strength=0.8), mk, (0, 0, 0.22), coll, bevel=0.02)
    L.box(f"{name}_mkbart", (0.08, 0.02, 0.02), L.mat("hh_bart", "#4A3328", 0.5), mk, (0, -0.004, 0.1), coll)
    L.box(f"{name}_mkkoerper", (0.2, 0.02, 0.18), L.mat("hh_hemd", "#6C7EC4", 0.5, emit="#6C7EC4", strength=0.5), mk, (0, 0, -0.02), coll, bevel=0.03)
    brz = PR.pastry(coll, f"{name}_vbrezel", "brezel", scr, (0, -0.02, -0.17), 0.9)
    brz.rotation_euler = (math.pi / 2, 0, 0)
    # Titelzeile oben
    m_tit = L.mat("hh_titel", "#FFFFFF", 0.4, emit="#FFFFFF", strength=1.4)
    tb = L.empty(f"{name}_titelbox", scr, (0, -0.008, h * 0.36), coll)
    L.box(f"{name}_titelbg", (w - 0.1, 0.004, 0.2), L.mat("hh_titelbg", NAVY, 0.5), tb, (0, 0, 0), coll, bevel=0.02)
    tt = _text(f"{name}_titel", titel, 0.062, m_tit, tb, (0, -0.004, -0.02), coll, extrude=0.002)
    # Untertitel-Woerter
    m_ut = L.mat("hh_ut", "#FFD23F", 0.4, emit="#FFD23F", strength=1.6)
    ut = []
    n = len(woerter)
    for q, wd in enumerate(woerter):
        o = _text(f"{name}_ut{q}", wd, 0.06, m_ut, scr, ((q - (n - 1) / 2) * (w - 0.12) / n, -0.012, -h * 0.05), coll, extrude=0.002)
        o.scale = (0, 0, 0)
        ut.append(o)
    # Fortschrittsbalken
    L.box(f"{name}_bar0", (w - 0.14, 0.004, 0.015), L.mat("hh_bar0", "#8E7A66", 0.5), scr, (0, -0.006, -h * 0.44), coll)
    bar = L.empty(f"{name}_barp", scr, (-(w - 0.14) / 2, -0.008, -h * 0.44), coll)
    L.box(f"{name}_bar", (w - 0.14, 0.004, 0.017), L.mat("hh_bar", ROT, 0.4, emit=ROT, strength=1.5), bar, ((w - 0.14) / 2, 0, 0), coll)
    # Notensymbole (Kopf, Hals, Faehnchen)
    noten = []
    m_n = L.mat("hh_note", TURQ, 0.3, emit=TURQ, strength=3.0)
    for q in range(4):
        no = L.empty(f"{name}_note{q}", root, ((-1) ** q * (w / 2 + 0.12), -0.05, -h * 0.25 + q * 0.18), coll)
        L.sphere(f"{name}_nk{q}", 0.035, 8, 5, (1.3, 0.6, 1), m_n, no, (0, 0, 0), coll)
        L.box(f"{name}_nh{q}", (0.012, 0.012, 0.14), m_n, no, (0.04, 0, 0.07), coll)
        L.box(f"{name}_nf{q}", (0.05, 0.012, 0.025), m_n, no, (0.06, 0, 0.13), coll).rotation_euler = (0, 0.5, 0)
        no.scale = (0, 0, 0)
        noten.append(no)
    return P(root=root, scr=scr, mk=mk, brezel=brz, titelbox=tb, ut=ut, bar=bar, noten=noten, h=h, w=w)


def handy_abspielen(T, hh, f0, f1, f_titel, f_worte=None, intervall=9, f_noten=None):
    """Video laeuft: Mini-Kalle wippt, Brezel dreht sich, Fortschrittsbalken waechst, Untertitel poppen Wort fuer Wort
    (ab f_worte), Titelzeile klappt ab f_titel auf, Noten schweben am Rand."""
    T.set(hh.mk, "location", lambda f: (0.02 * math.sin(f * 0.3), -0.006, 0.02 + 0.015 * abs(math.sin(f * 0.25))), f0, f1)
    T.set(hh.brezel, "rotation_euler", lambda f: (math.pi / 2, 0.35 * math.sin(f * 0.2), 0), f0, f1)
    T.set(hh.bar, "scale", lambda f: (clamp01((f - f0) / max(1, f1 - f0)) + 0.02, 1, 1), f0, f1)
    fw = f_worte if f_worte is not None else f0 + 8
    for q, o in enumerate(hh.ut):
        T.set(o, "scale", lambda f, q=q: (pop(f, fw + q * intervall, 6, 1.3),) * 3 if f >= fw + q * intervall else (0, 0, 0), f0, f1)
    KV.schild_klappen(T, hh.titelbox, f_titel, dauer=9)
    T.set(hh.titelbox, "scale", lambda f: (0, 0, 0), f0, f_titel - 1)
    for q, no in enumerate(hh.noten):
        st = (f_noten if f_noten is not None else f0 + 4) + q * 7

        def loc(f, q=q, no=no, st=st, base=tuple(no.location)):
            t = ((f - st) % 40) / 40
            return (base[0] + 0.05 * math.sin(f * 0.15 + q), base[1], base[2] + 0.35 * t)
        T.set(no, "location", loc, f0, f1)
        T.set(no, "scale", lambda f, st=st: (math.sin(math.pi * (((f - st) % 40) / 40)) * (1 if f >= st else 0),) * 3, f0, f1)
        T.set(no, "rotation_euler", lambda f, q=q: (0, 0.3 * math.sin(f * 0.2 + q), 0), f0, f1)


# ------------------------------------------------------------------ Papierflieger
def papierflieger_licht(coll, name, s=1.0):
    """Leuchtender Papierflieger, Spitze nach +X."""
    root = L.empty(name, coll=coll)
    m = L.mat("pf_papier", "#E9FFFC", 0.4, emit="#BFFCF5", strength=2.2)
    m2 = L.mat("pf_falte", TURQ, 0.4, emit=TURQ, strength=2.5)
    a = 0.32 * s
    L.poly_flat(f"{name}_fl1", [(-a, 0.0), (a, 0.0), (-a, 0.16 * s)], 0.004, m, root, (0, 0, 0), coll, plane="XY")
    L.poly_flat(f"{name}_fl2", [(-a, 0.0), (a, 0.0), (-a, -0.16 * s)], 0.004, m, root, (0, 0, 0), coll, plane="XY")
    kiel = L.poly_flat(f"{name}_kiel", [(-a, 0.0), (a, 0.0), (-a, -0.08 * s)], 0.006, m2, root, (0, 0, 0), coll)
    return P(root=root)


def flug(T, pf, pos_fn, f0, f1):
    """Flieger folgt pos_fn, Nase in Flugrichtung, Schraeglage in Kurven."""
    def rot(f):
        a, b = Vector(pos_fn(f - 1)), Vector(pos_fn(f + 1))
        d = b - a
        if d.length < 1e-5:
            return (0, 0, 0)
        yaw = math.atan2(d.y, d.x)
        pitch = -math.atan2(d.z, math.hypot(d.x, d.y))
        c = Vector(pos_fn(f + 3)) - b
        bank = 0.0
        if c.length > 1e-5:
            bank = max(-0.6, min(0.6, (math.atan2(c.y, c.x) - yaw) * 3))
        return (bank, pitch, yaw)
    T.set(pf.root, "location", lambda f: tuple(pos_fn(f)), f0, f1)
    T.set(pf.root, "rotation_euler", rot, f0, f1)


# ------------------------------------------------------------------ Handy auf dem Tisch
def handy_vibriert(coll, name):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_g", (0.09, 0.17, 0.012), L.mat("hv_g", "#1E1C2E", 0.35, metallic=0.3), root, (0, 0, 0.006), coll, bevel=0.008)
    m_scr = L.unique_mat(L.mat("hv_scr", "#9FF6EE", 0.3, emit="#9FF6EE", strength=2.0), f"{name}_scrm")
    L.box(f"{name}_scr", (0.078, 0.15, 0.004), m_scr, root, (0, 0, 0.013), coll)
    for q in range(3):
        L.box(f"{name}_bn{q}", (0.06, 0.022, 0.003), L.mat("hv_bn", "#FFFFFF", 0.4, emit="#FFFFFF", strength=1.5), root,
              (0, 0.045 - q * 0.03, 0.016), coll)
    return P(root=root, m_scr=m_scr)


def vibrieren(T, hv, f0, f1, start, ziel, pulse=6):
    """Schnelles Zittern in Pulsen, das Handy wandert dabei ueber die Tischplatte. Rueckgabe: Buzz-Frames."""
    a, b = Vector(start), Vector(ziel)

    def an(f):
        return ((f - f0) % pulse) < pulse * 0.65
    T.set(hv.root, "location", lambda f: tuple(a.lerp(b, clamp01((f - f0) / max(1, f1 - f0))) +
                                               (Vector((0.006 * math.sin(f * 7.1), 0.006 * math.cos(f * 6.3), 0)) if an(f) else Vector())),
          f0 - 1, 10 ** 5)
    T.set(hv.root, "rotation_euler", lambda f: (0, 0, 0.4 * clamp01((f - f0) / max(1, f1 - f0)) + (0.05 * math.sin(f * 5.3) if an(f) and f < f1 else 0)),
          f0 - 1, 10 ** 5)
    hell = tuple(hv.m_scr.diffuse_color)
    T.set(hv.m_scr, "diffuse_color", lambda f: hell if (f0 <= f < f1 and an(f)) or f >= f1 else tuple(c * 0.55 for c in hell[:3]) + (1.0,), 0, 10 ** 5)
    return list(range(f0, f1, pulse))


# ------------------------------------------------------------------ Herzen und Sprechblasen
herzchen = VP.herzchen


def sprechblasen(T, coll, name, origin, f0, count, seed, f_end=None):
    """Weisse Sprechblasen mit drei Punkten steigen schaukelnd auf und ploppen."""
    r = random.Random(seed)
    o0 = Vector(origin)
    m_b = L.mat("sb_blase", "#FFFFFF", 0.4, emit="#FFFFFF", strength=1.2)
    m_p = L.mat("sb_punkt", "#6C5BA8", 0.4)
    for i in range(count):
        root = L.empty(f"{name}_{i}", coll=coll)
        L.box(f"{name}_{i}_b", (0.16, 0.03, 0.11), m_b, root, (0, 0, 0), coll, bevel=0.04, seg=2)
        L.poly_flat(f"{name}_{i}_z", [(-0.04, -0.05), (0.0, -0.05), (-0.06, -0.1)], 0.03, m_b, root, (0, 0, 0), coll)
        for q in range(3):
            L.sphere(f"{name}_{i}_p{q}", 0.013, 6, 4, (1, 1, 1), m_p, root, (-0.04 + 0.04 * q, -0.018, 0), coll)
        t0 = f0 + r.uniform(0, 22) + i * 2
        life = r.uniform(28, 40) if f_end is None else min(r.uniform(28, 40), f_end - t0)
        st = o0 + Vector((r.uniform(-0.35, 0.35), r.uniform(-0.1, 0.1), 0))
        vz, ph = r.uniform(0.7, 1.1), r.uniform(0, 6.28)
        T.set(root, "location", lambda f, t0=t0, st=st, vz=vz, ph=ph: tuple(st + Vector((0.1 * math.sin(3 * max(0, f - t0) / FPS + ph), 0,
                                                                                         vz * max(0, f - t0) / FPS))), t0 - 1, t0 + life + 1)
        T.set(root, "scale", lambda f, t0=t0, life=life: ((pop(f, t0, 6, 1.25) * (unpop(f, t0 + life - 5, 5) if f > t0 + life - 5 else 1)) if f >= t0 else 0,) * 3,
              t0 - 1, t0 + life + 1)
        T.set(root, "scale", lambda f: (0, 0, 0), 0, 1)


# ------------------------------------------------------------------ Wellenringe, Mini-Baeckerei, Figuren
def wellenringe(T, coll, name, pos, f0, n=4, abstand=14, dauer=34, r_end=3.2):
    """n tuerkise Ringe nacheinander. Rueckgabe: Startframes und Funktion radius(f) der Wellenfront (groesster Ring)."""
    starts = [f0 + q * abstand for q in range(n)]
    for q, st in enumerate(starts):
        KV.lichtring_welle(T, coll, f"{name}{q}", pos, st, dauer=dauer, r_end=r_end)

    def radius(f):
        r = 0.0
        for st in starts:
            if f >= st:
                r = max(r, 0.05 + r_end * ease_out(clamp01((f - st) / dauer)))
        return r
    return starts, radius


def mini_baeckerei(coll, name, s=1.0):
    root = L.empty(name, coll=coll)
    root.scale = (s, s, s)
    L.box(f"{name}_sockel", (0.9, 0.7, 0.06), L.mat("mb_sockel", "#8E8A80", 0.7), root, (0, 0, 0.03), coll)
    L.box(f"{name}_wand", (0.8, 0.6, 0.55), L.mat("mb_wand", "#F3E3C3", 0.65), root, (0, 0, 0.335), coll, bevel=0.02)
    dach = L.empty(f"{name}_dach", root, (0, 0, 0.61), coll)
    m_d = L.mat("mb_dach", "#C0392B", 0.6)
    for sx in (-1, 1):
        p = L.box(f"{name}_dachf{sx}", (0.48, 0.72, 0.04), m_d, dach, (sx * 0.2, 0, 0.13), coll)
        p.rotation_euler = (0, sx * 0.6, 0)
    L.box(f"{name}_kamin", (0.09, 0.09, 0.22), L.mat("mb_kamin", "#7A4E3A", 0.7), root, (0.22, 0.12, 0.85), coll)
    L.box(f"{name}_tuer", (0.16, 0.02, 0.28), L.mat("mb_tuer", "#5A3E2E", 0.6), root, (-0.18, -0.305, 0.2), coll)
    L.box(f"{name}_fenster", (0.26, 0.02, 0.18), L.mat("mb_fenster", "#FFE7A8", 0.4, emit="#FFE7A8", strength=1.6), root, (0.15, -0.305, 0.32), coll)
    for q in range(6):                                    # Markise rot-weiss
        mk = L.box(f"{name}_mark{q}", (0.07, 0.18, 0.02), L.mat("mb_mark", "#E5484D" if q % 2 == 0 else "#FBF8F0", 0.6), root,
                   (-0.18 + q * 0.07, -0.38, 0.5), coll)
        mk.rotation_euler = (-0.45, 0, 0)
    arm = L.empty(f"{name}_schildarm", root, (0.4, -0.2, 0.5), coll)
    L.box(f"{name}_arm", (0.16, 0.015, 0.015), L.mat("mb_arm", "#2A2638", 0.5), arm, (0.08, 0, 0), coll)
    schild = L.empty(f"{name}_schild", arm, (0.14, 0, -0.01), coll)
    PR.pastry(coll, f"{name}_brezel", "brezel", schild, (0, 0, -0.07), 0.7).rotation_euler = (math.pi / 2, 0, 0)
    return P(root=root, schild=schild)


def figuren_feld(coll, name, center, n, seed, r_min=0.7, r_max=3.0, s=0.5):
    """Kleine Spielfiguren-Leute im Kreis um center. Rueckgabe: Liste P(root, r, a)."""
    rnd = random.Random(seed)
    cols = ["#E0703D", "#3E8E6A", "#6C5BA8", "#C9944A", "#2E8C88", "#B5524F", "#4E6B8A", "#D9A866", "#7A9E3E", "#C25E86"]
    c = Vector(center)
    out = []
    for i in range(n):
        r = r_min + (r_max - r_min) * math.sqrt(rnd.random())
        a = rnd.uniform(0, 2 * math.pi)
        root = L.empty(f"{name}{i}", coll=coll)
        root.location = c + Vector((r * math.cos(a), r * math.sin(a), 0))
        col = cols[i % len(cols)]
        L.cyl(f"{name}{i}_k", 0.09 * s * 2, 0.32 * s * 2, 8, L.mat(f"ff_{col}", col, 0.6), root, (0, 0, 0.16 * s * 2), coll, r2=0.05 * s * 2)
        L.sphere(f"{name}{i}_h", 0.07 * s * 2, 8, 6, (1, 1, 1), L.mat(f"ff_haut{i % 3}", ["#E7B08A", "#C98E68", "#F1C6A4"][i % 3], 0.6), root,
                 (0, 0, 0.39 * s * 2), coll)
        for sx in (-1, 1):
            L.sphere(f"{name}{i}_a{sx}", 0.012 * s * 2, 6, 4, (1, 1, 1), L.mat("ff_auge", "#17142a", 0.5), root,
                     (sx * 0.025 * s * 2, -0.065 * s * 2, 0.4 * s * 2), coll)
        root.scale = (0, 0, 0)
        out.append(P(root=root, r=r, a=a, rz0=rnd.uniform(-math.pi, math.pi)))
    return out


def figuren_poppen(T, figs, f_pop_fn, f1, ziel_rz_fn):
    """Jede Figur poppt bei f_pop_fn(fig) mit Ueberschwingen auf, springt kurz und dreht sich zur Mitte."""
    for g in figs:
        fp = f_pop_fn(g)
        rz1 = ziel_rz_fn(g)
        T.set(g.root, "scale", lambda f, fp=fp: (pop(f, fp, 7, 1.3),) * 3 if f >= fp else (0, 0, 0), 0, f1)
        T.set(g.root, "rotation_euler", lambda f, fp=fp, g=g, rz1=rz1: (0, 0, lerp(g.rz0, rz1, ease_out_back(clamp01((f - fp - 6) / 9), 1.6))), fp, f1)
        base = tuple(g.root.location)
        T.set(g.root, "location", lambda f, fp=fp, base=base: (base[0], base[1], base[2] + 0.12 * math.sin(math.pi * clamp01((f - fp - 5) / 8))), fp, f1)


# ------------------------------------------------------------------ Stempel GESTERN / HEUTE
def stempel(coll, name, text, farbe=ROT, breite=0.9, hoehe=0.3):
    """Stempelabdruck (Vorderseite -Y): Rahmen, Text, leicht schraeg. pivot = Oberkante (zum Aufklappen)."""
    root = L.empty(name, coll=coll)
    piv = L.empty(f"{name}_piv", root, (0, 0, 0), coll)
    m = L.mat(f"st_{farbe}", farbe, 0.5, emit=farbe, strength=1.6)
    m_bg = L.mat("st_papier", "#FBF3E4", 0.6, emit="#FBF3E4", strength=0.9)
    inner = L.empty(f"{name}_in", piv, (0, 0, -hoehe / 2), coll)
    inner.rotation_euler = (0, math.radians(-6), 0)
    L.box(f"{name}_bg", (breite, 0.01, hoehe), m_bg, inner, (0, 0.006, 0), coll, bevel=0.02)
    t = 0.028
    for nm, sz, lo in (("o", (breite - 0.06, 0.012, t), (0, 0, hoehe / 2 - 0.05)), ("u", (breite - 0.06, 0.012, t), (0, 0, -hoehe / 2 + 0.05)),
                       ("l", (t, 0.012, hoehe - 0.1), (-breite / 2 + 0.045, 0, 0)), ("r", (t, 0.012, hoehe - 0.1), (breite / 2 - 0.045, 0, 0))):
        L.box(f"{name}_{nm}", sz, m, inner, lo, coll)
    _text(f"{name}_t", text, hoehe * 0.5, m, inner, (0, -0.004, -hoehe * 0.16), coll, extrude=0.004)
    root.scale = (0, 0, 0)
    return P(root=root, piv=piv)


def stempel_klappen(T, st, f, f_aus, s=1.0):
    """Klappt um die Oberkante von hinten herunter (Ueberschwingen), Pop, am Ende kleiner Ausblend-Pop."""
    T.set(st.piv, "rotation_euler", lambda x: (math.pi / 2 * (1 - ease_out_back(clamp01((x - f) / 9), 2.4)), 0, 0), f - 1, f + 10)
    T.set(st.root, "scale", lambda x: ((s * pop(x, f, 6, 1.18) * (unpop(x, f_aus, 6) if x > f_aus else 1)) if f <= x < f_aus + 7 else 0,) * 3,
          0, 10 ** 5)


# ------------------------------------------------------------------ Fragezeichen
def fragezeichen(coll, name, s=0.28):
    root = L.empty(name, coll=coll)
    m = L.unique_mat(L.mat("fz_grau", "#9A98A6", 0.5, emit="#B6B4C2", strength=0.6, alpha=0.95), f"{name}_m")
    _text(f"{name}_t", "?", s, m, root, (0, 0, 0), coll, extrude=0.02)
    root.scale = (0, 0, 0)
    return P(root=root, m=m)


def fragezeichen_an(T, q, f, dauer, folge_fn, rz=0.0):
    """Poppt ueber folge_fn(f) auf, schwebt mit, loest sich nach dauer auf (schrumpft, steigt, wird durchsichtig)."""
    T.set(q.root, "location", lambda x: tuple(Vector(folge_fn(x)) + Vector((0, 0, 0.2 * clamp01((x - f - dauer + 10) / 10)))), f - 1, f + dauer + 1)
    T.set(q.root, "scale", lambda x: (pop(x, f, 6, 1.3) * (1 - ease_in(clamp01((x - f - dauer + 10) / 10))) if f <= x < f + dauer else 0,) * 3, 0, 10 ** 5)
    T.set(q.root, "rotation_euler", lambda x: (math.pi / 2, 0, rz + 0.25 * math.sin((x - f) * 0.2)), f - 1, f + dauer + 1)
    T.set(q.m, "diffuse_color", lambda x: 0.95 * (1 - clamp01((x - f - dauer + 10) / 10)), f, f + dauer, index=3)
