"""Welt-Aufbau: Sets (theke, buero, studio) und die komplette Welt (Figuren, Kamera-Rig, Regie).

Sets: theke, buero, studio. Jedes Set liegt an einem eigenen Ursprung in derselben Welt
(Whip-Pans schwenken zwischen echten Orten). Licht pro Set: warmes Key, kuehles Fill,
tuerkis-violettes Rim, weiche Schatten. Lichter haben eine Cutoff-Distanz."""
import math
import random

import bpy
from mathutils import Vector

import importlib
import time

from mathutils import Quaternion

import anim
import characters as C
import look as L
import props as PR
from anim import ease_in, ease_out, window, Noise

FPS = 30

ORIGIN = {"theke": Vector((0, 0, 0)), "buero": Vector((40, 0, 0)), "studio": Vector((80, 0, 0)),
          "backstube": Vector((120, 0, 0)), "stadtkarte": Vector((160, 0, 0))}


def tile_mat(name, c1, c2, mortar, scale=6.0, mortar_size=0.02, rough=0.6, brick_w=0.5, row_h=0.25, offset=0.5,
             noise=0.0):
    if name in L._MATS:
        return L._MATS[name]
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Color1"].default_value = L.srgb(c1)
    br.inputs["Color2"].default_value = L.srgb(c2)
    br.inputs["Mortar"].default_value = L.srgb(mortar)
    br.inputs["Scale"].default_value = scale
    br.inputs["Mortar Size"].default_value = mortar_size
    br.inputs["Brick Width"].default_value = brick_w
    br.inputs["Row Height"].default_value = row_h
    br.offset = offset
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.3
    m.diffuse_color = L.srgb(c1)
    L._MATS[name] = m
    return m


def plane(name, size, material, loc, rot=(0, 0, 0), coll=None):
    o = L.box(name, (size[0], size[1], 0.02), material, None, loc, coll)
    o.rotation_euler = rot
    return o


class SetData:
    def __init__(self, name, origin):
        self.name = name
        self.o = origin
        self.objs = {}
        self.lights = []

    def p(self, x, y, z):
        return self.o + Vector((x, y, z))


def _lights(S, coll, key, fill, rim, key_e=900, fill_e=220, rim_e=650, rim2=None, rim2_e=400):
    lk = L.light(f"{S.name}_key", "AREA", key_e, "#FFD6A0", S.p(*key), L.look_rot(S.p(*key), S.p(0, 0.2, 1.6)),
                 size=2.6, coll=coll, cutoff=18)
    lf = L.light(f"{S.name}_fill", "AREA", fill_e, "#9DB2FF", S.p(*fill), L.look_rot(S.p(*fill), S.p(0, 0.2, 1.5)),
                 size=3.0, coll=coll, cutoff=18, shadow=False)
    lr = L.light(f"{S.name}_rim", "AREA", rim_e, L.VIOLET, S.p(*rim), L.look_rot(S.p(*rim), S.p(0, 0.3, 1.8)),
                 size=1.6, coll=coll, cutoff=18, shadow=False)
    S.lights += [lk, lf, lr]
    S.objs.update(key=lk, fill=lf, rim=lr)
    if rim2:
        lr2 = L.light(f"{S.name}_rim2", "AREA", rim2_e, L.TURQ, S.p(*rim2), L.look_rot(S.p(*rim2), S.p(0, 0.3, 1.8)),
                      size=1.4, coll=coll, cutoff=18, shadow=False)
        S.lights.append(lr2)
        S.objs["rim2"] = lr2


# =================================================================== THEKE
def build_theke(coll):
    S = SetData("theke", ORIGIN["theke"])
    c = coll
    floor = tile_mat("floor_wood", "#7A5236", "#6C4830", "#4E3424", scale=3.0, mortar_size=0.01, brick_w=1.6,
                     row_h=0.18, offset=0.5, rough=0.62)
    plane("theke_floor", (14, 10), floor, S.p(0, 0, -0.01), coll=c)
    tiles = tile_mat("wall_tiles", "#DCCFB9", "#D2C4AC", "#A89A83", scale=5.5, mortar_size=0.025, brick_w=0.5,
                     row_h=0.5, offset=0.0, rough=0.55)
    plane("theke_wall", (14, 6), tiles, S.p(0, 2.45, 3.0), rot=(math.pi / 2, 0, 0), coll=c)
    L.box("theke_wainscot", (14, 0.08, 1.1), L.mat("wainscot", "#3F5A78", 0.62), None, S.p(0, 2.4, 0.55), c)
    L.box("theke_wainscot_top", (14, 0.12, 0.06), L.mat("wood_light", L.WOOD_LIGHT, 0.6), None, S.p(0, 2.38, 1.12), c)
    # Seitenwand rechts (Tiefe)
    plane("theke_wall_r", (8, 6), tiles, S.p(3.6, 0, 3.0), rot=(math.pi / 2, 0, math.pi / 2), coll=c)
    # Brotregal hinten links
    wood = L.mat("wood", L.WOOD, 0.62)
    wdark = L.mat("wood_dark", L.WOOD_DARK, 0.65)
    sx = -1.55
    for z in (0.95, 1.55, 2.15, 2.75):
        L.box(f"theke_shelf{z}", (1.9, 0.45, 0.06), wood, None, S.p(sx, 2.15, z), c, bevel=0.01)
    for x in (-0.95, 0.95):
        L.box(f"theke_shelfside{x}", (0.07, 0.47, 2.05), wdark, None, S.p(sx + x, 2.15, 1.85), c)
    L.box("theke_shelfback", (1.9, 0.04, 2.05), L.mat("shelfback", "#5A3E2E", 0.7), None, S.p(sx, 2.37, 1.85), c)
    crust = L.mat("crust", L.CRUST, 0.65)
    crust2 = L.mat("crust2", "#B97A3E", 0.65)
    r = random.Random(5)
    for z in (1.0, 1.6, 2.2):
        x = sx - 0.82
        while x < sx + 0.8:
            kind = r.choice(["loaf", "loaf", "round", "baguette"])
            if kind == "loaf":
                L.sphere("loaf", 0.13, 10, 6, (1.45, 1.0, 0.8), r.choice([crust, crust2]), None,
                         S.p(x + 0.17, 2.12, z + 0.11), c)
                x += 0.38
            elif kind == "round":
                L.sphere("round", 0.15, 10, 6, (1.0, 1.0, 0.75), r.choice([crust, crust2]), None,
                         S.p(x + 0.16, 2.1, z + 0.12), c)
                x += 0.34
            else:
                o = L.sphere("bag", 0.06, 8, 5, (1, 1, 6.0), crust, None, S.p(x + 0.08, 2.2, z + 0.3), c)
                o.rotation_euler = (0.25, 0.15, 0)
                x += 0.16
    # Tuer hinten rechts (Gegenlicht)
    dx = 1.75
    L.box("theke_doorframe", (1.2, 0.14, 2.5), wdark, None, S.p(dx, 2.4, 1.25), c)
    glow = L.mat("door_glass", "#FFE7BF", 0.4, emit="#FFE7BF", strength=1.5)
    L.box("theke_doorglass", (0.86, 0.16, 1.3), glow, None, S.p(dx, 2.4, 1.55), c)
    L.box("theke_doorpanel", (0.86, 0.16, 0.62), L.mat("door_panel", "#4E6B8A", 0.6), None, S.p(dx, 2.39, 0.45), c)
    L.box("theke_doorbar", (0.86, 0.17, 0.06), wdark, None, S.p(dx, 2.39, 0.86), c)
    L.cyl("theke_doorhandle", 0.025, 0.25, 6, L.mat("brass", L.GOLD, 0.45, metallic=0.6), None,
          S.p(dx - 0.33, 2.3, 1.05), c)
    S.objs["door"] = S.p(dx, 2.3, 1.5)
    dl = L.light("theke_daylight", "AREA", 140, "#FFE2B8", S.p(dx, 2.9, 1.8), L.look_rot(S.p(dx, 2.9, 1.8), S.p(0, 0, 1.5)),
                 size=1.2, coll=c, cutoff=14, shadow=False)
    S.lights.append(dl)
    # Haengelampen
    for x in (-1.0, 1.1):
        L.cyl(f"theke_lampcord{x}", 0.008, 1.0, 5, L.mat("cord", "#222", 0.7), None, S.p(x, 0.6, 3.55), c)
        L.cyl(f"theke_lampshade{x}", 0.08, 0.22, 12, L.mat("lampshade", "#2F4A5E", 0.55), None, S.p(x, 0.6, 2.98), c,
              r2=0.25)
        L.sphere(f"theke_bulb{x}", 0.07, 8, 5, (1, 1, 1), L.mat("bulb", "#FFE7BF", 0.4, emit="#FFD9A0", strength=8),
                 None, S.p(x, 0.6, 2.86), c)
        lp = L.light(f"theke_lamp{x}", "POINT", 22, "#FFD9A0", S.p(x, 0.6, 2.8), size=0.15, coll=c, cutoff=8, shadow=False)
        S.lights.append(lp)
    # Ladentheke
    cream = L.mat("counter_front", "#E9DFCC", 0.62)
    L.box("theke_counter", (3.3, 0.72, 0.98), cream, None, S.p(0, -0.32, 0.49), c)
    for i in range(7):
        L.box(f"theke_counterpanel{i}", (0.05, 0.03, 0.8), wood, None, S.p(-1.5 + i * 0.5, -0.69, 0.5), c)
    L.box("theke_counterbase", (3.32, 0.74, 0.1), wdark, None, S.p(0, -0.32, 0.05), c)
    L.box("theke_countertop", (3.45, 0.86, 0.07), L.mat("countertop", L.WOOD_LIGHT, 0.55), None, S.p(0, -0.32, 1.015),
          c, bevel=0.015)
    S.top_z = 1.05
    # Kasse mit Schublade (links)
    kx = -1.18
    reg = L.empty("theke_register", None, S.p(kx, -0.42, S.top_z), c)
    m_reg = L.mat("register", "#46496E", 0.5)
    m_trim = L.mat("brass", L.GOLD, 0.45, metallic=0.6)
    L.box("reg_base", (0.56, 0.48, 0.14), m_reg, reg, (0, 0, 0.07), c, bevel=0.02)
    drawer = L.empty("reg_drawer", reg, (0, 0, 0.0), c)
    L.box("reg_drawerbox", (0.5, 0.44, 0.1), L.mat("drawer", "#5A5E86", 0.5), drawer, (0, -0.04, 0.06), c, bevel=0.01)
    L.box("reg_drawerhandle", (0.16, 0.02, 0.025), m_trim, drawer, (0, -0.265, 0.07), c)
    for i in range(5):
        L.cyl(f"reg_coin{i}", 0.04, 0.012, 10, L.mat("coin", L.GOLD, 0.42, metallic=0.75), drawer,
              (-0.15 + i * 0.075, -0.1, 0.11), c)
    body = L.box("reg_body", (0.5, 0.32, 0.26), m_reg, reg, (0, 0.06, 0.27), c, bevel=0.03)
    body.rotation_euler = (math.radians(-12), 0, 0)
    for i in range(3):
        for j in range(4):
            L.box(f"reg_key{i}{j}", (0.06, 0.05, 0.025), L.mat("regkey", L.FLOUR, 0.55), reg,
                  (-0.13 + j * 0.085, -0.07 + i * 0.06, 0.42 - i * 0.012), c, bevel=0.008)
    L.box("reg_display", (0.3, 0.06, 0.12), m_reg, reg, (0, 0.17, 0.52), c, bevel=0.015)
    L.box("reg_displayglass", (0.24, 0.02, 0.07), L.mat("reg_glass", "#123", 0.4, emit=L.TURQ, strength=1.2), reg,
          (0, 0.135, 0.53), c)
    L.box("reg_trim", (0.58, 0.5, 0.02), m_trim, reg, (0, 0, 0.145), c)
    S.objs["register"] = reg
    S.objs["drawer"] = drawer
    # Broetchenkorb (rechts)
    bk = L.empty("theke_basket", None, S.p(0.9, -0.42, S.top_z), c)
    wick = L.mat("wicker", "#B0773B", 0.75)
    L.cyl("basket_bowl", 0.3, 0.16, 12, wick, bk, (0, 0, 0.08), c, r2=0.36)
    L.torus("basket_rim", 0.36, 0.035, 14, 5, L.mat("wicker2", "#8E5D2C", 0.75), bk, (0, 0, 0.165), c)
    L.box("basket_cloth", (0.5, 0.5, 0.01), L.mat("basket_cloth", "#C8D2E4", 0.8), bk, (0, 0, 0.17), c).rotation_euler = (0, 0, 0.6)
    rolls = []
    for i, (x, y) in enumerate([(-0.12, -0.08), (0.12, -0.1), (0.0, 0.1), (-0.17, 0.12), (0.17, 0.1)]):
        rp = L.empty(f"roll{i}", bk, (x, y, 0.2), c)
        L.sphere(f"roll_m{i}", 0.12, 10, 6, (1.15, 0.95, 0.7), crust, rp, (0, 0, 0.0), c)
        L.box(f"roll_cut{i}", (0.15, 0.02, 0.02), L.mat("rollcut", "#E3B375", 0.7), rp, (0, 0, 0.08), c).rotation_euler = (0, 0, 0.5)
        rolls.append(rp)
    S.objs["rolls"] = rolls
    S.objs["basket"] = bk
    # Laptop (Mitte rechts), schraeg zur Kamera
    lp = PR.laptop(c, "theke_laptop")
    lp.root.location = S.p(0.36, -0.45, S.top_z)
    lp.root.rotation_euler = (0, 0, math.radians(200))
    S.objs["laptop"] = lp
    # kleine Details: Glas mit Kochloeffeln, Papiertueten
    L.cyl("theke_jar", 0.09, 0.22, 10, L.mat("jar", "#BFD8E0", 0.3, alpha=0.6), None, S.p(-0.6, -0.15, S.top_z + 0.11), c)
    for i in range(3):
        o = L.cyl(f"theke_spoon{i}", 0.012, 0.36, 5, wood, None, S.p(-0.6 + (i - 1) * 0.03, -0.15, S.top_z + 0.26), c)
        o.rotation_euler = (0, (i - 1) * 0.25, 0)
    for i in range(3):
        L.box(f"theke_bag{i}", (0.18, 0.1, 0.25), L.mat("paperbag", "#D7B98C", 0.8), None,
              S.p(1.62 - i * 0.03, 2.1, 0.95 + 0.13 + 0.6 * 0 + 0.0), c).location.x += 0
    _lights(S, c, key=(-2.6, -3.2, 4.2), fill=(3.2, -2.8, 1.8), rim=(1.6, 2.0, 3.6), rim2=(-1.8, 1.8, 3.2),
            key_e=360, fill_e=95, rim_e=320, rim2_e=220)
    S.kalle = S.p(-0.12, 0.28, 0.0)
    S.byte = S.p(0.78, -0.05, 2.05)
    return S


# =================================================================== BUERO
def build_buero(coll):
    S = SetData("buero", ORIGIN["buero"])
    c = coll
    carpet = tile_mat("carpet", "#3D4566", "#394161", "#333A57", scale=2.0, mortar_size=0.0, rough=0.9)
    plane("buero_floor", (14, 10), carpet, S.p(0, 0, -0.01), coll=c)
    wall = tile_mat("wallpaper", "#56627F", "#515C79", "#4C5672", scale=4.0, mortar_size=0.0, brick_w=0.12, row_h=4.0,
                    offset=0.0, rough=0.7)
    plane("buero_wall", (14, 6), wall, S.p(0, 2.45, 3.0), rot=(math.pi / 2, 0, 0), coll=c)
    plane("buero_wall_l", (8, 6), wall, S.p(-3.6, 0, 3.0), rot=(math.pi / 2, 0, math.pi / 2), coll=c)
    L.box("buero_skirting", (14, 0.06, 0.14), L.mat("wood_dark", L.WOOD_DARK, 0.65), None, S.p(0, 2.42, 0.07), c)
    wood = L.mat("wood", L.WOOD, 0.62)
    wdark = L.mat("wood_dark", L.WOOD_DARK, 0.65)
    # Pinnwand
    L.box("buero_pinboard", (1.3, 0.05, 0.9), L.mat("cork", "#B8895A", 0.85), None, S.p(-0.85, 2.4, 2.05), c, bevel=0.01)
    L.box("buero_pinframe", (1.4, 0.04, 1.0), wdark, None, S.p(-0.85, 2.42, 2.05), c)
    r = random.Random(9)
    for i in range(7):
        col = [L.FLOUR, "#F6E3B0", "#CDEFEA", "#F7D2C9", L.FLOUR][i % 5]
        n = L.box(f"buero_note{i}", (0.22, 0.01, 0.2), L.mat(f"note{col}", col, 0.7), None,
                  S.p(-1.35 + (i % 4) * 0.33, 2.36, 2.3 - (i // 4) * 0.42 + r.uniform(-0.04, 0.04)), c)
        n.rotation_euler = (0, r.uniform(-0.15, 0.15), 0)
        L.sphere(f"buero_pin{i}", 0.018, 6, 4, (1, 1, 1), L.mat("pinred", L.RED, 0.5), None,
                 S.p(-1.35 + (i % 4) * 0.33, 2.34, 2.38 - (i // 4) * 0.42), c)
    # Wanduhr
    clk = PR.wall_clock(c, "buero_clock")
    clk.root.location = S.p(1.05, 2.38, 2.55)
    S.objs["clock"] = clk
    # Regal mit Ordnern
    L.box("buero_shelf", (1.0, 0.36, 0.05), wood, None, S.p(1.95, 2.2, 1.55), c)
    L.box("buero_shelf2", (1.0, 0.36, 0.05), wood, None, S.p(1.95, 2.2, 2.15), c)
    cols = ["#B5524F", "#3E8E6A", "#C9944A", "#2E8C88", "#6C5BA8", "#B5524F", "#C9944A"]
    for row, z in enumerate((1.58, 2.18)):
        for i in range(6):
            o = L.box(f"buero_folder{row}{i}", (0.1, 0.3, 0.42), L.mat(f"folder{cols[(i + row) % 7]}", cols[(i + row) % 7], 0.65),
                      None, S.p(1.55 + i * 0.13, 2.2, z + 0.21), c, bevel=0.01)
            L.box(f"buero_flabel{row}{i}", (0.06, 0.01, 0.12), L.mat("flabel", L.FLOUR, 0.6), o, (0, -0.15, 0.06), c)
            if i == 5:
                o.rotation_euler = (0, 0.25, 0)
    # Mehlsaecke in der Ecke
    for i, (x, y, z, rz) in enumerate([(-2.2, 1.6, 0, 0.3), (-1.65, 1.75, 0, -0.2), (-1.95, 1.65, 0.6, 0.1)]):
        s = PR.flour_sack(c, f"buero_sack{i}", label=True, scale=1.0)
        s.root.location = S.p(x, y, z)
        s.root.rotation_euler = (0, 0, rz)
    # Schreibtisch
    L.box("buero_desktop", (1.7, 0.85, 0.06), L.mat("desktop", L.WOOD_LIGHT, 0.55), None, S.p(0.75, -0.05, 0.95), c,
          bevel=0.015)
    for x in (-0.78, 0.78):
        L.box(f"buero_deskleg{x}", (0.07, 0.75, 0.92), wdark, None, S.p(0.75 + x, -0.05, 0.46), c)
    L.box("buero_drawers", (0.5, 0.72, 0.5), wood, None, S.p(1.25, -0.05, 0.65), c)
    lp = PR.laptop(c, "buero_laptop")
    lp.root.location = S.p(0.82, 0.0, 0.98)
    lp.root.rotation_euler = (0, 0, math.radians(215))
    S.objs["laptop"] = lp
    # Tasse, Stifte
    L.cyl("buero_mug", 0.07, 0.14, 10, L.mat("mug", "#E9E2D3", 0.55), None, S.p(1.35, 0.15, 1.05), c)
    L.cyl("buero_mugcoffee", 0.06, 0.01, 10, L.mat("coffee", "#3B2416", 0.4), None, S.p(1.35, 0.15, 1.115), c)
    # Buerostuhl
    ch = L.empty("buero_chair", None, S.p(-0.42, 0.22, 0.0), c)
    m_ch = L.mat("chair", "#2D3557", 0.62)
    m_met = L.mat("chairmetal", L.METAL, 0.45, metallic=0.5)
    for i in range(5):
        a = 2 * math.pi * i / 5
        leg = L.box(f"chair_leg{i}", (0.06, 0.38, 0.04), m_met, ch, (0.19 * math.sin(a), 0.19 * math.cos(a), 0.08), c)
        leg.rotation_euler = (0, 0, -a)
        L.sphere(f"chair_wheel{i}", 0.04, 8, 5, (1, 1, 1), m_ch, ch, (0.36 * math.sin(a), 0.36 * math.cos(a), 0.04), c)
    seatpiv = L.empty("chair_seatpiv", ch, (0, 0, 0.1), c)
    L.cyl("chair_pole", 0.035, 0.38, 8, m_met, seatpiv, (0, 0, 0.17), c)
    seat = L.empty("chair_seat", seatpiv, (0, 0, 0.36), c)
    L.box("chair_seatmesh", (0.6, 0.56, 0.1), m_ch, seat, (0, 0, 0.05), c, bevel=0.04)
    L.box("chair_back", (0.56, 0.08, 0.6), m_ch, seat, (0, 0.3, 0.5), c, bevel=0.04)
    L.box("chair_backpost", (0.06, 0.04, 0.3), m_met, seat, (0, 0.3, 0.15), c)
    S.objs["chair"] = ch
    S.objs["chair_seat"] = seat
    S.objs["chair_spin"] = seatpiv
    # Schreibtischlampe
    L.cyl("buero_lampbase", 0.1, 0.03, 10, m_met, None, S.p(0.2, 0.15, 0.995), c)
    arm = L.cyl("buero_lamparm", 0.015, 0.5, 6, m_met, None, S.p(0.24, 0.15, 1.24), c)
    arm.rotation_euler = (0, 0.25, 0)
    L.cyl("buero_lampshade", 0.06, 0.16, 10, L.mat("lampshade2", L.GOLD, 0.5), None, S.p(0.33, 0.1, 1.48), c, r2=0.14)
    lp2 = L.light("buero_desklamp", "SPOT", 60, "#FFD8A0", S.p(0.33, 0.1, 1.45), (0.4, 0, 0), size=0.1, coll=c,
                  cutoff=6, spot=1.4)
    S.lights.append(lp2)
    # Fenster-Licht (Gegenlicht links hinten)
    L.box("buero_window", (1.0, 0.1, 1.2), L.mat("door_glass", "#FFE7BF", 0.4, emit="#FFE7BF", strength=2.2), None,
          S.p(-3.55, 1.0, 1.9), c).rotation_euler = (0, 0, math.pi / 2)
    L.box("buero_windowframe", (1.1, 0.12, 1.3), wdark, None, S.p(-3.57, 1.0, 1.9), c).rotation_euler = (0, 0, math.pi / 2)
    wl = L.light("buero_winlight", "AREA", 160, "#FFE2B8", S.p(-3.2, 1.0, 2.0), L.look_rot(S.p(-3.2, 1, 2), S.p(0, 0, 1.2)),
                 size=1.2, coll=c, cutoff=12)
    S.lights.append(wl)
    _lights(S, c, key=(-2.2, -3.4, 4.0), fill=(3.4, -2.4, 1.8), rim=(1.8, 2.0, 3.5), rim2=(-2.0, 1.8, 3.0),
            key_e=430, fill_e=110, rim_e=320, rim2_e=230)
    S.kalle = S.p(-0.42, 0.18, 0.0)
    S.byte = S.p(0.15, 0.45, 2.15)
    return S


# =================================================================== BACKSTUBE (2.2)
def build_backstube(coll):
    """Backstube hinter dem Verkaufsraum (neuer Winkel auf dieselbe Baeckerei): gemauerter Holzofen mit Glut,
    Arbeitstisch mit Mehl, Teigknetmaschine, Blechwagen mit Brezeln, Mehlsaecke 'WEIZEN 550', Fenster zur Strasse,
    offene Tuer mit Blick auf die Theke von hinten. Alle Materialien heissen 'bs_*' (Lichtstimmungen: apply_licht).
    Kamera-Standpunkte: S.cams['totale'] (vom Ofen Richtung Tuer), S.cams['nah'] (am Arbeitstisch)."""
    S = SetData("backstube", ORIGIN["backstube"])
    c = coll
    m = lambda n, col, r=0.6, **kw: L.mat(f"bs_{n}", col, r, **kw)  # noqa: E731
    floor = tile_mat("bs_floor", "#A86A47", "#9C6040", "#6E4330", scale=2.6, mortar_size=0.02, brick_w=0.5, row_h=0.5,
                     offset=0.0, rough=0.7)
    plane("bs_floor", (10, 10), floor, S.p(0, 0.5, -0.01), coll=c)
    wall = tile_mat("bs_wall", "#D8C7A8", "#CFBC9C", "#A8957A", scale=4.5, mortar_size=0.02, brick_w=0.6, row_h=0.3,
                    rough=0.7)
    wdark = m("wood_dark", L.WOOD_DARK, 0.65)
    wood = m("wood", L.WOOD, 0.62)
    wlight = m("wood_light", L.WOOD_LIGHT, 0.55)
    # Rueckwand mit Tueroeffnung (x 0.3 .. 1.5, Hoehe 2.5)
    DX = 0.9
    L.box("bs_wall_l", (4.3, 0.12, 4.0), wall, None, S.p(-1.85, 3.2, 2.0), c)
    L.box("bs_wall_r", (2.9, 0.12, 4.0), wall, None, S.p(2.95, 3.2, 2.0), c)
    L.box("bs_wall_t", (1.2, 0.12, 1.5), wall, None, S.p(DX, 3.2, 3.25), c)
    L.box("bs_skirting", (10, 0.06, 0.14), wdark, None, S.p(0, 3.13, 0.07), c)
    plane("bs_wall_left", (10, 4.0), wall, S.p(-4.0, 0, 2.0), rot=(math.pi / 2, 0, math.pi / 2), coll=c)
    plane("bs_wall_right", (10, 4.0), wall, S.p(4.4, 0, 2.0), rot=(math.pi / 2, 0, math.pi / 2), coll=c)
    L.box("bs_ceiling", (10, 10, 0.1), m("ceiling", "#5A4636", 0.7), None, S.p(0, 0.5, 3.95), c)
    for k in range(5):
        L.box(f"bs_beam{k}", (10, 0.18, 0.2), wdark, None, S.p(0, -1.5 + k * 1.2, 3.82), c)
    # Tuerrahmen und offene Tuer (Blatt nach innen geklappt)
    for x in (DX - 0.65, DX + 0.65):
        L.box(f"bs_doorpost{x}", (0.1, 0.18, 2.55), wdark, None, S.p(x, 3.2, 1.27), c)
    L.box("bs_doortop", (1.4, 0.18, 0.1), wdark, None, S.p(DX, 3.2, 2.55), c)
    leaf = L.empty("bs_doorleaf", None, S.p(DX + 0.6, 3.12, 0), c)
    leaf.rotation_euler = (0, 0, math.radians(-105))
    L.box("bs_doorleafm", (1.15, 0.06, 2.4), m("door_panel", "#4E6B8A", 0.6), leaf, (-0.58, 0, 1.22), c)
    L.box("bs_doorglass", (0.6, 0.07, 0.8), m("doorglass", "#D9E7F2", 0.4), leaf, (-0.58, 0, 1.7), c)
    S.objs["door"] = leaf
    # Kulisse: Verkaufsraum mit der Theke von hinten (gleiche Farben wie das Set 'theke')
    plane("bs_k_floor", (4.0, 4.6), tile_mat("bs_k_floor", "#7A5236", "#6C4830", "#4E3424", scale=3.0, mortar_size=0.01,
                                            brick_w=1.6, row_h=0.18, offset=0.5, rough=0.62), S.p(DX, 5.4, -0.005), coll=c)
    kw = tile_mat("bs_k_wall", "#DCCFB9", "#D2C4AC", "#A89A83", scale=5.5, mortar_size=0.025, brick_w=0.5, row_h=0.5,
                  offset=0.0, rough=0.55)
    for x in (DX - 2.0, DX + 2.0):
        plane(f"bs_k_side{x}", (4.6, 4.0), kw, S.p(x, 5.4, 2.0), rot=(math.pi / 2, 0, math.pi / 2), coll=c)
    L.box("bs_k_front", (4.2, 0.1, 1.0), m("k_wainscot", "#3F5A78", 0.62), None, S.p(DX, 7.6, 0.5), c)
    L.box("bs_k_window", (4.0, 0.08, 2.6), m("k_shopwindow", "#FFE7BF", 0.4, emit="#FFE7BF", strength=1.5), None,
          S.p(DX, 7.65, 2.3), c)
    L.box("bs_k_wtop", (4.2, 0.1, 0.4), kw, None, S.p(DX, 7.6, 3.8), c)
    ctr = L.empty("bs_k_theke", None, S.p(DX, 5.3, 0), c)
    L.box("bs_k_counter", (3.3, 0.72, 0.98), m("k_counter", "#E9DFCC", 0.62), ctr, (0, 0, 0.49), c)
    L.box("bs_k_countertop", (3.45, 0.86, 0.07), m("k_countertop", L.WOOD_LIGHT, 0.55), ctr, (0, 0, 1.015), c, bevel=0.015)
    L.box("bs_k_backpanel", (3.2, 0.04, 0.85), m("k_shelfdark", "#4E3424", 0.7), ctr, (0, -0.37, 0.48), c)
    for k in range(3):
        L.box(f"bs_k_shelf{k}", (3.1, 0.3, 0.03), wood, ctr, (0, -0.3, 0.15 + 0.3 * k), c)
        for j in range(4):
            L.box(f"bs_k_bag{k}{j}", (0.16, 0.1, 0.2), m("k_paperbag", "#D7B98C", 0.8), ctr,
                  (-1.2 + j * 0.75 + 0.1 * k, -0.32, 0.27 + 0.3 * k), c)
    reg = L.empty("bs_k_register", ctr, (-1.18, 0.1, 1.05), c)
    L.box("bs_k_regbase", (0.56, 0.48, 0.14), m("k_register", "#46496E", 0.5), reg, (0, 0, 0.07), c, bevel=0.02)
    L.box("bs_k_regbody", (0.5, 0.32, 0.26), m("k_register", "#46496E", 0.5), reg, (0, 0.06, 0.27), c, bevel=0.03)
    L.box("bs_k_regdisplay", (0.3, 0.06, 0.12), m("k_register", "#46496E", 0.5), reg, (0, 0.17, 0.5), c)
    L.cyl("bs_k_basket", 0.3, 0.16, 12, m("k_wicker", "#B0773B", 0.75), ctr, (0.9, 0.1, 1.13), c, r2=0.36)
    lap = L.empty("bs_k_laptop", ctr, (0.36, 0.1, 1.05), c)
    L.box("bs_k_lapbase", (0.62, 0.42, 0.03), m("k_laptop", "#9AA0B8", 0.45), lap, (0, 0, 0.015), c)
    L.box("bs_k_laplid", (0.62, 0.025, 0.4), m("k_laptop", "#9AA0B8", 0.45), lap, (0, -0.2, 0.22), c)
    for x in (DX - 1.0, DX + 1.0):
        L.cyl(f"bs_k_lampcord{x}", 0.008, 1.0, 5, m("cord", "#222222", 0.7), None, S.p(x, 5.9, 3.45), c)  # noqa
        L.cyl(f"bs_k_lampshade{x}", 0.08, 0.22, 12, m("lampshade", "#2F4A5E", 0.55), None, S.p(x, 5.9, 2.88), c, r2=0.25)
        L.sphere(f"bs_k_bulb{x}", 0.07, 8, 5, (1, 1, 1), m("k_bulb", "#FFE7BF", 0.4, emit="#FFD9A0", strength=8), None,
                 S.p(x, 5.9, 2.76), c)
    # Grosser gemauerter Holzofen (linke Wand), Maul zeigt in den Raum (+X)
    brick = tile_mat("bs_brick", "#9C4A32", "#8E422C", "#5C2E22", scale=6.0, mortar_size=0.03, brick_w=0.5, row_h=0.25,
                     rough=0.8)
    ov = S.p(-2.55, 2.4, 0)                       # Ofen an der Rueckwand links, Maul zur Kamera (-Y)
    L.box("bs_oven_base", (2.1, 1.6, 1.0), brick, None, ov + Vector((0, 0, 0.5)), c)
    L.sphere("bs_oven_dome", 1.0, 14, 8, (1.2, 0.85, 0.85), brick, None, ov + Vector((0, 0.05, 1.0)), c)
    L.box("bs_oven_front", (2.1, 0.16, 0.95), brick, None, ov + Vector((0, -0.74, 1.45)), c)
    L.box("bs_oven_chimney", (0.5, 0.5, 2.2), brick, None, ov + Vector((0.5, 0.35, 2.85)), c)
    L.box("bs_oven_ledge", (2.5, 0.4, 0.08), m("stone", "#8A8478", 0.7), None, ov + Vector((0, -0.95, 1.0)), c)
    mouth = ov + Vector((0, -0.83, 1.4))
    L.box("bs_oven_mouth", (1.0, 0.06, 0.62), m("oven_mouth", "#120806", 0.9), None, mouth, c)
    L.cyl("bs_oven_arch", 0.5, 0.07, 14, m("oven_mouth", "#120806", 0.9), None, mouth + Vector((0, 0, 0.31)), c, axis="Y")
    m_glut = L.mat("bs_glut", "#FF7A2E", 0.4, emit="#FF7A2E", strength=6.0)
    glut = L.empty("bs_glutbed", None, mouth + Vector((0, -0.07, -0.22)), c)
    rg = random.Random(31)
    embers = []
    for k in range(16):
        e = L.ico(f"bs_ember{k}", rg.uniform(0.06, 0.1), 1, (1, 0.6, 0.7), m_glut, glut,
                  (rg.uniform(-0.4, 0.4), rg.uniform(-0.03, 0.0), rg.uniform(0, 0.16)), c)
        embers.append(e)
    for k in range(4):
        lg = L.cyl(f"bs_ovenlog{k}", 0.05, 0.5, 7, m("charcoal", "#2B1A14", 0.8), glut,
                   (-0.25 + 0.17 * k, -0.02, 0.24), c, axis="X")
        lg.rotation_euler = (0, 0, 0.3 * (k - 1.5))
    L.box("bs_oven_door", (0.8, 0.06, 0.55), m("iron", "#3A3A44", 0.45, metallic=0.6), None,
          ov + Vector((1.45, -1.05, 0.32)), c).rotation_euler = (0.25, 0, -0.3)
    gl = L.light("bs_glutlight", "POINT", 120, "#FF8A3D", mouth + Vector((0, -0.4, 0)), size=0.4, coll=c, cutoff=6,
                 shadow=False)
    S.objs.update(glut=glut, embers=embers, glut_mat=m_glut, glut_light=gl, oven_mouth=mouth, oven=ov)
    # Holzstapel neben dem Ofen
    for k in range(6):
        L.cyl(f"bs_woodpile{k}", 0.07, 0.6, 7, m("log", "#8A5A3A", 0.7), None,
              ov + Vector((-1.35 + 0.15 * (k % 3), -1.15, 0.07 + 0.13 * (k // 3))), c, axis="Y")
    # Arbeitstisch aus Holz mit Mehl
    T0 = S.p(0.1, 0.5, 0)
    S.table_z = 0.96
    L.box("bs_table_top", (2.4, 1.1, 0.08), wlight, None, T0 + Vector((0, 0, 0.92)), c, bevel=0.02)
    for x in (-1.1, 1.1):
        for y in (-0.45, 0.45):
            L.box(f"bs_table_leg{x}{y}", (0.08, 0.08, 0.9), wdark, None, T0 + Vector((x, y, 0.45)), c)
    L.box("bs_table_shelf", (2.2, 0.9, 0.04), wood, None, T0 + Vector((0, 0, 0.25)), c)
    m_mehl = m("mehl", "#F7F3EA", 0.9)
    rm = random.Random(8)
    for k in range(7):
        o = L.cyl(f"bs_tablemehl{k}", rm.uniform(0.12, 0.3), 0.01, 10, m_mehl, None,
                  T0 + Vector((rm.uniform(-1.0, 1.0), rm.uniform(-0.4, 0.4), 0.965)), c)
        o.scale = (1, rm.uniform(0.5, 1.0), 1)
    L.sphere("bs_dough", 0.16, 10, 6, (1.2, 1.0, 0.55), m("dough", "#EBD3A8", 0.7), None, T0 + Vector((-0.5, 0.05, 1.02)), c)
    L.box("bs_scraper", (0.14, 0.01, 0.1), m("metal", L.METAL, 0.4, metallic=0.6), None, T0 + Vector((-0.15, -0.25, 0.98)),
          c).rotation_euler = (math.pi / 2, 0, 0.5)
    L.box("bs_scraper_grip", (0.14, 0.03, 0.03), wdark, None, T0 + Vector((-0.15, -0.25, 1.01)), c).rotation_euler = (0, 0, 0.5)
    L.cyl("bs_rollpin", 0.04, 0.5, 10, wlight, None, T0 + Vector((0.55, 0.15, 1.0)), c, axis="X").rotation_euler = (0, 0, 0.3)
    for k in range(5):
        L.ico(f"bs_doughscrap{k}", 0.03, 1, (1.2, 1, 0.5), m("dough", "#EBD3A8", 0.7), None,
              T0 + Vector((rm.uniform(-0.9, 0.9), rm.uniform(-0.4, 0.4), 0.975)), c)
    # Mehl auf dem Boden
    for k in range(10):
        o = L.cyl(f"bs_floormehl{k}", rm.uniform(0.15, 0.4), 0.006, 10, m_mehl, None,
                  S.p(rm.uniform(-2.2, 2.6), rm.uniform(-1.5, 2.6), 0.004), c)
        o.scale = (1, rm.uniform(0.4, 1.0), 1)
    # Teigknetmaschine
    km = S.p(2.1, -0.95, 0)
    m_mach = m("machine", "#5E8C8A", 0.45)
    m_met = m("metal", L.METAL, 0.4, metallic=0.6)
    L.box("bs_kneader_base", (0.7, 0.6, 0.75), m_mach, None, km + Vector((0, 0, 0.375)), c, bevel=0.03)
    L.box("bs_kneader_col", (0.22, 0.22, 0.9), m_mach, None, km + Vector((0, 0.22, 1.2)), c, bevel=0.03)
    L.box("bs_kneader_head", (0.3, 0.6, 0.2), m_mach, None, km + Vector((0, 0.0, 1.62)), c, bevel=0.04)
    L.cyl("bs_kneader_bowl", 0.3, 0.32, 16, m_met, None, km + Vector((0, -0.08, 0.91)), c, r2=0.26)
    L.sphere("bs_kneader_dough", 0.25, 10, 6, (1, 1, 0.45), m("dough", "#EBD3A8", 0.7), None, km + Vector((0, -0.08, 1.05)), c)
    hook = L.empty("bs_kneader_hook", None, km + Vector((0, -0.1, 1.5)), c)
    L.cyl("bs_kneader_hookm", 0.02, 0.45, 6, m_met, hook, (0, 0, -0.22), c)
    S.objs["kneader_hook"] = hook
    L.box("bs_kneader_plate", (0.36, 0.01, 0.1), m("plate", "#F5F1E8", 0.5), None, km + Vector((0, -0.31, 0.6)), c)
    L.text("bs_kneader_lab", "KNETER", 0.07, m("ink", "#141228", 0.5), None, tuple(km + Vector((0, -0.318, 0.59))), c,
           extrude=0.003, font=L.font())
    # Blechwagen mit Brezeln
    bw = S.p(2.25, 1.15, 0)
    for x in (-0.32, 0.32):
        for y in (-0.42, 0.42):
            L.box(f"bs_rack_post{x}{y}", (0.04, 0.04, 1.8), m_met, None, bw + Vector((x, y, 0.95)), c)
            L.cyl(f"bs_rack_wheel{x}{y}", 0.05, 0.04, 8, m("rubber", "#222", 0.7), None, bw + Vector((x, y, 0.05)), c,
                  axis="X")
    for k in range(5):
        z = 0.35 + 0.32 * k
        L.box(f"bs_rack_tray{k}", (0.62, 0.86, 0.02), m("tray", "#8E93A8", 0.4, metallic=0.6), None, bw + Vector((0, 0, z)), c)
        for j in range(3):
            PR.pastry(c, f"bs_rack_brezel{k}{j}", "brezel", None, tuple(bw + Vector((0, -0.28 + 0.28 * j, z + 0.01))), 0.9)
    # Mehlsaecke 'WEIZEN 550' an der Rueckwand
    for k, (x, z, rz) in enumerate([(2.05, 0, 0.1), (2.75, 0, -0.08), (2.4, 0.62, 0.05)]):
        sk = PR.flour_sack(c, f"bs_sack{k}", label=True, scale=1.0, text1="WEIZEN", text2="550")
        sk.root.location = S.p(x, 2.85, z)
        sk.root.rotation_euler = (0, 0, rz)
    # Fenster zur Strasse (Rueckwand links)
    wpos = S.p(-0.6, 3.12, 1.95)
    m_win = L.mat("bs_window", "#8CA3CF", 0.4, emit="#8CA3CF", strength=2.0)
    L.box("bs_window_glass", (1.3, 0.06, 1.1), m_win, None, wpos, c)
    for dx, dz, w, h in [(0, 0.58, 1.46, 0.08), (0, -0.58, 1.46, 0.1), (-0.69, 0, 0.08, 1.2), (0.69, 0, 0.08, 1.2),
                         (0, 0, 0.05, 1.1), (0, 0, 1.3, 0.05)]:
        L.box(f"bs_window_frame{dx}{dz}{w}", (w, 0.1, h), m("winframe", "#F0EADD", 0.6), None,
              wpos + Vector((dx, -0.03, dz)), c)
    moon = L.cyl("bs_moon", 0.13, 0.01, 18, L.mat("bs_moon", "#E8F0FF", 0.4, emit="#E8F0FF", strength=5.0), None,
                 wpos + Vector((0.32, -0.045, 0.25)), c, axis="Y")
    sun = L.cyl("bs_sun", 0.22, 0.01, 20, L.mat("bs_sunglow", "#FFD36B", 0.4, emit="#FFD36B", strength=5.0), None,
                wpos + Vector((-0.3, -0.045, -0.2)), c, axis="Y")
    # Lichtstrahl durchs Fenster (Mond blau, Morgensonne warm)
    tgt = S.p(0.6, 0.4, 0.95)
    d = tgt - wpos
    beams = {}
    for nm, col, al in (("moon", "#6E8FE0", 0.08), ("sun", "#FFD9A0", 0.11)):
        piv = L.empty(f"bs_beam_{nm}", None, wpos, c)
        piv.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        L.cyl(f"bs_beamm_{nm}", 0.45, d.length * 1.1, 12, L.mat(f"bs_glow_beam_{nm}", col, 0.4, emit=col, strength=1.0,
                                                                alpha=al), piv, (0, 0, d.length * 0.55), c, r2=0.7, cap=False)
        beams[nm] = piv
    S.objs.update(window_mat=m_win, moon=moon, sun=sun, beams=beams, window=wpos, beam_target=tgt)
    # Neonroehre an der Decke
    m_neon = L.mat("bs_neon", "#2A2E3A", 0.4, emit="#E8F4FF", strength=6.0)
    L.box("bs_neon_housing", (1.8, 0.2, 0.08), m("lampbox", "#C9CED8", 0.5), None, S.p(0.1, 0.5, 3.7), c)
    L.box("bs_neon_tube", (1.6, 0.08, 0.06), m_neon, None, S.p(0.1, 0.5, 3.64), c)
    S.objs["neon_mat"] = m_neon
    # Regalbrett mit Schuesseln (Wand rechts vorn)
    L.box("bs_shelf", (0.35, 1.4, 0.04), wood, None, S.p(4.22, -0.8, 1.7), c)
    for k in range(3):
        L.cyl(f"bs_bowl{k}", 0.13, 0.12, 12, m("bowl", "#E9E2D3", 0.55), None, S.p(4.22, -1.3 + 0.45 * k, 1.78), c, r2=0.09)
    _lights(S, c, key=(-2.4, -3.0, 3.6), fill=(3.0, -2.6, 2.0), rim=(1.6, 2.4, 3.4), key_e=300, fill_e=80, rim_e=200)
    S.kalle = S.p(0.1, 1.35, 0.0)
    S.byte = S.p(0.9, 0.5, 1.6)
    S.top_z = S.table_z
    S.cams = {"totale": (S.p(-1.4, -5.6, 2.5), S.p(-0.55, 2.0, 1.4), 28.0),
              "nah": (S.p(0.4, -1.7, 1.75), S.p(0.1, 0.6, 1.15), 42.0)}
    return S


# ------------------------------------------------------------------ Lichtstimmungen (2.2)
LICHT = {"nacht": (0.055, 0.065, 0.15), "frueh": (0.9, 0.95, 1.05), "morgen": (1.06, 0.98, 0.86)}
LICHT_STANDARD = {"backstube": "frueh"}           # theke: ohne Feld 'licht' wie bisher (keine Toenung)
LICHT_AUSNAHMEN = ("ar_", "lea_brillen", "byte", "antenna", "codeseg", "screen_display", "trail", "bs_glut", "bs_window", "bs_neon",
                   "bs_moon", "bs_sun", "bs_glow", "helper", "spark", "sparkt", "bang", "pix", "badge", "digit")


def apply_licht(W):
    """Feld 'licht' pro Szene ('nacht' | 'frueh' | 'morgen') fuer die Sets backstube und theke.
    Die Regie kann W.licht_extra = [(f0, f1, set, stimmung), ...] setzen; diese Abschnitte haben Vorrang.
    Workbench kennt kein Licht: die Stimmung toent die Objektfarben aller Materialien (ausser Leuchtteilen und Byte)
    waehrend der Szene; die Backstube schaltet dazu Neonroehre, Fensterfarbe, Mond/Sonne, Lichtstrahl und Staub."""
    T = W.T
    spans = []
    for s in W.tl["scenes"]:
        mood = s.get("licht") or LICHT_STANDARD.get(s["set"])
        if s["set"] in ("backstube", "theke") and mood in LICHT:
            spans.append((s["f0"], s["f1"], s["set"], mood))
    extra = [tuple(e) for e in getattr(W, "licht_extra", [])]     # Regie: kurze Abschnitte (Flackern, Zeitraffer)
    spans = extra + spans
    W.licht_spans = spans
    if not spans:
        return

    def mood_at(f):
        for a, b, st, md in spans:
            if a <= f < b:
                return st, md
        return None, None

    def tint(f, k):
        st, md = mood_at(f)
        return LICHT[md][k] if md else 1.0
    lo, hi = min(a for a, _, _, _ in spans), max(b for _, b, _, _ in spans)
    for m in list(bpy.data.materials):
        if m.name.startswith(LICHT_AUSNAHMEN) or "_shellmat" in m.name or "_pixmat" in m.name or "_tipmat" in m.name \
                or "_ledmat" in m.name:
            continue
        for k in range(3):
            T.mul(m, "diffuse_color", lambda f, k=k: tint(f, k), lo - 1, hi, index=k)
    S = W.sets.get("backstube")
    if S is None or not any(st == "backstube" for _, _, st, _ in spans):
        return
    win = {"nacht": L.srgb("#3E5FA8"), "frueh": L.srgb("#9DB1D8"), "morgen": L.srgb("#FFE3A6")}
    neon_on, neon_off = L.srgb("#F2F8FF"), L.srgb("#2A2E3A")

    def bs_mood(f):
        st, md = mood_at(f)
        return md if st == "backstube" else None
    T.set(S.objs["window_mat"], "diffuse_color", lambda f: win.get(bs_mood(f) or "frueh"), lo - 1, hi)
    T.set(S.objs["neon_mat"], "diffuse_color", lambda f: neon_on if bs_mood(f) == "frueh" else neon_off, lo - 1, hi)
    T.set(S.objs["moon"], "scale", lambda f: (1, 1, 1) if bs_mood(f) == "nacht" else (0, 0, 0), lo - 1, hi)
    T.set(S.objs["sun"], "scale", lambda f: (1, 1, 1) if bs_mood(f) == "morgen" else (0, 0, 0), lo - 1, hi)
    T.set(S.objs["beams"]["moon"], "scale", lambda f: (1, 1, 1) if bs_mood(f) == "nacht" else (0, 0, 0), lo - 1, hi)
    T.set(S.objs["beams"]["sun"], "scale", lambda f: (1, 1, 1) if bs_mood(f) == "morgen" else (0, 0, 0), lo - 1, hi)
    # Mehlstaub tanzt im Morgenlicht (im Lichtstrahl)
    wpos, tgt = S.objs["window"], S.objs["beam_target"]
    motes = PR.ambient_motes(T, W.coll, "bs_beamdust", tuple(wpos.lerp(tgt, 0.55)), (0.45, 0.35, 0.45), 40, 2201, lo, hi,
                             drift=0.05, scale=0.9)
    for o in motes:
        T.mul(o, "scale", lambda f: (1.0,) * 3 if bs_mood(f) == "morgen" else (0.0,) * 3, lo, hi)
    for lt in S.lights:
        e0 = lt.data.energy
        T.set(lt.data, "energy", lambda f, e0=e0: e0 * {"nacht": 0.15, "frueh": 0.9, "morgen": 1.1}.get(bs_mood(f), 1.0),
              lo - 1, hi)


def glut(T, S, f0, f1, level_fn, seed=0):
    """Ofenglut der Backstube: Flackern (Farbe und Groesse der Glutstuecke), Staerke level_fn(f) 0..1."""
    r = random.Random(seed)
    hot, cold = L.srgb("#FFB347"), L.srgb("#3A1A10")
    base = L.srgb("#FF7A2E")

    def col(f):
        lv = max(0.0, min(1.0, level_fn(f)))
        fl = 0.85 + 0.15 * math.sin(f * 0.9 + 1.3) * math.sin(f * 0.37)
        c = tuple(cold[k] + (base[k] - cold[k]) * lv * fl for k in range(3))
        if lv > 0.85:
            t = (lv - 0.85) / 0.15
            c = tuple(c[k] + (hot[k] - c[k]) * t * fl for k in range(3))
        return c + (1.0,)
    T.set(S.objs["glut_mat"], "diffuse_color", col, f0, f1)
    for k, e in enumerate(S.objs["embers"]):
        ph = r.uniform(0, 6.28)
        T.set(e, "scale", lambda f, ph=ph: ((0.55 + 0.45 * max(0.0, min(1.2, level_fn(f)))) * (1 + 0.15 * math.sin(f * 0.6 + ph)),) * 3,
              f0, f1)
    T.set(S.objs["glut_light"].data, "energy", lambda f: 160 * max(0.05, level_fn(f)), f0, f1)


# =================================================================== STUDIO
def build_studio(coll, screen_dir=None, n_frames=1):
    S = SetData("studio", ORIGIN["studio"])
    c = coll
    m_floor = L.mat("studio_floor", "#17142C", 0.32, spec=0.5)
    L.cyl("studio_floor", 9.0, 0.04, 48, m_floor, None, S.p(0, 0.5, -0.02), c)
    # Boden mit dezentem tuerkisem Gitter
    m_grid = L.mat("studio_grid", "#1E5A63", 0.5, emit=L.TURQ, strength=0.35)
    for k in range(-9, 10):
        L.box(f"studio_gx{k}", (0.012, 12.0, 0.004), m_grid, None, S.p(k * 0.5, 1.0, 0.002), c)
    for k in range(-10, 14):
        L.box(f"studio_gy{k}", (9.0, 0.012, 0.004), m_grid, None, S.p(0, k * 0.5, 0.002), c)
    # Rueckwand: dunkel mit leuchtenden Lamellen (Tiefe, kein leerer Hintergrund)
    L.box("studio_back", (16, 0.1, 8), L.mat("studio_back", "#1F1B3A", 0.7), None, S.p(0, 5.0, 3.5), c)
    for i in range(9):
        x = -4.0 + i * 1.0
        col = L.TURQ if i % 3 == 0 else L.VIOLET
        L.box(f"studio_lamella{i}", (0.05, 0.05, 5.5), L.mat(f"lamella{col}", col, 0.5, emit=col, strength=1.2), None,
              S.p(x, 4.9, 2.9), c)
    # Grosser schwebender Screen
    scr = L.empty("studio_screen", None, S.p(0.35, 3.0, 3.9), c)
    L.box("screen_frame", (3.45, 0.14, 2.05), L.mat("screen_frame", L.NAVY2, 0.5), scr, (0, 0, 0), c, bevel=0.06, seg=2)
    L.box("screen_edge", (3.55, 0.08, 2.15), L.mat("screen_edge", L.TURQ, 0.5, emit=L.TURQ, strength=2.0), scr,
          (0, 0.04, 0), c, bevel=0.06, seg=2)
    m_disp = bpy.data.materials.new("screen_display")
    nt = m_disp.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Roughness"].default_value = 0.5
    if screen_dir:
        import glob
        import os
        files = sorted(glob.glob(os.path.join(screen_dir, "*.png")))
        img = bpy.data.images.load(files[0])
        img.source = "SEQUENCE"
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.image_user.frame_duration = n_frames
        tex.image_user.frame_start = 1
        tex.image_user.frame_offset = 0
        tex.image_user.use_auto_refresh = True
        tex.interpolation = "Linear"
        nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Emission Strength"].default_value = 1.0
    S.screen_strength = b.inputs["Emission Strength"]
    disp = L.box("screen_display", (3.25, 0.02, 1.85), m_disp, scr, (0, -0.08, 0), c)
    # UV fuer die Front: einfache planare Projektion
    me = disp.data
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (v.x / 3.25 + 0.5, v.z / 1.85 + 0.5)
    S.objs["screen"] = scr
    sl = L.light("studio_screenlight", "AREA", 220, "#7FE8E0", S.p(0.35, 2.8, 3.6),
                 L.look_rot(S.p(0.35, 2.8, 3.6), S.p(0, -1, 1.6)), size=3.0, coll=c, cutoff=10, shadow=False)
    S.lights.append(sl)
    S.objs["screenlight"] = sl
    # Spot fuer Szene 7
    spot = L.light("studio_spot", "SPOT", 0, "#FFE7C2", S.p(0.3, -1.2, 5.8), L.look_rot(S.p(0.3, -1.2, 5.8), S.p(0.3, 0.2, 1.5)),
                   size=0.3, coll=c, cutoff=12, spot=0.7)
    S.lights.append(spot)
    S.objs["spot"] = spot
    _lights(S, c, key=(-3.0, -3.0, 4.0), fill=(3.4, -2.6, 1.8), rim=(2.4, 2.4, 3.2), rim2=(-2.6, 2.2, 3.0),
            key_e=900, fill_e=200, rim_e=700, rim2_e=520)
    S.kalle = S.p(-0.42, -0.6, 0.0)
    S.byte = S.p(0.0, -0.6, 2.2)
    return S


# ------------------------------------------------------------------ Kamera
class CamRig:
    """Kamera aus Shot-Funktionen: shot(f) -> (pos, ziel, brennweite). Dazu Handheld-Drift (Seed),
    Punch-ins (3 %, 6 Frames), Shakes und Whip-Pans (8 Frames, Gierwinkel)."""

    def __init__(self, sc, n_frames):
        cd = bpy.data.cameras.new("cam")
        cd.sensor_fit = "VERTICAL"
        cd.sensor_height = 36
        cd.clip_start = 0.05
        cd.clip_end = 80
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = 2.2
        self.cam = bpy.data.objects.new("cam", cd)
        sc.collection.objects.link(self.cam)
        sc.camera = self.cam
        self.cam.rotation_mode = "QUATERNION"
        self.focus = L.empty("cam_focus")
        cd.dof.focus_object = self.focus
        self.n = n_frames
        self.shots = []      # (f0, f1, fn)
        self.punch = []      # frames
        self.shakes = []     # (f, amp, dur)
        self.whips = []      # (frame_boundary, direction)
        self.focus_fn = None
        self.drift = (Noise(101, 3, 0.25), Noise(202, 3, 0.22), Noise(303, 3, 0.2), Noise(404, 2, 0.3))
        self.drift_amp = 1.0
        self._cache = {}

    def add_shot(self, f0, f1, fn):
        self.shots.append((f0, f1, fn))

    def base(self, f):
        for f0, f1, fn in self.shots:
            if f0 <= f < f1:
                return fn(f)
        f0, f1, fn = self.shots[-1] if f >= self.shots[-1][1] else self.shots[0]
        return fn(min(max(f, f0), f1 - 1))

    def state(self, f):
        if f in self._cache:
            return self._cache[f]
        b = self.base(f)
        pos, tgt, lens = b[0], b[1], b[2]
        roll_extra = b[3] if len(b) > 3 else 0.0
        pos, tgt = Vector(pos), Vector(tgt)
        t = f / FPS
        d = self.drift
        env = self.drift_env(f) if getattr(self, "drift_env", None) else 1.0
        a = 0.022 * self.drift_amp * env
        pos = pos + Vector((a * d[0](t), a * 0.5 * d[1](t), a * d[2](t)))
        tgt = tgt + Vector((a * 0.6 * d[1](t + 3), 0, a * 0.6 * d[0](t + 7)))
        roll = 0.012 * self.drift_amp * env * d[3](t) + roll_extra
        # Punch-ins (3 %, 6 Frames)
        for pf in self.punch:
            lens *= 1 + 0.03 * window(f, pf - 1, pf + 6, 2, 4)
        # Shakes
        for sf, amp, dur in self.shakes:
            if sf <= f <= sf + dur:
                k = 1 - (f - sf) / dur
                pos = pos + Vector((amp * k * math.sin(f * 2.7), 0, amp * k * math.cos(f * 3.3)))
        fwd = (tgt - pos).normalized()
        q = fwd.to_track_quat("-Z", "Y")
        # Whip-Pans: Gier-Offset um die Hochachse
        yaw = 0.0
        for wb, dirn in self.whips:
            if wb - 4 <= f < wb:
                yaw = dirn * 0.95 * ease_in((f - (wb - 4) + 1) / 4)
            elif wb <= f < wb + 4:
                yaw = -dirn * 0.95 * (1 - ease_out((f - wb + 1) / 4))
        if yaw:
            q = Quaternion((0, 0, 1), -yaw) @ q
        q = q @ Quaternion((0, 0, 1), roll)
        self._cache[f] = (pos, q, lens, tgt)
        return self._cache[f]

    def register(self, T):
        quats = {}
        prev = None
        for f in range(0, self.n):
            p, q, ln, tg = self.state(f)
            if prev is not None and prev.dot(q) < 0:
                q = -q
            quats[f] = q
            prev = q
        T.set(self.cam, "location", lambda f: tuple(self.state(int(f))[0]), 0, self.n - 1)
        T.set(self.cam, "rotation_quaternion", lambda f: tuple(quats[int(min(max(f, 0), self.n - 1))]), 0, self.n - 1)
        T.set(self.cam.data, "lens", lambda f: self.state(int(f))[2], 0, self.n - 1)
        if self.focus_fn:
            T.set(self.focus, "location", lambda f: tuple(self.focus_fn(int(f))), 0, self.n - 1)


# ------------------------------------------------------------------ Welt bauen
class World:
    pass


def build(tl, screen_dir):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    sc = bpy.context.scene
    W = World()
    W.tl = tl
    W.sc = sc
    W.n = tl["frames"]
    W.T = anim.Tracks(FPS)
    coll = sc.collection
    W.coll = coll
    W.sets = {"theke": build_theke(coll), "buero": build_buero(coll),
              "studio": build_studio(coll, screen_dir, W.n), "backstube": build_backstube(coll)}
    if any(s["set"] == "stadtkarte" for s in tl["scenes"]):      # 2.3: nur bauen, wenn die Folge es nutzt
        import stadtkarte as SK
        W.sets["stadtkarte"] = SK.build_stadtkarte(coll, ORIGIN["stadtkarte"])
    extras = tl["slug"] not in ("drei-helfer", "website")     # neue Merkmale ab dieser Folge
    W.kalle = C.Kalle(coll, extras=extras)
    W.byte = C.Byte(coll, light_energy=26.0)
    if extras:
        W.byte.add_ear_rings()
    W.lea = None
    if any(s["sprecher"] == "lea" for s in tl["scenes"]):       # 2.4: Lea nur bauen, wenn die Folge sie nutzt
        import lea as LE
        W.lea = LE.Lea(coll)
    W.helpers = [C.Helper(coll, 1, "scan"), C.Helper(coll, 2, "digits"), C.Helper(coll, 3, "feather")] \
        if tl["slug"] == "drei-helfer" else []
    W.cam = CamRig(sc, W.n)
    W.cues = []        # Soundeffekte: (frame, art)
    W.anchors = {}     # Name -> Objekt (fuer Overlay-Projektion)
    W.labels = []      # 3D-verankerte Overlay-Zahlen
    slug = tl["slug"].replace("-", "_")
    try:
        mod = importlib.import_module(f"choreo.{slug}")
    except ModuleNotFoundError:
        mod = importlib.import_module("choreo.generic")
    mod.direct(W)
    apply_licht(W)                                   # 2.2: Lichtstimmung pro Szene (Feld 'licht')
    W.cam.register(W.T)
    t0 = time.time()
    n = W.T.bake(0, W.n - 1, loop_frames=getattr(W, "loop_frames", 0))
    print(f"[scene] {n} Keys gebacken in {time.time()-t0:.1f}s", flush=True)
    return W


