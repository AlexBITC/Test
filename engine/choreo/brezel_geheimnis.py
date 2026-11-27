"""Regie fuer 'Das Geheimnis in Kalles Haenden' (folge-10-brezel-geheimnis). Szenen-Index 0..13 = Szene 1..14.

Gefuehlsbogen: 1 Frust (schnell, laut), 2-3 der Kipp-Moment (leise, keine Effekte, Blicke), 4-8 Byte als Forscher
(Zeitlupe), 9-11 Lernen und Durchbruch (POV mit [AR]), 12 Kalles stiller Stolz (erster Mehlfleck), 13 erster Verkauf
(durchs Schaufenster, weiche Ueberblendung), 14 Team, Loop.
Kulissen: backstube -> studio -> backstube -> studio -> backstube (morgen) -> theke -> backstube.
Kameras nie zweimal hintereinander gleich: push_in, zoom_gesicht, schwenk, rueckfahrt, zeitlupe_haende+rueckfahrt,
zeitlupe_haende (Handgelenk), zoom_gesicht, schwenk (Eisberg), push_in, pov, rueckfahrt, zoom_gesicht, durchs_fenster
+push_in, Fahrt in die Startposition.
Requisiten: assets/props/brezel_geheimnis.py, Bildschirm: assets/screens/brezel_geheimnis.py.
"""
import math
import os
import sys


import characters as C
import look as L
import props as PR
import lea as LE
import ar as AR
import kameras as KA
from anim import (ease_in, ease_out, ease_in_out, window, pop, unpop, lerp, clamp01)
from choreo.common import Ctx, path, V
from choreo.mehlpreis import fahrt, push_in

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "props"))
import brezel_geheimnis as BG  # noqa: E402
import viral as VP  # noqa: E402
import nachtschicht as NP  # noqa: E402

FPS = 30
zoom_gesicht = schwenk = rueckfahrt = fahrt


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    l = W.lea
    BS, ST, TH = c.sets["backstube"], c.sets["studio"], c.sets["theke"]
    sc = c.sc
    S = [(s["f0"], s["f1"]) for s in sc]
    coll = W.coll
    cam = W.cam
    TZ = BS.table_z

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
    W.anchors["lea_face"] = L.empty("anchor_lea_face", l.head, (0, -0.22, 0.28), coll)
    W.anchors["byte"] = b.body
    W.licht_extra = []
    W.cam.blenden = [(S[12][0], 15)]                    # weicher Uebergang in die Theke (0,5 s)

    # ------------------------------------------------------------ Grundbewegung (alle drei Figuren)
    C.kalle_idle(T, k, 0, N - 1, seed=7)
    LE.lea_idle(T, l, 0, N - 1, seed=23)
    C.byte_idle(T, b, 0, N - 1, seed=3, amp=0.02)
    C.byte_blinks(T, b, 0, N - 1, seed=11)
    C.antenna_spring(T, b, 2, N - 1)
    C.follow_through(T, k.hat, k.head, "rotation_euler", 2, 0.9, 3, 0, N - 1)
    C.follow_through(T, k.skirt, k.hips, "rotation_euler", 1, 1.2, 4, 0, N - 1)
    C.follow_through(T, l.skirt, l.hips, "rotation_euler", 1, 1.2, 4, 0, N - 1)
    if getattr(k, "towel", None):
        C.follow_through(T, k.towel, k.hips, "rotation_euler", 1, 2.0, 5, 0, N - 1, out_idx=0)
    C.pose(T, k, "arms_rest", -10, None, 1, 1, weight=0.6, settle=False)
    C.pose(T, l, "arms_rest", -10, None, 1, 1, weight=0.6, settle=False)
    ruhig = (1, 2, 11, 12)
    for i, s in enumerate(sc):
        if s["sprecher"] == "kalle":
            C.kalle_lipsync(T, k, s, s["f0"], s["f1"])
        elif s["sprecher"] == "lea":
            LE.lea_lipsync(T, l, s, s["f0"], s["f1"])
        else:
            C.byte_speak(T, b, s, s["f0"], s["f1"])
        if i not in ruhig and i != 9:
            for w in s["words"]:
                if w["hl"]:
                    cam.punch.append(w["f0"])
    cam.drift_env = lambda f: min(1.0, f / 10.0, max(0.0, (N - 7 - f) / 10.0)) * \
        (0.35 if any(S[i][0] <= f < S[i][1] for i in ruhig) else 1.0)
    for o in (b.body, b.root, k.root, l.root):
        T.set(o, "rotation_euler", lambda f: (0, 0, 0), 0, 1)
    k.cloth.scale = (0, 0, 0)

    def setze(fig, f0, f1, loc, rz=0.0, s=1.0):
        T.set(fig.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(fig.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)
        T.set(fig.root, "scale", lambda f, s=s: (s, s, s), f0, f1)

    def setze_byte(f0, f1, loc, s=1.0):
        T.set(b.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(b.root, "scale", lambda f, s=s: (s, s, s), f0, f1)

    def weg(fig, f0, f1):
        setze(fig, f0, f1, BS.p(6.0, 6.0, 0), 0.0, 1.0)

    # ------------------------------------------------------------ Backstube: Aufbau
    K_BS = BS.p(0.62, 1.38, 0)
    L_BS = BS.p(-0.42, 1.36, 0)
    BG.reihe_missglueckt(coll, "mg", BS.p(-0.95, 0.2, TZ), V(0.205, 0, 0), s=0.72)
    uhr = NP.wanduhr_backstube(coll, "uhr_bs")
    uhr.root.location = BS.p(2.3, 3.1, 2.75)
    NP.uhr_stellen(T, uhr, lambda f: 6 * 60 + 40 + f / FPS * 0.6, 0, N - 1)
    uhr.t412.scale = (0, 0, 0)
    uhr.tnach.scale = (0, 0, 0)
    blech = VP.brezelblech(coll, "blech")
    blech.root.location = BS.p(1.05, 0.62, TZ)
    zettel = BG.schildchen_handschrift(coll, "versuch10", "Versuch 10")
    zettel.root.location = BS.p(-1.12, 0.45, TZ)
    zettel.root.rotation_euler = (0, 0, 0.3)
    sack = PR.flour_sack(coll, "sack_bs", label=True, scale=1.1, text1="WEIZEN", text2="550")
    sack.root.location = BS.p(-1.9, 1.1, 0)
    sack.root.rotation_euler = (0, 0, 0.25)
    # die zehnte Brezel (Lea haelt sie hoch, sie sackt zusammen)
    zehnte = BG.brezel_missglueckt(coll, "zehnte", "acht", 1.0)
    zehnte.root.parent = l.hand["L"]
    zehnte.root.location = (0.02, -0.06, -0.12)
    zehnte.root.rotation_euler = (math.pi / 2, 0, 0)
    f0_1, f1_1 = S[0]

    T.set(zehnte.root, "rotation_euler", lambda f: (math.pi / 2 + 0.9 * ease_in(clamp01((f + 6) / 20)), 0,
                                                     0.3 * math.sin(f * 0.5) * (1 - clamp01((f + 6) / 20))), 0, f1_1)
    T.set(zehnte.root, "scale", lambda f: (1, 1, 1 - 0.45 * ease_in(clamp01((f + 6) / 20))) if (f < f1_1 + 4 or f >= N - 14)
          else (0, 0, 0), 0, N)

    # Mehl an Leas Haenden waechst ueber die Folge; Mehlstrich ab Szene 2, Mehlfleck ab Szene 12
    def mehl_level(f):
        if f < S[3][0]:
            return 0.35
        if f < S[9][0]:
            return 0.55
        return 0.55 + 0.45 * clamp01((f - S[9][0]) / max(1, S[11][0] - S[9][0]))
    LE.lea_mehl(T, l, mehl_level, 0, N - 1)

    # =================================================================== SZENE 1 (push_in, Bewegung ab Frame 0)
    setze(k, 0, S[1][1], K_BS, 0.0)
    setze(l, 0, S[3][1], L_BS, 0.0)
    setze_byte(0, S[2][0], BS.p(1.55, 1.9, 2.05), 0.8)
    C.pose(T, l, {"sh_L": (-1.75, -0.95, 0.0), "el_L": (-0.25, 0, 0), "hips": (0.04, 0, 0)}, -8, 18, 1, 14, settle=False)
    T.add(l.body, "location", lambda f: (0, 0, -0.04 * ease_out(clamp01((f + 4) / 22))), 0, f1_1)   # sackt in sich zusammen
    T.add(l.head, "rotation_euler", lambda f: (0.12 * ease_out(clamp01((f + 4) / 22)), 0, 0), 0, f1_1)
    # Kalle rauft sich unter der Muetze die Haare (beide Haende zum Kopf), Mehl staubt
    C.pose(T, k, {"sh_R": (-2.75, 0.3, 0.25), "sh_L": (-2.75, -0.3, -0.25), "el_R": (-0.95, 0, 0), "el_L": (-0.95, 0, 0)},
           -4, f1_1 - 10, 1, 8, settle=False)
    for side in ("R", "L"):
        T.add(k.hand[side], "rotation_euler", lambda f: (0.35 * math.sin(f * 0.9), 0, 0), 0, f1_1 - 6)
    T.add(k.hat, "location", lambda f: (0, 0, 0.04 * abs(math.sin(f * 0.45)) * window(f, 0, f1_1 - 6, 1, 6)), 0, f1_1)
    BG.mehl_puder(T, coll, "s1puder", K_BS + V(0, -0.1, 2.45), 2, 16, 101)
    BG.mehl_puder(T, coll, "s1puder2", K_BS + V(0, -0.1, 2.45), 14, 10, 102)
    C.kalle_look(T, k, lambda f: BS.p(-0.3, 0.2, TZ), 0, S[2][0] + 6, ramp=3)       # schaut auf die Brezeln
    C.kalle_react(T, k, "schock", hl(0), hold=f1_1 - hl(0) - 2, speaking=True, hat=False)
    cue(8, "buzz", 0.9)
    S1A = (BS.p(-0.25, -2.75, 2.75), BS.p(0.0, 0.75, 1.3), 30.0)
    S1W = (BS.p(-0.45, -3.6, 3.0), BS.p(0.0, 0.75, 1.3), 30.0)
    s1 = push_in(f0_1, f1_1, S1A, k=0.2)

    def shot1(f):
        t = ease_out(min(1.0, (f + 6) / 26))
        p0, t0_, l0 = S1W
        p1, t1_, l1 = s1(f)
        return (V(p0).lerp(V(p1), t), V(t0_).lerp(V(t1_), t), lerp(l0, l1, t))
    cam.add_shot(f0_1, f1_1, shot1)

    # =================================================================== SZENE 2 (Lea, zoom_gesicht langsam, leise)
    f0_2, f1_2 = S[1]
    wisch = f0_2 + int((f1_2 - f0_2) * 0.45)
    LE.lea_react(T, l, "traurig", f0_2 + 8, hold=S[2][1] - f0_2 - 2, speaking=True, weg=1.0)
    C.pose(T, l, {"sh_L": (-0.25, -0.1, 0), "sh_R": (-0.25, 0.1, 0)}, f0_2, wisch - 4, 10, 6)      # Haende sinken
    C.pose(T, l, {"sh_R": (-2.45, 0.6, 0.2), "el_R": (-1.9, 0, 0), "hand_R": (0, 0, 0.6)}, wisch - 4, wisch + 12, 5, 8)
    T.add(l.hand["R"], "location", lambda f: (0.04 * math.sin((f - wisch) * 0.35) * window(f, wisch, wisch + 12, 2, 4), 0, 0),
          wisch - 2, wisch + 14)
    BG.mehlstrich_stirn(T, l, wisch + 4)
    C.kalle_look(T, k, lambda f: BS.p(-0.3, 0.2, TZ), S[1][0], S[2][0] + 4, ramp=6)
    C.kalle_traurig(T, k, f0_2 + 10, S[2][1], speaking=False, staerke=0.5)
    cue(f0_2 + 2, "ticken", 0.45)
    cue(f0_2 + 32, "ticken", 0.45)
    LF = L_BS + V(0, -0.22, 1.86)
    A2 = (L_BS + V(0.35, -2.6, 1.95), LF + V(0.05, 0.2, -0.25), 32.0)
    B2 = (L_BS + V(0.2, -1.65, 1.9), LF + V(0.02, 0, -0.18), 38.0)
    cam.add_shot(f0_2, f1_2, zoom_gesicht(f0_2, f1_2, A2, B2, ease=ease_in_out))

    # =================================================================== SZENE 3 (Kalle verlegen, schwenk Kalle -> Lea)
    f0_3, f1_3 = S[2]
    setze(k, f0_3, S[3][0], K_BS, -0.25)
    C.kalle_react(T, k, "traurig", f0_3 + 6, hold=f1_3 - f0_3 - 4, speaking=True)
    ab = f0_3 + 4
    hatpath = path([(ab, V(0, 0.01, 0.53)), (ab + 10, V(0.1, -0.35, 0.05)), (ab + 18, V(0.0, -0.55, -0.55))], ease_in_out)
    T.set(k.hat, "location", lambda f: hatpath(f) if f < f1_3 else (0, 0.01, 0.53), ab - 1, f1_3 + 1)
    T.set(k.hat, "location", lambda f: (0, 0.01, 0.53), f1_3 + 1, f1_3 + 2)
    T.add(k.hat, "rotation_euler", lambda f: (0.9 * window(f, ab + 8, f1_3, 6, 4), 0, 1.6 * math.sin((f - ab) * 0.12) *
                                              window(f, ab + 10, f1_3, 6, 4)), ab, f1_3)
    C.pose(T, k, {"sh_R": (-1.1, 0.25, 0.35), "sh_L": (-1.1, -0.25, -0.35), "el_R": (-1.2, 0, 0.3), "el_L": (-1.2, 0, -0.3)},
           ab + 6, f1_3 - 2, 6, 6)
    C.kalle_look(T, k, lambda f: L_BS + V(0, -0.2, 1.9), f0_3 + 6, f1_3, ramp=8)     # sucht zum ersten Mal Leas Blick
    T.add(k.head, "rotation_euler", lambda f: (0, 0, -0.45 * window(f, f0_3 + 4, f1_3, 10, 6)), f0_3, f1_3)
    bp3 = path([(f0_3, BS.p(1.55, 1.9, 2.05)), (f1_3, BS.p(0.75, 1.75, 2.0))], ease_in_out)
    T.set(b.root, "location", lambda f: bp3(f), f0_3, f1_3)
    T.set(b.root, "scale", lambda f: (0.8,) * 3, f0_3, f1_3)
    cue(f0_3 + 20, "ticken", 0.4)
    KF = K_BS + V(0, -0.25, 1.92)
    A3 = (K_BS + V(-0.25, -2.05, 1.95), KF + V(0, 0, -0.2), 36.0)
    B3 = (BS.p(0.05, -2.0, 1.92), LF + V(0.25, 0, -0.25), 36.0)
    cam.add_shot(f0_3, f1_3, schwenk(f0_3 + 6, f1_3, A3, B3))

    # =================================================================== SZENE 4 (Byte filmt, Kalle rollt, rueckfahrt)
    f0_4, f1_4 = S[3]
    setze(k, f0_4, S[4][0], K_BS, 0.0)
    B4 = BS.p(0.85, 0.45, TZ + 0.42)                           # direkt ueber Kalles Haenden (seitlich, Gesicht frei)
    bp4 = path([(f0_4, BS.p(0.75, 1.75, 2.0)), (f0_4 + 14, B4)], ease_in_out)
    T.set(b.root, "location", lambda f: bp4(f), f0_4, f1_4)
    T.set(b.root, "scale", lambda f: (0.8,) * 3, f0_4, f1_4)
    ka = BG.kamera_antenne(coll, "rec_cam", b)
    BG.kamera_ausklappen(T, ka, wd(3, "film") - 4, S[4][0] - 2)
    VP.rec_blink(T, ka.cam, f0_4, S[4][0])
    T.set(k.hat, "location", lambda f: (0, 0.01, 0.53 + 0.25 * (1 - ease_out(clamp01((f - f0_4) / 10)))), f0_4, f0_4 + 12)
    strang = BG.teigstrang(coll, "strang_k", n=16, laenge=0.42)
    strang.root.location = BS.p(0.62, 0.7, TZ)
    roll0 = f0_4 + 16
    LE.haende_rollen(T, k, roll0, S[4][0] + 4)
    BG.teigstrang_form(T, strang, lambda f, u: V(-0.21 + 0.42 * u, 0, 0.022) * (0.75 + 0.25 * clamp01((f - roll0) / 50)),
                       f0_4, S[4][0])
    T.set(strang.root, "scale", lambda f: (1, 1, 1) if S[3][0] <= f < S[4][0] or S[13][0] <= f else (0, 0, 0), 0, N)
    LE.lea_react(T, l, "neutral", wd(3, "langsam"), hold=20)
    T.add(l.head, "rotation_euler", lambda f: (-0.32 * window(f, wd(3, "langsam") - 2, S[4][0] + 2, 10, 4), 0,
                                               -0.3 * window(f, wd(3, "langsam") - 2, S[4][0] + 2, 10, 4)), f0_4, S[4][0] + 2)
    A4 = (BS.p(0.62, -1.3, 1.85), BS.p(0.5, 0.8, 1.35), 34.0)
    B4c = (BS.p(0.25, -3.1, 2.15), BS.p(0.25, 0.9, 1.45), 30.0)
    cam.add_shot(f0_4, f1_4, rueckfahrt(f0_4 + 4, f1_4, A4, B4c))
    cam.whips.append((S[4][0], 1))

    # =================================================================== STUDIO: fuenf Standbilder (Szene 5, 6)
    f0_5, f1_5 = S[4]
    weg(k, f0_5, S[6][0])
    weg(l, f0_5, S[6][0])
    labels = ["Rollen", "Formen", "Schlingen", "Andrücken", "Ablegen"]
    sbs = []
    SBX = [-1.1, -0.55, 0.0, 0.55, 1.1]
    worte5 = [wd(4, "Brezel"), wd(4, "In", 2), wd(4, "fünf"), wd(4, "Schritten"), wd(4, "Zeitlupe")]
    for j, (x, lab) in enumerate(zip(SBX, labels)):
        sb = BG.hand_standbild_3d(coll, f"sb{j}", j + 1, lab, pose=j / 4)
        sb.root.location = ST.p(x, -0.1, 1.15)
        fin = max(f0_5 + 6 + 5 * j, worte5[j] - 6) if j > 0 else f0_5 - 2
        T.set(sb.root, "scale", lambda f, fin=fin: ((0.8 * pop(f, fin, 9) * (unpop(f, S[5][1] - 6, 6) if f > S[5][1] - 6 else 1)),) * 3,
              fin - 1, S[5][1] + 2)
        T.add(sb.root, "rotation_euler", lambda f, j=j: (0, 0, 0.12 * math.sin(f * 0.05 + j)), f0_5, S[5][1])
        cue(fin + 1, "pop", 0.35)
        sbs.append(sb)
    setze_byte(f0_5, S[5][1], ST.p(1.45, -0.6, 2.05), 0.9)
    cue(f0_5 - 3, "whoosh", 0.9)
    SB3 = ST.p(SBX[0], -0.1, 1.15) + V(0, 0, 0.2 * 0.8)
    KA.mehlstaub_schwebend(T, coll, "zl_staub5", SB3 + V(0, -0.35, 0.1), f0_5, S[5][1])
    zl5 = KA.zeitlupe_haende(lambda f: SB3, f0_5, f0_5 + 40, abstand=0.9, hoehe=0.18, seite=0.25, lens=48.0)
    A5 = zl5(f0_5 + 40)
    B5 = (ST.p(0.0, -4.4, 1.9), ST.p(0.0, 0.4, 1.55), 28.0)
    r5 = rueckfahrt(f0_5 + 40, f1_5 - 4, A5, B5)
    cam.add_shot(f0_5, f1_5, lambda f: zl5(f) if f < f0_5 + 40 else r5(f))

    # =================================================================== SZENE 6 (Handgelenk, Bahnen, zeitlupe_haende)
    f0_6, f1_6 = S[5]
    sb3 = sbs[2]
    T.add(sb3.root, "location", lambda f: (0, -0.25 * window(f, f0_6, f1_6, 8, 6), 0.1 * window(f, f0_6, f1_6, 8, 6)), f0_6, f1_6)
    for j, sb in enumerate(sbs):
        if j != 2:
            T.mul(sb.root, "scale", lambda f: ((1 - 0.6 * window(f, f0_6, f1_6, 8, 6)),) * 3, f0_6, f1_6)
    WR = ST.p(0.08, -0.35, 1.45)
    bogen = AR.bogen_punkte(WR + V(0, -0.05, 0.0), 0.16, math.radians(200), math.radians(340), 16, ebene="XZ", hub=-0.04)
    bk = AR.bahn(coll, "bahn_kalle", [p + V(0, 0, 0.12) for p in bogen])
    b_on = wd(5, "Schwung") - 8
    AR.bahn_zeichnen(T, bk, b_on, 18, f1_6 - 4)
    gl = [WR + V(-0.2 + 0.4 * t, -0.05, 0.02) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    bl = AR.bahn(coll, "bahn_lea", gl, farbe="#9A9CAB", glow=False)
    AR.bahn_zeichnen(T, bl, wd(5, "Lea") - 6, 12, f1_6 - 4)
    luft = BG.teigstrang(coll, "strang_luft", n=14, laenge=0.3, r=0.016)
    luft.root.location = WR + V(0, -0.04, 0.12)
    BG.teigstrang_form(T, luft, BG.form_schwung(BG.form_gerade(0.3), lambda f: (f - b_on) / 40, hoehe=0.1, dreh=1.6),
                       f0_6, f1_6)
    T.set(luft.root, "scale", lambda f: (1, 1, 1) if f0_6 <= f < f1_6 else (0, 0, 0), 0, N)
    lab_k = AR.schritt_kreis(coll, "kreis3", 3)
    lab_k.root.location = WR + V(-0.32, -0.02, 0.3)
    AR.einblenden(T, lab_k.root, f0_6 + 4, f1_6 - 6, 0.9)
    setze_byte(f0_6, f1_6, ST.p(-0.7, -0.75, 1.75), 0.75)
    cue(b_on, "ding", 0.25)
    zl6 = KA.zeitlupe_haende(lambda f: WR + V(0, 0, 0.08), f0_6, f1_6, abstand=0.95, hoehe=0.12, seite=0.2, lens=40.0)
    cam.add_shot(f0_6, f1_6, zl6)
    cam.whips.append((S[6][0], -1))

    # =================================================================== SZENE 7 (Kalle staunt ueber seine Hand)
    f0_7, f1_7 = S[6]
    setze(k, f0_7, S[8][0], K_BS, 0.25)
    setze(l, f0_7, S[8][0], L_BS + V(0.25, 0.0, 0), 0.2)
    cue(f0_7 - 3, "whoosh", 0.9)
    C.kalle_react(T, k, "staunen", hl(6), hold=f1_7 - hl(6) - 4, speaking=True)
    C.pose(T, k, {"sh_R": (-1.05, 0.55, 0.2), "el_R": (-0.9, 0, 0)}, f0_7 + 2, f1_7 - 2, 6, 6)
    T.add(k.hand["R"], "rotation_euler", lambda f: (0, 0, 1.2 * math.sin((f - f0_7) * 0.12)), f0_7, f1_7)
    sw7 = wd(6, "einfach") - 4
    T.add(k.hand["R"], "rotation_euler", lambda f: (0, 0.9 * math.sin(math.pi * clamp01((f - sw7) / 12)), 0), sw7, sw7 + 13)
    C.kalle_look(T, k, lambda f: K_BS + V(-0.55, -0.55, 1.35), f0_7, f1_7, ramp=6)
    nach = sw7 + 9                                            # Lea macht den Schwung leise nach
    C.pose(T, l, {"sh_R": (-1.2, 0.3, 0.2), "el_R": (-1.0, 0, 0)}, nach - 6, f1_7 + 4, 6, 6)
    T.add(l.hand["R"], "rotation_euler", lambda f: (0, 0.8 * math.sin(math.pi * clamp01((f - nach) / 14)), 0), nach, nach + 15)
    C.kalle_look(T, l, lambda f: K_BS + V(-0.35, -0.55, 1.55), f0_7, f1_7, ramp=8)
    setze_byte(f0_7, f1_7, BS.p(1.35, 1.6, 2.15), 0.75)
    HAND7 = K_BS + V(-0.55, -0.55, 1.35)
    A7 = (K_BS + V(-0.55, -2.4, 1.75), K_BS + V(-0.12, -0.2, 1.75), 32.0)
    B7 = (K_BS + V(-0.5, -2.05, 1.8), (KF + HAND7) / 2 + V(0, 0, 0.05), 32.0)
    cam.add_shot(f0_7, f1_7, zoom_gesicht(f0_7, f1_7, A7, B7))
    cam.whips.append((S[7][0], 1))

    # =================================================================== SZENE 8 (Eisberg, schwenk nach unten)
    f0_8, f1_8 = S[7]
    eis = BG.eisberg_wissen(coll, "eisberg")
    EIS = ST.p(0.0, -0.4, 1.75)
    eis.root.location = EIS
    T.set(eis.root, "scale", lambda f: (0.9 * pop(f, f0_8 + 2, 10),) * 3 if f0_8 <= f < f1_8 + 2 else (0, 0, 0), 0, N)
    T.add(eis.root, "location", lambda f: (0, 0, 0.03 * math.sin(f * 0.07)), f0_8, f1_8)
    for j, sy in enumerate(eis.symbole):
        T.set(sy, "scale", lambda f, j=j: ((1 + 0.12 * math.sin(f * 0.2 + j)),) * 3, f0_8, f1_8)
    setze_byte(f0_8, f1_8, ST.p(1.15, -0.9, 2.3), 0.8)
    cue(f0_8 - 3, "whoosh", 0.9)
    A8 = (EIS + V(0.1, -3.3, 1.1), EIS + V(0, 0, 0.7), 30.0)
    B8 = (EIS + V(0.0, -3.4, -0.55), EIS + V(0, 0, -0.75), 30.0)
    cam.add_shot(f0_8, f1_8, schwenk(f0_8 + 10, f1_8 - 4, A8, B8))
    cam.whips.append((S[8][0], -1))

    # =================================================================== SZENE 9 (Morgenlicht, Brille, push_in)
    f0_9, f1_9 = S[8]
    L9 = BS.p(-0.1, 1.3, 0)
    setze(l, f0_9, S[12][0], L9, 0.0)
    setze(k, f0_9, S[10][0], L9 + V(0.55, 0.55, 0), -0.2)
    C.pose(T, k, {"sh_R": (-0.5, 0.5, 0.0), "sh_L": (-0.5, -0.5, 0.0), "el_R": (-1.8, 0, 0.6), "el_L": (-1.8, 0, -0.6)},
           f0_9, S[10][0], 6, 6)
    nick = wd(8, "auf") + 4
    T.add(k.head, "rotation_euler", lambda f: (0.18 * math.sin(math.pi * clamp01((f - nick) / 12)), 0, 0), nick, nick + 13)
    cue(f0_9 - 3, "whoosh", 0.9)
    BY9 = L9 + V(0.62, -0.6, 1.7)
    setze_byte(f0_9, f1_9, BY9, 0.85)
    for side, rot in (("R", (-1.3, 0.3, 0.3)), ("L", (-1.3, -0.3, -0.3))):
        C.byte_arm(T, b, side, rot, f0_9 + 2, wd(8, "auf") - 2, ramp=5)
    auf = wd(8, "auf")
    LE.lea_brille(T, l, [(0, "ab"), (auf - 2, "auf"), (S[10][0] + 8, "stirn"), (S[13][0] + 10, "auf"), (N - 6, "ab")],
                  0, N - 1, aufleuchten=(auf + 6,))
    gl9 = L.empty("brille_hand", None, (0, 0, 0), coll)
    L.box("brille_hand_m", (0.3, 0.02, 0.07), L.mat("lea_brillenrand", "#2EE6D6", 0.4, emit="#2EE6D6", strength=2.0), gl9,
          (0, 0, 0), coll)
    T.set(gl9, "location", lambda f: tuple((BY9 + V(-0.18, -0.05, -0.05)).lerp(L9 + V(0, -0.3, 2.0),
                                                                                 ease_in_out(clamp01((f - auf + 12) / 10)))),
          f0_9, f1_9)
    T.set(gl9, "scale", lambda f: (1, 1, 1) if f0_9 + 2 <= f < auf - 2 else (0, 0, 0), 0, N)
    LE.lea_react(T, l, "zweifel", f0_9 + 8, hold=auf - f0_9 - 4)
    LE.lea_react(T, l, "staunen", auf + 6, hold=f1_9 - auf - 6)
    LF9 = L9 + V(0, -0.22, 1.86)
    A9 = (L9 + V(0.2, -3.0, 1.85), LF9 + V(0, 0, -0.3), 32.0)
    cam.add_shot(f0_9, f1_9, push_in(f0_9, f1_9, A9, k=0.18))

    # =================================================================== SZENE 10 (POV mit [AR])
    f0_10, f1_10 = S[9]
    HANDS = L9 + V(0, -0.45, TZ + 0.06)
    KA.pov_kopf_ausblenden(T, l, f0_10, f1_10)
    w_r, w_f, w_s = wd(9, "Rollen"), wd(9, "Formen"), wd(9, "Schwung")
    LE.haende_rollen(T, l, f0_10, w_f - 2, amp=0.12)
    LE.haende_schlingen(T, l, w_f - 2, f1_10 + 4, zeit=lambda f: clamp01((f - (w_f - 2)) / max(1, f1_10 - w_f)))
    for side in ("R", "L"):                                     # Hand zittert beim ersten Schritt, wird dann ruhig
        T.add(l.hand[side], "rotation_euler", lambda f: (0.06 * math.sin(f * 2.3) * (1 - clamp01((f - f0_10) / 30)), 0,
                                                          0.05 * math.sin(f * 2.9) * (1 - clamp01((f - f0_10) / 30))),
              f0_10, f0_10 + 31)
    st10 = BG.teigstrang(coll, "strang_lea", n=18, laenge=0.46)
    st10.root.location = HANDS + V(0, 0.05, -0.1)
    gerade = BG.form_gerade(0.46)
    brezel = BG.form_brezel(1.15, 0.03)
    schwung = BG.form_schwung(gerade, lambda f: (f - w_s + 6) / 22, hoehe=0.16, dreh=1.4)
    BG.teigstrang_form(T, st10, lambda f, u: (gerade(f, u) if f < w_s - 6 else
                                               schwung(f, u).lerp(brezel(f, u), ease_in_out(clamp01((f - w_s - 4) / 14)))),
                       f0_10, f1_10 + 2)
    T.set(st10.root, "scale", lambda f: (1, 1, 1) if f0_10 <= f < f1_10 else (0, 0, 0), 0, N)
    # Holo-Haende ueber den echten Haenden (machen die Bewegung vor)
    for side, dx in (("R", 0.17), ("L", -0.17)):
        hh = AR.holo_haende(coll, f"holo_{side}", side, 0.75)
        AR.holo_bewegen(T, hh, lambda f, dx=dx: HANDS + V(dx * (1 - 0.6 * clamp01((f - w_f) / 12)) +
                                                          0.05 * math.sin((f - f0_10) * 0.25) * (f < w_f), -0.02,
                                                          0.3 + 0.08 * math.sin(math.pi * clamp01((f - w_s + 10) / 18))),
                        lambda f, dx=dx: (math.radians(75), 0.9 * math.sin(math.pi * clamp01((f - w_s + 10) / 18)) *
                                          (1 if dx > 0 else -1), 0), f0_10, f1_10, f_in=f0_10 + 2, f_out=f1_10 - 6)
    for n, (x, f_in) in enumerate([(0.28, w_r - 2), (0.0, w_f - 2), (-0.28, w_s - 2)], start=1):
        kr = AR.schritt_kreis(coll, f"ar_kreis{n}", n, r=0.06)
        kr.root.location = HANDS + V(x, -0.42, 0.18)
        kr.root.rotation_euler = (math.radians(-55), 0, math.pi)
        AR.einblenden(T, kr.root, f_in, f1_10 - 4, 1.0)
    pf = AR.pfeil(coll, "ar_pfeil", 0.2, 0.05)
    pf.root.location = HANDS + V(-0.12, -0.3, 0.14)
    pf.root.rotation_euler = (math.radians(-55), 0, math.pi)
    AR.einblenden(T, pf.root, w_f, f1_10 - 4)
    bogen10 = AR.bogen_punkte(HANDS + V(0.08, -0.02, 0.12), 0.17, math.radians(200), math.radians(340), 16, hub=0.06)
    b10 = AR.bahn(coll, "ar_bogen", bogen10, r=0.007)
    AR.bahn_zeichnen(T, b10, w_s - 6, 12, f1_10 - 4)
    cue(w_s + 2, "ding", 0.6)
    setze_byte(f0_10, f1_10, L9 + V(0.85, -1.35, 2.15), 0.7)
    pov10 = KA.pov(T, l, f0_10, lambda f: HANDS, augen=1.98, lens=22.0, amp=0.8, blick_vor=0.25)
    cam.add_shot(f0_10, f1_10, pov10)

    # =================================================================== SZENE 11 (perfekt!, rueckfahrt)
    f0_11, f1_11 = S[10]
    blech11 = BG.brezel_roh_perfekt(coll, "perfekt", 1.05)
    pod = BG.siegerpodest_mini(coll, "podest")
    POD = L9 + V(0.05, -0.85, TZ)
    pod.root.location = POD
    T.set(pod.root, "scale", lambda f: (1, 1, 1) if S[10][0] - 2 <= f < S[12][0] or f >= S[13][0] else (0, 0, 0), 0, N)
    blech11.root.location = POD + V(0, 0, 0.1)
    T.set(blech11.root, "scale", lambda f: ((pop(f, f0_11, 8)),) * 3 if f0_11 <= f < S[12][0] else (0, 0, 0), 0, N)
    LE.lea_react(T, l, "jubel", hl(10), hold=f1_11 - hl(10) - 2, speaking=True)
    C.pose(T, l, {"sh_R": (-2.3, 0.75, 0.3), "sh_L": (-2.3, -0.75, -0.3), "el_R": (-2.0, 0, 0.4), "el_L": (-2.0, 0, -0.4)},
           wd(10, "perfekt") + 6, f1_11 - 2, 5, 6)                   # Haende vor den Mund
    setze_byte(f0_11, f1_11, L9 + V(0.75, -0.6, 1.85), 0.8)
    cue(wd(10, "perfekt") + 2, "ding", 0.7)
    A11 = (L9 + V(0.1, -1.7, 1.7), POD + V(0, 0.2, 0.45), 34.0)
    B11 = (L9 + V(-0.2, -3.4, 2.1), L9 + V(0, -0.3, 1.45), 30.0)
    cam.add_shot(f0_11, f1_11, rueckfahrt(f0_11 + 6, f1_11, A11, B11))

    # =================================================================== SZENE 12 (Kalle geruehrt, erster Mehlfleck)
    f0_12, f1_12 = S[11]
    K12 = L9 + V(0.6, 0.05, 0)
    setze(k, f0_12, S[12][0], K12, -0.35)
    C.kalle_react(T, k, "geruehrt", f0_12 + 8, hold=f1_12 - f0_12 - 6, speaking=True)
    C.kalle_look(T, k, lambda f: POD + V(0, 0, 0.12) if f < f0_12 + int(0.55 * (f1_12 - f0_12)) else L9 + V(0, -0.2, 1.88),
                 f0_12, f1_12, ramp=8)
    hand12 = f0_12 + int(0.55 * (f1_12 - f0_12))
    C.pose(T, k, {"sh_R": (-1.75, 1.0, 0.25), "el_R": (-0.55, 0, 0)}, hand12 - 8, S[12][0] + 2, 8, 4)   # Hand auf die Schulter
    BG.mehl_puder(T, coll, "s12puder", L9 + V(0.25, -0.05, 1.62), hand12, 10, 1201)
    BG.mehlfleck_schuerze(T, l, hand12 + 2)
    LE.lea_react(T, l, "geruehrt", hand12 + 4, hold=f1_12 - hand12 - 2)
    C.kalle_look(T, l, lambda f: L9 + V(0.09, -0.27, 1.12) if f < hand12 + 14 else K12 + V(0, -0.2, 1.95),
                 hand12, f1_12, ramp=6)
    T.add(l.head, "rotation_euler", lambda f: (0.3 * window(f, hand12, hand12 + 16, 4, 6), 0,
                                               -0.3 * window(f, hand12 + 14, f1_12, 6, 4)), hand12, f1_12)
    for q in range(max(1, (f1_12 - f0_12) // 60)):
        cue(f0_12 + 4 + q * 60, "knistern", 0.35)
    setze_byte(f0_12, f1_12, BS.p(1.4, 1.8, 2.1), 0.75)
    A12 = ((K12 + L9) / 2 + V(0.15, -2.6, 1.85), (K12 + L9) / 2 + V(0.0, 0, 1.7), 32.0)
    B12 = ((K12 + L9) / 2 + V(0.1, -1.9, 1.85), (K12 + L9) / 2 + V(0.05, 0, 1.75), 36.0)
    cam.add_shot(f0_12, f1_12, zoom_gesicht(f0_12, f1_12, A12, B12, ease=ease_in_out))

    # =================================================================== SZENE 13 (Theke: durchs Fenster, dann innen)
    f0_13, f1_13 = S[12]
    innen = f0_13 + int(0.52 * (f1_13 - f0_13))
    sf = KA.schaufenster(coll, TH)
    KA.schaufenster_zeigen(T, sf, f0_13 - 16, innen)
    ausl = BG.auslage_theke(coll, "auslage")
    ausl.root.location = TH.p(-0.3, -3.6, 0)
    T.set(ausl.root, "scale", lambda f: (1, 1, 1) if f0_13 - 16 <= f < f1_13 + 2 else (0, 0, 0), 0, N)
    geb = BG.brezel_gebacken(coll, "gebacken", 1.5)
    geb.root.location = ausl.root.location + V(0.35, -0.05, 0.73)
    BG.salz_glitzern(T, geb, f0_13, f1_13)
    nimmt = f0_13 + int(0.4 * (f1_13 - f0_13))
    T.set(geb.root, "scale", lambda f: (1, 1, 1) if f0_13 - 16 <= f < nimmt else (0, 0, 0), 0, N)
    sch = BG.schildchen_handschrift(coll, "von_lea", "VON LEA")
    sch.root.location = ausl.root.location + V(0.05, -0.2, 0.73)
    sch.root.scale = (1.5, 1.5, 1.5)
    T.set(sch.root, "scale", lambda f: (1, 1, 1) if f0_13 - 16 <= f < f1_13 + 2 else (0, 0, 0), 0, N)
    kundin = PR.customer(coll, "kundin", "#C0566B", s=3.4)
    kp_t = path([(0.0, TH.p(-2.4, -2.9, 0)), (1.0, TH.p(-0.75, -2.85, 0))], ease_out)
    PR.customer_walk(T, kundin, kp_t, f0_13 - 16, nimmt + 14, f0_13 + 10)
    kp_weg = path([(nimmt + 14, TH.p(-0.75, -2.85, 0)), (f1_13, TH.p(-2.8, -3.2, 0))], ease_in_out)
    T.set(kundin.root, "location", lambda f: kp_weg(f), nimmt + 14, f1_13)
    T.set(kundin.root, "rotation_euler", lambda f: (0, 0, 1.2), nimmt + 14, f1_13)

    def kp(f):
        return kp_t(1.0) if f < nimmt + 14 else kp_weg(f)
    T.set(kundin.root, "scale", lambda f: (3.4,) * 3 if f0_13 - 16 <= f < f1_13 + 2 else (0, 0, 0), 0, N)
    tuete = BG.papiertuete(coll, "tuete")
    tp = path([(nimmt, TH.p(-0.05, -0.4, TH.top_z)), (nimmt + 14, TH.p(-0.45, -2.5, 1.0)), (f1_13, TH.p(-2.4, -3.0, 1.0))],
              ease_in_out)
    T.set(tuete.root, "location", lambda f: tp(f), nimmt, f1_13)
    T.set(tuete.root, "scale", lambda f: (1, 1, 1) if nimmt <= f < f1_13 + 2 else (0, 0, 0), 0, N)
    setze(k, f0_13, S[13][0], TH.p(0.0, 0.25, 0), 0.0)
    C.pose(T, k, {"sh_R": (-1.3, 0.1, 0.25), "el_R": (-0.25, 0, 0)}, nimmt - 6, nimmt + 16, 6, 6)    # reicht die Tuete
    LT = TH.p(0.95, 2.05, 0)                                  # Lea in der Tuer zur Backstube
    setze(l, f0_13, S[13][0], LT, 0.3)
    LE.lea_react(T, l, "geruehrt", innen + 6, hold=f1_13 - innen - 6, speaking=True)
    C.kalle_look(T, l, lambda f: V(kp(f)) + V(0, 0, 1.9), innen, f1_13, ramp=8)
    setze_byte(f0_13, f1_13, LT + V(0.55, -0.25, 1.85), 0.75)
    cue(f0_13 + 8, "tuerglocke", 0.55)
    cue(nimmt + 6, "rascheln", 0.6)
    fen = KA.durchs_fenster(sf, f0_13, innen, ziel=TH.p(-0.05, -3.4, 0.9), abstand=0.8, hoehe=1.3, lens=32.0, schwenk=0.15)
    LF13 = LT + V(0, -0.22, 1.86)
    A13 = (LT + V(-0.55, -2.6, 1.9), LF13 + V(0, 0, -0.35), 34.0)
    pin13 = push_in(innen, f1_13, A13, k=0.3)
    cam.add_shot(f0_13, f1_13, lambda f: fen(f) if f < innen else pin13(f))
    cam.whips.append((S[13][0], 1))

    # =================================================================== SZENE 14 (Team, Loop)
    f0_14, f1_14 = S[13]
    setze(k, f0_14, N, K_BS, 0.0)
    setze(l, f0_14, N, L_BS, 0.0)
    cue(f0_14 - 3, "whoosh", 0.8)
    C.pose(T, k, {"sh_R": (-0.9, 0.3, 0.3), "el_R": (-1.8, 0, 0), "sh_L": (-0.9, -0.3, -0.3), "el_L": (-1.8, 0, 0)},
           f0_14 + 2, f0_14 + 20, 4, 6)                     # Aermel hochkrempeln
    stollen = L.empty("stollenteig", None, (0, 0, 0), coll)
    L.box("stollenteig_m", (0.42, 0.26, 0.12), L.mat("bg_teig", "#EBCB9C", 0.75), stollen, (0, 0, 0.06), coll, bevel=0.05, seg=2)
    sp14 = path([(f0_14 + 18, K_BS + V(-0.2, -0.75, TZ)), (f0_14 + 36, L_BS + V(0.3, -0.75, TZ))], ease_in_out)
    T.set(stollen, "location", lambda f: sp14(f), f0_14, N)
    T.set(stollen, "scale", lambda f: (1, 1, 1) if f0_14 <= f < N - 4 else (0, 0, 0), 0, N)
    C.pose(T, k, {"sh_L": (-0.9, -0.2, -0.3), "el_L": (-0.4, 0, 0)}, f0_14 + 16, f0_14 + 40, 5, 8)
    C.kalle_react(T, k, "jubel", hl(13), hold=20, speaking=True, hat=False)
    LE.lea_react(T, l, "jubel", f0_14 + 26, hold=24)
    ka2 = BG.kamera_antenne(coll, "rec_cam2", b)
    BG.kamera_ausklappen(T, ka2, f0_14 + 10, N - 10)
    VP.rec_blink(T, ka2.cam, f0_14, N - 1)
    setze_byte(f0_14, N, BS.p(1.55, 1.9, 2.05), 0.8)
    for j in range(4):
        ts = BG.teigstrang(coll, f"reihe2_{j}", n=10, laenge=0.3)
        ts.root.location = BS.p(-0.9 + 0.5 * j, 0.25, TZ)
        T.set(ts.root, "scale", lambda f: (1, 1, 1) if f >= f0_14 else (0, 0, 0), 0, N)
    # Loop: Lea haelt am Ende wieder die zehnte Brezel hoch, Kamera endet in der Startposition von Szene 1
    C.pose(T, l, {"sh_L": (-1.75, -0.95, 0.0), "el_L": (-0.25, 0, 0), "hips": (0.04, 0, 0)}, N - 14, N + 10, 8, 1, settle=False)
    cam.add_shot(f0_14, N, fahrt(f0_14, N - 3, (BS.p(0.1, -2.6, 2.1), BS.p(0.1, 1.0, 1.5), 32.0), shot1(0)))

    # ------------------------------------------------------------ Bytes Display-Augen
    eyes = ["schock", "traurig", "neutral", "neutral", "staunen", "staunen", "jubel", "neutral", "jubel", "jubel",
            "jubel", "geruehrt", "geruehrt", "jubel"]
    sched = [(0, "schock")] + [(S[i][0], e) for i, e in enumerate(eyes)]
    C.byte_face(T, b, sched, 0, N - 1)

    def focus(f):
        i = next((j for j, s in enumerate(sc) if s["f0"] <= f < s["f1"]), len(sc) - 1)
        if i == 0:
            return K_BS + V(0, -0.25, 1.8)
        if i == 1:
            return LF
        if i == 2:
            return KF if f < f0_3 + 20 else LF
        if i in (4, 5):
            return V(cam.state(f)[3])
        if i == 6:
            return KF
        if i == 8:
            return LF9
        if i == 9:
            return HANDS
        if i == 11:
            return (K12 + L9) / 2 + V(0, -0.2, 1.85)
        if i == 12:
            return LF13 if f >= innen else geb.root.location
        return V(cam.state(f)[3])
    W.cam.focus_fn = focus
