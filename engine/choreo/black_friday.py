"""Regie fuer 'Der teuerste Rabatt' (folge-05-black-friday, ohne Stimme). Szenen-Index 0..13 = Szene 1..14.
Running Gags: '−30 %'-Neonschild (Szene 1, 2, 12, 14), Bytes Sonnenbrille (Szene 8 bis 13).
Kassenbon auf dem Screen als roter Faden (Szene 4, 5, 6, 11). Kamera-Presets nie zweimal hintereinander."""
import math
import random

from mathutils import Vector

import characters as C
import look as L
import props as PR
from anim import (ease_in, ease_out, ease_in_out, ease_out_back, spring, window, pop, unpop, lerp)
from choreo.common import Ctx, path, V
from choreo.mehlpreis import harter_zoom, fahrt, push_in, vis

FPS = 30
zoom_gesicht = rueckfahrt = schwenk = fahrt


def kreisfahrt(f0, f1, center, radius, height, a0, a1, lens):
    def fn(f):
        a = math.radians(lerp(a0, a1, ease_in_out((f - f0) / max(1, f1 - f0))))
        pos = Vector(center) + Vector((radius * math.sin(a), -radius * math.cos(a), height))
        return (pos, Vector(center), lens)
    return fn


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    TH, ST = c.sets["theke"], c.sets["studio"]
    sc = c.sc
    S = [(s["f0"], s["f1"]) for s in sc]
    coll = W.coll
    cam = W.cam
    top = TH.top_z

    def hl(i, n=0):
        ws = [w["f0"] for w in sc[i]["words"] if w["hl"]]
        return ws[min(n, len(ws) - 1)] if ws else sc[i]["f0"] + 6

    def wd(i, core):
        for w in sc[i]["words"]:
            if w["w"].strip(".,!?:…").lower() == core.lower():
                return w["f0"]
        return sc[i]["f0"] + 4

    def cue(f, kind, g=1.0):
        c.cue(int(f), kind, g)

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

    def set_kalle(f0, f1, loc, rz=0.0):
        T.set(k.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(k.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)

    # ------------------------------------------------------------ Theke: Requisiten
    K = V(TH.kalle)
    face = K + V(0, -0.25, 1.95)
    lap = TH.objs["laptop"]
    lap.root.rotation_euler = (0, 0, math.radians(-14))
    lap_pos = lap.root.location + V(0.02, -0.05, 0.25)
    B_TH = TH.p(0.62, -0.2, 2.15)
    theke = [i for i, s in enumerate(sc) if s["set"] == "theke"]
    studio = [i for i, s in enumerate(sc) if s["set"] == "studio"]
    for i in theke:
        set_kalle(S[i][0], S[i][1], K, 0.0)
    PR.ambient_motes(T, coll, "th_dust", tuple(TH.p(0, 0.4, 1.9)), (2.2, 1.2, 0.9), 30, 501, 0, N - 1, drift=0.08)
    PR.ambient_motes(T, coll, "st_dust", tuple(ST.p(0, 0.6, 2.2)), (2.4, 1.6, 1.2), 30, 502, 0, N - 1,
                     color_kind="sparkt", drift=0.06, scale=0.6)
    L.box("sack_tisch", (1.3, 0.6, 0.9), L.mat("wood_dark", L.WOOD_DARK, 0.65), None, TH.p(1.05, 0.95, 0.45), coll)
    for q, (x, t1, t2) in enumerate([(0.75, "WEIZEN", "550"), (1.4, "ROGGEN", "1150")]):
        sk = PR.flour_sack(coll, f"sack{q}", label=True, scale=0.75, text1=t1, text2=t2)
        sk.root.location = TH.p(x, 0.95, 0.9)
        sk.root.rotation_euler = (0, 0, 0.2 - 0.4 * q)
    # Neonschild '−30 % AUF ALLES' (Running Gag)
    sign = PR.neonschild(coll, "neon30", "−30 % AUF ALLES", color="#FF3B6B", width=0.86, height=0.3, size=0.098)
    SIGN = TH.p(-0.8, -0.35, 2.3)                     # haengt links neben Kalles Kopf
    sign.root.rotation_euler = (math.radians(-8), 0, 0)
    hand0 = K + V(-0.45, -0.7, 1.75)
    slam1 = S[0][0] + 7
    grab14 = S[13][0] + 6                                  # Szene 14: Kalle schnappt sich das Schild (Loop)

    def sign_pos(f):
        if f < slam1:                                    # fliegt in Frame 0 schon
            t = ease_in((f + 4) / (slam1 + 4))
            return hand0.lerp(SIGN, t) + V(0, 0, 0.35 * math.sin(math.pi * t))
        if f >= grab14:
            return SIGN.lerp(hand0, ease_in_out((f - grab14) / 8))
        return SIGN
    T.set(sign.root, "location", lambda f: tuple(sign_pos(f)), 0, N - 1)
    T.set(sign.root, "scale", lambda f: (1 + 0.12 * spring((f - slam1) / FPS, 4, 0.3), 1, 1 - 0.12 * spring((f - slam1) / FPS, 4, 0.3))
          if f >= slam1 else (1, 1, 1), 0, slam1 + 20)
    aus2 = (hl(1) - 2, hl(1) + 16)
    PR.neon_flacker(T, sign, 0, N - 1, seed=30, aus=aus2)
    # Brezeln mit Preisschildern auf der Theke (huepfen)
    brez = []
    for q, x in enumerate((0.72, 0.9, 1.08)):
        bz = PR.brezel_schild(coll, f"brezel{q}", "1,20 €", loc=tuple(TH.p(x, -0.66, top)), s=1.15)
        T.add(bz.root, "location", lambda f, q=q: (0, 0, 0.06 * max(0.0, math.sin(f * 0.45 + q * 1.3))), 0, N - 1)
        brez.append(bz)
    # Konfetti-Kanone: feuert vor Frame 0 (Konfetti ist im ersten Frame schon in der Luft)
    kan = PR.konfetti_kanone(coll, "kanone")
    kan.root.location = TH.p(1.38, -0.55, top)
    kan.root.rotation_euler = (0, 0, math.radians(35))
    KINDS = ["confetti_#FFE14D", "confetti_#F2B45A", "confetti_#FF3B6B", "confetti_#2EE6D6", "confetti_#F5F1E8"]
    PR.burst(T, coll, "konf1", "confetti", tuple(TH.p(1.25, -0.7, top + 0.45)), -10, 60, 1001, speed=(2.0, 3.4), up=1.6,
             spread=1.0, gravity=-2.5, life=(55, 80), size=(1.2, 1.8), drag=1.2, flutter=0.6, wobble=0.04,
             kinds=KINDS, dir_bias=(-1.2, 0.3, 0.6))
    T.add(kan.barrel, "location", lambda f: (0, 0.06 * spring((f + 10) / FPS, 4, 0.3), 0), 0, 20)

    # =================================================================== SZENE 1 – Black Friday (push_in, schnell)
    f0_1, f1_1 = S[0]
    S1A = (TH.p(-0.12, -4.7, 1.9), TH.p(-0.15, 0.2, 1.5), 38.0)
    s1 = push_in(f0_1, f1_1, S1A, k=0.22)
    cam.add_shot(f0_1, f1_1, s1)
    slap = {"sh_R": (-1.3, 0.3, 0.2), "el_R": (-0.3, 0, 0), "hips": (0.08, 0, 0.05)}
    C.pose(T, k, slap, -6, slam1 + 10, 1, 8, settle=False)
    C.reaction(T, coll, k, "jubel", hl(0), hold=f1_1 - hl(0), speaking=True, seed=1)
    T.set(b.root, "scale", lambda f: (0, 0, 0), 0, 1)
    T.set(b.root, "location", lambda f: tuple(lap_pos), 0, S[1][0])

    # =================================================================== SZENE 2 – Byte stoppt (fahrt)
    f0_2, f1_2 = S[1]
    bp = f0_2 + 1
    stop = TH.p(-0.55, -1.05, 1.62)                      # direkt vor dem Neonschild
    bpath = path([(bp, lap_pos), (bp + 6, lap_pos + V(-0.2, -0.4, 0.4)), (bp + 13, stop)], ease_out)
    T.set(b.root, "location", lambda f: bpath(f), f0_2, f1_2)
    T.set(b.root, "scale", lambda f: (max(0.0, ease_out_back(min(1, (f - bp) / 6), 2.2)),) * 3, bp - 1, bp + 7)
    T.mul(b.body, "scale", lambda f: (1 + 0.25 * window(f, bp + 12, bp + 22, 1, 8), 1,
                                      1 - 0.2 * window(f, bp + 12, bp + 22, 1, 8)), bp + 12, bp + 22)
    C.trail(T, coll, "s2trail", lambda f: bpath(f), bp, bp + 15, n=8, size=0.06)
    alarm = PR.alarmlicht(coll, "alarm", parent=b.ant, loc=(0, 0, 0.21))
    T.set(alarm.root, "scale", lambda f: (pop(f, bp + 2, 5),) * 3, bp + 1, bp + 8)
    T.set(alarm.root, "scale", lambda f: (0, 0, 0), 0, 1)
    T.set(alarm.spin, "rotation_euler", lambda f: (0, 0, f * 0.6), 0, N - 1)
    green_f = wd(7, "Besseres") - 6
    T.set(alarm.red, "scale", lambda f: (1, 1.1, 1.1) if f < green_f else (0, 0, 0), 0, N)
    T.set(alarm.green, "scale", lambda f: (pop(f, green_f, 5),) * 3, green_f - 1, green_f + 6)
    T.set(alarm.green, "scale", lambda f: (0, 0, 0), 0, 1)
    cue(bp, "whoosh", 1.0)
    cue(aus2[0], "buzz", 1.0)
    C.reaction(T, coll, k, "schock", hl(1), hold=f1_2 - hl(1), seed=2, hat=True)
    cam.add_shot(f0_2, f1_2, fahrt(f0_2, f1_2, (TH.p(0.4, -4.3, 1.85), TH.p(0.35, 0.0, 1.45), 40.0),
                               (TH.p(-0.35, -4.1, 1.8), TH.p(-0.4, 0.0, 1.4), 42.0)))

    # =================================================================== SZENE 3 – Beweis-Brezel (zoom_gesicht)
    f0_3, f1_3 = S[2]
    T.set(b.root, "location", lambda f: tuple(stop), f0_3, f1_3)
    bend = {"hips": (0.3, 0, 0.15), "sh_R": (-1.2, 0.35, 0.3), "el_R": (-0.5, 0, 0), "head": (0.2, 0, 0.2)}
    C.pose(T, k, bend, f0_3 + 1, f1_3 + 2, 6, 6)
    proof = PR.brezel_schild(coll, "beweis", "1,20 €", s=1.2)
    proof.root.parent = k.hand["R"]
    proof.root.location = (0, -0.1, -0.12)
    proof.root.rotation_euler = (math.pi / 2, 0, 0)
    drop12 = hl(11) - 4
    T.set(proof.root, "scale", lambda f: (1.2 * pop(f, f0_3 + 4, 6),) * 3 if f < drop12 else (0, 0, 0), f0_3 + 3, drop12 + 1)
    T.set(proof.root, "scale", lambda f: (0, 0, 0), 0, 1)
    PR.burst(T, coll, "s3konf", "confetti", tuple(face + V(0, 0, 0.75)), f0_3 + 4, 16, 1003, speed=(0.1, 0.3), up=0.2,
             gravity=-0.8, life=(30, 44), size=(1.0, 1.4), flutter=0.7, wobble=0.04, kinds=KINDS)
    C.reaction(T, coll, k, "zweifel", hl(2) - 2, hold=f1_3 - hl(2) + 2, speaking=True, seed=3)
    T.add(k.brow["R"], "location", lambda f: (0, 0, 0.07 * window(f, hl(2) - 4, f1_3, 4, 6)), hl(2) - 4, f1_3)
    cam.add_shot(f0_3, f1_3, zoom_gesicht(f0_3, f1_3, (TH.p(-0.1, -4.2, 1.8), TH.p(-0.15, 0.0, 1.42), 42.0),
                                      (face + V(-0.05, -3.2, -0.05), face + V(-0.05, 0, -0.4), 52.0)))

    # =================================================================== Studio: Requisiten
    KS = ST.p(-1.05, -0.45, 0)
    for i in studio:
        set_kalle(S[i][0], S[i][1], KS, 0.35)
    T.set(ST.objs["spot"].data, "energy", lambda f: 0, 0, 1)
    CTR = ST.p(0.15, 0.6, 2.55)
    big = PR.pastry(coll, "bigbrezel", "brezel", None, (0, 0, 0), 4.2)
    big.location = CTR - V(0, 0, 0.3)
    big.rotation_euler = (0, 0, 0)
    T.set(big, "rotation_euler", lambda f: (0.1 * math.sin(f * 0.05), 0.18 * math.sin(f * 0.07), 0.25 * math.sin(f * 0.04)), 0, N - 1)
    big_on, big_off = S[3][0], S[5][1]
    vis(T, big, big_on, big_off, base=4.2)
    lab_m = L.mat("label_ink", "#F5F1E8", 0.5, emit="#F5F1E8", strength=0.5)
    tagL = PR.preisschild(coll, "tagL", old="", new="0,90 €")
    tagL.root.location = ST.p(-0.85, 0.35, 2.75)
    tagL.root.scale = (0.75, 0.75, 0.75)
    tagL.new.scale = (1, 1, 1)
    L.text("tagL_lab", "KOSTEN", 0.15, lab_m, tagL.flip, (0, -0.04, 0.17), coll, extrude=0.008, font=L.font())
    tagR = PR.preisschild(coll, "tagR", old="", new="0,84 €")
    tagR.root.location = ST.p(1.2, 0.35, 2.75)
    tagR.root.scale = (0.75, 0.75, 0.75)
    L.text("tagR_lab", "PREIS", 0.15, lab_m, tagR.flip, (0, -0.04, 0.17), coll, extrude=0.008, font=L.font())
    old120 = L.text("tagR_old", "1,20 €", 0.24, L.mat("old_gold", "#F2B45A", 0.4, emit="#F2B45A", strength=2.0),
                    tagR.flip, (0, -0.04, -0.12), coll, extrude=0.012, font=L.font())
    for tg, d in ((tagL, 0), (tagR, 4)):
        f_in = S[3][0] + 8 + d
        vis(T, tg.root, f_in, big_off, base=0.75, dur_in=7)
        T.set(tg.flip, "rotation_euler", lambda f, f_in=f_in: (math.pi / 2 * (1 - ease_out_back(min(1, max(0, (f - f_in) / 9)), 1.4)), 0, 0),
              f_in - 1, f_in + 10)

    # =================================================================== SZENE 4 – Kosten und Preis (kreisfahrt)
    f0_4, f1_4 = S[3]
    BS = ST.p(0.15, -0.2, 2.0)
    T.set(b.root, "location", lambda f: tuple(BS), f0_4, S[7][0])
    cue(f0_4 + 1, "whoosh", 0.9)
    C.reaction(T, coll, k, "neutral", hl(3), seed=4)
    cam.add_shot(f0_4, f1_4, kreisfahrt(f0_4, f1_4, CTR + V(0, 0, -0.2), 5.0, 0.0, -14, 14, 34.0))
    cam.whips.append((f0_4, 1))

    # =================================================================== SZENE 5 – Marge, drei Muenzen (push_in)
    f0_5, f1_5 = S[4]
    coins = []
    for q in range(3):
        cn = PR.coin_small(coll, f"marge{q}")
        cn.scale = (2.2, 2.2, 2.2)
        tq = f0_5 + 4 + 5 * q
        hold = BS + V(-0.12 + 0.12 * q, -0.25, 0.32 + 0.03 * (q == 1))
        T.set(cn, "location", lambda f, tq=tq, hold=hold: tuple((CTR - V(0, 0, 0.2)).lerp(hold, ease_out((f - tq) / 9)) +
                                                                V(0, 0, 0.25 * math.sin(math.pi * min(1, max(0, (f - tq) / 9))))),
              tq - 1, S[5][1])
        T.set(cn, "rotation_euler", lambda f: (math.pi / 2, 0, f * 0.2), tq - 1, S[5][1])
        cn_hide = hl(5) - 2 + 2 * q
        T.set(cn, "scale", lambda f, tq=tq, h=cn_hide: (2.2 * pop(f, tq, 5) * (unpop(f, h, 5) if f > h else 1),) * 3, tq - 1, cn_hide + 6)
        T.set(cn, "scale", lambda f: (0, 0, 0), 0, 1)
        coins.append((cn, cn_hide, hold))
        cue(tq + 8, "pop", 0.8)
    T.add(b.root, "location", lambda f: (0, 0, 0.12 * window(f, hl(4) - 6, f1_5, 4, 6)), hl(4) - 6, f1_5)
    cue(hl(4), "ding", 1.0)
    C.reaction(T, coll, k, "staunen", hl(4), hold=f1_5 - hl(4), seed=5)
    cam.add_shot(f0_5, f1_5, push_in(f0_5, f1_5, (ST.p(0.15, -4.4, 2.3), BS + V(0, 0, 0.25), 38.0), k=0.25))

    # =================================================================== SZENE 6 – Schere, Verlust (harter_zoom)
    f0_6, f1_6 = S[5]
    sch = PR.schere(coll, "schere")
    cut = wd(5, "84") - 3
    SC0 = tagR.root.location + V(0.7, -0.4, 0.6)
    SC1 = tagR.root.location + V(0.05, -0.15, 0.05)
    T.set(sch.root, "location", lambda f: tuple(SC0.lerp(SC1, ease_in_out((f - f0_6) / max(1, cut - f0_6)))), f0_6, f1_6)
    T.set(sch.root, "rotation_euler", lambda f: (math.pi / 2, 0, math.radians(-40)), f0_6, f0_6 + 1)
    for piv, sx in sch.blades:
        T.set(piv, "rotation_euler", lambda f, sx=sx: (0, sx * (0.05 + 0.35 * abs(math.sin(f * 0.6))), 0), f0_6, f1_6)
    T.set(sch.root, "scale", lambda f: (pop(f, f0_6 + 1, 5) * (unpop(f, cut + 8, 5) if f > cut + 8 else 1),) * 3, f0_6, cut + 14)
    T.set(sch.root, "scale", lambda f: (0, 0, 0), 0, 1)
    T.set(tagR.flip, "rotation_euler", lambda f: (math.pi * ease_out_back(min(1, max(0, (f - cut - 2) / 10)), 1.3), 0, 0),
          cut + 1, cut + 13)
    T.set(old120, "scale", lambda f: (1, 1, 1) if f < cut + 6 else (0, 0, 0), 0, cut + 7)
    T.set(tagR.new, "scale", lambda f: (pop(f, cut + 5, 6, 1.2),) * 3, cut + 4, cut + 11)
    T.set(tagR.new, "rotation_euler", lambda f: (math.pi, 0, math.pi), 0, 1)
    for q, (cn, h, hold) in enumerate(coins):
        PR.burst(T, coll, f"crumble{q}", "spark", tuple(hold), h + 4, 8, 1060 + q, speed=(0.3, 0.7), up=0.3,
                 gravity=-2.0, life=(14, 22), size=(0.8, 1.2))
    mm = PR.muenze_minus(coll, "minusmuenze")
    mf = hl(5) + 4
    T.set(mm, "location", lambda f: tuple(BS + V(0, -0.3, 0.2 - 1.4 * ease_in(min(1, max(0, (f - mf) / 14))))), mf - 1, f1_6)
    T.set(mm, "rotation_euler", lambda f: (0.3 * (f - mf) * 0.2, 0, 0.4 * (f - mf) * 0.1), mf - 1, f1_6)
    T.set(mm, "scale", lambda f: (1.6 * pop(f, mf, 5),) * 3 if f < f1_6 - 2 else (0, 0, 0), mf - 1, f1_6)
    T.set(mm, "scale", lambda f: (0, 0, 0), 0, 1)
    cue(hl(5), "buzz", 1.0)
    C.reaction(T, coll, k, "schock", hl(5), hold=f1_6 - hl(5), seed=6)
    SCR = ST.objs["screen"].location
    cam.add_shot(f0_6, f1_6, harter_zoom(f0_6, f1_6, (ST.p(0.2, -5.4, 2.4), ST.p(0.3, 0.6, 2.7), 34.0),
                                     (SCR + V(0, -6.2, -1.1), SCR + V(0, 0, -0.5), 42.0), hl(5) - 2, dur=5))

    # =================================================================== SZENE 7 – Schlange aus Tueten (rueckfahrt, Theke)
    f0_7, f1_7 = S[6]
    T.set(b.root, "location", lambda f: tuple(B_TH), f0_7, S[7][0])
    hold7 = {"sh_R": (-2.6, 0.5, 0.3), "sh_L": (-2.6, -0.5, -0.3), "el_R": (-1.5, 0, 0.6), "el_L": (-1.5, 0, -0.6)}
    C.pose(T, k, hold7, f0_7 + 1, f1_7 + 3, 5, 6)
    C.reaction(T, coll, k, "schock", hl(6) - 4, hold=f1_7 - hl(6) + 4, speaking=True, seed=7, hat=False)
    m6 = L.mat("minus_red", "#FF3B3B", 0.4, emit="#FF3B3B", strength=3.0)
    for q in range(7):
        x = -1.25 + q * 0.41
        bag = PR.brezel_tuete(coll, f"tuete{q}")
        bag.location = TH.p(x, -1.0 - 0.05 * (q % 2), top - 0.6)
        T.add(bag, "location", lambda f, q=q: (0, 0, 0.05 * max(0.0, math.sin(f * 0.5 + q))), f0_7, f1_7 + 2)
        tq = f0_7 + 3 + 5 * q
        vis(T, bag, tq, f1_7 + 2, base=1.8, dur_in=5)
        lab = L.text(f"minus6_{q}", "−6ct", 0.07, m6, bag, (0, -0.08, 0.235), coll, extrude=0.006, font=L.font())
        T.set(lab, "scale", lambda f, tq=tq: (pop(f, tq + 3, 5, 1.4),) * 3, tq + 2, tq + 9)
        T.set(lab, "scale", lambda f: (0, 0, 0), 0, 1)
        cue(tq + 3, "pop", 0.7)
    cue(hl(6), "buzz", 1.0)
    cam.add_shot(f0_7, f1_7, rueckfahrt(f0_7, f1_7, (face + V(0, -3.4, -0.1), face + V(0, 0, -0.45), 48.0),
                                    (TH.p(0.0, -5.6, 1.9), TH.p(0.0, 0.0, 1.35), 34.0), ease_out))
    cam.whips.append((f0_7, -1))

    # =================================================================== SZENE 8 – Sonnenbrille (zoom_gesicht)
    f0_8, f1_8 = S[7]
    BS8 = ST.p(0.15, -0.3, 2.2)
    T.set(b.root, "location", lambda f: tuple(BS8), f0_8, S[8][0])
    for lt in ST.lights:
        if lt.data.energy > 0 and lt.name != "studio_spot":
            e0 = lt.data.energy
            T.set(lt.data, "energy", lambda f, e0=e0: e0 * (0.35 if S[7][0] + 2 <= f < S[7][1] else 1.0), 0, N)
    spot = ST.objs["spot"]
    spot.location = ST.p(0.15, -1.6, 5.4)
    spot.rotation_euler = L.look_rot(spot.location, BS8)
    T.set(spot.data, "energy", lambda f: 900 * window(f, S[7][0] + 1, S[7][1] + 2, 4, 4), 0, N)
    shades = PR.sonnenbrille(coll, "shades")
    shades.parent = b.body
    shades.location = (0, -0.24, 0.035)
    on = wd(7, "Aber") - 2
    off = hl(12) + 2
    T.set(shades, "location", lambda f: (0, -0.24, 0.035 + 0.4 * (1 - ease_out((f - on) / 8))), on - 1, on + 9)
    T.set(shades, "location", lambda f: (0, -0.24 - 0.2 * ease_in((f - off) / 6), 0.035 + 0.25 * ease_in((f - off) / 6)),
          off, off + 7)
    T.set(shades, "scale", lambda f: (1, 1, 1) if on - 1 <= f < off + 7 else (0, 0, 0), 0, N)
    C.reaction(T, coll, k, "neutral", hl(7), seed=8)
    cam.add_shot(f0_8, f1_8, zoom_gesicht(f0_8, f1_8, (ST.p(0.4, -4.8, 2.3), ST.p(0.4, 0.4, 2.1), 36.0),
                                      (BS8 + V(0.3, -2.9, 0.0), BS8 + V(0.3, 0, -0.3), 46.0)))
    cam.whips.append((f0_8, 1))

    # =================================================================== SZENE 9 – Reste-Tonne, 40 Brezeln (schwenk)
    f0_9, f1_9 = S[8]
    BIN = ST.p(-0.1, 0.55, 0.0)
    PILE = ST.p(1.25, 0.6, 0.0)
    ped = L.box("bin_ped", (1.3, 0.9, 0.9), L.mat("pedestal", "#2B2750", 0.5), None, BIN + V(0.2, 0, 0.45), coll)
    ped2 = L.box("pile_ped", (1.2, 1.0, 0.9), L.mat("pedestal", "#2B2750", 0.5), None, PILE + V(0, 0, 0.45), coll)
    tonne = PR.muelltonne_reste(coll, "tonne")
    tonne.root.location = BIN + V(0, 0, 0.9)
    for o in (ped, ped2, tonne.root):
        vis(T, o, f0_9, None, dur_in=6)
    T.set(tonne.lid, "rotation_euler", lambda f: (-1.9 * ease_out_back(min(1, max(0, (f - f0_9 - 4) / 8)), 1.6), 0, 0),
          f0_9 + 3, f0_9 + 13)
    T.add(tonne.bin, "rotation_euler", lambda f: (0, 0.06 * math.sin(f * 0.9), 0), f0_9, f1_9)
    rr = random.Random(909)
    top_pile = PILE + V(0, 0, 0.9)
    for q in range(40):
        tq = f0_9 + 6 + q * 0.9
        lay = int(q / 12)
        a = rr.uniform(0, 6.28)
        rad = (0.42 - 0.12 * lay) * math.sqrt(rr.random())
        dst = top_pile + V(rad * math.cos(a), rad * math.sin(a), 0.03 + 0.08 * lay)
        src = BIN + V(0, -0.1, 1.75)
        bzp = PR.pastry(coll, f"rest{q}", "brezel", None, (0, 0, 0), 0.85)

        def bl(f, tq=tq, dst=dst, src=src):
            t = min(1.0, max(0.0, (f - tq) / 12))
            p = src.lerp(dst, ease_in_out(t))
            p.z += 0.6 * math.sin(math.pi * t)
            return tuple(p)
        T.set(bzp, "location", bl, tq - 1, tq + 13)
        T.set(bzp, "rotation_euler", lambda f, q=q: (q * 0.4, q * 0.2, q * 0.7), tq - 1, tq)
        T.set(bzp, "scale", lambda f, tq=tq: (0.85 * pop(f, tq, 4),) * 3 if f < S[10][0] + 4 else (0.85 * unpop(f, S[10][0] + 4, 6),) * 3,
              tq - 1, S[10][0] + 11)
        T.set(bzp, "scale", lambda f: (0, 0, 0), 0, 1)
        if q % 5 == 0:
            cue(tq + 12, "pop", 0.5)
    cue(f0_9 + 2, "whoosh", 0.9)
    C.reaction(T, coll, k, "staunen", hl(8), hold=f1_9 - hl(8), seed=9)
    cam.add_shot(f0_9, f1_9, schwenk(f0_9, f1_9, (ST.p(-0.6, -4.2, 2.45), BIN + V(0, 0, 1.85), 40.0),
                                 (ST.p(0.6, -4.2, 2.45), PILE + V(0, 0, 1.75), 40.0)))
    T.set(b.root, "location", lambda f: tuple(ST.p(0.0, -0.3, 2.2)), f0_9, S[10][0])

    # =================================================================== SZENE 10 – 17:00, halber Preis (fahrt)
    f0_10, f1_10 = S[9]
    clk = PR.wall_clock(coll, "uhr", r=0.45)
    CLK = ST.p(-1.0, 1.4, 3.35)
    clk.root.location = CLK
    vis(T, clk.root, S[8][0], None)
    jump = hl(9, 0) - 3
    T.set(clk.hands[0], "rotation_euler", lambda f: (0, math.radians(lerp(300, 510, ease_out_back(min(1, max(0, (f - jump) / 8)), 1.4))), 0),
          0, N - 1)
    T.set(clk.hands[1], "rotation_euler", lambda f: (0, math.radians(lerp(180, 720, ease_out_back(min(1, max(0, (f - jump) / 8)), 1.4))), 0),
          0, N - 1)
    dig = L.text("uhr_17", "17:00", 0.22, L.mat("dig_gold", "#F2B45A", 0.4, emit="#F2B45A", strength=4.0), None,
                 tuple(CLK + V(0, -0.05, -0.65)), coll, extrude=0.012, font=L.font())
    vis(T, dig, jump + 2, None, dur_in=6)
    halb = PR.neonschild(coll, "halb", "½ PREIS", color="#3DDC84", width=0.95, height=0.36, size=0.2)
    halb.root.location = PILE + V(0, -0.15, 1.75)
    hp = hl(9, 2) - 3
    vis(T, halb.root, hp, None, dur_in=7)
    T.set(halb.root, "rotation_euler", lambda f: (math.pi / 2 * (1 - ease_out_back(min(1, max(0, (f - hp) / 9)), 1.4)), 0, 0),
          hp - 1, hp + 10)
    PR.neon_flacker(T, halb, hp, N - 1, seed=31, strength=0.5)
    C.reaction(T, coll, k, "jubel", hl(9), hold=f1_10 - hl(9), seed=10)
    cam.add_shot(f0_10, f1_10, fahrt(f0_10, f1_10, (ST.p(-0.8, -4.0, 2.6), CLK + V(0, 0, -0.5), 40.0),
                               (ST.p(0.7, -4.0, 2.3), PILE + V(0, 0, 1.6), 40.0)))

    # =================================================================== SZENE 11 – Tonne wird Kasse, +24 € (push_in)
    f0_11, f1_11 = S[10]
    tw = f0_11 + 3
    T.add(tonne.root, "rotation_euler", lambda f: (0, 0, 2 * math.pi * ease_in_out((f - tw) / 12)), tw, tw + 12)
    T.set(tonne.bin, "scale", lambda f: (1, 1, 1) if f < tw + 6 else (0, 0, 0), 0, tw + 7)
    T.set(tonne.kasse, "scale", lambda f: (pop(f, tw + 6, 6, 1.15),) * 3, tw + 5, tw + 13)
    dr = hl(10) - 6
    T.set(tonne.drawer, "location", lambda f: (0, -0.3 * ease_out_back(min(1, max(0, (f - dr) / 6)), 1.5), 0), dr - 1, N)
    col = PR.coin_column(coll, "coins11", 24, spacing=0.035)
    COL = BIN + V(0.5, -0.15, 0.9)
    col.root.location = COL
    col.root.scale = (1.4, 1.4, 1.0)
    for q, cn in enumerate(col.coins):
        tq = dr + 4 + q * 0.7
        T.set(cn, "scale", lambda f, tq=tq: (min(1.0, ease_out((f - tq) / 3)),) * 3, tq - 1, tq + 4)
        T.set(cn, "scale", lambda f: (0, 0, 0), 0, 1)
    PR.burst(T, coll, "s11coins", "coinp", tuple(BIN + V(0, -0.35, 1.2)), dr + 2, 14, 1101, speed=(1.0, 1.8), up=1.0,
             gravity=-5.0, life=(18, 26), size=(1.0, 1.3), dir_bias=(0.8, 0, 0.3))
    cue(hl(10), "ding", 1.0)
    C.reaction(T, coll, k, "jubel", hl(10), hold=f1_11 - hl(10), seed=11)
    cam.add_shot(f0_11, f1_11, push_in(f0_11, f1_11, (ST.p(0.15, -4.6, 2.3), BIN + V(0.3, 0, 1.3), 38.0), k=0.25))
    cam.whips.append((f0_11, 1))
    # Studio-Requisiten nach Szene 11 weg (Szene 12-14 an der Theke, Loop)
    for o in (ped, ped2):
        T.set(o, "scale", lambda f, o=o: (unpop(f, S[10][1] + 2, 3),) * 3, S[10][1], S[10][1] + 6)

    # =================================================================== SZENE 12 – zahlen alle voll? (zoom_gesicht, Theke)
    f0_12, f1_12 = S[11]
    T.set(b.root, "location", lambda f: tuple(B_TH), f0_12, S[12][0])
    C.reaction(T, coll, k, "staunen", hl(11) - 2, hold=f1_12 - hl(11) + 4, speaking=True, seed=12)
    PR.burst(T, coll, "s12drop", "crumb", tuple(K + V(-0.4, -0.55, 1.4)), drop12, 6, 1201, speed=(0.1, 0.3), up=0.1,
             gravity=-6.0, life=(16, 22), size=(1.2, 1.6))
    PR.neon_flacker(T, sign, f0_12, f1_12, seed=77, strength=0.5)
    cam.add_shot(f0_12, f1_12, zoom_gesicht(f0_12, f1_12, (TH.p(-0.2, -4.4, 1.85), TH.p(-0.2, 0.0, 1.45), 40.0),
                                      (face + V(-0.38, -3.7, 0.05), face + V(-0.4, 0, -0.3), 44.0)))
    cam.whips.append((f0_12, -1))

    # =================================================================== SZENE 13 – Neon-Plakat (schwenk)
    f0_13, f1_13 = S[12]
    B13 = TH.p(1.3, -0.5, 1.95)
    b13 = path([(f0_13, B_TH), (f0_13 + 8, B_TH + V(0.4, -0.2, 0.15)), (f0_13 + 16, B13)], ease_in_out)
    T.set(b.root, "location", lambda f: b13(f), f0_13, S[13][0])
    plakat = PR.neon_plakat(coll, "plakat", ["AB 17 UHR –", "RESTE ½ PREIS"], color="#3DDC84", size=0.17)
    plakat.root.location = TH.p(0.75, 2.32, 2.92)
    snap = f0_13 + 3
    T.set(plakat.frame, "scale", lambda f: (ease_out((f - snap) / 6),) * 3, snap - 1, snap + 7)
    n_l = len(plakat.letters)
    for q, o in enumerate(plakat.letters):
        tq = snap + 4 + 46 * q / n_l
        T.set(o, "scale", lambda f, tq=tq: (pop(f, tq, 4, 1.25),) * 3, tq - 1, tq + 5)
    cue(snap, "whoosh", 0.9)
    cue(snap + 52, "ding", 1.0)
    T.mul(b.body, "scale", lambda f: (1 + 0.1 * window(f, snap - 2, snap + 6, 1, 4),) * 3, snap - 2, snap + 6)
    C.reaction(T, coll, k, "staunen", hl(12), hold=f1_13 - hl(12), seed=13)
    cam.add_shot(f0_13, f1_13, schwenk(f0_13, f1_13, (TH.p(0.45, -4.0, 1.95), B_TH + V(0, 0, -0.35), 44.0),
                                 (TH.p(0.6, -4.4, 2.5), TH.p(0.65, 1.0, 2.6), 42.0)))

    # =================================================================== SZENE 14 – Schild behalt i (Loop)
    f0_14, f1_14 = S[13]
    grabp = {"sh_R": (-1.3, 0.35, 0.2), "el_R": (-0.35, 0, 0)}
    C.pose(T, k, grabp, grab14 - 2, N + 10, 4, 8)
    C.reaction(T, coll, k, "jubel", hl(13), hold=f1_14 - hl(13) - 4, speaking=True, seed=14)
    T.add(b.body, "rotation_euler", lambda f: (0.6 * window(f, f0_14 + 4, N - 18, 5, 6), 0, 0), f0_14, N - 16)
    back = N - 16
    T.set(b.root, "location", lambda f: tuple(B_TH.lerp(lap_pos, ease_in((f - back) / 10)) if f > back else B_TH), f0_14, N)
    T.set(b.root, "scale", lambda f: (1 - ease_in((f - back - 2) / 9),) * 3 if f > back else (1, 1, 1), back, N)
    PR.burst(T, coll, "konf14", "confetti", tuple(TH.p(1.25, -0.7, top + 0.45)), N - 22, 40, 1402, speed=(2.0, 3.4),
             up=1.6, spread=1.0, gravity=-2.5, life=(55, 80), size=(1.2, 1.8), drag=1.2, flutter=0.6, wobble=0.04,
             kinds=KINDS, dir_bias=(-1.2, 0.3, 0.6))
    cam.add_shot(f0_14, N, fahrt(f0_14, N - 7, (TH.p(0.0, -4.4, 1.85), TH.p(0.0, 0.0, 1.45), 42.0), s1(0)))
    cam.whips.append((f0_14, -1))

    # Byte-Ausdruecke
    sched = [(0, "neutral"), (S[1][0], "surprised"), (S[2][0], "serious"), (S[3][0], "happy"), (S[4][0], "happy"),
             (S[5][0], "worried"), (S[6][0], "serious"), (S[7][0], "wink"), (S[8][0], "happy"), (S[10][0], "happy"),
             (S[12][0], "wink"), (S[13][0], "serious")]
    C.byte_face(T, b, sched, 0, N - 1)

    def focus(f):
        for i in studio:
            if S[i][0] <= f < S[i][1]:
                return V(T.loc(b.root, f))
        return V(T.loc(k.root, f)) + V(0, -0.25, 1.95)
    W.cam.focus_fn = focus
