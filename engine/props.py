"""Wiederverwendbare Requisiten und Partikel (alle Zufallswerte mit festem Seed)."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import look as L
from anim import (ease_in_out, ease_out, ease_out_back, spring, tween, window, pop, unpop)

FPS = 30


class P:
    """Einfacher Container fuer Requisiten-Teile."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


# ------------------------------------------------------------------ Mehlsack 25 kg
def flour_sack(coll, name, label=True, scale=1.0, color=L.BURLAP, bow=False):
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
        L.text(f"{name}_t1", "MEHL", 0.11, mt, lab, (0, -0.008, 0.03), coll, extrude=0.003, font=L.font())
        L.text(f"{name}_t2", "25 kg", 0.065, mt, lab, (0, -0.008, -0.06), coll, extrude=0.003, font=L.font())
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
