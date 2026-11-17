"""Regie fuer 'Baecker ohne Website'. Alle Aktionen haengen an den Wort-Zeitstempeln der Stimmen.
Szenen-Indizes 0..11 entsprechen Szene 1..12. Alle Code-, Zeilen- und Website-Bilder stammen aus
website/ (echter Quelltext, echte Playwright-Aufnahmen)."""
import json
import math
import os
import random

from mathutils import Vector, Matrix

import characters as C
import look as L
import props as PR
from anim import (ease_in, ease_out, ease_in_out, ease_out_back, spring, window, pop, unpop, lerp, Noise)
from choreo.common import Ctx, path, pop_obj, V

FPS = 30
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WEB = os.path.join(ROOT, "website")
SHOTS = os.path.join(WEB, "shots")


def J(*p):
    return os.path.join(SHOTS, *p)


def rotz(v, a):
    return Matrix.Rotation(a, 3, "Z") @ Vector(v)


def lerp3(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def shot_lerp(f0, f1, A, B, ease=ease_in_out, roll=(0.0, 0.0)):
    def fn(f):
        t = ease((f - f0) / max(1, f1 - f0))
        return (lerp3(A[0], B[0], t), lerp3(A[1], B[1], t), lerp(A[2], B[2], t), lerp(roll[0], roll[1], t))
    return fn


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    TH, ST = c.sets["theke"], c.sets["studio"]
    sc = c.sc
    S = [(s["f0"], s["f1"]) for s in sc]
    coll = W.coll
    cam = W.cam
    boxen = json.load(open(J("boxen.json")))
    geraete = json.load(open(J("geraete", "geraete.json")))
    meta = json.load(open(os.path.join(WEB, "meta.json")))

    def wf(i, core, nth=1):
        n = 0
        for w in sc[i]["words"]:
            if w["w"].strip(".,!?:–").lower() == core.lower():
                n += 1
                if n == nth:
                    return w["f0"]
        return sc[i]["f0"]

    # ------------------------------------------------------------ Anker fuer Overlays / QA
    W.anchors["kalle_face"] = L.empty("anchor_kalle_face", k.head, (0, -0.25, 0.28), coll)
    W.anchors["byte"] = b.body

    # ------------------------------------------------------------ Grundbewegung (nie starr)
    C.kalle_idle(T, k, 0, N - 1, seed=7)
    C.byte_idle(T, b, 0, N - 1, seed=3)
    C.byte_blinks(T, b, 0, N - 1, seed=11)
    C.antenna_spring(T, b, 2, N - 1)
    C.byte_code_face(T, b, 0, N - 1)
    C.follow_through(T, k.hat, k.head, "rotation_euler", 2, 0.9, 3, 0, N - 1)
    C.follow_through(T, k.hat, k.head, "rotation_euler", 0, 0.7, 3, 0, N - 1)
    C.follow_through(T, k.skirt, k.hips, "rotation_euler", 1, 1.2, 4, 0, N - 1)
    C.follow_through(T, k.skirt, k.hips, "rotation_euler", 0, 1.0, 4, 0, N - 1)
    C.pose(T, k, "arms_rest", -10, None, 1, 1, weight=0.6, settle=False)

    def set_kalle(f0, f1, loc, rz=0.0):
        T.set(k.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(k.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)

    def set_byte(f0, f1, loc):
        T.set(b.root, "location", lambda f, loc=loc: tuple(loc) if callable(loc) is False else tuple(loc(f)), f0, f1)

    # Sprechen; Kalle schaut Byte an, wenn Byte spricht
    for i, s in enumerate(sc):
        if s["sprecher"] == "kalle":
            C.kalle_lipsync(T, k, s, s["f0"], s["f1"])
        else:
            C.byte_speak(T, b, s, s["f0"], s["f1"])
        for w in s["words"]:
            if w["hl"] and i not in (5,):
                cam.punch.append(w["f0"])

    # Kamera-Drift an Anfang und Ende auf null (nahtloser Loop: letztes Bild = erstes Bild)
    cam.drift_env = lambda f: min(1.0, f / 12.0, max(0.0, (N - 1 - f) / 12.0))

    K_TH = V(TH.kalle)
    B_TH = TH.p(0.66, -0.28, 2.28)
    top = TH.top_z

    # ------------------------------------------------------------ Requisiten Theke
    slips = PR.order_slips(coll, "slips", n=22, seed=5)
    slips.root.location = TH.p(-0.62, -0.5, top)
    PR.slips_flutter(T, slips, 0, S[1][0] + 12, amount=1.0)
    PR.slips_flutter(T, slips, S[1][0] + 12, S[11][0], amount=0.35, seed=31)
    laptop = TH.objs["laptop"]
    laptop.root.rotation_euler = (0, 0, math.radians(-14))
    lap_d0 = PR._display_plane(coll, "lap_leer", J("geraete", "browser_leer.png"), 0.56, 0.34, laptop.lid,
                               (0, -0.0095, 0.2))
    lap_d1 = PR._display_plane(coll, "lap_web", J("viewport_laptop.png"), 0.56, 0.34, laptop.lid, (0, -0.011, 0.2))
    # Fragezeichen blinkt (Szene 1-11), danach echte Website (Szene 12)
    web_on = S[11][0] + 6
    T.set(lap_d0, "scale", lambda f: (1, 1, 1) if f < web_on else (0, 0, 0), 0, N)
    T.set(lap_d1, "scale", lambda f: (pop(f, web_on, 6),) * 3, 0, N)
    q_blink = PR._display_plane(coll, "lap_leer2", J("geraete", "browser_leer_blink.png"), 0.56, 0.34, laptop.lid,
                                (0, -0.0102, 0.2))
    T.set(q_blink, "scale", lambda f: ((1, 1, 1) if (f // 9) % 2 == 0 and f < S[2][0] + 4 else (0, 0, 0)), 0, N)

    # Kalles Handy auf der Theke (Szene 11/12)
    phone11 = PR.device(coll, "phone11", "handy", [J("handy_bestaetigung.png")], scale=0.5)
    PH_POS = TH.p(-0.18, -0.62, top + 0.24)
    phone11.root.rotation_euler = (math.radians(-12), 0, 0)
    T.set(phone11.root, "location", lambda f: tuple(PH_POS), 0, 1)
    stand = L.box("phone_stand", (0.16, 0.12, 0.05), L.mat("stand", L.WOOD_DARK, 0.6), None,
                  TH.p(-0.18, -0.56, top + 0.025), coll)
    nf = L.empty("anchor_phone_notify", None, PH_POS + V(0, 0, 0.36), coll)
    W.anchors["phone_notify"] = nf

    # =================================================================== SZENE 1 – Theke, Hook
    f0_1, f1_1 = S[0]
    A1 = (TH.p(0.14, -4.6, 2.12), TH.p(0.1, 0.2, 1.98), 33.0)
    B1 = (TH.p(0.1, -3.35, 2.05), TH.p(0.08, 0.2, 1.98), 42.0)
    cam.add_shot(f0_1, f1_1, shot_lerp(f0_1, f1_1, A1, B1, ease_out))
    set_kalle(0, S[2][1], K_TH, 0.0)
    T.set(b.root, "scale", lambda f: (0, 0, 0), 0, 1)
    C.reaction(T, coll, k, "zweifel", wf(0, "Internet") - 2, hold=40, speaking=True)
    # Kalle schaut auf den wackligen Stapel, dann zur Kamera
    C.kalle_look(T, k, lambda f: slips.root.location + V(0, 0, 0.2), 4, wf(0, "Internet") - 4, 0.8)

    # =================================================================== SZENE 2 – Windstoss
    f0_2, f1_2 = S[1]
    gust = wf(1, "Zetteln") - 6
    fly = list(range(11, 22))               # obere Haelfte fliegt weg
    tgts = [TH.p(-0.35 + 0.14 * (j % 5), 0.42 + 0.05 * (j % 3), 0.02) for j in range(6)] + \
           [TH.p(-1.18 + 0.1 * (j % 3) - 0.1, -0.47 + 0.04 * j, top + 0.012) for j in range(5)]
    PR.slips_blowaway(T, slips, fly, gust, tgts, seed=12, dur=(20, 30))
    for j, i in enumerate(fly[:5]):
        pass
    c.cue(gust, "buzz", 1.0)
    c.cue(gust - 4, "whoosh", 0.5)
    PR.ambient_motes(T, coll, "gustdust", tuple(TH.p(-0.3, -0.6, 1.5)), (0.8, 0.3, 0.4), 18, 77, gust - 2, gust + 40,
                     drift=0.25)
    # Kalle greift ins Leere (rechter Arm nach den Zetteln)
    grab = {"sh_R": (-1.35, 0.35, 0.35), "el_R": (-0.35, 0, 0), "hips": (0.06, 0, 0.12), "head": (0.1, 0, 0.2)}
    C.pose(T, k, grab, gust + 10, gust + 34, 5, 10)
    T.add(k.finger["R"], "scale", lambda f: (0, 0, 1.6 * window(f, gust + 12, gust + 34, 3, 6)), gust + 10, gust + 36)
    C.reaction(T, coll, k, "zweifel", wf(1, "verschlamp") - 2, hold=30, speaking=True, seed=2)

    def shot2(f):
        t = ease_in_out((f - f0_2) / (f1_2 - f0_2))
        u = ease_in_out((f - gust) / 30)
        pos = TH.p(-0.25 - 0.1 * u, -3.0, 2.05)
        tgt_paper = TH.p(-0.62, -0.2, 1.85 + 0.5 * u)
        tgt_face = TH.p(-0.12, 0.2, 2.0)
        w = ease_in_out((f - (gust + 26)) / 28)
        lens = 40 - 4 * window(f, gust, gust + 40, 10, 20)
        return (pos, tgt_paper.lerp(tgt_face, w if f > gust + 26 else 0.0) if f >= gust else
                tgt_face.lerp(tgt_paper, ease_in_out((f - f0_2) / max(1, gust - f0_2))), lens)
    cam.add_shot(f0_2, f1_2, shot2)

    # =================================================================== SZENE 3 – Byte aus dem Laptop
    f0_3, f1_3 = S[2]
    burst_f = f0_3 + 4
    lap_pos = laptop.root.location + V(0.0, -0.05, 0.28)
    arrive = f0_3 + 22
    T.set(b.root, "scale", lambda f: ((1, 1, 1) if f >= burst_f else (0, 0, 0)), f0_3, f0_3 + 1)
    T.set(b.root, "scale", lambda f: (max(0.0, ease_out_back(min(1, (f - burst_f) / 6), 2.0)),) * 3,
          burst_f - 1, burst_f + 7)
    bpath = path([(burst_f, lap_pos), (burst_f + 8, TH.p(0.9, -1.0, 2.7)), (arrive, B_TH)], ease_out)
    T.set(b.root, "location", lambda f: bpath(f), f0_3, f1_3)
    T.mul(b.body, "scale", lambda f: (1 - 0.15 * window(f, arrive - 4, arrive + 6, 2, 6), 1,
                                      1 + 0.15 * window(f, arrive - 4, arrive + 6, 2, 6)), arrive - 4, arrive + 6)
    C.trail(T, coll, "s3trail", lambda f: bpath(f), burst_f, arrive + 4, n=9, size=0.07)
    PR.flash(T, coll, "s3flash", tuple(lap_pos), burst_f, 8, 0.25, L.TURQ, 200)
    c.cue(burst_f - 2, "whoosh", 1.0)
    code_w = wf(2, "Code")
    T.add(b.tip, "scale", lambda f: (1.8 * window(f, code_w - 2, code_w + 10, 2, 8),) * 3, code_w - 2, code_w + 10)
    T.add(L.bsdf(b.m_tip).inputs["Emission Strength"], "default_value",
          lambda f: 30 * window(f, code_w - 2, code_w + 10, 2, 8), code_w - 2, code_w + 10)
    PR.burst(T, coll, "s3ant", "spark", tuple(B_TH + V(0.03, 0, 0.4)), code_w - 1, 8, 31, speed=(0.6, 1.0),
             up=0.8, gravity=-1.0, life=(10, 16), size=(0.6, 1.0))
    C.kalle_look(T, k, lambda f: V(T.loc(b.root, f)), burst_f, f1_3, 1.0, 3)
    C.reaction(T, coll, k, "zweifel", wf(2, "Website") - 2, hold=30, seed=3)
    A3 = (TH.p(0.0, -2.6, 2.05), TH.p(-0.05, 0.2, 2.0), 45.0)
    B3 = (TH.p(0.2, -3.7, 2.1), TH.p(0.22, 0.2, 2.02), 36.0)
    cam.add_shot(f0_3, f1_3, shot_lerp(f0_3, f1_3, A3, B3, ease_in_out))

    # =================================================================== Studio-Grundlagen
    scr = ST.objs["screen"]
    scr_light = ST.objs["screenlight"]
    screen_on = [S[4], S[9]]
    T.set(scr, "scale", lambda f: (1, 1, 1) if any(a - 2 <= f < bb + 2 for a, bb in screen_on) else (0, 0, 0), 0, N)
    T.set(scr_light.data, "energy", lambda f: 220 if any(a <= f < bb for a, bb in screen_on) else 0, 0, N)
    T.set(scr, "location", lambda f: tuple(ST.p(-0.45, 3.3, 4.45)) if f < S[9][0] else tuple(ST.p(0.0, 2.6, 4.1)),
          0, N)
    T.set(ST.objs["spot"].data, "energy", lambda f: 0, 0, 1)
    W.cam.whips.append((S[3][0], 1))
    c.cue(S[3][0] - 5, "whoosh", 0.9)

    # =================================================================== SZENE 4 – Rezept = Code
    f0_4, f1_4 = S[3]
    K4 = ST.p(-0.45, 0.3, 0)
    set_kalle(f0_4, S[4][0], K4, -0.22)
    B4 = ST.p(0.55, 0.0, 2.2)
    T.set(b.root, "location", lambda f: tuple(B4), f0_4, S[4][0])
    card = PR.recipe_card(coll, "recipe")
    card.root.location = ST.p(-0.1, 0.6, 3.45)
    card.root.rotation_euler = (0, 0, math.radians(4))
    pop_obj(T, card.root, f0_4 + 3, f1_4 - 2)
    r_w = wf(3, "Rezept")
    for i, row in enumerate(card.rows):
        pop_obj(T, row, r_w - 4 + 5 * i)
    code = json.load(open(J("code", "code.json")))
    keys = ["kopf", "angebot", "formular"]
    lines_f = [wf(3, "Computer") - 4, wf(3, "Zeile") - 6, wf(3, "Schritt") - 6]
    cl_objs = []
    for i, key in enumerate(keys):
        o = PR.code_plate(coll, f"focus_{key}", J("code", f"fokus_{key}.png"), height=0.16,
                          loc=tuple(ST.p(0.1, 0.45, 3.0 - 0.24 * i)), backing=True)
        pop_obj(T, o, lines_f[i], f1_4 - 2)
        cl_objs.append(o)
        # leuchtende Linie: Rezeptschritt -> Code-Zeile
        a = card.root.location + V(0.38, -0.04, 0.13 - 0.2 * i)
        bb = o.location + V(-o["w"] / 2 - 0.03, 0, 0)
        PR.glow_line(T, coll, f"recipe_link{i}", a, bb, lines_f[i] + 2, f1_4 - 4, r=0.008)
        c.cue(lines_f[i], "pop", 0.35)
    for nm, x in (("wand_a", -0.95), ("wand_b", 1.1)):
        wo = L.tplane(f"s4_{nm}", J("code", f"{nm}.png"), height=4.2, parent=None,
                      loc=tuple(ST.p(x * 1.3, 3.6, 3.0)), coll=coll, emit=0.5,
                      mat=L.img_mat(f"wall_{nm}", J("code", f"{nm}.png"), 0.5))
        pop_obj(T, wo, f0_4, f1_4 - 1, dur_in=10)
    A4 = (ST.p(0.1, -4.7, 2.25), ST.p(0.1, 0.5, 2.25), 33.0)
    B4c = (ST.p(0.1, -4.25, 2.28), ST.p(0.1, 0.5, 2.28), 35.0)
    cam.add_shot(f0_4, f1_4, shot_lerp(f0_4, f1_4, A4, B4c, ease_out))
    # Tiefenunschaerfe: nur die drei Code-Zeilen im Fokus scharf, die Code-Wand dahinter weich
    dof = W.cam.cam.data.dof
    T.set(dof, "aperture_fstop", lambda f: 0.12 if S[3][0] <= f < S[3][1] else 2.2, 0, N)
    face_s = [(0, "neutral"), (S[2][0] + 6, "happy"), (code_w - 2, "code"), (S[3][0] + 4, "happy"),
              (lines_f[0] - 2, "code")]
    C.kalle_look(T, k, lambda f: card.root.location, f0_4 + 6, f1_4 - 4, 0.8)

    # =================================================================== SZENE 5 – Code-Turm
    f0_5, f1_5 = S[4]
    K5 = ST.p(-0.32, 0.1, 0)
    B5 = ST.p(0.0, -0.1, 2.45)
    T.set(b.root, "location", lambda f: tuple(B5 + V(0, 0, 0.04 * math.sin(f * 0.6))), f0_5, S[5][0])
    set_kalle(S[4][0], S[5][0], K5, -0.3)
    TW = ST.p(0.78, 0.35, 1.0)
    tw_base = L.cyl("tower_base", 0.62, 0.06, 20, L.mat("tower_base", "#2B2750", 0.5, emit=L.TURQ, strength=0.3),
                    None, TW + V(0, 0, -0.03), coll)
    import timing as OV
    fa, fb = OV.counter_window(sc[4])
    n_pl = len(code["platten"])
    plates = []
    for i in range(n_pl):
        pl = PR.code_plate(coll, f"plate{i}", J("code", f"platte_{i:02d}.png"), height=0.07, backing=True)
        pos, ang = PR.tower_slot(i, n_pl, radius=0.34, rise=0.036)
        world = TW + pos
        launch = fa + (fb - 8 - fa) * i / (n_pl - 1)
        land = launch + 8

        def ploc(f, launch=launch, land=land, world=world):
            if f <= launch:
                return tuple(B5)
            t = min(1.0, (f - launch) / (land - launch))
            p = B5.lerp(world, ease_out(t))
            p.z += 0.5 * math.sin(math.pi * t)
            return tuple(p)
        T.set(pl, "location", ploc, launch - 1, land + 1)
        T.set(pl, "rotation_euler", lambda f, ang=ang, launch=launch: (0, 0, ang * ease_out((f - launch) / 8)),
              launch - 1, launch + 9)
        T.set(pl, "scale", lambda f, launch=launch: (pop(f, launch, 5),) * 3, launch - 1, launch + 6)
        plates.append((pl, land, world))
        if i % 3 == 0:
            c.cue(int(land), "pop", 0.22)
    c.cue(fb, "pop", 1.0)
    bowl = PR.dough_bowl(coll, "bowl")
    ped = L.box("bowl_ped", (0.5, 0.5, 1.35), L.mat("pedestal", "#2B2750", 0.5), None, ST.p(0.05, -0.25, 0.675),
                coll, bevel=0.02)
    bowl.root.location = ST.p(0.05, -0.25, 1.35)
    for o in (bowl.root, ped, tw_base):
        pop_obj(T, o, f0_5, S[5][0] + 6)
    T.set(bowl.dough, "scale", lambda f: (1 + 0.04 * ease_in_out((f - f0_5) / (f1_5 - f0_5)), 1 +
                                          0.04 * ease_in_out((f - f0_5) / (f1_5 - f0_5)),
                                          1 + 0.35 * ease_in_out((f - f0_5) / (f1_5 - f0_5))), f0_5, f1_5)
    T.set(bowl.dough, "location", lambda f: (0, 0, 0.16 + 0.03 * ease_in_out((f - f0_5) / (f1_5 - f0_5))), f0_5, f1_5)
    C.reaction(T, coll, k, "staunen", wf(4, "Hunderte"), hold=int(0.9 * (f1_5 - f0_5)), seed=5)
    C.kalle_look(T, k, lambda f: TW + V(0, 0, 1.8), f0_5, f1_5, 0.9)
    glimpse = f0_5 + int(0.72 * (f1_5 - f0_5))

    def shot5(f):
        t = ease_in_out((f - f0_5) / max(1, glimpse - f0_5))
        pos = ST.p(0.12, -4.1, 1.95).lerp(ST.p(0.15, -4.1, 2.2), t)
        tgt = ST.p(0.12, 0.3, 2.1).lerp(ST.p(0.15, 0.3, 2.4), t)
        lens = 33.0
        if f > glimpse:
            u = ease_in_out((f - glimpse) / (f1_5 - glimpse))
            pos = pos.lerp(V(K5) + V(0.25, -3.1, 2.05), u)
            tgt = tgt.lerp(V(K5) + V(0.15, 0, 2.02), u)
            lens = lerp(33, 38, u)
        return (pos, tgt, lens)
    cam.add_shot(f0_5, f1_5, shot5)

    # =================================================================== SZENE 6 – Geruest, Farben, klickbar
    f0_6, f1_6 = S[5]
    A0 = f0_6
    B0 = wf(5, "Farben") - 5
    C0 = wf(5, "dann", 2) - 3
    P0 = ST.p(0.15, 1.15, 0)
    VIEWZ = 3.28
    th0, th1 = math.radians(-28), math.radians(30)
    orbit_end = C0

    def theta(f):
        return lerp(th0, th1, ease_in_out((f - A0) / max(1, orbit_end - A0)))
    K6L, B6L = V(-0.55, -0.3, 0), V(0.08, -0.6, 2.15)
    T.set(k.root, "location", lambda f: tuple(P0 + rotz(K6L, theta(f))), f0_6, f1_6)
    T.set(k.root, "rotation_euler", lambda f: (0, 0, theta(f) - 0.18), f0_6, f1_6)
    T.set(b.root, "location", lambda f: tuple(P0 + rotz(B6L, theta(f))), f0_6, f1_6)
    C.reaction(T, coll, k, "staunen", wf(5, "Gerüst"), hold=f1_6 - wf(5, "Gerüst"), seed=6)
    C.kalle_look(T, k, lambda f: P0 + V(0, 0, VIEWZ), f0_6, C0 + 10, 0.9)

    # Turm zerfaellt in Partikel
    for i, (pl, land, world) in enumerate(plates):
        d0 = A0 + 2 + int(i * 10 / n_pl)
        T.set(pl, "scale", lambda f, d0=d0: (unpop(f, d0, 5),) * 3, d0 - 1, d0 + 6)
    PR.burst(T, coll, "tower_dust", "sparkt", tuple(TW + V(0, 0, 1.4)), A0 + 2, 40, 61, speed=(0.8, 1.8), up=0.5,
             spread=1.0, gravity=0.0, life=(12, 20), size=(0.8, 1.4), drag=2.0, dir_bias=(-0.6, 0.5, 0.4))

    # Ebenen (echte Geruest-/Stil-Ausschnitte der Handy-Ansicht)
    page = L.empty("page", None, P0 + V(0, 0, VIEWZ), coll)
    teile = boxen["teile"]
    F = 1.0 / 398.0     # m pro CSS-Pixel (Spaltenbreite 1,0 m)

    def hpx(name):
        return L.img_size(J("abschnitte", f"stil_{name}.png"))[1] / boxen["dpr"]

    layout = []         # (name, x, z_top, height, card_index)
    zt = 1.0
    for nm in ("kopf", "hero", "zeiten", "fuss"):
        h = hpx(nm) * F
        layout.append((nm, -0.58, zt, h, None))
        zt -= h + 0.08
    zt = 1.0
    h = hpx("titel_angebot") * F
    layout.append(("titel_angebot", 0.58, zt, h, None))
    zt -= h + 0.08
    cw = 0.32
    for i in range(12):
        nm = f"karte{i + 1:02d}"
        ph = L.img_size(J("abschnitte", f"stil_{nm}.png"))
        ch = cw * ph[1] / ph[0]
        col, row = i % 3, i // 3
        layout.append((nm, 0.58 + (col - 1) * (cw + 0.03), zt - row * (ch + 0.11), ch, i))
    zt -= 4 * (ch + 0.11) + 0.02
    h = hpx("formular") * F
    form_top = zt
    layout.append(("formular", 0.58, zt, h, None))
    fbox = teile["formular"]
    for nm in ("feld_name", "feld_anzahl", "feld_tag", "feld_senden"):
        bx = teile[nm]
        x = 0.58 + ((bx["x"] + bx["w"] / 2) - (fbox["x"] + fbox["w"] / 2)) * F
        z = form_top - (bx["y"] - fbox["y"]) * F
        layout.append((nm, x, z, hpx(nm) * F, None))
    span_top = 1.0
    span_bot = min(z_ - h_ for _, _, z_, h_, _ in layout)
    mid = (span_top + span_bot) / 2
    layers = []
    rr = random.Random(66)
    for j, (nm, x, ztop, h, ci) in enumerate(layout):
        lay = PR.web_layer(coll, f"L_{nm}", J("abschnitte", f"geruest_{nm}.png"), J("abschnitte", f"stil_{nm}.png"),
                           h, parent=page, card=ci is not None)
        zc = ztop - h / 2 - mid
        depth = -0.1 * ((j * 3) % 5) - (0.35 if nm.startswith("feld") else 0.0)
        flat = V(x, 0, zc)
        explode = V(x * 1.06, depth, zc * 1.04)
        start = V(TW - page.location) + V(rr.uniform(-0.3, 0.3), 0, rr.uniform(-0.6, 0.8))
        layers.append(dict(obj=lay, nm=nm, h=h, zc=zc, flat=flat, explode=explode, start=start, ci=ci))
    order = sorted(range(len(layers)), key=lambda j: -layers[j]["zc"])
    pop_span = int(0.62 * (B0 - A0))
    for rank, j in enumerate(order):
        L_ = layers[j]
        t_in = A0 + 6 + int(pop_span * rank / len(order))
        L_["t_in"] = t_in

        def lloc(f, L_=L_):
            if f < L_["t_in"] + 7:
                t = ease_out((f - (L_["t_in"] - 4)) / 11)
                return tuple(L_["start"].lerp(L_["explode"], t))
            if f < C0:
                return tuple(L_["explode"])
            t = ease_in_out((f - C0) / 8)
            return tuple(L_["explode"].lerp(L_["flat"], t))
        T.set(L_["obj"].root, "location", lloc, A0, f1_6)
        T.set(L_["obj"].root, "scale", lambda f, t_in=t_in: (pop(f, t_in, 7, 1.12),) * 3, t_in - 1, t_in + 8)
        if rank % 2 == 0:
            c.cue(t_in + 4, "pop", 0.3)
        # Funke fliegt vom Turm zur Ebene (Partikel werden zu Ebenen)
        if rank % 2 == 0:
            spark = L.ico(f"s6spark{j}", 0.04, 1, (1, 1, 1), L.mat("sparkt", L.TURQ, 0.4, emit=L.TURQ, strength=6.0),
                          None, (0, 0, 0), coll)
            a_ = TW + V(0, 0, 1.4)
            b_ = page.location + L_["explode"]
            T.set(spark, "location", lambda f, a_=a_, b_=b_, t_in=t_in: tuple(a_.lerp(b_, ease_in_out((f - (t_in - 8)) / 10))),
                  t_in - 9, t_in + 2)
            T.set(spark, "scale", lambda f, t_in=t_in: (window(f, t_in - 9, t_in + 1, 2, 2),) * 3, t_in - 10, t_in + 2)

    # PHASE B: Farbwelle von oben nach unten
    wave = PR.color_wave(coll, "wave", 2.6)
    w_dur = 26
    top_z, bot_z = span_top - mid + 0.1, span_bot - mid - 0.1
    T.set(wave, "location", lambda f: tuple(page.location + V(0, -0.75, lerp(top_z, bot_z, ease_in_out((f - B0) / w_dur)))),
          B0, B0 + w_dur)
    T.set(wave, "scale", lambda f: (window(f, B0 - 1, B0 + w_dur + 2, 3, 4),) * 3, B0 - 2, B0 + w_dur + 3)
    T.set(wave, "scale", lambda f: (0, 0, 0), 0, 1)
    c.cue(B0 - 3, "whoosh", 0.9)
    for j, L_ in enumerate(layers):
        lay = L_["obj"]
        ztop_rel = L_["zc"] + L_["h"] / 2
        hit = B0 + w_dur * (top_z - ztop_rel) / (top_z - bot_z)
        grow = max(2.0, w_dur * L_["h"] / (top_z - bot_z))
        if L_["ci"] is None:
            T.set(lay.stil, "scale", lambda f, hit=hit, grow=grow: (1, 1, ease_in_out((f - hit) / grow)), hit - 1,
                  hit + grow + 1)
        else:
            hit = hit + 2 * (L_["ci"] % 3)
            T.set(lay.spin, "rotation_euler",
                  lambda f, hit=hit: (0, 0, math.pi * ease_out_back(min(1, max(0, (f - hit) / 8)), 1.4)), hit - 1, hit + 9)
            kind = PR.CARD_PASTRY[L_["ci"]]
            pz = PR.pastry(coll, f"pastry{L_['ci']}", kind, parent=lay.root,
                           loc=(-lay.w * 0.3, -0.08, L_["h"] / 2), s=0.7)
            ph_ = hit + 7
            T.set(pz, "scale", lambda f, ph_=ph_: (0.7 * pop(f, ph_, 6, 1.2),) * 3, ph_ - 1, ph_ + 7)
            T.add(pz, "location", lambda f, ph_=ph_: (0, 0, 0.09 * max(0.0, math.sin(math.pi * min(1, (f - ph_) / 9)))
                                                      if f > ph_ else 0), ph_, ph_ + 10)
            T.set(pz, "rotation_euler", lambda f, ph_=ph_: (0.3, 0, 2 * math.pi * ease_out((f - ph_) / 12)), ph_, ph_ + 12)
        T.set(lay.bevel, "width", lambda f, hit=hit: 0.03 * ease_out((f - hit - 2) / 6), hit, hit + 9)
        T.set(lay.frame, "scale", lambda f, hit=hit: (1 - ease_in_out((f - hit) / 6),) * 3, hit - 1, hit + 7)
        T.set(lay.shadow, "scale", lambda f, hit=hit: (ease_out((f - hit - 3) / 6),) * 3, hit + 2, hit + 10)

    # PHASE C: zusammenfahren (satter Pop), ins Handy gleiten, tippen, Haken
    phone = PR.device(coll, "phone6", "handy", [J("geraete", g["datei"]) for g in geraete["formular"]], scale=1.0)
    PHL = V(0.42, -2.25, 2.72)
    ph_pos = P0 + rotz(PHL, th1)
    phone.root.rotation_euler = (0, 0, th1)
    p_in = C0 + 4
    T.set(phone.root, "location", lambda f: tuple(ph_pos + V(0, 0, -1.6 * (1 - ease_out_back(min(1, max(0, (f - p_in) / 10)), 1.2)))),
          p_in - 1, p_in + 11)
    T.set(phone.root, "scale", lambda f: ((1, 1, 1) if f >= p_in else (0, 0, 0)), 0, p_in + 1)
    T.set(phone.root, "scale", lambda f: (unpop(f, f1_6 - 2, 2),) * 3, f1_6 - 3, f1_6 + 1)
    collapse = C0 + 8
    T.add(page, "scale", lambda f: (0.07 * spring((f - collapse) / FPS, 3.5, 0.3) if f >= collapse else 0,) * 3,
          collapse, collapse + 20)
    c.cue(collapse, "pop", 1.0)
    glide0, glide1 = collapse + 4, collapse + 14
    disp_c = ph_pos + rotz(V(0, -0.02, -0.01), th1)
    T.set(page, "location", lambda f: tuple((P0 + V(0, 0, VIEWZ)).lerp(disp_c, ease_in(min(1, max(0, (f - glide0) / (glide1 - glide0)))))),
          glide0 - 1, glide1 + 1)
    T.mul(page, "scale", lambda f: (lerp(1, 0.16, ease_in((f - glide0) / (glide1 - glide0))) if f < glide1 else 0,) * 3,
          glide0 - 1, N)
    T.set(page, "rotation_euler", lambda f: (0, 0, th1 * ease_in_out((f - glide0) / (glide1 - glide0))), glide0 - 1, glide1 + 1)
    # Display-Sequenz (echte Playwright-Frames)
    seq = [glide1, glide1 + 5, glide1 + 8, glide1 + 11, glide1 + 14, glide1 + 18, glide1 + 22, glide1 + 31, glide1 + 37]
    for i, d in enumerate(phone.displays):
        nxt = seq[i + 1] if i + 1 < len(seq) else 10 ** 6
        T.set(d, "scale", lambda f, a=seq[i], nb=nxt: (1, 1, 1) if a <= f < nb else (0, 0, 0), 0, N)
    PR.flash(T, coll, "s6flash", tuple(disp_c + V(0, -0.1, 0)), glide1 - 1, 6, 0.3, L.TURQ, 150)
    # Button-Overlay exakt ueber dem echten Button (federt auf 0.95)
    dpr = boxen["dpr"]
    bsec, bsend = boxen["breiten"]["handy"]["boxen"]["bestellen"], teile["feld_senden"]
    y_off = geraete["formular"][0]["y_offset_px"]
    px_cx = (bsend["x"] + bsend["w"] / 2 - (bsec["x"] - 4)) * dpr
    px_cy = y_off + (bsend["y"] + bsend["h"] / 2 - (bsec["y"] - 4)) * dpr
    img_w, img_h = L.img_size(J("geraete", geraete["formular"][0]["datei"]))
    vis = min(1.0, (phone.dh / phone.dw) * img_w / img_h)
    bx = (px_cx / img_w - 0.5) * phone.dw
    bz = phone.dh / 2 - (px_cy / img_h) / vis * phone.dh - 0.01
    bw = bsend["w"] * dpr / img_w * phone.dw
    btn = L.tplane("btn_overlay", J("abschnitte", "stil_feld_senden.png"), width=bw * 1.02, parent=phone.body,
                   loc=(bx, -0.012, bz), coll=coll, emit=1.0)
    tap = seq[7]
    T.set(btn, "scale", lambda f: (1, 1, 1) if seq[0] <= f < seq[8] else (0, 0, 0), 0, N)
    T.mul(btn, "scale", lambda f: (1 - 0.05 * window(f, tap - 1, tap + 5, 1, 4) + 0.03 * spring((f - tap - 5) / FPS, 4, 0.3)
                                   * (f > tap + 5),) * 3, tap - 1, tap + 16)
    fing = PR.finger(coll, "finger")
    tip_w = phone.root.location if False else None
    btn_world = ph_pos + rotz(V(bx, -0.012, bz), th1)
    fin_start = btn_world + rotz(V(0.55, -0.6, -0.55), th1)
    fin_tap = btn_world + rotz(V(0.0, -0.03, -0.02), th1)

    def floc(f):
        if f < tap - 8:
            return tuple(fin_start.lerp(fin_tap + rotz(V(0, -0.12, 0), th1), ease_out((f - (tap - 16)) / 8)))
        if f < tap:
            return tuple((fin_tap + rotz(V(0, -0.12, 0), th1)).lerp(fin_tap, ease_in((f - (tap - 8)) / 8)))
        return tuple(fin_tap.lerp(fin_start, ease_in_out((f - tap - 3) / 12)))
    T.set(fing, "location", floc, tap - 17, tap + 16)
    T.set(fing, "rotation_euler", lambda f: (math.radians(-55), 0, th1 + math.radians(25)), tap - 17, tap + 16)
    T.set(fing, "scale", lambda f: (1, 1, 1) if tap - 16 <= f < tap + 15 else (0, 0, 0), 0, N)
    chk = PR.check_badge(coll, "check6")
    chk.location = ph_pos + rotz(V(-0.36, -0.1, -0.12), th1)
    chk.rotation_euler = (0, 0, th1)
    pop_obj(T, chk, seq[8], f1_6 - 3, base=1.0)
    T.set(chk, "scale", lambda f: (0, 0, 0), 0, 1)
    c.cue(seq[8], "pop", 0.8)
    PR.burst(T, coll, "s6conf", "spark", tuple(chk.location), seq[8] + 1, 12, 66, speed=(0.8, 1.4), up=0.6,
             gravity=-1.0, life=(12, 18), size=(0.6, 1.0))

    def shot6(f):
        if f < orbit_end:
            th = theta(f)
            return (P0 + rotz(V(0, -6.6, 2.25), th), P0 + rotz(V(0, 0, 2.25), th), 35.0)
        t = ease_in_out((f - orbit_end) / max(1, glide1 + 6 - orbit_end))
        a_pos, a_tgt = P0 + rotz(V(0, -6.6, 2.25), th1), P0 + rotz(V(0, 0, 2.25), th1)
        b_pos, b_tgt = P0 + rotz(V(0.18, -5.0, 2.2), th1), P0 + rotz(V(0.18, 0, 2.2), th1)
        return (a_pos.lerp(b_pos, t), a_tgt.lerp(b_tgt, t), lerp(35, 37, t))
    cam.add_shot(f0_6, f1_6, shot6)

    # =================================================================== SZENE 7/8 – Geraete
    f0_7, f1_7 = S[6]
    devs = {}
    DPOS = {"handy": (ST.p(-0.95, 0.9, 3.05), 1.25), "tablet": (ST.p(0.12, 0.9, 3.05), 1.0),
            "laptop": (ST.p(1.55, 0.9, 3.05), 1.0)}
    for nm in ("handy", "tablet", "laptop"):
        dv = PR.device(coll, f"dev_{nm}", nm, [J("geraete", f"angebot_{nm}.png")], scale=DPOS[nm][1])
        devs[nm] = dv
    dev_on, dev_off = f0_7, S[9][1]
    K7 = ST.p(0.25, 0.2, 0)
    B7 = ST.p(0.55, 0.1, 2.35)
    set_kalle(f0_7, S[8][0], K7, 0.0)
    T.set(b.root, "location", lambda f: tuple(B7), f0_7, S[7][0])
    hub = ST.p(0.2, 0.55, 2.62)
    band_f = f0_7 + 2
    PR.glow_line(T, coll, "band_main", B7 + V(0.1, 0.1, 0.05), hub, band_f, S[7][1] - 4, r=0.025, dur=6)
    for nm, dv in devs.items():
        tgt = DPOS[nm][0] + V(0, -0.05, -DEVH(nm) * DPOS[nm][1] / 2 - 0.02)
        PR.glow_line(T, coll, f"band_{nm}", hub, tgt, band_f + 5, S[7][1] - 4, r=0.016, dur=6)
    c.cue(band_f, "whoosh", 0.4)
    # 12 Karten gleiten: 1 Spalte (Handy) -> 2 (Tablet) -> 4 (Laptop)
    cardpos = {}
    for nm in ("handy", "tablet", "laptop"):
        dv = devs[nm]
        vp = boxen["breiten"][nm]["viewport"]
        bx_ = boxen["breiten"][nm]["boxen"]
        pageh = bx_["page"]["h"]
        y0 = max(0, min(bx_["angebot"]["y"] - 12, pageh - vp["height"]))
        vis_ = min(1.0, (dv.dh / dv.dw) * vp["width"] / vp["height"])
        s_ = DPOS[nm][1]
        lst = []
        for cb in bx_["karten"]:
            x = ((cb["x"] + cb["w"] / 2) / vp["width"] - 0.5) * dv.dw
            z = dv.dh / 2 - ((cb["y"] + cb["h"] / 2 - y0) / vp["height"]) / vis_ * dv.dh
            w = cb["w"] / vp["width"] * dv.dw
            h = cb["h"] / vp["height"] / vis_ * dv.dh
            lst.append((DPOS[nm][0] + V(x * s_, -0.07, z * s_), w * s_, h * s_))
        cardpos[nm] = lst
    t_h, t_t0, t_t1, t_l0, t_l1 = f0_7 + 8, f0_7 + 16, f0_7 + 42, f0_7 + 50, f0_7 + 76
    for i in range(12):
        cp = L.tplane(f"glide{i}", J("abschnitte", f"stil_karte{i + 1:02d}.png"), height=1.0, parent=None,
                      coll=coll, emit=1.0)
        base_w = cp["w"]
        (ph, pw_, phh), (pt, tw, th_), (pl, lw, lh) = cardpos["handy"][i], cardpos["tablet"][i], cardpos["laptop"][i]

        def gl(f, i=i, ph=ph, pt=pt, pl=pl):
            d = 0.6 * i
            if f < t_t0 + d:
                return tuple(ph)
            if f < t_t1 + d:
                t = ease_in_out((f - t_t0 - d) / (t_t1 - t_t0))
                p = ph.lerp(pt, t)
                p.y -= 0.35 * math.sin(math.pi * t)
                return tuple(p)
            if f < t_l0 + d:
                return tuple(pt)
            t = ease_in_out((f - t_l0 - d) / (t_l1 - t_l0))
            p = pt.lerp(pl, t)
            p.y -= 0.35 * math.sin(math.pi * t)
            return tuple(p)

        def gs(f, i=i, a=(pw_ / base_w, phh), bb=(tw / base_w, th_), cc=(lw / base_w, lh)):
            d = 0.6 * i
            if f < t_t1 + d:
                t = ease_in_out((f - t_t0 - d) / (t_t1 - t_t0))
                sx, sz = lerp(a[0], bb[0], t), lerp(a[1], bb[1], t)
            else:
                t = ease_in_out((f - t_l0 - d) / (t_l1 - t_l0))
                sx, sz = lerp(bb[0], cc[0], t), lerp(bb[1], cc[1], t)
            k_ = pop(f, t_h + i, 6) * (unpop(f, S[7][1] - 3, 3) if f > S[7][1] - 3 else 1)
            return (sx * k_, 1, sz * k_)
        T.set(cp, "location", gl, f0_7, S[7][1])
        T.set(cp, "scale", gs, f0_7, S[7][1] + 1)
        T.set(cp, "scale", lambda f: (0, 0, 0), 0, 1)
    A7 = (ST.p(-0.2, -4.2, 2.25), ST.p(-0.2, 0.9, 2.25), 35.0)
    B7c = (ST.p(0.8, -4.2, 2.25), ST.p(0.8, 0.9, 2.25), 35.0)
    cam.add_shot(f0_7, f1_7, shot_lerp(f0_7, f1_7, A7, B7c, ease_in_out))
    C.reaction(T, coll, k, "staunen", wf(6, "Code") + 2, hold=f1_7 - wf(6, "Code"), seed=7)
    C.kalle_look(T, k, lambda f: ST.p(0.2 + 1.2 * ease_in_out((f - f0_7) / (f1_7 - f0_7)) - 0.6, 0.9, 3.0), f0_7, f1_7, 0.9)

    # ----- SZENE 8: Des gibt's doch net!
    f0_8, f1_8 = S[7]
    C.reaction(T, coll, k, "staunen", wf(7, "Des"), hold=f1_8 - wf(7, "Des") + 6, speaking=True, seed=8)
    T.add(k.hat, "location", lambda f: (0, 0, 0.12 * max(0, math.sin(math.pi * (f - wf(7, "doch")) / 7)) *
                                        (1 if f - wf(7, "doch") < 7 else 0.5 if f - wf(7, "doch") < 14 else 0)),
          wf(7, "doch"), wf(7, "doch") + 14)
    for side in ("R", "L"):
        T.set(k.reflect[side], "scale", lambda f: (window(f, f0_8 - 2, f1_8 + 4, 4, 4) * 1.0,) * 3, f0_8 - 3, f1_8 + 5)
    face8 = V(K7) + V(0, -0.25, 1.98)
    lap0 = f0_8 + 2

    def blap(f):
        a = 2 * math.pi * ease_in_out((f - lap0) / (f1_8 - lap0 - 2)) - math.pi / 2 - 0.9
        return tuple(V(K7) + V(0.78 * math.cos(a), 0.62 * math.sin(a), 2.55 + 0.1 * math.sin(2 * a)))
    T.set(b.root, "location", blap, f0_8, f1_8)
    C.trail(T, coll, "s8trail", lambda f: blap(f), lap0, f1_8, n=8, size=0.06)
    A8 = (ST.p(0.8, -4.2, 2.25), ST.p(0.8, 0.9, 2.25), 35.0)
    B8 = (face8 + V(0.05, -3.0, 0.03), face8 + V(0.0, 0, 0.0), 42.0)
    cam.add_shot(f0_8, f1_8, shot_lerp(f0_8, f1_8, A8, B8, ease_out, roll=(0.0, math.radians(-6))))

    # =================================================================== SZENE 9 – Marketing
    f0_9, f1_9 = S[8]
    TAB_Z = 1.7
    SHOP = ST.p(0.35, 0.45, TAB_Z)
    table = L.empty("s9_table", None, ST.p(0.35, 0.55, 0), coll)
    L.cyl("s9_tabletop", 1.1, 0.08, 28, L.mat("table_top", "#2B2750", 0.5), table, (0, 0, TAB_Z - 0.04), coll)
    L.torus("s9_tablerim", 1.1, 0.02, 40, 4, L.mat("table_rim", L.TURQ, 0.5, emit=L.TURQ, strength=3.0), table,
            (0, 0, TAB_Z), coll)
    L.cyl("s9_tableleg", 0.18, TAB_Z, 12, L.mat("pedestal", "#2B2750", 0.5), table, (0, 0, TAB_Z / 2), coll)
    shop = PR.mini_shop(coll, "shop")
    shop.root.location = SHOP
    shop.root.scale = (1.0,) * 3
    pop_obj(T, shop.root, f0_9 + 2, S[9][1] + 4, base=1.0)
    pop_obj(T, table, f0_9, S[9][1] + 2)
    T.set(shop.root, "scale", lambda f: (0, 0, 0), 0, 1)
    T.add(shop.sign, "scale", lambda f: (0.08 * math.sin(f * 0.5) * window(f, f0_9, S[9][1], 4, 4),) * 3, f0_9, S[9][1])
    K9 = ST.p(-0.6, -0.6, 0)
    set_kalle(S[8][0], S[10][0], K9, 0.25)
    B9 = ST.p(0.95, -0.55, 2.35)
    T.set(b.root, "location", lambda f: tuple(B9), f0_9, S[10][0])
    D9 = {"handy": (ST.p(-0.45, 0.95, TAB_Z), 0.3), "tablet": (ST.p(0.35, 1.35, TAB_Z), 0.26),
          "laptop": (ST.p(1.15, 0.95, TAB_Z), 0.22)}
    door = SHOP + V(0, -0.38, 0.0)
    cols = ["#FF9F43", "#6B55C9", "#3DDC84", "#FF5A5F", "#2EE6D6", "#FFE14D"]
    for nm, dv in devs.items():
        p7, s7 = DPOS[nm]
        p9, s9 = D9[nm]
        h9 = DEVH(nm) * s9 / 2 + 0.02 + (0.03 if nm == "laptop" else 0)
        p9z = p9 + V(0, 0, h9)

        def dloc(f, p7=p7, p9z=p9z):
            if f < f0_9:
                return tuple(p7)
            return tuple(p7.lerp(p9z, ease_in_out((f - f0_9) / 12)))
        T.set(dv.root, "location", dloc, S[6][0], S[9][1])
        T.set(dv.root, "scale", lambda f, s7=s7, s9=s9: (lerp(s7, s9, ease_in_out((f - f0_9) / 12)) *
                                                          (pop(f, dev_on, 8) if f < dev_on + 9 else 1) *
                                                          (unpop(f, dev_off - 4, 5) if f > dev_off - 4 else 1),) * 3,
              dev_on - 1, dev_off + 2)
        T.set(dv.root, "scale", lambda f: (0, 0, 0), 0, 1)
        # Kunden laufen auf leuchtenden Pfaden zum Laden
        side = V(-0.62 if nm == "handy" else 0.62, -0.25 if nm != "tablet" else 0.4, 0)
        pts = [p9 + V(0, -0.2, 0.0), SHOP + side, door]
        for a_, b_ in zip(pts, pts[1:]):
            PR.glow_line(T, coll, f"path_{nm}{a_.x:.1f}", a_ + V(0, 0, 0.01), b_ + V(0, 0, 0.01), f0_9 + 10,
                         S[9][1] - 4, r=0.014, color=L.YELLOW, dur=10)
        for q in range(2):
            cu = PR.customer(coll, f"cust_{nm}{q}", cols[(q * 3 + len(nm)) % 6], s=0.8)
            st_ = f0_9 + 14 + 18 * q + (6 if nm == "tablet" else 0)
            ar_ = st_ + 52
            segs = [(pts[0] - pts[1]).length, (pts[1] - pts[2]).length]

            def pf(t, pts=pts, segs=segs):
                d = t * sum(segs)
                if d < segs[0]:
                    return pts[0].lerp(pts[1], d / segs[0])
                return pts[1].lerp(pts[2], (d - segs[0]) / segs[1])
            PR.customer_walk(T, cu, pf, st_, S[9][1], ar_)
            T.set(cu.root, "scale", lambda f, st_=st_, ar_=ar_: (pop(f, st_, 6) * (unpop(f, ar_ + 2, 5) if f > ar_ + 2 else 1),) * 3,
                  st_ - 1, ar_ + 8)
            T.set(cu.root, "scale", lambda f: (0, 0, 0), 0, 1)
    C9 = ST.p(0.35, 0.55, 0)

    def ph9(f):
        return lerp(math.radians(-16), math.radians(16), ease_in_out((f - f0_9) / (f1_9 - f0_9)))
    T.set(k.root, "location", lambda f: tuple(C9 + rotz(V(K9) - C9, ph9(min(f, f1_9)))), f0_9, f1_9)
    T.set(k.root, "rotation_euler", lambda f: (0, 0, 0.25 + ph9(min(f, f1_9))), f0_9, f1_9)
    T.set(b.root, "location", lambda f: tuple(C9 + rotz(V(B9) - C9, ph9(min(f, f1_9)))), f0_9, f1_9)

    def shot9(f):
        ph = ph9(f)
        return (C9 + rotz(V(-0.15, -5.15, 3.1), ph), C9 + rotz(V(-0.15, 0, 2.0), ph), 28.0)
    cam.add_shot(f0_9, f1_9, shot9)
    C.reaction(T, coll, k, "neutral", wf(8, "Marketing"), seed=9)
    C.kalle_look(T, k, lambda f: SHOP + V(0, 0, 0.6), f0_9 + 4, f1_9, 0.9)

    # =================================================================== SZENE 10 – Muenzsaeule
    f0_10, f1_10 = S[9]
    t1, t2 = OV.calc_times(sc[9])
    col_ = PR.coin_column(coll, "coins", 52, spacing=0.03)
    COL = ST.p(1.18, 0.3, 1.7)
    K10, B10 = ST.p(-0.38, -0.5, 0), ST.p(0.72, -0.6, 2.3)
    set_kalle(f0_10, S[10][0], K10, 0.2)
    T.set(b.root, "location", lambda f: tuple(B10), f0_10, S[10][0])
    col_.root.location = COL
    col_.root.scale = (1.3, 1.3, 1.0)
    d_start, d_end = t1 + 6, t2
    for i, cn in enumerate(col_.coins):
        land = d_start + (d_end - d_start) * i / 51
        zz = 0.015 + i * 0.03
        T.set(cn, "location", lambda f, land=land, zz=zz: (0, 0, zz + (2.4 * (1 - ease_in((f - (land - 6)) / 6)) if f < land else 0)),
              land - 7, land)
        T.set(cn, "scale", lambda f, land=land: (1, 1, 1) if f >= land - 6 else (0, 0, 0), land - 8, land - 5)
        T.set(cn, "scale", lambda f: (0, 0, 0), 0, 1)
        T.set(cn, "scale", lambda f, land=land: (unpop(f, S[9][1] - 3, 3),) * 3, S[9][1] - 4, S[9][1] + 1)
        if i % 4 == 0:
            c.cue(int(land), "pop", 0.18)
    c.cue(t2 + 16, "pop", 1.0)
    PR.burst(T, coll, "coinspark", "spark", tuple(COL + V(0, -0.1, 1.6)), t2 + 16, 14, 70, speed=(0.8, 1.6), up=0.8,
             gravity=-1.5, life=(14, 22))
    C.reaction(T, coll, k, "staunen", wf(9, "tausend"), hold=f1_10 - wf(9, "tausend"), seed=10)
    C.kalle_look(T, k, lambda f: COL + V(0, 0, 1.2), f0_10, f1_10, 0.9)
    A10 = (ST.p(0.3, -4.5, 2.05), ST.p(0.3, 0.6, 2.2), 31.0)
    B10 = (ST.p(0.3, -4.6, 2.25), ST.p(0.3, 0.6, 2.4), 31.0)
    cam.add_shot(f0_10, f1_10, shot_lerp(f0_10, f1_10, A10, B10, ease_in_out))

    # =================================================================== SZENE 11 – erste Bestellung
    f0_11, f1_11 = S[10]
    set_kalle(f0_11, N, K_TH, 0.0)
    T.set(b.root, "location", lambda f: tuple(B_TH), f0_11, N)
    W.cam.whips.append((f0_11, -1))
    c.cue(f0_11 - 5, "whoosh", 0.9)
    ring = f0_11 + 2
    c.cue(ring, "ding", 1.0)
    T.set(phone11.root, "location", lambda f: tuple(PH_POS + V(0.006 * math.sin(f * 2.9) * window(f, ring, ring + 30, 1, 6),
                                                               0, 0.004 * math.sin(f * 3.7) * window(f, ring, ring + 30, 1, 6))),
          ring, N)
    T.set(phone11.root, "scale", lambda f: (0.5 * (1 + 0.08 * window(f, ring, ring + 8, 2, 6)),) * 3, ring, ring + 9)
    T.set(phone11.root, "scale", lambda f: (0.5 * pop(f, f0_11 - 30, 1),) * 3, 0, 1)
    T.set(phone11.root, "scale", lambda f: (0, 0, 0) if f < f0_11 - 6 else (0.5, 0.5, 0.5), 0, f0_11 - 5)
    PR.flash(T, coll, "phoneflash", tuple(PH_POS + V(0, -0.1, 0)), ring, 10, 0.2, L.TURQ, 160)
    PR.shock_ring(T, coll, "phonering", tuple(PH_POS + V(0, -0.05, 0)), ring + 2, 14, 0.5, axis="Y")
    T.set(stand, "scale", lambda f: (0, 0, 0) if f < f0_11 - 6 else (1, 1, 1), 0, f0_11 - 5)
    shock = wf(10, "Oh") + 1
    C.reaction(T, coll, k, "schock", shock, hold=f1_11 - shock, seed=11, hat=False)
    W.cam.shakes.append((shock, 0.02, 8))
    land = S[11][0] + 14

    def hatz(f):
        if f < shock:
            return 0.0
        if f < land - 10:
            return 1.9 * ease_out((f - shock) / 10)
        return 1.9 * (1 - ease_in((f - (land - 10)) / 10)) if f < land else 0.0
    T.add(k.hat, "location", lambda f: (0, 0, hatz(f)), shock, land + 1)
    T.add(k.hat, "rotation_euler", lambda f: (0.4 * math.sin((f - shock) * 0.3), 0, 0.25 * (f - shock)) if f < land else (0, 0, 0),
          shock, land + 1)
    T.mul(k.hat, "scale", lambda f: (1, 1, 1 - 0.2 * spring((f - land) / FPS, 4, 0.3)), land, land + 20)
    C.kalle_look(T, k, lambda f: PH_POS, f0_11, shock + 6, 1.0)
    A11 = (TH.p(0.05, -3.4, 2.05), TH.p(0.0, 0.2, 1.9), 40.0)
    face11 = V(K_TH) + V(0, -0.25, 1.98)

    def shot11(f):
        if f < shock:
            return (A11[0], A11[1], lerp(40, 42, (f - f0_11) / max(1, shock - f0_11)))
        t = ease_out((f - shock) / 5)
        return (A11[0].lerp(face11 + V(0.02, -3.0, 0.03), t), A11[1].lerp(face11, t), lerp(42, 46, t))
    cam.add_shot(f0_11, f1_11, shot11)

    # =================================================================== SZENE 12 – Jubel, Loop
    f0_12, f1_12 = S[11]
    jub = f0_12 + 6
    C.reaction(T, coll, k, "jubel", jub, hold=f1_12 - jub - 6, speaking=True, seed=12, hat=False)
    gone = f0_12 + 2
    for i, sl in enumerate(slips.slips[:11]):
        T.set(sl, "scale", lambda f, i=i: (unpop(f, gone + i % 4, 5),) * 3, gone - 1, gone + 10)
    PR.burst(T, coll, "slipspuff", "puff", tuple(slips.root.location + V(0, 0, 0.1)), gone + 2, 10, 120,
             speed=(0.5, 1.0), up=0.6, gravity=-0.3, life=(14, 22), size=(0.6, 1.2), drag=3.0)
    PR.flash(T, coll, "lapflash", tuple(laptop.root.location + V(0, 0.05, 0.25)), web_on - 1, 8, 0.25, L.YELLOW, 120)
    c.cue(web_on, "pop", 0.6)
    s1_pos = shot_lerp(S[0][0], S[0][1], A1, B1, ease_out)(0)
    end_from = (face11 + V(0.02, -3.0, 0.03), face11, 46.0)
    cam.add_shot(f0_12, N, shot_lerp(f0_12, N - 1, end_from, (s1_pos[0], s1_pos[1], s1_pos[2]), ease_in_out))
    W.loop_frames = 0

    # ------------------------------------------------------------ Byte-Gesicht
    face_s += [(S[4][0], "happy"), (fa - 3, "code"), (S[5][0] + 2, "happy"), (C0, "curious"), (seq[8], "happy"),
               (S[6][0], "code"), (S[7][0], "happy"), (S[8][0], "neutral"), (wf(8, "Marketing"), "happy"),
               (S[9][0], "neutral"), (wf(9, "tausend"), "surprised"), (S[10][0], "surprised"), (S[11][0], "happy")]
    C.byte_face(T, b, face_s, 0, N - 1)
    # Kamera-Fokus folgt Kalles Gesicht, ausser in Szene 4 (scharfe Code-Zeilen) und 6 (Ebenen/Handy)

    def focus(f):
        if S[3][0] <= f < S[3][1]:
            return ST.p(0.1, 0.45, 2.78)
        if S[5][0] <= f < S[5][1]:
            return P0 + V(0, 0, VIEWZ) if f < C0 + 6 else ph_pos
        if S[6][0] <= f < S[6][1]:
            return ST.p(0.3, 0.6, 2.8)
        return V(T.loc(k.root, f)) + V(0, -0.25, 1.95)
    W.cam.focus_fn = focus


def DEVH(nm):
    return PR.DEVICE[nm][1]
