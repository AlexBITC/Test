"""Regie fuer 'Viel verkauft, kein Geld'. Jede Beat-Aktion startet 3 Frames vor ihrem Wort
(timeline: beat_list[f_beat]), der Sound liegt exakt auf dem Wort (f_word). Szenen-Index 0..12 = Szene 1..13.
Wiederverwendet: Kalle/Byte, Sets, Licht, Kamera-Rig, Partikel, Mehlsack, Konfetti. Neu: siehe props.py."""
import math
import random

import bpy
from mathutils import Vector, Matrix

import characters as C
import look as L
import props as PR
from anim import (ease_in, ease_out, ease_in_out, ease_out_back, spring, window, pop, unpop, lerp, Noise)
from choreo.common import Ctx, path, pop_obj, V

FPS = 30


def rotz(v, a):
    return Matrix.Rotation(a, 3, "Z") @ Vector(v)


def lerp3(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def shot_lerp(f0, f1, A, B, ease=ease_in_out):
    def fn(f):
        t = ease((f - f0) / max(1, f1 - f0))
        return (lerp3(A[0], B[0], t), lerp3(A[1], B[1], t), lerp(A[2], B[2], t))
    return fn


def vis(T, obj, f_in, f_out, base=1.0, dur_in=8, dur_out=8, start_hidden=True):
    """Pop-in bei f_in, Scale-Down bei f_out (None = bleibt)."""
    pop_obj(T, obj, f_in, f_out, base=base, dur_in=dur_in, dur_out=dur_out)
    if start_hidden:
        T.set(obj, "scale", lambda f: (0, 0, 0), 0, 1)


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    TH, BU, ST = c.sets["theke"], c.sets["buero"], c.sets["studio"]
    sc = c.sc
    S = [(s["f0"], s["f1"]) for s in sc]
    coll = W.coll
    cam = W.cam

    def bt(i, wort):
        for x in sc[i]["beat_list"]:
            if x["wort"] == wort:
                return x["f_beat"]
        raise KeyError((i, wort))

    def wd(i, wort):
        return bt(i, wort) + 3

    # Sounds exakt auf dem Wort
    for s in sc:
        for x in s["beat_list"]:
            if x["sound"] and x["sound"] != "none":
                c.cue(x["f_word"], x["sound"], 1.0)

    # ------------------------------------------------------------ Anker
    W.anchors["kalle_face"] = L.empty("anchor_kalle_face", k.head, (0, -0.25, 0.28), coll)
    W.anchors["byte"] = b.body

    # ------------------------------------------------------------ Grundbewegung (wie bisher)
    C.kalle_idle(T, k, 0, N - 1, seed=7)
    C.byte_idle(T, b, 0, N - 1, seed=3)
    C.byte_blinks(T, b, 0, N - 1, seed=11)
    C.antenna_spring(T, b, 2, N - 1)
    C.byte_code_face(T, b, 0, N - 1)
    C.follow_through(T, k.hat, k.head, "rotation_euler", 2, 0.9, 3, 0, N - 1)
    C.follow_through(T, k.hat, k.head, "rotation_euler", 0, 0.7, 3, 0, N - 1)
    C.follow_through(T, k.skirt, k.hips, "rotation_euler", 1, 1.2, 4, 0, N - 1)
    C.follow_through(T, k.skirt, k.hips, "rotation_euler", 0, 1.0, 4, 0, N - 1)
    C.follow_through(T, k.towel, k.hips, "rotation_euler", 1, 2.0, 5, 0, N - 1, out_idx=0)
    C.pose(T, k, "arms_rest", -10, None, 1, 1, weight=0.6, settle=False)
    for i, s in enumerate(sc):
        if s["sprecher"] == "kalle":
            C.kalle_lipsync(T, k, s, s["f0"], s["f1"])
        else:
            C.byte_speak(T, b, s, s["f0"], s["f1"])
            C.kalle_look(T, k, lambda f: V(T.loc(b.root, f)) + V(T.loc(b.bob, f)), s["f0"], s["f1"], 0.8)
        for w in s["words"]:
            if w["hl"]:
                cam.punch.append(w["f0"])
    cam.drift_env = lambda f: min(1.0, f / 10.0, max(0.0, (N - 7 - f) / 10.0))

    def set_kalle(f0, f1, loc, rz=0.0):
        T.set(k.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(k.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)

    # ------------------------------------------------------------ Theke umbauen (nur diese Folge)
    top = TH.top_z
    reg = TH.objs["register"]
    reg.location = TH.p(-0.74, -0.44, top)
    drawer = TH.objs["drawer"]
    for o in bpy.data.objects:
        if o.name.startswith("reg_coin"):
            o.scale = (0, 0, 0)            # Schublade ist leer
    bk = TH.objs["basket"]
    bk.location = TH.p(-1.38, -0.42, top)
    lap = TH.objs["laptop"]
    T.set(lap.root, "scale", lambda f: (0, 0, 0), 0, 1)
    vit = PR.vitrine(coll, "vitrine")
    vit.root.location = TH.p(0.3, -0.5, top)
    K = TH.p(-0.3, 0.3, 0)
    set_kalle(0, S[3][0], K, 0.0)
    set_kalle(S[10][0], N, K, 0.0)
    B_TH = TH.p(0.27, 0.0, 2.08)                      # rechts neben Kalles Kopf (0,55 BU)
    OUT_R = TH.p(2.6, -0.6, 2.3)                      # ausserhalb rechts
    face_w = lambda: V(K) + V(0, -0.25, 1.95)          # noqa: E731
    # Kassentaste druecken: rechte Hand auf der Taste (Frame 1 und Loop-Ende)
    press = {"sh_R": (-0.95, 0.42, 0.28), "el_R": (-0.75, 0, 0), "hips": (-0.04, 0, 0.05), "head": (0.08, 0, 0.06)}
    hand_env = {}

    def press_w(f):
        a = 1.0 - ease_in_out((f - 4) / 10) if f < 16 else 0.0
        e = S[12][0] + 0
        nb = wd(12, "nicht") - 3
        if f >= nb:
            a = ease_in_out((f - nb) / 10)
        return a
    for jn, rot in press.items():
        j = C.joint(k, jn)
        T.add(j, "rotation_euler", lambda f, rot=rot: tuple(r * press_w(f) for r in rot), 0, N - 1)
    hand_env["press"] = press_w
    # Taste geht beim Druck runter
    key = bpy.data.objects.get("reg_key11")
    if key:
        T.add(key, "location", lambda f: (0, 0, -0.012 * (window(f, -1, 6, 1, 4) + window(f, N - 8, N + 4, 3, 1))),
              0, N - 1)
    # Schublade: 5 % offen im ersten Frame (in Bewegung), springt auf 'verkauft' auf 100 %, bleibt offen bis
    # Szene 11 (zu), am Loop-Ende geschlossen
    d_open = bt(0, "verkauft")

    def drawer_d(f):
        if f < d_open:
            return 0.05 + 0.02 * ease_out(f / max(1, d_open))
        if f < S[10][0]:
            return 0.07 + 0.93 * ease_out_back(min(1, (f - d_open) / 6), 1.70158 * 0.8)
        return 0.0
    T.set(drawer, "location", lambda f: (0, -0.3 * drawer_d(f), 0), 0, N - 1)

    # =================================================================== SZENE 1 – Hook
    f0_1, f1_1 = S[0]
    A1 = (TH.p(-0.2, -4.6, 1.85), TH.p(-0.2, 0.3, 1.6), 50.0)
    geld = wd(0, "Geld")
    face_z = (face_w() + V(0, -4.1, 0.05), face_w() + V(0, 0, -0.18), 85.0)

    def shot1(f):
        pos, tgt = A1[0], A1[1]
        lens = 50.0 * (1 + 0.03 * ease_out(f / 20))
        if f >= geld - 1:
            t = ease_out((f - (geld - 1)) / 4)
            pos, tgt, lens = pos.lerp(face_z[0], t), tgt.lerp(face_z[1], t), lerp(lens, 85.0, t)
        return (pos, tgt, lens)
    cam.add_shot(f0_1, f1_1, shot1)
    T.set(b.root, "location", lambda f: tuple(OUT_R), 0, S[2][0])
    T.set(b.root, "scale", lambda f: (0, 0, 0), 0, 1)
    # 'verkauft': linke Hand zeigt auf die Vitrine (4 Frames Antizipation, 6 Frames Nachschwingen)
    pv = bt(0, "verkauft")
    point = {"sh_L": (-1.25, -0.55, -0.25), "el_L": (-0.25, 0, 0), "hips": (0.04, 0, -0.1), "head": (0.12, 0, -0.18)}
    C.pose(T, k, {kk: tuple(-0.15 * x for x in v) for kk, v in point.items()}, pv - 4, pv, 2, 2, settle=False)
    C.pose(T, k, point, pv, S[1][0] + 10, 6, 10, overshoot=0.18)
    PR.burst(T, coll, "crumbs1", "crumb", tuple(vit.root.location + V(0.1, -0.2, vit.H)), pv + 3, 5, 501,
             speed=(0.2, 0.5), up=0.3, spread=0.6, gravity=-6.0, life=(20, 30), size=(0.9, 1.3), spin=6.0)
    # 'Kein': Motte flattert aus der Schublade (Bogen 0,5 BU nach oben links Richtung Kamera)
    mo = PR.moth(coll, "moth")
    mk = bt(0, "Kein")
    m0 = reg.location + V(0, -0.32, 0.1)
    mpath = path([(mk, m0), (mk + 8, m0 + V(-0.15, -0.25, 0.3)), (mk + 20, m0 + V(-0.4, -0.55, 0.55)),
                  (S[1][0] + 14, m0 + V(-1.4, -0.9, 1.6))], ease_in_out)
    T.set(mo.root, "location", lambda f: mpath(f), mk - 1, S[1][0] + 16)
    T.set(mo.root, "rotation_euler", lambda f: (0.3, 0.2 * math.sin(f * 0.5), 0.9 + 0.3 * math.sin(f * 0.3)), mk - 1,
          S[1][0] + 16)
    T.set(mo.root, "scale", lambda f: ((1, 1, 1) if mk <= f <= S[1][0] + 15 else (0, 0, 0)), 0, S[1][0] + 17)
    PR.moth_flap(T, mo, mk - 1, S[1][0] + 16)
    for q in range(4):
        PR.burst(T, coll, f"mothdust{q}", "dust", tuple(mpath(mk + 4 + 4 * q)), mk + 4 + 4 * q, 1, 520 + q,
                 speed=(0.05, 0.15), gravity=-0.3, life=(16, 22), size=(1.2, 1.6))
    # 'Geld': schock (Ruck, Augen x1,8, Pupillen klein, Muetze 0,6 BU hoch + 360 Grad, Landung 14 Frames)
    gb = bt(0, "Geld")
    C.reaction(T, coll, k, "schock", gb + 3, hold=S[1][0] + 8 - gb, speaking=True, seed=1, hat=False)
    for side in ("R", "L"):
        T.mul(k.eye[side], "scale", lambda f: (1 + 0.06 * window(f, gb + 3, S[1][0] + 8, 2, 8),) * 3, gb, S[1][0] + 10)
        pm = bpy.data.objects[f"k_pupil_{side}"]          # Pupillen-Mesh selbst verkleinern (bleibt vorn)
        T.mul(pm, "scale", lambda f: (1 - 0.4 * window(f, gb + 3, S[1][0] + 8, 2, 8),) * 3, gb, S[1][0] + 10)
    hl = 14

    def hat_up(f):
        t = (f - gb) / 14.0
        if t <= 0 or t >= 1:
            return 0.0
        return 0.6 * 4 * t * (1 - t)
    T.add(k.hat, "location", lambda f: (0, 0, hat_up(f)), gb, gb + 15)
    T.add(k.hat, "rotation_euler", lambda f: (0, 0, 2 * math.pi * ease_in_out((f - gb) / 14)), gb, gb + 15)
    T.mul(k.hat, "scale", lambda f: (1 + 0.1 * spring((f - gb - hl) / FPS, 4, 0.3),
                                     1 + 0.1 * spring((f - gb - hl) / FPS, 4, 0.3),
                                     1 - 0.1 * spring((f - gb - hl) / FPS, 4, 0.3)), gb + hl, gb + hl + 16)
    sweat = L.sphere("sweat", 0.022, 8, 5, (0.8, 0.8, 1.35), L.mat("sweat", "#BFFFF8", 0.2, emit="#BFFFF8", strength=1.5),
                     k.head, (-0.29, -0.12, 0.36), coll)
    T.set(sweat, "location", lambda f: (-0.29, -0.12, 0.36 - 0.16 * ease_in((f - gb - 4) / 20)), gb, gb + 26)
    T.set(sweat, "scale", lambda f: (window(f, gb + 3, gb + 26, 3, 5),) * 3, gb, gb + 27)
    T.set(sweat, "scale", lambda f: (0, 0, 0), 0, 1)

    # =================================================================== SZENE 2
    f0_2, f1_2 = S[1]
    A2 = (face_z[0], face_z[1], 85.0)
    B2a = (face_w() + V(0.15, -4.4, 0.0), face_w() + V(0.15, 0, -0.3), 70.0)
    B2b = (face_w() + V(-0.05, -4.4, 0.0), face_w() + V(-0.05, 0, -0.3), 70.0)

    def shot2(f):
        if f < f0_2 + 8:
            return shot_lerp(f0_2, f0_2 + 8, A2, B2a, ease_out)(f)
        return shot_lerp(f0_2 + 8, f1_2, B2a, B2b, ease_in_out)(f)
    cam.add_shot(f0_2, f1_2, shot2)
    # 'Buero': Daumen ueber die Schulter zur Ladentuer, Buerofenster gegenueber leuchtet auf
    bb_ = bt(1, "Büro")
    thumb = {"sh_R": (-2.1, 0.9, 0.3), "el_R": (-1.6, 0, 0.3), "head": (0, 0, -0.2), "hips": (0, 0, -0.08)}
    C.pose(T, k, thumb, bb_, bt(1, "6") + 4, 6, 8)
    win = L.box("office_window", (0.34, 0.01, 0.26), L.unique_mat(L.mat("office_win", "#F2B45A", 0.5, emit="#F2B45A",
                                                                          strength=0.0), "office_win_m"),
                None, TH.p(1.75, 2.3, 1.7), coll)
    m_win = L.bsdf(win.data.materials[0]).inputs["Emission Strength"]
    T.set(m_win, "default_value", lambda f: 2.0 * ease_out((f - bb_) / 6), bb_, bb_ + 7)
    T.set(m_win, "default_value", lambda f: 0.0, 0, 1)
    win.data.materials[0].diffuse_color = L.srgb("#5C4A3A")
    T.set(win.data.materials[0], "diffuse_color", lambda f: tuple(L.srgb("#5C4A3A")[i] + (L.srgb("#F2B45A")[i] -
                                                                                           L.srgb("#5C4A3A")[i]) * ease_out((f - bb_) / 6) for i in range(4)),
          bb_, bb_ + 7)
    # '6': 6 Kalenderblaetter ueber dem Kopf, Stagger 3 Frames, flattern zu Boden
    b6 = bt(1, "6")
    rr = random.Random(66)
    for q in range(6):
        cs = PR.calendar_sheet(coll, f"cal{q}")
        base = face_w() + V(-0.42 + q * 0.17, -0.12, 0.62 + 0.05 * (q % 2))
        tq = b6 + 3 * q
        fall0 = b6 + 22 + 3 * q
        dx, rz = rr.uniform(-0.2, 0.2), rr.uniform(-2, 2)

        def cloc(f, base=base, fall0=fall0, dx=dx, q=q):
            if f < fall0:
                return tuple(base)
            t = (f - fall0) / FPS
            return tuple(base + V(dx * t + 0.05 * math.sin(7 * t + q), -0.1 * t, -1.8 * t * t))
        T.set(cs, "location", cloc, tq - 1, fall0 + 40)
        T.set(cs, "rotation_euler", lambda f, fall0=fall0, rz=rz: (0.3 * math.sin(0.4 * max(0, f - fall0)), 0,
                                                                   rz * max(0, f - fall0) / FPS), tq - 1, fall0 + 40)
        T.set(cs, "scale", lambda f, tq=tq, fall0=fall0: (pop(f, tq, 6) * (1 - ease_in((f - fall0 - 26) / 10)),) * 3,
              tq - 1, fall0 + 37)
        T.set(cs, "scale", lambda f: (0, 0, 0), 0, 1)
    # 'net': zweifel + Faust tippt zweimal auf die Theke, Broetchen huepfen
    bn = bt(1, "net")
    C.reaction(T, coll, k, "zweifel", bn + 3, hold=S[2][0] + 20 - bn, speaking=True, seed=2)
    T.add(k.mouth, "rotation_euler", lambda f: (0, 0.18 * window(f, bn, S[2][0] + 18, 3, 8), 0), bn, S[2][0] + 20)
    knock = {"sh_L": (-0.7, -0.2, 0), "el_L": (-0.9, 0, 0)}
    C.pose(T, k, knock, bn, bn + 16, 4, 6)
    T.add(k.sh["L"], "rotation_euler", lambda f: (0.18 * max(0, math.sin(math.pi * (f - bn - 4) / 4))
                                                   if bn + 4 <= f <= bn + 12 else 0, 0, 0), bn, bn + 14)
    for ri, rp in enumerate(TH.objs["rolls"]):
        for kn in (bn + 6, bn + 10):
            T.add(rp, "location", lambda f, ri=ri, kn=kn: (0, 0, 0.02 * max(0.0, math.sin(math.pi * (f - kn - 2 * ri) / 5))
                                                           if 0 <= f - kn - 2 * ri <= 5 else 0), kn, kn + 18)

    # =================================================================== SZENE 3 – Byte kommt
    f0_3, f1_3 = S[2]
    bh = bt(2, "hol")
    arr = bh + 14
    bpath = path([(bh, OUT_R), (bh + 7, TH.p(1.0, -0.9, 2.55)), (arr, B_TH)], ease_out)
    T.set(b.root, "location", lambda f: bpath(f), f0_3, f1_3)
    T.set(b.root, "scale", lambda f: (1, 1, 1) if f >= bh else (0, 0, 0), f0_3, bh + 1)
    T.mul(b.body, "scale", lambda f: (1 + 0.15 * window(f, arr - 2, arr + 8, 2, 6), 1,
                                      1 - 0.15 * window(f, arr - 2, arr + 8, 2, 6)), arr - 2, arr + 8)
    C.trail(T, coll, "s3trail", lambda f: bpath(f), bh, arr + 4, n=8, size=0.06)
    cheek = L.light("byte_cheek", "POINT", 0, L.TURQ, tuple(V(K) + V(0.05, -0.35, 1.9)), size=0.2, coll=coll,
                    shadow=False, cutoff=2)
    T.set(cheek.data, "energy", lambda f: 30 * ease_out((f - arr) / 8) if f < S[3][0] else 0, arr, S[3][0] + 1)
    T.set(cheek.data, "energy", lambda f: 0, 0, 1)
    bz = bt(2, "zurück")
    T.add(L.bsdf(b.m_shell).inputs["Emission Strength"], "default_value",
          lambda f: 2.6 * window(f, bz, bz + 16, 3, 10), bz, bz + 16)
    T.add(k.head, "rotation_euler", lambda f: (0, 0, -0.32 * window(f, bz, f1_3 + 2, 8, 6)), bz, f1_3 + 2)
    A3 = B2b
    B3 = (V(K) + V(0.3, -4.9, 1.85), V(K) + V(0.3, 0.0, 1.62), 50.0)
    cam.add_shot(f0_3, f1_3, lambda f: shot_lerp(f0_3, f0_3 + 12, A3, B3, ease_out)(f))
    cam.whips.append((S[3][0], 1))

    # =================================================================== SZENE 4 – Buero, Rechnungen
    f0_4, f1_4 = S[3]
    KB = BU.p(-0.05, 0.62, 0)
    set_kalle(S[3][0], S[5][0], KB, 0.12)
    desk_z = 0.98
    lapb = BU.objs["laptop"]
    lapb.root.location = BU.p(1.35, 0.05, desk_z)
    lapb.root.rotation_euler = (0, 0, math.radians(200))
    clk = BU.objs["clock"]
    clk.root.scale = (0, 0, 0)
    # Wand-Monitor mit Screen-Texturen
    mon = L.empty("buero_monitor", None, BU.p(0.62, 0.95, 3.08), coll)
    mon.scale = (1.6, 1.6, 1.6)
    L.cyl("mon_rod", 0.012, 1.2, 6, L.mat("antenna", L.METAL, 0.5, metallic=0.4), mon, (0, 0.03, 0.95), coll)
    L.box("mon_frame", (1.36, 0.06, 0.8), L.mat("screen_frame", L.NAVY2, 0.5), mon, (0, 0, 0), coll, bevel=0.03)
    L.box("mon_edge", (1.4, 0.04, 0.84), L.mat("screen_edge", L.TURQ, 0.5, emit=L.TURQ, strength=2.0), mon,
          (0, 0.02, 0), coll, bevel=0.03)
    disp_src = bpy.data.objects["screen_display"]
    md = L.box("mon_display", (1.28, 0.01, 0.72), disp_src.data.materials[0], mon, (0, -0.035, 0), coll)
    uv = md.data.uv_layers.new(name="UVMap")
    for poly in md.data.polygons:
        for li in poly.loop_indices:
            vv = md.data.vertices[md.data.loops[li].vertex_index].co
            uv.data[li].uv = (vv.x / 1.28 + 0.5, vv.z / 0.72 + 0.5)
    # Ordner (Ruecken #19A99D), aufgeklappt
    fold = L.empty("folder", None, BU.p(0.35, -0.15, desk_z), coll)
    m_f = L.mat("folder_teal", "#19A99D", 0.55)
    L.box("folder_l", (0.3, 0.36, 0.012), m_f, fold, (-0.16, 0, 0.006), coll)
    L.box("folder_r", (0.3, 0.36, 0.012), m_f, fold, (0.16, 0, 0.006), coll)
    L.box("folder_spine", (0.04, 0.37, 0.03), L.mat("folder_spine", "#14857C", 0.55), fold, (0, 0, 0.015), coll)
    L.box("folder_paper", (0.26, 0.32, 0.02), L.mat("invoice_paper", PR.PAPER, 0.7), fold, (0.16, 0, 0.022), coll)
    B_BU = BU.p(0.78, -0.25, 1.62)
    T.set(b.root, "location", lambda f: tuple(B_BU), f0_4, S[4][0])
    br_ = bt(3, "Rechnungen")
    invs = []
    for q in range(3):
        iv = PR.invoice(coll, f"inv{q}")
        slot = BU.p(0.1 + q * 0.27, -0.6, 1.72 + 0.02 * (q == 1))
        t_in = br_ + 3 * q
        p0 = fold.location + V(0.16, 0, 0.05)
        T.set(iv.root, "location", lambda f, p0=p0, slot=slot, t_in=t_in: tuple(
            p0.lerp(slot, ease_out_back(min(1, max(0, (f - t_in) / 10)), 1.4)) +
            V(0, 0, 0.15 * math.sin(math.pi * min(1, max(0, (f - t_in) / 10))))), t_in - 1, S[3][1])
        T.set(iv.root, "rotation_euler", lambda f, t_in=t_in, q=q: (
            -math.pi / 2 * (1 - ease_out((f - t_in) / 10)), 0, (q - 1) * 0.12 * ease_out((f - t_in) / 10)),
            t_in - 1, t_in + 11)
        T.set(iv.root, "scale", lambda f, t_in=t_in: (min(1.0, pop(f, t_in, 6)),) * 3, t_in - 1, t_in + 7)
        T.set(iv.root, "scale", lambda f: (0, 0, 0), 0, 1)
        invs.append((iv, slot))
    scan = L.box("scanbar", (0.85, 0.01, 0.012), L.mat("scanbar", L.TURQ, 0.4, emit=L.TURQ, strength=6.0), None,
                 (0, 0, 0), coll)
    sc0 = br_ + 12
    T.set(scan, "location", lambda f: tuple(BU.p(0.37, -0.64, 1.88 - 0.32 * ease_in_out((f - sc0) / 10))), sc0 - 1,
          sc0 + 11)
    T.set(scan, "scale", lambda f: (window(f, sc0 - 1, sc0 + 11, 2, 2),) * 3, sc0 - 2, sc0 + 12)
    T.set(scan, "scale", lambda f: (0, 0, 0), 0, 1)
    b620 = bt(3, "620")
    for q, (iv, slot) in enumerate(invs):
        ts = b620 + 3 * q
        T.set(iv.stamp, "scale", lambda f, ts=ts: ((1 + 0.2 * spring((f - ts - 4) / FPS, 4, 0.35),
                                                    1, 1 - 0.2 * spring((f - ts - 4) / FPS, 4, 0.35))
                                                   if f >= ts + 4 else (pop(f, ts, 4),) * 3), ts - 1, ts + 20)
        T.set(iv.stamp, "rotation_euler", lambda f, ts=ts: (-1.2 * (1 - ease_in(min(1, (f - ts) / 4))), math.radians(-12), 0),
              ts - 1, ts + 5)
    b1860 = bt(3, "1.860")
    stack = PR.coin_stack(coll, "stack18", 18)
    stack.root.location = BU.p(0.38, -0.36, desk_z)
    stack.root.scale = (1.4, 1.4, 1.4)
    for q, (iv, slot) in enumerate(invs):
        t0 = b1860 + 2 * q
        T.set(iv.upper, "rotation_euler", lambda f, t0=t0: (2.6 * ease_in_out((f - t0) / 8), 0, 0), t0, t0 + 9)
        T.set(iv.lower, "rotation_euler", lambda f, t0=t0: (-2.4 * ease_in_out((f - t0) / 8), 0, 0), t0, t0 + 9)
        T.set(iv.root, "location", lambda f, t0=t0, slot=slot: tuple(slot.lerp(stack.root.location + V(0, 0, 0.2),
                                                                                ease_in((f - t0 - 6) / 8))), t0 + 6, t0 + 15)
        T.set(iv.root, "scale", lambda f, t0=t0: (unpop(f, t0 + 12, 4),) * 3, t0 + 11, t0 + 17)
    for q, cn in enumerate(stack.coins):
        tc = b1860 + 2 * q
        T.set(cn, "scale", lambda f, tc=tc: (min(1.0, ease_out((f - tc) / 4)),) * 3, tc - 1, tc + 5)
        T.set(cn, "scale", lambda f: (0, 0, 0), 0, 1)
    T.set(stack.root, "scale", lambda f: (1.4 * unpop(f, S[5][0] + 2, 4),) * 3, S[5][0], S[5][0] + 8)
    A4 = (BU.p(0.42, -5.4, 2.05), BU.p(0.42, 0.3, 2.05), 50.0)
    B4 = (BU.p(0.42, -5.4, 2.2), BU.p(0.42, 0.3, 1.95), 50.0)
    cam.add_shot(f0_4, f1_4, shot_lerp(f0_4, f1_4, A4, B4, ease_in_out))

    # =================================================================== SZENE 5 – Stoppuhr
    f0_5, f1_5 = S[4]
    B5 = V(KB) + V(0.55, -0.25, 2.05)
    T.set(b.root, "location", lambda f: tuple(B_BU.lerp(B5, ease_in_out((f - f0_5) / 10))), f0_5, S[5][0])
    sw = PR.stopwatch(coll, "stopwatch")
    sw.root.location = B5 + V(0.32, -0.05, 0.08)
    b2 = bt(4, "2")
    vis(T, sw.root, b2, S[5][0] - 2, dur_in=6)
    T.set(sw.hand, "rotation_euler", lambda f: (0, 2 * math.pi * (2 / 60) * ease_out_back(min(1, max(0, (f - b2 - 3) / 6)),
                                                                                        2.5), 0), b2, b2 + 10)
    bs = bt(4, "Sekunden")
    C.reaction(T, coll, k, "staunen", bs + 3, hold=f1_5 - bs + 4, speaking=True, seed=5)
    PR.burst(T, coll, "bang5", "bang", tuple(V(KB) + V(0, -0.2, 2.5)), bs + 3, 4, 551, speed=(0.8, 1.2), up=1.2,
             spread=0.9, gravity=-1.5, life=(16, 22), spin=1.0, drag=2.0)
    A5 = (V(KB) + V(0.3, -4.6, 2.0), V(KB) + V(0.3, 0, 1.72), 70.0)
    cam.add_shot(f0_5, f1_5, lambda f: (A5[0], A5[1], 70.0 * (1 + 0.06 * ease_out((f - f0_5) / 8))))
    cam.whips.append((S[5][0], 1))

    # =================================================================== SZENE 6 – Kontoglas
    f0_6, f1_6 = S[5]
    KS = ST.p(-0.32, -0.35, 0)
    set_kalle(S[5][0], S[10][0], KS, 0.25)
    GL = ST.p(0.45, 1.0, 1.85)
    ped = L.cyl("glass_ped", 0.34, 1.85, 20, L.mat("pedestal", "#2B2750", 0.5), None, ST.p(0.45, 1.0, 0.925), coll)
    gl = PR.konto_glas(coll, "kontoglas")

    def gl_pos(f):
        if f < S[7][0]:
            return GL
        if f < S[9][0]:
            return GL + V(-0.4, 0.4, 0) * ease_in_out((f - S[7][0]) / 14)
        if f < S[10][0]:
            return GL + V(-0.4, 0.4, 0) * (1 - ease_in_out((f - S[9][0]) / 14))
        return TH.p(0.98, -0.45, top)
    T.set(gl.root, "location", lambda f: tuple(gl_pos(f)), S[5][0], N)
    T.set(ped, "location", lambda f: tuple(gl_pos(f) - V(0, 0, 0.925)), S[5][0], S[10][0])
    vis(T, gl.root, f0_6, None, dur_in=8)
    vis(T, ped, f0_6, None, dur_in=8)
    mill = bt(5, "Mühle")
    sack = PR.flour_sack(coll, "sack6", label=True, scale=0.42)
    zet = PR.muehlrad_zettel(coll, "zettel")
    zet.root.parent = sack.body
    zet.root.location = (0.24, -0.2, 0.32)
    zet.root.rotation_euler = (0, 0.15, 0)
    zet.root.scale = (1 / 0.42 * 0.9,) * 3
    S6SACK = ST.p(1.05, 0.85, 1.85)
    ped2 = L.cyl("sack_ped", 0.3, 1.85, 16, L.mat("pedestal", "#2B2750", 0.5), None, ST.p(1.05, 0.85, 0.925), coll)
    vis(T, ped2, f0_6, S[10][0] - 4)

    def sack_pos(f):
        if f < S[10][0]:
            return S6SACK + V(0, 0, 2.2 * (1 - ease_in((f - (mill - 7)) / 10)) if f < mill + 3 else 0)
        return TH.p(1.38, -0.35, top)
    T.set(sack.root, "location", lambda f: tuple(sack_pos(f)), mill - 8, N)
    T.set(sack.root, "scale", lambda f: (0.42 if f >= mill - 7 else 0,) * 3, 0, mill - 6)

    def sq(f):
        if f < mill + 3:
            return (1, 1, 1)
        t = (f - mill - 3) / FPS
        sp = spring(t, 3.2, 0.3)
        return (1 + 0.2 * sp, 1 + 0.2 * sp, 1 - 0.2 * sp)
    T.set(sack.body, "scale", sq, mill - 8, mill + 25)
    PR.burst(T, coll, "s6flour", "puff", tuple(S6SACK + V(0, 0, 0.05)), mill + 3, 12, 601, speed=(0.8, 1.4), up=0.15,
             gravity=-0.6, life=(16, 24), size=(0.6, 1.1), drag=3.5, ring=True)
    b15 = bt(5, "1.500")
    T.set(gl.mark_mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], "default_value",
          lambda f: 2.0 * ease_out((f - b15) / 6), b15, b15 + 7)
    T.set(gl.mark_mat, "diffuse_color", lambda f: tuple(min(1.0, x * (1 + 1.2 * ease_out((f - b15) / 6)))
                                                       for x in L.srgb("#FF5A5F")[:3]) + (1,), b15, b15 + 7)
    b900 = bt(5, "900")
    fill_end = b900 + 24

    def level(f):
        if f < b900:
            return 0.0
        if f < S[10][0]:
            return 0.6 * ease_out((f - b900) / 24)
        return glass_level_11(f)
    falls = []
    for q in range(12):
        tq = b900 + 2 * q
        cn = PR.coin_small(coll, f"fall900_{q}")
        x0 = V(0.12 * math.cos(q * 2.3), 0.12 * math.sin(q * 2.3), 0)

        def floc(f, tq=tq, x0=x0):
            t = min(1.0, max(0.0, (f - tq) / 8))
            zz = lerp(0.9, 0.02 + level(tq + 8) * 0.58, ease_in(t))
            if f > tq + 8:
                zz += 0.025 * max(0.0, math.sin(math.pi * (f - tq - 8) / 5)) if f < tq + 13 else 0
            return tuple(gl_pos(f) + x0 + V(0, 0, zz))
        T.set(cn, "location", floc, tq - 1, tq + 14)
        T.set(cn, "rotation_euler", lambda f, q=q: (0.4 * math.sin(q), 0.3, q), tq - 1, tq + 14)
        T.set(cn, "scale", lambda f, tq=tq: (1, 1, 1) if tq <= f <= tq + 10 else (0, 0, 0), 0, tq + 11)
        falls.append(cn)
    b600 = bt(5, "600")
    T.set(gl.gap, "scale", lambda f: ((1, 1, (0.4 * (gl.H - 0.02)) * (0.35 + 0.65 * abs(math.cos(math.pi * (f - b600) / 6))))
                                      if b600 <= f < S[7][0] + 6 else (0, 0, 0)), 0, S[7][0] + 7)
    T.set(gl.gap, "scale", lambda f: ((1, 1, 0.4 * (gl.H - 0.02)) if S[9][0] <= f < S[10][0] else (0, 0, 0)),
          S[9][0], S[10][0] + 1)
    B6 = ST.p(2.15, 1.5, 3.1)
    T.set(b.root, "location", lambda f: tuple(B6), S[5][0], S[7][0])
    T.add(L.bsdf(b.m_shell).inputs["Emission Strength"], "default_value",
          lambda f: -0.35 * window(f, b600, b600 + 18, 3, 8), b600, b600 + 18)
    A6 = (ST.p(0.15, -6.6, 2.45), ST.p(0.2, 1.0, 2.55), 35.0)
    B6c = (ST.p(0.2, -6.2, 2.45), ST.p(0.2, 1.0, 2.55), 46.0)
    cam.add_shot(f0_6, f1_6, shot_lerp(f0_6, f1_6, A6, B6c, ease_in_out))

    # =================================================================== SZENE 7
    f0_7, f1_7 = S[6]
    bv = bt(6, "verkauft")
    C.reaction(T, coll, k, "zweifel", bv + 3, hold=f1_7 - bv, speaking=True, seed=7)
    C.pose(T, k, "scratch", bv - 2, f1_7 - 4, 6, 8)
    T.add(k.hat, "rotation_euler", lambda f: (0, 0.26 * window(f, bv, bv + 24, 4, 10) *
                                              (1 + 0.15 * math.sin((f - bv) * 0.9)), 0), bv, bv + 26)
    T.add(k.towel, "location", lambda f: (0, 0, -0.03 * window(f, bv + 2, f1_7 + 30, 3, 20)), bv, f1_7 + 30)
    C.kalle_look(T, k, lambda f: gl_pos(f) + V(0, 0, 0.3), f0_7, bv, 0.8)
    face_s = V(KS) + V(0, -0.25, 1.95)
    A7 = (face_s + V(0.25, -4.4, 0.05), face_s + V(0.25, 0, -0.25), 70.0)

    def shot7(f):
        a = math.radians(8) * ease_in_out((f - f0_7) / (f1_7 - f0_7))
        return (face_s + rotz(V(0.25, -4.4, 0.05), a), face_s + V(0.25, 0, -0.25), 70.0)
    cam.add_shot(f0_7, f1_7, shot7)
    T.set(b.root, "location", lambda f: tuple(V(KS) + V(0.6, -0.3, 2.1)), f0_7, S[7][0])

    # =================================================================== SZENE 8 – Erinnerung
    f0_8, f1_8 = S[7]
    SCR = ST.objs["screen"].location
    B8a, B8 = V(KS) + V(0.6, -0.3, 2.1), ST.p(1.7, 1.6, 3.0)
    T.set(b.root, "location", lambda f: tuple(path([(f0_8, B8a), (f0_8 + 8, ST.p(1.0, 0.2, 3.3)), (f0_8 + 16, B8)], ease_out)(f)),
          f0_8, f1_8)
    b3 = bt(7, "3")
    for q, (iv, slot) in enumerate(invs):
        ta = b3 + 3 * q
        dock = SCR + V(-0.8 + q * 0.5, -0.25, -0.62)
        st0 = ST.p(-0.3 + q * 0.4, -0.8, 1.8)

        def iloc(f, ta=ta, dock=dock, st0=st0):
            t = ease_in_out((f - ta) / 12)
            p = st0.lerp(dock, t)
            p.z += 0.5 * math.sin(math.pi * t)
            return tuple(p)
        T.set(iv.root, "location", iloc, ta - 1, S[8][0] + 2)
        T.set(iv.root, "rotation_euler", lambda f: (0, 0, 0), ta - 1, ta)
        T.set(iv.upper, "rotation_euler", lambda f: (0, 0, 0), ta - 1, ta)
        T.set(iv.lower, "rotation_euler", lambda f: (0, 0, 0), ta - 1, ta)
        T.set(iv.root, "scale", lambda f, ta=ta: ((lerp(1.0, 0.2 * 2.2, ease_in_out((f - ta) / 12)) * pop(f, ta - 1, 4),) * 3
                                                  if f < bt(7, "Tagen") + 2 else (unpop(f, bt(7, "Tagen") + 2, 4) * 0.44,) * 3),
              ta - 2, bt(7, "Tagen") + 8)
    bta = bt(7, "Tagen")
    mail = L.box("mailcard", (1.0, 0.01, 0.7), L.mat("mail_card", PR.PAPER, 0.6), None, (0, 0, 0), coll)
    env = PR.envelope_mail(coll, "env")
    mc = SCR + V(0, -0.35, 0)
    T.set(mail, "location", lambda f: tuple(mc), bta - 1, bta + 10)
    T.set(mail, "scale", lambda f: ((1 - 0.7 * ease_in_out((f - bta) / 8), 1, max(0.02, 1 - 0.75 * ease_in_out((f - bta) / 8)))
                                    if bta <= f < bta + 8 else (0, 0, 0)), bta - 1, bta + 9)
    T.set(mail, "scale", lambda f: (0, 0, 0), 0, 1)
    eout = path([(bta + 7, mc), (bta + 14, mc + V(0.6, -0.3, 0.4)), (bta + 28, mc + V(2.6, -0.6, 2.2))], ease_in)
    T.set(env.root, "location", lambda f: eout(f), bta + 6, bta + 29)
    T.set(env.root, "scale", lambda f: ((pop(f, bta + 6, 5) * 1.6,) * 3 if f < bta + 28 else (0, 0, 0)), bta + 5, bta + 29)
    T.set(env.root, "scale", lambda f: (0, 0, 0), 0, 1)
    T.set(env.flap, "rotation_euler", lambda f: (2.6 * (1 - ease_out((f - bta - 6) / 6)), 0, 0), bta + 5, bta + 13)
    PR.burst(T, coll, "envspark", "sparkt", tuple(mc + V(0.6, -0.3, 0.4)), bta + 12, 8, 801, speed=(0.3, 0.7), up=0.3,
             gravity=-0.5, life=(10, 16), size=(0.8, 1.2))
    A8 = (SCR + V(0.1, -8.6, -1.5), SCR + V(0.1, 0, -0.95), 50.0)

    def shot8(f):
        lens = 50.0 * (1 + 0.05 * ease_out((f - f0_8) / (f1_8 - f0_8)))
        tilt = math.radians(6) * ease_in_out((f - (bta + 4)) / 18) if f > bta + 4 else 0
        tgt = A8[1] + V(0, 0, 8.6 * math.tan(tilt))
        return (A8[0], tgt, lens)
    cam.add_shot(f0_8, f1_8, shot8)

    # =================================================================== SZENE 9
    f0_9, f1_9 = S[8]
    B9 = V(KS) + V(0.6, -0.3, 2.1)
    T.set(b.root, "location", lambda f: tuple(path([(f0_9, B8), (f0_9 + 6, ST.p(0.6, 0.4, 3.0)), (f0_9 + 12, B9)],
                                                    ease_in_out)(f)), f0_9, f1_9)
    bk_ = bt(8, "klar")
    T.add(k.head, "rotation_euler", lambda f: (0.12 * max(0, math.sin(math.pi * (f - bk_) / 6)) if bk_ <= f < bk_ + 12
                                               else 0, 0, 0), bk_, bk_ + 12)
    thumbs = {"sh_R": (-1.25, 0.3, 0.2), "el_R": (-1.5, 0, 0)}
    C.pose(T, k, {kk: tuple(-0.12 * x for x in v) for kk, v in thumbs.items()}, bk_ - 4, bk_, 2, 2, settle=False)
    C.pose(T, k, thumbs, bk_, bt(8, "nie") - 2, 6, 8, overshoot=0.2)
    T.set(k.finger["R"], "scale", lambda f: (1, 1, 0.35), 0, 1)
    bnie = bt(8, "nie")
    C.reaction(T, coll, k, "staunen", bnie + 3, hold=f1_9 - bnie + 4, speaking=True, seed=9)
    PR.burst(T, coll, "bang9", "bang", tuple(V(KS) + V(0, -0.2, 2.5)), bnie + 3, 5, 901, speed=(0.8, 1.2), up=1.2,
             spread=0.9, gravity=-1.5, life=(16, 22), spin=1.0, drag=2.0)
    heart = {"sh_L": (-1.05, -0.95, -0.2), "el_L": (-1.7, 0, -0.4)}
    C.pose(T, k, heart, bnie + 2, f1_9 + 4, 6, 6)
    face9 = V(KS) + V(0, -0.25, 1.95)
    A9 = (face9 + V(0.28, -4.4, 0.05), face9 + V(0.28, 0, -0.25), 70.0)
    cam.add_shot(f0_9, f1_9, lambda f: (A9[0], A9[1], 70.0 * (1 + 0.04 * ease_out((f - f0_9) / 10))))

    # =================================================================== SZENE 10 – Liquiditaet
    f0_10, f1_10 = S[9]
    B10 = gl_pos(S[9][0] + 20) + V(0.6, -0.2, 0.95)
    T.set(b.root, "location", lambda f: tuple(B9.lerp(B10, ease_in_out((f - f0_10) / 14))), f0_10, S[10][0])
    bl = bt(9, "Liquidität")
    T.set(gl.rim, "scale", lambda f: (ease_out((f - bl) / 8),) * 3 if f < S[10][0] else (0, 0, 0), bl - 1, S[10][0] + 1)
    T.add(L.bsdf(b.m_shell).inputs["Emission Strength"], "default_value", lambda f: 2.6 * window(f, bl, bl + 16, 3, 10),
          bl, bl + 16)
    bj = bt(9, "jetzt")
    T.add(gl.top, "location", lambda f: (0, 0, 0.03 * max(0.0, math.sin(math.pi * (f - bj) / 6)) if bj <= f < bj + 6 else 0),
          bj, bj + 7)
    T.mul(gl.fill, "scale", lambda f: (1, 1, 1 + 0.06 * max(0.0, math.sin(math.pi * (f - bj) / 6)) if bj <= f < bj + 6 else 1),
          bj, bj + 7)
    bvs = bt(9, "versprochenes")
    ghost = L.empty("ghostcol", None, (0, 0, 0), coll)
    m_gh = L.mat("ghost_gold", "#F2B45A", 0.5, emit="#F2B45A", strength=0.3, alpha=0.35)
    L.cyl("ghost_m", 0.16, 0.74, 16, m_gh, ghost, (0, 0, 0.37), coll)
    m_dash = L.mat("ghost_dash", "#F2B45A", 0.5, emit="#F2B45A", strength=2.0)
    for q in range(10):
        a = q * 2 * math.pi / 10
        L.box(f"ghost_dash_b{q}", (0.05, 0.012, 0.012), m_dash, ghost, (0.17 * math.cos(a), 0.17 * math.sin(a), 0.74), coll
              ).rotation_euler = (0, 0, a + math.pi / 2)
        L.box(f"ghost_dash_v{q}", (0.01, 0.01, 0.06), m_dash, ghost, (0.17 * math.cos(a), 0.17 * math.sin(a), 0.1 + 0.07 * (q % 8)),
              coll)
    gpos = GL + V(0.62, -0.05, 0)
    ghost.location = gpos
    poke = bvs + 16
    T.set(ghost, "scale", lambda f: ((ease_out((f - bvs) / 8),) * 3 if f < poke + 2 else (0, 0, 0)), bvs - 1, poke + 3)
    T.set(ghost, "scale", lambda f: (0, 0, 0), 0, 1)
    PR.burst(T, coll, "ghostpix", "pix", tuple(gpos + V(0, 0, 0.37)), poke + 2, 20, 1001, speed=(0.3, 0.8), up=1.2,
             spread=0.8, gravity=0.5, life=(26, 30), size=(0.8, 1.2), drag=1.0, dir_bias=(0.2, 0, 1.0))
    T.set(b.root, "location", lambda f: tuple(path([(bvs + 4, B10), (poke - 4, gpos + V(0.45, -0.3, 0.75)),
                                                    (poke, gpos + V(0.2, -0.2, 0.5)), (poke + 10, B10)], ease_in_out)(f)),
          bvs + 4, poke + 10)
    C10 = GL + V(-0.08, 0, 0.3)

    def shot10(f):
        a = math.radians(-6 + 12 * ease_in_out((f - f0_10) / (f1_10 - f0_10)))
        return (C10 + rotz(V(0, -5.9, 0.2), a), C10 + rotz(V(0, 0, -0.1), a), 35.0)
    cam.add_shot(f0_10, f1_10, shot10)
    cam.whips.append((S[10][0], -1))

    # =================================================================== SZENE 11 – Geld da
    f0_11, f1_11 = S[10]
    B11 = B_TH
    T.set(b.root, "location", lambda f: tuple(B11), f0_11, S[12][0])
    bgeld = bt(10, "Geld")
    bm = bt(10, "Mühle")
    b1260 = bt(10, "1.260")

    def glass_level_11(f):
        if f < bgeld + 4:
            return 0.6
        if f < bm:
            return 0.6 + 1.24 * ease_out((f - bgeld - 4) / 24)
        return 1.84 - 1.0 * ease_in_out((f - bm) / 15)
    glas_lvl = level
    PR.glas_level(T, gl, glas_lvl, S[5][0], N)
    env2 = PR.envelope_mail(coll, "env2")
    door = TH.p(1.75, 2.0, 1.6)
    over = TH.p(0.98, -0.45, top + 1.0)
    ein = path([(bgeld - 10, door), (bgeld - 2, over + V(0.3, 0.3, 0.3)), (bgeld + 2, over)], ease_out)
    T.set(env2.root, "location", lambda f: ein(f), bgeld - 11, bgeld + 30)
    T.set(env2.root, "scale", lambda f: ((1.4 * pop(f, bgeld - 10, 5),) * 3 if f < bgeld + 28 else (unpop(f, bgeld + 28, 4) * 1.4,) * 3),
          bgeld - 11, bgeld + 33)
    T.set(env2.root, "scale", lambda f: (0, 0, 0), 0, 1)
    T.set(env2.root, "rotation_euler", lambda f: (math.pi * ease_in_out((f - bgeld) / 6), 0, 0), bgeld - 1, bgeld + 7)
    T.set(env2.flap, "rotation_euler", lambda f: (-2.4 * ease_out((f - bgeld - 2) / 5), 0, 0), bgeld + 1, bgeld + 8)
    for q in range(24):
        tq = bgeld + 4 + q
        cn = PR.coin_small(coll, f"rain{q}")
        x0 = V(0.1 * math.cos(q * 1.7), 0.1 * math.sin(q * 1.7), 0)
        T.set(cn, "location", lambda f, tq=tq, x0=x0: tuple(over + x0 - V(0, 0, 0.1) +
                                                            V(0, 0, -0.9 * ease_in(min(1, (f - tq) / 7)))), tq - 1, tq + 8)
        T.set(cn, "rotation_euler", lambda f, q=q: (q * 0.7, q * 0.3, 0), tq - 1, tq + 8)
        T.set(cn, "scale", lambda f, tq=tq: (1, 1, 1) if tq <= f < tq + 7 else (0, 0, 0), 0, tq + 8)
    sackpos = TH.p(1.38, -0.35, top + 0.25)
    for q in range(10):
        tq = bm + q * 1.5
        cn = PR.coin_small(coll, f"stream{q}")
        a_, b_ = TH.p(0.98, -0.45, top + 0.9), sackpos

        def sloc(f, tq=tq, a_=a_, b_=b_):
            t = ease_in_out(min(1, max(0, (f - tq) / 15)))
            p = a_.lerp(b_, t)
            p.z += 0.45 * math.sin(math.pi * t)
            return tuple(p)
        T.set(cn, "location", sloc, tq - 1, tq + 16)
        T.set(cn, "scale", lambda f, tq=tq: (1, 1, 1) if tq <= f < tq + 15 else (0, 0, 0), 0, tq + 16)
    T.set(zet.check, "scale", lambda f: (pop(f, bm + 15, 6, 1.15),) * 3 if f < N - 30 else (unpop(f, N - 30, 4),) * 3,
          bm + 14, N - 25)
    T.set(gl.ring, "scale", lambda f: (ease_out((f - b1260) / 8),) * 3, b1260 - 1, b1260 + 9)
    T.set(gl.mark_g, "scale", lambda f: (ease_out((f - b1260) / 6),) * 3, b1260 - 1, b1260 + 7)
    T.set(gl.mark, "scale", lambda f: (1 - ease_out((f - b1260) / 6),) * 3, b1260 - 1, b1260 + 7)
    C.reaction(T, coll, k, "staunen", b1260 + 3, hold=f1_11 - b1260, seed=11)
    A11 = (TH.p(0.25, -4.9, 1.75), TH.p(0.25, 0.3, 1.5), 50.0)
    B11c = (TH.p(0.25, -4.9, 1.95), TH.p(0.25, 0.3, 1.62), 50.0)
    cam.add_shot(f0_11, f1_11, shot_lerp(f0_11, bm, A11, B11c, ease_out))

    tv = L.empty("theke_tv", None, TH.p(0.66, -0.15, 2.4), coll)
    tv.scale = (1.12, 1.12, 1.12)
    L.box("tv_frame", (1.5, 0.06, 0.88), L.mat("screen_frame", L.NAVY2, 0.5), tv, (0, 0, 0), coll, bevel=0.03)
    L.box("tv_edge", (1.54, 0.04, 0.92), L.mat("screen_edge", L.TURQ, 0.5, emit=L.TURQ, strength=2.0), tv,
          (0, 0.02, 0), coll, bevel=0.03)
    tvd = L.box("tv_display", (1.42, 0.01, 0.8), bpy.data.objects["screen_display"].data.materials[0], tv,
                (0, -0.035, 0), coll)
    uvt = tvd.data.uv_layers.new(name="UVMap")
    for poly in tvd.data.polygons:
        for li in poly.loop_indices:
            vv = tvd.data.vertices[tvd.data.loops[li].vertex_index].co
            uvt.data[li].uv = (vv.x / 1.42 + 0.5, vv.z / 0.8 + 0.5)
    vis(T, tv, S[10][0], S[11][0] + 4, dur_in=8, dur_out=8)

    # =================================================================== SZENE 12 – Jubel
    f0_12, f1_12 = S[11]
    bha = bt(11, "Ha")
    clap = {"sh_R": (-1.2, 0.55, 0.35), "sh_L": (-1.2, -0.55, -0.35), "el_R": (-0.9, 0, 0.4), "el_L": (-0.9, 0, -0.4)}
    C.pose(T, k, {kk: (v[0], v[1] * 1.35, v[2]) for kk, v in clap.items()}, bha - 4, bha, 3, 2, settle=False)
    C.pose(T, k, clap, bha, bha + 10, 2, 6)
    PR.burst(T, coll, "clapdust", "flourdust", tuple(V(K) + V(0, -0.55, 1.5)), bha + 3, 6, 1201, speed=(0.3, 0.6), up=0.6,
             gravity=-0.3, life=(14, 20), size=(0.8, 1.2), drag=2.0)
    bgo = bt(11, "Gold")
    C.reaction(T, coll, k, "jubel", bgo + 3, hold=S[12][0] + 8 - bgo, speaking=True, seed=12)
    C1 = B11

    def loop_b(f):
        a = 2 * math.pi * ease_in_out((f - bgo - 3) / 18)
        return tuple(C1 + V(0, -0.15 * math.sin(a), 0.15 - 0.15 * math.cos(a)))
    T.set(b.root, "location", loop_b, bgo + 2, bgo + 22)
    T.set(b.root, "location", lambda f: tuple(B11), bgo + 22, S[12][0])
    T.add(b.body, "rotation_euler", lambda f: (-2 * math.pi * ease_in_out((f - bgo - 3) / 18), 0, 0), bgo + 3, bgo + 21)
    A12 = (TH.p(0.1, -5.2, 1.8), TH.p(0.1, 0.3, 1.55), 35.0)

    def shot12(f):
        pb = 1 + 0.10 * ease_out((f - f0_12) / 8)
        bounce = 0.015 * math.sin((f - f0_12) * 0.55) * window(f, f0_12 + 8, f1_12, 4, 4)
        pos = A12[1] + (A12[0] - A12[1]) * pb + V(0, 0, bounce)
        return (pos, A12[1] + V(0, 0, bounce * 0.5), 35.0)
    cam.add_shot(f0_12, f1_12, shot12)

    # =================================================================== SZENE 13 – Loop
    f0_13, f1_13 = S[12]
    bmk = bt(12, "Merk")
    bvk = bt(12, "verkauft")
    bni = bt(12, "nicht")
    BF = TH.p(0.62, -1.2, 2.0)                        # direkt vor der Kamera rechts
    T.set(b.root, "location", lambda f: tuple(B11.lerp(BF, ease_in_out((f - f0_13) / 8))), f0_13, bvk)
    T.add(b.body, "rotation_euler", lambda f: (0, 0, 0.35 * window(f, bmk, bvk, 4, 4)), bmk, bvk)
    exitp = path([(bvk, BF), (bvk + 6, BF + V(0.6, 0.0, 0.35)), (bvk + 12, OUT_R)], ease_in)
    T.set(b.root, "location", lambda f: exitp(f), bvk, N)
    T.set(b.root, "scale", lambda f: (1, 1, 1) if f < bvk + 13 else (0, 0, 0), bvk, bvk + 14)
    for q, obj in enumerate([gl.root, sack.root]):
        ts = bvk + 2 * q
        base = 0.42 if obj is sack.root else 1.0
        T.set(obj, "scale", lambda f, ts=ts, base=base: (base * (1 - ease_in_out((f - ts) / 8)),) * 3, ts - 1, ts + 9)
    A13 = A12
    S1 = (A1[0], A1[1], 50.0)
    cam.add_shot(f0_13, N, shot_lerp(f0_13, N - 7, A13, S1, ease_in_out))

    # ------------------------------------------------------------ Byte-Ausdruecke
    EXP = {"neutral": "neutral", "freundlich": "happy", "ernst": "serious", "zwinkern": "wink", "besorgt": "worried"}
    sched = [(0, "neutral")]
    for i, s in enumerate(sc):
        sched.append((s["f0"], EXP.get(s.get("ausdruck_byte") or "neutral", "neutral")))
    sched += [(bz, "happy"), (bs + 3, "wink"), (bs + 20, "happy"), (b600, "worried"), (bmk, "wink")]
    C.byte_face(T, b, sched, 0, N - 1)

    def focus(f):
        if S[3][0] <= f < S[4][0]:
            return BU.p(0.35, -0.5, 1.4)
        if S[5][0] <= f < S[6][0] or S[9][0] <= f < S[10][0]:
            return gl_pos(f) + V(0, 0, 0.4)
        if S[7][0] <= f < S[8][0]:
            return SCR
        return V(T.loc(k.root, f)) + V(0, -0.25, 1.95)
    W.cam.focus_fn = focus
