"""Set 'stadtkarte' (Engine 2.3): Low-Poly-Stadtdiorama auf einer schwebenden runden Platte.

Ursprung (160, 0, 0). Plattenmitte S.p(0, 1.0, 0), Oberseite auf Hoehe S.pz (wie die Theke), Radius S.r.
Lokale Koordinaten (x, y) relativ zur Plattenmitte, z = Hoehe ueber der Oberflaeche; S.welt(x, y, z, f) rechnet
in Weltkoordinaten um (die Platte kann sich drehen: S.dreh_fn(f) in Radiant, Standard 0).

Viertel (S.viertel[name] = lokale Mitte):
  altstadt     links: Fachwerkhaeuser, Kirchturm, Marktplatz mit Weihnachtsbaum, zwei kleine Baeckereien mit Markisen
  neubaugebiet hinten rechts: gleichfoermige weisse Wuerfelhaeuser, viel Gruen, leere Strassen
  bahnhof      vorn rechts: Bahnhofsgebaeude mit Uhr (Turm) und Anzeigetafel, Gleise, Zug, Bushaltestelle, Kiosk,
               leerer Laden (S.objs['laden'])
Dazu Fluss mit Bruecke, Strassen, Kalles Baeckerei (vorn links) mit rotem Brezel-Pin.

Datenebenen (einzeln zuschaltbar, die Regie liest dafuer das Feld 'visual', siehe ebenen_aus_visual):
  personen(...)      Personenstroeme als leuchtende Punkte, Dichte = Passanten (dichte_fn 0..1)
  pin(...)           nummerierte Standort-Pins, die aus dem Boden steigen (pin_steigen, pin_farbe)
  konkurrenz(...)    graue Brezel-Marker fuer Wettbewerber
  heatmap(...)       Schleier rot (belebt) / blau (ruhig)
  info_karte(...)    schwebende, beschriftbare Info-Karten (hoechstens 3 Zeilen)
Kamera: drohnenflug(...) (weicher Flug mit Schraeglage in Kurven), totale_oben(S), tief_viertel(S, viertel).
Figuren: Kalle steht vorn an der Plattenkante (S.kalle, Kante S.kante), Byte schwebt ueber der Platte (S.byte);
die Regie kann beide auch klein (Massstab) auf die Platte stellen oder wie bisher im Vordergrund zeigen.
Alle Materialien heissen 'sk_*'."""
import math
import random

import bpy
from mathutils import Vector

import look as L
from anim import ease_in_out, ease_out, ease_out_back, pop, unpop, clamp01

FPS = 30
R = 2.6          # Plattenradius
PZ = 1.02        # Hoehe der Oberflaeche
MITTE = (0.0, 1.0)

GRAS = "#7FBF5A"
GRAS2 = "#94CF6A"
ERDE = "#7A5236"
ERDE2 = "#5A3A26"
WASSER = "#4FA3E0"
STRASSE = "#8D8FA3"
PFLASTER = "#C9B79A"
WEISS = "#F4F2EC"
NAVY = "#141228"
ROT = "#E5484D"
GELB = "#FFE14D"
GRUEN = "#3DDC84"
GRAU = "#9A9CAB"
TURQ = "#2EE6D6"
GOLD = "#F2B45A"


def m(name, col, r=0.6, **kw):
    return L.mat(f"sk_{name}", col, r, **kw)


def _text(name, s, size, mat, parent, loc, coll, rot=(math.pi / 2, 0, 0), align="CENTER", extrude=0.004):
    return L.text(name, s, size, mat, parent, loc, coll, extrude=extrude, rot=rot, font=L.font(), align=align)


class P:
    def __init__(self, **kw):
        self.__dict__.update(kw)


# ------------------------------------------------------------------ Bausteine
def haus(name, parent, coll, loc, w, d, h, wand, dach, fachwerk=False, rot=0.0, fenster="#2C3E66", flach=False,
         dach_h=None):
    """Haus mit Satteldach (Giebel nach vorn/hinten) oder Flachdach. loc = lokale Mitte am Boden."""
    o = L.empty(name, parent, loc, coll)
    o.rotation_euler = (0, 0, rot)
    L.box(f"{name}_b", (w, d, h), wand, o, (0, 0, h / 2), coll)
    if flach:
        L.box(f"{name}_r", (w + 0.02, d + 0.02, 0.025), dach, o, (0, 0, h + 0.012), coll)
    else:
        rh = dach_h or w * 0.55
        L.poly_flat(f"{name}_r", [(-w / 2 - 0.02, 0), (w / 2 + 0.02, 0), (0, rh)], d + 0.03, dach, o, (0, 0, h), coll)
    # Fenster vorn (-Y), 2 je Etage
    mw = m("fenster" + fenster, fenster, 0.4)
    et = max(1, int(h / 0.13))
    for e in range(et):
        z = 0.07 + e * (h - 0.06) / et
        for sx in ((-0.25, 0.25) if w > 0.14 else (0.0,)):
            L.box(f"{name}_w{e}{sx}", (w * 0.18, 0.006, 0.045), mw, o, (sx * w, -d / 2 - 0.003, z + 0.02), coll)
    if fachwerk:
        mb = m("balken", "#5A3826", 0.6)
        for sx in (-0.5, 0.0, 0.5):
            L.box(f"{name}_fp{sx}", (0.012, 0.006, h), mb, o, (sx * w * 0.96, -d / 2 - 0.004, h / 2), coll)
        for z in (h * 0.48, h - 0.01):
            L.box(f"{name}_fh{z:.3f}", (w, 0.006, 0.012), mb, o, (0, -d / 2 - 0.004, z), coll)
        for sx in (-1, 1):
            b = L.box(f"{name}_fd{sx}", (0.012, 0.006, h * 0.5), mb, o, (sx * w * 0.25, -d / 2 - 0.005, h * 0.24), coll)
            b.rotation_euler = (0, sx * 0.55, 0)
    return o


def baum(name, parent, coll, loc, s=1.0, col=None):
    o = L.empty(name, parent, loc, coll)
    o.scale = (s, s, s)
    L.cyl(f"{name}_t", 0.012, 0.06, 5, m("stamm", "#6B4A30", 0.7), o, (0, 0, 0.03), coll)
    L.ico(f"{name}_k", 0.055, 1, (1, 1, 1.15), m("krone" + (col or "a"), col or "#4E9E4A", 0.7), o, (0, 0, 0.1), coll)
    return o


def brezel_form(name, parent, coll, loc, mat, s=1.0):
    """Flache Brezel-Silhouette (fuer Pins und Marker), Vorderseite -Y."""
    o = L.empty(name, parent, loc, coll)
    o.scale = (s, s, s)
    L.torus(f"{name}_bauch", 0.1, 0.022, 14, 5, mat, o, (0, 0, -0.01), coll, axis="Y").scale = (1.15, 1, 0.75)
    for sx in (-1, 1):
        t = L.torus(f"{name}_ohr{sx}", 0.05, 0.02, 10, 5, mat, o, (sx * 0.045, 0, 0.035), coll, axis="Y")
        t.rotation_euler = (0, sx * 0.5, 0)
    return o


# ------------------------------------------------------------------ Set
def build_stadtkarte(coll, origin):
    from build_world import SetData
    S = SetData("stadtkarte", origin)
    c = coll
    S.r, S.pz = R, PZ
    S.mitte = S.p(MITTE[0], MITTE[1], PZ)
    S.dreh_fn = lambda f: 0.0

    def welt(x, y, z=0.0, f=None):
        a = S.dreh_fn(f) if f is not None else 0.0
        ca, sa = math.cos(a), math.sin(a)
        return S.mitte + Vector((x * ca - y * sa, x * sa + y * ca, z))
    S.welt = welt
    # Umgebung: dunkler Boden, Rueckwand mit Lichtpunkten (Tiefe), Schatten unter der Platte
    L.cyl("sk_boden", 14.0, 0.04, 48, m("boden", "#1C1934", 0.6), None, S.p(0, 1.0, -0.02), c)
    L.cyl("sk_wand", 13.0, 12.0, 72, m("wand", "#221D45", 0.7), None, S.p(0, 1.0, 5.0), c, cap=False)
    rnd = random.Random(5)
    m_st = m("stern", "#6F67B8", 0.5)
    for k in range(70):
        a = rnd.uniform(0.35 * math.pi, 1.65 * math.pi) + math.pi / 2
        z = rnd.uniform(1.0, 9.5)
        L.ico(f"sk_stern{k}", rnd.uniform(0.02, 0.05), 0, (1, 1, 1), m_st, None,
              S.p(12.8 * math.cos(a), 1.0 + 12.8 * math.sin(a), z), c)
    L.cyl("sk_schatten", R * 0.85, 0.01, 40, m("schatten", "#120F24", 0.8), None, S.p(MITTE[0], MITTE[1], 0.0), c)
    # Platte: Rasen oben, Erdschichten, nach unten schmaler; leuchtender Rand
    root = L.empty("sk_root", None, S.mitte, c)
    S.root = root
    L.cyl("sk_gras", R, 0.06, 64, m("gras", GRAS, 0.75), root, (0, 0, -0.03), c)
    L.cyl("sk_erde", R * 0.995, 0.22, 64, m("erde", ERDE, 0.8), root, (0, 0, -0.17), c, r2=R * 0.995)
    L.cyl("sk_erde2", R * 0.99, 0.28, 64, m("erde2", ERDE2, 0.8), root, (0, 0, -0.42), c, r2=R * 0.72)
    L.torus("sk_rand", R + 0.01, 0.025, 64, 6, m("rand", TURQ, 0.4, emit=TURQ, strength=2.5), root, (0, 0, -0.06), c)
    L.torus("sk_rand_unten", R * 0.74, 0.02, 48, 6, m("rand", TURQ, 0.4, emit=TURQ, strength=2.5), root, (0, 0, -0.57), c)

    def innen(x, y, rr=R - 0.04):
        return x * x + y * y <= rr * rr

    # Fluss (von vorn nach hinten, leicht geschwungen) mit Bruecke
    flusspunkte = [(-0.5, -2.7), (-0.32, -1.6), (-0.62, -0.5), (-0.45, 0.6), (-0.72, 1.6), (-0.55, 2.7)]
    m_w = m("wasser", WASSER, 0.25, spec=0.6)
    m_w2 = m("welle", "#A8D8F5", 0.3)
    S.fluss = []
    pts = []
    for i in range(len(flusspunkte) - 1):
        a, b = Vector(flusspunkte[i]), Vector(flusspunkte[i + 1])
        for t in range(6):
            pts.append(a.lerp(b, t / 6))
    pts.append(Vector(flusspunkte[-1]))
    wellen = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        mid = (a + b) / 2
        if not innen(mid.x, mid.y, R - 0.02):
            continue
        d = b - a
        seg = L.box(f"sk_fluss{i}", (0.36, d.length + 0.03, 0.012), m_w, root, (mid.x, mid.y, 0.002), c)
        seg.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
        S.fluss.append((mid.x, mid.y))
        if i % 3 == 1:
            wv = L.box(f"sk_welle{i}", (0.1, 0.012, 0.004), m_w2, root, (mid.x + 0.05, mid.y, 0.01), c)
            wv.rotation_euler = (0, 0, math.atan2(-d.x, d.y) + math.pi / 2)
            wellen.append(wv)
    S.objs["wellen"] = wellen
    # Strassen
    m_s = m("strasse", STRASSE, 0.7)
    m_l = m("linie", WEISS, 0.6)

    def strasse(name, a, b, w=0.13, linie=True):
        a, b = Vector(a), Vector(b)
        d = b - a
        mid = (a + b) / 2
        o = L.box(name, (w, d.length, 0.008), m_s, root, (mid.x, mid.y, 0.004), c)
        o.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
        if linie:
            n = int(d.length / 0.16)
            for k in range(n):
                p = a + d * ((k + 0.5) / n)
                ln = L.box(f"{name}_l{k}", (0.008, 0.06, 0.004), m_l, root, (p.x, p.y, 0.009), c)
                ln.rotation_euler = o.rotation_euler
        return o
    strasse("sk_str_ow", (-2.5, -0.25), (-0.95, -0.25))
    strasse("sk_str_ow2", (-0.05, -0.25), (2.55, -0.25))
    strasse("sk_str_ns", (0.35, -1.2), (0.35, 2.3))
    strasse("sk_str_nb1", (0.35, 0.8), (2.15, 0.8), 0.1, False)
    strasse("sk_str_nb2", (0.35, 1.65), (1.75, 1.65), 0.1, False)
    strasse("sk_str_nb3", (1.3, 0.8), (1.3, 2.05), 0.1, False)
    strasse("sk_str_alt", (-1.5, -0.25), (-1.5, 0.15), 0.1, False)
    # Bruecke ueber den Fluss (auf Hoehe der Ost-West-Strasse)
    br = L.empty("sk_bruecke", root, (-0.5, -0.25, 0), c)
    L.box("sk_br_deck", (1.0, 0.2, 0.04), m("bruecke", "#B9A58A", 0.6), br, (0, 0, 0.045), c)
    for sy in (-1, 1):
        L.box(f"sk_br_gel{sy}", (1.0, 0.015, 0.05), m("gelaender", "#6E5A48", 0.6), br, (0, sy * 0.095, 0.09), c)
    for sx in (-0.25, 0.25):
        L.box(f"sk_br_pf{sx}", (0.06, 0.16, 0.05), m("bruecke", "#B9A58A", 0.6), br, (sx, 0, 0.02), c)
    S.objs["bruecke"] = br

    # ---------------------------------------------------- ALTSTADT
    AX, AY = -1.5, 0.5
    S.viertel = {"altstadt": (AX, AY + 0.0), "neubaugebiet": (1.3, 1.3), "bahnhof": (1.05, -0.95)}
    alt = L.empty("sk_altstadt", root, (0, 0, 0), c)
    L.cyl("sk_markt", 0.42, 0.012, 24, m("pflaster", PFLASTER, 0.7), alt, (AX, AY, 0.006), c)
    for k in range(10):                                         # Pflaster-Ringe
        pass
    L.torus("sk_markt_ring", 0.3, 0.008, 24, 4, m("pflaster2", "#B5A283", 0.7), alt, (AX, AY, 0.013), c)
    wand_cols = ["#F2E6CF", "#EAD7B5", "#F5EBDD", "#E8CFAE"]
    dach_cols = ["#C4553A", "#B04A34", "#D0673F"]
    hp = [(-0.55, 0.45, 0.4), (-0.25, 0.55, 0.2), (0.05, 0.58, -0.1), (0.35, 0.5, -0.35), (0.52, 0.2, -1.4),
          (0.55, -0.12, -1.6), (-0.62, 0.12, 1.4), (-0.64, -0.2, 1.6), (-0.9, 0.75, 0.6), (0.5, 0.85, -0.3),
          (-0.3, 0.95, 0.1), (-1.0, 0.25, 1.5)]
    for k, (dx, dy, rot) in enumerate(hp):
        x, y = AX + dx, AY + dy
        if not innen(x, y, R - 0.2):
            continue
        haus(f"sk_fw{k}", alt, c, (x, y, 0), 0.2, 0.18, 0.2 + 0.05 * (k % 3), m(f"wand{k % 4}", wand_cols[k % 4], 0.7),
             m(f"dach{k % 3}", dach_cols[k % 3], 0.65), fachwerk=True, rot=rot)
    # Kirche mit Turm
    kir = L.empty("sk_kirche", alt, (AX - 0.25, AY + 1.05, 0), c)
    haus("sk_kirchenschiff", kir, c, (0.25, 0.05, 0), 0.3, 0.5, 0.3, m("kirche", "#E9E1D2", 0.7), m("kirchdach", "#5A5F7A", 0.6),
         rot=math.pi / 2)
    L.box("sk_turm", (0.2, 0.2, 0.75), m("kirche", "#E9E1D2", 0.7), kir, (0, -0.1, 0.375), c)
    L.cyl("sk_turmspitze", 0.15, 0.4, 4, m("kirchdach", "#5A5F7A", 0.6), kir, (0, -0.1, 0.95), c, r2=0.0).rotation_euler = \
        (0, 0, math.pi / 4)
    L.cyl("sk_turmuhr", 0.055, 0.01, 16, m("uhr", WEISS, 0.5), kir, (0, -0.205, 0.62), c, axis="Y")
    L.box("sk_turmkreuz", (0.012, 0.012, 0.1), m("gold", GOLD, 0.4), kir, (0, -0.1, 1.2), c)
    L.box("sk_turmkreuz2", (0.06, 0.012, 0.012), m("gold", GOLD, 0.4), kir, (0, -0.1, 1.22), c)
    # Weihnachtsbaum auf dem Marktplatz
    wb = L.empty("sk_weihnachtsbaum", alt, (AX, AY, 0.012), c)
    m_t = m("tanne", "#2F7D45", 0.7)
    for j, (r, z) in enumerate([(0.13, 0.08), (0.1, 0.17), (0.07, 0.25)]):
        L.cyl(f"sk_wb{j}", r, 0.14, 8, m_t, wb, (0, 0, z), c, r2=0.0)
    L.ico("sk_wb_stern", 0.03, 0, (1, 1, 1), m("stern_gold", GELB, 0.3, emit=GELB, strength=3.0), wb, (0, 0, 0.34), c)
    rk = random.Random(3)
    kugeln = []
    for j in range(9):
        a = rk.uniform(0, 6.28)
        z = rk.uniform(0.04, 0.24)
        rr = 0.12 * (1 - z / 0.33) + 0.01
        col = [ROT, GELB, "#FFFFFF"][j % 3]
        kugeln.append(L.ico(f"sk_wb_k{j}", 0.014, 0, (1, 1, 1), m(f"kugel{j % 3}", col, 0.3, emit=col, strength=2.0), wb,
                            (rr * math.cos(a), rr * math.sin(a), z + 0.02), c))
    S.objs.update(weihnachtsbaum=wb, kugeln=kugeln)
    # Zwei kleine Baeckereien mit Markisen (Konkurrenz), an der Strasse, Front nach vorn
    S.baeckereien = []
    for j, (x, col1, col2) in enumerate([(AX - 0.55, ROT, WEISS), (AX + 0.45, "#3D7BD9", WEISS)]):
        bk = haus(f"sk_baeckerei{j}", alt, c, (x, AY - 0.55, 0), 0.26, 0.2, 0.22, m("wand_bk", "#F6EEDC", 0.7),
                  m(f"dach{j}", dach_cols[j], 0.65), fachwerk=True)
        for s_ in range(6):
            st = L.box(f"sk_markise{j}_{s_}", (0.045, 0.1, 0.006), m(f"mk{j}{s_ % 2}", [col1, col2][s_ % 2], 0.6), bk,
                       (-0.1125 + s_ * 0.045, -0.15, 0.13), c)
            st.rotation_euler = (-0.45, 0, 0)
        L.box(f"sk_bk_schild{j}", (0.2, 0.006, 0.04), m("schild_bk", NAVY, 0.5), bk, (0, -0.104, 0.19), c)
        _text(f"sk_bk_t{j}", "BÄCKER", 0.03, m("schild_ink", WEISS, 0.5), bk, (0, -0.109, 0.183), c, extrude=0.001)
        S.baeckereien.append((x, AY - 0.55))
    # ---------------------------------------------------- NEUBAUGEBIET
    NX, NY = 1.3, 1.3
    neu = L.empty("sk_neubau", root, (0, 0, 0), c)
    m_wh = m("weiss", WEISS, 0.7)
    m_fd = m("flachdach", "#C8CBD6", 0.7)
    m_rasen = m("rasen", GRAS2, 0.8)
    for ix in range(3):
        for iy in range(3):
            x, y = NX - 0.55 + ix * 0.5, NY - 0.45 + iy * 0.45
            if (ix, iy) == (1, 1):
                continue
            if not innen(x, y, R - 0.2):
                continue
            L.box(f"sk_nb_rasen{ix}{iy}", (0.36, 0.32, 0.006), m_rasen, neu, (x, y, 0.003), c)
            haus(f"sk_nb{ix}{iy}", neu, c, (x - 0.05, y + 0.02, 0), 0.16, 0.16, 0.16, m_wh, m_fd, flach=True,
                 fenster="#5C7BB0")
            baum(f"sk_nb_baum{ix}{iy}", neu, c, (x + 0.12, y - 0.1, 0), 0.9)
    for k in range(14):                                          # viel Gruen
        rr = random.Random(40 + k)
        x, y = NX + rr.uniform(-0.9, 0.9), NY + rr.uniform(-0.75, 0.9)
        if innen(x, y, R - 0.15) and abs(x - 0.35) > 0.12 and abs(y - 0.8) > 0.1 and abs(y - 1.65) > 0.1 \
                and abs(x - 1.3) > 0.1:
            baum(f"sk_nb_b{k}", neu, c, (x, y, 0), rr.uniform(0.8, 1.2), "#5BAF52")
    # Spielplatz in der Mitte
    L.box("sk_nb_spiel", (0.3, 0.26, 0.006), m("sand", "#E8D49A", 0.8), neu, (NX, NY, 0.004), c)
    L.box("sk_nb_rutsche", (0.04, 0.14, 0.006), m("rutsche", ROT, 0.5), neu, (NX + 0.05, NY, 0.05), c).rotation_euler = (0.6, 0, 0)
    # ---------------------------------------------------- BAHNHOF
    BX, BY = 1.05, -1.1
    bhf = L.empty("sk_bahnhof", root, (0, 0, 0), c)
    L.box("sk_bhf_platz", (1.6, 0.55, 0.008), m("pflaster", PFLASTER, 0.7), bhf, (BX, BY + 0.5, 0.004), c)
    haus("sk_bhf", bhf, c, (BX, BY, 0), 0.95, 0.3, 0.26, m("bhf", "#D9895B", 0.7), m("bhfdach", "#5A4A6A", 0.6),
         dach_h=0.12, fenster="#F2D27A")
    L.box("sk_bhf_turm", (0.18, 0.18, 0.5), m("bhf", "#D9895B", 0.7), bhf, (BX, BY - 0.02, 0.25), c)
    L.cyl("sk_bhf_turmdach", 0.14, 0.14, 4, m("bhfdach", "#5A4A6A", 0.6), bhf, (BX, BY - 0.02, 0.57), c, r2=0.0).rotation_euler \
        = (0, 0, math.pi / 4)
    # Bahnhofsuhr (Turm, Seite zur Kamera -Y) mit Zeigern
    uhr = L.empty("sk_bhf_uhr", bhf, (BX, BY - 0.115, 0.4), c)
    L.cyl("sk_uhr_rand", 0.075, 0.012, 24, m("uhrrand", NAVY, 0.5), uhr, (0, 0.004, 0), c, axis="Y")
    L.cyl("sk_uhr_bl", 0.066, 0.012, 24, m("uhr", WEISS, 0.5), uhr, (0, -0.002, 0), c, axis="Y")
    for h_ in range(12):
        a = h_ / 12 * 2 * math.pi
        L.box(f"sk_uhr_s{h_}", (0.006, 0.004, 0.016 if h_ % 3 == 0 else 0.009), m("uhrrand", NAVY, 0.5), uhr,
              (0.054 * math.sin(a), -0.01, 0.054 * math.cos(a)), c).rotation_euler = (0, a, 0)
    zh = L.empty("sk_uhr_h", uhr, (0, -0.012, 0), c)
    L.box("sk_uhr_hm", (0.008, 0.004, 0.036), m("uhrrand", NAVY, 0.5), zh, (0, 0, 0.016), c)
    zm = L.empty("sk_uhr_m", uhr, (0, -0.014, 0), c)
    L.box("sk_uhr_mm", (0.006, 0.004, 0.054), m("uhrrand", NAVY, 0.5), zm, (0, 0, 0.024), c)
    S.objs.update(uhr=uhr, uhr_h=zh, uhr_m=zm)
    # Anzeigetafel 7:15 an der Front
    taf = L.empty("sk_tafel", bhf, (BX + 0.3, BY - 0.16, 0.17), c)
    L.box("sk_tafel_b", (0.22, 0.008, 0.08), m("tafel", NAVY, 0.5), taf, (0, 0, 0), c)
    S.objs["tafel_text"] = _text("sk_tafel_t", "7:15", 0.06, m("tafel_ink", GELB, 0.3, emit=GELB, strength=3.0), taf,
                                 (0, -0.006, -0.003), c, extrude=0.001)
    S.objs["tafel"] = taf
    _text("sk_bhf_schild", "BAHNHOF", 0.05, m("schild_ink2", WEISS, 0.5), bhf, (BX - 0.27, BY - 0.158, 0.2), c,
          extrude=0.002)
    L.box("sk_bhf_schild_b", (0.26, 0.006, 0.06), m("schild_bk", NAVY, 0.5), bhf, (BX - 0.27, BY - 0.154, 0.2), c)
    # Gleise (Ost-West, vor dem Bahnhof) und Bahnsteig
    GY = BY - 0.42
    S.gleis_y = GY
    L.box("sk_bahnsteig", (1.3, 0.12, 0.04), m("bahnsteig", "#B8B3A8", 0.7), bhf, (BX + 0.05, BY - 0.24, 0.02), c)
    x0 = -0.05
    x1 = math.sqrt(R * R - GY * GY) - 0.03
    L.box("sk_gleisbett", (x1 - x0, 0.2, 0.012), m("schotter", "#8A8074", 0.8), bhf, ((x0 + x1) / 2, GY, 0.006), c)
    m_sch = m("schiene", "#C9CCD8", 0.3, metallic=0.5)
    for sy in (-0.045, 0.045):
        L.box(f"sk_schiene{sy}", (x1 - x0, 0.012, 0.014), m_sch, bhf, ((x0 + x1) / 2, GY + sy, 0.02), c)
    n_sw = int((x1 - x0) / 0.06)
    for k in range(n_sw):
        L.box(f"sk_schwelle{k}", (0.022, 0.15, 0.008), m("schwelle", "#5E4636", 0.7), bhf, (x0 + 0.03 + k * 0.06, GY, 0.013), c)
    L.box("sk_prellbock", (0.04, 0.14, 0.06), m("prell", ROT, 0.5), bhf, (x0, GY, 0.04), c)
    S.gleis = (x0, x1)
    # Zug (faehrt von rechts ein)
    zug = L.empty("sk_zug", root, (x1 + 2.0, GY, 0.03), c)
    m_z = m("zug", "#E8EDF5", 0.5)
    m_z2 = m("zugrot", ROT, 0.5)
    m_zf = m("zugfenster", "#2C3E66", 0.3)
    for w_ in range(3):
        wx = w_ * 0.44
        L.box(f"sk_zug_w{w_}", (0.42, 0.12, 0.12), m_z, zug, (wx, 0, 0.07), c, bevel=0.015)
        L.box(f"sk_zug_s{w_}", (0.42, 0.124, 0.025), m_z2, zug, (wx, 0, 0.04), c)
        for f_ in range(4):
            L.box(f"sk_zug_f{w_}{f_}", (0.06, 0.126, 0.035), m_zf, zug, (wx - 0.15 + f_ * 0.1, 0, 0.095), c)
    L.box("sk_zug_nase", (0.06, 0.11, 0.1), m_z2, zug, (-0.24, 0, 0.065), c, bevel=0.02)
    L.ico("sk_zug_licht", 0.014, 0, (1, 1, 1), m("zuglicht", GELB, 0.3, emit=GELB, strength=3.0), zug, (-0.27, -0.035, 0.05), c)
    S.objs["zug"] = zug
    # Bushaltestelle, Kiosk, leerer Laden
    bus = L.empty("sk_bus", bhf, (BX + 0.62, BY + 0.62, 0), c)
    L.box("sk_bus_dach", (0.24, 0.1, 0.012), m("glasdach", "#9FC9E8", 0.3), bus, (0, 0, 0.16), c)
    for sx in (-0.11, 0.11):
        L.box(f"sk_bus_p{sx}", (0.012, 0.012, 0.16), m("metall", "#7E8299", 0.4), bus, (sx, 0.04, 0.08), c)
    L.box("sk_bus_rw", (0.22, 0.008, 0.12), m("glas", "#BFE0F5", 0.3), bus, (0, 0.045, 0.08), c)
    L.cyl("sk_bus_schild", 0.035, 0.008, 16, m("bus_schild", "#F2C94C", 0.5), bus, (0.15, -0.02, 0.2), c, axis="Y")
    L.box("sk_bus_mast", (0.01, 0.01, 0.2), m("metall", "#7E8299", 0.4), bus, (0.15, -0.015, 0.1), c)
    _text("sk_bus_h", "H", 0.04, m("schild_ink3", "#2E7D32", 0.5), bus, (0.15, -0.026, 0.198), c, extrude=0.001)
    kio = L.empty("sk_kiosk", bhf, (BX - 0.55, BY + 0.62, 0), c)
    L.box("sk_kiosk_b", (0.2, 0.16, 0.15), m("kiosk", "#5BA3A0", 0.6), kio, (0, 0, 0.075), c)
    L.box("sk_kiosk_d", (0.24, 0.2, 0.02), m("kioskdach", "#2F5F6A", 0.6), kio, (0, 0, 0.16), c)
    L.box("sk_kiosk_fen", (0.14, 0.006, 0.06), m("kioskfen", "#F2D27A", 0.4), kio, (0, -0.083, 0.09), c)
    L.box("sk_kiosk_sb", (0.18, 0.006, 0.04), m("schild_bk", NAVY, 0.5), kio, (0, -0.104, 0.19), c)
    _text("sk_kiosk_t", "KIOSK", 0.03, m("schild_ink", WEISS, 0.5), kio, (0, -0.109, 0.183), c, extrude=0.001)
    L.box("sk_kiosk_sbh", (0.012, 0.012, 0.03), m("metall", "#7E8299", 0.4), kio, (0, -0.095, 0.17), c)
    S.objs["kiosk"] = kio
    lad = L.empty("sk_laden", bhf, (BX + 0.05, BY + 0.72, 0), c)
    haus("sk_laden_h", lad, c, (0, 0, 0), 0.26, 0.2, 0.2, m("laden", "#E9E4F2", 0.7), m("ladendach", "#8A86A8", 0.6),
         flach=True, fenster="#3A3F5C")
    L.box("sk_laden_tuer", (0.06, 0.006, 0.1), m("ladentuer", "#3A3F5C", 0.5), lad, (0.08, -0.103, 0.05), c)
    S.objs["laden"] = lad
    S.laden = (BX + 0.05, BY + 0.72)
    # Kalles Baeckerei (vorn links) mit rotem Brezel-Pin
    KX, KY = -1.55, -1.25
    kb = haus("sk_kalle_bk", root, c, (KX, KY, 0), 0.34, 0.24, 0.26, m("kalle_wand", "#F3E3C3", 0.7),
              m("kalle_dach", "#B04A34", 0.65), fachwerk=True)
    for s_ in range(8):
        st = L.box(f"sk_kmark{s_}", (0.045, 0.12, 0.006), m(f"kmark{s_ % 2}", [GOLD, WEISS][s_ % 2], 0.6), kb,
                   (-0.1575 + s_ * 0.045, -0.18, 0.15), c)
        st.rotation_euler = (-0.45, 0, 0)
    L.box("sk_kalle_schild", (0.3, 0.006, 0.05), m("schild_bk", NAVY, 0.5), kb, (0, -0.124, 0.225), c)
    _text("sk_kalle_t", "KALLE", 0.038, m("schild_gold", GOLD, 0.4), kb, (0, -0.129, 0.217), c, extrude=0.001)
    kpin = L.empty("sk_kalle_pin", root, (KX, KY, 0.72), c)
    L.cyl("sk_kpin_stiel", 0.012, 0.36, 8, m("pinstiel", "#E9E9F2", 0.4), kpin, (0, 0, -0.2), c)
    L.ico("sk_kpin_spitze", 0.02, 0, (1, 1, 1.4), m("pinstiel", "#E9E9F2", 0.4), kpin, (0, 0, -0.38), c)
    L.cyl("sk_kpin_kopf", 0.17, 0.05, 24, m("pinrot", ROT, 0.4, emit=ROT, strength=1.2), kpin, (0, 0, 0.02), c, axis="Y")
    brezel_form("sk_kpin_brezel", kpin, c, (0, -0.03, 0.02), m("pinbrezel", WEISS, 0.4), 0.9)
    S.objs["kalle_pin"] = kpin
    S.kalle_bk = (KX, KY)
    # Baeume und Park am Fluss
    for k, (x, y) in enumerate([(-0.95, 1.1), (-1.05, 1.5), (0.0, 1.0), (0.1, 1.4), (-0.15, 2.1), (-2.2, -0.8),
                                (-0.9, -1.0), (-0.05, -1.3), (-2.0, 1.1), (-1.15, -1.8), (0.15, 0.3), (-0.15, -2.3),
                                (2.2, -0.55), (1.95, 0.25), (-2.35, 0.3)]):
        if innen(x, y, R - 0.12):
            baum(f"sk_baum{k}", root, c, (x, y, 0), 1.0 + 0.2 * (k % 3))
    # Licht (fuer Cycles/Eevee; Workbench nutzt Objektfarben)
    from build_world import _lights
    _lights(S, c, key=(-3.0, -3.5, 5.0), fill=(3.4, -3.0, 2.5), rim=(1.6, 4.0, 4.0), key_e=900, fill_e=220, rim_e=500)
    S.kante = S.p(MITTE[0], MITTE[1] - R, 0)
    S.kalle = S.p(MITTE[0] - 0.55, MITTE[1] - R - 0.42, 0.0)
    S.byte = S.p(MITTE[0] + 0.6, MITTE[1] - R - 0.1, PZ + 0.85)
    S.top_z = PZ
    S.objs["root"] = root
    S.cams = {"totale_oben": totale_oben(S)}
    return S


# ------------------------------------------------------------------ Bewegung im Set
def leben(T, S, f0, f1):
    """Grundbewegung: Wellen auf dem Fluss, Weihnachtskugeln funkeln, Kalle-Pin schwebt."""
    for k, wv in enumerate(S.objs["wellen"]):
        x0, y0 = wv.location.x, wv.location.y
        T.set(wv, "location", lambda f, x0=x0, y0=y0, k=k: (x0 + 0.04 * math.sin(f * 0.08 + k), y0 + ((f * 0.004 + k * 0.1) % 0.12) - 0.06,
                                                         0.01), f0, f1)
    for k, kg in enumerate(S.objs["kugeln"]):
        T.set(kg, "scale", lambda f, k=k: ((0.8 + 0.35 * max(0.0, math.sin(f * 0.25 + k * 1.7))),) * 3, f0, f1)
    kp = S.objs["kalle_pin"]
    z0 = kp.location.z
    T.set(kp, "location", lambda f: (S.kalle_bk[0], S.kalle_bk[1], z0 + 0.03 * math.sin(f * 0.12)), f0, f1)
    T.set(kp, "rotation_euler", lambda f: (0, 0, 0.25 * math.sin(f * 0.05)), f0, f1)


def drehen(T, S, f0, f1, fn):
    """Platte drehen (fn(f) in Radiant). Daten-Ebenen folgen ueber S.welt(..., f)."""
    S.dreh_fn = fn
    T.set(S.root, "rotation_euler", lambda f: (0, 0, fn(f)), f0, f1)


def bahnhofsuhr(T, S, minuten_fn, f0, f1):
    """Zeiger der Bahnhofsuhr: minuten_fn(f) = Minuten seit 0:00 (7:15 -> 435)."""
    T.set(S.objs["uhr_m"], "rotation_euler", lambda f: (0, (minuten_fn(f) % 60) / 60 * 2 * math.pi, 0), f0, f1)
    T.set(S.objs["uhr_h"], "rotation_euler", lambda f: (0, (minuten_fn(f) / 60 % 12) / 12 * 2 * math.pi, 0), f0, f1)


def zug_fahrt(T, S, f0, f_halt, f1=None, x_halt=None):
    """Zug faehrt von rechts ein und haelt am Bahnsteig (ease out); ab f1 faehrt er wieder ab (optional)."""
    z = S.objs["zug"]
    xa = S.gleis[1] + 1.6
    xh = x_halt if x_halt is not None else 0.62
    y, zz = S.gleis_y, 0.03

    def x(f):
        if f < f0:
            return xa
        if f < f_halt:
            return xa + (xh - xa) * ease_out((f - f0) / max(1, f_halt - f0))
        if f1 is not None and f >= f1:
            t = (f - f1) / 40
            return xh - 3.0 * t * t
        return xh
    T.set(z, "location", lambda f: (x(f), y, zz), f0 - 1, (f1 + 60) if f1 else f_halt + 1)
    # ausserhalb der Platte unsichtbar
    T.set(z, "scale", lambda f: (1, 1, 1) if -0.5 < x(f) < S.gleis[1] + 0.3 else (0, 0, 0), f0 - 1,
          (f1 + 60) if f1 else f_halt + 1)


# ------------------------------------------------------------------ Datenebenen
def billboard(T, W, obj, pos_fn, f0, f1, tilt=1.0):
    """Objekt (Vorderseite -Y) dreht sich zur Kamera. pos_fn(f) = Weltposition."""
    def rot(f):
        cp = W.cam.state(int(min(max(f, 0), W.n - 1)))[0]
        d = cp - Vector(pos_fn(f))
        h = math.hypot(d.x, d.y)
        return (-math.atan2(d.z, h) * tilt, 0, math.atan2(d.x, -d.y))
    T.set(obj, "rotation_euler", rot, f0, f1)


def personen(T, S, coll, name, pfade, n, f0, f1, dichte_fn=lambda f: 1.0, farbe="#FFF3B0", r=0.022, tempo=1.0,
             seed=1, hoehe=0.03):
    """Personenstroeme: n leuchtende Punkte laufen entlang der Pfade (Listen lokaler (x, y)-Punkte).
    Sichtbar ist der Anteil dichte_fn(f) (0..1). Rueckgabe: Liste P(obj, mat, pos_fn)."""
    rnd = random.Random(seed)
    mat = m(f"punkt_{farbe}", farbe, 0.3, emit=farbe, strength=3.0)
    out = []
    lens = []
    for p in pfade:
        segs = [(Vector(p[i]), Vector(p[i + 1])) for i in range(len(p) - 1)]
        lens.append((segs, sum((b - a).length for a, b in segs)))
    for k in range(n):
        segs, total = lens[k % len(lens)]
        off = rnd.uniform(0, total)
        sp = rnd.uniform(0.010, 0.016) * tempo
        lat = rnd.uniform(-0.035, 0.035)
        thr = rnd.uniform(0, 1)
        o = L.ico(f"{name}{k}", r, 1, (1, 1, 1), mat, None, (0, 0, 0), coll)

        def pos(f, segs=segs, total=total, off=off, sp=sp, lat=lat):
            d = (off + f * sp) % total
            for a, b in segs:
                ln = (b - a).length
                if d <= ln:
                    q = a + (b - a) * (d / max(1e-6, ln))
                    nrm = Vector((-(b - a).y, (b - a).x)).normalized() * lat
                    return S.welt(q.x + nrm.x, q.y + nrm.y, hoehe + 0.006 * math.sin(f * 0.7 + off * 9), f)
                d -= ln
            return S.welt(segs[-1][1].x, segs[-1][1].y, hoehe, f)
        T.set(o, "location", lambda f, pos=pos: tuple(pos(f)), f0, f1)
        T.set(o, "scale", lambda f, thr=thr: (1.0,) * 3 if thr < dichte_fn(f) else (0.0,) * 3, f0, f1)
        out.append(P(obj=o, mat=mat, pos=pos, thr=thr))
    return out


def pin(coll, name, nummer, text, farbe=GELB):
    """Nummerierter Standort-Pin: Stiel, runder Kopf mit Zahl, Schild mit Namen darunter. Eigenes Material
    (Farbe umschaltbar ueber pin_farbe). Vorderseite -Y (billboard)."""
    root = L.empty(name, coll=coll)
    kopf_m = L.unique_mat(m("pin", farbe, 0.4), f"sk_{name}_mat")
    kopf_m.diffuse_color = L.srgb(farbe)
    L.cyl(f"{name}_stiel", 0.014, 0.42, 8, m("pinstiel", "#E9E9F2", 0.4), root, (0, 0, 0.21), coll)
    L.ico(f"{name}_spitze", 0.024, 0, (1, 1, 1.3), m("pinstiel", "#E9E9F2", 0.4), root, (0, 0, 0.0), coll)
    kopf = L.empty(f"{name}_kopf", root, (0, 0, 0.56), coll)
    L.cyl(f"{name}_kreis", 0.15, 0.05, 28, kopf_m, kopf, (0, 0, 0), coll, axis="Y")
    L.torus(f"{name}_ring", 0.15, 0.014, 28, 5, m("pinring", NAVY, 0.4), kopf, (0, 0, 0), coll, axis="Y")
    _text(f"{name}_n", str(nummer), 0.19, m("pinzahl", NAVY, 0.5), kopf, (0, -0.03, -0.01), coll, extrude=0.004)
    schild = L.empty(f"{name}_schild", kopf, (0, 0, 0.27), coll)
    w = 0.085 * len(text) + 0.12
    L.box(f"{name}_sb", (w, 0.02, 0.17), m("schild_navy", NAVY, 0.5), schild, (0, 0, 0), coll, bevel=0.03, seg=2)
    _text(f"{name}_st", text, 0.13, m("schild_weiss", WEISS, 0.5), schild, (0, -0.014, -0.006), coll, extrude=0.002)
    root.scale = (0, 0, 0)
    return P(root=root, kopf=kopf, mat=kopf_m, schild=schild, nummer=nummer)


def pin_steigen(T, W, S, p, x, y, f_in, f_out=None, s=1.0, schild=True):
    """Pin steigt aus dem Boden (mit Ueberschwingen) an der lokalen Stelle (x, y), dreht den Kopf zur Kamera."""
    end = (f_out + 10) if f_out is not None else W.n - 1

    def rise(f):
        t = clamp01((f - f_in) / 12)
        h = -0.5 + 0.5 * ease_out_back(t, 2.2)
        if f_out is not None and f > f_out:
            h -= 0.6 * clamp01((f - f_out) / 8) ** 2
        return h

    def pos(f):
        return S.welt(x, y, rise(f) * s, f)
    T.set(p.root, "location", lambda f: tuple(pos(f)), f_in - 1, end)
    T.set(p.root, "scale", lambda f: (s,) * 3 if (f >= f_in and (f_out is None or f < f_out + 9)) else (0,) * 3,
          f_in - 1, end)
    billboard(T, W, p.kopf, lambda f: pos(f) + Vector((0, 0, 0.56 * s)), f_in - 1, end, tilt=0.6)
    if not schild:
        p.schild.scale = (0, 0, 0)


def pin_farbe(T, p, farbe_fn, f0, f1):
    """Kopffarbe umschalten: farbe_fn(f) -> Hex ('#FFE14D' gelb, '#9A9CAB' grau, '#3DDC84' gruen)."""
    cache = {}

    def col(f):
        h = farbe_fn(f)
        if h not in cache:
            cache[h] = L.srgb(h)
        return cache[h]
    T.set(p.mat, "diffuse_color", col, f0, f1)


def konkurrenz(coll, name):
    """Grauer Brezel-Marker (Wettbewerber) auf kurzem Stab."""
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_stab", 0.01, 0.22, 6, m("kstab", "#C8CAD6", 0.5), root, (0, 0, 0.11), coll)
    kopf = L.empty(f"{name}_kopf", root, (0, 0, 0.3), coll)
    L.cyl(f"{name}_scheibe", 0.12, 0.03, 24, m("kgrau", "#6E7186", 0.5), kopf, (0, 0.012, 0), coll, axis="Y")
    brezel_form(f"{name}_brezel", kopf, coll, (0, -0.012, 0.01), m("kbrezel", "#C9CBD6", 0.5), 0.85)
    root.scale = (0, 0, 0)
    return P(root=root, kopf=kopf)


def marker_setzen(T, W, S, mk, x, y, f_in, f_out=None, s=1.0):
    end = (f_out + 8) if f_out is not None else W.n - 1

    def pos(f):
        drop = (1 - ease_out(clamp01((f - f_in) / 8))) * 0.4
        return S.welt(x, y, drop, f)
    T.set(mk.root, "location", lambda f: tuple(pos(f)), f_in - 1, end)
    T.set(mk.root, "scale", lambda f: (s * pop(f, f_in, 8) * (unpop(f, f_out, 6) if f_out is not None and f > f_out else 1),) * 3,
          f_in - 1, end)
    billboard(T, W, mk.kopf, lambda f: pos(f) + Vector((0, 0, 0.3 * s)), f_in - 1, end, tilt=0.5)


def heatmap(T, S, coll, name, x, y, radius, f0, f1, farbe_fn, staerke_fn=lambda f: 1.0, ringe=4):
    """Heatmap-Schleier: konzentrische, halbtransparente Scheiben (innen kraeftiger). farbe_fn(f) -> 'rot'|'blau'."""
    farben = {"rot": L.srgb("#FF3B3B"), "blau": L.srgb("#3B7BFF"), "gelb": L.srgb("#FFC83B")}
    scheiben = []
    for k in range(ringe):
        rr = radius * (1 - k / ringe)
        mt = bpy.data.materials.new(f"sk_{name}_hm{k}")
        mt.surface_render_method = "BLENDED"
        mt.diffuse_color = (1, 0, 0, 0.2)
        o = L.cyl(f"{name}{k}", rr, 0.004, 40, mt, None, (0, 0, 0), coll)

        def col(f, k=k):
            c_ = farben[farbe_fn(f)]
            a = (0.16 + 0.05 * k) * clamp01(staerke_fn(f)) * (0.9 + 0.1 * math.sin(f * 0.15 + k))
            return (c_[0], c_[1], c_[2], a)
        T.set(mt, "diffuse_color", col, f0, f1)
        T.set(o, "location", lambda f, k=k: tuple(S.welt(x, y, 0.03 + 0.012 * k, f)), f0, f1)
        T.set(o, "scale", lambda f: (1, 1, 1) if staerke_fn(f) > 0.01 else (0, 0, 0), f0, f1)
        scheiben.append(o)
    return scheiben


def info_karte(coll, name, zeilen, breite=None, akzent=TURQ):
    """Schwebende Info-Karte: weisse Karte mit farbigem Rand, hoechstens 3 Stichworte. Vorderseite -Y."""
    zeilen = list(zeilen)[:3]
    root = L.empty(name, coll=coll)
    card = L.empty(f"{name}_card", root, (0, 0, 0), coll)
    n = len(zeilen)
    lh = 0.15
    w = breite or (0.075 * max(len(z) for z in zeilen) + 0.2)
    h = n * lh + 0.12
    L.box(f"{name}_rand", (w + 0.04, 0.02, h + 0.04), m("karte_rand" + akzent, akzent, 0.4, emit=akzent, strength=1.5),
          card, (0, 0.006, 0), coll, bevel=0.04, seg=2)
    L.box(f"{name}_bg", (w, 0.025, h), m("karte_bg", WEISS, 0.5), card, (0, 0, 0), coll, bevel=0.03, seg=2)
    for j, z in enumerate(zeilen):
        zz = (n - 1) / 2 * lh - j * lh
        _text(f"{name}_z{j}", z, 0.115, m("karte_ink", NAVY, 0.5), card, (0, -0.016, zz - 0.035), coll, extrude=0.002)
    root.scale = (0, 0, 0)
    return P(root=root, card=card, w=w, h=h)


def karte_zeigen(T, W, S, k, x, y, z, f_in, f_out=None, s=1.0, welt=None):
    """Info-Karte erscheint (Pop), schwebt leicht und schaut zur Kamera. welt: feste Weltposition statt (x, y, z)."""
    end = (f_out + 8) if f_out is not None else W.n - 1

    def pos(f):
        base = Vector(welt) if welt is not None else S.welt(x, y, z, f)
        return base + Vector((0, 0, 0.025 * math.sin((f - f_in) * 0.12)))
    T.set(k.root, "location", lambda f: tuple(pos(f)), f_in - 1, end)
    T.set(k.root, "scale", lambda f: (s * pop(f, f_in, 9) * (unpop(f, f_out, 7) if f_out is not None and f > f_out else 1),) * 3,
          f_in - 1, end)
    billboard(T, W, k.root, pos, f_in - 1, end, tilt=0.8)


def ebenen_aus_visual(visual: str) -> set:
    """Welche Datenebenen eine Szene laut 'visual' braucht (Schluesselwoerter)."""
    v = visual.lower()
    out = set()
    for key, words in {"personen": ("punkte", "personen", "passanten", "strom"), "pins": ("pin",),
                       "konkurrenz": ("marker", "konkurrenz"), "heatmap": ("heatmap",),
                       "karte": ("info-karte", "infokarte", "karte '", "karte „")}.items():
        if any(w in v for w in words):
            out.add(key)
    return out


# ------------------------------------------------------------------ Kamera
def totale_oben(S, hoehe=1.0):
    """Schraeg von oben auf die ganze Platte (passt in 9:16)."""
    c_ = S.mitte
    return (c_ + Vector((0.0, -6.2 * hoehe, 4.9 * hoehe)), c_ + Vector((0.0, -0.25, -0.35)), 28.0)


def tief_viertel(S, viertel, dist=1.5, hoehe=0.42, seite=0.0, lens=24.0, f=None):
    """Tiefer Standpunkt am Rand eines Viertels (knapp ueber den Daechern), Blick ins Viertel."""
    x, y = S.viertel[viertel] if isinstance(viertel, str) else viertel
    ziel = S.welt(x, y, 0.12, f)
    pos = S.welt(x + seite, y - dist, hoehe, f)
    return (pos, ziel, lens)


def drohnenflug(keys, ziele, lens=26.0, bank=1.0, ease=ease_in_out):
    """Weicher Drohnenflug: keys = [(frame, pos)], ziele = [(frame, ziel)] (Catmull-Rom). In Kurven legt sich die
    Kamera in die Schraeglage (Roll ~ Gierrate, gegleaettet). lens: Zahl oder fn(f). Rueckgabe: fn(f) fuer add_shot."""
    from choreo.common import path
    pf = path(keys, ease)
    tf = path(ziele, ease)

    def heading(f):
        a, b = Vector(pf(f - 1)), Vector(pf(f + 1))
        ta, tb = Vector(tf(f - 1)) - a, Vector(tf(f + 1)) - b
        return math.atan2(ta.x, ta.y), math.atan2(tb.x, tb.y)

    def roll(f):
        acc = 0.0
        for d in range(-4, 5):
            h0, h1 = heading(f + d)
            dh = (h1 - h0 + math.pi) % (2 * math.pi) - math.pi
            acc += dh
        return max(-0.22, min(0.22, -bank * acc / 9 * 6.0))

    def fn(f):
        ln = lens(f) if callable(lens) else lens
        return (Vector(pf(f)), Vector(tf(f)), ln, roll(f))
    return fn
