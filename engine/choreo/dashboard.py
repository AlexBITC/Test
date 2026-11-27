"""Regie fuer 'Kalles Ausgaben-Dashboard' (folge-07-dashboard). Szenen-Index 0..12 = Szene 1..13.

Ablauf: Theke -> Studio (Analyse) -> Theke (Schreck) -> Studio -> Theke (Dashboard-Reveal) -> Studio (Ersparnis) -> Theke (Loop).
Kalle macht nur zwei Handgriffe: Ordner zum Laptop schieben (Szene 3), einmal klicken (Szene 11).
Running Gags: Geister-Kaffeemaschine (Szene 1, 2, 6, 11, kurz 13), Kalles Kaffeetasse (Szene 1, 7).
Requisiten: assets/props/dashboard.py, Bildschirm: assets/screens/dashboard.py (screen_dashboard in Aufbaustufen).
Kamera-Presets nie zweimal hintereinander (Szene 12 als Kranfahrt von unten nach oben, Szene 11 Schwenk).
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
from choreo.black_friday import kreisfahrt
from choreo.viral import laptop_display

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "props"))
import dashboard as DP  # noqa: E402

FPS = 30
zoom_gesicht = schwenk = kranfahrt = fahrt


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
    T.set(b.body, "rotation_euler", lambda f: (0, 0, 0), 0, 1)
    T.set(b.root, "rotation_euler", lambda f: (0, 0, 0), 0, 1)
    k.cloth.scale = (0, 0, 0)                       # Tuch weg: Kalle haelt die Tasse

    def set_kalle(f0, f1, loc, rz=0.0):
        T.set(k.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(k.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)

    def set_byte(f0, f1, loc):
        T.set(b.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)

    theke = [i for i, s in enumerate(sc) if s["set"] == "theke"]
    studio = [i for i, s in enumerate(sc) if s["set"] == "studio"]
    K = V(TH.kalle)
    face = K + V(0, -0.25, 1.95)
    for i in theke:
        set_kalle(S[i][0], S[i][1], K, 0.0)
    for i in studio:
        set_kalle(S[i][0], S[i][1], ST.p(-7, 3, 0), 0.0)

    # ------------------------------------------------------------ Theke: Laptop, Ladenfront, Hintergrund
    lap = TH.objs["laptop"]
    LAP = TH.p(0.45, -0.36, top)
    LS = 1.35
    lap.root.location = LAP
    lap.root.scale = (LS, LS, LS)
    laptop_display(lap)
    TH.objs["basket"].location.x += 0.45            # Brotkorb etwas zur Seite (Laptop frei), wie Folge viral
    ROT_FRONT, ROT_KALLE = math.radians(-18), math.radians(-138)
    turn0 = S[8][0] + 6                              # Szene 9: Byte dreht den Laptop zu Kalle
    turn1 = turn0 + 16

    def lap_rot(f):
        if S[8][0] <= f < S[11][0]:
            return lerp(ROT_FRONT, ROT_KALLE, ease_in_out((f - turn0) / (turn1 - turn0)))
        return ROT_FRONT
    T.set(lap.root, "rotation_euler", lambda f: (0, 0, lap_rot(f)), 0, N - 1)

    def lap_pt(x, y, z, rz=ROT_FRONT):
        m = V((math.cos(rz), math.sin(rz), 0)), V((-math.sin(rz), math.cos(rz), 0))
        loc = V((x * LS, y * LS, z * LS))
        return LAP + V((m[0].x * loc.x + m[1].x * loc.y, m[0].y * loc.x + m[1].y * loc.y, loc.z))
    scr_local = (0, 0.2 + 0.2 * math.sin(math.radians(12)), 0.03 + 0.2 * math.cos(math.radians(12)))
    SCR = lap_pt(*scr_local)
    SCR_K = lap_pt(*scr_local, rz=ROT_KALLE)
    lap_out = SCR + V(0.04, -0.12, 0)
    PR.ambient_motes(T, coll, "th_dust", tuple(TH.p(0, 0.2, 1.9)), (2.2, 1.2, 0.9), 30, 701, 0, N - 1, drift=0.08)
    PR.ambient_motes(T, coll, "st_dust", tuple(ST.p(0, 0.6, 2.4)), (2.4, 1.6, 1.2), 30, 702, 0, N - 1,
                     color_kind="sparkt", drift=0.06, scale=0.6)
    front = DP.ladenfront(coll, "ladenfront", breite=12.0, hoehe=5.5)
    front.root.location = TH.p(0.3, -3.1, 0)
    T.set(front.root, "scale", lambda f: (1, 1, 1) if (S[8][0] <= f < S[9][0] or S[10][0] <= f < S[10][1]) else (0, 0, 0),
          0, N)

    # ------------------------------------------------------------ Geister-Kaffeemaschine (Running Gag)
    ghost = DP.geister_kaffeemaschine(coll, "geist_kaffee", "49 €/Monat")
    DP.geist_schweben(T, ghost, 0, N - 1, seed=4)
    G1 = K + V(-0.78, 0.62, 1.72)
    G2 = K + V(-0.4, 0.42, 2.12)
    ghost.root.scale = (1.15,) * 3

    # ------------------------------------------------------------ Kaffeetasse (Szene 1, 7, 13)
    cup = DP.kaffeetasse(coll, "tasse")
    cup.root.parent = k.hand["R"]
    cup.root.location = (0.0, -0.08, -0.06)
    cup.root.rotation_euler = (math.pi / 2, 0, 0)
    hold_cup = {"sh_R": (-0.75, 0, 0.35), "el_R": (-1.55, 0, 0)}
    cup_t = DP.kaffeetasse(coll, "tasse_theke")      # abgestellte Tasse (Szene 3)
    cup_t.root.location = TH.p(-0.75, -0.42, top)

    # =================================================================== SZENE 1 – Geister-Kaffeemaschine (push_in, schnell)
    f0_1, f1_1 = S[0]
    B1 = face + V(0.72, -0.42, -0.05)
    brake = 12
    b1 = path([(-8, lap_out + V(0, 0.1, 0)), (0, lap_out + V(0.0, -0.2, 0.15)), (brake - 4, B1 + V(0.05, -0.15, 0.08)),
               (brake, B1)], ease_out)
    T.set(b.root, "location", lambda f: b1(f), 0, S[1][0])
    T.set(b.root, "scale", lambda f: (min(1.0, 0.72 + 0.28 * ease_out((f + 3) / 8)),) * 3, 0, 8)
    T.mul(b.body, "scale", lambda f: (1 - 0.16 * window(f, brake - 1, brake + 10, 1, 8), 1,
                                      1 + 0.18 * window(f, brake - 1, brake + 10, 1, 8)), brake - 2, brake + 12)
    C.trail(T, coll, "s1trail", lambda f: b1(f), 0, brake + 4, n=8, size=0.06)
    point1 = wd(0, "kaffeemaschine") - 6
    C.byte_arm(T, b, "R", (-1.7, 0.0, -0.9), point1, S[1][0] + 4, ramp=5)       # zeigt hinter Kalle
    C.byte_hand(T, b, "R", "point", point1, S[1][0] + 4)
    T.add(b.body, "rotation_euler", lambda f: (0, 0, -0.45 * window(f, point1, S[1][0] + 4, 5, 6)), point1, S[1][0] + 6)
    T.set(ghost.root, "location", lambda f: tuple(G1), 0, S[1][0])
    C.pose(T, k, hold_cup, -10, S[2][0] + 2, 1, 6, settle=False)
    T.set(cup.root, "scale", lambda f: (1, 1, 1) if (f < S[2][0] or S[6][0] <= f) else (0, 0, 0), 0, N)
    T.set(cup_t.root, "scale", lambda f: (1, 1, 1) if S[2][0] <= f < S[3][0] else (0, 0, 0), 0, N)
    # Kalle erstarrt (Augen gross, Kopf zurueck)
    frz = hl(0) + 2
    for side in ("R", "L"):
        T.mul(k.eye[side], "scale", lambda f: (1 + 0.55 * window(f, frz, f1_1, 2, 6),) * 3, frz, f1_1)
    T.add(k.head, "rotation_euler", lambda f: (-0.1 * window(f, frz, f1_1, 3, 6), 0, 0), frz, f1_1)
    T.add(k.mouth, "location", lambda f: (0, 0, -0.03 * window(f, frz, f1_1, 3, 6)), frz, f1_1)
    cue(0, "whoosh", 0.8)
    cue(hl(0), "buzz", 1.0)
    S1A = (TH.p(0.4, -4.1, 1.95), TH.p(-0.05, 0.0, 1.72), 40.0)
    s1 = push_in(f0_1, f1_1, S1A, k=0.22)
    S1W = (TH.p(0.6, -4.9, 2.0), TH.p(-0.05, 0.0, 1.72), 40.0)

    def shot1(f):
        t = ease_out(min(1.0, (f + 6) / 30))
        p0, t0_, l0 = S1W
        p1, t1_, l1 = s1(f)
        return (V(p0).lerp(V(p1), t), V(t0_).lerp(V(t1_), t), lerp(l0, l1, t))
    cam.add_shot(f0_1, f1_1, shot1)

    # =================================================================== SZENE 2 – Quatsch! (zoom_gesicht)
    f0_2, f1_2 = S[1]
    away = f0_2 + 4
    T.set(k.root, "rotation_euler", lambda f: (0, 0, -0.55 * ease_in_out((f - away) / 10)), f0_2, f1_2)
    wave = {"sh_L": (-1.6, 0, -0.5), "el_L": (-0.9, 0, 0)}
    C.pose(T, k, wave, f0_2, f0_2 + 22, 4, 6)
    T.add(k.el["L"], "rotation_euler", lambda f: (0, 0, 0.5 * math.sin((f - f0_2) * 0.9) * window(f, f0_2 + 2, f0_2 + 22, 3, 4)),
          f0_2, f0_2 + 22)
    g2 = path([(f0_2, G1), (f0_2 + 18, G2), (f1_2, G2 + V(0.08, -0.05, -0.02))], ease_in_out)
    T.set(ghost.root, "location", lambda f: g2(f), f0_2, S[2][0])
    T.set(ghost.root, "rotation_euler", lambda f: (0, 0, 0.5 * ease_in_out((f - f0_2 - 8) / 14)), f0_2, S[2][0])
    T.set(ghost.root, "rotation_euler", lambda f: (0, 0, 0), 0, 1)
    C.reaction(T, coll, k, "zweifel", hl(1) - 2, hold=f1_2 - hl(1) + 2, speaking=True, seed=2)
    set_byte(f0_2, S[2][0], B1)
    cam.add_shot(f0_2, f1_2, zoom_gesicht(f0_2, f1_2, (TH.p(-0.35, -4.1, 2.0), TH.p(-0.35, 0.2, 1.75), 40.0),
                                         (face + V(-0.15, -3.0, 0.12), face + V(-0.2, 0.3, -0.12), 46.0)))

    # =================================================================== SZENE 3 – Ordner zum Laptop (push_in auf den Laptop)
    f0_3, f1_3 = S[2]
    ordner = DP.ordner_kontoauszuege(coll, "ordner")
    shove = wd(2, "zieh") - 4
    O0 = TH.p(-0.4, -0.45, top)
    O1 = lap_pt(-0.42, -0.08, 0)
    T.set(ordner.root, "location", lambda f: tuple(O0.lerp(O1, ease_out((f - shove) / 14))), f0_3, S[3][0])
    T.set(ordner.root, "rotation_euler", lambda f: (0, 0, math.radians(-15)), f0_3, f0_3 + 1)
    T.set(ordner.root, "scale", lambda f: (1.25,) * 3 if f0_3 <= f < S[3][0] else (0, 0, 0), 0, N)
    push = {"sh_R": (-1.05, 0, -0.15), "sh_L": (-1.05, 0, 0.15), "el_R": (-0.5, 0, 0), "el_L": (-0.5, 0, 0), "hips": (0.18, 0, 0)}
    C.pose(T, k, push, shove - 6, shove + 18, 6, 8)
    T.add(k.head, "rotation_euler", lambda f: (0, 0, 0.15 * window(f, f0_3, shove, 4, 4)), f0_3, shove + 2)  # widerwillig
    DP.blaetter_einsaugen(T, coll, "blatt", lambda f: tuple(V(T.loc(ordner.root, f)) + V(0, 0, 0.5)),
                          SCR, shove + 10, n=12, seed=3)
    B3 = lap_pt(0.62, 0.05, 0.62)
    set_byte(f0_3, S[3][0], B3)
    C.byte_arm(T, b, "L", (-1.4, 0.4, 0.4), wd(2, "hier") - 4, f1_3, ramp=4)     # zeigt auf den Bildschirm
    C.byte_hand(T, b, "L", "point", wd(2, "hier") - 4, f1_3)
    C.reaction(T, coll, k, "neutral", hl(2), seed=3)
    cam.add_shot(f0_3, f1_3, push_in(f0_3, f1_3, (SCR + V(-0.85, -3.0, 0.5), SCR + V(-0.38, 0, 0.12), 34.0), k=0.3))

    # =================================================================== Studio: Faecher, Podest
    BS = ST.p(0.0, -0.4, 2.05)
    SCRN = ST.objs["screen"].location
    ped = L.box("fach_podest", (3.5, 0.7, 1.35), L.mat("pedestal", "#2B2750", 0.5), None, ST.p(0.2, 0.9, 0.675), coll)
    faecher = DP.kategorien_faecher(coll, "faecher")
    faecher.root.location = ST.p(0.2, 0.9, 1.35)
    FACH = [V(faecher.root.location) + V(fb.location) + V(0, 0, 0.25) for fb in faecher.faecher]
    T.set(ST.objs["spot"].data, "energy", lambda f: 0, 0, 1)

    # =================================================================== SZENE 4 – Tornado, 1.200 Buchungen (kreisfahrt)
    f0_4, f1_4 = S[3]
    set_byte(f0_4, S[4][0], BS)
    split = wd(3, "sortiert") - 6
    DP.kaertchen_tornado(T, coll, "karte", tuple(BS), f0_4 + 1, split, FACH, n=110, seed=5, radius=0.85)
    T.add(b.body, "rotation_euler", lambda f: (0, 0, 0.35 * math.sin((f - f0_4) * 0.2) * window(f, f0_4, split, 4, 6)), f0_4, split)
    C.byte_arm(T, b, "L", (-2.4, -0.6, 0), f0_4 + 2, split, ramp=4)
    C.byte_arm(T, b, "R", (-2.4, 0.6, 0), f0_4 + 2, split, ramp=4)
    cue(f0_4 - 5, "whoosh", 1.0)
    cam.whips.append((f0_4, 1))
    cam.add_shot(f0_4, f1_4, kreisfahrt(f0_4, f1_4, BS + V(0, 0, -0.3), 4.0, 0.45, -24, 18, 34.0))

    # =================================================================== SZENE 5 – drei rote Punkte (push_in)
    f0_5, f1_5 = S[4]
    set_byte(f0_5, S[5][0], BS + V(-0.55, 0, 0.1))
    WP = [BS + V(0.05, -0.45, 0.75), BS + V(0.5, -0.5, 0.92), BS + V(0.95, -0.45, 0.75)]
    wps = []
    t_dots = [wd(4, "drei") + 2, wd(4, "rote") + 2, wd(4, "punkte") + 2]
    for q in range(3):
        w = DP.warnpunkt_rot(coll, f"warn{q}")
        tq = t_dots[q]
        src = FACH[4]

        def wl(f, tq=tq, q=q, src=src):
            t = ease_out_back(min(1.0, max(0.0, (f - tq) / 10)), 1.4)
            p = V(src).lerp(WP[q], min(1.0, max(0.0, (f - tq) / 10)))
            p.z += 0.5 * math.sin(math.pi * min(1.0, max(0.0, (f - tq) / 10)))
            return tuple(p + V(0, 0, 0.05 * math.sin(f * 0.15 + q)))
        T.set(w.root, "location", wl, tq - 1, N - 1)
        T.set(w.root, "scale", lambda f, tq=tq: (0.65 * pop(f, tq, 6),) * 3, tq - 1, tq + 7)
        T.set(w.root, "scale", lambda f: (0, 0, 0), 0, 1)
        DP.warnpunkt_pulsieren(T, w, tq, N - 1, seed=q)
        cue(tq + 2, "pop", 0.9)
        wps.append(w)
    C.byte_arm(T, b, "R", (-2.2, 0.5, -0.3), f0_5 + 4, f1_5 - 4, ramp=5)
    C.byte_hand(T, b, "R", "point", f0_5 + 4, f1_5 - 4)
    cam.add_shot(f0_5, f1_5, push_in(f0_5, f1_5, (ST.p(0.4, -4.6, 2.45), WP[1] + V(0, 0, -0.3), 34.0), k=0.3))

    # =================================================================== SZENE 6 – 49 Euro, Geist taucht auf (schwenk Screen -> Geist)
    f0_6, f1_6 = S[5]
    burst1 = wd(5, "49") - 2
    DP.warnpunkt_platzen(T, coll, wps[0], burst1, WP[0], seed=1)
    T.set(wps[0].root, "scale", lambda f: (0, 0, 0), burst1 + 6, N)
    GS = WP[0] + V(-0.15, 0.05, -0.35)
    T.set(ghost.root, "location", lambda f: tuple(GS + V(0, 0, 0.25 * (1 - ease_out((f - burst1) / 12)))), f0_6, S[6][0])
    T.set(ghost.root, "scale", lambda f: (1.15 * pop(f, burst1 + 1, 8),) * 3 if f >= burst1 else (0, 0, 0), f0_6 - 1, burst1 + 10)
    T.set(ghost.root, "scale", lambda f: (1.15,) * 3, burst1 + 10, burst1 + 11)
    T.set(ghost.root, "scale", lambda f: (0, 0, 0), S[3][0], S[3][0] + 1)        # im Studio erst ab dem Platzen
    T.set(ghost.root, "scale", lambda f: (1.15,) * 3, 0, 1)
    for piv in ghost.chains:
        T.add(piv, "rotation_euler", lambda f: (0.5 * math.sin(f * 1.9) * window(f, burst1, f1_6, 2, 10), 0, 0), burst1, f1_6)
    cue(wd(5, "49") + 4, "pop", 1.0)                       # Zeile 1 gefuellt
    set_byte(f0_6, S[6][0], BS + V(0.55, 0.05, 0.1))
    cam.add_shot(f0_6, f1_6, schwenk(f0_6, f1_6, (ST.p(0.3, -5.0, 3.0), SCRN + V(0.2, 0, -0.35), 34.0),
                                     (ST.p(-0.3, -3.8, 2.4), GS + V(0, 0, 0.3), 40.0)))

    # =================================================================== SZENE 7 – Kalle verschluckt sich (harter_zoom)
    f0_7, f1_7 = S[6]
    T.set(ghost.root, "scale", lambda f: (0, 0, 0), f0_7, S[7][0])
    sip = {"sh_R": (-1.35, 0, 0.55), "el_R": (-1.75, 0, 0)}
    spit = wd(6, "2022?!") - 2
    drop = spit + 6
    C.pose(T, k, sip, f0_7 - 2, drop, 1, 4, settle=False)
    for side, sx in (("R", -1), ("L", 1)):
        T.add(k.sh[side], "rotation_euler", lambda f, sx=sx: (0, -sx * 0.4 * window(f, drop, f1_7, 3, 10), 0), drop, f1_7)
    mouth = face + V(0, -0.12, -0.17)
    DP.kaffee_spritzer(T, coll, "spritz", tuple(mouth), spit, n=26, seed=7, slow=0.45, richtung=(0.1, -1, 0.35))
    cup_fall = DP.kaffeetasse(coll, "tasse_fall")
    c_start = K + V(-0.33, -0.5, 1.62)

    def cf(f):
        t = max(0.0, (f - drop) / FPS) * 0.5           # Zeitlupe
        p = c_start + V(0.05, -0.35 * t, -4.9 * t * t)
        return tuple(V((p.x, p.y, max(top + 0.02, p.z))))
    T.set(cup_fall.root, "location", cf, drop - 1, S[7][0])
    T.set(cup_fall.root, "rotation_euler", lambda f: (2.4 * ease_out((f - drop) / 26), 0.6 * ease_out((f - drop) / 26), 0), drop - 1, S[7][0])
    T.set(cup_fall.root, "scale", lambda f: (1, 1, 1) if drop <= f < S[7][0] else (0, 0, 0), 0, N)
    T.set(cup.root, "scale", lambda f: (0, 0, 0) if drop <= f < S[12][0] else ((1, 1, 1) if (f < S[2][0] or S[6][0] <= f) else (0, 0, 0)),
          0, N)
    DP.kaffee_spritzer(T, coll, "spritz2", tuple(c_start + V(0, -0.05, 0.05)), drop + 2, n=16, seed=8, slow=0.4,
                       richtung=(0.3, -0.6, 0.7))
    C.reaction(T, coll, k, "schock", hl(6) - 26, hold=f1_7 - hl(6) + 26, speaking=True, seed=7, hat=True)
    for side in ("R", "L"):                            # Augen springen raus
        T.mul(k.eye[side], "scale", lambda f: (1 + 0.5 * window(f, spit, spit + 30, 2, 12),) * 3, spit, spit + 30)
        T.add(k.eye[side], "location", lambda f: (0, -0.06 * window(f, spit, spit + 26, 2, 12), 0), spit, spit + 26)
    cue(f0_7 - 5, "whoosh", 1.0)
    cue(spit, "buzz", 1.0)
    cam.whips.append((f0_7, -1))
    cam.add_shot(f0_7, f1_7, harter_zoom(f0_7, f1_7, (TH.p(-0.1, -4.3, 1.9), TH.p(-0.15, 0, 1.6), 38.0),
                                         (face + V(0, -2.7, 0.05), face + V(0, 0, -0.2), 48.0), spit - 3, dur=5))

    # =================================================================== SZENE 8 – Kasse doppelt, Strom verlaengert (fahrt links -> rechts)
    f0_8, f1_8 = S[7]
    set_byte(f0_8, S[8][0], BS + V(0.1, 0.05, 0.1))
    b2, b3 = wd(7, "doppelt") - 2, wd(7, "still") - 2
    DP.warnpunkt_platzen(T, coll, wps[1], b2, WP[1], seed=2)
    DP.warnpunkt_platzen(T, coll, wps[2], b3, WP[2], seed=3)
    T.set(wps[1].root, "scale", lambda f: (0, 0, 0), b2 + 6, N)
    T.set(wps[2].root, "scale", lambda f: (0, 0, 0), b3 + 6, N)
    LEFT, RIGHT = BS + V(-1.2, -0.3, -0.05), BS + V(1.3, -0.3, -0.1)
    box_a = DP.software_box(coll, "kasse_a")
    box_g = DP.software_box(coll, "kasse_g", geist=True)
    box_a.root.location = LEFT + V(-0.22, 0, 0)
    box_g.root.location = LEFT + V(0.22, 0, 0.05)
    for o, d in ((box_a.root, 0), (box_g.root, 3)):
        T.set(o, "scale", lambda f, d=d: (1.6 * pop(f, b2 + 2 + d, 7),) * 3 if f0_8 <= f < S[8][0] else (0, 0, 0), 0, N)
    T.add(box_g.root, "location", lambda f: (0, 0, 0.05 * math.sin(f * 0.17)), f0_8, S[8][0])
    meter = DP.stromzaehler(coll, "stromzaehler")
    meter.root.location = RIGHT
    meter.root.scale = (1.5,) * 3
    T.set(meter.root, "scale", lambda f: (1.5 * pop(f, b3 + 2, 7),) * 3 if f0_8 <= f < S[8][0] else (0, 0, 0), 0, N)
    DP.zaehler_drehen(T, meter, b3, S[8][0], speed=1.1)
    st = PR.stempel(coll, "stempel")
    hit_st = wd(7, "verlängert") + 6
    SP = RIGHT + V(0, -0.35, 0.3)
    T.set(st, "location", lambda f: tuple(SP + V(0, 0, 0.45 * (1 - ease_in(min(1, max(0, (f - hit_st + 8) / 8)))))), f0_8, S[8][0])
    T.set(st, "rotation_euler", lambda f: (math.pi / 2, 0, 0), f0_8, f0_8 + 1)
    T.set(st, "scale", lambda f: (1.4 * pop(f, hit_st - 10, 5) * (unpop(f, hit_st + 8, 6) if f > hit_st + 8 else 1),) * 3
          if f0_8 <= f < S[8][0] else (0, 0, 0), 0, N)
    T.set(meter.abdruck, "scale", lambda f: (pop(f, hit_st, 4, 1.2),) * 3 if f >= hit_st else (0, 0, 0), 0, N)
    cue(wd(7, "29") + 4, "pop", 1.0)                       # Zeile 2
    cue(wd(7, "60") + 4, "pop", 1.0)                       # Zeile 3
    cue(f0_8 - 5, "whoosh", 0.9)
    cam.whips.append((f0_8, 1))
    cam.add_shot(f0_8, f1_8, fahrt(f0_8, f1_8, (ST.p(-1.5, -4.4, 2.3), LEFT + V(0.45, 0, 0.2), 36.0),
                                   (ST.p(1.55, -4.4, 2.2), RIGHT + V(0.0, 0, 0.15), 36.0)))

    # =================================================================== SZENE 9 – Dashboard-Reveal (push_in ueber Kalles Schulter)
    f0_9, f1_9 = S[8]
    B9 = lap_pt(0.52, -0.05, 0.42)
    for side, sx in (("R", -1), ("L", 1)):
        C.byte_arm(T, b, side, (-1.0, -sx * 0.3, 0.0), turn0 - 4, turn1 + 4, ramp=4)
        C.byte_hand(T, b, side, "grab", turn0 - 4, turn1 + 4)
    B9b = TH.p(1.4, -0.6, 1.85)                           # nach dem Drehen zur Seite (Dashboard frei)
    b9 = path([(f0_9, B9), (turn1, B9 + V(-0.2, 0.2, 0)), (turn1 + 12, B9b)], ease_in_out)
    T.set(b.root, "location", lambda f: b9(f), f0_9, S[9][0])
    # Lichtschein vom Bildschirm auf Kalles Gesicht (Workbench: Hautton heller, leicht tuerkis)
    glow_on = (turn1 - 2, S[11][0])
    for mn, tint in (("skin", (0.1, 0.16, 0.18)), ("skin_dark", (0.08, 0.12, 0.14)), ("cheek", (0.06, 0.1, 0.12))):
        m = bpy.data.materials.get(mn)
        if m is None:
            continue
        base = tuple(m.diffuse_color)
        T.set(m, "diffuse_color", lambda f, base=base, tint=tint: tuple(min(1.0, x + d * window(f, glow_on[0], glow_on[1], 6, 4))
                                                                         for x, d in zip(base[:3], tint)) + (base[3],), 0, N)
    C.reaction(T, coll, k, "neutral", hl(8), seed=9)
    cue(f0_9 - 5, "whoosh", 1.0)
    cam.whips.append((f0_9, -1))
    n_k = V((math.sin(ROT_KALLE), -math.cos(ROT_KALLE), 0))           # Display-Normale zu Kalle
    C9a = TH.p(0.15, 1.25, 2.25)                                     # ueber Kalles Schulter
    C9b = TH.p(0.2, 1.0, 2.08)
    cam.add_shot(f0_9, f1_9, lambda f: (V(C9a).lerp(V(C9b), ease_in_out((f - turn1 + 4) / max(1, f1_9 - turn1 - 4)))
                                        if f > turn1 - 4 else V(C9a), SCR_K + V(0.03, 0.06, 0.0), 40.0))

    # =================================================================== SZENE 10 – 138 Euro (zoom_gesicht, Dashboard unscharf vorn)
    f0_10, f1_10 = S[9]
    K10 = K + V(0.2, -0.12, 0)
    set_kalle(f0_10, f1_10, K10, 0.6)
    lean = {"hips": (0.3, 0, 0.1), "head": (-0.05, 0, 0.1)}
    C.pose(T, k, lean, f0_10 + 1, S[10][0] - 2, 6, 6)
    T.add(k.body, "location", lambda f: (0, 0, -0.22 * window(f, f0_10 + 1, S[10][0] + 2, 6, 6)), f0_10, S[10][0] + 4)
    T.add(k.stache, "rotation_euler", lambda f: (0.1 * math.sin(f * 2.6), 0, 0.06 * math.sin(f * 3.1)), f0_10, f1_10)
    C.reaction(T, coll, k, "staunen", hl(9) + 2, hold=f1_10 - hl(9) - 2, speaking=True, seed=10, hat=False)
    set_byte(f0_10, S[10][0], B9b)
    face10 = K10 + V(0.45, -0.38, 1.7)
    cam.add_shot(f0_10, f1_10, zoom_gesicht(f0_10, f1_10, (SCR_K + V(0.75, -1.9, 0.9), face10 + V(0, 0, -0.1), 40.0),
                                           (SCR_K + V(0.55, -1.35, 0.95), face10 + V(0, 0, -0.1), 46.0)))

    # =================================================================== SZENE 11 – Ein Klick, drei Kuendigungen (schwenk ueber die Geister)
    f0_11, f1_11 = S[10]
    klick = wd(10, "klick")
    set_kalle(f0_11, f1_11, K, 0.6)
    tap = {"sh_R": (-1.2, 0, -0.2), "el_R": (-0.45, 0, 0)}
    C.pose(T, k, tap, klick - 8, klick + 10, 5, 8)
    T.set(k.finger["R"], "scale", lambda f: (1, 1, 0.35 + 0.65 * window(f, klick - 8, klick + 12, 3, 5)), klick - 9, klick + 13)
    T.add(k.hand["R"], "location", lambda f: (0, 0, -0.03 * window(f, klick - 1, klick + 4, 1, 3)), klick - 2, klick + 5)
    cue(klick, "pop", 0.6)
    haken = [klick + 8, klick + 22, klick + 36]
    GA = [TH.p(-0.15, -1.3, 2.0), TH.p(0.55, -1.5, 2.1), TH.p(1.25, -1.3, 2.0)]
    T.set(ghost.root, "location", lambda f: tuple(GA[0]), f0_11, S[11][0])
    T.set(ghost.root, "scale", lambda f: (1.15,) * 3, f0_11, f0_11 + 1)
    DP.aufloesen(T, coll, ghost.root, haken[0], GA[0] + V(0, 0, 0.3), base=1.15, name="aufl0", seed=11)
    T.set(ghost.root, "scale", lambda f: (0, 0, 0), haken[0] + 9, S[12][0])
    box_g2 = DP.software_box(coll, "kasse_g2", geist=True)
    box_g2.root.location = GA[1]
    box_g2.root.scale = (1.5,) * 3
    T.set(box_g2.root, "scale", lambda f: (1.5,) * 3 if f0_11 <= f < haken[1] else (0, 0, 0), 0, N)
    DP.aufloesen(T, coll, box_g2.root, haken[1], GA[1] + V(0, 0, 0.35), base=1.5, name="aufl1", seed=12)
    T.set(box_g2.root, "scale", lambda f: (0, 0, 0), haken[1] + 9, N)
    T.set(box_g2.root, "scale", lambda f: (0, 0, 0), 0, f0_11)
    T.add(box_g2.root, "location", lambda f: (0, 0, 0.05 * math.sin(f * 0.15)), f0_11, f1_11)
    meter2 = DP.stromzaehler(coll, "stromzaehler2")
    meter2.root.location = GA[2]
    DP.zaehler_drehen(T, meter2, f0_11, f1_11, speed=1.1)
    T.set(meter2.root, "scale", lambda f: (1.3,) * 3 if f0_11 <= f < haken[2] else (0, 0, 0), 0, N)
    DP.aufloesen(T, coll, meter2.root, haken[2], GA[2] + V(0, 0, 0.4), base=1.3, name="aufl2", seed=13)
    T.set(meter2.root, "scale", lambda f: (0, 0, 0), haken[2] + 9, N)
    T.set(meter2.root, "scale", lambda f: (0, 0, 0), 0, f0_11)
    for q, hq in enumerate(haken):
        cue(hq, "ding", 1.0)
        u = DP.briefumschlag_kuendigung(coll, f"brief{q}")
        DP.umschlag_fliegen(T, u, SCR_K + V(0, 0, 0.05), GA[q] + V(0.2, -0.6, 0.6 + 0.15 * q), hq - 2, dur=24, seed=q)
        T.set(u.root, "scale", lambda f, hq=hq: (1.6 * pop(f, hq - 2, 5) * (unpop(f, hq + 22, 4) if f > hq + 22 else 1),) * 3
              if hq - 2 <= f < hq + 27 else (0, 0, 0), 0, N)
    set_byte(f0_11, S[11][0], TH.p(1.75, -0.2, 1.85))
    cam.add_shot(f0_11, f1_11, schwenk(f0_11, f1_11, (TH.p(0.78, 1.2, 2.4), GA[0] + V(0.1, 0, -0.25), 36.0),
                                       (TH.p(0.9, 1.15, 2.4), GA[2] + V(-0.1, 0, -0.25), 36.0)))

    # =================================================================== SZENE 12 – Muenzsaeule, 1.656 € (Kranfahrt unten -> oben)
    f0_12, f1_12 = S[11]
    col = PR.coin_column(coll, "saeule", 60, spacing=0.032)
    CB = ST.p(-1.0, -0.5, 0.0)
    col.root.location = CB
    col.root.scale = (2.6, 2.6, 1.0)
    rise0, rise1 = f0_12 + 4, wd(11, "euro") + 4
    hcol = 60 * 0.032

    def rise(f):
        return ease_out(min(1.0, max(0.0, (f - rise0) / max(1, rise1 - rise0))))
    T.set(col.root, "scale", lambda f: (2.6, 2.6, max(0.001, 1.6 * rise(f))) if f0_12 <= f < S[12][0] else (0, 0, 0), 0, N)
    T.set(b.root, "location", lambda f: tuple(CB + V(0, 0, hcol * 1.6 * rise(f) + 0.3)), f0_12, S[12][0])
    T.set(b.root, "rotation_euler", lambda f: (0.12 * math.sin(f * 0.3), 0.18 * math.sin(f * 0.21), 0.2), f0_12, S[12][0])
    T.set(b.root, "rotation_euler", lambda f: (0, 0, 0), S[12][0], S[12][0] + 1)
    for side, sx in (("R", -1), ("L", 1)):
        C.byte_arm(T, b, side, (-0.2, -sx * 1.3, 0.0), f0_12 + 2, f1_12, ramp=4)     # Arme zur Balance
    PR.burst(T, coll, "s12coins", "coinp", tuple(CB + V(0, -0.2, 0.3)), rise0 + 4, 14, 1201, speed=(1.0, 1.8), up=1.2,
             gravity=-5.0, life=(18, 26), size=(1.0, 1.4))
    cue(f0_12 - 5, "whoosh", 1.0)
    cue(rise1, "ding", 1.0)
    cam.whips.append((f0_12, 1))
    top_c = CB + V(0, 0, hcol * 1.6 + 0.3)
    cam.add_shot(f0_12, f1_12, kranfahrt(f0_12, f1_12, (ST.p(-0.2, -4.6, 0.9), CB + V(0.4, 0, 0.8), 36.0),
                                         (ST.p(-0.2, -4.8, 3.6), top_c + V(0.55, 0, 0.2), 36.0)))

    # =================================================================== SZENE 13 – Was koschtesch du? (Loop)
    f0_13, f1_13 = S[12]
    set_kalle(f0_13, N, K, 0.0)
    B13 = face + V(0.6, -0.45, -0.12)
    lean13 = {"hips": (0.2, 0, -0.12), "head": (0.1, 0, -0.25)}
    C.pose(T, k, lean13, f0_13 + 2, N - 14, 6, 10)
    C.pose(T, k, hold_cup, f0_13 - 2, N + 10, 1, 4, settle=False)
    C.reaction(T, coll, k, "zweifel", hl(12) - 4, hold=N - hl(12) - 10, speaking=True, seed=13)
    back = N - 18
    T.set(b.root, "location", lambda f: tuple(B13.lerp(lap_out + V(0, 0.1, 0), ease_in((f - back) / 14)) if f > back else B13),
          f0_13, N)
    T.set(b.root, "scale", lambda f: (1 - 0.28 * ease_in((f - back - 4) / 12),) * 3 if f > back + 4 else (1, 1, 1), back, N)
    T.add(b.root, "location", lambda f: (0.06 * ease_in_out((f - f0_13) / 40), 0.08 * ease_in_out((f - f0_13) / 40), 0), f0_13, back)
    # Geist flackert kurz auf und ist zum Loop wieder da
    T.set(ghost.root, "location", lambda f: tuple(G1), f0_13, N)
    fl = f0_13 + 30
    T.set(ghost.root, "scale", lambda f: ((1.15,) * 3 if (fl <= f < fl + 3 or fl + 6 <= f < fl + 8 or f >= N - 7) else (0, 0, 0)),
          f0_13, N)
    cue(f0_13 - 5, "whoosh", 0.9)
    cam.whips.append((f0_13, -1))
    cam.add_shot(f0_13, N, fahrt(f0_13, N - 7, (face + V(0.35, -3.0, 0.1), face + V(0.3, 0, -0.25), 44.0), shot1(0)))

    # ------------------------------------------------------------ Bytes Display-Augen je Reaktion
    eyes = ["schock", "neutral", "neutral", "staunen", "neutral", "staunen", "schock", "neutral", "jubel", "jubel", "jubel",
            "jubel", "schock"]
    sched = [(0, "neutral")] + [(S[i][0], e) for i, e in enumerate(eyes)]
    sched += [(brake, "neutral"), (point1, "schock"), (wd(12, "du") - 4, "schock")]
    sched = [(f, e) for f, e in sched if not (S[12][0] <= f < wd(12, "du") - 4 and e == "schock")] + [(S[12][0], "neutral")]
    C.byte_face(T, b, sched, 0, N - 1)

    def focus(f):
        i = next((j for j, s in enumerate(sc) if s["f0"] <= f < s["f1"]), len(sc) - 1)
        if i in (3, 4, 5, 7, 11):
            return V(T.loc(b.root, f))
        if i == 2:
            return V(SCR)
        if i in (8, 10):
            return V(SCR_K)
        if i == 9:
            return face10
        return V(T.loc(k.root, f)) + V(0, -0.25, 1.95)
    W.cam.focus_fn = focus
