"""Regie fuer 'Wo kommt Filiale Nr. 2 hin?' (folge-09-filiale). Szenen-Index 0..12 = Szene 1..13.

Theke (Szene 1-2, 11-13) und Set 'stadtkarte' (Szene 3-10, Engine 2.3). Running Gag: der Stadtplan rollt sich immer
wieder zusammen (Szene 1, 2, 13). Kamera nie zweimal hintereinander gleich: push_in, rueckfahrt, totale_oben mit
Drehung, drohnenflug, schwenk (tief_viertel), drohnenflug langsam, drohnenflug mit hartem Stopp, zoom_gesicht,
push_in (tief_viertel), rueckfahrt, zoom_gesicht, push_in, Rueckfahrt in die Startposition (Loop).
Requisiten: assets/props/filiale.py, Bildschirm: assets/screens/filiale.py.
"""
import math
import os
import sys


import characters as C
import look as L
import props as PR
import stadtkarte as SK
from anim import (ease_in, ease_out, ease_in_out, ease_out_back, window, pop, unpop, lerp, clamp01)
from choreo.common import Ctx, path, V
from choreo.mehlpreis import fahrt, push_in
from choreo.viral import laptop_display

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "props"))
import filiale as FP  # noqa: E402
import viral as VP  # noqa: E402

FPS = 30
zoom_gesicht = schwenk = rueckfahrt = fahrt


def ease_out_quint(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 5


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    TH, SKS = c.sets["theke"], c.sets["stadtkarte"]
    sc = c.sc
    S = [(s["f0"], s["f1"]) for s in sc]
    coll = W.coll
    cam = W.cam
    top = TH.top_z
    welt = SKS.welt

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
    C.byte_idle(T, b, 0, N - 1, seed=3, amp=0.025)
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
        if i not in (5, 8):                          # ruhige Szenen ohne Punch-ins
            for w in s["words"]:
                if w["hl"]:
                    cam.punch.append(w["f0"])
    cam.drift_env = lambda f: min(1.0, f / 10.0, max(0.0, (N - 7 - f) / 10.0)) * (0.5 if S[2][0] <= f < S[10][0] else 1.0)
    T.set(b.body, "rotation_euler", lambda f: (0, 0, 0), 0, 1)
    T.set(b.root, "rotation_euler", lambda f: (0, 0, 0), 0, 1)
    T.set(b.root, "scale", lambda f: (1, 1, 1), 0, 1)
    T.set(k.root, "scale", lambda f: (1, 1, 1), 0, 1)

    def set_kalle(f0, f1, loc, rz=0.0):
        T.set(k.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(k.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)

    def set_byte(f0, f1, loc, s=1.0):
        T.set(b.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(b.root, "scale", lambda f, s=s: (s, s, s), f0, f1)

    # ------------------------------------------------------------ Theke: Aufbau
    K = V(TH.kalle)
    face = K + V(0, -0.25, 1.95)
    for i in (0, 1, 10, 11, 12):
        set_kalle(S[i][0], S[i][1], K, 0.0)
    lap = TH.objs["laptop"]
    LAP = TH.p(0.5, -0.34, top)
    LS = 1.2
    lap.root.location = LAP
    lap.root.rotation_euler = (0, 0, math.radians(-20))
    lap.root.scale = (LS, LS, LS)
    laptop_display(lap)
    TH.objs["basket"].location.x += 0.45
    lap_rot = lap.root.rotation_euler.to_matrix()

    def lap_pt(x, y, z):
        return LAP + lap_rot @ V(x * LS, y * LS, z * LS)
    SCR = lap_pt(0, 0.2 + 0.2 * math.sin(math.radians(12)), 0.03 + 0.2 * math.cos(math.radians(12)))
    B_T = TH.p(0.92, -0.2, top + 0.62)                     # Byte schwebt rechts neben dem Laptop
    PR.ambient_motes(T, coll, "th_dust", tuple(TH.p(0, 0.2, 1.9)), (2.2, 1.2, 0.9), 34, 901, 0, N - 1, drift=0.08)
    # Brezelblech hinter Kalle (wiederverwendet) und glaenzende Brezel
    L.box("blech_tisch", (1.2, 0.6, 0.9), L.mat("wood_dark", L.WOOD_DARK, 0.65), None, TH.p(-0.85, 1.0, 0.45), coll)
    blech = VP.brezelblech(coll, "blech")
    blech.root.location = TH.p(-0.85, 1.0, 0.9)
    # Stadtplan auf der Theke (links vor Kalle)
    SP_LOC = TH.p(-0.62, -0.42, top + 0.005)
    sp = FP.stadtplan_rolle(coll, "stadtplan", laenge=0.95, breite=0.5)
    sp.root.location = SP_LOC
    sp.root.rotation_euler = (0, 0, math.radians(4))

    # Auf/Zu des Stadtplans: Szene 1 (schon in Frame 0 am Aufrollen, rollt sich wieder zusammen),
    # Szene 2 (wird angesaugt), Szene 13 (aufgeknallt, Ende = Zustand von Frame 0)
    f0_1, f1_1 = S[0]
    slam13 = N - 9                                         # Knall in Szene 13: in den letzten 9 Frames rollt er auf

    def offen(f):
        if f < S[1][0]:
            if f < 14:
                return 0.32 + 0.68 * ease_out_back(clamp01((f + 4) / 18), 1.4)
            if f < 30:
                return 1.0
            t = clamp01((f - 30) / 10)
            return max(0.0, 1.0 - ease_in(t)) + 0.06 * math.sin(clamp01((f - 40) / 10) * math.pi) * (f >= 40)
        if f < slam13:
            return 0.0
        if f < N - 4:                                       # Knall: Plan klatscht flach auf, rollt an
            return 0.32 * ease_out(clamp01((f - slam13) / 5))
        return 0.32 + 0.68 * ease_out_back(clamp01((f - N + 4) / 18), 1.4)   # = Zustand vor Frame 0 (Loop)
    FP.rollen(T, sp, offen, 0, N - 1)
    # Szene 2: Byte schnippt, der Plan wird in den Laptop gesaugt (Lichtwirbel steigt auf)
    f0_2, f1_2 = S[1]
    snap = wd(1, "Idee") + 2
    suck0, suck1 = snap + 3, snap + 15
    sp_path = path([(suck0, SP_LOC), (suck0 + 6, (SP_LOC + SCR) / 2 + V(0, -0.15, 0.25)), (suck1, SCR)], ease_in)

    def sp_loc(f):
        if f < suck0:
            return tuple(SP_LOC)
        if f < suck1:
            return sp_path(f)
        if f >= slam13 - 14:                                # Szene 13: liegt wieder auf der Theke
            return tuple(SP_LOC)
        return tuple(SCR)

    def sp_scale(f):
        if suck0 <= f < suck1:
            return (1 - 0.9 * ease_in((f - suck0) / (suck1 - suck0)),) * 3
        if suck1 <= f < slam13 - 14:
            return (0, 0, 0)
        if slam13 - 14 <= f < slam13 - 6:
            return (pop(f, slam13 - 14, 8),) * 3
        return (1, 1, 1)
    T.set(sp.root, "location", sp_loc, 0, N - 1)
    T.set(sp.root, "scale", sp_scale, 0, N - 1)
    T.set(sp.root, "rotation_euler", lambda f: (0, 0, math.radians(4) + (3.0 * ease_in((f - suck0) / 12) if suck0 <= f < suck1 else 0)),
          0, N - 1)
    portal = FP.lichtwirbel_portal(coll, "portal")
    portal.root.location = SCR + V(0, -0.05, 0.05)
    FP.wirbel(T, portal, suck1 - 2, f1_2 + 4, hoehe=1.8)
    cue(suck0 - 2, "whoosh", 1.0)

    # =================================================================== SZENE 1 (push_in, schnell)
    set_byte(0, S[2][0], B_T)
    C.pose(T, k, {"sh_L": (-1.05, -0.1, -0.2), "el_L": (-0.35, 0, 0), "hips": (-0.12, 0, 0)}, -6, 10, 1, 10, settle=False)
    T.add(k.body, "location", lambda f: (0, 0, -0.03 * (1 - ease_out(clamp01((f + 3) / 10)))), 0, 12)
    C.reaction(T, coll, k, "jubel", hl(0), hold=f1_1 - hl(0) - 4, speaking=True, seed=1)
    S1A = (TH.p(0.2, -3.7, 2.0), TH.p(-0.05, -0.1, 1.55), 38.0)
    S1W = (TH.p(0.55, -4.9, 2.15), TH.p(-0.05, -0.1, 1.55), 38.0)
    s1 = push_in(f0_1, f1_1, S1A, k=0.2)

    def shot1(f):
        t = ease_out(min(1.0, (f + 6) / 24))
        p0, t0_, l0 = S1W
        p1, t1_, l1 = s1(f)
        return (V(p0).lerp(V(p1), t), V(t0_).lerp(V(t1_), t), lerp(l0, l1, t))
    cam.add_shot(f0_1, f1_1, shot1)
    PR.burst(T, coll, "s1flour", "puff", tuple(SP_LOC + V(0.45, 0, 0.05)), 0, 12, 1101, speed=(0.5, 1.1), up=0.5,
             gravity=-0.4, life=(18, 28), size=(0.8, 1.4), drag=3.0, ring=True)

    # =================================================================== SZENE 2 (rueckfahrt nach oben, Lichtwirbel)
    C.byte_snap(T, b, "R", snap)
    C.byte_arm(T, b, "L", (-0.6, -0.9, 0.0), snap + 4, f1_2, ramp=5)
    cue(snap, "pop", 0.5)
    C.kalle_react(T, k, "staunen", suck1, hold=f1_2 - suck1)
    C.kalle_look(T, k, lambda f: V(sp_loc(f)), suck0 - 2, f1_2, ramp=4)
    A2 = (TH.p(0.35, -3.2, 1.9), TH.p(0.25, -0.2, 1.55), 36.0)
    B2 = (TH.p(0.5, -2.2, 4.6), SCR + V(0, 0.1, 1.6), 30.0)
    cam.add_shot(f0_2, f1_2, rueckfahrt(f0_2 + 6, f1_2, A2, B2))
    cam.whips.append((S[2][0], 1))

    # =================================================================== STADTKARTE: Datenebenen
    f0_3 = S[2][0]
    f1_10 = S[9][1]
    SK.leben(T, SKS, f0_3 - 2, f1_10 + 2)
    rot_end = 0.0
    SK.drehen(T, SKS, f0_3 - 2, S[2][1] + 1, lambda f: lerp(-0.55, rot_end, ease_out(clamp01((f - f0_3) / max(1, S[2][1] - f0_3)))))
    PR.ambient_motes(T, coll, "sk_dust", tuple(SKS.mitte + V(0, 0, 1.0)), (3.0, 3.0, 1.2), 30, 902, f0_3, f1_10,
                     color_kind="sparkt", drift=0.05, scale=0.6)
    # Uhr: 7:14 -> 7:15 (Minutensprung in Szene 7)
    f0_7, f1_7 = S[6]
    SK.bahnhofsuhr(T, SKS, lambda f: 434 + (1 if f >= f0_7 + 8 else 0), f0_3, f1_10)
    # Pins
    AX, AY = SKS.viertel["altstadt"]
    NX, NY = SKS.viertel["neubaugebiet"]
    LX, LY = SKS.laden
    P1 = (AX, AY)
    P2 = (NX, NY)
    P3 = (LX - 0.32, LY - 0.08)
    pins = [SK.pin(coll, "pin1", 1, "ALTSTADT", "#FFFFFF"), SK.pin(coll, "pin2", 2, "NEUBAUGEBIET", "#FFFFFF"),
            SK.pin(coll, "pin3", 3, "BAHNHOF", "#FFFFFF")]
    PS = 1.25
    def pin_k(f):                                     # Pins: gross in Totale/Drohne, klein im Neubaugebiet
        if f < S[3][1] - 6:
            return 2.1
        if f < S[4][1]:
            return lerp(2.1, 1.0, ease_in_out(clamp01((f - S[3][1] + 6) / 10)))
        if f < S[5][1]:
            return lerp(1.0, 0.7, ease_in_out(clamp01((f - S[5][0]) / 8)))
        return lerp(0.7, 1.0, ease_in_out(clamp01((f - S[6][0]) / 8)))
    pin_in = [wd(2, "Altstadt"), wd(2, "Neubaugebiet"), wd(2, "Bahnhof")]
    for p, (x, y), fi in zip(pins, (P1, P2, P3), pin_in):
        SK.pin_steigen(T, W, SKS, p, x, y, fi - 2, S[9][1] + 2, PS)
        cue(fi, "pop", 0.8)
        T.mul(p.root, "scale", lambda f: (pin_k(f),) * 3, f0_3, f1_10 + 2)
    f0_5 = S[4][0]
    SK.pin_farbe(T, pins[0], lambda f: "#FFE14D" if f >= wd(4, "Schön") else "#FFFFFF", f0_3, f1_10 + 1)
    SK.pin_farbe(T, pins[1], lambda f: "#9A9CAB" if f >= wd(5, "ruhig") else "#FFFFFF", f0_3, f1_10 + 1)
    f0_10 = S[9][0]
    SK.pin_farbe(T, pins[2], lambda f: "#3DDC84" if f >= wd(9, "Kunden") else "#FFFFFF", f0_3, f1_10 + 1)

    # =================================================================== SZENE 3 (totale_oben, Platte dreht sich)
    f1_3 = S[2][1]
    TOT = SK.totale_oben(SKS, 0.93)
    cam.add_shot(f0_3, f1_3, lambda f: (V(TOT[0]) + V(0, 0.5 * (1 - ease_out(clamp01((f - f0_3) / 40))), 0.35 * (1 - ease_out(clamp01((f - f0_3) / 40)))),
                                        V(TOT[1]), TOT[2]))
    set_kalle(f0_3, S[3][0], SKS.p(-3.6, 1.0, 0), 0.0)            # Kalle steht ausserhalb des Bildes
    B_ST = welt(1.2, -2.35, 0.9)
    set_byte(f0_3, S[3][0], B_ST, 0.85)
    C.byte_arm(T, b, "L", (-1.4, -0.3, 0.0), wd(2, "Altstadt") - 3, f1_3 - 4, ramp=5)

    # =================================================================== SZENE 4 (drohnenflug zur Altstadt, Kalle vorn)
    f0_4, f1_4 = S[3]
    K4 = welt(-0.35, -3.05, 0.0)
    K4 = V((K4.x, K4.y, 0.0))
    set_kalle(f0_4, f1_4, K4, 0.45)
    C.pose(T, k, "point_wind", f0_4 + 2, f1_4 - 4, 6, 8)
    C.kalle_look(T, k, lambda f: welt(P1[0], P1[1], 0.9), f0_4, f1_4, ramp=6)
    C.reaction(T, coll, k, "jubel", hl(3), hold=f1_4 - hl(3) - 4, speaking=True, seed=4)
    T.add(k.head, "rotation_euler", lambda f: (0.12 * window(f, f0_4 + 10, f1_4, 10, 8), 0, 0.25 * window(f, f0_4, f1_4, 8, 8)),
          f0_4, f1_4)                                          # vertraeumt: Kopf leicht gehoben, zur Altstadt
    set_byte(f0_4, f1_4, welt(1.4, -1.6, 1.2), 0.75)
    d4 = SK.drohnenflug([(f0_4, V(TOT[0])), (f0_4 + 14, welt(1.6, -4.6, 2.6)), (f1_4, welt(1.25, -6.3, 1.9))],
                        [(f0_4, V(TOT[1])), (f0_4 + 14, welt(0.2, -0.9, 0.8)), (f1_4, welt(-0.75, -1.3, 0.8))],
                        lens=lambda f: lerp(28.0, 30.0, ease_in_out(clamp01((f - f0_4) / (f1_4 - f0_4)))), bank=1.4)
    cam.add_shot(f0_4, f1_4, d4)

    # =================================================================== SZENE 5 (tief_viertel Altstadt, schwenk)
    f1_5 = S[4][1]
    set_kalle(f0_5, S[7][0], SKS.p(-3.6, 1.0, 0), 0.0)
    mk = []
    mk_in = [wd(4, "schon") - 2, wd(4, "zwei") + 2]
    for j, (x, y) in enumerate(SKS.baeckereien):
        m_ = SK.konkurrenz(coll, f"mk{j}")
        SK.marker_setzen(T, W, SKS, m_, x, y + 0.02, mk_in[j], S[9][1], s=1.0)
        cue(mk_in[j], "pop", 0.8)
        mk.append(m_)
    karte1 = SK.info_karte(coll, "karte1", ["Schön", "teuer", "2 Bäckereien"])
    SK.karte_zeigen(T, W, SKS, karte1, P1[0] + 0.85, P1[1] + 0.15, 1.3, wd(4, "Bäckereien") - 4, f1_5 - 9, s=0.8)
    set_byte(f0_5, f1_5, welt(-0.55, -0.95, 0.75), 0.6)
    C.byte_arm(T, b, "R", (-1.3, 0.3, 0.2), mk_in[0], f1_5 - 4, ramp=5)
    A5 = (welt(-2.1, -0.95, 0.6), welt(-2.0, 0.35, 0.5), 19.0)
    B5 = (welt(-1.05, -0.95, 0.62), welt(-1.1, 0.35, 0.55), 19.0)
    cam.add_shot(f0_5, f1_5, schwenk(f0_5, f1_5, A5, B5))

    # =================================================================== SZENE 6 (drohnenflug langsam ins Neubaugebiet)
    f0_6, f1_6 = S[5]
    nb_str = [[(0.55, 1.2), (2.0, 1.2)], [(1.3, 2.0), (1.3, 0.85)]]
    SK.personen(T, SKS, coll, "nb_leute", nb_str, 2, f0_6 - 2, f1_6 + 2, farbe="#FFF3B0", r=0.05, tempo=0.6, seed=6,
                hoehe=0.1)
    SK.heatmap(T, SKS, coll, "hm_nb", NX, NY, 1.05, f0_6, f1_6 + 4, lambda f: "blau",
               lambda f: ease_out(clamp01((f - f0_6 - 6) / 20)))
    karte2 = SK.info_karte(coll, "karte2", ["Wenig", "Laufkundschaft"], akzent="#3B7BFF")
    SK.karte_zeigen(T, W, SKS, karte2, P2[0] - 0.3, P2[1] + 0.25, 1.0, wd(5, "ruhig", 2) - 6, f1_6 - 2, s=0.75)
    set_byte(f0_6, f1_6, welt(-0.25, 0.75, 0.65), 0.5)
    for q in range(0, max(1, (f1_6 - f0_6) // 20)):
        cue(f0_6 + 6 + q * 20, "grillen", 0.35)
    d6 = SK.drohnenflug([(f0_6, welt(-1.7, -0.9, 1.9)), (f0_6 + (f1_6 - f0_6) // 2, welt(-0.6, 0.0, 1.7)),
                         (f1_6, welt(0.05, 0.25, 1.35))],
                        [(f0_6, welt(-0.5, 0.8, 0.3)), (f0_6 + (f1_6 - f0_6) // 2, welt(0.8, 1.1, 0.35)),
                         (f1_6, welt(1.3, 1.35, 0.45))], lens=24.0, bank=1.6)
    cam.add_shot(f0_6, f1_6, d6)

    # =================================================================== SZENE 7 (Zug, Hunderte Punkte, harter Stopp)
    halt = wd(6, "laufen") - 2
    SK.zug_fahrt(T, SKS, f0_7 - 10, halt)
    flut0 = halt + 2
    bh_wege = [[(0.62, -1.42), (0.6, -0.8), (0.35, -0.25), (-0.3, -0.25), (-1.4, -0.25), (-2.4, -0.25)],
               [(0.95, -1.42), (1.0, -0.7), (1.5, -0.25), (2.45, -0.25)],
               [(0.8, -1.42), (0.42, -0.7), (0.35, 0.4), (0.35, 1.6)],
               [(1.2, -1.42), (1.7, -0.62), (2.2, -0.5)],
               [(0.7, -1.42), (0.2, -0.95), (-0.2, -0.35), (-0.95, -0.25)]]
    menge = lambda f: ease_out(clamp01((f - flut0) / 26))   # noqa: E731
    SK.personen(T, SKS, coll, "bh_leute", bh_wege, 230, f0_7, S[9][1] + 2, menge, farbe="#FFF3B0", r=0.026,
                        tempo=1.0, seed=7, hoehe=0.08)
    SK.heatmap(T, SKS, coll, "hm_bh", 0.95, -0.75, 1.2, f0_7, S[9][1] + 2, lambda f: "rot",
               lambda f: ease_out(clamp01((f - flut0 - 4) / 24)))
    zaehler = FP.zaehler_schwebend(coll, "zaehler", breite=1.25)
    Z_POS = welt(P3[0], P3[1] - 0.05, 1.2)
    T.set(pins[2].schild, "scale", lambda f: (0, 0, 0) if flut0 - 2 <= f < S[7][0] else (1, 1, 1), f0_7 - 1, S[7][0] + 1)
    T.set(zaehler.root, "location", lambda f: tuple(Z_POS + V(0, 0, 0.02 * math.sin(f * 0.1))), f0_7, S[8][0])
    T.set(zaehler.root, "scale", lambda f: (0.8 * pop(f, flut0, 8) * (unpop(f, S[7][0] - 6, 6) if f > S[7][0] - 6 else 1),) * 3,
          f0_7 - 1, S[7][0] + 2)
    SK.billboard(T, W, zaehler.root, lambda f: Z_POS, f0_7, S[7][0] + 2, tilt=0.8)
    W.anchors["zaehler"] = zaehler.anker
    z_end = wd(6, "Leute") + 2
    W.labels.append({"anchor": "zaehler", "f0": flut0 + 4, "f1": S[7][0] - 6, "count_f0": flut0 + 4, "count_f1": z_end,
                     "from": 0, "to": 8000, "fmt": "{}", "dec": 0, "dy": -8})
    cue(f0_7 - 4, "zug", 0.9)
    cue(halt - 30 if halt - 30 > f0_7 else f0_7 + 2, "zug", 0.7)
    set_byte(f0_7, f1_7, welt(-0.15, -1.7, 0.9), 0.6)
    stop7 = min(wd(6, "8.000") - 2, f1_7 - 10)
    d7 = SK.drohnenflug([(f0_7, welt(1.9, 0.2, 1.7)), (f0_7 + (stop7 - f0_7) // 2, welt(2.3, -1.4, 2.0)),
                         (stop7, welt(1.25, -2.65, 1.6))],
                        [(f0_7, welt(1.2, 0.9, 0.3)), (f0_7 + (stop7 - f0_7) // 2, welt(1.4, -0.4, 0.25)),
                         (stop7, welt(1.0, -0.65, 0.42))], lens=24.0, bank=1.4, ease=ease_out_quint)

    def shot7(f):
        if f < stop7:
            return d7(f)
        p, t_, ln, rl = d7(stop7)
        k_ = window(f, stop7, stop7 + 8, 0, 6)       # kurzer Nachfeder-Ruck beim harten Stopp
        return (p + V(0, 0.03 * k_ * math.sin((f - stop7) * 1.6), -0.02 * k_), t_, ln, 0.0)
    cam.add_shot(f0_7, f1_7, shot7)
    cam.shakes.append((stop7, 0.02, 6))

    # =================================================================== SZENE 8 (zoom_gesicht Kalle, Bahnhof dahinter)
    f0_8, f1_8 = S[7]
    K8 = welt(0.95, -2.95, 0.0)
    K8 = V((K8.x, K8.y, 0.0))
    set_kalle(f0_8, f1_8, K8, 0.15)
    C.pose(T, k, "scratch", f0_8 + 4, f1_8 - 2, 6, 8)
    T.add(k.hat, "rotation_euler", lambda f: (0, 0.12 * window(f, f0_8 + 8, f1_8 - 2, 6, 6) * math.sin(f * 0.9), 0), f0_8,
          f1_8)
    T.add(k.hips, "rotation_euler", lambda f: (0.1 * window(f, f0_8, f1_8, 8, 8), 0, 0), f0_8, f1_8)
    T.add(k.head, "rotation_euler", lambda f: (-0.1 * window(f, f0_8, f1_8, 8, 8), 0, 0.35 * window(f, f0_8, f1_8, 10, 8)), f0_8, f1_8)
    C.kalle_look(T, k, lambda f: welt(1.05, -0.9, 0.2), f0_8, f1_8, ramp=6)
    C.kalle_react(T, k, "zweifel", hl(7), hold=f1_8 - hl(7) - 2, speaking=True)
    set_byte(f0_8, f1_8, welt(2.4, -2.6, 1.6), 0.6)
    F8 = K8 + V(0, -0.25, 1.95)
    A8 = (K8 + V(-0.75, -3.4, 1.7), K8 + V(0.05, 0.5, 1.2), 30.0)
    B8 = (K8 + V(-0.45, -2.4, 1.75), F8 + V(0.05, 0.3, -0.55), 34.0)
    cam.add_shot(f0_8, f1_8, zoom_gesicht(f0_8, f1_8, A8, B8))

    # =================================================================== SZENE 9 (tief_viertel Bahnhof, push_in)
    f0_9, f1_9 = S[8]
    set_kalle(f0_9, S[10][0], SKS.p(-3.6, 1.0, 0), 0.0)
    gold_in = wd(8, "drei") + 2
    gold_wege = [[(0.62, -1.42), (0.6, -0.8), (0.4, -0.45), (0.2, -0.3)], [(0.95, -1.42), (1.0, -0.7), (1.15, -0.4)],
                 [(0.8, -1.42), (0.5, -0.75), (0.62, -0.5)]]
    gold = SK.personen(T, SKS, coll, "gold_leute", gold_wege, 7, f0_9, S[9][0] + 8,
                       lambda f: 1.0 if f >= gold_in else 0.0, farbe="#F2B45A", r=0.034, tempo=0.6, seed=9)
    raster = FP.punktraster_100(coll, "raster")
    R_POS = welt(0.5, -0.9, 1.3)
    T.set(raster.root, "location", lambda f: tuple(R_POS + V(0, 0, 0.02 * math.sin(f * 0.1))), f0_9, f0_10 + 14)
    T.set(raster.root, "scale", lambda f: (0.5 * pop(f, f0_9 + 6, 9) * (unpop(f, f0_10 + 4, 7) if f > f0_10 + 4 else 1),) * 3,
          f0_9 - 1, f0_10 + 14)
    SK.billboard(T, W, raster.root, lambda f: R_POS, f0_9, f0_10 + 14, tilt=0.8)
    for j, g in enumerate(raster.gold):
        T.set(g, "scale", lambda f, j=j: ((1.0 + 0.5 * window(f, gold_in + 3 * j, gold_in + 3 * j + 10, 2, 6)),) * 3,
              f0_9, f1_9)
    cue(gold_in, "pop", 0.6)
    tafel = FP.screen_tafel(coll, "tafel", breite=1.5)
    TF_POS = welt(1.3, -0.3, 1.35)
    T.set(tafel.root, "location", lambda f: tuple(TF_POS + V(0, 0, 0.02 * math.sin(f * 0.08))), f0_9, f1_10 + 2)
    T.set(tafel.root, "scale", lambda f: (pop(f, f0_9 + 10, 9) * lerp(0.7, 1.0, ease_in_out(clamp01((f - f0_10) / 20))),) * 3,
          f0_9 + 9, f0_10 + 22)
    SK.billboard(T, W, tafel.root, lambda f: TF_POS, f0_9, f1_10 + 2, tilt=0.6)
    set_byte(f0_9, f1_9, welt(1.65, -1.75, 0.95), 0.6)
    A9 = (welt(1.15, -3.15, 1.15), welt(0.75, -0.2, 0.75), 24.0)
    cam.add_shot(f0_9, f1_9, push_in(f0_9, f1_9, A9, k=0.16))

    # =================================================================== SZENE 10 (Kundenschlange, Schild, rueckfahrt)
    f1_10 = S[9][1]
    queue = [(0.75, -0.95), (0.55, -0.6), (0.85, -0.42), (LX - 0.05, LY - 0.25), (LX + 0.07, LY - 0.13)]
    gold_pos = [g.pos for g in gold]
    FP.kundenschlange_gold(T, SKS, coll, "schlange", lambda q, f: gold_pos[q % len(gold_pos)](f), queue, 14, f0_10 + 2,
                           f1_10 + 2)
    for g in gold:
        T.set(g.obj, "scale", lambda f: (1.0,) * 3 if gold_in <= f < f0_10 + 3 else (0.0,) * 3, f0_9, f1_10 + 2)
    schild = FP.schild_filiale(coll, "schild")
    sch_f = wd(9, "Kunden") - 2
    schild.root.location = welt(LX, LY - 0.13, 0.29)
    FP.aufklappen(T, schild, sch_f, s=0.85)
    cue(sch_f + 3, "ding", 1.0)
    set_byte(f0_10, f1_10, welt(-0.35, -1.75, 0.95), 0.6)
    A10 = (welt(1.0, -2.85, 1.3), welt(0.8, -0.3, 0.55), 26.0)
    B10 = (V(TOT[0]), V(TOT[1]) + V(0, 0.3, 0.25), TOT[2])
    cam.add_shot(f0_10, f1_10, rueckfahrt(f0_10 + 6, f1_10 - 2, A10, B10))
    # Stadtrauschen ueber alle Stadtkarten-Szenen (am Bahnhof lauter)
    f = f0_3
    while f < f1_10 - 10:
        bh = S[6][0] - 10 <= f < f1_10
        cue(f, "stadtrauschen", 0.55 if bh else 0.3)
        f += 75
    cam.whips.append((S[10][0], -1))

    # =================================================================== SZENE 11 (Theke, zoom_gesicht, Arme verschraenkt)
    f0_11, f1_11 = S[10]
    cue(f0_11 - 3, "whoosh", 1.0)
    set_byte(f0_11, S[12][1] + 1, B_T, 1.0)
    C.pose(T, k, {"sh_R": (-0.5, 0.5, 0.0), "sh_L": (-0.5, -0.5, 0.0), "el_R": (-1.8, 0, 0.6),
                  "el_L": (-1.8, 0, -0.6), "head": (0.04, 0, 0)}, f0_11 + 1, f1_11 - 2, 6, 8)
    C.kalle_react(T, k, "zweifel", hl(10), hold=f1_11 - hl(10) - 2, speaking=True)
    A11 = (TH.p(-0.5, -3.4, 1.95), K + V(0, 0, 1.45), 32.0)
    B11 = (TH.p(-0.3, -2.4, 1.95), face + V(0.02, 0, -0.42), 38.0)
    cam.add_shot(f0_11, f1_11, zoom_gesicht(f0_11, f1_11, A11, B11))

    # =================================================================== SZENE 12 (Kiosk-Hologramm, push_in)
    f0_12, f1_12 = S[11]
    holo = FP.kiosk_hologramm(coll, "holo")
    holo.root.location = TH.p(0.98, -0.42, top + 0.02)
    holo.root.rotation_euler = (0, 0, math.radians(-12))
    h_in = wd(11, "Kiosk") - 4
    FP.holo_an(T, holo, h_in, f1_12 - 4, s=1.0)
    cue(h_in, "ding", 0.8)
    br = FP.broetchen_plastik(coll, "broetchen")
    br_in = wd(11, "aufgebackenen") - 6
    br_path = path([(br_in - 8, TH.p(0.98, -0.56, top + 0.18)), (br_in + 6, B_T + V(0.3, -0.2, -0.22))], ease_in_out)
    T.set(br.root, "location", lambda f: br_path(f), br_in - 8, f1_12)
    T.set(br.root, "scale", lambda f: ((pop(f, br_in - 8, 6) * (unpop(f, f1_12 - 4, 4) if f > f1_12 - 4 else 1)) * 1.5,) * 3,
          br_in - 9, f1_12 + 1)
    T.set(br.root, "rotation_euler", lambda f: (0.25 * math.sin(f * 0.2), 0, 0.15 * math.sin(f * 0.13)), br_in - 8, f1_12)
    T.set(br.root, "scale", lambda f: (0, 0, 0), 0, 1)
    C.byte_arm(T, b, "L", (-1.1, -0.5, -0.35), br_in, f1_12 - 2, ramp=5)
    C.byte_hand(T, b, "L", "grab", br_in + 4, f1_12 - 2, ramp=3)
    T.add(b.body, "rotation_euler", lambda f: (0, 0.2 * window(f, br_in + 4, f1_12, 4, 6), -0.15 * window(f, br_in + 4, f1_12, 4, 6)),
          br_in, f1_12)
    C.kalle_react(T, k, "staunen", wd(11, "aufgebackenen"), hold=16)
    A12 = (TH.p(0.95, -3.3, 1.8), TH.p(0.9, -0.3, 1.35), 34.0)
    cam.add_shot(f0_12, f1_12, push_in(f0_12, f1_12, A12, k=0.24))

    # =================================================================== SZENE 13 (Brezel wie Trophaee, Knall, Loop)
    f0_13, f1_13 = S[12]
    bz = FP.brezel_glaenzend(coll, "brezel_gl", s=1.5)
    grab = f0_13 + 4
    bz.root.parent = k.hand["R"]
    bz.root.location = (0.0, -0.06, -0.12)
    T.set(bz.root, "scale", lambda f: (1, 1, 1) if grab <= f < slam13 - 10 else (0, 0, 0), 0, N)
    FP.glitzern(T, bz, grab, slam13)
    C.pose(T, k, {"sh_R": (-2.8, -0.35, 0.0), "el_R": (-0.3, 0, 0), "head": (-0.1, 0, 0)}, grab, slam13 - 12, 5, 6)
    C.reaction(T, coll, k, "jubel", hl(12), hold=max(8, slam13 - 12 - hl(12)), speaking=True, seed=13)
    PR.burst(T, coll, "s13glitz", "sparkt", tuple(K + V(0.35, -0.3, 2.6)), grab + 8, 14, 1301, speed=(0.4, 0.9),
             up=0.5, gravity=-0.3, life=(18, 26), size=(0.6, 1.0), drag=2.0)
    # Knall: linke Hand schlaegt den Plan auf die Theke (gleiche Pose wie Frame 0)
    C.pose(T, k, {"sh_L": (-1.05, -0.1, -0.2), "el_L": (-0.35, 0, 0), "hips": (-0.12, 0, 0)}, slam13 - 6, N + 12, 4, 1,
           settle=False)
    T.add(k.body, "location", lambda f: (0, 0, -0.03 * window(f, slam13 - 2, N + 10, 2, 1)), slam13 - 3, N)
    cue(slam13 - 1, "pop", 0.6)
    cam.add_shot(f0_13, N, fahrt(f0_13, N - 3, (TH.p(-0.45, -3.0, 2.05), K + V(-0.1, 0, 1.75), 36.0), shot1(0)))

    # ------------------------------------------------------------ Bytes Display-Augen je Reaktion
    eyes = ["jubel", "jubel", "neutral", "jubel", "zweifel", "neutral", "staunen", "zweifel", "neutral", "jubel",
            "zweifel", "jubel", "jubel"]
    sched = [(0, "jubel")] + [(S[i][0], e) for i, e in enumerate(eyes)] + [(br_in + 4, "zweifel"),
                                                                           (wd(11, "Brötchen") + 4, "jubel")]
    C.byte_face(T, b, sched, 0, N - 1)

    def focus(f):
        i = next((j for j, s in enumerate(sc) if s["f0"] <= f < s["f1"]), len(sc) - 1)
        if i in (0, 10, 12):
            return face
        if i == 1:
            return V(SCR) if f < suck1 + 6 else V(SCR) + V(0, 0, 0.8)
        if i == 11:
            return V(B_T)
        if i == 7:
            return F8
        if i == 2:
            return SKS.mitte
        if i == 3:
            return K4 + V(0, -0.25, 1.9)
        return V(cam.state(f)[3])
    W.cam.focus_fn = focus
