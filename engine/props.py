"""Wiederverwendbare Requisiten und Partikel (alle Zufallswerte mit festem Seed)."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import look as L
from anim import (ease_in_out, ease_out, ease_out_back, spring, tween, window, pop, unpop, Noise)

FPS = 30


class P:
    """Einfacher Container fuer Requisiten-Teile."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


# ------------------------------------------------------------------ Mehlsack 25 kg
def flour_sack(coll, name, label=True, scale=1.0, color=L.BURLAP, bow=False, text1="MEHL", text2="25 kg"):
    root = L.empty(name, coll=coll)
    root.scale = (scale,) * 3
    body = L.empty(f"{name}_body", root, (0, 0, 0), coll)      # Squash-Pivot am Boden
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=2, use_grid_fill=True)
    for v in bm.verts:
        x, y, z = v.co
        z01 = z + 0.5
        bulge = 1.0 + 0.16 * math.sin(math.pi * min(1, z01 * 1.1))
        top = 1.0 - 0.38 * max(0, z01 - 0.7) / 0.3
        v.co = Vector((x * 0.46 * bulge * top, y * 0.30 * bulge * top, z01 * 0.62))
    m_sack = L.mat(f"sack_{color}", color, 0.85)
    sack = L.from_bm(f"{name}_mesh", bm, m_sack, body, (0, 0, 0), coll)
    # zugebundener Zipfel
    L.cyl(f"{name}_neck", 0.07, 0.06, 8, L.mat("sack_tie", "#8C6A45", 0.8), body, (0, 0, 0.63), coll)
    L.cyl(f"{name}_tuft", 0.11, 0.09, 8, m_sack, body, (0, 0, 0.7), coll, r2=0.05)
    if label:
        lab = L.empty(f"{name}_label", body, (0, -0.165, 0.30), coll)
        L.box(f"{name}_labelplate", (0.34, 0.012, 0.22), L.mat("sack_label", L.FLOUR, 0.65), lab, (0, 0, 0), coll,
              bevel=0.01)
        mt = L.mat("sack_text", "#5A3B26", 0.6)
        L.text(f"{name}_t1", text1, 0.11 if len(text1) <= 5 else 0.075, mt, lab, (0, -0.008, 0.03), coll,
               extrude=0.003, font=L.font())
        L.text(f"{name}_t2", text2, 0.065, mt, lab, (0, -0.008, -0.06), coll, extrude=0.003, font=L.font())
    if bow:
        mb = L.mat("bow", L.RED, 0.55)
        for sx in (-1, 1):
            o = L.sphere(f"{name}_bow{sx}", 0.07, 8, 5, (1.2, 0.5, 0.7), mb, body, (sx * 0.08, -0.02, 0.66), coll)
            o.rotation_euler = (0, sx * 0.5, 0)
        L.sphere(f"{name}_bowknot", 0.035, 8, 5, (1, 1, 1), mb, body, (0, -0.04, 0.66), coll)
    return P(root=root, body=body, mesh=sack, mat=m_sack)


# ------------------------------------------------------------------ Briefumschlag
def envelope(coll, name, scale=1.0):
    root = L.empty(name, coll=coll)
    root.scale = (scale,) * 3
    m_p = L.mat("paper", L.FLOUR, 0.62)
    m_in = L.mat("paper_in", "#E6DFD0", 0.65)
    body = L.box(f"{name}_body", (0.42, 0.02, 0.28), m_p, root, (0, 0, 0), coll, bevel=0.006)
    # Vorderseiten-Falz (Dreiecke)
    L.poly_flat(f"{name}_fold", [(-0.21, -0.14), (0.0, 0.0), (0.21, -0.14)], 0.004, m_in, root, (0, -0.012, 0),
                coll)
    sheet = L.box(f"{name}_sheet", (0.36, 0.006, 0.24), L.mat("sheet", "#FFFFFF", 0.6), root, (0, 0.004, 0.0), coll)
    lines = []
    for i in range(3):
        lines.append(L.box(f"{name}_line{i}", (0.22 - 0.05 * (i == 2), 0.004, 0.018), L.mat("ink", L.NAVY2, 0.6),
                           sheet, (-0.04, -0.005, 0.06 - i * 0.045), coll))
    flap = L.empty(f"{name}_flappiv", root, (0, -0.012, 0.14), coll)
    L.poly_flat(f"{name}_flap", [(-0.21, 0.0), (0.0, -0.17), (0.21, 0.0)], 0.006, m_p, flap, (0, 0, 0), coll)
    L.cyl(f"{name}_seal", 0.03, 0.01, 10, L.mat("seal", L.RED, 0.55), flap, (0, -0.01, -0.12), coll, axis="Y")
    return P(root=root, body=body, flap=flap, sheet=sheet)


def paper_plane(coll, name, scale=1.0):
    root = L.empty(name, coll=coll)
    root.scale = (scale,) * 3
    m = L.mat("paper", L.FLOUR, 0.62)
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in [(0, 0.3, 0), (-0.16, -0.18, 0.02), (0, -0.14, -0.05), (0.16, -0.18, 0.02),
                                   (0, -0.16, 0.0)]]
    bm.faces.new((v[0], v[1], v[4]))
    bm.faces.new((v[0], v[4], v[3]))
    bm.faces.new((v[0], v[2], v[4]))
    L.from_bm(f"{name}_mesh", bm, m, root, (0, 0, 0), coll)
    return P(root=root)


# ------------------------------------------------------------------ Postfach-Symbol mit Zaehler
def inbox_icon(coll, name):
    root = L.empty(name, coll=coll)
    tile = L.box(f"{name}_tile", (0.36, 0.05, 0.3), L.mat("inbox_tile", L.NAVY2, 0.5), root, (0, 0, 0), coll,
                 bevel=0.04, seg=2)
    m_t = L.mat("inbox_tray", L.TURQ, 0.5, emit=L.TURQ, strength=2.5)
    for (x, z, w, h) in [(0, -0.06, 0.24, 0.025), (-0.11, -0.01, 0.025, 0.12), (0.11, -0.01, 0.025, 0.12),
                         (-0.05, -0.04, 0.06, 0.02), (0.05, -0.04, 0.06, 0.02)]:
        L.box(f"{name}_tr{x}{z}", (w, 0.02, h), m_t, root, (x, -0.03, z), coll)
    badge = L.empty(f"{name}_badge", root, (0.16, -0.05, 0.13), coll)
    L.cyl(f"{name}_badgedisc", 0.085, 0.03, 16, L.mat("badge_red", L.RED, 0.5, emit=L.RED, strength=0.6), badge,
          (0, 0, 0), coll, axis="Y")
    digits = []
    for d in "123":
        t = L.text(f"{name}_n{d}", d, 0.12, L.mat("badge_digit", "#FFFFFF", 0.5), badge, (0, -0.02, -0.005), coll,
                   extrude=0.004, font=L.font())
        t.scale = (0, 0, 0)
        digits.append(t)
    return P(root=root, badge=badge, digits=digits)


# ------------------------------------------------------------------ Preisschild
def price_tag(coll, name, text, good=False, mode="string", width=0.62):
    """mode 'string': haengt an einer Schnur (Pendel um X). mode 'hinge': Scharnier an der Oberkante."""
    color = L.GREEN if good else L.RED
    root = L.empty(name, coll=coll)
    piv = L.empty(f"{name}_piv", root, (0, 0, 0), coll)
    m_tag = L.mat(f"tag_{color}", color, 0.55, emit=color, strength=0.25)
    drop = 0.3 if mode == "string" else 0.0
    if mode == "string":
        L.cyl(f"{name}_string", 0.006, drop, 5, L.mat("string", "#D8CBB3", 0.8), piv, (0, 0, -drop / 2), coll)
        L.sphere(f"{name}_pin", 0.025, 8, 5, (1, 1, 1), L.mat("pin", L.METAL, 0.5, metallic=0.5), root, (0, 0, 0),
                 coll)
    h = 0.26
    body = L.box(f"{name}_body", (width, 0.03, h), m_tag, piv, (0, 0, -drop - h / 2), coll, bevel=0.03, seg=2)
    L.cyl(f"{name}_hole", 0.022, 0.04, 10, L.mat("hole", L.NAVY, 0.6), piv, (0, 0, -drop - 0.035), coll, axis="Y")
    L.text(f"{name}_text", text, 0.13 if len(text) < 9 else 0.105, L.mat("tagtext", "#FFFFFF", 0.5,
                                                                          emit="#FFFFFF", strength=0.3),
           piv, (0, -0.02, -drop - h / 2 - 0.02), coll, extrude=0.004, font=L.font())
    return P(root=root, piv=piv, body=body, mat=m_tag)


# ------------------------------------------------------------------ Muenzen
_COIN_MESH = {}


def coin(coll, name, parent=None, loc=(0, 0, 0)):
    m = L.mat("coin", L.GOLD, 0.42, metallic=0.75, emit=L.GOLD, strength=0.12)
    m2 = L.mat("coin_rim", "#D99A42", 0.45, metallic=0.75)
    root = L.empty(name, parent, loc, coll)
    if "c" not in _COIN_MESH:
        a = L.cyl("coin_proto", 0.1, 0.03, 14, m, None, (0, 0, 0), coll)
        b = L.cyl("coin_proto_in", 0.072, 0.034, 14, m2, None, (0, 0, 0), coll)
        _COIN_MESH["c"] = (a.data, b.data)
        bpy.data.objects.remove(a)
        bpy.data.objects.remove(b)
    o = bpy.data.objects.new(f"{name}_m", _COIN_MESH["c"][0])
    L.link(o, coll)
    o.parent = root
    o2 = bpy.data.objects.new(f"{name}_i", _COIN_MESH["c"][1])
    L.link(o2, coll)
    o2.parent = root
    return root


def coin_column(coll, name, n, spacing=0.032):
    root = L.empty(name, coll=coll)
    coins = [coin(coll, f"{name}_c{i}", root, (0, 0, 0.015 + i * spacing)) for i in range(n)]
    return P(root=root, coins=coins, height=n * spacing)


# ------------------------------------------------------------------ Balkenwaage
def balance(coll, name):
    root = L.empty(name, coll=coll)
    m_b = L.mat("scale_brass", L.GOLD, 0.45, metallic=0.6)
    m_d = L.mat("scale_dark", L.NAVY2, 0.55)
    L.cyl(f"{name}_foot", 0.38, 0.1, 16, m_d, root, (0, 0, 0.05), coll, r2=0.3)
    L.cyl(f"{name}_post", 0.05, 1.5, 10, m_b, root, (0, 0, 0.85), coll)
    L.sphere(f"{name}_cap", 0.08, 10, 6, (1, 1, 1), m_b, root, (0, 0, 1.62), coll)
    beam = L.empty(f"{name}_beam", root, (0, 0, 1.55), coll)
    L.box(f"{name}_beammesh", (1.9, 0.07, 0.07), m_b, beam, (0, 0, 0), coll, bevel=0.02)
    pans = []
    for sx in (-1, 1):
        hang = L.empty(f"{name}_hang{sx}", beam, (sx * 0.9, 0, 0), coll)
        for k in range(3):
            a = 2 * math.pi * k / 3
            s = L.cyl(f"{name}_str{sx}{k}", 0.006, 0.62, 4, L.mat("string", "#D8CBB3", 0.8), hang,
                      (0.12 * math.cos(a) / 2, 0.12 * math.sin(a) / 2, -0.3), coll)
        L.cyl(f"{name}_pan{sx}", 0.3, 0.06, 16, m_b, hang, (0, 0, -0.62), coll, r2=0.24)
        pans.append(hang)
    return P(root=root, beam=beam, pans=pans)


# ------------------------------------------------------------------ Schwebende Tastatur
def keyboard(coll, name, cols=10, rows=4):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_base", (cols * 0.11 + 0.08, 0.36 + 0.1, 0.05), L.mat("kb_base", L.NAVY2, 0.5), root, (0, 0, 0),
          coll, bevel=0.02)
    L.box(f"{name}_edge", (cols * 0.11 + 0.1, 0.36 + 0.12, 0.02), L.mat("kb_edge", L.TURQ, 0.5, emit=L.TURQ,
                                                                          strength=1.5), root, (0, 0, -0.03), coll)
    keys = []
    for r in range(rows):
        for cc in range(cols):
            piv = L.empty(f"{name}_k{r}_{cc}", root, ((cc - (cols - 1) / 2) * 0.11, (r - (rows - 1) / 2) * 0.1, 0.03),
                          coll)
            mk = L.unique_mat(L.mat("key", "#3A3566", 0.55, emit=L.TURQ, strength=0.0), f"{name}_kmat{r}_{cc}")
            L.box(f"{name}_km{r}_{cc}", (0.09, 0.08, 0.04), mk, piv, (0, 0, 0.02), coll, bevel=0.012)
            keys.append((piv, mk))
    return P(root=root, keys=keys)


# ------------------------------------------------------------------ Senden-Button
def send_button(coll, name, r=0.2, holo=False):
    root = L.empty(name, coll=coll)
    alpha = 0.75 if holo else None
    L.cyl(f"{name}_base", r * 1.15, 0.05, 20, L.mat("btn_base" + ("h" if holo else ""), L.NAVY2, 0.5, alpha=alpha),
          root, (0, 0, 0.025), coll)
    cap = L.empty(f"{name}_cap", root, (0, 0, 0.05), coll)
    m_c = L.unique_mat(L.mat("btn_cap" + ("h" if holo else ""), L.TURQ, 0.5, emit=L.TURQ, strength=1.6, alpha=alpha),
                       f"{name}_capmat")
    L.cyl(f"{name}_capmesh", r, 0.07, 20, m_c, cap, (0, 0, 0.035), coll)
    icon = L.poly_flat(f"{name}_icon", [(-0.09, -0.05), (0.1, 0.0), (-0.09, 0.05), (-0.05, 0.0)], 0.01,
                       L.mat("btn_icon", "#FFFFFF", 0.5, emit="#FFFFFF", strength=1.0), cap, (0, 0, 0.075), coll,
                       plane="XY")
    icon.scale = (r / 0.2,) * 3
    return P(root=root, cap=cap, mat=m_c)


# ------------------------------------------------------------------ Wanduhr
def wall_clock(coll, name, r=0.32):
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_rim", r, 0.06, 20, L.mat("clock_rim", L.WOOD_DARK, 0.6), root, (0, 0, 0), coll, axis="Y")
    L.cyl(f"{name}_face", r * 0.88, 0.07, 20, L.mat("clock_face", L.FLOUR, 0.6), root, (0, -0.005, 0), coll, axis="Y")
    for i in range(12):
        a = 2 * math.pi * i / 12
        L.box(f"{name}_tick{i}", (0.02, 0.01, 0.05 if i % 3 == 0 else 0.03), L.mat("ink", L.NAVY2, 0.6), root,
              (math.sin(a) * r * 0.74, -0.045, math.cos(a) * r * 0.74), coll).rotation_euler = (0, a, 0)
    hands = []
    for i, (ln, w) in enumerate([(0.17, 0.03), (0.25, 0.02)]):
        piv = L.empty(f"{name}_hand{i}", root, (0, -0.05 - 0.008 * i, 0), coll)
        L.box(f"{name}_handm{i}", (w, 0.01, ln), L.mat("clock_hand", L.NAVY, 0.6), piv, (0, 0, ln / 2 - 0.02), coll)
        hands.append(piv)
    L.cyl(f"{name}_hub", 0.025, 0.03, 10, L.mat("clock_hub", L.RED, 0.5), root, (0, -0.07, 0), coll, axis="Y")
    return P(root=root, hands=hands)


# ------------------------------------------------------------------ Lesebrille
def reading_glasses(coll, name, parent=None, loc=(0, 0, 0)):
    root = L.empty(name, parent, loc, coll)
    m = L.mat("glasses", "#2B2440", 0.5)
    for sx in (-1, 1):
        L.torus(f"{name}_rim{sx}", 0.075, 0.012, 14, 5, m, root, (sx * 0.115, 0, 0), coll, axis="Y")
        L.box(f"{name}_arm{sx}", (0.01, 0.3, 0.012), m, root, (sx * 0.19, 0.15, 0.01), coll)
    L.box(f"{name}_bridge", (0.07, 0.012, 0.012), m, root, (0, 0, 0.02), coll)
    return root


# ------------------------------------------------------------------ Laptop
def laptop(coll, name, screen_mat=None):
    root = L.empty(name, coll=coll)
    m = L.mat("laptop", "#9AA0B8", 0.45, metallic=0.3)
    L.box(f"{name}_base", (0.62, 0.42, 0.03), m, root, (0, 0, 0.015), coll, bevel=0.01)
    L.box(f"{name}_keys", (0.52, 0.2, 0.004), L.mat("laptop_keys", "#2D2A44", 0.6), root, (0, -0.02, 0.032), coll)
    lid = L.empty(f"{name}_lid", root, (0, 0.2, 0.03), coll)
    lid.rotation_euler = (math.radians(-12), 0, 0)
    L.box(f"{name}_lidmesh", (0.62, 0.025, 0.4), m, lid, (0, 0.012, 0.2), coll, bevel=0.01)
    scr = L.box(f"{name}_screen", (0.56, 0.01, 0.34), screen_mat or L.mat("laptop_screen", "#1E2A4A", 0.4,
                                                                           emit=L.TURQ, strength=0.35),
                lid, (0, -0.003, 0.2), coll)
    return P(root=root, lid=lid, screen=scr)


# ------------------------------------------------------------------ Partikel
_PMESH = {}


def _proto(kind, coll):
    if kind in _PMESH:
        return _PMESH[kind]
    if kind == "dust":
        o = L.ico("p_dust", 0.018, 1, (1, 1, 1), L.mat("dust", L.FLOUR, 0.6, emit=L.FLOUR, strength=1.2), None,
                  (0, 0, 0), coll)
    elif kind == "puff":
        o = L.ico("p_puff", 0.07, 2, (1, 1, 0.8), L.mat("puff", L.FLOUR, 0.9, emit=L.FLOUR, strength=0.35, alpha=0.45),
                  None, (0, 0, 0), coll)
    elif kind == "spark":
        o = L.ico("p_spark", 0.025, 0, (1, 1, 1.6), L.mat("spark", L.YELLOW, 0.4, emit=L.YELLOW, strength=6.0), None,
                  (0, 0, 0), coll)
    elif kind == "sparkt":
        o = L.ico("p_sparkt", 0.022, 0, (1, 1, 1.6), L.mat("sparkt", L.TURQ, 0.4, emit=L.TURQ, strength=6.0), None,
                  (0, 0, 0), coll)
    elif kind.startswith("confetti"):
        col = kind.split("_")[1]
        o = L.box(f"p_{kind}", (0.05, 0.008, 0.03), L.mat(f"conf_{col}", col, 0.6, emit=col, strength=0.3), None,
                  (0, 0, 0), coll)
    elif kind == "bang":
        o = L.text("p_bang", "!", 0.22, L.mat("bang", L.YELLOW, 0.4, emit=L.YELLOW, strength=4.0), None, (0, 0, 0),
                   coll, extrude=0.02, font=L.font())
        me = bpy.data.meshes.new_from_object(o)
        bpy.data.objects.remove(o)
        _PMESH[kind] = me
        return me
    elif kind == "crumb":
        o = L.ico("p_crumb", 0.008, 0, (1, 1, 0.7), L.mat("crumb", "#B8702E", 0.7), None, (0, 0, 0), coll)
    elif kind == "pix":
        o = L.box("p_pix", (0.02, 0.02, 0.02), L.mat("pix", "#BFFFF8", 0.4, emit="#BFFFF8", strength=4.0), None,
                  (0, 0, 0), coll)
    elif kind == "sweat":
        o = L.sphere("p_sweat", 0.02, 8, 5, (0.8, 0.8, 1.3), L.mat("sweat", "#BFFFF8", 0.2, emit="#BFFFF8",
                                                                  strength=1.0), None, (0, 0, 0), coll)
    elif kind == "flourdust":
        o = L.ico("p_flourdust", 0.03, 1, (1, 1, 1), L.mat("puff", L.FLOUR, 0.9, emit=L.FLOUR, strength=0.35,
                                                            alpha=0.45), None, (0, 0, 0), coll)
    elif kind == "coinp":
        o = L.cyl("p_coin", 0.06, 0.018, 12, L.mat("coin", L.GOLD, 0.42, metallic=0.75), None, (0, 0, 0), coll)
    else:
        raise ValueError(kind)
    me = o.data
    bpy.data.objects.remove(o)
    _PMESH[kind] = me
    return me


def burst(T, coll, name, kind, origin, f0, count, seed, speed=(1.0, 2.0), up=0.6, spread=1.0, gravity=-4.0,
          life=(18, 30), size=(0.7, 1.3), drag=0.0, spin=8.0, ring=False, slow=1.0, kinds=None, dir_bias=(0, 0, 0),
          fade_frac=0.35, tw=None, flutter=0.0, wobble=0.0):
    """Partikel-Explosion mit Schwerkraft, Seed, Rotation, Ausblenden (nie ewig im Bild)."""
    r = random.Random(seed)
    objs = []
    o0 = Vector(origin)
    for i in range(count):
        kd = kinds[i % len(kinds)] if kinds else kind
        me = _proto(kd, coll)
        o = bpy.data.objects.new(f"{name}_{i}", me)
        L.link(o, coll)
        if ring:
            a = 2 * math.pi * i / count + r.uniform(-0.15, 0.15)
            d = Vector((math.cos(a), math.sin(a) * 0.6, r.uniform(0.05, 0.35)))
        else:
            d = Vector((r.uniform(-1, 1) * spread, r.uniform(-1, 1) * spread * 0.6, r.uniform(0.2, 1.0) * up + 0.2))
        d = (d + Vector(dir_bias)).normalized() * r.uniform(*speed)
        lf = r.randint(*life)
        sz = r.uniform(*size)
        rot0 = Vector((r.uniform(0, 6.28), r.uniform(0, 6.28), r.uniform(0, 6.28)))
        rv = Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1))) * spin
        start = f0 + r.randint(0, 2)

        wph = r.uniform(0, 6.28)

        def pos(f, d=d, start=start, lf=lf, wph=wph):
            fe = tw(f) if tw else f
            t = max(0.0, min(fe - start, lf)) / FPS * slow
            if drag > 0:
                k = (1 - math.exp(-drag * t)) / drag
                p = o0 + d * k
            else:
                p = o0 + d * t
            p = p + Vector((0, 0, 0.5 * gravity * t * t))
            if wobble:
                p = p + Vector((wobble * math.sin(9 * t + wph), wobble * 0.5 * math.cos(7 * t + wph), 0))
            return tuple(p)

        def scl(f, start=start, lf=lf, sz=sz, wph=wph):
            f = tw(f) if tw else f
            if f < start:
                return (0, 0, 0)
            t = (f - start) / lf
            if t >= 1:
                return (0, 0, 0)
            a = ease_out_back(min(1, (f - start) / 4), 2.0)
            b = 1 - max(0, (t - (1 - fade_frac)) / fade_frac)
            s = sz * a * b
            if flutter:
                return (s * (1 - flutter * abs(math.sin(1.1 * (f - start) + wph))), s, s)
            return (s, s, s)

        end = start + lf + 1
        if tw:
            end = start + 1
            while tw(end) < start + lf + 1 and end < start + 2000:
                end += 1
        T.set(o, "location", pos, start - 1, end)
        T.set(o, "rotation_euler", lambda f, rot0=rot0, rv=rv, start=start: tuple(
            rot0 + rv * max(0, (tw(f) if tw else f) - start) / FPS), start - 1, end)
        T.set(o, "scale", scl, start - 1, end)
        objs.append(o)
    return objs


def ambient_motes(T, coll, name, center, size, count, seed, f0, f1, color_kind="dust", drift=0.05, scale=1.0):
    """Schwebender Mehlstaub / Lichtpunkte: langsames Driften, sanftes Ein-/Ausblenden."""
    r = random.Random(seed)
    me = _proto(color_kind, coll)
    c = Vector(center)
    objs = []
    for i in range(count):
        o = bpy.data.objects.new(f"{name}_{i}", me)
        L.link(o, coll)
        p0 = c + Vector((r.uniform(-1, 1) * size[0], r.uniform(-1, 1) * size[1], r.uniform(-1, 1) * size[2]))
        ph = [r.uniform(0, 6.28) for _ in range(3)]
        fr = [r.uniform(0.05, 0.16) for _ in range(3)]
        sz = r.uniform(0.5, 1.4) * scale
        tw = r.uniform(0.2, 0.5)

        def pos(f, p0=p0, ph=ph, fr=fr):
            t = f / FPS
            return (p0.x + drift * 3 * math.sin(2 * math.pi * fr[0] * t + ph[0]),
                    p0.y + drift * 2 * math.sin(2 * math.pi * fr[1] * t + ph[1]),
                    p0.z + drift * 2.5 * math.sin(2 * math.pi * fr[2] * t + ph[2]) + 0.02 * t)

        def scl(f, sz=sz, ph=ph, tw=tw):
            s = sz * (0.65 + 0.35 * math.sin(2 * math.pi * tw * f / FPS + ph[0])) * window(f, f0, f1, 10, 10)
            return (s, s, s)

        T.set(o, "location", pos, f0, f1)
        T.set(o, "scale", scl, f0, f1)
        objs.append(o)
    return objs


def shock_ring(T, coll, name, loc, f0, dur=14, r_end=1.4, axis="Z", color=L.TURQ):
    m = L.unique_mat(L.mat("ring", color, 0.5, emit=color, strength=5.0), f"{name}_mat")
    o = L.torus(name, 1.0, 0.035, 32, 5, m, None, loc, coll, axis=axis)
    T.set(o, "scale", lambda f: ((0.05 + r_end * ease_out((f - f0) / dur)) if f >= f0 and f <= f0 + dur else 0,) * 3,
          f0 - 1, f0 + dur + 1)
    s = L.bsdf(m).inputs["Emission Strength"]
    T.set(s, "default_value", lambda f: 6.0 * (1 - ease_in_out((f - f0) / dur)), f0, f0 + dur)
    return o


def flash(T, coll, name, loc, f0, dur=8, r=0.6, color=L.FLOUR, energy=400):
    m = L.unique_mat(L.mat("flash", color, 0.5, emit=color, strength=8.0, alpha=0.8), f"{name}_mat")
    o = L.ico(name, r, 2, (1, 1, 1), m, None, loc, coll)
    T.set(o, "scale", lambda f: ((ease_out((f - f0) / dur) * (1 - ease_in_out((f - f0) / dur)) * 2.2)
                                 if f0 <= f <= f0 + dur else 0,) * 3, f0 - 1, f0 + dur + 1)
    lt = L.light(f"{name}_l", "POINT", 0, color, loc, size=0.3, coll=coll, shadow=False, cutoff=6)
    T.set(lt.data, "energy", lambda f: energy * window(f, f0, f0 + dur + 4, 2, dur), f0 - 1, f0 + dur + 5)
    return o


# =================================================================== Website-Folge: neue Requisiten
def _segment(name, a, b, r, mat, coll, seg=6):
    """Zylinder von Punkt a nach b (fuer Lichtlinien, Pfade)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    o = L.cyl(name, r, 1.0, seg, mat, None, (0, 0, 0), coll, origin="bottom")
    o.location = a
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    o["len"] = d.length
    o.scale = (1, 1, d.length)
    return o


def glow_line(T, coll, name, a, b, f_in, f_out=None, r=0.012, color=L.TURQ, dur=8):
    """Leuchtende Linie, die von a nach b waechst (und wieder verschwindet)."""
    m = L.mat(f"glowline_{color}", color, 0.5, emit=color, strength=5.0)
    o = _segment(name, a, b, r, m, coll)
    ln = o["len"]

    def scl(f):
        g = ease_out((f - f_in) / dur)
        if f_out is not None and f > f_out:
            g *= 1 - ease_in_out((f - f_out) / 6)
        return (1 if g > 0 else 0, 1 if g > 0 else 0, max(0.0, g) * ln)
    T.set(o, "scale", scl, f_in - 1, (f_out + 7) if f_out is not None else f_in + dur + 1)
    return o


# ------------------------------------------------------------------ Bestellzettel-Stapel
def order_slips(coll, name, n=14, seed=5):
    """Wackliger Stapel kleiner Bestellzettel (jeder mit Kritzel-Zeilen)."""
    r = random.Random(seed)
    root = L.empty(name, coll=coll)
    m_p = L.mat("slip_paper", "#FBF6EA", 0.75)
    m_y = L.mat("slip_yellow", "#F7E7A6", 0.75)
    m_ink = L.mat("slip_ink", "#3A4A8A", 0.6)
    slips = []
    for i in range(n):
        piv = L.empty(f"{name}_s{i}", root, (r.uniform(-0.03, 0.03), r.uniform(-0.03, 0.03), 0.004 + i * 0.011), coll)
        piv.rotation_euler = (r.uniform(-0.04, 0.04), r.uniform(-0.04, 0.04), r.uniform(-0.35, 0.35))
        L.box(f"{name}_sm{i}", (0.2, 0.15, 0.004), m_y if i % 4 == 1 else m_p, piv, (0, 0, 0), coll)
        for j in range(3):
            L.box(f"{name}_si{i}_{j}", (0.12 - 0.03 * (j == 2), 0.008, 0.002), m_ink, piv,
                  (-0.02, 0.04 - j * 0.03, 0.003), coll)
        slips.append(piv)
    return P(root=root, slips=slips)


def slips_flutter(T, sl, f0, f1, amount=1.0, seed=8):
    """Obere Zettel flattern im Luftzug."""
    n = len(sl.slips)
    for i, s in enumerate(sl.slips):
        k = amount * (0.2 + 0.8 * (i / (n - 1)) ** 2)
        nz = Noise(seed + i, 3, 1.4)
        T.add(s, "rotation_euler", lambda f, k=k, nz=nz: (0.18 * k * nz(f / FPS), 0.14 * k * nz(f / FPS + 3),
                                                           0.08 * k * nz(f / FPS + 6)), f0, f1)


def slips_blowaway(T, sl, idx, f0, targets, seed=12, dur=(22, 34)):
    """Zettel idx wirbeln hoch und segeln zu den Zielen (Weltkoordinaten), danach liegen sie dort."""
    r = random.Random(seed)
    for k, i in enumerate(idx):
        s = sl.slips[i]
        p_start = Vector(sl.root.location) + Vector(s.location)
        d = r.randint(*dur)
        st = f0 + k * 2
        tgt = Vector(targets[k % len(targets)])
        up = r.uniform(0.6, 1.1)
        spin = Vector((r.uniform(-6, 6), r.uniform(-6, 6), r.uniform(-9, 9)))

        def world(f, s=s, st=st, d=d, tgt=tgt, up=up, p0=p_start):
            t = min(1.0, max(0.0, (f - st) / d))
            p = p0.lerp(tgt, ease_in_out(t))
            p.z += up * math.sin(math.pi * min(1, t * 1.15)) + 0.06 * math.sin(t * 18)
            return p

        par = sl.root

        def loc(f, s=s, world=world):
            # in lokale Koordinaten des Stapels (Stapel steht still, ist nicht skaliert/rotiert)
            return tuple(world(f) - Vector(par.location))
        T.set(s, "location", loc, st, st + d + 1)
        T.set(s, "rotation_euler", lambda f, st=st, d=d, spin=spin: tuple(
            spin * ease_out(min(1.0, max(0.0, (f - st) / d))) * 0.5), st, st + d + 1)


def V3(x):
    return Vector(x)


# ------------------------------------------------------------------ Rezeptkarte
def recipe_card(coll, name, lines=("1 Mehl", "2 Wasser", "3 Backen")):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_card", (0.9, 0.03, 0.78), L.mat("recipe_card", "#FFF4E0", 0.7), root, (0, 0, 0), coll,
          bevel=0.03, seg=2)
    L.box(f"{name}_band", (0.9, 0.032, 0.14), L.mat("recipe_band", "#8B4A1F", 0.6), root, (0, -0.002, 0.32), coll)
    L.text(f"{name}_title", "REZEPT", 0.09, L.mat("recipe_title", "#FFF4E0", 0.6), root, (0, -0.022, 0.318),
           coll, extrude=0.003, font=L.font())
    rows = []
    m_t = L.mat("recipe_text", "#5E3014", 0.6)
    for i, t in enumerate(lines):
        row = L.empty(f"{name}_row{i}", root, (-0.36, -0.022, 0.13 - i * 0.2), coll)
        L.text(f"{name}_t{i}", t, 0.13, m_t, row, (0, 0, 0), coll, extrude=0.004, align="LEFT", font=L.font())
        rows.append(row)
    return P(root=root, rows=rows)


# ------------------------------------------------------------------ Code-Zeilen-Platte
def code_plate(coll, name, png, height=0.075, parent=None, loc=(0, 0, 0), backing=True):
    """Duenne leuchtende Platte mit der Textur einer echten Code-Zeile."""
    root = L.empty(name, parent, loc, coll)
    pl = L.tplane(f"{name}_tex", png, height=height, parent=root, loc=(0, -0.008, 0), coll=coll, emit=2.0,
                  origin="center")
    if backing:
        w = pl["w"] + 0.04
        L.box(f"{name}_back", (w, 0.012, height + 0.02), L.mat("plate_back", "#14303A", 0.5, emit=L.TURQ,
                                                                 strength=0.25), root, (0, 0, 0), coll)
        L.box(f"{name}_edge", (w + 0.01, 0.006, 0.006), L.mat("plate_edge", L.TURQ, 0.5, emit=L.TURQ, strength=5.0),
              root, (0, -0.004, -height / 2 - 0.01), coll)
    root["w"] = pl["w"]
    return root


def tower_slot(i, n, radius=0.42, rise=0.045, turn=0.42):  # noqa: ARG001
    """Position/Drehung der i-ten Platte im Spiral-Code-Turm (lokal zum Turm-Fuss)."""
    a = i * turn
    return Vector((radius * math.sin(a), -radius * math.cos(a), 0.05 + i * rise)), a


# ------------------------------------------------------------------ Teigschuessel
def dough_bowl(coll, name):
    root = L.empty(name, coll=coll)
    m_b = L.mat("bowl", "#6F86B8", 0.45)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=14, radius1=0.17, radius2=0.3, depth=0.26)
    bmesh.ops.translate(bm, vec=Vector((0, 0, 0.13)), verts=bm.verts)
    L.from_bm(f"{name}_wall", bm, m_b, root, (0, 0, 0), coll)
    L.cyl(f"{name}_foot", 0.17, 0.02, 14, m_b, root, (0, 0, 0.01), coll)
    L.torus(f"{name}_rim", 0.3, 0.018, 16, 5, L.mat("bowl_rim", "#8FA4D2", 0.45), root, (0, 0, 0.26), coll)
    dough = L.empty(f"{name}_dough", root, (0, 0, 0.16), coll)
    L.sphere(f"{name}_doughm", 0.25, 12, 7, (1, 1, 0.45), L.mat("dough", "#F3E3C3", 0.8), dough, (0, 0, 0), coll)
    return P(root=root, dough=dough)


# ------------------------------------------------------------------ Website-Ebene
def web_layer(coll, name, geruest_png, stil_png, height, parent=None, loc=(0, 0, 0), card=False):
    """Eine Website-Ebene: Platte (Bevel-Animation), Geruest-Textur vorne, Stil-Textur (bei Karten auf der
    Rueckseite -> Dominodrehung), Schatten darunter."""
    root = L.empty(name, parent, loc, coll)
    spin = L.empty(f"{name}_spin", root, (0, 0, 0), coll)
    w_px, h_px = L.img_size(stil_png)
    width = height * w_px / h_px
    slab = L.box(f"{name}_slab", (width * 0.98, 0.02, height * 0.96), L.mat("layer_slab", "#21456E", 0.5, emit=L.TURQ,
                                                                             strength=0.2), spin, (0, 0.012, 0), coll)
    bev = slab.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.0
    bev.segments = 4
    bev.limit_method = "ANGLE"
    ger = L.tplane(f"{name}_ger", geruest_png, height=height, parent=spin, loc=(0, -0.004, 0), coll=coll, emit=2.5)
    stil = L.empty(f"{name}_stilpiv", spin, (0, 0, height / 2), coll)   # Farbwelle: waechst von oben nach unten
    if card:
        stp = L.tplane(f"{name}_stil", stil_png, height=height, parent=spin, loc=(0, 0.026, 0), coll=coll, emit=1.0)
        stp.rotation_euler = (0, 0, math.pi)
        stil.scale = (1, 1, 1)
    else:
        stp = L.tplane(f"{name}_stil", stil_png, height=height, parent=stil, loc=(0, -0.006, 0), coll=coll, emit=1.0,
                       origin="top")
        stil.scale = (1, 1, 0)
    # leuchtender Geruest-Rahmen (sichtbar bis die Farbwelle kommt)
    frame = L.empty(f"{name}_frame", spin, (0, -0.012, 0), coll)
    m_f = L.mat("layer_frame", L.TURQ, 0.5, emit=L.TURQ, strength=5.0)
    t = 0.012
    for k_, (sx, sz, x, z) in enumerate([(width, t, 0, height / 2), (width, t, 0, -height / 2),
                                         (t, height, -width / 2, 0), (t, height, width / 2, 0)]):
        L.box(f"{name}_fr{k_}", (sx, 0.006, sz), m_f, frame, (x, 0, z), coll)
    shadow = L.box(f"{name}_shadow", (width * 0.96, 0.004, height * 0.9), L.mat("layer_shadow", "#0E0C1C", 0.9),
                   root, (0.02 * height, 0.05, -0.05 * height), coll)
    shadow.scale = (0, 0, 0)
    return P(root=root, spin=spin, slab=slab, bevel=bev, ger=ger, stil=stil, stil_plane=stp, shadow=shadow, frame=frame,
             w=width, h=height, card=card)


def color_wave(coll, name, width):
    """Warme Farbwelle: leuchtendes Band, das ueber die Ebenen nach unten laeuft."""
    root = L.empty(name, coll=coll)
    L.box(f"{name}_core", (width, 0.02, 0.06), L.mat("wave_core", "#FFE14D", 0.5, emit="#FFC24D", strength=6.0),
          root, (0, 0, 0), coll)
    L.box(f"{name}_glow", (width, 0.01, 0.22), L.mat("wave_glow", "#FF9F43", 0.5, emit="#FF9F43", strength=2.0,
                                                     alpha=0.55), root, (0, 0.01, 0.06), coll)
    return root


# ------------------------------------------------------------------ Gebaeck-Set
CRUST_C = "#C98A4B"


def pastry(coll, name, kind, parent=None, loc=(0, 0, 0), s=1.0):
    """Low-Poly-Gebaeck: broetchen, brezel, croissant, stollen, laugenstange, schnecke, brot."""
    root = L.empty(name, parent, loc, coll)
    root.scale = (s, s, s)
    crust = L.mat("p_crust", CRUST_C, 0.65)
    lauge = L.mat("p_lauge", "#7A3E17", 0.55)
    salt = L.mat("p_salt", "#FFFFFF", 0.6)
    if kind == "broetchen":
        L.sphere(f"{name}_m", 0.1, 10, 6, (1.2, 1.0, 0.72), crust, root, (0, 0, 0.06), coll)
        L.box(f"{name}_cut", (0.13, 0.016, 0.016), L.mat("p_cut", "#EBC48A", 0.7), root, (0, 0, 0.128), coll)
    elif kind == "brezel":
        for sx in (-1, 1):
            t = L.torus(f"{name}_loop{sx}", 0.055, 0.022, 10, 5, lauge, root, (sx * 0.05, 0, 0.09), coll, axis="Y")
            t.rotation_euler = (0, sx * 0.4, 0)
        o = L.torus(f"{name}_belly", 0.11, 0.024, 12, 5, lauge, root, (0, 0, 0.06), coll, axis="Y")
        o.scale = (1, 1, 0.55)
        for j in range(4):
            L.ico(f"{name}_salt{j}", 0.01, 0, (1, 1, 1), salt, root, (-0.07 + j * 0.045, -0.03, 0.12 - 0.02 * (j % 2)),
                  coll)
    elif kind == "croissant":
        for j in range(5):
            a = (j - 2) * 0.42
            r = 0.05 if j == 2 else 0.04 if j in (1, 3) else 0.028
            L.sphere(f"{name}_seg{j}", r, 8, 5, (1, 1.1, 1), L.mat("p_crois", "#E0A458", 0.6), root,
                     (0.11 * math.sin(a), 0.04 * (1 - math.cos(a)), 0.05), coll)
    elif kind == "stollen":
        L.box(f"{name}_m", (0.24, 0.1, 0.08), L.mat("p_stollen", "#D9A866", 0.7), root, (0, 0, 0.045), coll,
              bevel=0.03, seg=2)
        L.box(f"{name}_sugar", (0.22, 0.09, 0.03), salt, root, (0, 0, 0.085), coll, bevel=0.012)
    elif kind == "laugenstange":
        o = L.cyl(f"{name}_m", 0.03, 0.26, 8, lauge, root, (0, 0, 0.04), coll, axis="X")
        for j in range(3):
            L.ico(f"{name}_salt{j}", 0.01, 0, (1, 1, 1), salt, root, (-0.08 + j * 0.08, -0.02, 0.07), coll)
    elif kind == "schnecke":
        L.cyl(f"{name}_m", 0.1, 0.05, 12, L.mat("p_schnecke", "#E3A962", 0.65), root, (0, 0, 0.03), coll)
        L.torus(f"{name}_sw", 0.055, 0.012, 12, 4, L.mat("p_swirl", "#B5762E", 0.6), root, (0, 0, 0.058), coll)
        for j in range(3):
            a = j * 2.1
            L.ico(f"{name}_r{j}", 0.012, 0, (1, 1, 1), L.mat("p_raisin", "#4A2A3A", 0.6), root,
                  (0.075 * math.cos(a), 0.075 * math.sin(a), 0.06), coll)
    elif kind == "brot":
        L.sphere(f"{name}_m", 0.13, 10, 6, (1.4, 0.9, 0.75), L.mat("p_brot", "#A9652C", 0.65), root, (0, 0, 0.07), coll)
    return root


CARD_PASTRY = ["broetchen", "brezel", "croissant", "stollen", "brot", "schnecke", "laugenstange", "broetchen",
               "stollen", "brot", "croissant", "schnecke"]


# ------------------------------------------------------------------ Geraete
DEVICE = {  # Breite, Hoehe, Tiefe, Displayrand
    "handy": (0.42, 0.86, 0.04, 0.025),
    "tablet": (0.84, 1.15, 0.04, 0.045),
    "laptop": (1.44, 0.92, 0.035, 0.04),
}


def device(coll, name, kind, displays, scale=1.0):
    """Low-Poly-Handy/Tablet/Laptop. displays: Liste von PNG-Pfaden (umschaltbar ueber Scale)."""
    w, h, d, rim = DEVICE[kind]
    root = L.empty(name, coll=coll)
    root.scale = (scale,) * 3
    body = L.empty(f"{name}_body", root, (0, 0, 0), coll)
    m_body = L.mat(f"dev_{kind}", "#2A2747" if kind != "laptop" else "#9AA0B8", 0.4, metallic=0.3)
    screen_parent = body
    if kind == "laptop":
        L.box(f"{name}_base", (w * 1.04, 0.62, 0.04), m_body, body, (0, -0.31, -h / 2 - 0.02), coll, bevel=0.012)
        L.box(f"{name}_keys", (w * 0.9, 0.36, 0.006), L.mat("laptop_keys", "#2D2A44", 0.6), body,
              (0, -0.3, -h / 2 + 0.002), coll)
    L.box(f"{name}_shell", (w, d, h), m_body, body, (0, d / 2, 0), coll, bevel=0.03 if kind != "laptop" else 0.012,
          seg=2)
    L.box(f"{name}_bezel", (w - 0.01, 0.004, h - 0.01), L.mat("dev_bezel", "#0E0C1A", 0.4), body, (0, -0.002, 0), coll,
          bevel=0.02 if kind != "laptop" else 0.008, seg=2)
    if kind == "handy":
        L.box(f"{name}_notch", (0.09, 0.006, 0.018), L.mat("dev_notch", "#000000", 0.4), body, (0, -0.005, h / 2 - 0.03),
              coll, bevel=0.008)
    dw, dh = w - 2 * rim, h - 2 * rim - (0.02 if kind == "handy" else 0)
    scr = []
    for i, png in enumerate(displays):
        pw, ph = L.img_size(png)
        # Bild fuellt das Display in der Breite; Hoehe wird beschnitten (oben buendig)
        p = _display_plane(coll, f"{name}_disp{i}", png, dw, dh, body, (0, -0.006 - 0.0005 * i, -0.01 if kind == "handy" else 0))
        p.scale = (1, 1, 1) if i == 0 else (0, 0, 0)
        scr.append(p)
    return P(root=root, body=body, displays=scr, w=w, h=h, dw=dw, dh=dh, kind=kind)


def _display_plane(coll, name, png, dw, dh, parent, loc):
    """Ebene dw x dh; UV zeigt den oberen Ausschnitt des Bildes (Breite passt)."""
    pw, ph = L.img_size(png)
    vis = min(1.0, (dh / dw) * pw / ph)        # sichtbarer Anteil der Bildhoehe
    bm = bmesh.new()
    vs = [bm.verts.new((-dw / 2, 0, -dh / 2)), bm.verts.new((dw / 2, 0, -dh / 2)), bm.verts.new((dw / 2, 0, dh / 2)),
          bm.verts.new((-dw / 2, 0, dh / 2))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new("UVMap")
    for lp, co in zip(f.loops, [(0, 1 - vis), (1, 1 - vis), (1, 1), (0, 1)]):
        lp[uv].uv = co
    root = L.empty(f"{name}_piv", parent, loc, coll)
    L._mesh_obj(name, bm, L.img_mat(f"disp_{png}", png, 1.0, alpha=False), root, (0, 0, 0), coll)
    return root


# ------------------------------------------------------------------ 3D-Finger
def finger(coll, name):
    root = L.empty(name, coll=coll)
    skin = L.mat("skin", "#E7B08A", 0.62)
    L.cyl(f"{name}_m", 0.045, 0.32, 10, skin, root, (0, 0, 0.16), coll, origin="center")
    L.sphere(f"{name}_tip", 0.045, 10, 6, (1, 1, 1), skin, root, (0, 0, 0.0), coll)
    L.box(f"{name}_nail", (0.05, 0.01, 0.06), L.mat("nail", "#F4D2BE", 0.4), root, (0, -0.04, 0.04), coll, bevel=0.01)
    L.cyl(f"{name}_sleeve", 0.07, 0.2, 10, L.mat("shirt", "#7C8DB5", 0.66), root, (0, 0, 0.4), coll)
    return root


# ------------------------------------------------------------------ Gruener Haken
def check_badge(coll, name):
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_disc", 0.16, 0.04, 20, L.mat("check_disc", L.GREEN, 0.5, emit=L.GREEN, strength=1.5), root,
          (0, 0, 0), coll, axis="Y")
    L.poly_flat(f"{name}_mark", [(-0.08, 0.0), (-0.03, -0.05), (0.08, 0.06), (0.06, 0.08), (-0.03, -0.01),
                                 (-0.06, 0.02)], 0.02, L.mat("check_mark", "#FFFFFF", 0.4, emit="#FFFFFF", strength=2.0),
                root, (0, -0.03, 0), coll)
    return root


# ------------------------------------------------------------------ Mini-Laden mit Leuchtschild
def mini_shop(coll, name):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_house", (0.8, 0.6, 0.55), L.mat("shop_wall", "#F3E6CF", 0.7), root, (0, 0, 0.275), coll)
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in [(-0.46, -0.36, 0), (0.46, -0.36, 0), (0, -0.36, 0.3), (-0.46, 0.36, 0),
                                   (0.46, 0.36, 0), (0, 0.36, 0.3)]]
    for f in [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (0, 2, 5, 3)]:
        bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    L.from_bm(f"{name}_roof", bm, L.mat("shop_roof", "#8B4A1F", 0.6), root, (0, 0, 0.55), coll)
    L.box(f"{name}_door", (0.18, 0.02, 0.3), L.mat("shop_door", "#5E3014", 0.6), root, (0, -0.305, 0.15), coll)
    L.box(f"{name}_win", (0.22, 0.02, 0.16), L.mat("shop_win", "#FFE7BF", 0.4, emit="#FFD9A0", strength=2.5), root,
          (0.24, -0.305, 0.3), coll)
    L.box(f"{name}_awning", (0.84, 0.16, 0.04), L.mat("shop_awning", "#FF5A5F", 0.6), root, (0, -0.37, 0.48), coll)
    sign = L.empty(f"{name}_sign", root, (0, -0.33, 0.98), coll)
    L.box(f"{name}_signboard", (0.5, 0.04, 0.36), L.mat("sign_board", "#1D2A4A", 0.5), sign, (0, 0, 0), coll,
          bevel=0.03, seg=2)
    m_n = L.mat("neon", L.YELLOW, 0.4, emit=L.YELLOW, strength=6.0)
    for sx in (-1, 1):
        t = L.torus(f"{name}_neon{sx}", 0.06, 0.012, 12, 4, m_n, sign, (sx * 0.055, -0.03, 0.04), coll, axis="Y")
    o = L.torus(f"{name}_neonb", 0.12, 0.013, 14, 4, m_n, sign, (0, -0.03, -0.01), coll, axis="Y")
    o.scale = (1, 1, 0.55)
    L.cyl(f"{name}_pole", 0.015, 0.2, 6, L.mat("antenna", L.METAL, 0.5, metallic=0.4), root, (0, -0.33, 0.72), coll)
    return P(root=root, sign=sign)


# ------------------------------------------------------------------ Low-Poly-Kunde
def customer(coll, name, color, s=1.0):
    root = L.empty(name, coll=coll)
    root.scale = (s, s, s)
    body = L.empty(f"{name}_body", root, (0, 0, 0), coll)
    L.cyl(f"{name}_torso", 0.07, 0.2, 8, L.mat(f"cust_{color}", color, 0.6), body, (0, 0, 0.24), coll, r2=0.05)
    L.sphere(f"{name}_head", 0.06, 8, 6, (1, 1, 1), L.mat("skin", "#E7B08A", 0.62), body, (0, 0, 0.41), coll)
    legs = []
    for sx in (-1, 1):
        lp = L.empty(f"{name}_leg{sx}", body, (sx * 0.03, 0, 0.14), coll)
        L.box(f"{name}_legm{sx}", (0.035, 0.035, 0.14), L.mat("cust_leg", "#34497A", 0.6), lp, (0, 0, -0.07), coll)
        legs.append(lp)
    return P(root=root, body=body, legs=legs)


def customer_walk(T, cu, path_fn, f0, f1, f_arrive):
    """Laeuft entlang path_fn(t 0..1) von f0 bis f_arrive, Beine schwingen, Koerper wippt."""
    def t(f):
        return min(1.0, max(0.0, (f - f0) / max(1, f_arrive - f0)))
    T.set(cu.root, "location", lambda f: tuple(path_fn(t(f))), f0, f1)

    def yaw(f):
        a, b = Vector(path_fn(max(0, t(f) - 0.02))), Vector(path_fn(min(1, t(f) + 0.02)))
        d = b - a
        return (0, 0, math.atan2(-d.x, d.y) if d.length > 1e-5 else 0)
    T.set(cu.root, "rotation_euler", yaw, f0, f1)
    walking = lambda f: 1.0 if f < f_arrive else 0.0  # noqa: E731
    for k, lg in enumerate(cu.legs):
        T.set(lg, "rotation_euler", lambda f, k=k: (0.6 * walking(f) * math.sin(0.9 * (f - f0) + k * math.pi), 0, 0),
              f0, f1)
    T.set(cu.body, "location", lambda f: (0, 0, 0.02 * walking(f) * abs(math.sin(0.9 * (f - f0)))), f0, f1)


# =================================================================== Folge "Viel verkauft, kein Geld"
PAPER = "#F5F1E8"


def moth(coll, name):
    """Low-Poly-Motte: Spannweite 0,12 BU, 2 Fluegelpaare #F5F1E8 (Pivots fuer Fluegelschlag),
    Koerper #3A2A22, 2 Fuehler."""
    root = L.empty(name, coll=coll)
    m_w = L.mat("moth_wing", PAPER, 0.8)
    m_b = L.mat("moth_body", "#3A2A22", 0.7)
    L.sphere(f"{name}_body", 0.012, 8, 5, (1, 2.2, 1), m_b, root, (0, 0, 0), coll)
    L.sphere(f"{name}_head", 0.008, 6, 4, (1, 1, 1), m_b, root, (0, -0.026, 0.002), coll)
    wings = []
    for sx in (-1, 1):
        for k, (ln, wd, y) in enumerate([(0.06, 0.035, -0.006), (0.045, 0.028, 0.014)]):
            piv = L.empty(f"{name}_wpiv{sx}{k}", root, (sx * 0.006, y, 0.004), coll)
            L.poly_flat(f"{name}_wing{sx}{k}", [(0, -wd / 2), (sx * ln, -wd * 0.3), (sx * ln * 0.9, wd * 0.45),
                                                (0, wd / 2)], 0.002, m_w, piv, (0, 0, 0), coll, plane="XY")
            wings.append((piv, sx))
    for sx in (-1, 1):
        o = L.cyl(f"{name}_ant{sx}", 0.0015, 0.03, 4, m_b, root, (sx * 0.006, -0.04, 0.01), coll)
        o.rotation_euler = (math.radians(-60), sx * 0.4, 0)
    return P(root=root, wings=wings)


def moth_flap(T, mo, f0, f1, hz=12.0):
    """Fluegelschlag 12 Hz (Fluegel um die Laengsachse, +-60 Grad)."""
    for piv, sx in mo.wings:
        T.set(piv, "rotation_euler", lambda f, sx=sx: (0, sx * 1.05 * math.sin(2 * math.pi * hz * f / FPS), 0), f0, f1)


def invoice(coll, name, stamp=True):
    """Rechnungsblatt 0,21 x 0,30 x 0,003 BU, #F5F1E8, Textzeilen als graue Balken #8A8580.
    Oberes Drittel und Rest als zwei Teile (Pivot) -> kann einrollen/falten. Stempel 'OFFEN' separat."""
    root = L.empty(name, coll=coll)
    m_p = L.mat("invoice_paper", PAPER, 0.7)
    m_l = L.mat("invoice_line", "#8A8580", 0.7)
    lower = L.empty(f"{name}_lower", root, (0, 0, 0), coll)
    L.box(f"{name}_sheetlo", (0.21, 0.003, 0.18), m_p, lower, (0, 0, -0.06), coll)
    upper = L.empty(f"{name}_upper", root, (0, 0, 0.03), coll)       # Faltkante
    L.box(f"{name}_sheetup", (0.21, 0.003, 0.12), m_p, upper, (0, 0, 0.06), coll)
    L.box(f"{name}_head", (0.09, 0.002, 0.02), L.mat("invoice_head", "#19A99D", 0.6), upper, (-0.05, -0.002, 0.095),
          coll)
    for k in range(3):
        L.box(f"{name}_lu{k}", (0.16 - 0.03 * (k == 2), 0.002, 0.008), m_l, upper, (-0.005, -0.002, 0.06 - k * 0.02),
              coll)
    for k in range(6):
        L.box(f"{name}_ll{k}", (0.17 - 0.04 * (k % 3 == 2), 0.002, 0.008), m_l, lower,
              (-0.005, -0.002, -0.01 - k * 0.022), coll)
    L.box(f"{name}_sum", (0.06, 0.002, 0.012), L.mat("invoice_sum", "#3A2A22", 0.6), lower, (0.06, -0.002, -0.14),
          coll)
    st = None
    if stamp:
        st = L.empty(f"{name}_stamppiv", root, (0.02, -0.006, -0.03), coll)
        st.rotation_euler = (0, math.radians(-12), 0)
        m_s = L.mat("stamp_red", "#FF5A5F", 0.55, emit="#FF5A5F", strength=0.4)
        fr = L.empty(f"{name}_stamp", st, (0, 0, 0), coll)
        for k_, (w, h, x, z) in enumerate([(0.15, 0.008, 0, 0.03), (0.15, 0.008, 0, -0.03), (0.008, 0.068, -0.071, 0),
                                           (0.008, 0.068, 0.071, 0)]):
            L.box(f"{name}_stfr{k_}", (w, 0.002, h), m_s, fr, (x, 0, z), coll)
        L.text(f"{name}_sttxt", "OFFEN", 0.042, m_s, fr, (0, -0.001, -0.002), coll, extrude=0.001, font=L.font())
        st.scale = (0, 0, 0)
    return P(root=root, upper=upper, lower=lower, stamp=st)


def coin_small(coll, name, parent=None, loc=(0, 0, 0)):
    """Muenze r 0,04 BU, Hoehe 0,012 BU, #F2B45A mit Rand #B8702E, 12 Segmente (gemeinsames Mesh)."""
    if "small" not in _COIN_MESH:
        a = L.cyl("coin_s_proto", 0.04, 0.012, 12, L.mat("coin_s", "#F2B45A", 0.42, metallic=0.75, emit="#F2B45A",
                                                          strength=0.15), None, (0, 0, 0), coll)
        b = L.torus("coin_s_rim_proto", 0.037, 0.0055, 12, 4, L.mat("coin_s_rim", "#B8702E", 0.45, metallic=0.6),
                    None, (0, 0, 0), coll)
        _COIN_MESH["small"] = (a.data, b.data)
        bpy.data.objects.remove(a)
        bpy.data.objects.remove(b)
    root = L.empty(name, parent, loc, coll)
    for k, me in enumerate(_COIN_MESH["small"]):
        o = bpy.data.objects.new(f"{name}_{k}", me)
        L.link(o, coll)
        o.parent = root
    return root


def coin_stack(coll, name, n):
    """Muenzsaeule aus n kleinen Muenzen (Stagger-Animation in der Regie)."""
    root = L.empty(name, coll=coll)
    coins = [coin_small(coll, f"{name}_c{i}", root, (0, 0, 0.006 + i * 0.012)) for i in range(n)]
    return P(root=root, coins=coins)


def konto_glas(coll, name):
    """Kontoglas: Zylinder r 0,25 BU, Hoehe 0,6 BU (100 % = 1.500 EUR), getoent #BFFFF8, Roughness 0,1.
    Fuellstand per Parameter (fill-Pivot, Scale-Z = Fuellstand), Markierungslinie oben (rot/gruen umschaltbar),
    rote Luecke, tuerkise Randkante, gruener Bodenring."""
    root = L.empty(name, coll=coll)
    H, R = 0.6, 0.25
    m_g = L.mat("glass", "#BFFFF8", 0.1, alpha=0.22, spec=0.6)
    L.cyl(f"{name}_wall", R, H, 24, m_g, root, (0, 0, H / 2), coll, cap=False)
    L.cyl(f"{name}_base", R + 0.01, 0.02, 24, L.mat("glass_base", "#9FD9D3", 0.1, alpha=0.6), root, (0, 0, 0.01), coll)
    L.torus(f"{name}_lip", R, 0.008, 28, 4, L.mat("glass_lip", "#DFFFFB", 0.1, alpha=0.7), root, (0, 0, H), coll)
    fill = L.empty(f"{name}_fill", root, (0, 0, 0.02), coll)
    m_gold = L.mat("glass_gold", "#F2B45A", 0.4, metallic=0.7, emit="#F2B45A", strength=0.2)
    L.cyl(f"{name}_goldm", R - 0.025, 1.0, 20, m_gold, fill, (0, 0, 0.5), coll)
    ridge = L.mat("glass_gold_ridge", "#B8702E", 0.45, metallic=0.6)
    for k in range(10):
        L.torus(f"{name}_ridge{k}", R - 0.025, 0.004, 20, 3, ridge, fill, (0, 0, 0.1 * k + 0.05), coll)
    top = L.empty(f"{name}_filltop", root, (0, 0, 0.02), coll)        # Muenzen obenauf (folgt Fuellstand)
    for k in range(6):
        a = k * 1.1
        coin_small(coll, f"{name}_topcoin{k}", top, (0.12 * math.cos(a), 0.12 * math.sin(a), 0.006))
    fill.scale = (1, 1, 0.0001)
    m_red = L.unique_mat(L.mat("mark_red", "#FF5A5F", 0.5, emit="#FF5A5F", strength=0.0), f"{name}_markmat")
    mark = L.torus(f"{name}_mark", R + 0.004, 0.009, 28, 4, m_red, root, (0, 0, H - 0.01), coll)
    m_grn = L.mat("mark_green", "#3DDC84", 0.5, emit="#3DDC84", strength=2.0)
    mark_g = L.torus(f"{name}_markg", R + 0.006, 0.0095, 28, 4, m_grn, root, (0, 0, H - 0.01), coll)
    mark_g.scale = (0, 0, 0)
    gap = L.empty(f"{name}_gappiv", root, (0, 0, 0.02 + 0.6 * (H - 0.02)), coll)
    L.cyl(f"{name}_gap", R - 0.02, 1.0, 20, L.mat("gap_red", "#FF5A5F", 0.5, emit="#FF5A5F", strength=2.0, alpha=0.5),
          gap, (0, 0, 0.5), coll)
    gap.scale = (0, 0, 0)
    rim = L.empty(f"{name}_rimpiv", root, (0, 0, 0), coll)
    m_t = L.mat("glass_rim", L.TURQ, 0.4, emit=L.TURQ, strength=4.0)
    for z in (0.02, H):
        L.torus(f"{name}_rim{z}", R + 0.012, 0.007, 28, 4, m_t, rim, (0, 0, z), coll)
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        L.box(f"{name}_rimv{k}", (0.008, 0.008, H), m_t, rim, ((R + 0.012) * math.cos(a), (R + 0.012) * math.sin(a), H / 2),
              coll)
    rim.scale = (0, 0, 0)
    ring = L.torus(f"{name}_greenring", R + 0.07, 0.016, 32, 4, L.mat("ring_green", "#3DDC84", 0.5, emit="#3DDC84",
                                                                       strength=4.0), root, (0, 0, 0.01), coll)
    ring.scale = (0, 0, 0)
    return P(root=root, fill=fill, top=top, mark=mark, mark_mat=m_red, mark_g=mark_g, gap=gap, rim=rim, ring=ring,
             H=H, R=R)


def glas_level(T, g, fn, f0, f1):
    """Fuellstand (Anteil von 100 %, darf > 1 sein) als Funktion der Zeit."""
    span = g.H - 0.02
    T.set(g.fill, "scale", lambda f: (1, 1, max(0.0001, fn(f) * span)), f0, f1)
    T.set(g.top, "location", lambda f: (0, 0, 0.02 + max(0.0, fn(f)) * span), f0, f1)
    T.set(g.top, "scale", lambda f: (1, 1, 1) if fn(f) > 0.01 else (0, 0, 0), f0, f1)


def calendar_sheet(coll, name):
    """Kalenderblatt 0,08 x 0,10 BU, #F5F1E8, oberer Rand #FF5A5F."""
    root = L.empty(name, coll=coll)
    L.box(f"{name}_p", (0.08, 0.002, 0.1), L.mat("cal_paper", PAPER, 0.7), root, (0, 0, 0), coll)
    L.box(f"{name}_top", (0.08, 0.003, 0.02), L.mat("cal_red", "#FF5A5F", 0.6), root, (0, -0.001, 0.04), coll)
    for k in range(3):
        L.box(f"{name}_d{k}", (0.05, 0.002, 0.006), L.mat("invoice_line", "#8A8580", 0.7), root,
              (0, -0.002, 0.01 - k * 0.018), coll)
    return root


def stopwatch(coll, name):
    """Stoppuhr: Durchmesser 0,15 BU, Gehaeuse #8FA3B0, Zifferblatt #F5F1E8, Zeiger #FF5A5F (Pivot)."""
    root = L.empty(name, coll=coll)
    m_c = L.mat("sw_case", "#8FA3B0", 0.4, metallic=0.4)
    L.cyl(f"{name}_case", 0.075, 0.03, 20, m_c, root, (0, 0, 0), coll, axis="Y")
    L.cyl(f"{name}_face", 0.064, 0.032, 20, L.mat("sw_face", PAPER, 0.6), root, (0, -0.002, 0), coll, axis="Y")
    L.cyl(f"{name}_crown", 0.012, 0.025, 8, m_c, root, (0, 0, 0.088), coll)
    L.cyl(f"{name}_btn", 0.018, 0.012, 8, m_c, root, (0, 0, 0.104), coll)
    for i in range(12):
        a = 2 * math.pi * i / 12
        L.box(f"{name}_tick{i}", (0.005, 0.004, 0.012), L.mat("ink", L.NAVY2, 0.6), root,
              (0.052 * math.sin(a), -0.019, 0.052 * math.cos(a)), coll).rotation_euler = (0, a, 0)
    hand = L.empty(f"{name}_hand", root, (0, -0.021, 0), coll)
    L.box(f"{name}_handm", (0.006, 0.004, 0.055), L.mat("sw_hand", "#FF5A5F", 0.5, emit="#FF5A5F", strength=0.5),
          hand, (0, 0, 0.024), coll)
    L.cyl(f"{name}_hub", 0.008, 0.01, 8, L.mat("sw_hand", "#FF5A5F", 0.5), root, (0, -0.022, 0), coll, axis="Y")
    return P(root=root, hand=hand)


def envelope_mail(coll, name):
    """Briefumschlag 0,30 x 0,20 BU, #F5F1E8, Kante #2EE6D6, Klappe animierbar (Pivot an der Oberkante)."""
    root = L.empty(name, coll=coll)
    m_p = L.mat("env_paper", PAPER, 0.62)
    m_e = L.mat("env_edge", L.TURQ, 0.5, emit=L.TURQ, strength=3.0)
    L.box(f"{name}_body", (0.3, 0.012, 0.2), m_p, root, (0, 0, 0), coll, bevel=0.004)
    for k_, (w, h, x, z) in enumerate([(0.31, 0.006, 0, 0.1), (0.31, 0.006, 0, -0.1), (0.006, 0.2, -0.152, 0),
                                       (0.006, 0.2, 0.152, 0)]):
        L.box(f"{name}_edge{k_}", (w, 0.014, h), m_e, root, (x, 0, z), coll)
    L.poly_flat(f"{name}_fold", [(-0.15, -0.1), (0.0, 0.01), (0.15, -0.1)], 0.003, L.mat("env_in", "#E6DFD0", 0.65),
                root, (0, -0.008, 0), coll)
    flap = L.empty(f"{name}_flappiv", root, (0, -0.008, 0.1), coll)
    L.poly_flat(f"{name}_flap", [(-0.15, 0.0), (0.0, -0.12), (0.15, 0.0)], 0.004, m_p, flap, (0, 0, 0), coll)
    L.poly_flat(f"{name}_flapedge", [(-0.15, 0.0), (0.0, -0.12), (0.01, -0.11), (-0.14, 0.0)], 0.005, m_e, flap,
                (0, -0.001, 0), coll)
    return P(root=root, flap=flap)


def muehlrad_zettel(coll, name):
    """Muehlrad-Zettel 0,10 x 0,12 BU, #F5F1E8, Muehlrad-Symbol #B8702E, Haken #3DDC84 einblendbar."""
    root = L.empty(name, coll=coll)
    L.box(f"{name}_p", (0.1, 0.003, 0.12), L.mat("note_paper", PAPER, 0.7), root, (0, 0, 0), coll)
    m_w = L.mat("wheel_brown", "#B8702E", 0.6)
    L.torus(f"{name}_wheel", 0.03, 0.005, 14, 4, m_w, root, (0, -0.003, 0.012), coll, axis="Y")
    for k in range(4):
        o = L.box(f"{name}_spoke{k}", (0.004, 0.003, 0.06), m_w, root, (0, -0.003, 0.012), coll)
        o.rotation_euler = (0, k * math.pi / 4, 0)
    for k in range(8):
        a = k * math.pi / 4
        L.box(f"{name}_pad{k}", (0.012, 0.003, 0.008), m_w, root, (0.036 * math.sin(a), -0.003, 0.012 + 0.036 * math.cos(a)),
              coll).rotation_euler = (0, a, 0)
    L.box(f"{name}_line", (0.06, 0.003, 0.006), L.mat("invoice_line", "#8A8580", 0.7), root, (0, -0.003, -0.04), coll)
    chk = L.empty(f"{name}_checkpiv", root, (0.025, -0.006, -0.03), coll)
    L.poly_flat(f"{name}_check", [(-0.03, 0.0), (-0.012, -0.02), (0.03, 0.025), (0.024, 0.031), (-0.012, -0.006),
                                  (-0.024, 0.006)], 0.006, L.mat("check_green", "#3DDC84", 0.5, emit="#3DDC84",
                                                                  strength=2.0), chk, (0, 0, 0), coll)
    chk.scale = (0, 0, 0)
    return P(root=root, check=chk)


def vitrine(coll, name):
    """Glasvitrine auf der Theke, nur noch 20 % gefuellt: 2 Broetchen, 1 Brezel, halber Hefezopf, Kruemel #B8702E."""
    root = L.empty(name, coll=coll)
    m_g = L.mat("vitrine_glass", "#D8F4F0", 0.1, alpha=0.18, spec=0.6)
    m_f = L.mat("wood_dark", L.WOOD_DARK, 0.65)
    W, D, Hh = 0.62, 0.36, 0.3
    L.box(f"{name}_floor", (W, D, 0.03), L.mat("vitrine_floor", "#E9DFCC", 0.6), root, (0, 0, 0.015), coll)
    L.box(f"{name}_glass", (W, D, Hh), m_g, root, (0, 0, 0.03 + Hh / 2), coll)
    for x in (-W / 2, W / 2):
        for y in (-D / 2, D / 2):
            L.box(f"{name}_post{x}{y}", (0.018, 0.018, Hh), m_f, root, (x, y, 0.03 + Hh / 2), coll)
    L.box(f"{name}_top", (W + 0.03, D + 0.03, 0.02), m_f, root, (0, 0, 0.04 + Hh), coll)
    pastry(coll, f"{name}_r1", "broetchen", root, (-0.2, 0.05, 0.03), 0.8)
    pastry(coll, f"{name}_r2", "broetchen", root, (-0.06, 0.07, 0.03), 0.8)
    pastry(coll, f"{name}_br", "brezel", root, (0.1, 0.04, 0.03), 0.75)
    zopf = L.empty(f"{name}_zopf", root, (0.2, 0.05, 0.03), coll)
    for k in range(3):
        L.sphere(f"{name}_zopf{k}", 0.045, 8, 5, (1.2, 0.8, 0.7), L.mat("p_zopf", "#D9A866", 0.6), zopf,
                 (k * 0.05 - 0.05, 0.012 * (-1) ** k, 0.035), coll)
    m_c = L.mat("crumb", "#B8702E", 0.7)
    rr = random.Random(41)
    for k in range(9):
        L.ico(f"{name}_crumb{k}", 0.007, 0, (1, 1, 0.7), m_c, root, (rr.uniform(-0.27, 0.27), rr.uniform(-0.14, 0.14), 0.035),
              coll)
    return P(root=root, H=Hh + 0.05, W=W, D=D)


# =================================================================== Folge "Byte telefoniert"
def rechnung_lang(coll, name, length=2.2, width=0.22):
    """Meterlange Rechnung: Papierstreifen (Scale-X = abgerollter Anteil) + Rolle, die mitwandert.
    Am Anfang rot umkreist '24 €/Sack'. Pivot am Streifenanfang, Streifen laeuft in +X."""
    root = L.empty(name, coll=coll)
    strip = L.empty(f"{name}_strip", root, (0, 0, 0), coll)
    m_p = L.mat("invoice_paper", PAPER, 0.7)
    L.box(f"{name}_paper", (length, width, 0.004), m_p, strip, (length / 2, 0, 0), coll)
    m_l = L.mat("invoice_line", "#8A8580", 0.7)
    for k in range(int(length / 0.07)):
        x = 0.05 + k * 0.07
        L.box(f"{name}_ln{k}", (0.045, width * (0.7 if k % 3 else 0.5), 0.002), m_l, strip, (x, 0, 0.003), coll)
    mark = L.empty(f"{name}_mark", strip, (0.16, 0, 0.006), coll)
    m_r = L.mat("mark_red", "#FF5A5F", 0.5, emit="#FF5A5F", strength=1.5)
    L.torus(f"{name}_circle", 0.1, 0.008, 24, 4, m_r, mark, (0, 0, 0), coll)
    mark.scale = (1.5, 0.95, 1)
    t = L.text(f"{name}_price", "24 €/Sack", 0.055, L.mat("price_red", "#C0353A", 0.6), mark, (0, 0, 0.004), coll,
               extrude=0.002, rot=(0, 0, 0), font=L.font())
    roll = L.empty(f"{name}_roll", root, (0, 0, 0.03), coll)
    L.cyl(f"{name}_rollm", 0.035, width, 14, m_p, roll, (0, 0, 0), coll, axis="Y")
    L.cyl(f"{name}_rollcore", 0.012, width + 0.01, 8, L.mat("roll_core", "#C9B79A", 0.7), roll, (0, 0, 0), coll, axis="Y")
    return P(root=root, strip=strip, roll=roll, mark=mark, length=length)


def rechnung_abrollen(T, r, fn, f0, f1):
    """fn(f) -> 0..1 abgerollter Anteil (0 = eingerollt). Rolle wandert ans Streifenende und wird duenner."""
    T.set(r.strip, "scale", lambda f: (max(0.001, fn(f)), 1, 1), f0, f1)
    T.set(r.roll, "location", lambda f: (r.length * fn(f), 0, 0.03 + 0.02 * (1 - fn(f))), f0, f1)
    T.set(r.roll, "scale", lambda f: (1.6 - 0.9 * fn(f), 1, 1.6 - 0.9 * fn(f)), f0, f1)
    T.set(r.mark, "scale", lambda f: ((1.5, 0.95, 1) if fn(f) > 0.12 else (0, 0, 0)), f0, f1)


def telefonhoerer(coll, name):
    """Altmodischer Telefonhoerer (Griff + Hoer-/Sprechmuschel), schwarz-rot."""
    root = L.empty(name, coll=coll)
    m = L.mat("handset", "#2A2238", 0.4)
    m2 = L.mat("handset_red", "#C0353A", 0.45)
    L.box(f"{name}_grip", (0.05, 0.04, 0.24), m, root, (0, 0, 0), coll, bevel=0.015)
    for z, nm in ((0.13, "ear"), (-0.13, "mouth")):
        cup = L.cyl(f"{name}_{nm}", 0.045, 0.05, 12, m2, root, (0, -0.025, z), coll, axis="Y")
    return root


def ringelkabel(T, coll, name, a_fn, b_fn, f0, f1, n=18, wrap_fn=None):
    """Ringelkabel als Kette kleiner Ringe zwischen zwei bewegten Punkten. wrap_fn(f) -> (center, r, amount)
    wickelt das Kabel spiralfoermig um einen Punkt (verheddert)."""
    m = L.mat("cable", "#2A2238", 0.5)
    rings = []
    for k in range(n):
        o = L.torus(f"{name}_r{k}", 0.022, 0.006, 8, 3, m, None, (0, 0, 0), coll, axis="X")

        def loc(f, k=k):
            t = (k + 0.5) / n
            p = Vector(a_fn(f)).lerp(Vector(b_fn(f)), t)
            p.z -= 0.18 * math.sin(math.pi * t)            # durchhaengen
            if wrap_fn:
                c, rr, am = wrap_fn(f)
                if am > 0:
                    ang = t * 6 * math.pi + f * 0.05
                    q = Vector(c) + Vector((rr * math.cos(ang), rr * math.sin(ang), 0.25 * (t - 0.5)))
                    p = p.lerp(q, am)
            return tuple(p)
        T.set(o, "location", loc, f0, f1)
        rings.append(o)
    return rings


def muehlen_kiste(coll, name, label):
    """Holzkiste mit Aufschrift (z. B. 'MÜHLE A', 'STAMMLIEFERANT'), Glocke oben (klingelt), Pivot unten
    (wackeln), Stempelflaeche vorne."""
    root = L.empty(name, coll=coll)
    body = L.empty(f"{name}_body", root, (0, 0, 0), coll)
    m_w = L.mat("crate_wood", "#B98A55", 0.7)
    m_d = L.mat("crate_dark", "#7A5536", 0.7)
    L.box(f"{name}_box", (0.6, 0.45, 0.42), m_w, body, (0, 0, 0.21), coll, bevel=0.015)
    for z in (0.08, 0.21, 0.34):
        L.box(f"{name}_plank{z}", (0.62, 0.47, 0.012), m_d, body, (0, 0, z), coll)
    for x in (-0.3, 0.3):
        L.box(f"{name}_post{x}", (0.03, 0.47, 0.42), m_d, body, (x, 0, 0.21), coll)
    plate = L.box(f"{name}_plate", (0.5, 0.01, 0.13), L.mat("crate_plate", "#F5F1E8", 0.6), body, (0, -0.232, 0.25), coll)
    L.text(f"{name}_label", label, 0.085 if len(label) < 9 else 0.044, L.mat("crate_ink", "#3A2A22", 0.6), body,
           (0, -0.24, 0.235), coll, extrude=0.003, font=L.font())
    bell = L.empty(f"{name}_bell", body, (0.18, 0, 0.42), coll)
    L.sphere(f"{name}_bellm", 0.05, 10, 6, (1, 1, 0.8), L.mat("bell_brass", L.GOLD, 0.35, metallic=0.7), bell,
             (0, 0, 0.03), coll)
    L.cyl(f"{name}_bellknob", 0.012, 0.03, 6, L.mat("bell_brass", L.GOLD, 0.35, metallic=0.7), bell, (0, 0, 0.075), coll)
    stamp_mark = L.empty(f"{name}_stampmark", body, (-0.02, -0.235, 0.1), coll)
    L.text(f"{name}_stamptxt", "STAMMLIEFERANT", 0.04, L.mat("stamp_red", "#FF5A5F", 0.55, emit="#FF5A5F",
                                                               strength=0.4), stamp_mark, (0, -0.004, 0), coll,
           extrude=0.002, font=L.font())
    stamp_mark.rotation_euler = (0, math.radians(-8), 0)
    stamp_mark.scale = (0, 0, 0)
    return P(root=root, body=body, bell=bell, stamp_mark=stamp_mark)


def kiste_wackeln(T, k, f0, f1, amount=1.0, seed=0):
    nz = Noise(300 + seed, 3, 3.0)
    T.add(k.body, "rotation_euler", lambda f: (0.05 * amount * nz(f / FPS), 0.07 * amount * nz(f / FPS + 3), 0), f0, f1)
    T.add(k.bell, "rotation_euler", lambda f: (0.35 * amount * math.sin(f * 2.4), 0, 0), f0, f1)


def angebotszettel(coll, name, price, green=False):
    """Angebotszettel mit grossem Preis; green=True leuchtet gruen (bestes Angebot)."""
    root = L.empty(name, coll=coll)
    col = "#3DDC84" if green else "#F5F1E8"
    m = L.unique_mat(L.mat(f"offer_{price}", col, 0.6, emit=col, strength=0.8 if green else 0.0), f"{name}_mat")
    L.box(f"{name}_p", (0.32, 0.01, 0.22), m, root, (0, 0, 0), coll, bevel=0.01)
    L.box(f"{name}_pin", (0.04, 0.012, 0.04), L.mat("pin_red", "#FF5A5F", 0.5), root, (0, -0.002, 0.09), coll)
    L.text(f"{name}_txt", price, 0.12, L.mat("offer_ink", "#3A2A22", 0.6), root, (0, -0.008, -0.02), coll,
           extrude=0.004, font=L.font())
    return P(root=root, mat=m)


def stempel(coll, name, text="STAMMLIEFERANT"):
    """Holzstempel mit Griff; Unterseite rot."""
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_knob", 0.05, 0.06, 12, L.mat("stamp_knob", "#7A5536", 0.6), root, (0, 0, 0.2), coll)
    L.cyl(f"{name}_neck", 0.02, 0.1, 8, L.mat("stamp_knob", "#7A5536", 0.6), root, (0, 0, 0.12), coll)
    L.box(f"{name}_base", (0.34, 0.1, 0.05), L.mat("crate_wood", "#B98A55", 0.7), root, (0, 0, 0.05), coll, bevel=0.01)
    L.box(f"{name}_rubber", (0.32, 0.09, 0.012), L.mat("stamp_red", "#FF5A5F", 0.55), root, (0, 0, 0.02), coll)
    t = L.text(f"{name}_txt", text, 0.035, L.mat("stamp_ink", "#FFFFFF", 0.5), root, (0, -0.052, 0.05), coll,
               extrude=0.001, font=L.font())
    return root


def sonnenbrille(coll, name):
    root = L.empty(name, coll=coll)
    m = L.mat("shades", "#141228", 0.2, metallic=0.3)
    for sx in (-1, 1):
        L.box(f"{name}_lens{sx}", (0.1, 0.012, 0.055), m, root, (sx * 0.065, 0, 0), coll, bevel=0.015)
    L.box(f"{name}_bridge", (0.04, 0.01, 0.012), m, root, (0, 0, 0.015), coll)
    L.box(f"{name}_glint", (0.03, 0.002, 0.008), L.mat("glint", "#FFFFFF", 0.4, emit="#FFFFFF", strength=2.0), root,
          (0.08, -0.008, 0.012), coll)
    return root


def preisschild(coll, name, old="24 €", new="19,70 €"):
    """Grosses Preisschild: alter Preis + roter Durchstrich (Scale-X), neuer Preis darunter (Pop)."""
    root = L.empty(name, coll=coll)
    flip = L.empty(f"{name}_flip", root, (0, 0, 0), coll)
    L.box(f"{name}_board", (0.95, 0.04, 0.75), L.mat("sign_board", "#1D2A4A", 0.5), flip, (0, 0, 0), coll, bevel=0.04)
    L.box(f"{name}_edge", (0.99, 0.03, 0.79), L.mat("plate_edge", L.TURQ, 0.5, emit=L.TURQ, strength=5.0), flip,
          (0, 0.01, 0), coll, bevel=0.04)
    L.text(f"{name}_old", old, 0.2, L.mat("old_price", "#F5F1E8", 0.5, emit="#F5F1E8", strength=0.5), flip,
           (0, -0.03, 0.17), coll, extrude=0.01, font=L.font())
    strike = L.empty(f"{name}_strikepiv", flip, (-0.27, -0.05, 0.19), coll)
    L.box(f"{name}_strike", (0.54, 0.01, 0.035), L.mat("mark_red", "#FF5A5F", 0.5, emit="#FF5A5F", strength=1.5),
          strike, (0.27, 0, 0), coll)
    strike.rotation_euler = (0, math.radians(-8), 0)
    strike.scale = (0, 1, 1)
    newp = L.empty(f"{name}_newpiv", flip, (0, -0.04, -0.15), coll)
    L.text(f"{name}_new", new, 0.24, L.mat("new_price", "#3DDC84", 0.5, emit="#3DDC84", strength=2.0), newp,
           (0, 0, 0), coll, extrude=0.012, font=L.font())
    newp.scale = (0, 0, 0)
    return P(root=root, flip=flip, strike=strike, new=newp)


# =================================================================== Folge "Der teuerste Rabatt"
def neonschild(coll, name, text, color="#FF3B6B", width=1.3, height=0.42, size=0.2):
    """Neonschild: dunkle Platte, leuchtende Schrift und Rahmen. Flackern/Ausfall ueber die Material-Farbe
    (neon_flacker). Workbench zeigt die Objektfarbe, daher wird diffuse_color animiert."""
    root = L.empty(name, coll=coll)
    L.box(f"{name}_board", (width, 0.04, height), L.mat("neon_board", "#141228", 0.4), root, (0, 0, 0), coll, bevel=0.03)
    m = L.unique_mat(L.mat(f"neon_{color}", color, 0.4, emit=color, strength=6.0), f"{name}_neon")
    for k_, (w, h, x, z) in enumerate([(width - 0.06, 0.018, 0, height / 2 - 0.04), (width - 0.06, 0.018, 0, -height / 2 + 0.04),
                                       (0.018, height - 0.08, -width / 2 + 0.03, 0), (0.018, height - 0.08, width / 2 - 0.03, 0)]):
        L.box(f"{name}_tube{k_}", (w, 0.02, h), m, root, (x, -0.03, z), coll)
    L.text(f"{name}_txt", text, size, m, root, (0, -0.035, -0.01), coll, extrude=0.012, font=L.font())
    return P(root=root, mat=m, color=color)


def neon_flacker(T, ns, f0, f1, seed=0, aus=None, strength=1.0):
    """Flackern: kurze dunkle Aussetzer (Seed); aus=(a, b) -> komplett aus."""
    r = random.Random(seed)
    drops = set()
    f = f0
    while f < f1:
        f += r.randint(9, 26)
        for k in range(r.randint(1, 3)):
            drops.add(f + k)
    on = L.srgb(ns.color)
    off = tuple(x * 0.18 for x in on[:3]) + (1.0,)

    def col(f):
        dark = (f in drops and r.random() < 2) or (aus and aus[0] <= f < aus[1])
        c = off if dark else on
        if strength < 1 and f in drops:
            c = tuple(a_ * 0.6 + b_ * 0.4 for a_, b_ in zip(on, off))
        return c
    T.set(ns.mat, "diffuse_color", col, f0, f1)
    T.set(L.bsdf(ns.mat).inputs["Emission Strength"], "default_value",
          lambda f: 0.6 if (f in drops or (aus and aus[0] <= f < aus[1])) else 6.0, f0, f1)


def konfetti_kanone(coll, name):
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_foot", 0.12, 0.05, 12, L.mat("cannon_dark", "#2A2238", 0.5), root, (0, 0, 0.025), coll)
    barrel = L.empty(f"{name}_barrel", root, (0, 0, 0.06), coll)
    barrel.rotation_euler = (math.radians(-35), 0, 0)
    L.cyl(f"{name}_tube", 0.07, 0.36, 12, L.mat("cannon_gold", "#F2B45A", 0.35, metallic=0.7), barrel, (0, 0, 0.18), coll)
    L.torus(f"{name}_ring", 0.075, 0.012, 12, 4, L.mat("cannon_red", "#FF3B6B", 0.5), barrel, (0, 0, 0.34), coll)
    return P(root=root, barrel=barrel)


def alarmlicht(coll, name, parent=None, loc=(0, 0, 0)):
    """Rundumleuchte (Kuppel + drehender Reflektor). Farbe rot/gruen ueber zwei Kuppeln (Scale-Umschaltung)."""
    root = L.empty(name, parent, loc, coll)
    L.cyl(f"{name}_base", 0.04, 0.02, 10, L.mat("alarm_base", "#2A2238", 0.5), root, (0, 0, 0), coll)
    red = L.sphere(f"{name}_red", 0.04, 10, 6, (1, 1, 1.1), L.mat("alarm_red", "#FF3B3B", 0.3, emit="#FF3B3B", strength=5.0),
                   root, (0, 0, 0.035), coll)
    green = L.sphere(f"{name}_green", 0.04, 10, 6, (1, 1, 1.1), L.mat("alarm_green", "#3DDC84", 0.3, emit="#3DDC84",
                                                                       strength=5.0), root, (0, 0, 0.035), coll)
    green.scale = (0, 0, 0)
    spin = L.empty(f"{name}_spin", root, (0, 0, 0.035), coll)
    L.box(f"{name}_beam", (0.012, 0.11, 0.025), L.mat("alarm_beam", "#FFFFFF", 0.3, emit="#FFFFFF", strength=4.0), spin,
          (0, 0.03, 0), coll)
    return P(root=root, red=red, green=green, spin=spin)


def brezel_schild(coll, name, preis="1,20 €", parent=None, loc=(0, 0, 0), s=1.0):
    """Brezel (Gebaeck-Set) mit kleinem Preisschild am Faden."""
    root = L.empty(name, parent, loc, coll)
    root.scale = (s, s, s)
    pastry(coll, f"{name}_b", "brezel", root, (0, 0, 0), 1.0)
    tag = L.empty(f"{name}_tag", root, (0.12, -0.06, 0.12), coll)
    L.box(f"{name}_tagp", (0.13, 0.006, 0.07), L.mat("tag_gold", "#F2B45A", 0.45, metallic=0.4), tag, (0, 0, 0), coll,
          bevel=0.008)
    L.text(f"{name}_tagt", preis, 0.04, L.mat("tag_ink", "#3A2A22", 0.6), tag, (0, -0.005, -0.004), coll, extrude=0.002,
           font=L.font())
    return P(root=root, tag=tag)


def schere(coll, name):
    root = L.empty(name, coll=coll)
    m = L.mat("scissor_metal", L.METAL, 0.3, metallic=0.8)
    m2 = L.mat("scissor_grip", "#FF3B6B", 0.5)
    blades = []
    for sx in (-1, 1):
        piv = L.empty(f"{name}_piv{sx}", root, (0, 0, 0), coll)
        L.box(f"{name}_blade{sx}", (0.03, 0.01, 0.28), m, piv, (0, 0, 0.14), coll, bevel=0.008)
        L.torus(f"{name}_grip{sx}", 0.045, 0.012, 12, 4, m2, piv, (sx * 0.03, 0, -0.07), coll, axis="Y")
        piv.rotation_euler = (0, sx * 0.25, 0)
        blades.append((piv, sx))
    return P(root=root, blades=blades)


def muenze_minus(coll, name):
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_m", 0.07, 0.02, 14, L.mat("coin_red", "#E0303A", 0.4, emit="#E0303A", strength=1.0), root, (0, 0, 0),
          coll, axis="Y")
    L.box(f"{name}_minus", (0.07, 0.024, 0.016), L.mat("coin_minus_w", "#FFFFFF", 0.4, emit="#FFFFFF", strength=1.0), root,
          (0, -0.004, 0), coll)
    return root


def brezel_tuete(coll, name):
    root = L.empty(name, coll=coll)
    L.box(f"{name}_bag", (0.22, 0.14, 0.3), L.mat("paperbag", "#D7B98C", 0.8), root, (0, 0, 0.15), coll, bevel=0.01)
    L.box(f"{name}_fold", (0.22, 0.145, 0.03), L.mat("paperbag_d", "#B8955F", 0.8), root, (0, 0, 0.29), coll)
    pastry(coll, f"{name}_logo", "brezel", root, (0, -0.075, 0.07), 0.45)
    return root


def muelltonne_reste(coll, name):
    """Muelltonne 'RESTE' mit Deckel-Pivot; dazu eine Kasse an derselben Stelle (Verwandlung per Scale-Wechsel)."""
    root = L.empty(name, coll=coll)
    bin_ = L.empty(f"{name}_bin", root, (0, 0, 0), coll)
    m = L.mat("bin_grey", "#5C6378", 0.5, metallic=0.2)
    L.cyl(f"{name}_body", 0.3, 0.75, 16, m, bin_, (0, 0, 0.375), coll, r2=0.34)
    for z in (0.2, 0.5):
        L.torus(f"{name}_rib{z}", 0.32 + 0.03 * z, 0.012, 16, 4, L.mat("bin_rib", "#454B5E", 0.5), bin_, (0, 0, z), coll)
    L.box(f"{name}_plate", (0.36, 0.02, 0.14), L.mat("bin_plate", "#F5F1E8", 0.6), bin_, (0, -0.33, 0.45), coll)
    L.text(f"{name}_txt", "RESTE", 0.1, L.mat("stamp_red", "#FF5A5F", 0.55, emit="#FF5A5F", strength=0.4), bin_,
           (0, -0.345, 0.44), coll, extrude=0.004, font=L.font())
    lid = L.empty(f"{name}_lid", bin_, (0, 0.34, 0.76), coll)
    L.cyl(f"{name}_lidm", 0.36, 0.05, 16, L.mat("bin_lid", "#454B5E", 0.5), lid, (0, -0.34, 0.02), coll)
    L.box(f"{name}_handle", (0.16, 0.04, 0.04), L.mat("bin_lid", "#454B5E", 0.5), lid, (0, -0.34, 0.06), coll)
    kasse = L.empty(f"{name}_kasse", root, (0, 0, 0), coll)
    mk = L.mat("register", "#46496E", 0.5)
    L.box(f"{name}_kbase", (0.7, 0.55, 0.3), mk, kasse, (0, 0, 0.15), coll, bevel=0.03)
    drawer = L.empty(f"{name}_kdrawer", kasse, (0, 0, 0.0), coll)
    L.box(f"{name}_kdrawerm", (0.62, 0.5, 0.12), L.mat("drawer", "#5A5E86", 0.5), drawer, (0, -0.04, 0.08), coll, bevel=0.01)
    L.box(f"{name}_kbody", (0.6, 0.35, 0.3), mk, kasse, (0, 0.08, 0.45), coll, bevel=0.03)
    L.box(f"{name}_kdisp", (0.4, 0.04, 0.14), L.mat("reg_glass", "#123", 0.4, emit=L.TURQ, strength=1.2), kasse,
          (0, -0.1, 0.55), coll)
    L.text(f"{name}_ktxt", "+24 €", 0.08, L.mat("ktxt", "#3DDC84", 0.4, emit="#3DDC84", strength=3.0), kasse,
           (0, -0.125, 0.545), coll, extrude=0.003, font=L.font())
    kasse.scale = (0, 0, 0)
    return P(root=root, bin=bin_, lid=lid, kasse=kasse, drawer=drawer)


def neon_plakat(coll, name, zeilen, color="#3DDC84", size=0.16):
    """Neon-Plakat: jeder Buchstabe ein eigenes Objekt (baut sich Stueck fuer Stueck auf)."""
    root = L.empty(name, coll=coll)
    m = L.mat(f"plakat_{color}", color, 0.4, emit=color, strength=6.0)
    letters = []
    fnt = L.font()
    for zi, zeile in enumerate(zeilen):
        z = -zi * size * 1.35
        w = len(zeile) * size * 0.55
        for ci, ch in enumerate(zeile):
            if ch == " ":
                continue
            o = L.text(f"{name}_{zi}_{ci}", ch, size, m, root, (-w / 2 + (ci + 0.5) * size * 0.55, -0.02, z), coll,
                       extrude=0.01, font=fnt)
            o.scale = (0, 0, 0)
            letters.append(o)
    rows = len(zeilen)
    frame = L.box(f"{name}_frame", (max(len(z_) for z_ in zeilen) * size * 0.58 + 0.15, 0.02, rows * size * 1.35 + 0.1),
                  L.mat("neon_board", "#141228", 0.4), root, (0, 0.01, -(rows - 1) * size * 0.675), coll)
    frame.scale = (0, 0, 0)
    return P(root=root, letters=letters, frame=frame)
