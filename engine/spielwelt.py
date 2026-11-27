"""Set 'spielwelt' (Engine 2.5): die Stadt als Aufbauspiel.

Ursprung (200, 0, 0). Raster: 1 Kachel = 1 m; alle Objekte rasten auf ganze oder halbe Kacheln ein (S.raster(x, y)).
Der Stadtplan folgt dem Set 'stadtkarte' (gleiche drei Viertel, gleicher Fluss, gleiche Bruecke, gleiche Lage von Kalles
Laden), umgerechnet mit x * 3, y * 7 (laenglich, damit die Stadt im Hochformat das ganze Bild fuellt).

Objekt-Katalog: assets/spielwelt/<objekt>.py (je Objekt eine Datei mit INFO, bauen(...) und benannten Zustaenden),
Uebersicht mit Groesse, Ankerpunkt, Rasterposition und Zustaenden in assets/spielwelt/manifest.json. Der Aufbau der Stadt
liest die Rasterpositionen aus dem Manifest ('platzierungen').

Ebenen: 'spiel_stadt' (Stadt bei S.p(0, 0, 0)) und 'spiel_laden' (Puppenhaus-Laden bei S.p(0, 70, 0), Filiale 2 als
kleinere Variante bei S.p(0, 90, 0)). Stil: Low-Poly mit runden Kanten, satten warmen Farben, feinen dunklen Outlines
(nach aussen versetzte Huelle, Rueckseiten ausgeblendet) und weichen Schatten nach unten rechts; render_stil() schaltet
das in scene.render_frames nur fuer Spielwelt-Frames ein.
Wetter: wetter(T, S, plan) mit 'sonne' (warme Schatten, Voegel), 'regen' (Tropfen, Pfuetzen, grauer Himmel, Schirme),
'abend' (Laternen an, lange Schatten); Tag-Nacht ueber zeitraffer(...).
Kameras: spiel_stadt, spiel_laden, spiel_flug (siehe unten).
"""
import importlib
import json
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector

import look as L
from anim import ease_in_out, clamp01, pop, unpop

FPS = 30
HIER = os.path.dirname(os.path.abspath(__file__))
KATALOG = os.path.join(HIER, "..", "assets", "spielwelt")
if KATALOG not in sys.path:
    sys.path.insert(0, KATALOG)

# Palette: Holz- und Teigtoene als Basis, Kalles Rot als Akzent, Bytes Tuerkis nur fuer Spiel-Oberflaeche und Hilfe
PAL = {"gras": "#8CC86A", "gras2": "#7DBB5C", "erde": "#B07A4A", "weg": "#E8D2A8", "strasse": "#9A93A6",
       "wasser": "#5EB4E8", "holz": "#C68A52", "holz_d": "#7A4E2E", "teig": "#F2D9B0", "creme": "#F7EBD3",
       "rot": "#E2483F", "dach": "#D0603F", "dach2": "#B84E3A", "weiss": "#FBF8F0", "grau": "#A7A3B4",
       "tuerkis": "#2EE6D6", "gold": "#F2B45A", "dunkel": "#2A1E18", "himmel": "#9FD3F2", "laub": "#5DAA4C",
       "laub2": "#4E9A44"}
OUTLINE = "#2A1E18"
STADT_X, STADT_Y = 3.0, 7.0                    # Umrechnung stadtkarte (lokal) -> Spielwelt-Raster


class P:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def m(name, col, r=0.55, **kw):
    """Material der Spielwelt (Name 'sw_*', Farbe aus PAL oder Hex)."""
    return L.mat(f"sw_{name}", PAL.get(col, col), r, **kw)


def rbox(name, size, mat, parent, loc, coll, r=0.06, seg=2):
    """Kasten mit runden Kanten (Spiel-Look)."""
    r = min(r, min(size) * 0.45)
    return L.box(name, size, mat, parent, loc, coll, bevel=r, seg=seg)


def text(name, s, size, mat, parent, loc, coll, rot=(math.pi / 2, 0, 0)):
    return L.text(name, s, size, mat, parent, loc, coll, extrude=0.01, rot=rot, font=L.font())


def outline(obj, breite=0.03):
    """Feine dunkle Outline: Kopie des Meshes mit Solidify nach aussen und umgedrehten Normalen, dunkles Material
    (sichtbar nur mit Rueckseiten-Ausblendung, siehe render_stil)."""
    if obj.type != "MESH" or obj.name.endswith("_ol"):
        return None
    me = obj.data.copy()
    me.materials.clear()
    me.materials.append(L.mat("sw_outline", OUTLINE, 0.9))
    h = bpy.data.objects.new(obj.name + "_ol", me)
    for c in obj.users_collection:
        c.objects.link(h)
    h.parent = obj
    mo = h.modifiers.new("ol", "SOLIDIFY")
    mo.thickness = breite
    mo.offset = 1.0
    mo.use_flip_normals = True
    mo.use_rim = False
    return h


def outlines_fuer(root, breite=0.03, min_groesse=0.05):
    """Outlines fuer alle Meshes unter root (sehr kleine Teile ausgenommen)."""
    for o in [root] + list(root.children_recursive):
        if o.type == "MESH" and not o.name.endswith("_ol") and max(o.dimensions) >= min_groesse:
            mt = o.active_material
            if mt is not None and mt.diffuse_color[3] < 0.99:      # Glas: keine Huelle (waere durchs Glas zu sehen)
                continue
            outline(o, breite)


def _griffe(x, out, tiefe=0):
    """Alle Objekte, die ein Katalog-Ergebnis (P) als Griffe fuer Animationen herausgibt."""
    if tiefe > 5 or x is None:
        return
    if isinstance(x, bpy.types.Object):
        out.add(x)
    elif isinstance(x, P):
        for v in x.__dict__.values():
            _griffe(v, out, tiefe + 1)
    elif isinstance(x, dict):
        for v in x.values():
            _griffe(v, out, tiefe + 1)
    elif isinstance(x, (list, tuple)):
        for v in x:
            _griffe(v, out, tiefe + 1)


def _rel(o, ziel):
    """Transformation von o relativ zu ziel aus den lokalen Matrizen (funktioniert auch bei Scale 0 weiter oben)."""
    from mathutils import Matrix
    m = Matrix.Identity(4)
    x = o
    while x is not None and x is not ziel:
        m = x.matrix_parent_inverse @ x.matrix_basis @ m
        x = x.parent
    return m


def zusammenfassen(p, root=None):
    """Statische Teile eines Katalog-Objekts zu je einem Mesh pro Griff zusammenfassen (Workbench rendert viele
    kleine Objekte langsam). Griffe = alle Objekte, die bauen() in P herausgibt (die Regie animiert nur diese);
    jedes andere Mesh wird in den naechsten Griff darueber eingebacken (Materialien bleiben). Schriften bleiben
    eigene Objekte. Vor outlines_fuer aufrufen."""
    root = root or p.root
    griffe = set()
    _griffe(p, griffe)
    griffe.add(root)
    bpy.context.view_layer.update()
    gruppen = {}
    for o in [root] + list(root.children_recursive):
        if o in griffe or o.type != "MESH" or o.modifiers:
            continue
        z = o.parent
        while z is not None and z not in griffe:
            z = z.parent
        if z is None:
            continue
        gruppen.setdefault(z, []).append(o)
    for ziel, objs in gruppen.items():
        if len(objs) < 2 and ziel.type == "MESH":
            continue
        bm = bmesh.new()
        mats, slot = [], {}
        for o in objs:
            me = o.data
            remap = []
            for m in me.materials:
                if m is None:
                    remap.append(0)
                    continue
                if m.name not in slot:
                    slot[m.name] = len(mats)
                    mats.append(m)
                remap.append(slot[m.name])
            tmp = bmesh.new()
            tmp.from_mesh(me)
            tmp.transform(_rel(o, ziel))
            for f in tmp.faces:
                f.material_index = remap[f.material_index] if remap else 0
            neu = bpy.data.meshes.new("tmp_m")
            tmp.to_mesh(neu)
            tmp.free()
            bm.from_mesh(neu)
            bpy.data.meshes.remove(neu)
        me = bpy.data.meshes.new(f"{ziel.name}_m")
        bm.to_mesh(me)
        bm.free()
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(f"{ziel.name}_m", me)
        for c in (ziel.users_collection or objs[0].users_collection):
            c.objects.link(ob)
        ob.parent = ziel
        ob.matrix_parent_inverse.identity()
        weg = set(objs)
        for o in objs:                                 # Kinder, die bleiben (Griffe, Schriften), an den Griff haengen
            for ch in list(o.children):
                if ch not in weg:
                    rel = _rel(ch, ziel)
                    ch.parent = ziel
                    ch.matrix_parent_inverse.identity()
                    ch.matrix_basis = rel
        for o in objs:
            bpy.data.objects.remove(o)
    return p


# ------------------------------------------------------------------ Weiche Schatten (aufgemalt, nach unten rechts)
SCHATTEN_VERSATZ = Vector((0.24, -0.24, 0.0))      # je Meter Objekthoehe: nach rechts unten im Bild
_DECALS = []


def schatten(name, coll, w, d, h, parent=None, loc=(0, 0, 0), rund=False):
    """Weicher Schatten als drei uebereinanderliegende, halbtransparente Flaechen (Kern dunkler, Rand weich).
    Workbench-Schatten waeren pro Bild etwa siebenmal teurer. Laenge und Staerke folgen dem Wetter (wetter())."""
    o = L.empty(f"{name}_schatten", parent, loc, coll)
    m = L.mat("sw_schatten", "#140C1C", 0.9, alpha=0.2)
    off = SCHATTEN_VERSATZ * h * 0.5
    for k, f in enumerate((1.0, 1.1, 1.22)):
        sx, sy = (w * 1.02 + abs(off.x) * 2) * f, (d * 1.02 + abs(off.y) * 2) * f
        if rund:
            L.cyl(f"{name}_sch{k}", 0.5, 0.004, 16, m, o, (off.x, off.y, 0.012 + 0.001 * k), coll).scale = (sx, sy, 1)
        else:
            rbox(f"{name}_sch{k}", (sx, sy, 0.004), m, o, (off.x, off.y, 0.012 + 0.001 * k), coll, r=min(sx, sy) * 0.3, seg=2)
    _DECALS.append((o, h))
    return o


# ------------------------------------------------------------------ Katalog
_KAT = {}


def katalog(name):
    """Objekt-Modul aus assets/spielwelt laden (INFO, bauen, Zustaende)."""
    if name not in _KAT:
        _KAT[name] = importlib.import_module(name)
    return _KAT[name]


def manifest():
    with open(os.path.join(KATALOG, "manifest.json"), encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ Set
KEIN_SCHATTEN = ("spielbrett", "laden_puppenhaus", "spieler_marker", "sternchen", "muenz_pop", "duftlinien", "rauchwolke",
                 "theke_auslage", "kasse", "laptop_mini", "marktplatz")


def build_spielwelt(coll, origin):
    from build_world import SetData
    S = SetData("spielwelt", origin)
    S.raster = lambda x, y, z=0.0: S.p(x, y, z)
    S.stadt = lambda x, y: (x * STADT_X, y * STADT_Y)          # stadtkarte-Koordinaten -> Raster
    S.laden_o = S.p(0, 70, 0)
    S.filiale_o = S.p(0, 90, 0)
    man = manifest()
    S.inst = {}
    for pl in man["platzierungen"]:
        mod = katalog(pl["objekt"])
        kw = dict(pl.get("parameter", {}))
        ebene_o = {"spiel_stadt": S.p(0, 0, 0), "spiel_laden": S.laden_o, "filiale": S.filiale_o}[pl.get("ebene", "spiel_stadt")]
        o = mod.bauen(coll, pl["id"], **kw)
        x, y = pl["raster"]
        o.root.location = ebene_o + Vector((x, y, pl.get("z", 0.0)))
        o.root.rotation_euler = (0, 0, math.radians(pl.get("drehung", 0)))
        o.info = mod.INFO
        S.inst[pl["id"]] = o
        zusammenfassen(o)
        w_, d_, h_ = (mod.INFO.get("groesse") or [0, 0, 0])[:3]
        if abs(pl.get("drehung", 0)) % 180 == 90:
            w_, d_ = d_, w_
        if pl.get("schatten", h_ >= 0.4 and pl.get("outline", True)) and pl["objekt"] not in KEIN_SCHATTEN:
            if pl["objekt"] in ("zug", "fahrzeug"):
                schatten(pl["id"], coll, w_, d_, h_, parent=o.root, rund=pl["objekt"] == "fahrzeug")
            else:
                schatten(pl["id"], coll, w_, d_, h_, loc=o.root.location, rund=pl["objekt"] in ("baum", "laterne", "tonne_reste"))
        if pl.get("outline", True):
            outlines_fuer(o.root, 0.035 if pl.get("ebene", "spiel_stadt") == "spiel_stadt" else 0.025)
    # Himmel-Kuppel (Farbe je Wetter) und Hintergrund-Ebene unter dem Spielbrett
    S.m_himmel = L.unique_mat(m("himmel", "himmel", 0.8), "sw_himmel_m")
    hi = L.cyl("sw_himmel", 60.0, 60.0, 40, S.m_himmel, None, S.p(0, 20, 10), coll, cap=False)
    hi.data.flip_normals()                       # von innen sichtbar (Rueckseiten werden im Spiel-Stil ausgeblendet)
    L.box("sw_tief", (140, 200, 0.2), S.m_himmel, None, S.p(0, 30, -3.0), coll)      # Brett schwebt vor dem Himmel
    S.kalle = S.p(-4.65, -10.5, 0)              # vor Kalles Laden (Eingang)
    return S


# ------------------------------------------------------------------ Bewegung
def wegpunkte_fn(punkte, tempo, phase=0.0, loop=True):
    """Position auf einem Weg (Liste Weltpunkte) als Funktion des Frames: (pos, richtung)."""
    pts = [Vector(p) for p in punkte]
    segs = list(zip(pts, pts[1:] + ([pts[0]] if loop else [])))
    laenge = sum((b - a).length for a, b in segs) or 1.0

    def fn(f):
        d = (phase + f * tempo / FPS) % laenge if loop else min(laenge, phase + f * tempo / FPS)
        for a, b in segs:
            ln = (b - a).length
            if d <= ln:
                return a.lerp(b, d / max(1e-6, ln)), (b - a)
            d -= ln
        return pts[-1], segs[-1][1] - segs[-1][0]
    return fn


def laufen(T, obj, weg_fn, f0, f1, huepfen=0.04, beine=None, wippen=True):
    """Figur/Fahrzeug folgt weg_fn(f) -> (pos, richtung); Blick in Laufrichtung, kleines Wippen beim Gehen."""
    def loc(f):
        p, _ = weg_fn(f)
        return tuple(p + Vector((0, 0, huepfen * abs(math.sin(f * 0.45)) if wippen else 0)))

    def rot(f):
        _, d = weg_fn(f)
        return (0, 0, math.atan2(-d.x, d.y) + math.pi if d.length > 1e-6 else 0)
    T.set(obj.root, "location", loc, f0, f1)
    T.set(obj.root, "rotation_euler", rot, f0, f1)
    for k, b in enumerate(beine or []):
        T.set(b, "rotation_euler", lambda f, k=k: (0.6 * math.sin(f * 0.45 + k * math.pi), 0, 0), f0, f1)


# ------------------------------------------------------------------ Wetter und Tageszeit
# Toenung im linearen Farbraum (wirkt im Bild etwa wie die Wurzel davon)
WETTER_TOENUNG = {"sonne": (1.06, 1.0, 0.9), "regen": (0.5, 0.55, 0.7), "abend": (0.62, 0.4, 0.52),
                  "nacht": (0.2, 0.22, 0.42)}
HIMMEL = {"sonne": "#9FD3F2", "regen": "#7E8796", "abend": "#C97B6E", "nacht": "#1E2550"}
# Schatten je Wetter: (Lichtrichtung, Staerke); abends tief stehende Sonne = lange Schatten
SCHATTEN = {"sonne": ((-0.4, 0.8, 0.45), 0.3), "regen": ((-0.3, 0.6, 0.75), 0.12), "abend": ((-0.88, 0.42, 0.16), 0.38),
            "nacht": ((-0.3, 0.6, 0.75), 0.1)}
_STIL = {"wetter": None}
AUSNAHMEN = ("sw_outline", "sw_licht", "sw_laterne_an", "sw_ui", "sw_tuerkis", "sw_gold_leucht", "sw_himmel")


def wetter(T, S, plan, f0, f1):
    """plan: [(frame, 'sonne' | 'regen' | 'abend' | 'nacht'), ...] mit 20-Frame-Uebergaengen. Toent alle Spielwelt-
    Materialien, faerbt den Himmel, schaltet Regen, Pfuetzen, Schirme, Voegel und Laternen."""
    plan = sorted(plan)

    def mix(f):
        cur, prev, t0 = plan[0][1], plan[0][1], plan[0][0]
        for fr, w in plan:
            if fr <= f:
                prev, cur, t0 = cur, w, fr
        return prev, cur, clamp01((f - t0) / 20)

    def ton(f, k):
        a, b, t = mix(f)
        return WETTER_TOENUNG[a][k] + (WETTER_TOENUNG[b][k] - WETTER_TOENUNG[a][k]) * t
    for mt in list(bpy.data.materials):
        if not mt.name.startswith("sw_") or mt.name.startswith(AUSNAHMEN):
            continue
        for k in range(3):
            T.mul(mt, "diffuse_color", lambda f, k=k: ton(f, k), f0, f1, index=k)
    hc = {k: L.srgb(v) for k, v in HIMMEL.items()}

    def himmel(f):
        a, b, t = mix(f)
        return tuple(hc[a][i] + (hc[b][i] - hc[a][i]) * t for i in range(3)) + (1.0,)
    T.set(S.m_himmel, "diffuse_color", himmel, f0, f1)
    S.wetter_an = lambda name, f: (lambda a, b, t: (t if b == name else 0.0) + ((1 - t) if a == name else 0.0))(*mix(f))
    _STIL["wetter"] = mix
    laenge = {"sonne": 1.0, "regen": 0.55, "abend": 2.0, "nacht": 0.5}
    staerke = {"sonne": 0.2, "regen": 0.06, "abend": 0.17, "nacht": 0.04}

    def wert(tab, f):
        a, b, t = mix(f)
        return tab[a] + (tab[b] - tab[a]) * t
    for o, h in _DECALS:
        for ch in o.children:
            x0, y0 = ch.location.x, ch.location.y
            T.set(ch, "location", lambda f, x0=x0, y0=y0: (x0 * wert(laenge, f), y0 * wert(laenge, f), 0.012), f0, f1)
        T.set(o, "scale", lambda f: (1 + 0.1 * (wert(laenge, f) - 1), 1 + 0.1 * (wert(laenge, f) - 1), 1), f0, f1)
    m_s = bpy.data.materials.get("sw_schatten")
    if m_s is not None:
        T.set(m_s, "diffuse_color", lambda f: wert(staerke, f), f0, f1, index=3)
    for inst in S.inst.values():
        if hasattr(inst, "wetter"):
            inst.wetter(T, S, f0, f1)


def regen(T, S, coll, mitte, groesse, n, f0, f1, staerke_fn, seed=3):
    """Regentropfen (schraege Striche) fallen in einem Quader um mitte; staerke_fn(f) 0..1."""
    rnd = random.Random(seed)
    mt = m("regen", "#CFE6FF", 0.3, alpha=0.75)
    out = []
    for k in range(n):
        o = L.box(f"sw_tropfen{k}", (0.02, 0.02, 0.32), mt, None, (0, 0, 0), coll)
        o.rotation_euler = (0.25, 0, 0)
        x0, y0, z0, sp = (rnd.uniform(-0.5, 0.5) * groesse[0], rnd.uniform(-0.5, 0.5) * groesse[1],
                          rnd.uniform(0, groesse[2]), rnd.uniform(0.35, 0.5))
        thr = rnd.random()
        T.set(o, "location", lambda f, x0=x0, y0=y0, z0=z0, sp=sp: tuple(Vector(mitte) + Vector(
            (x0, y0 - ((f * sp * 0.25) % groesse[2]) * 0.25, groesse[2] - ((z0 + f * sp) % groesse[2])))), f0, f1)
        T.set(o, "scale", lambda f, thr=thr: (1.0,) * 3 if thr < staerke_fn(f) else (0.0,) * 3, f0, f1)
        out.append(o)
    return out


# ------------------------------------------------------------------ Kameras (35 Grad von oben, fester Winkel)
NEIGUNG = math.radians(35)
AZIMUT = math.radians(14)


def _iso(ziel, abstand, lens):
    ziel = Vector(ziel)
    d = Vector((math.sin(AZIMUT) * math.cos(NEIGUNG), -math.cos(AZIMUT) * math.cos(NEIGUNG), math.sin(NEIGUNG)))
    return (ziel + d * abstand, ziel, lens)


def spiel_stadt(S, f0, f1, ziel=(0.0, 1.0, 0.0), abstand=62.0, lens=58.0, drift=1.2):
    """Isometrische Totale ueber die ganze Stadt, langsame Drift."""
    def fn(f):
        t = (f - f0) / FPS
        z = S.p(*ziel) + Vector((drift * math.sin(t * 0.18), drift * 0.6 * math.sin(t * 0.13 + 1.0), 0))
        return _iso(z, abstand, lens)
    return fn


def spiel_laden(S, f0, f1, ziel=None, abstand=23.0, lens=46.0, drift=0.25, laden="haupt"):
    """Puppenhaus-Ansicht in den Laden, gleicher Winkel."""
    o = S.laden_o if laden == "haupt" else S.filiale_o
    zl = Vector(ziel) if ziel is not None else o + Vector((-0.2, 0.4, 0.6))

    def fn(f):
        t = (f - f0) / FPS
        return _iso(zl + Vector((drift * math.sin(t * 0.3), drift * 0.5 * math.sin(t * 0.21), 0)), abstand, lens)
    return fn


def spiel_flug(A, B, f0, f1):
    """Weicher Flug zwischen zwei Iso-Einstellungen (pos, ziel, lens) bzw. Funktionen davon."""
    def get(X, f):
        return X(f) if callable(X) else X

    def fn(f):
        t = ease_in_out(clamp01((f - f0) / max(1, f1 - f0)))
        a, b = get(A, f), get(B, f)
        return (Vector(a[0]).lerp(Vector(b[0]), t), Vector(a[1]).lerp(Vector(b[1]), t), a[2] + (b[2] - a[2]) * t)
    return fn


def render_stil(sc, an, f=None):
    """Spielwelt-Stil fuer Workbench ein/aus: Rueckseiten ausblenden (Outlines), weiche Schatten nach unten rechts
    (je Wetter: abends lange Schatten, bei Regen fast keine)."""
    sh = sc.display.shading
    sh.show_backface_culling = an
    sh.show_shadows = False                          # weiche Schatten sind aufgemalt (schatten()), siebenmal schneller
    sh.cavity_type = "WORLD" if an else "BOTH"       # keine Kanten-Glanzlinien auf den Low-Poly-Rundungen
    if an:
        d, st = SCHATTEN["sonne"]
        if _STIL["wetter"] is not None and f is not None:
            a, b, t = _STIL["wetter"](f)
            (da, sa), (db, sb) = SCHATTEN[a], SCHATTEN[b]
            d = tuple(x + (y - x) * t for x, y in zip(da, db))
            st = sa + (sb - sa) * t
        sh.shadow_intensity = st
        sc.display.light_direction = d
        sc.display.shadow_shift = 0.1
        sc.display.shadow_focus = 0.5


def ein_aus(T, obj, f_an, f_aus=None, s=1.0, dur=8):
    end = (f_aus + dur) if f_aus is not None else f_an + dur + 1
    T.set(obj, "scale", lambda f: ((s * pop(f, f_an, dur) * (unpop(f, f_aus, 6) if f_aus is not None and f > f_aus else 1)),) * 3,
          f_an - 1, end)


__all__ = ["build_spielwelt", "katalog", "manifest", "m", "rbox", "text", "outline", "outlines_fuer", "wegpunkte_fn",
           "laufen", "zusammenfassen", "schatten", "wetter", "regen", "spiel_stadt", "spiel_laden", "spiel_flug", "render_stil", "ein_aus", "P", "PAL",
           "bmesh"]
