"""Regie fuer 'Byte telefoniert' (folge-04-mehlpreis, ohne Stimme). Szenen-Index 0..13 = Szene 1..14.
Running Gags: meterlange Rechnung (Szene 1, 2, 12, 14), platzender Mehlsack (Szene 1, 14).
Kamera-Presets: harter_zoom, fahrt, zoom_gesicht, rueckfahrt, push_in, schwenk (nie zweimal hintereinander)."""
import math
import random

import bpy
from mathutils import Vector

import characters as C
import look as L
import props as PR
from anim import (ease_in, ease_out, ease_in_out, ease_out_back, spring, window, pop, unpop, lerp, Noise)
from choreo.common import Ctx, path, pop_obj, V

FPS = 30


def lerp3(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def vis(T, obj, f_in, f_out=None, base=1.0, dur_in=8, dur_out=8):
    pop_obj(T, obj, f_in, f_out, base=base, dur_in=dur_in, dur_out=dur_out)
    T.set(obj, "scale", lambda f: (0, 0, 0), 0, 1)


# ------------------------------------------------------------------ Kamera-Presets
def harter_zoom(f0, f1, wide, close, f_hit, dur=4):
    def fn(f):
        t = ease_out((f - f_hit) / dur) if f >= f_hit else 0.0
        drift = 0.03 * ease_out((f - f0) / max(1, f_hit - f0)) if f < f_hit else 0.03
        pos = lerp3(wide[0], close[0], t) + Vector((0, drift, 0))
        return (pos, lerp3(wide[1], close[1], t), lerp(wide[2], close[2], t))
    return fn


def fahrt(f0, f1, A, B, ease=ease_in_out):
    return lambda f: (lerp3(A[0], B[0], ease((f - f0) / max(1, f1 - f0))), lerp3(A[1], B[1], ease((f - f0) / max(1, f1 - f0))),
                      lerp(A[2], B[2], ease((f - f0) / max(1, f1 - f0))))


zoom_gesicht = fahrt
rueckfahrt = fahrt


def push_in(f0, f1, A, k=0.18):
    def fn(f):
        t = ease_out((f - f0) / max(1, f1 - f0))
        pos = Vector(A[0]).lerp(Vector(A[1]), k * t)
        return (pos, Vector(A[1]), A[2] * (1 + 0.04 * t))
    return fn


schwenk = fahrt


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    TH, ST = c.sets["theke"], c.sets["studio"]
    sc = c.sc
    S = [(s["f0"], s["f1"]) for s in sc]
    coll = W.coll
    cam = W.cam
    top = TH.top_z

    def hl(i):
        return next((w["f0"] for w in sc[i]["words"] if w["hl"]), sc[i]["f0"] + 6)

    def wd(i, core, nth=1):
        n = 0
        for w in sc[i]["words"]:
            if w["w"].strip(".,!?:…").lower() == core.lower():
                n += 1
                if n == nth:
                    return w["f0"]
        return sc[i]["f0"] + 4

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
    if getattr(k, "towel", None):
        C.follow_through(T, k.towel, k.hips, "rotation_euler", 1, 2.0, 5, 0, N - 1, out_idx=0)
    C.pose(T, k, "arms_rest", -10, None, 1, 1, weight=0.6, settle=False)
    for i, s in enumerate(sc):
        if s["sprecher"] == "kalle":
            C.kalle_lipsync(T, k, s, s["f0"], s["f1"])
        else:
            C.byte_speak(T, b, s, s["f0"], s["f1"])
            C.kalle_look(T, k, lambda f: V(T.loc(b.root, f)) + V(T.loc(b.bob, f)), s["f0"], s["f1"], 0.85)
        for w in s["words"]:
            if w["hl"]:
                cam.punch.append(w["f0"])
    cam.drift_env = lambda f: min(1.0, f / 10.0, max(0.0, (N - 7 - f) / 10.0))

    def cue(f, kind, g=1.0):
        c.cue(int(f), kind, g)

    def set_kalle(f0, f1, loc, rz=0.0):
        T.set(k.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(k.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)

    # ------------------------------------------------------------ Theke
    K = V(TH.kalle)
    face = K + V(0, -0.25, 1.95)
    lap = TH.objs["laptop"]
    lap.root.rotation_euler = (0, 0, math.radians(-14))
    lap_pos = lap.root.location + V(0.02, -0.05, 0.25)
    B_TH = TH.p(0.62, -0.2, 2.15)
    theke_scenes = [i for i, s in enumerate(sc) if s["set"] == "theke"]
    studio_scenes = [i for i, s in enumerate(sc) if s["set"] == "studio"]
    for i in theke_scenes:
        set_kalle(S[i][0], S[i][1], K, 0.0)
    # Hintergrund: Mehlstaub in jeder Szene (Theke und Studio), flatternde Bestellzettel an der Theke
    PR.ambient_motes(T, coll, "th_dust", tuple(TH.p(0, 0.4, 1.9)), (2.2, 1.2, 0.9), 34, 401, 0, N - 1, drift=0.08)
    PR.ambient_motes(T, coll, "st_dust", tuple(ST.p(0, 0.6, 2.2)), (2.4, 1.6, 1.2), 30, 402, 0, N - 1,
                     color_kind="sparkt", drift=0.06, scale=0.6)
    slips = PR.order_slips(coll, "slips", n=14, seed=5)
    slips.root.location = TH.p(-0.62, -0.25, top)
    PR.slips_flutter(T, slips, 0, N - 1, amount=0.6)
    # beschriftete Requisiten an der Theke: Weizen-Sack (platzt), Roggen-Sack, lange Rechnung
    sack_r = PR.flour_sack(coll, "sack_roggen", label=True, scale=0.75, text1="ROGGEN", text2="1150")
    tisch = L.box("sack_tisch", (1.3, 0.6, 0.9), L.mat("wood_dark", L.WOOD_DARK, 0.65), None, TH.p(1.05, 0.95, 0.45), coll)
    sack_r.root.location = TH.p(1.45, 0.98, 0.9)
    sack_r.root.rotation_euler = (0, 0, -0.3)

    def burst_sack(name, f_b, loc, seed):
        sk = PR.flour_sack(coll, name, label=True, scale=0.8, text1="WEIZEN", text2="550")
        sk.root.location = loc
        sk.root.rotation_euler = (0, 0, 0.25)
        T.set(sk.body, "scale", lambda f: (1 + 0.25 * ease_in((f - f_b + 6) / 6), 1 + 0.25 * ease_in((f - f_b + 6) / 6),
                                           1 - 0.1 * ease_in((f - f_b + 6) / 6)) if f < f_b else (0, 0, 0), f_b - 7, f_b + 1)
        PR.burst(T, coll, f"{name}_cloud", "puff", tuple(loc + V(0, 0, 0.45)), f_b, 30, seed, speed=(1.2, 2.4), up=0.9,
                 gravity=-0.4, life=(26, 40), size=(1.2, 2.4), drag=2.5)
        PR.burst(T, coll, f"{name}_dust", "dust", tuple(loc + V(0, 0, 0.5)), f_b, 20, seed + 1, speed=(0.8, 1.8), up=1.2,
                 gravity=-0.8, life=(28, 44), size=(1.0, 1.6), drag=1.5)
        PR.burst(T, coll, f"{name}_shreds", "confetti_#D8C19A", tuple(loc + V(0, 0, 0.5)), f_b, 10, seed + 2,
                 speed=(1.0, 2.0), up=1.0, gravity=-3.0, life=(20, 30), size=(1.2, 1.8))
        return sk
    SACK_POS = TH.p(0.85, 0.85, 0.9)
    s1_burst = wd(0, "Mehl") - 3
    sk1 = burst_sack("sack_w1", s1_burst, SACK_POS, 501)
    cue(s1_burst, "buzz", 1.0)
    # lange Rechnung: rollt ab (Szene 1), Byte rutscht darauf (2), faellt und rollt sich ein (12), rollt wieder ab (14)
    rech = PR.rechnung_lang(coll, "rechnung", length=2.1)
    rech.root.location = TH.p(-1.05, -0.55, top + 0.07)
    rech.root.rotation_euler = (math.radians(-38), 0, 0)
    env = PR.envelope(coll, "umschlag", scale=0.7)
    s1_rip = S[0][0] + 6
    roll1_end = s1_rip + 26
    f_drop = hl(11) - 3
    f_roll2 = wd(13, "bezahlt") - 10

    def unrolled(f):
        if f < s1_rip:
            return 0.03
        if f < f_drop:
            return 0.03 + 0.97 * ease_out((f - s1_rip) / (roll1_end - s1_rip))
        if f < S[13][0]:
            return 1.0 - 0.97 * ease_in_out((f - f_drop) / 14)
        return 0.03 + 0.97 * ease_out((f - f_roll2) / 22) if f >= f_roll2 else 0.03
    PR.rechnung_abrollen(T, rech, unrolled, 0, N - 1)
    # Szene 12: Rolle trifft Kalle am Bauch (Rechnung kurz zu ihm hochgeschleudert)
    T.add(rech.roll, "location", lambda f: (0, 0, 0.5 * math.sin(math.pi * min(1, max(0, (f - f_drop - 10) / 8)))
                                            if f_drop + 10 <= f <= f_drop + 18 else 0), f_drop, f_drop + 20)
    hand_env = K + V(-0.38, -0.55, 1.45)
    env.root.location = hand_env
    env.root.rotation_euler = (0.2, 0, 0.3)
    T.set(env.root, "scale", lambda f: (0.7 if f < s1_rip + 30 else 0.7 * unpop(f, s1_rip + 30, 5),) * 3, 0, s1_rip + 36)
    T.set(env.flap, "rotation_euler", lambda f: (-2.4 * ease_out((f - s1_rip + 4) / 5), 0, 0), s1_rip - 5, s1_rip + 1)
    env2 = PR.envelope(coll, "umschlag2", scale=0.7)
    env2.root.location = hand_env
    env2.root.rotation_euler = (0.2, 0, 0.3)
    vis(T, env2.root, f_roll2 - 14, N - 6, base=0.7)
    # Rechnung reissen: Arm R zieht
    rip = {"sh_R": (-1.1, 0.25, 0.2), "el_R": (-0.9, 0, 0), "hips": (0.04, 0, 0.06)}
    C.pose(T, k, rip, 0, s1_rip + 20, 1, 10, settle=False)

    # =================================================================== SZENE 1 – Schock, harter Zoom
    f0_1, f1_1 = S[0]
    WIDE = (TH.p(0.1, -4.6, 1.85), TH.p(0.1, 0.2, 1.42), 38.0)
    CLOSE = (face + V(0.15, -3.7, -0.05), face + V(0.15, 0, -0.42), 50.0)
    s1 = harter_zoom(f0_1, f1_1, WIDE, CLOSE, hl(0) + 2)
    cam.add_shot(f0_1, f1_1, s1)
    C.reaction(T, coll, k, "schock", hl(0) + 2, hold=f1_1 - hl(0), speaking=True, seed=1)
    for side in ("R", "L"):
        T.mul(k.eye[side], "scale", lambda f: (1 + 0.15 * window(f, hl(0) + 2, f1_1 + 2, 2, 8),) * 3, hl(0), f1_1 + 4)
    T.set(b.root, "scale", lambda f: (0, 0, 0), 0, 1)
    T.set(b.root, "location", lambda f: tuple(lap_pos), 0, S[1][0])

    # =================================================================== SZENE 2 – Byte rutscht auf der Rechnung
    f0_2, f1_2 = S[1]
    bp = f0_2 + 2
    land = bp + 9
    strip0 = rech.root.location + V(1.8, 0.02, 0.12)
    strip1 = rech.root.location + V(0.75, 0.02, 0.12)
    bpath = path([(bp, lap_pos), (bp + 5, lap_pos + V(0.3, -0.2, 0.55)), (land, strip0), (f1_2 - 6, strip1),
                  (f1_2 + 2, B_TH)], ease_in_out)
    T.set(b.root, "location", lambda f: bpath(f), f0_2, f1_2 + 3)
    T.set(b.root, "scale", lambda f: (max(0.0, ease_out_back(min(1, (f - bp) / 6), 2.2)),) * 3, bp - 1, bp + 7)
    T.add(b.body, "rotation_euler", lambda f: (0, 0.35 * window(f, land, f1_2 - 4, 3, 5), 0), land, f1_2 - 3)
    T.mul(b.body, "scale", lambda f: (1 + 0.15 * window(f, land - 1, land + 6, 1, 5), 1,
                                      1 - 0.15 * window(f, land - 1, land + 6, 1, 5)), land - 1, land + 6)
    PR.flash(T, coll, "s2flash", tuple(lap_pos), bp, 8, 0.2, L.TURQ, 160)
    PR.burst(T, coll, "s2skid", "dust", tuple(strip0), land, 12, 520, speed=(0.4, 0.9), up=0.4, gravity=-0.5,
             life=(14, 22))
    cue(bp, "whoosh", 1.0)
    C.reaction(T, coll, k, "neutral", hl(1), seed=2)
    cam.add_shot(f0_2, f1_2, fahrt(f0_2, f1_2, (TH.p(0.35, -3.9, 1.75), TH.p(0.35, 0.0, 1.35), 42.0),
                               (TH.p(0.05, -4.0, 1.8), TH.p(0.1, 0.0, 1.42), 44.0)))

    # =================================================================== SZENE 3 – Kalle klopft an Bytes Kopf
    f0_3, f1_3 = S[2]
    B3 = TH.p(0.2, -0.45, 1.55)
    T.set(b.root, "location", lambda f: tuple(B_TH.lerp(B3, ease_in_out((f - f0_3) / 8))), f0_3, f1_3)
    tock = wd(2, "Ohren") - 6
    bend = {"hips": (0.32, 0, -0.12), "sh_L": (-1.25, -0.35, -0.2), "el_L": (-0.55, 0, 0), "head": (0.2, 0, -0.2)}
    C.pose(T, k, bend, f0_3 + 2, f1_3 - 2, 6, 6)
    T.add(k.sh["L"], "rotation_euler", lambda f: (0.22 * max(0, math.sin(math.pi * (f - tock) / 4)) if tock <= f <= tock + 4
                                                  else 0, 0, 0), tock - 1, tock + 5)
    T.add(b.body, "location", lambda f: (0.05 * spring((f - tock - 3) / FPS, 5, 0.3) if f > tock + 3 else 0, 0, 0),
          tock, tock + 20)
    PR.burst(T, coll, "s3flour", "dust", tuple(B3 + V(-0.25, -0.05, 0.25)), tock + 3, 10, 530, speed=(0.1, 0.3), up=0.1,
             gravity=-1.2, life=(18, 26), size=(1.0, 1.5))
    cue(tock + 3, "pop", 0.4)
    C.reaction(T, coll, k, "zweifel", hl(2) - 4, hold=f1_3 - hl(2) + 4, speaking=True, seed=3)
    T.add(k.brow["R"], "location", lambda f: (0, 0, 0.06 * window(f, hl(2) - 4, f1_3, 4, 6)), hl(2) - 4, f1_3)
    cam.add_shot(f0_3, f1_3, zoom_gesicht(f0_3, f1_3, (TH.p(0.0, -4.0, 1.8), TH.p(0.0, 0.0, 1.42), 44.0),
                                      (face + V(0.12, -2.6, -0.05), face + V(0.1, 0, -0.22), 58.0)))

    # =================================================================== SZENE 4 – drei Hoerer aus der Antenne
    f0_4, f1_4 = S[3]
    B4 = TH.p(0.55, -0.3, 2.0)
    T.set(b.root, "location", lambda f: tuple(B3.lerp(B4, ease_out((f - f0_4) / 8))), f0_4, S[4][0])
    ant = lambda f: V(T.loc(b.root, f)) + V(0.03, 0, 0.4)  # noqa: E731
    hoerer = []
    shots = [wd(3, "Ich") - 2, wd(3, "hab"), wd(3, "drei")]
    targets = [V(-0.55, -0.15, 0.4), V(0.05, -0.35, 0.75), V(0.6, -0.1, 0.45)]
    for q in range(3):
        h = PR.telefonhoerer(coll, f"hoerer{q}")
        tq = shots[q]
        hoerer.append(h)
        T.set(h, "scale", lambda f, tq=tq: (pop(f, tq, 5, 1.2),) * 3, tq - 1, tq + 6)
        T.set(h, "scale", lambda f: (0, 0, 0), 0, 1)
        cue(tq, "pop", 0.8)
    cue(f0_4 + 1, "whoosh", 0.9)

    # Hoerer-Positionen ueber alle Szenen (4: schiessen raus, 5: jonglieren, 6: verheddert, danach weg)
    J0, J1 = S[4][0], S[5][1]
    BS = ST.p(0.0, 0.2, 2.25)

    def h_pos(q, f):
        if f < S[4][0]:
            tq = shots[q]
            return ant(f) + targets[q] * ease_out_back(min(1, max(0, (f - tq) / 6)), 1.6)
        if f < S[5][0]:
            a = 2 * math.pi * (f - J0) / 22 + q * 2 * math.pi / 3
            return BS + V(0.42 * math.cos(a), -0.15, 0.55 + 0.25 * math.sin(a))
        a = q * 2 * math.pi / 3 + (f - S[5][0]) * 0.08
        return BS + V(0.32 * math.cos(a), -0.25, 0.1 + 0.08 * q)
    for q, h in enumerate(hoerer):
        T.set(h, "location", lambda f, q=q: tuple(h_pos(q, f)), shots[q] - 1, J1 + 1)
        T.set(h, "rotation_euler", lambda f, q=q: (0.3 * math.sin(f * 0.3 + q), 0.5 * math.sin(f * 0.21 + q), f * 0.15 * (q - 1)),
              shots[q] - 1, J1 + 1)
        T.set(h, "scale", lambda f, q=q: (unpop(f, J1 - 4, 4),) * 3, J1 - 5, J1 + 1)
    lean = {"hips": (-0.22, 0, 0.1), "head": (-0.15, 0, 0.12), "sh_R": (-0.6, 0.5, 0), "sh_L": (-0.6, -0.5, 0)}
    C.pose(T, k, lean, shots[0] + 2, f1_4 + 2, 4, 6, overshoot=0.2)
    C.reaction(T, coll, k, "staunen", shots[0] + 3, hold=f1_4 - shots[0], seed=4)
    cam.add_shot(f0_4, f1_4, rueckfahrt(f0_4, f1_4, (face + V(0.3, -2.8, 0.05), face + V(0.3, 0, -0.1), 55.0),
                                    (TH.p(0.15, -4.6, 1.85), TH.p(0.15, 0.0, 1.5), 38.0), ease_out))

    # =================================================================== Studio-Grundlagen
    KS = ST.p(-1.0, -0.45, 0)
    for i in studio_scenes:
        set_kalle(S[i][0], S[i][1], KS, 0.35)
    scr = ST.objs["screen"]
    T.set(ST.objs["spot"].data, "energy", lambda f: 0, 0, 1)
    peds = []
    crates = []
    labels = ["MÜHLE A", "MÜHLE B", "MÜHLE C"]
    CR = [ST.p(-0.85, 0.75, 1.05), ST.p(0.0, 0.95, 1.05), ST.p(0.85, 0.75, 1.05)]
    for q in range(3):
        ped = L.cyl(f"crate_ped{q}", 0.33, 1.05, 16, L.mat("pedestal", "#2B2750", 0.5), None, CR[q] - V(0, 0, 0.525), coll)
        cr = PR.muehlen_kiste(coll, f"kiste{q}", labels[q])
        cr.root.location = CR[q]
        cr.root.rotation_euler = (0, 0, (1 - q) * 0.25)
        PR.kiste_wackeln(T, cr, S[4][0], S[5][1], amount=1.0, seed=q)
        PR.kiste_wackeln(T, cr, S[7][0], N - 1, amount=0.3, seed=q + 5)
        crates.append(cr)
        peds.append(ped)
    # Ringelkabel Hoerer -> Kisten (Szene 5/6), verheddert um Byte in Szene 6
    w6a, w6b = S[5][0], hl(5)
    for q in range(3):
        PR.ringelkabel(T, coll, f"kabel{q}", lambda f, q=q: tuple(h_pos(q, f)), lambda f, q=q: tuple(CR[q] + V(0, -0.1, 0.42)),
                       S[4][0], S[5][1],
                       wrap_fn=lambda f: (BS, 0.3, window(f, w6a, S[5][1] + 20, 6, 14)))
    for q in range(3):
        for i_ in range(18):
            o = bpy.data.objects[f"kabel{q}_r{i_}"]
            T.set(o, "scale", lambda f: (1, 1, 1) if S[4][0] <= f < S[5][1] - 2 else (0, 0, 0), 0, N)

    # =================================================================== SZENE 5 – Hallo, hier ist Byte
    f0_5, f1_5 = S[4]
    T.set(b.root, "location", lambda f: tuple(BS), f0_5, S[5][1])
    for q, cr in enumerate(crates):
        for kk in range(3):
            cue(f0_5 + 8 + q * 7 + kk * 22, "ding", 0.25)
    cam.add_shot(f0_5, f1_5, push_in(f0_5, f1_5, (ST.p(0.0, -5.6, 2.25), ST.p(0.0, 0.6, 2.2), 32.0), k=0.16))
    C.reaction(T, coll, k, "neutral", hl(4), seed=5)
    cam.whips.append((f0_5, 1))

    # =================================================================== SZENE 6 – drei Angebote, verheddert
    f0_6, f1_6 = S[5]
    prices = ["23 €", "21 €", "22 €"]
    words6 = [wd(5, "23"), wd(5, "21"), wd(5, "22")]
    offers = []
    for q in range(3):
        o = PR.angebotszettel(coll, f"zettel{q}", prices[q], green=(q == 1))
        o.root.scale = (1.9, 1.9, 1.9)
        tq = words6[q] - 3
        base = CR[q] + V(0, -0.35, 0.85)
        T.set(o.root, "location", lambda f, tq=tq, base=base: tuple(base + V(0, 0, -0.5 * (1 - ease_out_back(min(1, max(0, (f - tq) / 7)), 1.8)))),
              tq - 1, tq + 8)
        T.set(o.root, "location", lambda f, base=base: tuple(base), tq + 8, tq + 9)
        o.root.scale = (0, 0, 0)
        T.set(o.root, "scale", lambda f, tq=tq: (1.9 * pop(f, tq, 6, 1.15),) * 3, tq - 1, tq + 7)
        T.set(o.root, "scale", lambda f: (0, 0, 0), 0, 1)
        T.add(o.root, "rotation_euler", lambda f, q=q: (0, 0.06 * math.sin(f * 0.2 + q), 0), tq, N - 1)
        offers.append((o, base))
        cue(words6[q], "pop", 1.0)
    T.add(L.bsdf(offers[1][0].mat).inputs["Emission Strength"], "default_value",
          lambda f: 1.5 * (0.5 + 0.5 * math.sin(f * 0.4)), words6[1], N - 1)
    T.add(b.body, "rotation_euler", lambda f: (0, 0, 4 * math.pi * ease_in_out((f - (hl(5) - 4)) / 18)), hl(5) - 4, hl(5) + 14)
    C.reaction(T, coll, k, "staunen", hl(5), hold=f1_6 - hl(5), seed=6)
    cam.add_shot(f0_6, f1_6, schwenk(f0_6, f1_6, (ST.p(-0.6, -3.9, 2.25), ST.p(-0.6, 0.6, 2.05), 40.0),
                                 (ST.p(0.7, -3.9, 2.25), ST.p(0.7, 0.6, 2.05), 40.0)))

    # =================================================================== SZENE 7 – Kalle haut auf die Theke
    f0_7, f1_7 = S[6]
    slap = hl(6) - 2
    hand = {"sh_L": (-1.45, -0.25, -0.1), "el_L": (-0.2, 0, 0)}
    C.pose(T, k, {kk: (-0.6 * v[0], v[1], v[2]) for kk, v in hand.items()}, f0_7, slap - 4, 3, 4, settle=False)
    C.pose(T, k, hand, slap - 4, f1_7, 4, 6, overshoot=0.25)
    PR.burst(T, coll, "s7flour", "puff", tuple(TH.p(-0.65, -0.45, top + 0.05)), slap, 16, 701, speed=(0.8, 1.6), up=0.7,
             gravity=-0.5, life=(16, 26), size=(0.8, 1.4), drag=3.0)
    drawer = TH.objs["drawer"]
    T.set(drawer, "location", lambda f: (0, -0.3 * ease_out_back(min(1, max(0, (f - slap - 2) / 6)), 1.5), 0), slap, N - 1)
    T.set(drawer, "location", lambda f: (0, 0, 0), S[13][0], N)
    C.reaction(T, coll, k, "jubel", slap + 2, hold=f1_7 - slap, speaking=True, seed=7)
    cam.add_shot(f0_7, f1_7, push_in(f0_7, f1_7, (TH.p(-0.25, -4.3, 1.85), TH.p(-0.25, 0.0, 1.4), 40.0), k=0.2))
    cam.whips.append((f0_7, -1))
    T.set(b.root, "location", lambda f: tuple(B_TH), S[6][0], S[7][0])

    # =================================================================== SZENE 8 – Moment. Sonnenbrille, vierte Kiste, Stempel
    f0_8, f1_8 = S[7]
    BS8 = ST.p(0.35, -0.2, 2.25)
    T.set(b.root, "location", lambda f: tuple(BS8), f0_8, S[8][0])
    for lt in ST.lights:
        if lt.data.energy > 0:
            e0 = lt.data.energy
            T.set(lt.data, "energy", lambda f, e0=e0: e0 * (0.35 if S[7][0] + 2 <= f < S[8][1] else 1.0), 0, N)
    spot = ST.objs["spot"]
    spot.location = ST.p(0.35, -1.6, 5.4)
    spot.rotation_euler = L.look_rot(spot.location, BS8)
    T.set(spot.data, "energy", lambda f: 900 * window(f, S[7][0] + 2, S[8][1], 4, 6), 0, N)
    shades = PR.sonnenbrille(coll, "shades")
    shades.parent = b.body
    shades.location = (0, -0.24, 0.035)
    on = wd(7, "Jetzt") - 2
    T.set(shades, "location", lambda f: (0, -0.24, 0.035 + 0.4 * (1 - ease_out((f - on) / 6))), on - 1, on + 7)
    off = hl(10) + 4
    T.set(shades, "location", lambda f: (0, -0.24 - 0.2 * ease_in((f - off) / 6), 0.035 + 0.25 * ease_in((f - off) / 6)),
          off, off + 7)
    T.set(shades, "scale", lambda f: (1, 1, 1) if on - 1 <= f < off + 7 else (0, 0, 0), 0, N)
    CR4 = ST.p(1.15, -0.1, 0.0)
    ped4 = L.cyl("crate_ped4", 0.4, 1.05, 16, L.mat("pedestal", "#2B2750", 0.5), None, CR4 + V(0, 0, 0.525), coll)
    vis(T, ped4, f0_8 + 4, None)
    CR4 = CR4 + V(0, 0, 1.05)
    cr4 = PR.muehlen_kiste(coll, "kiste4", "MÜHLE MAIER")
    cr4.root.scale = (1.15, 1.15, 1.15)
    roll_in = f0_8 + 4
    T.set(cr4.root, "location", lambda f: tuple(CR4 + V(1.6 * (1 - ease_out((f - roll_in) / 10)), 0, 0)), roll_in - 1, N)
    T.set(cr4.root, "rotation_euler", lambda f: (0, 0.5 * (1 - ease_out_back(min(1, (f - roll_in) / 12), 1.5)), 0), roll_in - 1,
          roll_in + 13)
    T.set(cr4.root, "scale", lambda f: (1.15, 1.15, 1.15) if f >= roll_in else (0, 0, 0), 0, roll_in + 1)
    st = PR.stempel(coll, "stempel")
    hit = hl(7) - 3
    T.set(st, "location", lambda f: tuple(CR4 + V(0, -0.3, 0.12 + 0.8 * (1 - ease_in((f - hit + 6) / 6)) if f < hit else 0.12 +
                                                  0.5 * ease_out((f - hit - 3) / 8) if f > hit + 3 else 0.12)), hit - 7, hit + 12)
    T.set(st, "rotation_euler", lambda f: (math.pi / 2, 0, 0), hit - 7, hit - 6)
    T.set(st, "scale", lambda f: (1, 1, 1) if hit - 7 <= f < hit + 12 else (0, 0, 0), 0, N)
    T.set(cr4.stamp_mark, "scale", lambda f: (pop(f, hit, 4, 1.2) * 1.0,) * 3, hit - 1, hit + 5)
    cue(f0_8 + 2, "whoosh", 0.9)
    C.reaction(T, coll, k, "neutral", hl(7), seed=8)
    face_b8 = BS8
    cam.add_shot(f0_8, f1_8, zoom_gesicht(f0_8, f1_8, (ST.p(0.6, -4.8, 2.3), ST.p(0.6, 0.4, 2.1), 36.0),
                                      (face_b8 + V(0.35, -2.9, 0.0), face_b8 + V(0.35, 0, -0.3), 46.0)))
    cam.whips.append((f0_8, 1))

    # =================================================================== SZENE 9 – Konkurrenz macht 21
    f0_9, f1_9 = S[8]
    T.set(b.root, "location", lambda f: tuple(BS8), f0_9, f1_9)
    o21, base21 = offers[1]
    flick = wd(8, "21") - 6
    tgt = CR4 + V(-0.1, -0.35, 0.75)
    T.set(o21.root, "location", lambda f: tuple(base21.lerp(tgt, ease_in_out((f - flick) / 10)) +
                                                V(0, 0, 0.5 * math.sin(math.pi * min(1, max(0, (f - flick) / 10))))), flick - 1, N - 1)
    T.set(o21.root, "rotation_euler", lambda f: (0, 0, 2 * math.pi * ease_out((f - flick) / 10)), flick - 1, flick + 11)
    PR.burst(T, coll, "sweat4", "sweat", tuple(CR4 + V(0, -0.3, 0.55)), flick + 10, 14, 901, speed=(0.3, 0.6), up=0.6,
             spread=1.0, gravity=-2.0, life=(18, 26), size=(0.9, 1.4))
    PR.burst(T, coll, "sweat4b", "sweat", tuple(CR4 + V(0.2, -0.3, 0.5)), f1_9 - 22, 10, 902, speed=(0.2, 0.5), up=0.5,
             gravity=-2.0, life=(16, 22))
    PR.kiste_wackeln(T, cr4, flick + 10, f1_9, amount=1.4, seed=9)
    C.reaction(T, coll, k, "zweifel", hl(8), hold=f1_9 - hl(8), seed=9)
    cam.add_shot(f0_9, f1_9, fahrt(f0_9, f1_9, (ST.p(0.3, -4.4, 2.25), ST.p(0.3, 0.3, 2.1), 40.0),
                               (ST.p(1.25, -4.4, 2.0), ST.p(1.3, 0.3, 1.2), 40.0)))

    # =================================================================== SZENE 10 – mein Mueller (Theke)
    f0_10, f1_10 = S[9]
    T.set(b.root, "location", lambda f: tuple(B_TH), f0_10, S[10][0])
    holdhat = {"sh_R": (-2.6, 0.5, 0.3), "sh_L": (-2.6, -0.5, -0.3), "el_R": (-1.5, 0, 0.6), "el_L": (-1.5, 0, -0.6),
               "head": (0, 0, 0.35)}
    C.pose(T, k, holdhat, f0_10 + 1, f1_10 + 2, 5, 6)
    C.kalle_look(T, k, lambda f: lap_pos, f0_10 + 4, f1_10, 1.0)
    C.reaction(T, coll, k, "schock", hl(9) - 2, hold=f1_10 - hl(9) + 4, speaking=True, seed=10, hat=False)
    PR.slips_flutter(T, slips, f0_10, f1_10, amount=2.5, seed=40)
    PR.burst(T, coll, "s10slips", "confetti_#F7E7A6", tuple(TH.p(-0.62, -0.1, top + 0.3)), f0_10 + 4, 12, 1001,
             speed=(0.4, 0.9), up=1.2, gravity=-0.6, life=(30, 44), size=(1.5, 2.2), flutter=0.7, wobble=0.05)
    cue(hl(9), "buzz", 1.0)
    cam.add_shot(f0_10, f1_10, harter_zoom(f0_10, f1_10, (TH.p(0.0, -4.2, 1.85), TH.p(0.0, 0.2, 1.45), 40.0),
                                     (face + V(0.1, -3.4, 0.0), face + V(0.1, 0, -0.3), 52.0), hl(9) - 1))
    cam.whips.append((f0_10, -1))

    # =================================================================== SZENE 11 – 19,70
    f0_11, f1_11 = S[10]
    BS11 = ST.p(-0.35, -0.3, 2.3)
    T.set(b.root, "location", lambda f: tuple(BS11), f0_11, S[11][0])
    sign = PR.preisschild(coll, "preisschild")
    SG = ST.p(0.55, 0.3, 2.55)
    sign.root.location = SG
    vis(T, sign.root, f0_11 + 1, S[11][0] - 1, base=1.2, dur_in=6)
    T.set(sign.flip, "rotation_euler", lambda f: (math.pi * (1 - ease_out_back(min(1, max(0, (f - f0_11 - 2) / 10)), 1.3)), 0, 0),
          f0_11 + 1, f0_11 + 13)
    sb = hl(10) - 10
    T.set(sign.strike, "scale", lambda f: (ease_out((f - sb) / 5), 1, 1), sb - 1, sb + 6)
    T.set(sign.new, "scale", lambda f: (pop(f, hl(10) - 3, 6, 1.25),) * 3, hl(10) - 4, hl(10) + 4)
    PR.burst(T, coll, "s11conf", "confetti", tuple(SG + V(0, -0.2, 0.3)), hl(10), 36, 1101, speed=(1.4, 2.6), up=1.2,
             spread=1.1, gravity=-2.5, life=(30, 44), size=(1.0, 1.5), drag=1.4, flutter=0.6, wobble=0.04,
             kinds=["confetti_#F5F1E8", "confetti_#FFE14D", "confetti_#D8C19A"])
    cue(hl(10), "ding", 1.0)
    C.reaction(T, coll, k, "jubel", hl(10), hold=f1_11 - hl(10), seed=11)
    cam.add_shot(f0_11, f1_11, push_in(f0_11, f1_11, (ST.p(0.2, -4.8, 2.3), SG + V(-0.3, 0, -0.25), 38.0), k=0.22))
    cam.whips.append((f0_11, 1))

    # =================================================================== SZENE 12 – 18 Prozent (Theke)
    f0_12, f1_12 = S[11]
    T.set(b.root, "location", lambda f: tuple(B_TH), f0_12, S[12][0])
    C.reaction(T, coll, k, "staunen", hl(11) - 2, hold=f1_12 - hl(11) + 4, speaking=True, seed=12)
    T.add(k.body, "location", lambda f: (0, 0.08 * spring((f - f_drop - 18) / FPS, 3, 0.3) if f > f_drop + 18 else 0, 0),
          f_drop + 18, f_drop + 40)
    cue(f_drop + 18, "pop", 0.6)
    cam.add_shot(f0_12, f1_12, zoom_gesicht(f0_12, f1_12, (TH.p(-0.05, -4.2, 1.8), TH.p(-0.05, 0.1, 1.4), 40.0),
                                      (face + V(0.0, -3.4, 0.0), face + V(0, 0, -0.35), 50.0)))
    cam.whips.append((f0_12, -1))

    # =================================================================== SZENE 13 – Saecke, Muenzsaeule
    f0_13, f1_13 = S[12]
    stack = L.empty("sackstack", None, ST.p(0.15, 0.1, 0), coll)
    for q, (x, y, z) in enumerate([(-0.3, 0, 0), (0.3, 0, 0), (0, 0.05, 0.55), (-0.3, 0.3, 0)]):
        sk = PR.flour_sack(coll, f"stack_sack{q}", label=True, scale=0.8, text1="WEIZEN", text2="550")
        sk.root.parent = stack
        sk.root.location = (x, y, z)
        sk.root.rotation_euler = (0, 0, 0.15 * (q - 1))
    vis(T, stack, f0_13, f1_13 + 4, dur_in=6)
    T.set(b.root, "location", lambda f: tuple(ST.p(0.15, 0.05, 1.42)), f0_13, f1_13)
    col = PR.coin_column(coll, "coins13", 60, spacing=0.05)
    COL = ST.p(1.0, 0.2, 0)
    col.root.location = COL
    col.root.scale = (1.6, 1.6, 1.0)
    for q, cn in enumerate(col.coins):
        tq = f0_13 + 6 + q * 0.6
        T.set(cn, "scale", lambda f, tq=tq: (min(1.0, ease_out((f - tq) / 3)),) * 3 if f < f1_13 + 2 else (0, 0, 0), tq - 1, f1_13 + 3)
        T.set(cn, "scale", lambda f: (0, 0, 0), 0, 1)
    PR.burst(T, coll, "coinsdrop", "coinp", tuple(COL + V(0, 0, 3.0)), f0_13 + 30, 16, 1301, speed=(0.4, 1.0), up=0.4,
             gravity=-6.0, life=(26, 40), size=(1.0, 1.4))
    for kk in range(4):
        cue(f0_13 + 34 + kk * 7, "pop", 0.3)
    cue(hl(12), "ding", 1.0)
    C.reaction(T, coll, k, "jubel", hl(12), hold=f1_13 - hl(12), seed=13)
    cam.add_shot(f0_13, f1_13, schwenk(f0_13, f1_13, (ST.p(0.4, -4.6, 1.2), ST.p(0.6, 0.3, 1.0), 34.0),
                                 (ST.p(0.4, -4.6, 2.6), ST.p(0.6, 0.3, 3.0), 34.0)))
    cam.whips.append((f0_13, 1))

    # =================================================================== SZENE 14 – jahrelang bezahlt (Loop)
    f0_14, f1_14 = S[13]
    back = N - 16                          # Byte schluepft zurueck in den Laptop (Loop: Frame 1 ohne Byte)
    T.set(b.root, "location", lambda f: tuple(B_TH.lerp(lap_pos, ease_in((f - back) / 10)) if f > back else B_TH), f0_14, N)
    T.set(b.root, "scale", lambda f: (1 - ease_in((f - back - 2) / 9),) * 3 if f > back else (1, 1, 1), back, N)
    slump = {"hips": (0.25, 0, 0), "head": (0.3, 0, 0.1), "sh_R": (-0.3, 0.2, 0), "sh_L": (-0.3, -0.2, 0)}
    C.pose(T, k, slump, f0_14 + 2, N - 14, 8, 10)
    T.add(k.body, "location", lambda f: (0, 0, -0.12 * window(f, f0_14 + 2, N - 12, 8, 10)), f0_14, N - 10)
    burst2 = hl(13) + 4
    sk2 = burst_sack("sack_w2", burst2, SACK_POS, 1401)
    T.set(sk2.root, "scale", lambda f: (0.8 if f >= f0_14 else 0,) * 3, 0, f0_14 + 1)
    T.set(sk1.root, "scale", lambda f: (0.8 if f >= N - 2 or f < s1_burst + 1 else 0,) * 3, 0, N)
    cue(burst2, "buzz", 1.0)
    C.reaction(T, coll, k, "schock", hl(13), hold=f1_14 - hl(13) - 10, speaking=True, seed=14, hat=False)
    S1START = s1(0)
    cam.add_shot(f0_14, N, fahrt(f0_14, N - 7, (face + V(0.05, -3.4, 0.0), face + V(0, 0, -0.35), 50.0), S1START))
    cam.whips.append((f0_14, -1))

    # Byte-Ausdruecke
    sched = [(0, "neutral"), (S[1][0], "happy"), (S[2][0], "serious"), (S[3][0], "wink"), (S[4][0], "happy"),
             (S[5][0], "surprised"), (S[5][0] + 30, "happy"), (S[7][0], "serious"), (S[8][0], "wink"),
             (S[10][0], "happy"), (S[12][0], "happy"), (S[13][0], "surprised")]
    C.byte_face(T, b, sched, 0, N - 1)

    def focus(f):
        for i in studio_scenes:
            if S[i][0] <= f < S[i][1]:
                return V(T.loc(b.root, f))
        return V(T.loc(k.root, f)) + V(0, -0.25, 1.95)
    W.cam.focus_fn = focus
