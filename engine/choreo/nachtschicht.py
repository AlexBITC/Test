"""Regie fuer 'Bytes Nachtschicht' (folge-08-nachtschicht). Szenen-Index 0..12 = Szene 1..13.

Gefuehl: Szene 1-6 schnell und hell, Szene 7 kippt (keine Partikel, langsam), Szene 8-9 ruhig (nur Raumatmosphaere),
ab Szene 10 wird es wieder warm. Kalles Muetze: schief (Szene 2-7), abgenommen (8-11), gerade aufgesetzt (12).
Running Gags: Ermittlungs-Pinnwand (Szene 1, 4), goldene Bewerbungsmappen (3, 11), Uhr 4:12 (1, 13).
Kamera-Presets nie zweimal hintereinander (Szene 7 als langsamer Zoom aufs Gesicht, weil Szene 8 push_in ist).
Requisiten: assets/props/nachtschicht.py, Bildschirm: assets/screens/nachtschicht.py.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

import build_world as BW
import characters as C
import look as L
import props as PR
from anim import (ease_in, ease_out, ease_in_out, ease_out_back, spring, window, pop, unpop, lerp)
from choreo.common import Ctx, path, V
from choreo.mehlpreis import harter_zoom, fahrt, push_in, vis
from choreo.black_friday import kreisfahrt
from choreo.viral import laptop_display

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "props"))
import nachtschicht as NP  # noqa: E402

FPS = 30
zoom_gesicht = schwenk = rueckfahrt = zoom = fahrt


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    TH, ST, BS = c.sets["theke"], c.sets["studio"], c.sets["backstube"]
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
    W.licht_extra = []

    # ------------------------------------------------------------ Grundbewegung
    C.kalle_idle(T, k, 0, N - 1, seed=7)
    C.byte_idle(T, b, 0, N - 1, seed=3, amp=0.02)
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
        if i not in (6, 7, 8):                      # ruhige Szenen ohne Punch-ins
            for w in s["words"]:
                if w["hl"]:
                    cam.punch.append(w["f0"])
    cam.drift_env = lambda f: min(1.0, f / 10.0, max(0.0, (N - 7 - f) / 10.0)) * (0.4 if S[6][0] <= f < S[9][0] else 1.0)
    T.set(b.body, "rotation_euler", lambda f: (0, 0, 0), 0, 1)
    T.set(b.root, "rotation_euler", lambda f: (0, 0, 0), 0, 1)
    k.cloth.scale = (0, 0, 0)

    def set_kalle(f0, f1, loc, rz=0.0):
        T.set(k.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(k.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)

    def set_byte(f0, f1, loc):
        T.set(b.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)

    # ------------------------------------------------------------ Backstube: Requisiten
    TZ = BS.table_z
    B_T = BS.p(0.15, 0.45, TZ + 0.24)                # Byte sitzt auf dem Arbeitstisch
    DOOR = BS.p(0.9, 3.45, 0)
    K_SACK = BS.p(-1.75, 0.85, 0)
    stapel_m = NP.mappen_stapel(coll, "stapel_mappen", n=16)
    stapel_m.root.location = BS.p(-0.55, 0.55, TZ)
    stapel_a = NP.auftrags_stapel(coll, "stapel_auftraege", n=26)
    stapel_a.root.location = BS.p(0.78, 0.55, TZ)
    pinn = NP.ermittlungs_pinnwand(coll, "pinnwand")
    PIN_T = BS.p(0.15, 0.98, TZ + 0.33)
    NP.faeden_schwingen(T, pinn, 0, N - 1)
    uhr = NP.wanduhr_backstube(coll, "uhr_bs")
    uhr.root.location = BS.p(2.3, 3.1, 2.75)
    haken = NP.schuerzenhaken(coll, "haken")
    haken.root.location = BS.p(1.95, 3.12, 1.85)
    thermos = NP.thermoskanne(coll, "thermos")
    thermos.root.parent = k.hand["L"]
    thermos.root.location = (0.02, -0.05, -0.12)
    thermos.root.rotation_euler = (math.pi / 2, 0, 0)
    keys = NP.schluesselbund(coll, "keys")
    keys.root.parent = k.hand["R"]
    keys.root.location = (0, -0.06, -0.08)
    sack = PR.flour_sack(coll, "sitzsack", label=True, scale=1.25, text1="WEIZEN", text2="550")
    sack.root.location = K_SACK + V(0, 0.02, 0)
    sack.root.rotation_euler = (0, 0, 0.15)
    door = BS.objs["door"]

    # Uhr: 4:12 in Szene 1, Zeitraffer in Szene 13, wieder 4:12 am Ende
    tl0 = S[12][0] + 6

    def zeit(f):
        if f < tl0:
            return 4 * 60 + 12 + f / 30.0 * 0.5 if f < S[1][1] else 7 * 60 + 40
        if f >= N - 10:
            return 4 * 60 + 12
        t = (f - tl0) / max(1, N - 10 - tl0)
        return 7 * 60 + 40 + t * (20 * 60 + 32)
    NP.uhr_stellen(T, uhr, zeit, 0, N - 1)
    T.set(uhr.t412, "scale", lambda f: (1, 1, 1) if (f < S[1][1] or f >= N - 10) else (0, 0, 0), 0, N)

    # Glut: Nacht hell, frueh fast aus, ab Szene 12 flammt sie auf
    flare = wd(11, "jetzt") - 2

    def glut_lv(f):
        if f < S[1][0]:
            return 1.0
        if f < S[7][0]:
            return 0.55
        if f < flare:
            return 0.14 + 0.04 * math.sin(f * 0.21)
        if f < S[12][0]:
            return min(1.25, 0.14 + 1.1 * ease_out((f - flare) / 10))
        return 0.9 if f < N - 20 else 1.0
    BW.glut(T, BS, 0, N - 1, glut_lv, seed=8)
    PR.ambient_motes(T, coll, "bs_dust", tuple(BS.p(0.2, 0.8, 1.8)), (2.0, 1.4, 1.0), 26, 801, 0, N - 1, drift=0.06, scale=0.8)
    PR.ambient_motes(T, coll, "st_dust", tuple(ST.p(0, 0.6, 2.4)), (2.4, 1.6, 1.2), 30, 802, 0, N - 1,
                     color_kind="sparkt", drift=0.06, scale=0.6)
    # Funken aus der Glut (Szene 1 und 12)
    mouth = BS.objs["oven_mouth"]
    for q, f_ in enumerate(range(4, S[1][0], 22)):
        PR.burst(T, coll, f"s1spark{q}", "spark", tuple(mouth + V(0, -0.15, -0.1)), f_, 4, 810 + q, speed=(0.3, 0.6),
                 up=0.9, gravity=-0.3, life=(14, 22), size=(0.5, 0.8), drag=1.0)

    # Tuer: geht in Frame 0 schon auf (Kalle kommt), am Ende wieder an derselben Stelle
    def door_rz(f):
        if f < S[1][0]:
            return math.radians(lerp(-25, -105, ease_out((f + 6) / 34)))
        if f >= S[12][0] + 30:
            return math.radians(lerp(-105, -25 + 0.0, ease_in_out((f - (S[12][0] + 30)) / max(1, N - 1 - (S[12][0] + 30))))) \
                if f < N - 1 else math.radians(lerp(-25, -105, ease_out(6 / 34)))
        return math.radians(-105)
    T.set(door, "rotation_euler", lambda f: (0, 0, door_rz(f)), 0, N - 1)

    # =================================================================== SZENE 1 – Nacht, Byte auf dem Tisch (push_in langsam)
    f0_1, f1_1 = S[0]
    set_byte(0, S[1][0], B_T)
    T.set(pinn.root, "location", lambda f: tuple(PIN_T), 0, S[3][0])
    T.set(pinn.root, "scale", lambda f: (0.5,) * 3, 0, S[3][0])
    T.set(pinn.root, "rotation_euler", lambda f: (math.radians(-8), 0, math.radians(5)), 0, S[3][0])
    set_kalle(0, S[1][0], DOOR, 0.0)
    T.add(k.root, "location", lambda f: (0, -0.5 * ease_out(min(1, (f + 8) / 50)), 0), 0, S[1][0])
    C.pose(T, k, {"sh_R": (-0.6, 0, 0.2), "el_R": (-0.8, 0, 0)}, -10, S[1][0] - 2, 1, 4, settle=False)  # Schluessel
    T.set(keys.root, "scale", lambda f: (1.3,) * 3 if f < S[1][0] else (0, 0, 0), 0, N)
    T.set(thermos.root, "scale", lambda f: (1.2,) * 3 if S[1][0] <= f < S[6][1] else (0, 0, 0), 0, N)
    C.byte_arm(T, b, "R", (-2.3, 0.6, 0.0), hl(0) - 6, f1_1 - 4, ramp=4)       # winkt
    T.add(b.arm["R"], "rotation_euler", lambda f: (0, 0, 0.5 * math.sin(f * 0.6) * window(f, hl(0) - 2, f1_1 - 4, 3, 4)), hl(0), f1_1)
    S1A = (BS.cams["totale"][0], BS.cams["totale"][1], BS.cams["totale"][2])
    s1 = push_in(f0_1, f1_1, (V(S1A[0]), B_T + V(-0.2, 0.3, 0.25), 28.0), k=0.12)
    S1W = (V(S1A[0]) + V(0, -0.6, 0.1), B_T + V(-0.2, 0.3, 0.25), 28.0)

    def shot1(f):
        t = ease_out(min(1.0, (f + 6) / 60))
        p1, t1_, l1 = s1(f)
        return (V(S1W[0]).lerp(V(p1), t), V(S1W[1]).lerp(V(t1_), t), lerp(S1W[2], l1, t))
    cam.add_shot(f0_1, f1_1, shot1)

    # =================================================================== SZENE 2 – Licht an, Kalle verschlafen (Nahe, zoom_gesicht)
    f0_2, f1_2 = S[1]
    set_kalle(f0_2, S[2][0], BS.kalle, 0.0)
    set_byte(f0_2, S[2][0], B_T)
    sw = f0_2                                          # Lichtschalter: Neonroehre flackert zweimal, dann an
    W.licht_extra += [(sw, sw + 3, "backstube", "nacht"), (sw + 3, sw + 5, "backstube", "frueh"),
                      (sw + 5, sw + 8, "backstube", "nacht"), (sw + 8, sw + 10, "backstube", "frueh"),
                      (sw + 10, sw + 12, "backstube", "nacht")]
    hat_tilt = (S[1][0], S[7][0])
    T.add(k.hat, "rotation_euler", lambda f: (0.1, 0.42, 0) if hat_tilt[0] <= f < hat_tilt[1] else (0, 0, 0), 0, N)
    T.add(k.hat, "location", lambda f: (0.06, 0, -0.03) if hat_tilt[0] <= f < hat_tilt[1] else (0, 0, 0), 0, N)
    T.set(k.lid["R"], "scale", lambda f: (1, 1, 1) if f0_2 <= f < hl(1) + 4 else (0, 0, 0), 0, N)
    T.add(k.lid["R"], "rotation_euler", lambda f: (1.05 * (1 - ease_out((f - hl(1)) / 4)) if f0_2 <= f < hl(1) + 4 else 0, 0, 0),
          f0_2, hl(1) + 5)
    yawn = wd(1, "früh?") + 8
    T.mul(k.mouth, "scale", lambda f: (1.1, 1, 1 + 3.5 * window(f, yawn, yawn + 12, 4, 5)), yawn, yawn + 12)
    T.add(k.head, "rotation_euler", lambda f: (-0.15 * window(f, yawn, yawn + 12, 4, 5), 0, 0), yawn, yawn + 12)
    hold_th = {"sh_L": (-0.7, 0, -0.35), "el_L": (-1.3, 0, 0)}
    C.pose(T, k, hold_th, f0_2, S[6][1], 4, 6, settle=False)
    C.reaction(T, coll, k, "staunen", hl(1) + 2, hold=f1_2 - hl(1) - 2, speaking=True, seed=2, hat=False)
    near = BS.cams["nah"]
    face_bs = V(BS.kalle) + V(0, -0.25, 1.95)
    cam.add_shot(f0_2, f1_2, zoom_gesicht(f0_2, f1_2, (V(near[0]), V(near[1]) + V(0, 0, 0.35), 40.0),
                                         (face_bs + V(0.1, -2.6, -0.05), face_bs + V(0, 0, -0.3), 48.0)))

    # =================================================================== SZENE 3 – 37 Bewerbungen -> 3 (kreisfahrt)
    f0_3, f1_3 = S[2]
    BST = ST.p(0.0, -0.4, 2.05)
    set_byte(f0_3, S[3][0], BST)
    mappen = []
    gold_idx = (8, 18, 28)
    for q in range(37):
        mp = NP.bewerbungsmappe(coll, f"mappe{q}", gold=q in gold_idx)
        mappen.append(mp)
    T.set(ST.objs["spot"].data, "energy", lambda f: 0, 0, 1)
    fan0 = f0_3 + 2
    grey = wd(2, "gelesen") - 2
    drei = wd(2, "drei") - 2
    GOLD_POS = [BST + V(-0.5, -0.75, -0.15), BST + V(0.0, -0.85, -0.05), BST + V(0.5, -0.75, -0.15)]
    for q, mp in enumerate(mappen):
        a = math.radians(170 - 160 * q / 36)
        R_ = 1.05
        fan_p = BST + V(R_ * math.cos(a), -0.35 - 0.002 * q, R_ * math.sin(a) * 0.95 + 0.05)
        t_in = fan0 + q * 0.35
        g = gold_idx.index(q) if q in gold_idx else None

        def loc(f, fan_p=fan_p, t_in=t_in, g=g, q=q):
            p = V(BST).lerp(fan_p, ease_out(min(1.0, max(0.0, (f - t_in) / 8))))
            if g is None and f > grey + (q % 12):
                p = p + V(0, 0.2, -1.2 * ease_in(min(1.0, (f - grey - (q % 12)) / 14)))
            if g is not None and f > drei + 4 * g:
                p = p.lerp(GOLD_POS[g], ease_in_out(min(1.0, (f - drei - 4 * g) / 10)))
            return tuple(p)
        T.set(mp.root, "location", loc, f0_3, S[4][1])
        T.set(mp.root, "rotation_euler", lambda f, a=a, g=g: (0, (a - math.pi / 2) * (1 - (ease_in_out(min(1.0, max(0.0, (f - drei - 4 * g) / 10)))
                                                                                     if g is not None else 0)), 0), f0_3, S[4][1])
        T.set(mp.lid, "rotation_euler", lambda f: (0, 0, -1.2), f0_3, f0_3 + 1)
        T.set(mp.root, "scale", lambda f, t_in=t_in, g=g, q=q: (1.25 * pop(f, t_in, 6) *
                                                               (1 if (g is not None or f < grey + (q % 12) + 10) else unpop(f, grey + (q % 12) + 10, 5)),) * 3
              if f0_3 <= f < S[3][0] or (g is not None and S[3][0] <= f < S[3][0]) else (0, 0, 0), 0, N)
        if g is None:
            NP.mappe_grau(T, mp, grey + (q % 12))
        else:
            NP.mappe_gold(T, mp, drei + 4 * g)
            cue(drei + 4 * g + 4, "pop", 0.9)
    grau = L.srgb("#7A7A88")
    blau = tuple(mappen[0].mat.diffuse_color)
    T.set(mappen[0].mat, "diffuse_color", lambda f: tuple(b_ + (g_ - b_) * ease_out((f - grey) / 10) for b_, g_ in zip(blau, grau))
          if f >= grey else blau, 0, N)
    C.byte_arm(T, b, "L", (-1.6, -1.0, 0), f0_3 + 2, grey, ramp=4)
    C.byte_arm(T, b, "R", (-1.6, 1.0, 0), f0_3 + 2, grey, ramp=4)
    cue(f0_3 - 5, "whoosh", 1.0)
    cam.whips.append((f0_3, 1))
    cam.add_shot(f0_3, f1_3, kreisfahrt(f0_3, f1_3, BST + V(0, 0, 0.2), 4.2, 0.35, -20, 18, 32.0))

    # =================================================================== SZENE 4 – Pinnwand, 1,10 € (push_in)
    f0_4, f1_4 = S[3]
    PIN_S = ST.p(0.75, 0.0, 2.35)
    T.set(pinn.root, "location", lambda f: tuple(PIN_S), S[3][0], S[5][0])
    T.set(pinn.root, "scale", lambda f: (1.45,) * 3, S[3][0], S[5][0])
    T.set(pinn.root, "rotation_euler", lambda f: (0, 0, math.radians(-6)), S[3][0], S[5][0])
    T.set(pinn.root, "scale", lambda f: (0, 0, 0), S[4][0], S[5][0])
    T.set(pinn.root, "location", lambda f: tuple(PIN_T), S[5][0], N)          # zurueck auf den Tisch (Backstube)
    T.set(pinn.root, "scale", lambda f: (0.5,) * 3, S[5][0], N)
    T.set(pinn.root, "rotation_euler", lambda f: (math.radians(-8), 0, math.radians(5)), S[5][0], N)
    for mp in mappen:                                   # Mappen im Studio weg (Gold-Mappen kommen in Szene 11 wieder)
        T.set(mp.root, "scale", lambda f: (0, 0, 0), S[3][0], S[10][0])
    BP = PIN_S + V(-1.0, -0.45, 0.05)
    set_byte(f0_4, S[4][0], BP)
    pz = NP.pinzette(coll, "pinzette")
    pz.root.parent = b.hand["R"]
    pz.root.location = (0, -0.02, -0.05)
    pz.root.rotation_euler = (math.pi, 0, 0)
    T.set(pz.root, "scale", lambda f: (1.4,) * 3 if f0_4 <= f < S[4][0] else (0, 0, 0), 0, N)
    pull = hl(3) - 6
    C.byte_arm(T, b, "R", (-1.5, -0.2, -0.6), pull - 8, f1_4, ramp=5)
    tag0 = V(pinn.tag.location)
    T.set(pinn.tag, "location", lambda f: tuple(tag0 + V(-0.35 * ease_out((f - pull) / 10), -0.25 * ease_out((f - pull) / 10),
                                                         0.08 * ease_out((f - pull) / 10))), f0_4, S[4][0])
    T.set(pinn.tag, "scale", lambda f: (1 + 0.5 * ease_out((f - pull) / 10),) * 3, f0_4, S[4][0])
    T.set(pinn.tag, "location", lambda f: tuple(tag0), S[4][0], N)
    T.set(pinn.tag, "scale", lambda f: (1, 1, 1), S[4][0], N)
    cam.add_shot(f0_4, f1_4, push_in(f0_4, f1_4, (ST.p(0.1, -4.4, 2.55), PIN_S + V(-0.45, 0, -0.05), 34.0), k=0.3))

    # =================================================================== SZENE 5 – Sterne 4,8 gegen 4,1 (schwenk links -> rechts)
    f0_5, f1_5 = S[4]
    sl_k = NP.sterne_leiste(coll, "sterne_kalle", "Kalle")
    sl_m = NP.sterne_leiste(coll, "sterne_markt", "Marktplatz")
    SK, SM = ST.p(-1.3, -0.55, 2.75), ST.p(1.3, -0.55, 2.75)
    for sl, P_ in ((sl_k, SK), (sl_m, SM)):
        sl.root.location = P_
        T.set(sl.root, "scale", lambda f: (1.35 * pop(f, f0_5 + 2, 6),) * 3 if f0_5 <= f < S[5][0] else (0, 0, 0), 0, N)
        T.add(sl.root, "location", lambda f: (0, 0, 0.04 * math.sin(f * 0.12)), f0_5, S[5][0])
    NP.sterne_fuellen(T, sl_k, 4.8, wd(4, "4,8") - 4, dt=6, cue=lambda f: cue(f, "pop", 0.8))
    NP.sterne_fuellen(T, sl_m, 4.1, wd(4, "4,1.") - 4, dt=5, cue=lambda f: cue(f, "pop", 0.6))
    set_byte(f0_5, S[5][0], ST.p(0.0, -0.75, 2.05))
    for side, sx in (("R", -1), ("L", 1)):              # Haende in die Seiten
        C.byte_arm(T, b, side, (0.3, -sx * 1.25, 0.0), f0_5 + 4, f1_5, ramp=5)
        T.add(b.hand[side], "rotation_euler", lambda f, sx=sx: (0, 0, sx * 1.2 * window(f, f0_5 + 4, f1_5, 5, 5)), f0_5, f1_5)
    cam.add_shot(f0_5, f1_5, schwenk(f0_5, f1_5, (ST.p(-0.8, -4.2, 2.6), SK + V(0.1, 0, -0.25), 36.0),
                                     (ST.p(0.8, -4.2, 2.6), SM + V(-0.1, 0, -0.25), 36.0)))

    # =================================================================== Theke: Laptop wie in Folge 'viral'
    lap = TH.objs["laptop"]
    LAP = TH.p(0.45, -0.36, top)
    LS = 1.35
    lap.root.location = LAP
    lap.root.rotation_euler = (0, 0, math.radians(-18))
    lap.root.scale = (LS, LS, LS)
    laptop_display(lap)
    TH.objs["basket"].location.x += 0.45
    rz = math.radians(-18)
    SCR = LAP + V(-math.sin(rz) * 0.326, math.cos(rz) * 0.326, 0.305)
    K = V(TH.kalle)
    face = K + V(0, -0.25, 1.95)
    stack_t = NP.auftrags_stapel(coll, "stapel_theke", n=4)
    STK = TH.p(-0.45, -0.5, top)
    stack_t.root.location = STK
    T.set(stack_t.root, "scale", lambda f: (1.2, 1.2, 1.2) if S[5][0] <= f < S[7][0] else (0, 0, 0), 0, N)

    # =================================================================== SZENE 6 – 62 Bestellungen (fahrt am Laptop)
    f0_6, f1_6 = S[5]
    set_kalle(f0_6, S[7][0], K, 0.0)
    set_byte(f0_6, S[7][0], SCR + V(0.55, -0.35, 0.3))
    rr = random.Random(66)
    for q in range(14):
        pf = NP.auftrags_papierflieger(coll, f"flieger{q}")
        t0 = f0_6 + 4 + q * 4.5
        dst = STK + V(rr.uniform(-0.05, 0.05), rr.uniform(-0.05, 0.05), 0.06 + 0.02 * q)
        up = rr.uniform(0.25, 0.55)

        def floc(f, t0=t0, dst=dst, up=up):
            t = min(1.0, max(0.0, (f - t0) / 14))
            p = V(SCR + V(0, -0.1, 0.0)).lerp(dst, ease_in_out(t))
            p.z += up * math.sin(math.pi * t)
            return tuple(p)
        T.set(pf.root, "location", floc, t0 - 1, t0 + 15)
        T.set(pf.root, "rotation_euler", lambda f, t0=t0: (0.3 * math.sin(f * 0.5), 0.2, math.radians(120) + 0.3 * math.sin(f * 0.3)),
              t0 - 1, t0 + 15)
        T.set(pf.root, "scale", lambda f, t0=t0: (1.6 * pop(f, t0, 4) * (unpop(f, t0 + 14, 3) if f > t0 + 14 else 1),) * 3
              if t0 <= f < t0 + 18 else (0, 0, 0), 0, N)
        T.set(pf.stamp, "scale", lambda f, t0=t0: (pop(f, t0 + 6, 4, 1.4),) * 3 if f >= t0 + 5 else (0, 0, 0), 0, N)
    T.set(stack_t.root, "scale", lambda f: (1.2, 1.2, 1.2 + 0.25 * ease_out((f - f0_6) / 70)), f0_6, S[6][0])
    st = PR.stempel(coll, "stempel6")
    st.parent = b.hand["L"]
    st.location = (0, -0.02, -0.08)
    st.rotation_euler = (math.pi, 0, 0)
    T.set(st, "scale", lambda f: (0.55,) * 3 if f0_6 <= f < S[6][0] else (0, 0, 0), 0, N)
    C.byte_arm(T, b, "L", (-1.2, -0.3, 0.0), f0_6 + 2, f1_6 - 2, ramp=3)
    T.add(b.arm["L"], "rotation_euler", lambda f: (0.4 * max(0.0, math.sin(f * 1.4)) * window(f, f0_6 + 4, f1_6 - 4, 2, 2), 0, 0),
          f0_6, f1_6)
    done = wd(5, "bestätigt.") + 4
    cue(f0_6 - 5, "whoosh", 1.0)
    cue(done, "ding", 1.0)
    cam.whips.append((f0_6, -1))
    C.reaction(T, coll, k, "neutral", hl(5), seed=6)
    cam.add_shot(f0_6, f1_6, fahrt(f0_6, f1_6, (SCR + V(-0.95, -2.5, 0.35), SCR + V(-0.3, 0, 0.05), 34.0),
                                   (SCR + V(0.2, -2.45, 0.35), SCR + V(0.1, 0, 0.05), 34.0)))

    # =================================================================== SZENE 7 – Alle schon bestaetigt? (langsamer Zoom)
    f0_7, f1_7 = S[6]
    paper = L.box("bestaetigung_hand", (0.2, 0.004, 0.27), L.mat("paper", "#F5F1E8", 0.7), k.hand["R"], (0, -0.08, -0.12), coll)
    L.box("bestaetigung_stamp", (0.12, 0.006, 0.05), L.mat("stamp_gruen", "#2FB36A", 0.5, emit="#2FB36A", strength=1.0), paper,
          (0.02, -0.004, -0.06), coll)
    T.set(paper, "scale", lambda f: (1, 1, 1) if f0_7 + 2 <= f < S[7][0] else (0, 0, 0), 0, N)
    read = {"sh_R": (-1.45, 0, 0.4), "el_R": (-0.9, 0, 0)}
    sink = wd(6, "bestätigt?") + 4
    C.pose(T, k, read, f0_7, sink, 6, 14, settle=False)
    T.add(k.head, "rotation_euler", lambda f: (0.22 * window(f, f0_7 + 2, f1_7 + 4, 8, 10), 0, 0), f0_7, f1_7 + 4)
    C.kalle_react(T, k, "zweifel", hl(6) - 4, hold=f1_7 - hl(6) + 4, speaking=True)
    th_c = NP.thermoskanne(coll, "thermos_theke")
    th_c.root.location = TH.p(-0.6, -0.45, top)
    th_c.root.scale = (1.2,) * 3
    put = f1_7 - 14
    T.set(thermos.root, "scale", lambda f: (0, 0, 0) if f >= put else ((1.2,) * 3 if S[1][0] <= f < S[6][1] else (0, 0, 0)), 0, N)
    T.set(th_c.root, "scale", lambda f: (1.2,) * 3 if put <= f < S[7][0] else (0, 0, 0), 0, N)
    cam.add_shot(f0_7, f1_7, zoom_gesicht(f0_7, f1_7, (face + V(0.15, -3.2, 0.0), face + V(0, 0, -0.3), 44.0),
                                         (face + V(0.1, -2.8, -0.02), face + V(0, 0, -0.28), 47.0), ease_in_out))

    # =================================================================== SZENE 8 – Kalle allein vor dem Ofen (Totale, sehr langsamer push_in)
    f0_8, f1_8 = S[7]
    seat_z = 0.1
    set_kalle(f0_8, S[11][0] + 4, K_SACK, 0.22)
    sit = {"hip_R": (-1.5, 0, 0.1), "hip_L": (-1.5, 0, -0.1), "knee_R": (1.45, 0, 0), "knee_L": (1.45, 0, 0), "skirt": (-0.6, 0, 0)}
    stand_up = wd(11, "na") + 2
    C.pose(T, k, sit, f0_8 - 1, stand_up, 1, 10, settle=False)
    T.add(k.body, "location", lambda f: (0, 0, seat_z * window(f, f0_8 - 1, stand_up, 1, 10)), f0_8 - 1, stand_up + 10)
    sad_end = S[9][0] + 30
    C.kalle_traurig(T, k, f0_8 + 6, sad_end, speaking=False, ramp=18)
    # Muetze ab: in beiden Haenden vor dem Bauch (Szene 8 bis 11), in Szene 12 gerade aufgesetzt
    off = wd(7, "dann") - 6
    hat_on = stand_up + 18
    HAT_HOME = V(k.hat.location)
    HAT_HAND = HAT_HOME + V(0, -0.55, -0.95)

    def hat_loc(f):
        if f < off or f >= hat_on + 12:
            return (0, 0, 0)
        if f < off + 18:
            return tuple((HAT_HAND - HAT_HOME) * ease_in_out((f - off) / 18) + V(0, 0, 0.15 * math.sin(math.pi * (f - off) / 18)))
        if f < hat_on:
            return tuple(HAT_HAND - HAT_HOME)
        return tuple((HAT_HAND - HAT_HOME) * (1 - ease_in_out((f - hat_on) / 12)) + V(0, 0, 0.2 * math.sin(math.pi * (f - hat_on) / 12)))
    T.add(k.hat, "location", hat_loc, off, hat_on + 13)
    T.add(k.hat, "rotation_euler", lambda f: (0.9 * window(f, off, hat_on + 12, 18, 12), 0, 0), off, hat_on + 13)
    holdhat = {"sh_R": (-0.65, 0, 0.45), "sh_L": (-0.65, 0, -0.45), "el_R": (-1.1, 0, 0), "el_L": (-1.1, 0, 0)}
    C.pose(T, k, holdhat, off - 4, hat_on + 2, 14, 10, settle=False)
    BDOOR = BS.p(0.9, 3.3, 1.55)
    set_byte(f0_8, S[8][0], BDOOR)
    T.set(b.root, "scale", lambda f: (0.85,) * 3, f0_8, S[8][0])
    T.set(b.root, "scale", lambda f: (1, 1, 1), S[8][0], S[8][0] + 1)
    W.licht_extra.append((S[7][0], S[7][1], "backstube", "frueh"))
    cue(f0_8, "whoosh", 0.25)                               # sehr leise
    for f_ in range(f0_8 + 4, S[9][0], 60):                   # Raumatmosphaere: Glut knistert, Uhr tickt
        cue(f_, "knistern", 0.22)
    for f_ in range(f0_8 + 10, S[9][0], 30):
        cue(f_, "ticken", 0.14)
    KS_face = K_SACK + V(0.05, -0.2, 1.62)
    tot = BS.cams["totale"]
    cam.add_shot(f0_8, f1_8, push_in(f0_8, f1_8, (V(tot[0]) + V(-0.6, 0.6, -0.2), KS_face + V(0.25, 0.7, -0.05), 28.0), k=0.1))

    # =================================================================== SZENE 9 – Byte kann nicht backen (Nahe, zoom auf die Haende)
    f0_9, f1_9 = S[8]
    BLAND = BS.p(-1.0, 0.4, TZ + 0.24)
    b9 = path([(f0_9, BDOOR), (f0_9 + 30, BS.p(-0.4, 1.0, 1.7)), (f0_9 + 50, BLAND)], ease_in_out)
    T.set(b.root, "location", lambda f: b9(f), f0_9, S[9][0])
    T.mul(b.body, "scale", lambda f: (1 + 0.1 * window(f, f0_9 + 50, f0_9 + 58, 1, 5), 1, 1 - 0.12 * window(f, f0_9 + 50, f0_9 + 58, 1, 5)),
          f0_9 + 49, f0_9 + 59)
    kl = NP.teigklumpen(coll, "klumpen")
    KL = BS.p(-0.72, 0.28, TZ)
    kl.root.location = KL
    T.set(kl.root, "scale", lambda f: (pop(f, f0_9 + 54, 5),) * 3 if f0_9 + 53 <= f < S[10][0] else (0, 0, 0), 0, N)
    knead0, tip = f0_9 + 56, wd(8, "nicht.") - 2
    for side, sx in (("R", -1), ("L", 1)):
        C.byte_arm(T, b, side, (-1.1, -sx * 0.15, 0.0), knead0, tip + 4, ramp=5)
        T.add(b.arm[side], "rotation_euler", lambda f, sx=sx: (0.25 * math.sin(f * 0.8 + (0 if sx < 0 else math.pi)) *
                                                               window(f, knead0, tip, 3, 3), 0, 0), knead0, tip)
        C.byte_hand(T, b, side, "grab", knead0, tip)
    T.add(kl.body, "scale", lambda f: (0.12 * math.sin(f * 0.8), 0, -0.1 * math.sin(f * 0.8)) if knead0 <= f < tip else (0, 0, 0),
          knead0, tip)
    NP.klumpen_kippen(T, kl, tip)
    T.add(b.root, "rotation_euler", lambda f: (0, 0, 0.35), f0_9 + 50, S[9][0])
    W.licht_extra.append((S[8][0], S[8][1], "backstube", "frueh"))
    for f_ in range(f0_9 + 20, f1_9, 60):
        cue(f_, "knistern", 0.22)
    for f_ in range(f0_9 + 5, f1_9, 30):
        cue(f_, "ticken", 0.14)
    cam.add_shot(f0_9, f1_9, zoom(f0_9, f1_9, (BS.p(-0.55, -1.9, 1.75), BS.p(-0.85, 0.45, 1.25), 40.0),
                                  (BS.p(-0.75, -1.75, 1.6), KL + V(-0.18, 0.05, 0.22), 46.0), ease_in_out))

    # =================================================================== SZENE 10 – Morgensonne, Bewertungskarte (schwenk Fenster -> die beiden)
    f0_10, f1_10 = S[9]
    B10 = K_SACK + V(0.55, -0.45, 1.25)
    b10 = path([(f0_10, BLAND), (f0_10 + 16, B10)], ease_in_out)
    T.set(b.root, "location", lambda f: b10(f), f0_10, S[10][0])
    karte = NP.bewertungskarte(coll, "karte")
    karte.root.parent = b.hand["L"]
    karte.root.location = (0.0, -0.06, -0.18)
    karte.root.rotation_euler = (0, 0, math.radians(-25))
    give = wd(9, "kommen") - 4
    T.set(karte.root, "scale", lambda f: (1.4 * pop(f, give, 6),) * 3 if give <= f < S[11][0] else (0, 0, 0), 0, N)
    C.byte_arm(T, b, "L", (-1.35, 0.35, 0.0), give - 2, S[11][0] - 4, ramp=6)
    C.byte_hand(T, b, "L", "grab", give - 2, S[11][0] - 4)
    T.add(b.root, "rotation_euler", lambda f: (0, 0, 0.45), f0_10, S[10][0])
    win = BS.objs["window"]
    cam.add_shot(f0_10, f1_10, schwenk(f0_10, f1_10, (BS.p(0.9, -2.6, 2.4), win + V(0, 0, -0.1), 36.0),
                                       (BS.p(-0.2, -3.4, 2.0), K_SACK + V(0.15, -0.2, 1.35), 36.0)))

    # =================================================================== SZENE 11 – drei goldene Mappen 'Gespraech mit Kalle' (rueckfahrt)
    f0_11, f1_11 = S[10]
    set_byte(f0_11, S[11][0], B10 + V(0.25, 0.1, 0.15))
    ROW = [K_SACK + V(-0.55 + 0.55 * j, -0.75, 1.15) for j in range(3)]
    for j, q in enumerate(gold_idx):
        mp = mappen[q]
        t0 = f0_11 + 4 + 6 * j
        src = ROW[j] + V(2.0 - j * 0.3, 0.6, 0.8)
        T.set(mp.root, "location", lambda f, t0=t0, src=src, j=j: tuple(V(src).lerp(ROW[j], ease_out(min(1.0, max(0.0, (f - t0) / 14))))
                                                                         + V(0, 0, 0.03 * math.sin(f * 0.2 + j))), f0_11, S[11][0] + 30)
        T.set(mp.root, "rotation_euler", lambda f: (0, 0, 0), f0_11, f0_11 + 1)
        T.set(mp.root, "scale", lambda f, t0=t0: (1.6 * pop(f, t0, 6),) * 3 if t0 <= f < S[11][0] + 30 else (0, 0, 0), S[10][0], N)
        T.set(mp.lid, "rotation_euler", lambda f: (0, 0, 0), f0_11, f0_11 + 1)
        T.set(mp.gesp, "scale", lambda f, t0=t0: (1.5 * pop(f, t0 + 12, 6),) * 3 if f >= t0 + 11 else (0, 0, 0), S[10][0], N)
        T.set(mp.check, "scale", lambda f: (0, 0, 0), S[10][0], N)
    cue(f0_11 + 4 + 12 + 14, "ding", 1.0)
    cam.add_shot(f0_11, f1_11, rueckfahrt(f0_11, f1_11, (K_SACK + V(0.3, -3.0, 1.6), K_SACK + V(0.15, 0, 1.25), 40.0),
                                          (K_SACK + V(0.6, -4.2, 1.9), K_SACK + V(0.3, 0, 1.3), 36.0), ease_out))

    # =================================================================== SZENE 12 – Kalle backt wieder (Totale, push_in)
    f0_12, f1_12 = S[11]
    set_byte(f0_12, S[12][0], B10 + V(0.45, 0.1, 0.1))
    T.set(k.root, "location", lambda f: tuple(K_SACK + V(0.15 * ease_in_out((f - stand_up) / 12), -0.25 * ease_in_out((f - stand_up) / 12), 0)),
          f0_12, S[12][0])
    T.set(k.root, "rotation_euler", lambda f: (0, 0, 0.22 - 0.22 * ease_in_out((f - stand_up) / 12)), f0_12, S[12][0])
    sleeves = {"sh_R": (-0.4, 0, 0.9), "sh_L": (-0.4, 0, -0.9), "el_R": (-1.9, 0, 0), "el_L": (-1.9, 0, 0)}
    C.pose(T, k, sleeves, hat_on + 10, hat_on + 20, 4, 4)
    log = NP.holzscheit(coll, "scheit")
    throw = flare - 10
    L0 = K_SACK + V(-0.2, -0.3, 1.2)

    def lg(f):
        t = min(1.0, max(0.0, (f - throw) / 10))
        p = L0.lerp(mouth + V(0, 0.05, -0.15), ease_in(t))
        p.z += 0.35 * math.sin(math.pi * t)
        return tuple(p)
    T.set(log.root, "location", lg, throw - 1, flare + 2)
    T.set(log.root, "rotation_euler", lambda f: (0, 0, 1.2 + 0.4 * (f - throw) * 0.1), throw - 1, flare + 2)
    T.set(log.root, "scale", lambda f: (1, 1, 1) if throw - 3 <= f < flare else (0, 0, 0), 0, N)
    C.pose(T, k, {"sh_L": (-1.6, 0, -0.6), "el_L": (-0.3, 0, 0)}, throw - 5, throw + 4, 3, 6)
    PR.burst(T, coll, "s12spark", "spark", tuple(mouth + V(0, -0.25, 0)), flare, 26, 1201, speed=(0.8, 1.6), up=1.2,
             gravity=-0.8, life=(16, 26), size=(0.7, 1.2), drag=1.0)
    braid0 = hl(11) - 10
    C.kalle_haende(T, k, "kneten", braid0 - 10, braid0 + 8)
    brz = PR.pastry(coll, "s12brezel", "brezel", k.hand["R"], (0.12, -0.1, -0.1), 1.4)
    brz.rotation_euler = (math.pi / 2, 0, 0)
    T.set(brz, "scale", lambda f: (1.4 * pop(f, braid0 + 6, 6, 1.25),) * 3 if braid0 + 5 <= f < S[12][0] else (0, 0, 0), 0, N)
    C.reaction(T, coll, k, "jubel", hl(11) + 2, hold=f1_12 - hl(11) - 4, speaking=True, seed=12, hat=False)
    clap0 = hl(11)
    for side, sx in (("R", -1), ("L", 1)):              # Byte klatscht
        C.byte_arm(T, b, side, (-1.4, sx * 0.55, 0.0), clap0 - 6, f1_12 - 2, ramp=4)
        T.add(b.arm[side], "rotation_euler", lambda f, sx=sx: (0, sx * 0.35 * max(0.0, math.sin(f * 1.3)) * window(f, clap0, f1_12 - 4, 2, 3), 0),
              clap0, f1_12)
        C.byte_hand(T, b, side, "offen", clap0 - 6, f1_12 - 2)
    cam.add_shot(f0_12, f1_12, push_in(f0_12, f1_12, (V(tot[0]) + V(-0.3, 0.8, -0.15), K_SACK + V(0.8, 0.3, 1.35), 30.0), k=0.2))

    # =================================================================== SZENE 13 – Zeitraffer bis 4:12 (fahrt -> Startposition)
    f0_13, f1_13 = S[12]
    W.licht_extra += [(f0_13, f0_13 + 12, "backstube", "morgen"), (f0_13 + 12, f0_13 + 22, "backstube", "frueh"),
                      (f0_13 + 22, f0_13 + 28, "backstube", "morgen"), (f0_13 + 28, f0_13 + 34, "backstube", "frueh")]
    sun = BS.objs["sun"]
    sun0 = V(sun.location)
    T.set(sun, "location", lambda f: tuple(sun0 + V(0.6 * ease_in_out((f - f0_13) / 34), 0, 0.35 * math.sin(math.pi * min(1, (f - f0_13) / 34)))),
          f0_13, N)
    # Kalle backt (schnell), haengt die Schuerze an den Haken und geht durch die Tuer
    C.kalle_haende(T, k, "kneten", f0_13, f0_13 + 18, ramp=3)
    HOOK = BS.p(1.75, 2.55, 0)
    walk0, at_hook, at_door = f0_13 + 18, f0_13 + 40, N - 12
    kp = path([(walk0, K_SACK + V(0.15, -0.25, 0)), (walk0 + 10, BS.p(-0.2, 1.6, 0)), (at_hook, HOOK),
               (at_hook + 10, HOOK + V(-0.3, 0.3, 0)), (at_door, DOOR + V(0, -0.5, 0))], ease_in_out)
    T.set(k.root, "location", lambda f: kp(f) if f >= walk0 else tuple(K_SACK + V(0.15, -0.25, 0)), f0_13, N)

    def k_rz(f):
        if f < walk0:
            return 0.0
        if f < at_hook:
            return lerp(0.0, math.pi * 0.85, ease_in_out((f - walk0) / 10))
        if f < at_door - 8:
            return math.pi * 0.95
        return lerp(math.pi * 0.95, 0.0, ease_in_out((f - (at_door - 8)) / 10))
    T.set(k.root, "rotation_euler", lambda f: (0, 0, k_rz(f)), f0_13, N)
    for side, ph in (("R", 0), ("L", math.pi)):
        T.add(k.hip[side], "rotation_euler", lambda f, ph=ph: (0.5 * math.sin((f - walk0) * 0.7 + ph) * window(f, walk0, at_door, 3, 4), 0, 0),
              walk0, at_door)
    apron_objs = [o for o in bpy.data.objects if o.name in ("k_apron", "k_apron_skirt", "k_towel", "k_towel_back")]
    for o in apron_objs:
        T.set(o, "scale", lambda f, s0=tuple(o.scale): (0, 0, 0) if at_hook + 4 <= f < N - 1 else s0, 0, N)
    T.set(haken.apron, "scale", lambda f: (1, 1, 1) if at_hook + 4 <= f < N - 1 else (0, 0, 0), 0, N)
    # Kunden kommen und gehen im Verkaufsraum (durch die Tuer sichtbar)
    for q in range(3):
        cu = PR.customer(coll, f"kunde_zr{q}", ["#E0703D", "#3E8E6A", "#6C5BA8"][q], s=3.2)
        y = 6.4 - 0.4 * q
        t_a = f0_13 + 2 + q * 8
        PR.customer_walk(T, cu, lambda t, y=y, q=q: tuple(BS.p(-1.0 + 3.8 * t if q % 2 == 0 else 2.8 - 3.8 * t, y, 0)), t_a, t_a + 30,
                         t_a + 30)
        T.set(cu.root, "scale", lambda f, t_a=t_a: (3.2,) * 3 if t_a <= f < t_a + 30 else (0, 0, 0), 0, N)
    # Byte wieder auf dem Tisch, neue Stapel wachsen
    bb = path([(f0_13, B10 + V(0.45, 0.1, 0.1)), (f0_13 + 16, B_T)], ease_in_out)
    T.set(b.root, "location", lambda f: bb(f), f0_13, N)
    T.set(stapel_m.root, "scale", lambda f: (1, 1, 0.2 + 0.8 * ease_out((f - f0_13 - 20) / 50)) if f >= f0_13 else (1, 1, 1), f0_13, N)
    T.set(stapel_a.root, "scale", lambda f: (1, 1, 0.2 + 0.8 * ease_out((f - f0_13 - 26) / 46)) if f >= f0_13 else (1, 1, 1), f0_13, N)
    T.set(stapel_m.root, "scale", lambda f: (1, 1, 1), 0, 1)
    T.set(stapel_a.root, "scale", lambda f: (1, 1, 1), 0, 1)
    T.set(keys.root, "scale", lambda f: (1.3,) * 3 if f >= at_door - 6 else ((1.3,) * 3 if f < S[1][0] else (0, 0, 0)), 0, N)
    cam.add_shot(f0_13, N, fahrt(f0_13, N - 8, (BS.p(0.2, -3.6, 2.1), BS.p(0.2, 1.2, 1.4), 30.0), shot1(0)))

    # ------------------------------------------------------------ Bytes Display-Augen je Reaktion
    eyes = ["jubel", "neutral", "jubel", "neutral", "jubel", "jubel", "zweifel", "traurig", "traurig", "neutral", "jubel",
            "jubel", "jubel"]
    sched = [(0, "jubel")] + [(S[i][0], e) for i, e in enumerate(eyes)]
    sched += [(S[9][0] + 20, "neutral"), (hl(1), "staunen")]
    C.byte_face(T, b, sched, 0, N - 1)

    def focus(f):
        i = next((j for j, s in enumerate(sc) if s["f0"] <= f < s["f1"]), len(sc) - 1)
        if i in (0, 2, 3, 4, 8, 12):
            return V(T.loc(b.root, f))
        if i == 5:
            return V(SCR)
        return V(T.loc(k.root, f)) + V(0, -0.25, 1.7 if i in (7, 9, 10) else 1.95)
    W.cam.focus_fn = focus
