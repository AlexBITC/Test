"""Regie fuer 'Byte macht Kalle viral' (folge-06-viral). Szenen-Index 0..13 = Szene 1..14.

Ablauf: Theke (Idee, Dreh) -> Theke-Laptop (Schnitt) -> Studio (Hook) -> Buero am Abend (Posten) -> Theke am Morgen.
Running Gags: Mini-Headset (Byte Szene 1 .. 13, Kalle Szene 14), Mehl auf der Technik (Szene 1, 5, 8).
Laptop als Zentrum: Bildschirm-Inhalte aus assets/screens/viral.py, per UV auf das Laptop-Display gelegt.
Kamera-Presets nie zweimal hintereinander. Requisiten: assets/props/viral.py.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

import characters as C
import look as L
import props as PR
from anim import (ease_in, ease_out, ease_in_out, ease_out_back, spring, window, pop, unpop, lerp)
from choreo.common import Ctx, path, V
from choreo.mehlpreis import harter_zoom, fahrt, push_in, vis

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "props"))
import viral as VP  # noqa: E402

FPS = 30
zoom_gesicht = rueckfahrt = schwenk = zoom = fahrt


def laptop_display(lap, aspect=1280 / 720):
    """Studio-Bildfolge (screen_display) auch auf das Laptop-Display legen: UV mit richtigem Seitenverhaeltnis."""
    m = bpy.data.materials.get("screen_display")
    if m is None:
        return
    me = lap.screen.data
    me.materials.clear()
    me.materials.append(m)
    uv = me.uv_layers.new(name="UVMap")
    w, h = 0.56, 0.34
    k = (w / h) / aspect
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (0.5 + v.x / w * k, 0.5 + v.z / h)


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    TH, ST, BU = c.sets["theke"], c.sets["studio"], c.sets["buero"]
    sc = c.sc
    S = [(s["f0"], s["f1"]) for s in sc]
    coll = W.coll
    cam = W.cam
    top = TH.top_z

    def hl(i, n=0):
        ws = [w["f0"] for w in sc[i]["words"] if w["hl"]]
        return ws[min(n, len(ws) - 1)] if ws else sc[i]["f0"] + 6

    def wd(i, core, nth=1):
        n = 0
        for w in sc[i]["words"]:
            if w["w"].strip(".,!?:…").lower() == core.lower():
                n += 1
                if n == nth:
                    return w["f0"]
        return sc[i]["f0"] + 4

    def cue(f, kind, g=1.0):
        c.cue(int(f), kind, g)

    W.anchors["kalle_face"] = L.empty("anchor_kalle_face", k.head, (0, -0.25, 0.28), coll)
    W.anchors["byte"] = b.body

    # ------------------------------------------------------------ Grundbewegung
    C.kalle_idle(T, k, 0, N - 1, seed=7)
    C.byte_idle(T, b, 0, N - 1, seed=3)
    C.byte_blinks(T, b, 0, N - 1, seed=11)
    C.antenna_spring(T, b, 2, N - 1)
    C.follow_through(T, k.hat, k.head, "rotation_euler", 2, 0.9, 3, 0, N - 1)
    C.follow_through(T, k.hat, k.head, "rotation_euler", 0, 0.7, 3, 0, N - 1)
    C.follow_through(T, k.skirt, k.hips, "rotation_euler", 1, 1.2, 4, 0, N - 1)
    C.follow_through(T, k.skirt, k.hips, "rotation_euler", 0, 1.0, 4, 0, N - 1)
    if getattr(k, "towel", None):
        C.follow_through(T, k.towel, k.hips, "rotation_euler", 1, 2.0, 5, 0, N - 1, out_idx=0)
    C.pose(T, k, "arms_rest", -10, None, 1, 1, weight=0.6, settle=False)
    for i, s in enumerate(sc):
        if s["sprecher"] == "kalle":
            C.kalle_lipsync(T, k, s, s["f0"], s["f1"])
        else:
            C.byte_speak(T, b, s, s["f0"], s["f1"])
        for w in s["words"]:
            if w["hl"]:
                cam.punch.append(w["f0"])
    cam.drift_env = lambda f: min(1.0, f / 10.0, max(0.0, (N - 7 - f) / 10.0))
    W.loop_frames = 0
    T.set(b.body, "rotation_euler", lambda f: (0, 0, 0), 0, 1)
    T.set(b.root, "rotation_euler", lambda f: (0, 0, 0), 0, 1)

    def set_kalle(f0, f1, loc, rz=0.0):
        T.set(k.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(k.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)

    def set_byte(f0, f1, loc):
        T.set(b.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)

    # ------------------------------------------------------------ Theke: Aufbau
    K = V(TH.kalle)
    face = K + V(0, -0.25, 1.95)
    theke = [i for i, s in enumerate(sc) if s["set"] == "theke"]
    for i in theke:
        set_kalle(S[i][0], S[i][1], K, 0.0)
    lap = TH.objs["laptop"]
    LAP = TH.p(0.45, -0.36, top)
    LS = 1.35
    lap.root.location = LAP
    lap.root.rotation_euler = (0, 0, math.radians(-18))
    lap.root.scale = (LS, LS, LS)
    laptop_display(lap)
    TH.objs["basket"].location.x += 0.45          # Brotkorb etwas zur Seite (Laptop frei)
    lap_rot = lap.root.rotation_euler.to_matrix()

    def lap_pt(x, y, z):
        return LAP + lap_rot @ V(x * LS, y * LS, z * LS)
    SCR = lap_pt(0, 0.2 + 0.2 * math.sin(math.radians(12)), 0.03 + 0.2 * math.cos(math.radians(12)))   # Display-Mitte
    lap_out = SCR + lap_rot @ V(0, -0.12, 0)          # direkt vor dem Display (Byte kommt heraus)
    W.anchors["laptop"] = L.empty("anchor_laptop", None, tuple(SCR), coll)
    PR.ambient_motes(T, coll, "th_dust", tuple(TH.p(0, 0.2, 1.9)), (2.2, 1.2, 0.9), 34, 601, 0, N - 1, drift=0.08)
    PR.ambient_motes(T, coll, "st_dust", tuple(ST.p(0, 0.6, 2.4)), (2.4, 1.6, 1.2), 30, 602, 0, N - 1,
                     color_kind="sparkt", drift=0.06, scale=0.6)
    PR.ambient_motes(T, coll, "bu_dust", tuple(BU.p(0.8, 0.2, 1.8)), (1.8, 1.0, 0.8), 24, 603, 0, N - 1, drift=0.05,
                     scale=0.8)
    # Tisch mit Brezelblech hinter Kalle
    L.box("blech_tisch", (1.2, 0.6, 0.9), L.mat("wood_dark", L.WOOD_DARK, 0.65), None, TH.p(-0.85, 1.0, 0.45), coll)
    blech = VP.brezelblech(coll, "blech")
    blech.root.location = TH.p(-0.85, 1.0, 0.9)
    # Fenster an der Rueckwand (Tageszeit: Tag, am Morgen danach Morgenlicht)
    fz_th = VP.fenster_tageszeit(coll, "fz_th", 0.75, 0.75)
    fz_th.root.location = TH.p(0.62, 2.36, 2.45)
    VP.tageszeit(T, fz_th, [(0, "tag"), (S[11][0] - 1, "tag"), (S[11][0], "morgen"), (N - 14, "morgen"), (N - 1, "tag")])

    # ------------------------------------------------------------ Byte: Headset, Mini-Kamera
    hs_b = VP.headset_mini(coll, "hs_byte")
    hs_b.root.parent = b.body
    hs_b.root.location = (0, 0.0, 0.0)
    cam_b = VP.mini_kamera(coll, "cam_byte")
    cam_b.root.parent = b.hand["R"]
    cam_b.root.location = (0.0, -0.03, -0.06)
    cam_b.root.rotation_euler = (math.pi / 2, 0, math.radians(10))
    C.byte_hand(T, b, "R", "grab", -10, None, ramp=1)
    VP.rec_blink(T, cam_b, 0, N - 1)
    # Mehl auf der Linse (Szene 1 drauf, Szene 5 weggewischt)
    m_fl = L.mat("puff", L.FLOUR, 0.9, emit=L.FLOUR, strength=0.35, alpha=0.45)
    flour_lens = L.empty("flour_lens", cam_b.root, (0.01, -0.075, 0), coll)
    rr = random.Random(5)
    for q in range(7):
        L.ico(f"flour_lens{q}", rr.uniform(0.008, 0.016), 1, (1, 0.5, 1), L.mat("flourspeck", "#FFFFFF", 0.8), flour_lens,
              (rr.uniform(-0.025, 0.03), 0, rr.uniform(-0.025, 0.025)), coll)

    # =================================================================== SZENE 1 – Byte schiesst aus dem Laptop (push_in)
    f0_1, f1_1 = S[0]
    STOP1 = face + V(0.46, -0.45, -0.2)
    brake = 13
    b1 = path([(-8, lap_out + V(0, 0.1, 0)), (0, lap_out + V(-0.02, -0.18, 0.12)), (brake - 4, STOP1 + V(0.05, -0.12, 0.05)),
               (brake, STOP1)], ease_out)
    T.set(b.root, "location", lambda f: b1(f), 0, S[1][0])
    T.set(b.root, "scale", lambda f: (min(1.0, 0.72 + 0.28 * ease_out((f + 3) / 8)),) * 3, 0, 8)
    T.mul(b.body, "scale", lambda f: (1 - 0.18 * window(f, brake - 1, brake + 10, 1, 8), 1,
                                      1 + 0.2 * window(f, brake - 1, brake + 10, 1, 8)), brake - 2, brake + 12)
    T.add(b.body, "rotation_euler", lambda f: (-0.5 * (1 - ease_out(min(1, f / brake))), 0, 0), 0, brake + 1)
    C.trail(T, coll, "s1trail", lambda f: b1(f), 0, brake + 4, n=8, size=0.06)
    C.byte_arm(T, b, "R", (-1.25, 0.2, 0.2), -4, S[1][0] + 10, ramp=4)          # haelt Kamera vor Kalles Gesicht
    C.byte_arm(T, b, "L", (-0.5, -1.1, 0.0), 2, f1_1 - 6, ramp=5)              # Arm ausgebreitet (Idee)
    # Kalle zuckt zurueck, Mehl staubt von der Schuerze
    flinch = brake - 1
    T.add(k.body, "location", lambda f: (0, 0.12 * window(f, flinch, flinch + 26, 3, 14), 0), flinch - 1, flinch + 27)
    T.add(k.hips, "rotation_euler", lambda f: (-0.16 * window(f, flinch, flinch + 26, 3, 14), 0, 0), flinch - 1, flinch + 27)
    T.add(k.head, "rotation_euler", lambda f: (-0.18 * window(f, flinch, flinch + 22, 2, 12), 0, 0), flinch - 1, flinch + 23)
    for side in ("R", "L"):
        T.mul(k.eye[side], "scale", lambda f: (1 + 0.5 * window(f, flinch, flinch + 20, 2, 10),) * 3, flinch, flinch + 21)
    PR.burst(T, coll, "s1flour", "puff", tuple(K + V(0, -0.42, 1.15)), flinch, 22, 1101, speed=(0.6, 1.4), up=0.5,
             gravity=-0.4, life=(22, 34), size=(1.0, 1.8), drag=3.0, ring=True)
    PR.burst(T, coll, "s1flour2", "flourdust", tuple(K + V(0, -0.42, 1.25)), flinch + 2, 12, 1102, speed=(0.8, 1.2),
             up=0.6, gravity=-1.0, life=(14, 20), size=(0.8, 1.2), dir_bias=(0.6, -0.5, 0.4))
    C.reaction(T, coll, k, "staunen", hl(0), hold=f1_1 - hl(0), seed=1)
    cue(0, "whoosh", 1.0)
    S1A = (TH.p(0.55, -4.1, 1.95), TH.p(0.05, 0.0, 1.62), 40.0)
    s1 = push_in(f0_1, f1_1, S1A, k=0.22)
    # schneller Push ab Frame 0: Kamera startet etwas weiter weg und faehrt in 30 Frames heran
    S1W = (TH.p(0.7, -4.9, 2.0), TH.p(0.05, 0.0, 1.62), 40.0)

    def shot1(f):
        t = ease_out(min(1.0, (f + 6) / 30))
        p0, t0_, l0 = S1W
        p1, t1_, l1 = s1(f)
        return (V(p0).lerp(V(p1), t), V(t0_).lerp(V(t1_), t), lerp(l0, l1, t))
    cam.add_shot(f0_1, f1_1, shot1)

    # =================================================================== SZENE 2 – Influencer? (zoom_gesicht)
    f0_2, f1_2 = S[1]
    STOP2 = STOP1 + V(0.05, -0.05, 0.0)
    push = wd(1, "koi") - 4
    b2 = path([(f0_2, STOP1), (push, STOP2), (push + 8, STOP2 + V(0.22, -0.12, 0.08)), (f1_2, STOP2 + V(0.25, -0.12, 0.1))],
              ease_in_out)
    T.set(b.root, "location", lambda f: b2(f), f0_2, S[2][0])
    cross = {"sh_R": (-0.45, 0, 0.9), "sh_L": (-0.45, 0, -0.9), "el_R": (-1.95, 0, 0), "el_L": (-1.95, 0, 0)}
    C.pose(T, k, cross, f0_2 + 2, push - 6, 6, 5)
    finger = {"sh_R": (-1.45, 0.15, -0.35), "el_R": (-0.25, 0, 0)}
    C.pose(T, k, finger, push - 5, push + 10, 5, 6)
    T.set(k.finger["R"], "scale", lambda f: (1, 1, 0.35 + 0.65 * window(f, push - 5, push + 12, 3, 5)), push - 6, push + 13)
    C.pose(T, k, cross, push + 11, f1_2 + 2, 6, 6)
    T.add(b.body, "rotation_euler", lambda f: (0, 0, -0.5 * window(f, push, push + 16, 2, 10)), push, push + 16)
    C.reaction(T, coll, k, "zweifel", hl(1) - 2, hold=f1_2 - hl(1) + 2, speaking=True, seed=2)
    T.add(k.stache, "rotation_euler", lambda f: (0, 0.18 * math.sin((f - f0_2) * 2.2) * window(f, f0_2 + 2, f0_2 + 18, 2, 6), 0),
          f0_2, f0_2 + 18)
    cue(hl(1), "buzz", 0.9)
    cam.add_shot(f0_2, f1_2, zoom_gesicht(f0_2, f1_2, (TH.p(-0.3, -4.2, 1.9), TH.p(-0.25, 0.0, 1.55), 40.0),
                                         (face + V(0.05, -3.1, 0.0), face + V(0.05, 0, -0.3), 50.0)))

    # =================================================================== SZENE 3 – Ringlicht und Regieklappe (rueckfahrt)
    f0_3, f1_3 = S[2]
    rl = VP.ringlicht(coll, "ringlicht")
    RL = TH.p(-0.55, -0.6, top)
    rl.root.location = RL
    rl.root.scale = (1.5,) * 3
    rl.root.rotation_euler = (0, 0, math.atan2(-(K.x - RL.x), (K.y - RL.y)) + math.pi)
    set_on = wd(2, "back") - 2
    rl_in = f0_3 + 4
    vis(T, rl.root, rl_in, S[7][1] + 2, base=1.5, dur_in=6, dur_out=2)
    VP.ringlicht_an(T, rl, set_on, S[7][1])
    B3 = RL + V(-0.42, -0.15, 0.78)
    b3 = path([(f0_3, STOP2 + V(0.25, -0.12, 0.1)), (rl_in + 6, RL + V(-0.1, -0.3, 0.95)), (set_on + 2, B3)], ease_in_out)
    T.set(b.root, "location", lambda f: b3(f), f0_3, S[3][0])
    C.byte_arm(T, b, "L", (-1.0, 0.6, 0.0), rl_in, set_on + 4, ramp=4)
    cue(set_on, "pop", 1.0)
    # Kalle im weichen Licht: Hautton, Hemd, Schuerze, Muetze heller (Workbench: Objektfarbe)
    for mn in ("skin", "skin_dark", "shirt", "apron", "hatwhite", "cheek"):
        m = bpy.data.materials.get(mn)
        if m is None:
            continue
        base = tuple(m.diffuse_color)
        lit = tuple(min(1.0, x * 1.16 + 0.03) for x in base[:3]) + (base[3],)
        T.set(m, "diffuse_color", lambda f, base=base, lit=lit:
              tuple(a + (bb - a) * window(f, set_on, S[7][1], 3, 2) for a, bb in zip(base, lit)), 0, N)
    # Mini-Regieklappe in Bytes linker Hand
    rk = VP.regieklappe_mini(coll, "klappe")
    rk.root.parent = b.hand["L"]
    rk.root.location = (0.0, -0.04, -0.12)
    rk.root.rotation_euler = (0, math.pi, 0)
    rk.root.scale = (0.85,) * 3
    clap = wd(2, "immer") + 4
    T.set(rk.root, "scale", lambda f: (0.85 * pop(f, set_on + 6, 5),) * 3 if f < clap + 14 else (0.85 * unpop(f, clap + 14, 5),) * 3,
          set_on + 5, clap + 20)
    T.set(rk.root, "scale", lambda f: (0, 0, 0), 0, 1)
    C.byte_arm(T, b, "L", (-1.6, -0.3, 0.0), set_on + 6, clap + 14, ramp=4)
    C.byte_hand(T, b, "L", "grab", set_on + 5, clap + 14)
    VP.klappe(T, rk, set_on + 10, clap)
    C.reaction(T, coll, k, "neutral", hl(2), seed=3)
    cam.add_shot(f0_3, f1_3, rueckfahrt(f0_3, f1_3, (face + V(-0.25, -2.9, -0.15), face + V(-0.25, 0, -0.45), 46.0),
                                       (TH.p(-0.15, -4.8, 1.85), TH.p(-0.15, 0.0, 1.45), 36.0), ease_out))

    # =================================================================== SZENE 4 – Brezel schlingen (schwenk Haende -> Byte)
    f0_4, f1_4 = S[3]
    braid0, braid1 = f0_4 + 4, f1_4 - 4
    knead = {"sh_R": (-1.1, 0, 0.45), "sh_L": (-1.1, 0, -0.45), "el_R": (-0.9, 0, 0), "el_L": (-0.9, 0, 0)}
    C.pose(T, k, knead, braid0 - 4, f1_4 - 2, 5, 6)
    for side, sx in (("R", -1), ("L", 1)):
        T.add(k.sh[side], "rotation_euler", lambda f, sx=sx: (0.22 * math.sin(f * 2.1 + sx), 0, sx * 0.25 * math.sin(f * 1.7))
              if braid0 <= f < braid1 else (0, 0, 0), braid0, braid1)
        T.add(k.el[side], "rotation_euler", lambda f, sx=sx: (0.3 * math.sin(f * 2.4 + 1 + sx), 0, 0)
              if braid0 <= f < braid1 else (0, 0, 0), braid0, braid1)
    for side in ("R", "L"):                     # blind: Augen zu beim Schlingen
        T.mul(k.eye[side], "scale", lambda f: (1, 1, 1 - 0.9 * window(f, braid0 + 2, braid1 - 2, 3, 3)), braid0, braid1)
    HANDS = K + V(0, -0.62, 1.32)
    rope = L.cyl("teigstrang", 0.03, 0.62, 8, L.mat("dough", "#EBD3A8", 0.7), None, tuple(HANDS), coll, axis="X")
    T.set(rope, "rotation_euler", lambda f: (0, 0.8 * math.sin(f * 1.9), f * 0.9), braid0, braid1)
    T.set(rope, "scale", lambda f: (1, 1, 1) if braid0 <= f < wd(3, "brezel") else (0, 0, 0), 0, N)
    done = wd(3, "brezel") + 1
    brz = PR.pastry(coll, "s4brezel", "brezel", None, tuple(HANDS + V(0, -0.05, -0.05)), 1.7)
    T.set(brz, "scale", lambda f: (1.7 * pop(f, done, 6, 1.25),) * 3 if f < f1_4 else (0, 0, 0), done - 1, f1_4 + 1)
    T.set(brz, "scale", lambda f: (0, 0, 0), 0, 1)
    PR.burst(T, coll, "s4flour", "flourdust", tuple(HANDS), braid0 + 2, 16, 1401, speed=(0.3, 0.8), up=0.5, gravity=-0.6,
             life=(16, 28), size=(0.6, 1.1))
    # Byte kreist mit der Kamera um Kalle
    orb_c = K + V(0, -0.2, 1.75)

    def orb(f):
        a = math.radians(lerp(195, -15, ease_in_out((f - f0_4) / max(1, f1_4 - f0_4))))
        return tuple(orb_c + V(0.95 * math.cos(a), 0.75 * math.sin(a), 0.1 * math.sin(f * 0.15)))
    T.set(b.root, "location", orb, f0_4, S[4][0])
    T.set(b.body, "rotation_euler", lambda f: (0, 0, math.atan2(-(orb_c - V(orb(f))).x, (orb_c - V(orb(f))).y) - 0.0),
          f0_4, f1_4)
    T.set(b.body, "rotation_euler", lambda f: (0, 0, 0), f1_4, f1_4 + 1)
    C.reaction(T, coll, k, "zweifel", hl(3) - 2, hold=f1_4 - hl(3), speaking=True, seed=4, hat=False)
    cam.add_shot(f0_4, f1_4, schwenk(f0_4, f1_4, (TH.p(-0.3, -3.3, 1.55), HANDS + V(0, 0, -0.05), 46.0),
                                     (TH.p(0.4, -3.6, 1.95), K + V(0.5, -0.6, 1.8), 42.0)))

    # =================================================================== SZENE 5 – Rohvideo (push_in auf den Laptop)
    f0_5, f1_5 = S[4]
    B5 = lap_pt(0.5, 0.02, 0.55)
    set_byte(f0_5, S[5][0], B5)
    wipe = wd(4, "mehl") - 4
    C.byte_arm(T, b, "R", (-1.2, -0.3, 0.6), f0_5 + 2, f1_5, ramp=5)
    C.byte_arm(T, b, "L", (-1.3, 0.2, -0.5), wipe - 4, wipe + 14, ramp=4)
    C.byte_hand(T, b, "L", "offen", wipe - 4, wipe + 14)
    T.add(b.arm["L"], "rotation_euler", lambda f: (0, 0, 0.45 * math.sin((f - wipe) * 0.9) * window(f, wipe, wipe + 12, 2, 3)),
          wipe, wipe + 13)
    T.set(flour_lens, "scale", lambda f: (1, 1, 1) if f < wipe + 6 else (0, 0, 0), 0, N)
    T.set(flour_lens, "scale", lambda f: (0, 0, 0), 0, flinch + 4)        # Mehl landet in Szene 1 auf der Linse
    T.set(flour_lens, "scale", lambda f: (pop(f, flinch + 4, 5),) * 3, flinch + 4, flinch + 10)
    T.set(flour_lens, "scale", lambda f: (1, 1, 1) if f < wipe + 6 else (0, 0, 0), flinch + 10, N)
    PR.burst(T, coll, "s5puff", "puff", tuple(B5 + V(-0.15, -0.3, -0.1)), wipe + 4, 12, 1501, speed=(0.4, 0.9), up=0.4,
             gravity=-0.3, life=(18, 26), size=(0.6, 1.1), drag=3.0)
    T.set(b.root, "rotation_euler", lambda f: (0, 0, math.radians(-25)), f0_5, S[7][0])
    T.set(b.root, "rotation_euler", lambda f: (0, 0, 0), S[7][0], S[7][0] + 1)
    C.reaction(T, coll, k, "neutral", hl(4), seed=5)
    cam.add_shot(f0_5, f1_5, push_in(f0_5, f1_5, (SCR + V(-0.3, -2.7, 0.42), SCR + V(0.2, 0, 0.08), 34.0), k=0.3))

    # =================================================================== SZENE 6 – Schnitt (zoom auf den Laptop-Bildschirm)
    f0_6, f1_6 = S[5]
    KB = lap_pt(0.36, -0.15, 0.03)
    B6 = lap_pt(0.55, 0.0, 0.3)
    hop = path([(f0_6, B5), (f0_6 + 5, (B5 + B6) / 2 + V(0, 0, 0.25)), (f0_6 + 10, B6)], ease_in_out)
    T.set(b.root, "location", lambda f: hop(f), f0_6, S[6][0])
    T.mul(b.body, "scale", lambda f: (1 + 0.16 * window(f, f0_6 + 9, f0_6 + 18, 1, 6), 1,
                                      1 - 0.18 * window(f, f0_6 + 9, f0_6 + 18, 1, 6)), f0_6 + 8, f0_6 + 18)
    type0, type1 = f0_6 + 11, f1_6 - 4
    C.byte_type(T, b, type0, type1, speed=4)
    T.add(b.root, "rotation_euler", lambda f: (0, 0, math.radians(30)), f0_6, f1_6)
    # Tasten leuchten unter Bytes Haenden
    m_key = L.mat("key_glow", "#9FF6EE", 0.4, emit=L.TURQ, strength=6.0)
    rk_ = random.Random(66)
    for q in range(16):
        kx, ky = rk_.uniform(-0.22, 0.24), rk_.uniform(-0.1, 0.06)
        key = L.box(f"keyglow{q}", (0.05, 0.04, 0.006), m_key, lap.root, (kx, ky, 0.036), coll)
        ph = rk_.randint(0, 5)
        T.set(key, "scale", lambda f, ph=ph: (1, 1, 1) if type0 <= f < type1 and ((f + ph) % 6) < 2 else (0, 0, 0), 0, N)
    cue(hl(5), "ding", 1.0)
    T.set(b.root, "rotation_euler", lambda f: (0, 0, 0), f0_6, f0_6 + 1)
    C.reaction(T, coll, k, "neutral", hl(5), seed=6)
    cam.add_shot(f0_6, f1_6, zoom(f0_6, f1_6, (SCR + V(-0.2, -2.9, 0.35), SCR + V(0.25, 0, -0.02), 36.0),
                                  (SCR + V(-0.05, -2.0, 0.22), SCR + V(0.22, 0, -0.06), 38.0), ease_out))

    # =================================================================== SZENE 7 – Effekte, Byte schnippt (fahrt am Laptop)
    f0_7, f1_7 = S[6]
    B7 = lap_pt(0.62, 0.1, 0.42)
    b7 = path([(f0_7, B6), (f0_7 + 8, B7)], ease_in_out)
    T.set(b.root, "location", lambda f: b7(f), f0_7, S[7][0])
    snaps = [wd(6, "zeitlupe") + 2, wd(6, "untertitel") + 2, wd(6, "musik") + 2]
    for q, fs in enumerate(snaps):
        C.byte_snap(T, b, "L", fs)
        cue(fs, "pop", 1.0)
        PR.burst(T, coll, f"s7snap{q}", "sparkt", tuple(B7 + V(-0.28, -0.12, 0.35)), fs, 8, 1701 + q, speed=(0.5, 1.0),
                 up=0.3, gravity=-0.5, life=(10, 16), size=(0.8, 1.2))
    C.reaction(T, coll, k, "neutral", hl(6), seed=7)
    cam.add_shot(f0_7, f1_7, fahrt(f0_7, f1_7, (SCR + V(-0.6, -2.35, 0.3), SCR + V(0.12, 0, 0.0), 38.0),
                                   (SCR + V(0.25, -2.35, 0.28), SCR + V(0.27, 0, 0.0), 38.0)))

    # =================================================================== SZENE 8 – Des bin ja i! (zoom_gesicht auf Kalle)
    f0_8, f1_8 = S[7]
    K8 = TH.p(-0.22, 0.02, 0.0)
    set_kalle(f0_8, f1_8, K8, 0.62)
    lean = {"hips": (0.24, 0, 0.1), "head": (-0.12, 0, 0.1), "sh_R": (-0.7, 0, 0.3), "sh_L": (-0.7, 0, -0.3)}
    C.pose(T, k, lean, f0_8 + 1, f1_8 + 2, 7, 6)
    T.add(k.body, "location", lambda f: (0.1 * window(f, f0_8 + 1, f1_8 + 2, 7, 6), 0, -0.28 * window(f, f0_8 + 1, f1_8 + 2, 7, 6)), f0_8, f1_8 + 2)
    # Muetze rutscht nach vorn
    T.add(k.hat, "location", lambda f: (0, -0.08 * window(f, hl(7) - 20, f1_8, 6, 4), -0.04 * window(f, hl(7) - 20, f1_8, 6, 4)),
          hl(7) - 20, f1_8)
    T.add(k.hat, "rotation_euler", lambda f: (0.35 * window(f, hl(7) - 20, f1_8, 6, 4), 0, 0), hl(7) - 20, f1_8)
    C.reaction(T, coll, k, "staunen", hl(7) - 2, hold=f1_8 - hl(7) + 2, speaking=True, seed=8, hat=False)
    for side in ("R", "L"):
        T.mul(k.eye[side], "scale", lambda f: (1 + 0.3 * window(f, f0_8 + 4, f1_8, 4, 3),) * 3, f0_8 + 4, f1_8)
    B8 = lap_pt(0.75, 0.05, 0.75)
    set_byte(f0_8, S[8][0], B8)
    C.byte_arm(T, b, "L", (-2.2, -0.5, 0.0), f0_8 + 6, f1_8 - 6, ramp=5)         # Daumen hoch
    C.byte_hand(T, b, "L", "point", f0_8 + 6, f1_8 - 6)
    # Mehl auf der Technik: Kalles Mehl staubt auf den Laptop
    PR.burst(T, coll, "s8flour", "puff", tuple(lap_pt(-0.2, -0.05, 0.08)), f0_8 + 10, 12, 1801, speed=(0.3, 0.8), up=0.5,
             gravity=-0.3, life=(20, 30), size=(0.7, 1.3), drag=3.0)
    specks = L.empty("laptop_flour", lap.root, (0, 0, 0), coll)
    for q in range(10):
        L.ico(f"laptop_flour{q}", rk_.uniform(0.008, 0.016), 1, (1, 1, 0.4), L.mat("flourspeck", "#FFFFFF", 0.8), specks,
              (rk_.uniform(-0.26, -0.05), rk_.uniform(-0.16, 0.05), 0.04), coll)
    T.set(specks, "scale", lambda f: (1, 1, 1) if f0_8 + 12 <= f < S[8][0] else (0, 0, 0), 0, N)
    cam.add_shot(f0_8, f1_8, zoom_gesicht(f0_8, f1_8, (TH.p(0.6, -3.7, 1.7), SCR + V(-0.42, 0, 0.12), 36.0),
                                         (TH.p(0.42, -2.7, 1.62), SCR + V(-0.48, 0, 0.14), 38.0)))
    W.anchors["kalle_face8"] = W.anchors["kalle_face"]

    # =================================================================== SZENE 9 – Studio: erstes Frame (push_in)
    f0_9, f1_9 = S[8]
    SCRN = ST.objs["screen"].location
    B9 = ST.p(-1.45, 0.4, 3.05)
    b9 = path([(f0_9, B9 + V(-0.6, -0.3, 0.3)), (f0_9 + 10, B9)], ease_out)
    T.set(b.root, "location", lambda f: b9(f), f0_9, S[9][0])
    point = wd(8, "erste") - 3
    C.byte_arm(T, b, "L", (-2.3, -0.9, 0.0), point, f1_9 - 4, ramp=5)
    C.byte_hand(T, b, "L", "point", point, f1_9 - 4)
    T.add(b.body, "rotation_euler", lambda f: (0, 0, 0.35 * window(f, point, f1_9, 5, 6)), point, f1_9)
    for i in (8,):
        set_kalle(S[i][0], S[i][1], ST.p(-6, 2, 0), 0.0)
    cue(f0_9 - 5, "whoosh", 1.0)
    cam.whips.append((f0_9, 1))
    cam.add_shot(f0_9, f1_9, push_in(f0_9, f1_9, (ST.p(-0.45, -5.6, 2.6), SCRN + V(-0.75, 0, -0.55), 31.0), k=0.2))
    # Requisiten im Studio: Ringlicht aus der Theke als Studiolicht, Klappe
    rl2 = VP.ringlicht(coll, "ringlicht_st")
    rl2.root.location = ST.p(1.75, -0.9, 0)
    rl2.root.scale = (3.4,) * 3
    rl2.root.rotation_euler = (0, 0, math.radians(-30))
    VP.ringlicht_an(T, rl2, 0)
    rk2 = VP.regieklappe_mini(coll, "klappe_st", "ERSTE SEKUNDE")
    rk2.root.location = ST.p(-1.9, -0.6, 0.0)
    rk2.root.scale = (4.0,) * 3
    rk2.root.rotation_euler = (0, 0, math.radians(18))

    # =================================================================== SZENE 10 – Buero am Abend, 18:00, POSTEN (schwenk)
    f0_10, f1_10 = S[9]
    for i in (9, 10):
        set_kalle(S[i][0], S[i][1], BU.p(-6, 2, 0), 0.0)
    fz = VP.fenster_tageszeit(coll, "fz_bu", 0.9, 1.1)
    fz.root.location = BU.p(2.85, 2.36, 2.0)
    VP.tageszeit(T, fz, [(0, "nacht"), (S[10][0] + 4, "nacht"), (S[10][1] - 18, "daemmerung"), (S[10][1], "morgen")])
    lamp = VP.schreibtischlampe(coll, "lampe")
    lamp.root.location = BU.p(1.45, 0.25, 0.98)
    lamp.root.rotation_euler = (0, 0, math.radians(200))
    clk = BU.objs["clock"]
    jump = wd(9, "18") - 3
    T.set(clk.hands[0], "rotation_euler", lambda f: (0, math.radians(lerp(357.5, 540, ease_out_back(min(1, max(0, (f - jump) / 8)), 1.4))), 0),
          0, N - 1)
    T.set(clk.hands[1], "rotation_euler", lambda f: (0, math.radians(lerp(330, 360, ease_out_back(min(1, max(0, (f - jump) / 8)), 1.4))), 0),
          0, N - 1)
    dig = L.text("uhr_18", "18:00", 0.2, L.mat("dig_gold", "#F2B45A", 0.4, emit="#F2B45A", strength=4.0), None,
                 tuple(clk.root.location + V(0, -0.05, -0.55)), coll, extrude=0.012, font=L.font())
    vis(T, dig, jump + 2, None, dur_in=6)
    pk = VP.posten_knopf(coll, "posten")
    PK = BU.p(0.45, -0.3, 0.98)
    pk.root.location = PK
    press = wd(9, "da") - 2
    VP.knopf_druecken(T, pk, press)
    B10 = PK + V(0.3, -0.05, 0.62)
    b10 = path([(f0_10, B10 + V(0.5, -0.4, 0.3)), (f0_10 + 12, B10), (press - 5, B10 + V(0, 0, 0.12)), (press, B10 - V(0, 0, 0.08)),
                (press + 8, B10)], ease_in_out)
    T.set(b.root, "location", lambda f: b10(f), f0_10, S[10][0])
    C.byte_arm(T, b, "R", (-0.9, 0.3, 0.0), press - 6, press + 8, ramp=3)
    C.byte_hand(T, b, "R", "offen", press - 6, press + 8)
    # Abend: dunkler Schleier vor der Kamera (Workbench hat kein Licht), Lampe und Fenster leuchten
    dim = L.box("abend_wand", (9.0, 0.002, 6.0), L.mat("abend", "#0B0A24", 0.9, alpha=0.5), None, BU.p(0, 2.435, 3.0), coll)
    T.set(dim, "scale", lambda f: (1, 1, 1) if S[9][0] <= f < S[10][1] else (0, 0, 0), 0, N)
    T.mul(dim, "scale", lambda f: (1 - ease_in_out((f - (S[10][1] - 24)) / 24),) * 3 if f > S[10][1] - 24 else (1, 1, 1),
          S[10][0], S[10][1])
    cue(f0_10 - 5, "whoosh", 1.0)
    cam.whips.append((f0_10, -1))
    CLK = clk.root.location
    cam.add_shot(f0_10, f1_10, schwenk(f0_10, f1_10, (BU.p(1.0, -3.0, 2.4), CLK + V(0, 0, -0.25), 40.0),
                                       (BU.p(0.8, -3.2, 2.05), PK + V(0.18, 0, 0.22), 40.0)))

    # =================================================================== SZENE 11 – 12.000 Aufrufe (harter_zoom auf den Zaehler)
    f0_11, f1_11 = S[10]
    az = VP.aufrufzaehler(coll, "zaehler")
    AZ = BU.p(-0.05, -0.15, 0.98)
    az.root.location = AZ + V(0, 0, 0.25 * 0.8)
    az.root.scale = (0.8,) * 3
    hit = hl(10)
    VP.zaehler_laufen(T, az, lambda f: 12000 * ease_out(min(1.0, max(0.0, (f - f0_11 - 2) / max(1, hit - f0_11)))), 0, N - 1)
    T.add(az.root, "location", lambda f: (0.006 * math.sin(f * 3.1), 0, 0.006 * math.cos(f * 2.7)) if f0_11 <= f < hit else (0, 0, 0),
          f0_11, hit)
    vis(T, az.root, f0_10 + 2, None, base=0.8)
    B11 = AZ + V(0.75, -0.1, 0.8)
    set_byte(f0_11, S[11][0], B11)
    hz = VP.herzchen(T, coll, "herz", tuple(AZ + V(0.0, -0.3, 0.55)), hit - 4, 16, 1111, f_end=f1_11 + 4)
    for q, (h_, t0) in enumerate(hz[::4]):
        cue(t0 + 1, "pop", 0.6)
    cue(hit, "ding", 1.0)
    cam.add_shot(f0_11, f1_11, harter_zoom(f0_11, f1_11, (BU.p(0.4, -3.6, 1.9), AZ + V(0.3, 0, 0.35), 38.0),
                                           (AZ + V(0.05, -1.9, 0.3), AZ + V(0.05, 0, 0.25), 44.0), hit - 3, dur=5))

    # =================================================================== SZENE 12 – Schlange am Morgen (rueckfahrt)
    f0_12, f1_12 = S[11]
    queue_pts = [TH.p(-1.25, -1.2, 0), TH.p(-1.75, -1.75, 0), TH.p(-2.15, -2.35, 0), TH.p(-2.5, -2.95, 0),
                 TH.p(-2.8, -3.55, 0), TH.p(-1.7, -2.9, 0), TH.p(-3.1, -4.15, 0)]
    kunden = VP.kunden_schlange(coll, "kunde", queue_pts, seed=12)
    for q, ku in enumerate(kunden):
        d = K + V(0, 0, 1.6) - ku.root.location
        ku.root.rotation_euler = (0, 0, math.atan2(d.x, -d.y))
        T.set(ku.root, "scale", lambda f, s0=ku.root.scale[0]: (s0,) * 3 if f0_12 - 1 <= f < S[13][0] else (0, 0, 0), 0, N)
        T.add(ku.body, "location", lambda f, q=q: (0, 0, 0.03 * max(0.0, math.sin(f * 0.35 + q))), f0_12, N - 1)
        if ku.phone is not None:
            T.add(ku.arm, "rotation_euler", lambda f, q=q: (0.08 * math.sin(f * 0.21 + q), 0, 0), f0_12, N - 1)
    tray = VP.brezelblech(coll, "blech_hand")
    tray.root.parent = k.hand["L"]
    tray.root.location = (0.3, 0.0, -0.18)
    tray.root.scale = (0.9,) * 3
    hold12 = {"sh_R": (-1.3, 0, 0.35), "sh_L": (-1.3, 0, -0.35), "el_R": (-0.6, 0, 0), "el_L": (-0.6, 0, 0)}
    C.pose(T, k, hold12, f0_12 - 2, S[12][1], 1, 6, settle=False)
    drop = hl(11) - 2
    T.set(tray.root, "rotation_euler", lambda f: (math.pi / 2 + 0.9 * window(f, drop, drop + 16, 3, 9) * (1 + 0.2 * math.sin((f - drop) * 1.3)), 0,
                                                  0.3 * window(f, drop, drop + 16, 3, 9)), f0_12, S[12][1])
    T.set(tray.root, "scale", lambda f: (0.9,) * 3 if f0_12 <= f < S[12][1] else (0, 0, 0), 0, N)
    PR.burst(T, coll, "s12crumbs", "crumb", tuple(K + V(0.3, -0.6, 1.35)), drop + 4, 10, 1201, speed=(0.3, 0.7), up=0.3,
             gravity=-5.0, life=(14, 20), size=(1.0, 1.5))
    T.set(rl.root, "scale", lambda f: (0, 0, 0), S[8][0], N)
    B12 = TH.p(-1.18, -0.5, top + 0.82)
    set_byte(f0_12, S[12][0], B12)
    C.reaction(T, coll, k, "schock", hl(11), hold=f1_12 - hl(11), speaking=True, seed=12)
    cue(f0_12 - 5, "whoosh", 1.0)
    cue(hl(11), "buzz", 1.0)
    cam.whips.append((f0_12, 1))
    cam.add_shot(f0_12, f1_12, rueckfahrt(f0_12, f1_12, (face + V(-0.35, -3.0, 0.0), face + V(-0.3, 0, -0.35), 46.0),
                                         (TH.p(1.1, -6.3, 2.5), TH.p(-0.85, -1.0, 1.45), 32.0), ease_out))

    # =================================================================== SZENE 13 – Reichweite, Byte auf der Kasse (zoom_gesicht)
    f0_13, f1_13 = S[12]
    REG = TH.objs["register"].location
    B13 = REG + V(0.02, -0.05, 0.78)
    set_byte(f0_13, S[13][0] + 4, B13)
    T.add(b.bob, "location", lambda f: (0, 0, -0.03), f0_13, S[13][0] + 4)
    T.set(b.root, "rotation_euler", lambda f: (0, math.radians(-10), math.radians(15)), f0_13, S[13][0] + 4)
    T.set(b.root, "rotation_euler", lambda f: (0, 0, 0), S[13][0] + 4, S[13][0] + 5)
    for side, sx in (("R", -1), ("L", 1)):
        C.byte_arm(T, b, side, (0.5, -sx * 1.0, 0.0), f0_13, S[13][0] + 2, ramp=1)     # Arme laessig nach hinten
    # Headset im Nacken
    T.set(hs_b.root, "rotation_euler", lambda f: (1.25, 0, 0) if f0_13 <= f < S[13][0] + 8 else (0, 0, 0), 0, N)
    T.set(hs_b.root, "location", lambda f: (0, 0.05, -0.06) if f0_13 <= f < S[13][0] + 8 else (0, 0, 0), 0, N)
    drawer = TH.objs["drawer"]
    pops = [f0_13 + 6 + 22 * q for q in range(5)]
    T.set(drawer, "location", lambda f: (0, -0.3 * max([ease_out_back(min(1, max(0, (f - p) / 5)), 1.8) *
                                                         (1 - ease_in_out(min(1, max(0, (f - p - 12) / 6)))) for p in pops]), 0),
          f0_13, f1_13)
    for q, p in enumerate(pops):
        PR.burst(T, coll, f"s13coins{q}", "coinp", tuple(REG + V(0, -0.45, 0.15)), p + 2, 7, 1301 + q, speed=(0.9, 1.5),
                 up=1.3, gravity=-6.0, life=(16, 24), size=(0.9, 1.2), dir_bias=(0.2, -0.6, 0.4))
    cue(hl(12), "ding", 1.0)
    # Mini-Kamera liegt jetzt auf der Theke (Kalle schnappt sie in Szene 14)
    cam_t = VP.mini_kamera(coll, "cam_theke")
    CT = TH.p(-0.62, -0.52, top + 0.045)
    cam_t.root.location = CT
    cam_t.root.rotation_euler = (0, 0, math.radians(20))
    VP.rec_blink(T, cam_t, 0, N - 1)
    grab = wd(13, "hätt") - 2
    T.set(cam_t.root, "scale", lambda f: (1, 1, 1) if f0_13 <= f < grab else (0, 0, 0), 0, N)
    T.set(cam_b.root, "scale", lambda f: (0, 0, 0) if f0_13 <= f < N - 16 else (1, 1, 1), 0, N)
    C.reaction(T, coll, k, "staunen", hl(12) + 6, hold=f1_13 - hl(12) - 6, seed=13)
    cam.add_shot(f0_13, f1_13, zoom_gesicht(f0_13, f1_13, (TH.p(0.3, -3.9, 2.45), B13 + V(0.35, 0, -0.3), 38.0),
                                           (TH.p(-0.25, -2.55, 2.25), B13 + V(0.05, 0, -0.1), 44.0)))

    # =================================================================== SZENE 14 – Kalle hat eine Idee (fahrt -> Startposition)
    f0_14, f1_14 = S[13]
    C.pose(T, k, {"sh_R": (-1.2, 0.3, -0.2), "el_R": (-0.6, 0, 0)}, grab - 6, N + 10, 5, 8)
    cam_k = VP.mini_kamera(coll, "cam_kalle")
    cam_k.root.parent = k.hand["R"]
    cam_k.root.location = (0, -0.06, -0.1)
    cam_k.root.rotation_euler = (math.pi / 2, 0, 0)
    cam_k.root.scale = (1.4,) * 3
    VP.rec_blink(T, cam_k, 0, N - 1)
    T.set(cam_k.root, "scale", lambda f: (1.4,) * 3 if f >= grab else (0, 0, 0), 0, N)
    # Headset fliegt von Byte auf Kalles Kopf
    swap0 = wd(13, "da") - 2
    swap1 = swap0 + 9
    hs_f = VP.headset_mini(coll, "hs_fly")
    hs_k = VP.headset_mini(coll, "hs_kalle")
    hs_k.root.parent = k.head
    hs_k.root.location = (0, 0.02, 0.33)
    hs_k.root.scale = (1.42,) * 3
    T.set(hs_k.root, "scale", lambda f: (1.42 * (1 + 0.12 * spring((f - swap1) / FPS, 4, 0.3)),) * 3 if f >= swap1 else (0, 0, 0), 0, N)
    T.set(hs_b.root, "scale", lambda f: (0, 0, 0) if swap0 <= f < N - 1 else (1, 1, 1), 0, N)
    kh = lambda f: V(T.loc(k.root, f)) + V(0, 0.02, 2.24)          # noqa: E731
    T.set(hs_f.root, "location", lambda f: tuple(B13.lerp(kh(f), ease_in_out((f - swap0) / 9)) +
                                                 V(0, 0, 0.35 * math.sin(math.pi * min(1, max(0, (f - swap0) / 9))))), swap0, swap1)
    T.set(hs_f.root, "scale", lambda f: (lerp(1.0, 1.42, ease_in_out((f - swap0) / 9)),) * 3 if swap0 <= f < swap1 else (0, 0, 0), 0, N)
    T.set(hs_f.root, "rotation_euler", lambda f: (0, 0, 2 * math.pi * ease_in_out((f - swap0) / 9)), swap0, swap1)
    # Grinsen, zum Laptop drehen
    turn = hl(13) - 4
    T.set(k.root, "rotation_euler", lambda f: (0, 0, 0.55 * ease_in_out((f - turn) / 10)), f0_14, N)
    C.kalle_react(T, k, "jubel", hl(13), hold=N - hl(13) - 8, speaking=True, hat=False)
    # Byte taucht wieder in den Laptop (Loop: Szene 1 schiesst er heraus)
    back = N - 16
    T.set(b.root, "location", lambda f: tuple(B13.lerp(lap_out + V(0, 0.1, 0), ease_in((f - back) / 12)) if f > back else B13), f0_14, N)
    T.set(b.root, "scale", lambda f: (1 - 0.28 * ease_in((f - back - 4) / 9),) * 3 if f > back + 4 else (1, 1, 1), back, N)
    C.trail(T, coll, "s14trail", lambda f: T.loc(b.root, f), back + 2, N - 1, n=6, size=0.05)
    cam.add_shot(f0_14, N, fahrt(f0_14, N - 7, (TH.p(-0.25, -3.6, 1.9), K + V(-0.15, 0, 1.7), 44.0), shot1(0)))
    cam.whips.append((f0_14, -1))

    # ------------------------------------------------------------ Bytes Display-Augen je Reaktion
    eyes = ["jubel", "zweifel", "neutral", "neutral", "staunen", "neutral", "jubel", "jubel", "neutral", "neutral",
            "staunen", "schock", "jubel", "jubel"]
    sched = [(0, "jubel")] + [(S[i][0], e) for i, e in enumerate(eyes)]
    sched += [(S[3][1] - 14, "wink"), (hl(10), "staunen"), (wd(4, "mehl"), "zweifel"), (wd(4, "mehl") + 14, "staunen")]
    C.byte_face(T, b, sched, 0, N - 1)

    def focus(f):
        i = next((j for j, s in enumerate(sc) if s["f0"] <= f < s["f1"]), len(sc) - 1)
        if i in (4, 5, 6):
            return V(SCR)
        if i in (8, 9, 10, 12):
            return V(T.loc(b.root, f))
        return V(T.loc(k.root, f)) + V(0, -0.25, 1.95)
    W.cam.focus_fn = focus
