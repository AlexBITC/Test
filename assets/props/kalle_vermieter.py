"""Requisiten fuer 'Meine KI macht jetzt meinen Job' (folge-12-kalle-vermieter).

Gleicher Low-Poly-Stil wie engine/props.py (Vorderseite -Y). Leuchten fuer Workbench ueber diffuse_color.
Wiederverwendet: Helfer-Bytes (characters.Helper), Muenzen und Muenzsaeule (props.coin, props.coin_column),
Telefonhoerer (props.telefonhoerer), Papiertuete (assets/props/brezel_geheimnis.py), Partikel (props.burst,
props.ambient_motes).

  stadtmodell_esslingen   grosses Low-Poly-Diorama: Neckar mit Wellen, Altstadt-Fachwerk mit roten Daechern, Burg auf
                          dem Huegel, Weinberge in Reihen, Mehrfamilienhaeuser, Bruecke mit kleinen Autos, Laternen.
                          Varianten Tag/Nacht (nacht()), baut sich blockweise mit Squash auf (aufbauen()). Keine Schrift.
  preis_pin               Pin (Kugel auf Nadel), poppt mit Ueberschwingen auf, erlischt (pin_an / pin_aus)
  bank_gebaeude           Bank mit Saeulen, Giebel, Treppe; roter Teppich rollt aus (teppich_ausrollen)
  waage_kippt             Balkenwaage: Schalen bleiben senkrecht, kippen() und Gleichgewicht; scheibe() als Gewicht
  sparbuch                Sparbuch (Umschlag, Seiten)
  portemonnaie_tropft     Portemonnaie, aus dem Muenzen tropfen (Aufprall mit Squash, Klirren als Cue-Liste)
  dampf_loop              Dampf, der in Schleife aufsteigt (Staerke als Funktion, kann verfliegen)
  mehlstaub               schwebender Mehlstaub im Licht und eine langsam sinkende Wolke
  lichtring_welle         tuerkiser Lichtring, der sich wie eine Welle ausbreitet
  konfetti_gruen          gruene Konfetti-Funken
  dazu: landen (Squash & Stretch mit Nachwippen), schild_klappen (Schild klappt mit Ueberschwingen auf),
  byte_lichtschein (tuerkises Licht um Byte, Staerke steuerbar), besen, schild_text, haken_gruen, etikett_kette.
"""
import math
import random

from mathutils import Vector

import look as L
import props as PR
from anim import ease_in_out, ease_out, ease_out_back, pop, unpop, clamp01, window

FPS = 30
P = PR.P
TURQ = "#2EE6D6"
GRUEN = "#3DDC84"
ROT = "#E5484D"
GOLD = "#F2B45A"
NAVY = "#141228"
WEISS = "#FBF8F0"


def _text(name, s, size, mat, parent, loc, coll, rot=(math.pi / 2, 0, 0), extrude=0.004, align="CENTER"):
    return L.text(name, s, size, mat, parent, loc, coll, extrude=extrude, rot=rot, font=L.font(), align=align)


# ------------------------------------------------------------------ Bewegungs-Helfer
def landen(T, obj, f, staerke=0.28, dauer=12):
    """Squash & Stretch beim Aufprall (multiplikativ, mit Nachwippen), unabhaengig von anderen Scale-Ebenen."""
    def sc(x):
        t = (x - f) / dauer
        if t < 0 or t > 1.8:
            return (1.0, 1.0, 1.0)
        k = staerke * math.exp(-3.0 * t) * math.cos(t * 10.0)
        return (1 + 0.5 * k, 1 + 0.5 * k, 1 - k)
    T.mul(obj, "scale", sc, f - 1, f + int(dauer * 1.8) + 1)


def schild_klappen(T, obj, f, dauer=9, achse=0, s=1.0, f_aus=None):
    """Schild klappt um die Unterkante auf (Rotation) und poppt mit Ueberschwingen."""
    def rot(x):
        t = clamp01((x - f) / dauer)
        a = -math.pi / 2 * (1 - ease_out_back(t, 2.2))
        r = [0.0, 0.0, 0.0]
        r[achse] = a
        return tuple(r)
    T.set(obj, "rotation_euler", rot, f - 1, f + dauer + 1)
    T.set(obj, "scale", lambda x: (s * pop(x, f - 1, 6, 1.12) * (unpop(x, f_aus, 6) if f_aus is not None and x > f_aus else 1),) * 3,
          f - 2, (f_aus + 8) if f_aus is not None else f + 8)


# ------------------------------------------------------------------ Stadtmodell
def _haus(name, parent, coll, loc, w, d, h, m_wand, m_dach, m_fenster, fachwerk=None, flach=False, stock=2):
    o = L.empty(name, parent, loc, coll)
    L.box(f"{name}_w", (w, d, h), m_wand, o, (0, 0, h / 2), coll, bevel=0.004)
    if flach:
        L.box(f"{name}_d", (w * 1.04, d * 1.04, 0.012), m_dach, o, (0, 0, h + 0.006), coll)
    else:
        L.poly_flat(f"{name}_d", [(-w / 2 - 0.01, 0), (w / 2 + 0.01, 0), (0, h * 0.5)], d * 1.06, m_dach, o, (0, 0, h), coll)
    fenster = []
    for k in range(stock):
        z = h * (0.3 + 0.45 * k / max(1, stock - 1)) if stock > 1 else h * 0.5
        for sx in (-1, 1):
            fenster.append(L.box(f"{name}_f{k}{sx}", (w * 0.18, 0.004, h * 0.13), m_fenster, o, (sx * w * 0.25, -d / 2 - 0.002, z), coll))
    if fachwerk is not None:
        for sx in (-1, 0, 1):
            L.box(f"{name}_fw{sx}", (0.006, 0.003, h * 0.9), fachwerk, o, (sx * w * 0.42, -d / 2 - 0.003, h * 0.47), coll)
        L.box(f"{name}_fwq", (w * 0.95, 0.003, 0.006), fachwerk, o, (0, -d / 2 - 0.003, h * 0.55), coll)
    return o, fenster


def stadtmodell_esslingen(coll, name, seed=12):
    """Diorama ca. 3,0 x 2,0 m (Ursprung = Mitte der Oberflaeche). Rueckgabe P mit Bloecken (fuer aufbauen),
    Haeusern (Pin-Plaetze), Ziel-Haus, Autos, Wellen, Laternen, Mond und den Tag/Nacht-Materialien."""
    rnd = random.Random(seed)
    root = L.empty(name, coll=coll)
    m_gras = L.unique_mat(L.mat("sm_gras", "#7DBF5E", 0.8), f"{name}_gras")
    m_erde = L.mat("sm_erde", "#8A5A3A", 0.8)
    m_wasser = L.unique_mat(L.mat("sm_wasser", TURQ, 0.3, emit=TURQ, strength=1.2), f"{name}_wasser")
    m_strasse = L.unique_mat(L.mat("sm_strasse", "#8C8798", 0.7), f"{name}_strasse")
    m_wand = [L.unique_mat(L.mat(f"sm_wand{k}", c, 0.7), f"{name}_wand{k}") for k, c in
              enumerate(["#F4E6CC", "#EBD7B4", "#F7EEDC", "#E6CFAA"])]
    m_dach = L.unique_mat(L.mat("sm_dach", "#C9503A", 0.6), f"{name}_dach")
    m_dach2 = L.unique_mat(L.mat("sm_dach2", "#A9472F", 0.6), f"{name}_dach2")
    m_flach = L.unique_mat(L.mat("sm_flach", "#B9B6C8", 0.7), f"{name}_flach")
    m_fw = L.mat("sm_fachwerk", "#5A3A26", 0.7)
    m_fenster = L.unique_mat(L.mat("sm_fenster", "#7F9BBE", 0.4), f"{name}_fenster")
    m_burg = L.unique_mat(L.mat("sm_burg", "#CFC6B4", 0.75), f"{name}_burg")
    m_rebe = L.unique_mat(L.mat("sm_rebe", "#3F9E4A", 0.7), f"{name}_rebe")
    tag_mats = [m_gras, m_strasse, m_dach, m_dach2, m_flach, m_burg, m_rebe] + m_wand
    blocks = []
    # Grundplatte (abgerundet, mit Erdkante)
    platte = L.empty(f"{name}_platte", root, (0, 0, 0), coll)
    L.box(f"{name}_gr", (3.0, 2.0, 0.08), m_gras, platte, (0, 0, -0.04), coll, bevel=0.05, seg=3)
    L.box(f"{name}_er", (3.04, 2.04, 0.12), m_erde, platte, (0, 0, -0.12), coll, bevel=0.05)
    blocks.append((platte, -9.0))
    # Neckar (schraeg von links hinten nach rechts vorn), mit Wellen
    fluss = L.empty(f"{name}_fluss", root, (0, 0, 0), coll)
    pts = [(-1.5, 0.05), (-0.8, -0.02), (0.0, -0.08), (0.8, -0.05), (1.5, -0.12)]
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        d = Vector((b[0] - a[0], b[1] - a[1]))
        o = L.box(f"{name}_n{k}", (d.length + 0.06, 0.26, 0.012), m_wasser, fluss, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.006), coll)
        o.rotation_euler = (0, 0, math.atan2(d.y, d.x))
    wellen = []
    m_welle = L.mat("sm_welle", "#BFFFF8", 0.3, emit="#BFFFF8", strength=2.0)
    for k in range(18):
        x = -1.4 + 2.8 * k / 17
        y = -0.06 * (x / 1.5) + rnd.uniform(-0.07, 0.07)
        wellen.append(L.box(f"{name}_wl{k}", (0.06, 0.008, 0.004), m_welle, fluss, (x, y, 0.014), coll))
    blocks.append((fluss, -8.0))
    # Strassen: am Fluss entlang (vorn) und ueber die Bruecke nach hinten
    str_ = L.empty(f"{name}_strassen", root, (0, 0, 0), coll)
    L.box(f"{name}_s1", (2.9, 0.08, 0.008), m_strasse, str_, (0, -0.3, 0.004), coll)
    L.box(f"{name}_s2", (0.08, 1.9, 0.008), m_strasse, str_, (0.25, 0, 0.005), coll)
    bruecke = L.box(f"{name}_br", (0.14, 0.36, 0.03), L.mat("sm_bruecke", "#B9A58A", 0.6), str_, (0.25, -0.07, 0.025), coll)
    blocks.append((str_, -7.0))
    # Altstadt: Fachwerkhaeuser mit roten Daechern (links vorn)
    haeuser = []
    for k in range(16):
        x = -1.3 + 0.17 * (k % 7) + rnd.uniform(-0.02, 0.02)
        y = -0.48 - 0.2 * (k // 7) + rnd.uniform(-0.02, 0.02)
        if x > -0.15:
            continue
        h = rnd.uniform(0.1, 0.15)
        o, fe = _haus(f"{name}_alt{k}", root, coll, (x, y, 0), 0.13, 0.12, h, m_wand[k % 4], m_dach if k % 3 else m_dach2, m_fenster,
                      fachwerk=m_fw, stock=2)
        haeuser.append({"obj": o, "dach": h * 1.5, "fenster": fe})
        blocks.append((o, x))
    # Kirche in der Altstadt
    ki, _ = _haus(f"{name}_kirche", root, coll, (-0.62, -0.75, 0), 0.14, 0.22, 0.16, m_wand[2], m_dach2, m_fenster, stock=1)
    L.box(f"{name}_turm", (0.07, 0.07, 0.32), m_wand[2], ki, (0, -0.06, 0.16), coll)
    L.cyl(f"{name}_turmd", 0.06, 0.12, 4, m_dach2, ki, (0, -0.06, 0.38), coll, r2=0.0)
    blocks.append((ki, -0.62))
    # Burg auf dem Huegel (links hinten) mit Weinbergen am Hang
    burg = L.empty(f"{name}_burg", root, (-0.95, 0.62, 0), coll)
    L.cyl(f"{name}_huegel", 0.5, 0.22, 14, m_gras, burg, (0, 0, 0.11), coll, r2=0.22)
    for k, (dx, dy) in enumerate([(-0.12, 0.0), (0.12, 0.02), (0.0, 0.1)]):
        L.cyl(f"{name}_bt{k}", 0.045, 0.2, 8, m_burg, burg, (dx, dy, 0.32), coll)
        L.cyl(f"{name}_bd{k}", 0.055, 0.07, 8, m_dach2, burg, (dx, dy, 0.455), coll, r2=0.0)
    L.box(f"{name}_bm", (0.26, 0.04, 0.09), m_burg, burg, (0, 0.0, 0.27), coll)
    blocks.append((burg, -0.95))
    reben = L.empty(f"{name}_reben", root, (0.75, 0.62, 0), coll)
    hang = L.box(f"{name}_hang", (1.1, 0.6, 0.02), m_gras, reben, (0, 0, 0.08), coll)
    hang.rotation_euler = (0.25, 0, 0)
    for k in range(8):
        r = L.box(f"{name}_rb{k}", (1.0, 0.025, 0.03), m_rebe, reben, (0, -0.26 + 0.075 * k, 0.03 + 0.019 * k + 0.02), coll)
        r.rotation_euler = (0.25, 0, 0)
    blocks.append((reben, 0.75))
    # Weinberg auch hinter der Burg
    reben2 = L.empty(f"{name}_reben2", root, (-0.2, 0.75, 0), coll)
    for k in range(5):
        L.box(f"{name}_rc{k}", (0.6, 0.022, 0.03), m_rebe, reben2, (0, -0.15 + 0.07 * k, 0.03 + 0.015 * k), coll)
    blocks.append((reben2, -0.2))
    # Mehrfamilienhaeuser (rechts vorn) - eines ist die gefundene Wohnung
    ziel = None
    for k in range(9):
        x = 0.5 + 0.28 * (k % 3) + rnd.uniform(-0.02, 0.02)
        y = -0.5 - 0.24 * (k // 3)
        h = rnd.uniform(0.2, 0.28)
        o, fe = _haus(f"{name}_mfh{k}", root, coll, (x, y, 0), 0.2, 0.14, h, m_wand[(k + 1) % 4], m_flach, m_fenster, flach=True, stock=3)
        eintrag = {"obj": o, "dach": h + 0.02, "fenster": fe}
        if k == 4:
            ziel = eintrag
        haeuser.append(eintrag)
        blocks.append((o, x))
    # weitere Haeuser hinter dem Fluss (Mitte)
    for k in range(6):
        x = -0.1 + 0.22 * k
        y = 0.25 + rnd.uniform(-0.03, 0.03)
        if 0.18 < x < 0.32:
            continue
        h = rnd.uniform(0.1, 0.16)
        o, fe = _haus(f"{name}_mid{k}", root, coll, (x, y, 0), 0.14, 0.13, h, m_wand[k % 4], m_dach, m_fenster, fachwerk=m_fw, stock=2)
        haeuser.append({"obj": o, "dach": h * 1.5, "fenster": fe})
        blocks.append((o, x))
    # Baeume
    m_baum = L.unique_mat(L.mat("sm_baum", "#4FA34A", 0.7), f"{name}_baum")
    tag_mats.append(m_baum)
    for k in range(10):
        x, y = rnd.uniform(-1.4, 1.4), rnd.choice([rnd.uniform(-0.95, -0.85), rnd.uniform(0.35, 0.45)])
        b = L.empty(f"{name}_baum{k}", root, (x, y, 0), coll)
        L.cyl(f"{name}_bs{k}", 0.01, 0.05, 5, L.mat("sm_stamm", "#6A4228", 0.7), b, (0, 0, 0.025), coll)
        L.ico(f"{name}_bk{k}", 0.045, 1, (1, 1, 1.2), m_baum, b, (0, 0, 0.08), coll)
        blocks.append((b, x))
    # Autos (fahren ueber die Bruecke und am Fluss entlang)
    autos = []
    for k, col in enumerate(["#E5484D", "#3D7BD9", "#F2C94C", "#FBF8F0"]):
        a = L.empty(f"{name}_auto{k}", root, (0, 0, 0.012), coll)
        L.box(f"{name}_ak{k}", (0.07, 0.035, 0.025), L.mat(f"sm_auto{col}", col, 0.5), a, (0, 0, 0.014), coll, bevel=0.006)
        L.box(f"{name}_ad{k}", (0.035, 0.03, 0.018), L.mat("sm_autoglas", "#B9D8EE", 0.3), a, (0, 0, 0.034), coll)
        autos.append(a)
    # Laternen
    laternen = []
    for k in range(10):
        x = -1.35 + 0.3 * k
        lt = L.empty(f"{name}_lat{k}", root, (x, -0.36, 0), coll)
        L.cyl(f"{name}_lm{k}", 0.004, 0.09, 5, L.mat("sm_mast", "#3E4A5A", 0.5), lt, (0, 0, 0.045), coll)
        m_l = L.unique_mat(L.mat("sm_lampe", "#6A6E7A", 0.4), f"{name}_lampe{k}")
        L.sphere(f"{name}_lk{k}", 0.012, 8, 5, (1, 1, 1), m_l, lt, (0, 0, 0.095), coll)
        laternen.append((lt, m_l))
        blocks.append((lt, x + 0.05))
    # Mond und Spiegelung (nur nachts)
    mond = L.empty(f"{name}_mond", root, (0.9, 0.95, 0.95), coll)
    L.sphere(f"{name}_mk", 0.09, 14, 9, (1, 1, 1), L.mat("sm_mond", "#FFF4C8", 0.3, emit="#FFF4C8", strength=2.5), mond, (0, 0, 0), coll)
    spiegel = L.box(f"{name}_ms", (0.09, 0.2, 0.002), L.mat("sm_mondsp", "#FFF4C8", 0.3, emit="#FFF4C8", strength=1.5, alpha=0.6),
                    root, (0.9, -0.06, 0.015), coll)
    mond.scale = (0, 0, 0)
    spiegel.scale = (0, 0, 0)
    return P(root=root, blocks=blocks, haeuser=haeuser, ziel=ziel, autos=autos, wellen=wellen, laternen=laternen, mond=mond,
             spiegel=spiegel, m_fenster=m_fenster, m_wasser=m_wasser, tag_mats=tag_mats, bruecke=bruecke)


def aufbauen(T, m, f0, dauer=30, f1=None, abbau=None):
    """Block fuer Block aus dem Boden (von links nach rechts), jeder springt mit Squash hoch. abbau: Frame, ab dem das
    Modell wieder im Boden versinkt."""
    xs = sorted(x for _, x in m.blocks)
    lo, hi = xs[0], xs[-1]
    f1 = f1 if f1 is not None else f0 + dauer + 400
    for o, x in m.blocks:
        st = f0 + int(dauer * (x - lo) / max(1e-6, hi - lo))
        T.set(o, "scale", lambda f, st=st: (1.0, 1.0, 1.0) if f >= st + 9 else
              ((pop(f, st, 9, 1.0) * (1 + 0.25 * math.sin(math.pi * clamp01((f - st) / 9)) * 0.0),
                pop(f, st, 9, 1.0), ease_out_back(clamp01((f - st) / 9), 2.6)) if f >= st else (0.0, 0.0, 0.0)), f0 - 1, f1)
        landen(T, o, st + 9, staerke=0.22, dauer=10)
    if abbau is not None:
        T.mul(m.root, "scale", lambda f: (1, 1, max(0.0, 1 - ease_in_out(clamp01((f - abbau) / 10)))) if f >= abbau else (1, 1, 1),
              abbau - 1, abbau + 12)


def leben(T, m, f0, f1):
    """Wellen glitzern und wandern, Autos fahren ueber die Bruecke und am Neckar entlang."""
    for k, w in enumerate(m.wellen):
        x0, y0 = w.location.x, w.location.y
        T.set(w, "location", lambda f, x0=x0, y0=y0, k=k: (((x0 + 1.45 + f * 0.004) % 2.9) - 1.45, y0, 0.014), f0, f1)
        T.set(w, "scale", lambda f, k=k: (0.6 + 0.4 * abs(math.sin(f * 0.15 + k)), 1, 1), f0, f1)
    wege = [[(-1.45, -0.3), (1.45, -0.3)], [(0.25, -0.9), (0.25, 0.9)], [(1.45, -0.32), (-1.45, -0.32)], [(0.27, 0.9), (0.27, -0.9)]]
    for k, (a, wg) in enumerate(zip(m.autos, wege)):
        p0, p1 = Vector(wg[0]), Vector(wg[1])
        ln = (p1 - p0).length
        ph = k * 0.7
        T.set(a, "location", lambda f, p0=p0, p1=p1, ln=ln, ph=ph: tuple(p0.lerp(p1, ((f * 0.012 + ph) % ln) / ln).to_3d() + Vector((0, 0, 0.012))),
              f0, f1)
        T.set(a, "rotation_euler", lambda f, d=p1 - p0: (0, 0, math.atan2(d.y, d.x)), f0, f1)


def nacht(T, m, f_an, f0, f1, dauer=20, f_aus=None):
    """Tag -> Nacht: Farben dunkler und kuehler, Fenster warm, Laternen gehen nacheinander an, Mond mit Spiegelung."""
    def k(f):
        a = clamp01((f - f_an) / dauer)
        if f_aus is not None and f >= f_aus:
            a *= 1 - clamp01((f - f_aus) / 8)
        return ease_in_out(a)
    for mt in m.tag_mats:
        base = tuple(mt.diffuse_color)
        T.set(mt, "diffuse_color", lambda f, b=base: (b[0] * (1 - 0.62 * k(f)), b[1] * (1 - 0.58 * k(f)), b[2] * (1 - 0.4 * k(f)), b[3]),
              f0, f1)
    fb = tuple(m.m_fenster.diffuse_color)
    warm = L.srgb("#FFC56A")
    T.set(m.m_fenster, "diffuse_color", lambda f: tuple(fb[i] + (warm[i] - fb[i]) * k(f) for i in range(3)) + (1,), f0, f1)
    for j, (lt, ml) in enumerate(m.laternen):
        st = f_an + 6 + 3 * j
        an, aus = L.srgb("#FFE7A0"), tuple(ml.diffuse_color)
        T.set(ml, "diffuse_color", lambda f, st=st, an=an, aus=aus: an if (f >= st and k(f) > 0.5) else aus, f0, f1)
    T.set(m.mond, "scale", lambda f: (k(f),) * 3, f0, f1)
    T.set(m.spiegel, "scale", lambda f: (k(f), k(f) * (0.8 + 0.2 * math.sin(f * 0.3)), 1), f0, f1)


# ------------------------------------------------------------------ Pins
def preis_pin(coll, name, farbe=TURQ):
    root = L.empty(name, coll=coll)
    m = L.unique_mat(L.mat("pin_kopf", farbe, 0.35, emit=farbe, strength=2.2), f"{name}_m")
    L.cyl(f"{name}_nadel", 0.006, 0.12, 6, L.mat("pin_nadel", "#C9CCD8", 0.4), root, (0, 0, 0.06), coll)
    L.sphere(f"{name}_kopf", 0.035, 10, 7, (1, 1, 1), m, root, (0, 0, 0.13), coll)
    root.scale = (0, 0, 0)
    return P(root=root, mat=m)


def pin_an(T, p, f, f_aus=None, s=1.0, f1=None):
    """Pin poppt mit Ueberschwingen auf, wippt kurz nach; f_aus: erlischt (grau) und sinkt weg (Domino)."""
    end = f1 if f1 is not None else (f_aus + 12 if f_aus is not None else f + 400)
    T.set(p.root, "scale", lambda x: (s * pop(x, f, 7, 1.25) * (unpop(x, f_aus + 4, 6) if f_aus is not None and x > f_aus + 4 else 1),) * 3,
          f - 1, end)
    if f_aus is not None:
        an, grau = tuple(p.mat.diffuse_color), L.srgb("#5A5866")
        T.set(p.mat, "diffuse_color", lambda x: grau if x >= f_aus else an, f - 1, end)


# ------------------------------------------------------------------ Bank
def bank_gebaeude(coll, name, s=1.0):
    root = L.empty(name, coll=coll)
    root.scale = (s, s, s)
    m_stein = L.mat("bank_stein", "#E8E2D4", 0.6)
    m_dunkel = L.mat("bank_dunkel", "#4A4F66", 0.5)
    for k in range(3):
        L.box(f"{name}_stufe{k}", (0.7 - 0.04 * k, 0.42 - 0.04 * k, 0.03), m_stein, root, (0, -0.02 * k, 0.015 + 0.03 * k), coll)
    L.box(f"{name}_korpus", (0.58, 0.3, 0.34), m_stein, root, (0, 0.04, 0.26), coll)
    for k in range(5):
        L.cyl(f"{name}_saeule{k}", 0.022, 0.32, 10, WEISS and L.mat("bank_saeule", "#F7F2E6", 0.5), root, (-0.24 + 0.12 * k, -0.15, 0.25), coll)
    L.box(f"{name}_gebaelk", (0.64, 0.36, 0.04), m_stein, root, (0, -0.02, 0.43), coll)
    L.poly_flat(f"{name}_giebel", [(-0.33, 0), (0.33, 0), (0, 0.13)], 0.36, m_stein, root, (0, -0.02, 0.45), coll)
    L.box(f"{name}_tuer", (0.12, 0.01, 0.2), m_dunkel, root, (0, -0.11, 0.18), coll)
    tep = L.empty(f"{name}_teppich", root, (0, -0.2, 0.062), coll)
    L.box(f"{name}_tp", (0.12, 1.0, 0.006), L.mat("bank_teppich", "#C8323A", 0.7), tep, (0, -0.5, 0), coll)
    tep.scale = (1, 0, 1)
    sch = L.empty(f"{name}_schild", root, (0, -0.95, 0.07), coll)
    L.box(f"{name}_sb", (0.36, 0.02, 0.12), L.mat("bank_schild", "#C8323A", 0.5), sch, (0, 0, 0.06), coll, bevel=0.01)
    _text(f"{name}_st", "200.000 €", 0.065, L.mat("bank_ink", WEISS, 0.5), sch, (0, -0.012, 0.038), coll)
    sch.scale = (0, 0, 0)
    rate = L.empty(f"{name}_rate", root, (0, -0.02, 0.62), coll)
    L.box(f"{name}_rb", (0.62, 0.02, 0.15), L.mat("bank_rate", "#D8323C", 0.45, emit="#D8323C", strength=1.0), rate, (0, 0, 0.075), coll,
          bevel=0.012)
    _text(f"{name}_rt", "Rate 1.000 € / Monat", 0.052, L.mat("bank_ink", WEISS, 0.5), rate, (0, -0.012, 0.055), coll)
    rate.scale = (0, 0, 0)
    return P(root=root, teppich=tep, schild=sch, rate=rate)


def teppich_ausrollen(T, b, f0, dauer=14, f1=None):
    T.set(b.teppich, "scale", lambda f: (1, ease_out(clamp01((f - f0) / dauer)), 1), f0 - 1, f1 or f0 + dauer + 1)


# ------------------------------------------------------------------ Waage
def waage_kippt(coll, name):
    """Grosse Balkenwaage (ca. 1,9 m breit). Schalen haengen immer senkrecht. kippen(T, w, winkel_fn)."""
    root = L.empty(name, coll=coll)
    m_b = L.mat("wk_messing", GOLD, 0.45, metallic=0.5)
    m_d = L.mat("wk_dunkel", "#2A2840", 0.55)
    L.cyl(f"{name}_fuss", 0.36, 0.1, 18, m_d, root, (0, 0, 0.05), coll, r2=0.28)
    L.cyl(f"{name}_saeule", 0.045, 1.4, 10, m_b, root, (0, 0, 0.8), coll)
    L.sphere(f"{name}_kappe", 0.08, 12, 8, (1, 1, 1), m_b, root, (0, 0, 1.56), coll)
    balken = L.empty(f"{name}_balken", root, (0, 0, 1.5), coll)
    L.box(f"{name}_bm", (1.8, 0.06, 0.07), m_b, balken, (0, 0, 0), coll, bevel=0.02)
    zeiger = L.cyl(f"{name}_zeiger", 0.015, 0.3, 6, m_b, balken, (0, -0.04, 0.15), coll, r2=0.004)
    schalen = []
    for sx in (-1, 1):
        h = L.empty(f"{name}_haenger{sx}", balken, (sx * 0.86, 0, 0), coll)
        for k in range(3):
            a = 2 * math.pi * k / 3
            L.cyl(f"{name}_sch{sx}{k}", 0.005, 0.56, 4, L.mat("wk_schnur", "#D8CBB3", 0.8), h,
                  (0.07 * math.cos(a), 0.07 * math.sin(a), -0.28), coll)
        L.cyl(f"{name}_schale{sx}", 0.3, 0.05, 18, m_b, h, (0, 0, -0.58), coll, r2=0.22)
        schalen.append(h)
    return P(root=root, balken=balken, schalen=schalen, zeiger=zeiger)


def kippen(T, w, winkel_fn, f0, f1):
    """winkel_fn(f) in Radiant (positiv = links tiefer). Schalen bleiben senkrecht."""
    T.set(w.balken, "rotation_euler", lambda f: (0, -winkel_fn(f), 0), f0, f1)
    for h in w.schalen:
        T.set(h, "rotation_euler", lambda f: (0, winkel_fn(f), 0), f0, f1)


def scheibe(coll, name, text, farbe, r=0.2, dicke=0.06):
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_k", r, dicke, 22, L.mat(f"wk_scheibe{farbe}", farbe, 0.5), root, (0, 0, dicke / 2), coll)
    _text(f"{name}_t", text, r * 0.42, L.mat("wk_ink", WEISS, 0.5), root, (0, -r - 0.004, dicke / 2 - r * 0.11), coll)
    L.box(f"{name}_tb", (r * 1.7, 0.01, r * 0.5), L.mat(f"wk_scheibe{farbe}", farbe, 0.5), root, (0, -r * 0.92, dicke / 2), coll)
    return P(root=root)


# ------------------------------------------------------------------ Sparbuch, Portemonnaie
def sparbuch(coll, name):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_u", (0.16, 0.22, 0.025), L.mat("sb_umschlag", "#2E6B4E", 0.5), root, (0, 0, 0.0125), coll, bevel=0.006)
    L.box(f"{name}_s", (0.15, 0.21, 0.02), L.mat("sb_seiten", "#F5F1E8", 0.8), root, (0.005, 0, 0.0125), coll)
    L.box(f"{name}_streifen", (0.16, 0.03, 0.026), L.mat("sb_gold", GOLD, 0.4), root, (0, 0.06, 0.0125), coll)
    return P(root=root)


def portemonnaie_tropft(coll, name, n=10):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_k", (0.26, 0.06, 0.17), L.mat("pm_leder", "#6A4228", 0.6), root, (0, 0, 0), coll, bevel=0.02)
    L.box(f"{name}_v", (0.27, 0.065, 0.02), L.mat("pm_naht", "#8A5A38", 0.6), root, (0, 0, 0.05), coll)
    muenzen = [PR.coin(coll, f"{name}_m{k}") for k in range(n)]
    for m in muenzen:
        m.scale = (0, 0, 0)
    return P(root=root, muenzen=muenzen)


def tropfen(T, pm, f0, f1, boden_z, intervall=9, start=None):
    """Muenzen tropfen nacheinander aus dem Portemonnaie, landen mit Squash und kleinem Huepfer. Rueckgabe: Aufprall-Frames."""
    aufprall = []
    st0 = start if start is not None else f0
    o0 = pm.root.matrix_world.translation.copy()
    for k, m in enumerate(pm.muenzen):
        st = st0 + k * intervall
        if st > f1 - 6:
            m.scale = (0, 0, 0)
            continue
        fall = max(6, int(math.sqrt(2 * max(0.05, o0.z - 0.1 - boden_z) / 9.81) * FPS))
        dx = (k % 3 - 1) * 0.06

        def loc(f, st=st, fall=fall, dx=dx):
            t = clamp01((f - st) / fall)
            z = o0.z - 0.1 - (o0.z - 0.1 - boden_z) * t * t
            if f > st + fall:                        # kleiner Huepfer nach dem Aufprall
                z = boden_z + 0.04 * max(0.0, math.sin(math.pi * clamp01((f - st - fall) / 6)))
            return (o0.x + dx, o0.y, z)
        T.set(m, "location", loc, st - 1, f1)
        T.set(m, "scale", lambda f, st=st: (1, 1, 1) if f >= st else (0, 0, 0), st - 2, f1)
        T.set(m, "rotation_euler", lambda f, st=st, fall=fall: (math.pi / 2 * (1 - clamp01((f - st) / fall)) + 0.0, 0, f * 0.2), st - 1, f1)
        landen(T, m, st + fall, staerke=0.35, dauer=8)
        aufprall.append(st + fall)
    return aufprall


# ------------------------------------------------------------------ Dampf, Mehlstaub, Licht, Konfetti
def dampf_loop(T, coll, name, pos, f0, f1, n=9, staerke_fn=lambda f: 1.0, hoehe=0.55, seed=4):
    """Weiche Dampfwoelkchen steigen in Schleife auf, wachsen und vergehen. staerke_fn(f) 0..1 (0 = verflogen)."""
    rnd = random.Random(seed)
    m = L.mat("dampf", "#FFFFFF", 0.9, emit="#FFFFFF", strength=0.4, alpha=0.32)
    out = []
    p = Vector(pos)
    for k in range(n):
        o = L.ico(f"{name}_{k}", 0.05, 2, (1, 1, 1.15), m, None, (0, 0, 0), coll)
        ph, per = rnd.uniform(0, 1), rnd.uniform(1.6, 2.4) * FPS
        dx, dy = rnd.uniform(-0.06, 0.06), rnd.uniform(-0.05, 0.05)

        def u(f, ph=ph, per=per):
            return ((f - f0) / per + ph) % 1.0
        T.set(o, "location", lambda f, dx=dx, dy=dy, u=u: (p.x + dx + 0.05 * math.sin(f * 0.07 + dx * 50) * u(f),
                                                           p.y + dy, p.z + hoehe * u(f)), f0, f1)
        T.set(o, "scale", lambda f, u=u: ((0.5 + 1.4 * u(f)) * math.sin(math.pi * u(f)) * staerke_fn(f),) * 3, f0, f1)
        out.append(o)
    return out


def mehlstaub(T, coll, name, center, size, f0, f1, count=40, seed=7):
    """Schwebender Mehlstaub im Licht (langsames Driften, Funkeln)."""
    return PR.ambient_motes(T, coll, name, center, size, count, seed, f0, f1, color_kind="dust", drift=0.04, scale=1.3)


def mehlwolke_sinkt(T, coll, name, pos, f0, dauer=60, n=8, seed=9):
    """Kleine Mehlstaubwolke, die langsam im Licht sinkt und vergeht."""
    rnd = random.Random(seed)
    m = L.mat("mehlwolke", "#F5EFE2", 0.9, emit="#F5EFE2", strength=0.3, alpha=0.38)
    p = Vector(pos)
    for k in range(n):
        o = L.ico(f"{name}_{k}", 0.06, 2, (1, 1, 0.8), m, None, (0, 0, 0), coll)
        d = Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.1, 0.1), rnd.uniform(-0.05, 0.08)))
        T.set(o, "location", lambda f, d=d: tuple(p + d * (1 + 0.6 * clamp01((f - f0) / dauer)) - Vector((0, 0, 0.25 * clamp01((f - f0) / dauer)))),
              f0 - 1, f0 + dauer + 1)
        T.set(o, "scale", lambda f: ((1.0 + 0.8 * clamp01((f - f0) / dauer)) * window(f, f0 - 1, f0 + dauer, 4, 20),) * 3, f0 - 1, f0 + dauer + 1)


def lichtring_welle(T, coll, name, pos, f0, dauer=18, r_end=2.2, farbe=TURQ):
    """Tuerkiser Lichtring breitet sich flach wie eine Welle aus (Ring + weicher Schimmer), blendet aus."""
    m = L.unique_mat(L.mat("lichtring", farbe, 0.3, emit=farbe, strength=3.0, alpha=0.85), f"{name}_m")
    ms = L.unique_mat(L.mat("lichtring_s", farbe, 0.3, emit=farbe, strength=1.0, alpha=0.25), f"{name}_ms")
    ring = L.torus(f"{name}_r", 1.0, 0.025, 48, 5, m, None, pos, coll)
    sch = L.cyl(f"{name}_s", 1.0, 0.004, 40, ms, None, pos, coll)
    for o, k in ((ring, 1.0), (sch, 0.96)):
        T.set(o, "scale", lambda f, k=k: ((0.05 + r_end * k * ease_out(clamp01((f - f0) / dauer))) if f0 <= f <= f0 + dauer else 0,) * 2 + (1,),
              f0 - 1, f0 + dauer + 1)
    base, base_s = tuple(m.diffuse_color), tuple(ms.diffuse_color)
    T.set(m, "diffuse_color", lambda f: base[:3] + (0.85 * (1 - clamp01((f - f0) / dauer)),), f0, f0 + dauer)
    T.set(ms, "diffuse_color", lambda f: base_s[:3] + (0.25 * (1 - clamp01((f - f0) / dauer)),), f0, f0 + dauer)
    return ring


def konfetti_gruen(T, coll, name, origin, f0, count=34, seed=3, richtung=(0, 0, 0)):
    return PR.burst(T, coll, name, "confetti_#3DDC84", origin, f0, count, seed, speed=(1.2, 2.4), up=1.0, spread=1.0, gravity=-3.0,
                    life=(26, 40), size=(0.8, 1.3), drag=1.2, spin=10.0, flutter=0.6, wobble=0.03, dir_bias=richtung,
                    kinds=["confetti_#3DDC84", "confetti_#7CF0A8", "confetti_#2FB86E", "spark"])


def byte_lichtschein(coll, name, parent):
    """Tuerkiser Lichtschein um Byte (zwei weiche Huellen) und ein Lichtfleck darunter. staerke(): heller und groesser."""
    m1 = L.unique_mat(L.mat("bl_kern", TURQ, 0.3, emit=TURQ, strength=1.0, alpha=0.10), f"{name}_m1")
    m2 = L.unique_mat(L.mat("bl_hof", TURQ, 0.3, emit=TURQ, strength=1.0, alpha=0.05), f"{name}_m2")
    h1 = L.sphere(f"{name}_h1", 0.3, 20, 12, (1, 1, 1), m1, parent, (0, 0, 0), coll)
    h2 = L.sphere(f"{name}_h2", 0.48, 20, 12, (1, 1, 1), m2, parent, (0, 0, 0), coll)
    m3 = L.unique_mat(L.mat("bl_fleck", TURQ, 0.3, emit=TURQ, strength=1.0, alpha=0.16), f"{name}_m3")
    fleck = L.cyl(f"{name}_fleck", 1.0, 0.003, 32, m3, None, (0, 0, 0), coll)
    return P(huellen=(h1, h2), mats=(m1, m2, m3), fleck=fleck)


def lichtschein_steuern(T, ls, staerke_fn, fleck_fn, f0, f1):
    """staerke_fn(f) ~0.5..2: Groesse und Helligkeit; fleck_fn(f) -> (x, y, z) Lichtfleck auf der Flaeche unter Byte."""
    for h, a0 in zip(ls.huellen, (0.10, 0.05)):
        T.set(h, "scale", lambda f: ((0.7 + 0.3 * staerke_fn(f)),) * 3, f0, f1)
    for mt, a0 in zip(ls.mats, (0.07, 0.035, 0.14)):
        T.set(mt, "diffuse_color", lambda f, a0=a0: min(0.3, a0 * staerke_fn(f)), f0, f1, index=3)
    T.set(ls.fleck, "location", lambda f: tuple(fleck_fn(f)), f0, f1)
    T.set(ls.fleck, "scale", lambda f: ((0.25 + 0.2 * staerke_fn(f)),) * 2 + (1,), f0, f1)


# ------------------------------------------------------------------ Kleinteile
def besen(coll, name):
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_stiel", 0.018, 1.35, 8, L.mat("besen_stiel", "#B07A4A", 0.6), root, (0, 0, 0.8), coll)
    L.box(f"{name}_kopf", (0.34, 0.07, 0.06), L.mat("besen_kopf", "#7A4E2E", 0.6), root, (0, 0, 0.12), coll, bevel=0.01)
    for k in range(8):
        L.box(f"{name}_b{k}", (0.03, 0.05, 0.12), L.mat("besen_borste", "#D8B46A", 0.8), root, (-0.15 + 0.043 * k, 0, 0.04), coll)
    return P(root=root)


def schild_text(coll, name, text, farbe=GRUEN, breite=0.7, hoehe=0.18, size=0.09, leuchten=1.2):
    root = L.empty(name, coll=coll)
    m = L.unique_mat(L.mat("schild_bg", farbe, 0.45, emit=farbe, strength=leuchten), f"{name}_bg")
    L.box(f"{name}_b", (breite, 0.03, hoehe), m, root, (0, 0, hoehe / 2), coll, bevel=0.02)
    _text(f"{name}_t", text, size, L.mat("schild_ink", WEISS, 0.5, emit=WEISS, strength=1.0), root, (0, -0.018, hoehe / 2 - size * 0.33), coll)
    root.scale = (0, 0, 0)
    return P(root=root, mat=m)


def haken_gruen(coll, name, s=0.35):
    root = L.empty(name, coll=coll)
    m = L.mat("haken_gruen", GRUEN, 0.35, emit=GRUEN, strength=2.5)
    L.cyl(f"{name}_ring", s, 0.03, 32, L.mat("haken_ring", "#1E5C3A", 0.5), root, (0, 0, 0), coll, axis="Y")
    L.poly_flat(f"{name}_h", [(-0.55 * s, 0.0), (-0.38 * s, -0.17 * s), (-0.12 * s, -0.42 * s), (0.6 * s, 0.38 * s), (0.42 * s, 0.55 * s),
                              (-0.12 * s, -0.05 * s), (-0.38 * s, 0.17 * s)], 0.04, m, root, (0, -0.03, 0), coll)
    root.scale = (0, 0, 0)
    return P(root=root)


def etikett_kette(coll, name, text="−250 € jeden Monat"):
    root = L.empty(name, coll=coll)
    m_k = L.mat("kette", "#A9ABB8", 0.4, metallic=0.5)
    for k in range(6):
        L.torus(f"{name}_g{k}", 0.025, 0.006, 10, 4, m_k, root, (0, 0, -0.05 * k), coll, axis="X" if k % 2 else "Y")
    et = L.empty(f"{name}_et", root, (0, 0, -0.38), coll)
    L.box(f"{name}_b", (0.86, 0.03, 0.2), L.mat("etikett_rot", ROT, 0.45, emit=ROT, strength=1.0), et, (0, 0, -0.1), coll, bevel=0.02)
    _text(f"{name}_t", text, 0.085, L.mat("schild_ink", WEISS, 0.5, emit=WEISS, strength=1.0), et, (0, -0.018, -0.13), coll)
    return P(root=root, etikett=et)


def schwingen(T, obj, f0, f1, amp=0.35, freq=1.1, daempf=1.6):
    """Pendelt an der Kette aus (Rotation um X und Z)."""
    T.set(obj, "rotation_euler", lambda f: (0.0, amp * math.exp(-daempf * (f - f0) / FPS) * math.sin(2 * math.pi * freq * (f - f0) / FPS),
                                            0.2 * amp * math.exp(-daempf * (f - f0) / FPS) * math.cos(2 * math.pi * freq * (f - f0) / FPS)),
          f0, f1)


def muenzsaeule_gruen(coll, name, n=24):
    """Gruene Muenzsaeule (props.coin_column mit gruenem Glanz)."""
    c = PR.coin_column(coll, name, n, spacing=0.03)
    m = L.mat("muenze_gruen", "#3DDC84", 0.35, metallic=0.5, emit="#3DDC84", strength=1.2)
    for co in c.coins:
        for o in [co] + list(co.children_recursive):
            if o.type == "MESH" and o.material_slots:          # Mesh wird mit allen Muenzen geteilt: Material am Objekt
                o.material_slots[0].link = "OBJECT"
                o.material_slots[0].material = m
    top = L.empty(f"{name}_top", c.root, (0, 0, 0), coll)
    return P(root=c.root, coins=c.coins, top=top, spacing=0.03)
