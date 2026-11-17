"""Regie fuer 'Byte schickt drei Helfer los'. Alle Aktionen haengen an den Wort-Zeitstempeln
(Beat = Wortbeginn - 3 Frames). Szenen-Indizes 0..8 entsprechen Szene 1..9."""
import math
import random

from mathutils import Vector

import characters as C
import look as L
import props as PR
from anim import (ease_in, ease_out, ease_in_out, ease_out_back, ease_in_back, spring, tween, window, pop,
                  unpop, lerp, impact_squash, Noise)
from choreo.common import Ctx, path, pop_obj, hidden, V, PR_pop_life

FPS = 30


def direct(W):
    c = Ctx(W)
    T, k, b, H, N = c.T, c.k, c.b, c.H, c.N
    TH, BU, ST = c.sets["theke"], c.sets["buero"], c.sets["studio"]
    sc = c.sc
    S = [(s["f0"], s["f1"]) for s in sc]
    coll = W.coll

    # ---------------------------------------------------------------- Anker fuer Overlays
    face = L.empty("anchor_kalle_face", k.head, (0, -0.25, 0.28), coll)
    W.anchors["kalle_face"] = face
    W.anchors["byte"] = b.body
    for h in H:
        W.anchors[f"helper{h.n}"] = h.body

    # ---------------------------------------------------------------- Grundbewegung
    C.kalle_idle(T, k, 0, N - 1, seed=7)
    C.byte_idle(T, b, 0, N - 1, seed=3)
    C.byte_blinks(T, b, 0, N - 1, seed=11)
    C.antenna_spring(T, b, 2, N - 1)
    # Sekundaerbewegung: Muetze und Schuerze schwingen nach
    C.follow_through(T, k.hat, k.head, "rotation_euler", 2, 0.9, 3, 0, N - 1)
    C.follow_through(T, k.hat, k.head, "rotation_euler", 0, 0.7, 3, 0, N - 1)
    C.follow_through(T, k.skirt, k.hips, "rotation_euler", 1, 1.2, 4, 0, N - 1)
    C.follow_through(T, k.skirt, k.hips, "rotation_euler", 0, 1.0, 4, 0, N - 1)

    # Positionen pro Set
    K_TH = V(TH.kalle)
    K_BU = V(BU.kalle) + V(0, 0, -0.25)
    K_ST = V(ST.kalle)
    B_TH = TH.p(0.46, -0.22, 2.38)
    TX = 0.13   # Kamera-Zielachse Theke (Kalle auf dem linken Drittel)

    def set_kalle(f0, f1, loc, rz=0.0):
        T.set(k.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(k.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)

    set_kalle(S[0][0], S[0][1], K_TH, 0.0)
    set_kalle(S[1][0], S[2][1], K_BU, 0.45)
    set_kalle(S[3][0], S[6][1], K_ST, -0.28)
    set_kalle(S[7][0], N, K_TH, 0.0)

    # Sprechen
    for i, s in enumerate(sc):
        if s["sprecher"] == "kalle":
            C.kalle_lipsync(T, k, s, s["f0"], s["f1"])
        else:
            C.byte_speak(T, b, s, s["f0"], s["f1"])
            # Kalle hoert zu und schaut Byte an
            C.kalle_look(T, k, lambda f: V(T.loc(b.root, f)) + V(T.loc(b.bob, f)), s["f0"], s["f1"], 0.9)
            for w in s["words"]:
                if w["hl"]:
                    W.cam.punch.append(w["f0"])
    for i, s in enumerate(sc):
        if s["sprecher"] == "kalle":
            for w in s["words"]:
                if w["hl"]:
                    W.cam.punch.append(w["f0"])

    # Byte-Gesicht (Pixel-Ausdruecke)
    face_sched = [(0, "serious"),
                  (S[1][0] + 10, "curious"), (S[2][0], "neutral"), (c.word(2, "Helfer"), "happy"),
                  (c.word(2, "Senden"), "wink"), (c.word(2, "Senden") + 18, "happy"),
                  (S[3][0], "neutral"), (c.word(3, "18"), "serious"), (c.word(3, "15,50"), "happy"),
                  (S[4][0], "happy"), (c.word(4, "150"), "surprised"), (c.word(4, "150") + 25, "happy"),
                  (S[5][0], "neutral"), (c.word(5, "Probelieferung"), "happy"),
                  (S[6][0], "neutral"), (c.word(6, "1.800"), "happy"),
                  (S[7][0], "neutral"), (c.word(7, "Des"), "happy"),
                  (S[8][0] + 6, "neutral"), (c.word(8, "150"), "surprised"), (N - 30, "serious")]
    C.byte_face(T, b, face_sched, 0, N - 1)

    # Helfer standardmaessig unsichtbar
    for h in H:
        T.set(h.root, "scale", lambda f: (0, 0, 0), 0, 1)
        C.byte_idle(T, h, 0, N - 1, seed=20 + h.n, amp=0.025)
        C.antenna_spring(T, h, 2, N - 1, gain=5.0)
        C.byte_face(T, h, [(0, "neutral")], 0, N - 1)
        C.byte_blinks(T, h, 0, N - 1, seed=40 + h.n)

    # Licht-Grundpegel aller Sets merken
    for st in (TH, BU, ST):
        for lt in st.lights:
            lt["base_e"] = lt.data.energy

    cam = W.cam
    G = {}
    B_BU = BU.p(0.05, 0.5, 2.02)
    B_ST = ST.p(0.34, -0.95, 2.1)
    xs = [0.0, 0.62, 1.24]
    plat_z = 2.1
    m_plat = L.mat("platform", L.NAVY2, 0.5)
    m_prim = L.mat("platform_rim", L.TURQ, 0.5, emit=L.TURQ, strength=2.0)
    clear6 = S[5][0]     # Studio-Requisiten verschwinden zu Beginn von Szene 6
    h1, h2, h3 = H
    sacks4 = []
    B6 = ST.p(0.2, -0.95, 2.1)

    def _szene1():
        # ================================================================ SZENE 1 – Theke
        i = 0
        f0, f1 = S[i]
        A_pos, A_tgt, A_lens = TH.p(TX + 0.12, -3.75, 2.32), TH.p(TX, 0.2, 1.93), 35.0
        B_pos, B_tgt, B_lens = TH.p(TX + 0.06, -3.25, 2.12), TH.p(TX, 0.2, 1.98), 50.0

        def shot1(f):
            t = ease_out((f - f0) / (f1 - f0))
            return (A_pos.lerp(B_pos, t), A_tgt.lerp(B_tgt, t), lerp(A_lens, B_lens, t))
        G['shot1'] = shot1
        cam.add_shot(f0, f1, shot1)
        cam.whips.append((f1, 1))
        c.cue(f1 - 5, "whoosh", 0.9)

        # Kalle wischt die Theke (Frame 1 schon in Bewegung)
        wipe_env = C.pose(T, k, "wipe", -20, None, 1, 1, settle=False)
        wipe_end = c.word(0, "150") - 8
        T.add(k.sh["R"], "rotation_euler", lambda f: (0.12 * math.sin(f * 0.38), 0, 0.3 * math.sin(f * 0.38 + 1.2)), 0, N - 1)
        # Wischen endet vor dem Sack (Arm zur Ruhe) – und beginnt wieder am Ende (Loop)
        loop_start = N - 40

        def wipe_w(f):
            if f < wipe_end:
                return 1.0
            if f < loop_start:
                return 1 - ease_in_out((f - wipe_end) / 10)
            return ease_in_out((f - loop_start) / 30)
        # Wisch-Pose nur in der Theke (Szene 1 und Loop-Ende): Gewicht ueber Faktor-Layer
        for jn, rot in C.POSES["wipe"].items():
            j = C.joint(k, jn)
            T.add(j, "rotation_euler", lambda f, rot=rot: tuple(r * (wipe_w(f) - 1) for r in rot), 0, N - 1)
        T.add(k.sh["R"], "rotation_euler", lambda f: tuple(v * (wipe_w(f) - 1) for v in
                                                           (0.12 * math.sin(f * 0.38), 0, 0.3 * math.sin(f * 0.38 + 1.2))),
              0, N - 1)
        T.set(k.cloth, "scale", lambda f: (1, 1, 1) if f < wipe_end + 4 else (max(0.0, 1 - (f - wipe_end - 4) / 4),) * 3,
              0, wipe_end + 9)
        T.set(k.cloth, "scale", lambda f: (pop(f, loop_start + 6, 8),) * 3, loop_start, loop_start + 16)

        # Byte rechts neben Kalle; Beat 'Kalle': Drehung + Lichtspur
        T.set(b.root, "location", lambda f: tuple(B_TH), f0, f1)
        bk = c.beat(0, "Kalle")
        spin0 = bk
        T.add(b.body, "rotation_euler", lambda f: (0, 0, 2 * math.pi * ease_in_out((f - spin0) / 14)), spin0, spin0 + 14)
        T.mul(b.body, "scale", lambda f: (1 + 0.08 * window(f, spin0, spin0 + 14, 4, 8), 1, 1 - 0.06 * window(f, spin0, spin0 + 14, 4, 8)),
              spin0, spin0 + 14)
        c.cue(spin0, "whoosh", 0.8)

        def spin_trail(f):
            a = 2 * math.pi * ease_in_out((f - spin0) / 14)
            return tuple(V(B_TH) + V(0.3 * math.cos(a + 1.5), 0.3 * math.sin(a + 1.5) * 0.5 - 0.05, 0.02))
        C.trail(T, coll, "s1trail", spin_trail, spin0, spin0 + 16, n=8, size=0.05)
        # Kalle schaut hoch, Augen folgen Byte
        T.add(k.head, "rotation_euler", lambda f: (-0.12 * window(f, bk + 2, wipe_end + 30, 5, 10), 0,
                                                   0.12 * window(f, bk + 2, wipe_end + 30, 5, 10)), bk + 2, wipe_end + 30)

        # Beat '150': Mehlsack faellt auf die Theke
        hit = c.word(0, "150")
        sack = PR.flour_sack(coll, "s1_sack", label=True, scale=1.0)
        sack_pos = TH.p(TX - 0.5, -0.45, TH.top_z)
        T.set(sack.root, "location", lambda f: tuple(sack_pos + V(0, 0, 3.2 * (1 - ease_in((f - (hit - 9)) / 9)) if f < hit else 0)),
              hit - 10, hit)
        T.set(sack.root, "scale", lambda f: (1, 1, 1) if f >= hit - 10 else (0, 0, 0), hit - 11, hit - 10)
        T.set(sack.root, "scale", lambda f: (unpop(f, f1 - 1, 1),) * 3 if f < f1 + 2 else (0, 0, 0), f1 - 2, f1 + 3)
        T.set(sack.root, "rotation_euler", lambda f: (0, 0.0, -0.25 + 0.15 * (1 - ease_out((f - hit + 9) / 12))), hit - 10, hit + 4)

        def squash_sack(f):
            if f < hit:
                z = 1 + 0.15 * ease_in((f - (hit - 6)) / 6) if f > hit - 6 else 1.0
                return (1 / math.sqrt(z), 1 / math.sqrt(z), z)
            t = (f - hit) / FPS
            sp = spring(t, 3.2, 0.3)
            return (1 + 0.2 * sp, 1 + 0.2 * sp, 1 - 0.2 * sp)   # 80 % Hoehe / 120 % Breite beim Aufprall
        T.set(sack.body, "scale", squash_sack, hit - 8, hit + 25)
        PR.burst(T, coll, "s1_flour", "puff", tuple(sack_pos + V(0, 0, 0.05)), hit, 22, 101, speed=(1.2, 2.0), up=0.15,
                 gravity=-0.6, life=(16, 26), size=(0.8, 1.6), drag=3.5, ring=True)
        PR.burst(T, coll, "s1_dust", "dust", tuple(sack_pos + V(0, 0, 0.2)), hit, 14, 102, speed=(0.6, 1.4), up=1.0,
                 gravity=-0.8, life=(20, 34), size=(0.8, 1.4), drag=1.5)
        for ri, rp in enumerate(TH.objs["rolls"]):
            T.add(rp, "location", lambda f, ri=ri: (0, 0, 0.09 * max(0.0, math.sin(math.pi * (f - hit - 2 - 2 * ri) / 8))
                                                    if 0 <= f - hit - 2 - 2 * ri <= 8 else 0), hit, hit + 22)
            T.add(rp, "rotation_euler", lambda f, ri=ri: (0.3 * window(f, hit + 2 + 2 * ri, hit + 14 + 2 * ri, 3, 6), 0, 0),
                  hit, hit + 24)
        cam.shakes.append((hit, 0.025, 8))
        c.cue(hit, "pop", 1.0)

        # Beat 'zu viel': rotes Preisschild an der Schnur (haengt an Byte), pendelt 3x gedaempft
        zv = c.word(0, "zu viel")
        tag1 = PR.price_tag(coll, "s1_tag", "150 € zu viel", good=False, mode="string", width=0.56)
        T.set(tag1.root, "location", lambda f: tuple(V(T.loc(b.root, f)) + V(T.loc(b.bob, f)) + V(-0.03, -0.08, -0.17)),
              f0, f1)
        T.set(tag1.root, "scale", lambda f: (PR_pop_life(f, zv - 3, f1 - 6, 5, 6),) * 3, zv - 4, f1)

        def swing(f):
            if f < zv - 3:
                return (math.radians(-95), 0, 0)
            t = (f - (zv - 3)) / FPS
            return (math.radians(-95) * spring(t, 1.25, 0.16), 0, 0.08 * math.sin(t * 5) * math.exp(-t * 2))
        T.set(tag1.piv, "rotation_euler", swing, zv - 4, f1)
        c.cue(zv, "buzz", 1.0)
        C.kalle_react(T, k, "zweifel", zv + 6, hold=f1 - zv - 4)
        W.anchors["tag1"] = tag1.body

        # Hook-Overlay wird in overlays.py gezeichnet; Mehlstaub im Gegenlicht (Theke, ganze Laufzeit)
        PR.ambient_motes(T, coll, "th_motes", TH.p(0.6, 1.2, 2.2), (2.2, 1.2, 1.1), 40, 7, 0, N - 1, "dust", 0.06)

    _szene1()

    def _szene2():
        # ================================================================ SZENE 2 – Buero
        i = 1
        f0, f1 = S[i]
        cen = BU.p(0.1, 0.15, 1.52)

        def orbit(f, a0, a1, r, z, lens, fa, fb, center=cen):
            t = ease_in_out((f - fa) / (fb - fa))
            a = math.radians(lerp(a0, a1, t))
            pos = center + V(r * math.sin(a), -r * math.cos(a), z - center.z)
            return pos, center, lens
        cam.add_shot(f0, f1, lambda f: orbit(f, -18, 12, 3.1, 1.95, 32, f0, f1))
        # Kalle plumpst auf den Stuhl
        C.pose(T, k, "sit", f0 - 2, S[2][1], 3, 4, settle=False)
        C.pose(T, k, "desk_hands", f0 + 8, c.word(1, "null") - 4, 8, 6)
        drop = f0 + 6
        T.add(k.body, "location", lambda f: (0, 0, 0.45 * (1 - ease_in((f - f0) / 6)) if f < drop else 0), f0, drop + 1)
        T.mul(k.torso, "scale", lambda f: (1 + 0.1 * spring((f - drop) / FPS, 3, 0.3), 1, 1 - 0.1 * spring((f - drop) / FPS, 3, 0.3))
              if f >= drop else (1, 1, 1), drop, drop + 24)
        seat = BU.objs["chair_seat"]
        spinp = BU.objs["chair_spin"]
        T.add(seat, "location", lambda f: (0, 0, -0.07 * spring((f - drop) / FPS, 3.0, 0.25)) if f >= drop else (0, 0, 0),
              drop, drop + 30)
        T.add(spinp, "rotation_euler", lambda f: (0, 0, 0.35 * math.sin(min(1, (f - drop) / 40) * math.pi) * spring((f - drop) / FPS, 0.9, 0.3)
                                                  if f >= drop else 0), drop, drop + 60)
        T.add(k.root, "rotation_euler", lambda f: (0, 0, 0.35 * math.sin(min(1, (f - drop) / 40) * math.pi) * spring((f - drop) / FPS, 0.9, 0.3)
                                                   if f >= drop else 0), drop, drop + 60)
        c.cue(drop, "pop", 0.7)
        # Beat 'drei': Postfach-Symbol springt hoch, Zaehler 1-2-3, drei Umschlaege flattern raus
        d3 = c.word(1, "drei")
        lap = BU.objs["laptop"]
        lap_top = V(lap.root.location) + V(0, 0, 0.45)
        inbox = PR.inbox_icon(coll, "s2_inbox")
        T.set(inbox.root, "location", lambda f: tuple(lap_top + V(-0.05, -0.05, 0.25 * ease_out_back(min(1, (f - d3 + 3) / 8), 2.0)
                                                                  if f >= d3 - 3 else 0)), d3 - 4, d3 + 10)
        T.set(inbox.root, "rotation_euler", lambda f: (0, 0, math.radians(35)), d3 - 4, d3 - 3)
        T.set(inbox.root, "scale", lambda f: (PR_pop_life(f, d3 - 3, f1 - 8, 7, 6) * 0.9,) * 3, d3 - 4, f1)
        for n, dg in enumerate(inbox.digits):
            fa = d3 + 2 + 6 * n
            fb = d3 + 2 + 6 * (n + 1) if n < 2 else f1 + 40
            T.set(dg, "scale", lambda f, fa=fa, fb=fb: (PR_pop_life(f, fa, fb, 5, 1),) * 3, fa - 1, fb + 2)
            T.add(inbox.badge, "rotation_euler", lambda f, fa=fa: (0, 0.35 * window(f, fa, fa + 6, 1, 5), 0), fa, fa + 6)
            c.cue(fa, "pop", 0.8)
        envs = []
        desk_z = BU.p(0, 0, 0.98).z
        stack = [BU.p(0.32, -0.25, 0), BU.p(0.34, -0.26, 0), BU.p(0.30, -0.27, 0)]
        for n in range(3):
            e = PR.envelope(coll, f"s2_env{n}", scale=0.8)
            st = d3 + 20 + 6 * n
            land = st + 14
            tgt = V(stack[n].x, stack[n].y, desk_z + 0.02 + 0.025 * n)
            src = lap_top + V(-0.1, -0.1, -0.1)
            mid = (src + tgt) / 2 + V(-0.15, -0.25, 0.55)
            pf = path([(st, src), (st + 7, mid), (land, tgt)], ease=lambda t: t)
            T.set(e.root, "location", lambda f, pf=pf: pf(f), st - 1, land + 1)
            rz_end = [0.18, -0.12, 0.35][n]
            T.set(e.root, "rotation_euler", lambda f, st=st, land=land, rz_end=rz_end:
                  (math.radians(-90) * ease_out((f - st) / (land - st)) + 0.5 * math.sin((f - st) * 0.9) * (1 - ease_out((f - st) / (land - st))),
                   0.4 * math.sin((f - st) * 0.7) * (1 - (f - st) / (land - st + 1)), rz_end), st - 1, land + 1)
            T.set(e.root, "scale", lambda f, st=st: (0.8 * pop(f, st, 6),) * 3, st - 1, st + 7)
            T.set(e.root, "scale", lambda f: (0.8 * unpop(f, f1 - 2, 2),) * 3 if f < f1 + 1 else (0, 0, 0), f1 - 3, f1 + 2)
            envs.append(e)
        # oberster Umschlag rutscht fast runter und bleibt wackelnd haengen
        top_land = d3 + 20 + 12 + 14
        T.add(envs[2].root, "location", lambda f: (0.16 * ease_out((f - top_land) / 10), -0.1 * ease_out((f - top_land) / 10), 0),
              top_land, f1)
        T.add(envs[2].root, "rotation_euler", lambda f: (0, -0.25 * ease_out((f - top_land) / 10) + 0.12 * math.sin((f - top_land) * 0.8) *
                                                         math.exp(-(f - top_land) / 18), 0), top_land, f1)
        # Beat 'null': Haende hoch, Wanduhr im Zeitraffer, Kratzen unter der Muetze
        nul = c.word(1, "null")
        C.pose(T, k, "hands_up", nul - 4, nul + 14, 5, 8)
        clk = BU.objs["clock"]
        T.add(clk.hands[1], "rotation_euler", lambda f: (0, 2 * math.pi * 3 * ease_in_out((f - nul) / 30), 0), nul, nul + 30)
        T.add(clk.hands[0], "rotation_euler", lambda f: (0, 2 * math.pi * 0.25 * ease_in_out((f - nul) / 30), 0), nul, nul + 30)
        T.add(clk.hands[1], "rotation_euler", lambda f: (0, 2 * math.pi * 3, 0), nul + 30, N - 1)
        T.add(clk.hands[0], "rotation_euler", lambda f: (0, 2 * math.pi * 0.25, 0), nul + 30, N - 1)
        scr = nul + 18
        C.pose(T, k, "scratch", scr, f1 + 6, 6, 6)
        T.add(k.sh["R"], "rotation_euler", lambda f: (0, 0, 0.12 * math.sin((f - scr) * 1.3) * window(f, scr + 4, f1, 3, 3)), scr, f1)
        T.add(k.hat, "rotation_euler", lambda f: (0, -0.22 * ease_out_back(min(1, (f - scr - 4) / 8), 2), 0) if f > scr + 4 else (0, 0, 0),
              scr, S[2][1])
        T.add(k.hat, "location", lambda f: (-0.05 * ease_out((f - scr - 4) / 8), 0, -0.02) if f > scr + 4 else (0, 0, 0), scr, S[2][1])
        C.kalle_react(T, k, "zweifel", c.wordf(1, "Mehl-Angebote") + 2, hold=40, speaking=True)
        # Byte schwebt hinter Kalles Schulter rein, Pixelaugen blinzeln neugierig
        pf_b2 = path([(f0, B_BU + V(1.6, 0.4, 0.9)), (f0 + 30, B_BU + V(0.3, 0.1, 0.25)), (f0 + 50, B_BU)])
        T.set(b.root, "location", pf_b2, f0, f0 + 51)
        T.set(b.root, "location", lambda f: tuple(B_BU), f0 + 51, S[2][0])
        C.trail(T, coll, "s2trail", lambda f: tuple(V(pf_b2(f))), f0, f0 + 40, n=6, size=0.05)
        PR.ambient_motes(T, coll, "bu_motes", BU.p(-1.2, 0.8, 1.9), (1.4, 0.9, 0.9), 26, 8, S[1][0], S[2][1], "dust", 0.05)

    _szene2()

    def _szene3():
        # ================================================================ SZENE 3 – Buero, drei Helfer
        i = 2
        f0, f1 = S[i]
        hw = c.word(2, "Helfer")
        se = c.word(2, "Senden")
        kface_bu = K_BU + V(0, 0, 1.92 - 0.25)
        c3 = BU.p(-0.1, -0.05, 1.68)

        def shot3(f):
            t = ease_in_out((f - f0) / (f1 - 5 - f0))
            pos = BU.p(-0.05, -2.75, 1.85).lerp(BU.p(0.05, -3.6, 2.0), t)
            return pos, (c3 + V(0, 0, -0.23)).lerp(BU.p(-0.05, -0.05, 1.6), t), lerp(50, 28, t)
        cam.add_shot(f0, f1, shot3)
        cam.whips.append((f1, 1))
        c.cue(f1 - 5, "whoosh", 0.9)
        B3 = BU.p(0.17, -0.22, 1.56)
        pf_b3 = path([(f0, B_BU), (f0 + 16, B3 + V(0.1, 0.0, 0.15)), (f0 + 24, B3)])
        T.set(b.root, "location", pf_b3, f0, f0 + 25)
        T.set(b.root, "location", lambda f: tuple(B3), f0 + 25, f1 + 1)
        # Antennenpunkt blinkt immer schneller, Byte zieht sich auf 85 % zusammen
        tip = L.bsdf(b.m_tip).inputs["Emission Strength"]
        T.set(tip, "default_value", lambda f: 2 + 6 * (0.5 + 0.5 * math.sin((max(0, f - f0) ** 1.6) * 0.06)), f0, hw)
        T.mul(b.body, "scale", lambda f: (1 - 0.15 * ease_in((f - (hw - 14)) / 14),) * 3 if f < hw else
              (1 + 0.15 * spring((f - hw) / FPS, 3, 0.3) - 0.15 * (1 - min(1, (f - hw) / 3)),) * 3, hw - 14, hw + 24)
        PR.flash(T, coll, "s3_flash", tuple(B3), hw, 8, 0.45, L.TURQ, 200)
        c.cue(hw, "whoosh", 1.0)
        form = [V(0.05, -0.05, 0.6), V(0.55, -0.05, 0.3), V(0.6, -0.05, -0.28)]
        for n, h in enumerate(H):
            st = hw + n
            sal = hw + 12 + 4 * n
            out = sal + 14
            p_form = B3 + form[n]
            p_far = BU.p(-0.4 + 0.8 * n, 1.2, 3.4)
            pf = path([(st, B3), (st + 9, p_form + V(0, 0, 0.06)), (sal, p_form), (out, p_form + V(0.0, -0.05, 0.08)),
                       (f1 + 2, p_far)])
            T.set(h.root, "location", pf, st - 1, f1 + 3)
            T.set(h.root, "scale", lambda f, st=st: (0.45 * pop(f, st, 8, 1.15),) * 3, st - 1, st + 9)
            T.set(h.root, "scale", lambda f: (0.45 * unpop(f, f1 - 3, 3),) * 3 if f < f1 + 1 else (0, 0, 0), f1 - 4, f1 + 2)
            # Salutieren nacheinander (4 Frames versetzt)
            T.add(h.body, "rotation_euler", lambda f, sal=sal: (0, 0.5 * window(f, sal, sal + 10, 3, 6), 0.3 * window(f, sal, sal + 10, 3, 6)),
                  sal, sal + 10)
            T.add(h.bob, "location", lambda f, sal=sal: (0, 0, 0.06 * window(f, sal, sal + 10, 3, 6)), sal, sal + 10)
            C.trail(T, coll, f"s3trail{n}", lambda f, pf=pf: pf(f), st, st + 12, n=5, size=0.035)
            C.trail(T, coll, f"s3trailB{n}", lambda f, pf=pf: pf(f), out, f1, n=5, size=0.035)
        # Beat 'Senden': Hologramm-Knopf vor Kalle
        holo = PR.send_button(coll, "s3_holo", r=0.13, holo=True)
        hp = BU.p(-0.45, -0.75, 1.2)
        T.set(holo.root, "location", lambda f: tuple(hp), se - 3, se - 2)
        T.set(holo.root, "rotation_euler", lambda f: (math.radians(70), 0, 0.3), se - 3, se - 2)
        T.set(holo.root, "scale", lambda f: (PR_pop_life(f, se - 3, f1 - 6, 7, 5),) * 3, se - 4, f1)
        capm = L.bsdf(holo.mat).inputs["Emission Strength"]
        T.set(capm, "default_value", lambda f: 1.0 + 2.5 * (0.5 + 0.5 * math.sin((f - se) * 0.6)), se - 3, f1)
        c.cue(se, "pop", 0.8)
        # Kalle staunt
        C.kalle_react(T, k, "staunen", hw, hold=f1 - hw - 4)
        PR.burst(T, coll, "s3_bang", "bang", tuple(kface_bu + V(0.05, -0.2, 0.55)), hw + 1, 4, 303, speed=(0.9, 1.3),
                 up=1.2, spread=0.8, gravity=-2.0, life=(16, 22), size=(0.8, 1.1), spin=1.5)

    _szene3()

    def _szene4():
        # ================================================================ SZENE 4 – Studio, Angebote lesen
        i = 3
        f0, f1 = S[i]
        liest = c.word(3, "liest")
        b18 = c.word(3, "18")
        b1550 = c.word(3, "15,50")
        # Studio-Licht faehrt hoch, Screen schaltet ein (Flackern)
        for lt in ST.lights:
            e0 = lt["base_e"]
            if lt.name == "studio_spot":
                continue
            T.set(lt.data, "energy", lambda f, e0=e0: e0 * (0.15 + 0.85 * ease_out((f - f0) / 14)), f0, f0 + 15)
        T.set(ST.screen_strength, "default_value", lambda f: (0.0 if f < f0 + 2 else
                                                              (0.4 + 0.6 * ((f * 7919) % 3 > 0)) if f < f0 + 12 else 1.0),
              f0, f0 + 13)

        def shot4(f):
            t = ease_in_out((f - f0) / (f1 - f0))
            pos = ST.p(0.15, -3.45, 1.75).lerp(ST.p(1.0, -3.1, 1.85), t)
            tgt = ST.p(0.15, 0.3, 2.25).lerp(ST.p(0.9, 0.2, 2.5), t)
            return pos, tgt, 35.0
        cam.add_shot(f0, f1, shot4)
        T.set(b.root, "location", lambda f: tuple(B_ST), f0, S[5][0])
        plats, envs4 = [], []
        for n, x in enumerate(xs):
            pl = L.empty(f"s4_plat{n}", None, ST.p(x, 0.3, plat_z), coll)
            L.cyl(f"s4_platm{n}", 0.3, 0.06, 16, m_plat, pl, (0, 0, -0.03), coll)
            L.torus(f"s4_platr{n}", 0.3, 0.018, 24, 4, m_prim, pl, (0, 0, 0), coll)
            T.set(pl, "scale", lambda f, n=n: (PR_pop_life(f, f0 + 6 + 3 * n, clear6 + 2 * n, 8, 6),) * 3, f0 + 5, clear6 + 10)
            T.add(pl, "location", lambda f, n=n: (0, 0, 0.03 * math.sin(f * 0.07 + n)), f0, clear6 + 10)
            plats.append(pl)
            e = PR.envelope(coll, f"s4_env{n}", scale=0.85)
            ep = ST.p(x, 0.25, 2.82)
            T.set(e.root, "location", lambda f, ep=ep, n=n: tuple(ep + V(0, 0, 0.04 * math.sin(f * 0.11 + n))), f0, liest + 40)
            es = liest + 6 * n
            T.set(e.root, "scale", lambda f, n=n, es=es: (0.85 * PR_pop_life(f, f0 + 10 + 4 * n, es + 16, 8, 5),) * 3, f0 + 9, es + 24)
            # Laschen klappen auf, Papier gleitet raus
            T.set(e.flap, "rotation_euler", lambda f, es=es: (math.radians(-170) * ease_out_back(min(1, max(0, (f - es - 4) / 6)), 1.5), 0, 0),
                  es + 3, es + 11)
            T.set(e.sheet, "location", lambda f, es=es: (0, 0.004, 0.2 * ease_out((f - es - 9) / 6)), es + 8, es + 16)
            envs4.append(e)
            # Scan-Strahl
            beam = L.box(f"s4_scan{n}", (0.42, 0.01, 0.02), L.mat("scanbeam", L.TURQ, 0.4, emit=L.TURQ, strength=6.0, alpha=0.8),
                         None, ep, coll)
            T.set(beam, "location", lambda f, ep=ep, es=es: tuple(ep + V(0, -0.03, 0.16 - 0.32 * ease_in_out((f - es) / 6))), es - 1, es + 7)
            T.set(beam, "scale", lambda f, es=es: (window(f, es, es + 7, 1, 2) * 1.0, 1, 1), es - 1, es + 8)
            # Mehl-Puff -> Sack faellt auf die Plattform (Squash)
            sk = PR.flour_sack(coll, f"s4_sack{n}", label=True, scale=0.72)
            sacks4.append(sk)
            spawn = es + 16
            landf = spawn + 8
            top = ST.p(x, 0.3, plat_z + 0.02)
            T.set(sk.root, "location", lambda f, top=top, spawn=spawn, landf=landf, ep=ep:
                  tuple(V(ep).lerp(top, ease_in((f - spawn) / (landf - spawn)))), spawn - 1, landf)
            T.set(sk.root, "scale", lambda f, spawn=spawn, n=n: (0.72 * PR_pop_life(f, spawn, clear6 + 3 * n, 5, 6),) * 3,
                  spawn - 1, clear6 + 3 * n + 8)
            T.set(sk.body, "scale", lambda f, landf=landf: (lambda xy, z: (xy, xy, z))(*impact_squash(f, landf, 0.2, 3.0)),
                  landf - 5, landf + 25)
            PR.burst(T, coll, f"s4_puff{n}", "puff", tuple(ep), spawn - 1, 10, 400 + n, speed=(0.5, 1.0), up=0.4, gravity=-0.3,
                     life=(12, 18), size=(0.7, 1.2), drag=4.0)
            c.cue(landf, "pop", 0.6)
        # Helfer 1 fliegt zu den Umschlaegen (Scan-Brille)
        for h in H:
            T.set(h.root, "scale", lambda f: (0.45 * pop(f, f0 + 4, 8),) * 3, f0 + 3, f0 + 12)
        p_h1 = path([(f0, ST.p(0.5, -0.2, 3.35)), (liest - 4, ST.p(-0.2, 0.0, 3.2)), (liest, ST.p(0.0, -0.15, 3.12)),
                     (liest + 6, ST.p(0.62, -0.15, 3.12)), (liest + 12, ST.p(1.24, -0.15, 3.12)),
                     (liest + 30, ST.p(1.75, 0.6, 3.3))])
        T.set(h1.root, "location", p_h1, f0, liest + 31)
        T.set(h1.root, "location", lambda f: tuple(ST.p(1.75, 0.6, 3.3)), liest + 31, S[5][0])
        T.set(h2.root, "location", lambda f: tuple(ST.p(1.9, 1.0, 2.7)), f0, S[4][0])
        T.set(h3.root, "location", lambda f: tuple(ST.p(-0.9, 1.2, 3.25)), f0, S[5][0])
        C.trail(T, coll, "s4trail", lambda f: p_h1(f), liest - 4, liest + 20, n=6, size=0.035)
        # Beat '18': rotes Schild klappt am Scharnier auf (180°), Buzz
        tagR = PR.price_tag(coll, "s4_tagred", "18,00 €", good=False, mode="hinge", width=0.58)
        tagG = PR.price_tag(coll, "s4_taggreen", "15,50 €", good=True, mode="hinge", width=0.58)
        for tg, x, bt, fo in ((tagR, xs[0], b18, clear6), (tagG, xs[2], b1550, clear6 + 4)):
            hp_ = ST.p(x, 0.18, 2.9)
            T.set(tg.root, "location", lambda f, hp_=hp_: tuple(hp_), f0, f0 + 1)
            T.set(tg.root, "scale", lambda f, bt=bt, fo=fo: (PR_pop_life(f, bt - 4, fo, 4, 6),) * 3, bt - 5, fo + 8)
            T.set(tg.piv, "rotation_euler", lambda f, bt=bt: (math.radians(180) * (1 - ease_out_back(min(1, max(0, (f - bt + 1) / 7)), 2.2))
                                                           + 0.15 * math.sin((f - bt) * 0.9) * math.exp(-(f - bt) / 10) * (f > bt + 6), 0, 0),
                  bt - 2, bt + 40)
        c.cue(b18, "buzz", 1.0)
        c.cue(b1550, "ding", 1.0)
        PR.burst(T, coll, "s4_sparkle", "spark", tuple(ST.p(xs[2], 0.1, 2.75)), b1550, 16, 404, speed=(0.8, 1.6), up=0.8,
                 gravity=-1.5, life=(14, 22), size=(0.8, 1.3), drag=1.0)
        # mittlerer Sack wird dezent grau
        mid_mat = L.unique_mat(sacks4[1].mat, "sack_mid_gray")
        sacks4[1].mesh.data.materials[0] = mid_mat
        bc = L.bsdf(mid_mat).inputs["Base Color"]
        gray, burl = L.srgb("#8E8A99"), L.srgb(L.BURLAP)
        T.set(bc, "default_value", lambda f: tuple(lerp(burl[j], gray[j], ease_in_out((f - b1550) / 12)) for j in range(4)),
              b1550, b1550 + 12)
        W.anchors["tag18"] = tagR.body
        W.anchors["tag1550"] = tagG.body
        # Kalle: zweifel – beugt sich vor, kneift ein Auge zusammen
        C.pose(T, k, "lean", b18 - 2, S[4][0] - 6, 6, 8)
        C.kalle_react(T, k, "zweifel", b18 + 2, hold=b1550 - b18)
        PR.ambient_motes(T, coll, "st_lights", ST.p(0.3, 1.2, 2.4), (2.6, 1.8, 1.4), 34, 9, S[3][0], S[6][1], "sparkt", 0.08,
                         scale=0.9)

    _szene4()

    def _szene5():
        # ================================================================ SZENE 5 – Ersparnis rechnen
        i = 4
        f0, f1 = S[i]
        b250 = c.word(4, "2,50")
        b60 = c.word(4, "60")
        b150 = c.word(4, "150")
        # mittlerer Sack macht Platz fuer die Muenzsaeule
        T.set(sacks4[1].root, "scale", lambda f: (0.72 * unpop(f, f0 + 2, 6),) * 3, f0 + 1, f0 + 9)
        # Helfer 2 fliegt zwischen die Schilder, Ziffern kreisen schneller
        # Byte steigt in Szene 5 hoeher (Gesicht nicht in der Untertitelzone), in Szene 6 zurueck
        B5 = ST.p(0.3, -0.9, 2.78)
        T.set(b.root, "location", lambda f: tuple(B_ST.lerp(B5, ease_in_out((f - f0) / 14))), f0, f0 + 15)
        T.set(b.root, "location", lambda f: tuple(B5.lerp(B_ST, ease_in_out((f - f1) / 14))), f1, f1 + 15)
        p_h2 = path([(f0, ST.p(1.9, 1.0, 2.7)), (f0 + 18, ST.p(1.0, -0.1, 3.0)), (f0 + 26, ST.p(0.62, -0.15, 2.95))])
        T.set(h2.root, "location", p_h2, f0, f0 + 27)
        T.set(h2.root, "location", lambda f: tuple(ST.p(0.62, -0.15, 2.95)), f0 + 27, S[5][0])
        C.trail(T, coll, "s5trail", lambda f: p_h2(f), f0, f0 + 24, n=6, size=0.035)
        T.set(h2.orbit, "rotation_euler", lambda f: (0, 0, 0.08 * f + (0.0 if f < f0 else 0.25 * (f - f0) * min(1, (f - f0) / 20))),
              0, S[5][0])

        def shot5(f):
            if f < b150 - 4:
                t = ease_in_out((f - f0) / (b150 - 4 - f0))
                pos = ST.p(0.4, -3.4, 2.45).lerp(ST.p(1.0, -3.3, 2.45), t)
                tgt = ST.p(0.55, 1.2, 2.55).lerp(ST.p(0.85, 1.2, 2.55), t)
                return pos, tgt, 32.0
            t = ease_in_out((f - (b150 - 4)) / max(1, f1 - (b150 - 4)))
            pos = ST.p(1.0, -3.3, 2.45).lerp(ST.p(0.35, -3.0, 1.5), min(1, t * 1.6))
            tgt = ST.p(0.85, 1.2, 2.55).lerp(ST.p(-0.3, 0.8, 2.15), min(1, t * 1.6)).lerp(ST.p(-0.3, 0.9, 2.7), ease_in_out(max(0, t * 1.6 - 0.6) / 1.0))
            return pos, tgt, 32.0
        cam.add_shot(f0, f1, shot5)
        # Beat '2,50': Muenzen fallen aus der Luecke, stapeln sich zur Saeule '2,50 €'
        col_base = ST.p(0.62, 0.3, plat_z + 0.01)
        small = []
        for n in range(10):
            cn = PR.coin(coll, f"s5_c{n}")
            small.append(cn)
            st = b250 - 4 + 2 * n
            land = st + 7
            tz = col_base + V(0, 0, 0.018 + 0.032 * n)
            T.set(cn, "location", lambda f, st=st, land=land, tz=tz: tuple(tz + V(0, 0, 1.0 * (1 - ease_in((f - st) / (land - st)))
                                                                                    if f < land else 0)), st - 1, land + 1)
            T.set(cn, "scale", lambda f, st=st, n=n: (PR_pop_life(f, st, clear6 + n // 3, 3, 5),) * 3, st - 1, clear6 + 10)
            T.add(cn, "location", lambda f, land=land: (0, 0, 0.02 * max(0, spring((f - land) / FPS, 4, 0.3)) if f > land else 0),
                  land, land + 12)
            if n == 9:
                T.set(cn, "rotation_euler", lambda f, land=land: (0.25 * math.exp(-(f - land) / 25), 0, (f - land) * 0.5 * math.exp(-(f - land) / 40))
                      if f > land else (0, 0, 0), land, land + 70)
        plq = L.empty("s5_plaque", None, col_base + V(0, -0.28, 0.08), coll)
        L.box("s5_plaquebg", (0.36, 0.02, 0.12), L.mat("plaque", L.NAVY2, 0.5), plq, (0, 0, 0), coll, bevel=0.02)
        L.text("s5_plaquet", "2,50 €", 0.09, L.mat("plaque_t", L.GOLD, 0.4, emit=L.GOLD, strength=1.2), plq, (0, -0.015, 0),
               coll, extrude=0.004, font=L.font())
        T.set(plq, "scale", lambda f: (PR_pop_life(f, b250 + 18, clear6, 7, 5),) * 3, b250 + 17, clear6 + 8)
        c.cue(b250, "pop", 0.9)
        # Beat '60': 60 kleine Saecke als Welle (6 Reihen à 10)
        grid = L.empty("s5_grid", None, ST.p(0.62, 1.55, 2.0), coll)
        grid.rotation_euler = (0.52, 0, 0)
        L.box("s5_gridplat", (2.35, 1.35, 0.05), m_plat, grid, (0, 0, -0.03), coll, bevel=0.02)
        L.box("s5_gridrim", (2.39, 1.39, 0.02), m_prim, grid, (0, 0, -0.05), coll)
        T.set(grid, "scale", lambda f: (PR_pop_life(f, b60 - 10, clear6 + 4, 8, 6),) * 3, b60 - 11, clear6 + 12)
        for r in range(6):
            c.cue(b60 + 4 * r + 6, "pop", 0.55)
            for cc in range(10):
                sk = PR.flour_sack(coll, f"s5_g{r}_{cc}", label=False, scale=0.26)
                st = b60 + 4 * r + 2 * cc
                land = st + 6
                pos = ST.p(0.62 + (cc - 4.5) * 0.215, 1.55 + (r - 2.5) * 0.2 * 0.866, 2.0 + (r - 2.5) * 0.2 * 0.5)
                sk.root.rotation_euler = (0.52, 0, 0)
                T.set(sk.root, "location", lambda f, pos=pos, st=st, land=land: tuple(pos + V(0, 0, 0.9 * (1 - ease_in((f - st) / (land - st)))
                                                                                              if f < land else 0)), st - 1, land + 1)
                T.set(sk.root, "scale", lambda f, st=st, r=r: (0.26 * PR_pop_life(f, st, clear6 + 4 + r, 3, 5),) * 3, st - 1, clear6 + 14)
                T.set(sk.body, "scale", lambda f, land=land: (lambda xy, z: (xy, xy, z))(*impact_squash(f, land, 0.25, 3.5)),
                      land - 4, land + 16)
        W.anchors["grid"] = grid
        # Beat '150': grosse Muenzsaeule waechst, Beschriftung zaehlt mit
        big = L.empty("s5_bigcol", None, ST.p(-0.42, 1.0, 0.0), coll)
        n_big = 40
        for n in range(n_big):
            cn = PR.coin(coll, f"s5_big{n}", big, (0, 0, 0.033 + 0.066 * n))
            cn.scale = (2.3, 2.3, 2.2)
        grow0, grow1 = b150 - 3, b150 + 24
        T.set(big, "scale", lambda f: (1.0 * pop(f, grow0, 5), 1.0 * pop(f, grow0, 5),
                                       max(0.001, ease_out_back(min(1, max(0, (f - grow0) / (grow1 - grow0))), 1.2))) if f < clear6 else
              (unpop(f, clear6 + 2, 6),) * 3, grow0 - 1, clear6 + 10)
        top_anchor = L.empty("s5_bigtop", big, (0, 0, 0.066 * n_big + 0.25), coll)
        W.anchors["col150"] = top_anchor
        W.labels.append({"anchor": "col150", "f0": grow0, "f1": clear6, "count_f0": grow0, "count_f1": grow1,
                         "from": 0, "to": 150, "fmt": "{} €", "dec": 0, "color": "gold", "dy": -70})
        PR.flash(T, coll, "s5_gleam", tuple(ST.p(-0.42, 1.0, 0.066 * n_big + 0.1)), grow1, 9, 0.35, L.YELLOW, 300)
        c.cue(b150, "ding", 1.0)
        C.kalle_react(T, k, "staunen", b150, hold=f1 - b150 - 2)
        C.kalle_look(T, k, lambda f: ST.p(-0.42, 1.0, 0.3 + 2.6 * ease_out((f - grow0) / (grow1 - grow0 + 10))), grow0, f1, 1.0, 4)
        T.add(k.head, "rotation_euler", lambda f: (-0.3 * window(f, grow0, f1 + 4, 10, 8), 0, -0.25 * window(f, grow0, f1 + 4, 10, 8)),
              grow0, f1 + 4)

    _szene5()

    def _szene6():
        # ================================================================ SZENE 6 – Mail schreiben
        i = 5
        f0, f1 = S[i]
        bs = c.word(5, "schreibt")
        bh = c.word(5, "Höflich")
        bp = c.word(5, "Probelieferung")
        scr_c = V(ST.objs["screen"].location)
        pan0 = bp + 10
        T.set(b.root, "location", lambda f: tuple(B_ST.lerp(B6, ease_in_out((f - pan0) / 15))), pan0, pan0 + 16)

        def shot6(f):
            if f < pan0:
                t = ease_in_out((f - f0) / (pan0 - f0))
                pos = ST.p(0.35, -7.4, 2.6).lerp(ST.p(0.35, -5.0, 2.6), t)
                tgt = ST.p(0.35, 3.0, 1.84).lerp(ST.p(0.35, 3.0, 2.07), t)
                return pos, tgt, 35.0
            t = ease_in_out((f - pan0) / (f1 - pan0))
            pos = ST.p(0.35, -5.0, 2.6).lerp(ST.p(-0.2, -3.3, 2.05), t)
            tgt = ST.p(0.35, 3.0, 2.07).lerp(K_ST + V(0.3, 0, 1.8), t)
            return pos, tgt, lerp(35.0, 42.0, t)
        cam.add_shot(f0, f1, shot6)
        kb = PR.keyboard(coll, "s6_kb")
        kbp = ST.p(0.0, 2.2, 2.72)
        T.set(kb.root, "location", lambda f: tuple(kbp + V(0, 0, 0.03 * math.sin(f * 0.09))), f0, S[6][0] + 10)
        T.set(kb.root, "rotation_euler", lambda f: (math.radians(28), 0, 0), f0, f0 + 1)
        T.set(kb.root, "scale", lambda f: (PR_pop_life(f, f0 + 4, S[6][0] + 2, 9, 6),) * 3, f0 + 3, S[6][0] + 10)
        p_h3 = path([(f0, ST.p(-0.9, 1.2, 3.25)), (f0 + 16, ST.p(-0.2, 0.9, 2.2)), (bs - 2, kbp + V(0, -0.05, 0.32))])
        T.set(h3.root, "location", p_h3, f0, bs - 1)
        T.set(h3.root, "location", lambda f: tuple(kbp + V(0.04 * math.sin(f * 0.8), -0.05, 0.32 + 0.03 * abs(math.sin(f * 0.8)))),
              bs - 1, S[6][0])
        C.trail(T, coll, "s6trail", lambda f: p_h3(f), f0, bs - 2, n=6, size=0.035)
        T.set(h1.root, "location", lambda f: tuple(ST.p(1.75, 0.6, 3.3)), f0, S[6][0])
        T.set(h2.root, "location", lambda f: tuple(ST.p(-0.9, 0.8, 3.0)), f0, S[6][0])
        # Tippen: Tasten federn einzeln, leuchten tuerkis, Funken
        r = random.Random(606)
        t_end = bp + 6
        tf = bs
        while tf < t_end:
            ki = r.randrange(len(kb.keys))
            piv, km = kb.keys[ki]
            T.add(piv, "location", lambda f, tf=tf: (0, 0, -0.025 * window(f, tf, tf + 5, 1, 4)), tf, tf + 6)
            T.add(L.bsdf(km).inputs["Emission Strength"], "default_value", lambda f, tf=tf: 3.0 * window(f, tf, tf + 8, 1, 6),
                  tf, tf + 9)
            tf += r.choice([2, 3, 3, 4])
        for n, fs_ in enumerate(range(bs, t_end, 14)):
            PR.burst(T, coll, f"s6_spark{n}", "sparkt", tuple(kbp + V(r.uniform(-0.4, 0.4), 0, 0.08)), fs_, 5, 600 + n,
                     speed=(0.5, 1.0), up=1.0, gravity=-2.0, life=(8, 12), size=(0.7, 1.0))
        # Beat 'Hoeflich': Haken poppt neben der Mail
        chk = L.poly_flat("s6_check", [(-0.18, 0.02), (-0.06, -0.12), (0.2, 0.18), (0.14, 0.24), (-0.06, 0.02), (-0.12, 0.08)],
                          0.05, L.mat("check", L.GREEN, 0.45, emit=L.GREEN, strength=1.5), None, (0, 0, 0), coll)
        chk_p = scr_c + V(1.25, -0.4, -1.15)
        T.set(chk, "location", lambda f: tuple(chk_p + V(0, 0, 0.03 * math.sin(f * 0.1))), f0, S[6][0] + 8)
        T.set(chk, "scale", lambda f: (1.3 * PR_pop_life(f, bh - 2, S[6][0] + 1, 8, 6),) * 3, bh - 3, S[6][0] + 8)
        c.cue(bh, "pop", 0.9)
        # Beat 'Probelieferung': Mini-Mehlsack mit Schleife poppt auf, dreht sich langsam
        mini = PR.flour_sack(coll, "s6_mini", label=True, scale=0.5, bow=True)
        mini_p = scr_c + V(1.25, -0.4, -1.75)
        T.set(mini.root, "location", lambda f: tuple(mini_p), f0, f0 + 1)
        T.set(mini.root, "scale", lambda f: (0.5 * PR_pop_life(f, bp - 2, S[6][0] + 2, 8, 6),) * 3, bp - 3, S[6][0] + 9)
        T.set(mini.root, "rotation_euler", lambda f: (0, 0, 0.04 * (f - bp)), bp - 3, S[6][0] + 9)
        c.cue(bp, "pop", 0.9)
        # Kalle staunt, setzt die Lesebrille auf, nickt zweimal
        C.kalle_react(T, k, "staunen", bs + 6, hold=30)
        gl = PR.reading_glasses(coll, "s6_glasses", k.head, (0, -0.365, 0.34))
        k.glasses = gl
        put = pan0 - 2
        C.pose(T, k, "glasses", put - 10, put + 8, 7, 8)
        T.set(gl, "scale", lambda f: (pop(f, put, 6),) * 3 if f < S[6][0] else (unpop(f, S[6][0] + 4, 5),) * 3, put - 1, S[6][0] + 10)
        T.add(k.head, "rotation_euler", lambda f: (0.16 * max(0, math.sin(math.pi * (f - put - 10) / 9)) if 0 < f - put - 10 < 18 else 0, 0, 0),
              put + 10, put + 30)
        C.kalle_look(T, k, lambda f: scr_c + V(0, 0, -0.2), f0, pan0, 0.8)

    _szene6()

    def _szene7():
        # ================================================================ SZENE 7 – Beschaffung
        i = 6
        f0, f1 = S[i]
        bb = c.word(6, "Beschaffung")
        br = c.word(6, "Richtige")
        b18h = c.word(6, "1.800")
        # Licht dimmt auf einen Spot
        for lt in ST.lights:
            e0 = lt["base_e"]
            if lt.name == "studio_spot":
                T.set(lt.data, "energy", lambda f: 0.0 if f < f0 else 1400 * ease_out((f - f0) / 14) if f < f1 - 4 else 1400 * (1 - (f - f1 + 4) / 4),
                      f0 - 1, f1)
            else:
                T.set(lt.data, "energy", lambda f, e0=e0: e0 * (1 - 0.7 * ease_in_out((f - f0) / 14)), f0, f0 + 15)
        T.set(ST.screen_strength, "default_value", lambda f: 1.0 - 0.45 * ease_in_out((f - f0) / 14), f0, f0 + 15)
        # Helfer fliegen zurueck und verschmelzen mit Byte (Lichtblitz)
        B7 = ST.p(0.3, -0.9, 2.6)
        T.set(b.root, "location", lambda f: tuple(B6.lerp(B7, ease_in_out((f - f0) / 10))), f0, f0 + 11)
        T.set(b.root, "location", lambda f: tuple(B7), f0 + 11, S[7][0])
        merge = f0 + 20
        for n, h in enumerate(H):
            p0 = V(T.loc(h.root, f0))
            pf = path([(f0, p0), (f0 + 10, (p0 + B7) / 2 + V(0, -0.3, 0.4)), (merge, B7)])
            T.set(h.root, "location", pf, f0, merge + 1)
            T.set(h.root, "scale", lambda f: (0.45 * (1 - ease_in((f - merge + 6) / 6)),) * 3 if f < merge else (0, 0, 0), merge - 7, merge + 1)
            C.trail(T, coll, f"s7trail{n}", lambda f, pf=pf: pf(f), f0, merge, n=5, size=0.035)
        PR.flash(T, coll, "s7_flash", tuple(B7), merge, 9, 0.45, L.TURQ, 220)
        T.mul(b.body, "scale", lambda f: (1 + 0.2 * spring((f - merge) / FPS, 3, 0.3),) * 3, merge, merge + 25)
        c.cue(merge, "whoosh", 0.6)
        # Kamera: langsame Kreisfahrt (45°) um die Waage, leicht von unten
        bal_c = ST.p(0.1, 0.45, 2.35)
        cam.add_shot(f0, f1, lambda f: (bal_c + V(4.4 * math.sin(math.radians(lerp(45, 0, ease_in_out((f - f0) / (f1 - f0))))),
                                                  -4.4 * math.cos(math.radians(lerp(45, 0, ease_in_out((f - f0) / (f1 - f0))))),
                                                  1.9 - bal_c.z), bal_c, 30.0))
        cam.whips.append((f1, -1))
        c.cue(f1 - 5, "whoosh", 0.9)
        # Beat 'Richtige': Balkenwaage waechst aus dem Boden
        bal = PR.balance(coll, "s7_bal")
        T.set(bal.root, "location", lambda f: tuple(ST.p(0.75, 0.9, 0.62)), f0, f0 + 1)
        ped = L.cyl("s7_pedestal", 0.42, 0.62, 20, m_plat, None, ST.p(0.75, 0.9, 0.31), coll)
        L.torus("s7_pedrim", 0.42, 0.02, 32, 4, m_prim, ped, (0, 0, 0.31), coll)
        T.set(ped, "scale", lambda f: (PR_pop_life(f, br - 6, f1 - 4, 8, 4),) * 3, br - 7, f1 + 1)
        T.set(bal.root, "scale", lambda f: (1.35 * min(1, pop(f, br - 4, 9)), 1.35 * min(1, pop(f, br - 4, 9)),
                                            1.35 * ease_out_back(min(1, max(0, (f - br + 4) / 12)), 1.4)) if f < f1 - 4 else
              (1.35 * unpop(f, f1 - 3, 3),) * 3, br - 5, f1 + 1)

        def tilt(f):
            if f < br + 8:
                return 0.0
            t = (f - br - 8) / FPS
            return 0.32 * math.sin(2 * math.pi * 0.7 * t + math.pi) * math.exp(-1.1 * t) * (1 if t > 0 else 0) + \
                (-0.22 * window(f, br + 8, br + 18, 5, 5))
        T.set(bal.beam, "rotation_euler", lambda f: (0, tilt(f), 0), br + 7, f1)
        for p_ in bal.pans:
            T.set(p_, "rotation_euler", lambda f: (0, -tilt(f), 0), br + 7, f1)
        bsk = PR.flour_sack(coll, "s7_sack", label=True, scale=0.55)
        bsk.root.parent = bal.pans[0]
        bsk.root.location = (0, 0, -0.6)
        plq = L.empty("s7_qual", bsk.body, (0, -0.2, 0.62), coll)
        L.box("s7_qualbg", (0.62, 0.02, 0.17), L.mat("qualbg", L.GREEN, 0.5, emit=L.GREEN, strength=0.4), plq, (0, 0, 0), coll, bevel=0.03)
        L.text("s7_qualt", "✓ Qualität".replace("✓ ", ""), 0.11, L.mat("tagtext", "#FFFFFF", 0.5), plq, (0.03, -0.015, -0.005), coll,
               extrude=0.004, font=L.font())
        L.poly_flat("s7_qualchk", [(-0.05, 0.0), (-0.02, -0.035), (0.05, 0.04), (0.035, 0.055), (-0.02, -0.005), (-0.035, 0.015)],
                    0.01, L.mat("tagtext", "#FFFFFF", 0.5), plq, (-0.23, -0.02, 0), coll)
        ptag = PR.price_tag(coll, "s7_price", "Preis", good=False, mode="hinge", width=0.42)
        ptag.root.parent = bal.pans[1]
        ptag.root.location = (0, 0, -0.26)
        ptag.root.scale = (0.85,) * 3
        # Beat '1.800': 12 Muenzsaeulen à 150 € fallen nacheinander, '1.800 €' zaehlt hoch
        shelf = L.empty("s7_shelf", None, ST.p(0.75, -0.3, 1.62), coll)
        L.box("s7_shelfm", (1.85, 0.36, 0.05), m_plat, shelf, (0, 0, -0.03), coll, bevel=0.02)
        L.box("s7_shelfr", (1.89, 0.4, 0.02), m_prim, shelf, (0, 0, -0.05), coll)
        T.set(shelf, "scale", lambda f: (PR_pop_life(f, b18h - 12, f1 - 6, 8, 5),) * 3, b18h - 13, f1)
        for n in range(12):
            col = PR.coin_column(coll, f"s7_col{n}", 9, 0.032)
            st = b18h + 3 * n - 3
            land = st + 6
            px = ST.p(0.75 + (n - 5.5) * 0.145, -0.3, 1.6)
            T.set(col.root, "location", lambda f, px=px, st=st, land=land: tuple(px + V(0, 0, 1.2 * (1 - ease_in((f - st) / (land - st)))
                                                                                      if f < land else 0)), st - 1, land + 1)
            T.set(col.root, "scale", lambda f, st=st, n=n: (PR_pop_life(f, st, f1 - 5 + 0 * n, 3, 4),) * 3, st - 1, f1)
            T.mul(col.root, "scale", lambda f, land=land: (lambda xy, z: (xy, xy, z))(*impact_squash(f, land, 0.18, 4.0)), land - 3, land + 14)
            c.cue(land, "pop", 0.5)
        lab = L.empty("s7_label", None, ST.p(0.45, -0.35, 2.62), coll)
        W.anchors["col1800"] = lab
        C.kalle_react(T, k, "neutral", bb, hold=20)
        C.kalle_look(T, k, lambda f: ST.p(0.45 + (min(11, max(0, (f - b18h) / 3)) - 5.5) * 0.145, -0.3, 2.0), b18h - 2, f1, 1.0, 4)
        T.add(k.stache, "rotation_euler", lambda f: (0, 0.14 * math.sin((f - b18h) * 1.5) * window(f, b18h + 20, b18h + 36, 2, 8), 0),
              b18h + 20, b18h + 36)

    _szene7()

    def _szene8():
        # ================================================================ SZENE 8 – Gesendet!
        i = 7
        f0, f1 = S[i]
        bg_ = c.word(7, "Gesendet")
        bd = c.word(7, "Des")

        def shot8(f):
            t = ease_out((f - f0) / (f1 - f0))
            pos = TH.p(TX + 0.18, -3.3, 1.66).lerp(TH.p(TX + 0.1, -2.6, 1.72), t)
            tgt = TH.p(TX, 0.2, 1.95).lerp(TH.p(TX, 0.2, 2.02), t)
            return pos, tgt, 28.0
        G['shot8'] = shot8
        cam.add_shot(f0, f1, shot8)
        T.set(b.root, "location", lambda f: tuple(B_TH), f0, N)
        lapt = TH.objs["laptop"]
        btn = PR.send_button(coll, "s8_btn", r=0.16)
        btn_p = TH.p(TX + 0.12, -0.6, TH.top_z)
        T.set(btn.root, "location", lambda f: tuple(btn_p), f0, f0 + 1)
        T.set(btn.root, "scale", lambda f: (PR_pop_life(f, f0 - 2, f1 + 6, 6, 6),) * 3, f0 - 3, f1 + 14)
        T.mul(btn.root, "scale", lambda f: (1 + 0.08 * (0.5 + 0.5 * math.sin((f - f0) * 0.5)),) * 3 if f < bg_ else (1, 1, 1), f0, bg_ + 1)
        T.set(btn.cap, "scale", lambda f: (1, 1, 1 - 0.4 * spring((f - bg_) / FPS, 3.5, 0.3)) if f >= bg_ else (1, 1, 1), bg_ - 1, bg_ + 25)
        C.pose(T, k, "point_wind", f0, bg_ - 3, 6, 3, settle=False)
        C.pose(T, k, "point_hit", bg_ - 3, bd - 6, 3, 6)
        T.set(k.finger["L"], "scale", lambda f: (1, 1, 0.35 + 0.65 * window(f, f0 + 2, bd - 4, 4, 6)), f0, bd)
        c.cue(bg_, "ding", 1.0)
        cam.shakes.append((bg_, 0.04, 9))
        PR.shock_ring(T, coll, "s8_ring", tuple(btn_p + V(0, 0, 0.08)), bg_, 14, 1.3)
        # Umschlag faltet sich zum Papierflieger und fliegt durch die Ladentuer
        env8 = PR.envelope(coll, "s8_env", scale=0.6)
        pl8 = PR.paper_plane(coll, "s8_plane", scale=0.8)
        e_p = btn_p + V(0, -0.05, 0.35)
        T.set(env8.root, "location", lambda f: tuple(e_p), bg_, bg_ + 1)
        T.set(env8.root, "scale", lambda f: (0.6 * pop(f, bg_ + 1, 5) * (1 - ease_in_out((f - bg_ - 4) / 10)),) * 3, bg_, bg_ + 15)
        T.set(env8.root, "rotation_euler", lambda f: (0, 0.6 * ease_in_out((f - bg_ - 4) / 10), 1.2 * ease_in_out((f - bg_ - 4) / 10)), bg_, bg_ + 15)
        door = V(TH.objs["door"])
        pp = path([(bg_ + 8, e_p), (bg_ + 18, e_p + V(0.35, 0.1, 0.55)), (bg_ + 30, door + V(-0.55, -0.4, 0.5)),
                   (bg_ + 40, door + V(0, 0.05, 0.0)), (bg_ + 44, door + V(0, 0.6, 0.0))], ease=lambda t: t)
        T.set(pl8.root, "location", pp, bg_ + 7, bg_ + 45)

        def plane_rot(f):
            a, b_ = V(pp(f)), V(pp(f + 1))
            d = (b_ - a)
            if d.length < 1e-6:
                return (0, 0, 0)
            yaw = math.atan2(-d.x, d.y)
            pitch = math.atan2(d.z, math.hypot(d.x, d.y))
            return (pitch, 0.4 * math.sin(f * 0.3), yaw)
        T.set(pl8.root, "rotation_euler", plane_rot, bg_ + 7, bg_ + 45)
        T.set(pl8.root, "scale", lambda f: (0.8 * pop(f, bg_ + 9, 6) * (1 - ease_in((f - bg_ - 38) / 6)),) * 3, bg_ + 8, bg_ + 45)
        C.trail(T, coll, "s8trail", lambda f: pp(f), bg_ + 10, bg_ + 44, n=8, size=0.035)
        # Beat 'Des': Jubel, Mehlwolke, Konfetti, Byte macht einen Looping
        C.kalle_react(T, k, "jubel", bd, hold=f1 - bd + 18, speaking=True)
        PR.burst(T, coll, "s8_flour", "puff", tuple(K_TH + V(0, -0.2, 1.3)), bd, 18, 801, speed=(0.8, 1.6), up=0.6, gravity=-0.4,
                 life=(18, 28), size=(0.9, 1.7), drag=3.0)
        conf_kinds = [f"confetti_{col}" for col in (L.TURQ, L.GOLD, L.YELLOW, L.RED, L.GREEN, L.FLOUR)]
        s9_0 = S[8][0]

        def tw(f):
            """Zeitlupe ab Szene 9: Konfetti haengt kurz in der Luft und faellt langsam."""
            if f < s9_0:
                return f
            return s9_0 + (f - s9_0) * 0.3
        PR.burst(T, coll, "s8_conf", "confetti", tuple(K_TH + V(0.1, -0.35, 2.3)), bd, 70, 802, speed=(1.8, 3.4), up=1.4, spread=1.3,
                 gravity=-2.4, life=(70, 95), size=(0.9, 1.4), drag=1.4, spin=10, kinds=conf_kinds, tw=tw, fade_frac=0.2)
        loop0 = bd
        T.add(b.body, "rotation_euler", lambda f: (-2 * math.pi * ease_in_out((f - loop0) / 18), 0, 0), loop0, loop0 + 18)
        T.add(b.bob, "location", lambda f: (0, -0.25 * math.sin(2 * math.pi * ease_in_out((f - loop0) / 18)),
                                            0.3 * (1 - math.cos(2 * math.pi * ease_in_out((f - loop0) / 18)))), loop0, loop0 + 18)
        C.trail(T, coll, "s8btrail", lambda f: tuple(V(T.loc(b.root, f)) + V(T.loc(b.bob, f))), loop0, loop0 + 20, n=7, size=0.05)

    _szene8()

    def _szene9():
        # ================================================================ SZENE 9 – Schock und Loop
        i = 8
        f0, f1 = S[i]
        bm_ = c.word(8, "Moment")
        b150b = c.word(8, "150")
        zoom1 = b150b + 4
        hold1 = zoom1 + 15
        back_end = N - 1
        face_t = TH.p(K_TH.x, K_TH.y - 0.2, 1.65)
        S8_end = G['shot8'](S[7][1] - 1)

        def shot9(f):
            p8, t8, l8 = S8_end
            if f < b150b:
                return p8, t8, l8
            if f < zoom1:
                t = ease_out((f - b150b) / 4)
                return p8.lerp(TH.p(K_TH.x + 0.05, -2.2, 2.0), t), t8.lerp(face_t, t), lerp(l8, 45, t)
            if f < hold1:
                return TH.p(K_TH.x + 0.05, -2.2, 2.0), face_t, 45
            t = ease_in_out((f - hold1) / max(1, back_end - hold1))
            p, tg, ln = G['shot1'](S[0][0])
            return TH.p(K_TH.x + 0.05, -2.2, 2.0).lerp(p, t), face_t.lerp(tg, t), lerp(45, ln, t)
        cam.add_shot(f0, f1, shot9)
        # Moment: Augen werden langsam groesser, Schweissperle
        for side in ("R", "L"):
            T.mul(k.eye[side], "scale", lambda f: (1 + 0.25 * window(f, bm_, hold1 + 10, 25, 15),) * 3, bm_, hold1 + 10)
        drop_ = L.sphere("s9_sweat", 0.035, 8, 6, (1, 1, 1.5), L.mat("sweat", "#BFF3EE", 0.3, emit=L.TURQ, strength=0.4), k.head,
                         (0.26, -0.18, 0.42), coll)
        T.set(drop_, "location", lambda f: (0.27, -0.2, 0.42 - 0.3 * ease_in((f - bm_ - 6) / 26)), bm_ + 5, bm_ + 33)
        T.set(drop_, "scale", lambda f: (PR_pop_life(f, bm_ + 5, bm_ + 28, 6, 5),) * 3, bm_ + 4, bm_ + 35)
        # 150: Schock, Muetze schiesst hoch, Kasse springt auf, Muenzen flattern davon
        C.kalle_react(T, k, "schock", b150b, hold=hold1 - b150b + 6, speaking=True)
        drw = TH.objs["drawer"]
        T.set(drw, "location", lambda f: (0, -0.3 * ease_out_back(min(1, (f - b150b) / 5), 2.5), 0) if f < hold1 + 6 else
              (0, -0.3 * (1 - ease_in_out((f - hold1 - 6) / 14)), 0), b150b - 1, hold1 + 21)
        reg_p = V(TH.objs["register"].location) + V(0, -0.35, 0.15)
        PR.burst(T, coll, "s9_coins", "coinp", tuple(reg_p), b150b + 2, 10, 901, speed=(1.2, 1.8), up=3.0, spread=0.5, gravity=0.6,
                 life=(26, 36), size=(1.0, 1.3), drag=0.6, spin=3, flutter=0.75, wobble=0.12, fade_frac=0.3)
        c.cue(b150b, "buzz", 1.0)
        # Byte zuckt zurueck
        T.add(b.root, "location", lambda f: (0.12 * window(f, b150b, hold1 + 12, 2, 14), 0.1 * window(f, b150b, hold1 + 12, 2, 14),
                                             0.06 * window(f, b150b, hold1 + 12, 2, 14)), b150b, hold1 + 12)
        T.add(b.body, "rotation_euler", lambda f: (0.3 * window(f, b150b, hold1 + 12, 2, 14), 0, -0.2 * window(f, b150b, hold1 + 12, 2, 14)),
              b150b, hold1 + 12)
        # Kalle hoert auf zu jubeln (Arme sinken langsam), Lachen friert ein
        C.kalle_look(T, k, lambda f: TH.p(0.35, -2.0, 2.0), f0, b150b, 0.6)

    _szene9()

    W.loop_frames = 12
    # Kamera-Fokus folgt Kalles Gesicht (leichte Tiefenunschaerfe im Hintergrund)
    W.cam.focus_fn = lambda f: tuple(V(T.loc(k.root, f)) + V(0, -0.25, 1.95))
