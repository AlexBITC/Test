"""Regie fuer 'Meine KI macht jetzt meinen Job' (folge-12-kalle-vermieter). Szenen-Index 0..12 = Szene 1..13.

Bogen: 1-2 Byte (als drei Helfer) macht den Laden, Kalle steht rum; 3 Idee Vermieter (75.000 gespart); 4-6 Byte findet
die Wohnung im Stadtmodell (250.000, Miete 750), Kalle jubelt; 7-9 der Daempfer (Bank 200.000, Rate 1.000, Waage kippt,
-250 jeden Monat = negativer Cashflow); 10 stiller Moment am Abend; 11-12 Nachtsuche, Waage im Gleichgewicht;
13 Kalle entscheidet, Byte teilt sich wieder in drei Helfer (Loop auf Szene 1).
Kulissen: theke (frueh) -> buero -> studio -> theke (Abend) -> studio -> theke (frueh).
Jede Szene: Hauptaktion, Nebenbewegung (Dampf, Staub, Wellen, Autos, Pendeln, Licht) und Kamera.
Byte wirft tuerkises Licht (Lichtschein um ihn und Lichtfleck darunter), staerker, je groesser er wird.
Requisiten: assets/props/kalle_vermieter.py, Bildschirm: assets/screens/kalle_vermieter.py.
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
from anim import (ease_in, ease_out, ease_in_out, ease_out_back, window, pop, unpop, lerp, clamp01)
from choreo.common import Ctx, V
from choreo.mehlpreis import fahrt, push_in

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "props"))
import kalle_vermieter as KV  # noqa: E402
import brezel_geheimnis as BG  # noqa: E402

FPS = 30
zoom_gesicht = rueckfahrt = schwenk = fahrt
WEG = V(400, 0, 0)


def orbit(cen, r, z, lens, a0, a1, f0, f1):
    def fn(f):
        t = ease_in_out(clamp01((f - f0) / max(1, f1 - f0)))
        a = math.radians(lerp(a0, a1, t))
        return (cen + V(r * math.sin(a), -r * math.cos(a), z - cen.z), cen, lens)
    return fn


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    TH, BU, ST = c.sets["theke"], c.sets["buero"], c.sets["studio"]
    sc = c.sc
    S = [(s["f0"], s["f1"]) for s in sc]
    coll = W.coll
    cam = W.cam
    TOP = TH.top_z

    def hl(i, n=0):
        ws = [w["f0"] for w in sc[i]["words"] if w["hl"]]
        return ws[min(n, len(ws) - 1)] if ws else sc[i]["f0"] + 6

    def wd(i, core, nth=1):
        n = 0
        for w in sc[i]["words"]:
            if w["w"].strip(".,!?:…").lower().startswith(core.lower()):
                n += 1
                if n == nth:
                    return w["f0"]
        return sc[i]["f0"] + 6

    def t(i, sek):
        """Zeitangabe relativ zum Szenenstart, an die Szenenlaenge angepasst (Visual-Angaben bei ~4,5 s Szenenlaenge)."""
        f0, f1 = S[i]
        return f0 + int(min(sek * FPS * max(1.0, (f1 - f0) / (4.5 * FPS)), f1 - f0 - 8))

    def cue(f, kind, g=1.0):
        c.cue(int(f), kind, g)

    W.loop_frames = 14
    cam.focus_fn = lambda f: Vector(cam.base(f)[1])          # Schaerfe immer auf dem Ziel der Einstellung
    W.anchors["kalle_face"] = L.empty("anchor_kalle_face", k.head, (0, -0.25, 0.28), coll)
    W.anchors["byte"] = b.body
    # Morgenlicht (kuehl-frisch) in den Theke-Szenen 1, 2, 13 - gleiches Licht am Anfang und Ende (Loop)
    W.licht_extra = [(S[0][0], S[1][1], "theke", "frueh"), (S[12][0], N + 1, "theke", "frueh")]

    # ------------------------------------------------------------ Grundbewegung
    C.kalle_idle(T, k, 0, N - 1, seed=7)
    C.byte_idle(T, b, 0, N - 1, seed=3, amp=0.02)
    C.byte_blinks(T, b, 0, N - 1, seed=11)
    C.antenna_spring(T, b, 2, N - 1)
    C.follow_through(T, k.hat, k.head, "rotation_euler", 2, 0.9, 3, 0, N - 1)
    C.follow_through(T, k.skirt, k.hips, "rotation_euler", 1, 1.2, 4, 0, N - 1)
    C.pose(T, k, "arms_rest", -10, None, 1, 1, weight=0.6, settle=False)
    for i, s in enumerate(sc):
        if s["sprecher"] == "kalle":
            C.kalle_lipsync(T, k, s, s["f0"], s["f1"])
        else:
            C.byte_speak(T, b, s, s["f0"], s["f1"])
        if i != 9:
            for w in s["words"]:
                if w["hl"]:
                    cam.punch.append(w["f0"])
    cam.drift_env = lambda f: min(1.0, f / 10.0, max(0.0, (N - 7 - f) / 10.0)) * (0.35 if S[9][0] <= f < S[9][1] else 1.0)
    for o in (b.body, b.root, k.root):
        T.set(o, "rotation_euler", lambda f: (0, 0, 0), 0, 1)
    k.cloth.scale = (0, 0, 0)
    T.mul(b.tip, "scale", lambda f: ((1 + 0.35 * max(0.0, math.sin(f * 0.35))),) * 3, 0, N - 1)    # Antenne pulsiert

    def setze(fig, f0, f1, loc, rz=0.0, s=1.0):
        T.set(fig.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(fig.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)
        T.set(fig.root, "scale", lambda f, s=s: (s, s, s), f0, f1)

    # ------------------------------------------------------------ Byte: Lichtschein (staerker, je groesser er wird)
    ls = KV.byte_lichtschein(coll, "bl", b.body)

    def flaeche(f):
        s_ = next((x for x in sc if x["f0"] <= f < x["f1"]), sc[-1])
        return {"theke": TOP + 0.005, "buero": 0.985, "studio": 0.012}[s_["set"]]

    # ============================================================ THEKE: Aufbau
    K_TH = V(TH.kalle)
    besen = KV.besen(coll, "besen")
    besen.root.location = TH.p(-1.85, -0.78, 0)
    besen.root.rotation_euler = (0.0, 0.22, 0.1)
    T.set(besen.root, "rotation_euler", lambda f: (0.0, 0.22 + 0.01 * math.sin(f * 0.05), 0.1), 0, N - 1)
    dampf_fn = lambda f: (1.0 if not (S[9][0] <= f < S[9][1]) else max(0.0, 1 - (f - S[9][0]) / (0.6 * (S[9][1] - S[9][0]))))  # noqa
    KV.dampf_loop(T, coll, "dampf_korb", TH.p(0.9, -0.42, TOP + 0.12), 0, N - 1, n=9, staerke_fn=dampf_fn)
    KV.mehlstaub(T, coll, "staub_th", TH.p(0.4, -0.2, 1.9), (1.2, 0.6, 0.6), 0, N - 1, count=34)
    KV.mehlwolke_sinkt(T, coll, "wolke_s1", TH.p(-0.9, -0.55, 1.75), S[0][0] + t(0, 1.6) - S[0][0], dauer=90)
    # Helfer-Bytes (wiederverwendet aus characters.Helper)
    H = [C.Helper(coll, 1, "scan"), C.Helper(coll, 2, "digits"), C.Helper(coll, 3, "feather")]
    for h in H:
        C.byte_idle(T, h, 0, N - 1, seed=20 + h.n, amp=0.025)
        C.byte_face(T, h, [(0, "neutral")], 0, N - 1)
        W.anchors[f"helper{h.n}"] = h.body
    hoerer = PR.telefonhoerer(coll, "hoerer")
    hoerer = getattr(hoerer, "root", hoerer)
    hoerer.parent = H[0].body
    hoerer.location = (0.24, -0.12, 0.0)
    hoerer.rotation_euler = (0.3, 0.6, 0.2)
    hoerer.scale = (2.0, 2.0, 2.0)
    lap = TH.objs["laptop"]
    # periodische Wege um Kalle (gleich in Szene 1 und 13 -> Loop)
    PER = 3.2 * FPS

    def weg(n, f):
        ph = 2 * math.pi * f / PER
        if n == 1:   # Telefon: rechts neben Kalle, wiegt sich beim Sprechen
            return TH.p(0.78 + 0.08 * math.sin(ph), -0.2 + 0.05 * math.cos(ph), 2.0 + 0.06 * math.sin(2 * ph))
        if n == 2:   # Laptop: schwebt ueber den Tasten
            return TH.p(0.42 + 0.05 * math.sin(2 * ph), -0.62, TOP + 0.5 + 0.03 * math.sin(4 * ph))
        u = (f % PER) / PER   # Tueten: vom Regal zum Stapel und zurueck
        a, z = TH.p(-1.5, 1.2, 1.7), TH.p(-0.8, -0.55, TOP + 1.25)
        q = ease_in_out(u * 2) if u < 0.5 else ease_in_out((1 - u) * 2)
        return a.lerp(z, q) + V(0, 0, 0.25 * math.sin(math.pi * q))
    f_merge = S[1][0] + 6
    f_split = t(12, 1.5)
    for h in H:
        T.set(h.root, "location", lambda f, h=h: tuple(weg(h.n, f)), 0, N - 1)
        T.set(h.root, "scale", lambda f, h=h: (0.62,) * 3 if (f < f_merge or f >= f_split + 10) else (0.0,) * 3, 0, N - 1)
    # Tueten landen mit Squash (Helfer 3), Kalle greift ins Leere
    tueten = []
    for j in range(4):
        tu = BG.papiertuete(coll, f"tuete{j}")
        tueten.append(tu)
    land = [int(PER * (0.5 + j)) for j in range(4)]           # Ankunft am Stapel

    def tuete_da(j, f):
        if f < S[1][1]:
            return j == 0 or f >= land[j - 1] if j > 0 else True
        if f >= S[12][0]:
            return j == 0
        return False
    for j, tu in enumerate(tueten):
        pos = TH.p(-0.8, -0.55, TOP + 0.265 * j)
        T.set(tu.root, "location", lambda f, pos=pos: tuple(pos), 0, N - 1)
        T.set(tu.root, "scale", lambda f, j=j: (1, 1, 1) if tuete_da(j, f) else (0, 0, 0), 0, N - 1)
        if j > 0:
            KV.landen(T, tu.root, land[j - 1], staerke=0.3, dauer=10)
    greif = t(0, 1.5)
    C.pose(T, k, {"sh_R": (-1.35, 0.35, 0.25), "el_R": (-0.35, 0, 0), "hips": (0.05, 0, 0)}, greif - 6, greif + 16, 6, 10)
    C.kalle_look(T, k, lambda f: TH.p(-0.8, -0.55, TOP + 0.6), greif - 8, greif + 22, ramp=4)
    # Laptop-Tasten leuchten tuerkis (Helfer 2 tippt)
    if getattr(lap, "screen", None) is not None and lap.screen.active_material is not None:
        m_scr = L.unique_mat(lap.screen.active_material, "kv_lapscreen")
        lap.screen.data.materials.clear()
        lap.screen.data.materials.append(m_scr)
        tq, dk = L.srgb("#2EE6D6"), L.srgb("#1C3A48")
        T.set(m_scr, "diffuse_color", lambda f: tq if (int(f / 3) % 3) else dk, 0, N - 1)

    # ------------------------------------------------------------ Szene 1: Kalle steht nur rum
    f1a, f1b = S[0]
    setze(k, 0, S[2][0], K_TH, 0.0)
    T.set(b.root, "scale", lambda f: (0, 0, 0), 0, f_merge)
    T.set(b.root, "location", lambda f: tuple(TH.p(0.8, -0.45, 2.05)), 0, S[2][0])
    C.kalle_react(T, k, "zweifel", hl(0), hold=f1b - hl(0) - 4, speaking=True, hat=False)
    A1 = (TH.p(0.35, -3.35, 1.72), K_TH + V(0.05, 0, 1.62), 30.0)
    B1 = (TH.p(0.25, -2.55, 1.78), K_TH + V(0.02, 0, 1.72), 38.0)
    cam.add_shot(f1a, f1b, fahrt(f1a, f1b, A1, B1, ease=ease_in_out))

    # ------------------------------------------------------------ Szene 2: Helfer verschmelzen zu Byte
    f2a, f2b = S[1]
    m_pos = TH.p(0.8, -0.45, 2.05)
    for h in H:
        p_fn = lambda f, h=h: weg(h.n, f)                                          # noqa: E731

        def spirale(f, h=h, p_fn=p_fn):
            u = clamp01((f - f2a + 4) / 12)
            a = 2 * math.pi * (h.n / 3 + 1.5 * u)
            ziel = m_pos + V(0.5 * (1 - u) * math.cos(a), 0.3 * (1 - u) * math.sin(a), 0)
            return tuple(Vector(p_fn(f)).lerp(ziel, ease_in(u)))
        T.set(h.root, "location", spirale, f2a - 4, f_merge + 10)
    cue(f_merge - 2, "whoosh", 0.8)
    T.set(b.root, "scale", lambda f: (1.25 * pop(f, f_merge, 9, 1.18),) * 3 if f < f2b + 1 else (1.25,) * 3, f_merge - 1, f2b + 2)
    KV.lichtring_welle(T, coll, "ring_s2", TH.p(0.6, -0.32, TOP + 0.01), f_merge + 2, dauer=20, r_end=2.0)
    PR.burst(T, coll, "funken_s2", "sparkt", tuple(m_pos), f_merge, 20, 21, speed=(0.8, 1.8), gravity=-1.0, life=(12, 20))
    C.byte_face(T, b, [(f_merge, "jubel"), (f_merge + 30, "neutral")], f_merge, f2b)
    schild = KV.schild_text(coll, "erledigt", "Alles erledigt", breite=0.62, hoehe=0.16, size=0.075)
    schild.root.location = TH.p(-1.18, -0.42, TOP + 0.5)
    f_sch = t(1, 1.5)
    KV.schild_klappen(T, schild.root, f_sch, f_aus=S[2][0] - 2)
    cue(f_sch, "pop", 0.5)
    gruen = tuple(schild.mat.diffuse_color)
    T.set(schild.mat, "diffuse_color", lambda f: gruen if (int((f - f_sch) / 8) % 2 == 0) else tuple(x * 0.6 for x in gruen[:3]) + (1,),
          f_sch, S[2][0])
    C.kalle_look(T, k, lambda f: m_pos, f_merge, f2b, ramp=5)
    C.kalle_react(T, k, "staunen", f_merge + 2, hold=20, hat=False)
    A2 = B1
    B2 = (TH.p(0.3, -3.6, 1.85), TH.p(0.05, -0.1, 1.6), 28.0)
    cam.add_shot(f2a, f2b, rueckfahrt(f2a + 4, f2b - 4, A2, B2))

    # ============================================================ BUERO (Szene 3): Sparbuch, Muenzsaeule 75.000
    f3a, f3b = S[2]
    cam.whips.append((f3a, 1))
    cue(f3a - 2, "whoosh", 0.6)
    K_BU = BU.p(0.62, 0.62, 0)
    setze(k, f3a, S[3][0], K_BU, 0.0)
    BU.objs["laptop"].root.scale = (0, 0, 0)
    sb = KV.sparbuch(coll, "sparbuch_bu")
    sb_ziel = BU.p(0.05, -0.2, 0.985)
    sb_start = BU.p(1.2, 0.1, 0.62)
    knall = f3a + 10
    T.set(sb.root, "location", lambda f: tuple(sb_start.lerp(sb_ziel, ease_in(clamp01((f - f3a) / 10))) +
                                               V(0, 0, 0.35 * math.sin(math.pi * clamp01((f - f3a) / 10)))), f3a - 1, knall + 1)
    T.set(sb.root, "scale", lambda f: (1.6,) * 3 if f3a <= f < f3b + 2 else (0, 0, 0), 0, N - 1)
    KV.landen(T, sb.root, knall, staerke=0.4, dauer=10)
    cue(knall, "pop", 0.7)
    C.pose(T, k, {"sh_R": (-1.6, 0.2, 0.2), "el_R": (-0.5, 0, 0)}, f3a - 2, knall + 2, 4, 6)
    PR.burst(T, coll, "papiere", "confetti_#F5F1E8", tuple(sb_ziel + V(0, 0, 0.05)), knall, 12, 31, speed=(0.8, 1.6), up=1.6,
             gravity=-1.5, life=(26, 36), size=(2.4, 3.4), drag=1.6, spin=6.0, flutter=0.9, wobble=0.05)
    saeule = KV.muenzsaeule_gruen(coll, "saeule", n=24)
    saeule.root.location = sb_ziel + V(0.0, 0.0, 0.05)
    s0 = t(2, 0.8)
    s1 = min(f3b - 18, s0 + 40)
    for j, co in enumerate(saeule.coins):
        fj = s0 + int((s1 - s0) * j / len(saeule.coins))
        T.set(co, "scale", lambda f, fj=fj: (pop(f, fj, 5, 1.2),) * 3 if f3a <= f < f3b + 2 else (0, 0, 0), 0, N - 1)
    T.set(saeule.coins[-1], "rotation_euler", lambda f: (0, 0, f * 0.25), 0, N - 1)
    T.set(saeule.top, "location", lambda f: (0, 0, 0.03 * len(saeule.coins) * clamp01((f - s0) / max(1, s1 - s0)) + 0.18), 0, N - 1)
    W.anchors["saeule_top"] = saeule.top
    W.labels.append({"anchor": "saeule_top", "f0": s0, "f1": f3b - 2, "count_f0": s0, "count_f1": s1, "from": 0, "to": 75000,
                     "fmt": "{} €", "dy": -40})
    for j in range(0, 24, 6):
        cue(s0 + int((s1 - s0) * j / 24), "pop", 0.35)
    cue(s1, "pop", 0.6)
    C.kalle_react(T, k, "jubel", hl(2), hold=f3b - hl(2) - 2, speaking=True, hat=False)
    C.pose(T, k, "hands_up", s1 - 2, f3b, 5, 6)
    T.add(k.hat, "location", lambda f: (0, 0, 0.12 * max(0.0, math.sin(math.pi * clamp01((f - s1) / 8)))), s1, s1 + 9)
    setze(b, f3a, S[3][0], BU.p(1.55, 0.35, 2.0), 0.0, 1.25)
    C.byte_face(T, b, [(f3a, "jubel")], f3a, f3b)
    KV.mehlstaub(T, coll, "staub_bu", BU.p(0.6, 0.0, 1.6), (0.9, 0.6, 0.6), f3a, f3b, count=24, seed=41)
    cen3 = BU.p(0.4, 0.1, 1.45)
    cam.add_shot(f3a, f3b, orbit(cen3, 3.4, 2.0, 30, -22, 16, f3a, f3b))

    # ============================================================ STUDIO: Stadtmodell
    M0 = ST.p(0.15, 0.55, 0.72)
    sm = KV.stadtmodell_esslingen(coll, "stadt")
    sm.root.location = M0
    sm.root.scale = (0.95, 0.95, 0.95)
    sockel = L.box("stadt_sockel", (3.0, 2.0, 0.72), L.mat("stadt_sockel", "#262246", 0.6), None, M0 - V(0, 0, 0.36), coll, bevel=0.04)
    f4a, f4b = S[3]
    s_vis = lambda f: (S[3][0] - 2 <= f < S[8][1] + 2) or (S[10][0] - 2 <= f < S[11][1] + 2)    # noqa: E731
    T.set(sockel, "scale", lambda f: (1, 1, (ease_out_back(clamp01((f - f4a) / 10), 1.6) if f < f4a + 10 else 1.0)) if s_vis(f) else (0, 0, 0),
          0, N - 1)
    T.set(sm.root, "scale", lambda f: (0.95,) * 3 if s_vis(f) else (0, 0, 0), 0, N - 1)
    KV.aufbauen(T, sm, f4a + 6, dauer=int(min(40, 1.4 * FPS)), f1=N - 1)
    KV.leben(T, sm, 0, N - 1)
    bpy.context.view_layer.update()

    def welt(o, dz=0.0):
        loc = o.location
        return M0 + V(loc.x * 0.95, loc.y * 0.95, (loc.z + dz) * 0.95)
    # Scan-Linie (Szene 4 und Szene 11 in Schleife)
    m_scan = L.mat("scanlinie", "#2EE6D6", 0.3, emit="#2EE6D6", strength=4.0, alpha=0.45)
    scan = L.box("scanlinie", (3.1, 0.03, 0.22), m_scan, None, M0, coll)
    scan_a = t(3, 1.5)
    f11a, f11b = S[10]

    def scan_loc(f):
        if scan_a <= f < scan_a + 26:
            u = (f - scan_a) / 26
        elif f11a + 20 <= f < f11b:
            u = ((f - f11a - 20) % 40) / 40
        else:
            return tuple(M0 + V(0, 0, -5))
        return tuple(M0 + V(0, -1.0 + 2.0 * u, 0.25))
    T.set(scan, "location", scan_loc, 0, N - 1)
    T.set(scan, "scale", lambda f: (1, 1, 1) if (scan_a <= f < scan_a + 26 or f11a + 20 <= f < f11b) else (0, 0, 0), 0, N - 1)
    cue(scan_a, "whoosh", 0.7)
    # Pins auf dutzenden Haeusern (Szene 4), Domino-Erloeschen (Szene 5), nur einer bleibt
    f5a, f5b = S[4]
    ziel = sm.ziel
    hs = [h for h in sm.haeuser if h is not ziel][:22] + [ziel]
    pins = []
    for j, h in enumerate(hs):
        p = KV.preis_pin(coll, f"pin{j}")
        p.root.location = welt(h["obj"], h["dach"] + 0.02)
        u = (h["obj"].location.y + 1.0) / 2.0
        f_an = scan_a + int(26 * clamp01(u)) + 2
        f_aus = None if h is ziel else f5a + 2 + 2 * j
        KV.pin_an(T, p, f_an, f_aus=f_aus if f_aus is not None else S[5][1], s=1.1, f1=N - 1)
        pins.append(p)
        if j % 5 == 0:
            cue(f_an, "pop", 0.3)
    # Ziel-Haus hebt sich, leuchtet gelb, ein Fenster im 2. Stock geht an
    zo = ziel["obj"]
    z0 = zo.location.z
    T.set(zo, "location", lambda f: (zo.location.x, zo.location.y, z0 + (0.06 * ease_out_back(clamp01((f - f5a - 6) / 10), 2.0)
                                                                          if S[4][0] <= f < S[8][1] else 0.0)), 0, N - 1)
    m_gelb = L.mat("ziel_gelb", "#FFD86A", 0.4, emit="#FFD86A", strength=1.6)
    for o in zo.children:
        if o.name.endswith("_w") and o.type == "MESH":
            alt = o.active_material
            o.material_slots[0].link = "OBJECT"
            o.material_slots[0].material = alt
            m_w = L.unique_mat(alt, "ziel_wand")
            o.material_slots[0].material = m_w
            base, gelb = tuple(m_w.diffuse_color), tuple(m_gelb.diffuse_color)
            T.set(m_w, "diffuse_color", lambda f, base=base, gelb=gelb: gelb if S[4][0] + 6 <= f < S[8][1] else base, 0, N - 1)
    fen2 = ziel["fenster"][2]
    m_f2 = L.mat("ziel_fenster", "#FFF2B0", 0.3, emit="#FFF2B0", strength=3.0)
    licht2 = L.box("ziel_licht", (0.045, 0.006, 0.04), m_f2, None, (0, 0, 0), coll)
    T.set(licht2, "location", lambda f: tuple(welt(zo) + V(fen2.location.x * 0.95, fen2.location.y * 0.95 - 0.004,
                                                           (fen2.location.z + z0) * 0.95 + (0.06 * 0.95 if f >= f5a + 16 else 0))), 0, N - 1)
    T.set(licht2, "scale", lambda f: (1, 1, 1) if S[4][0] + 12 <= f < S[8][1] else (0, 0, 0), 0, N - 1)
    haus_w = welt(zo, 0.0)
    W.anchors["haus"] = L.empty("anchor_haus", None, haus_w + V(0, 0, 0.3), coll)
    # Preisschild 250.000 und gruenes Schild Miete 750
    preis = KV.schild_text(coll, "preis250", "250.000 €", farbe="#F2B45A", breite=0.66, hoehe=0.2, size=0.11)
    preis.root.location = haus_w + V(0, -0.05, 0.42)
    f_p = t(4, 1.0)
    KV.schild_klappen(T, preis.root, f_p, f_aus=S[6][0] + 6)
    cue(f_p, "pop", 0.6)
    miete = KV.schild_text(coll, "miete750", "Miete 750 €", breite=0.7, hoehe=0.18, size=0.095)
    miete.root.location = haus_w + V(0, -0.05, 0.2)
    f_m = t(4, 2.0)
    KV.schild_klappen(T, miete.root, f_m, f_aus=S[6][0] + 6)
    T.add(miete.root, "rotation_euler", lambda f: (0, 0.12 * math.exp(-(f - f_m - 9) / 10) * math.sin((f - f_m - 9) * 0.7) if f > f_m + 9 else 0, 0),
          f_m, f_m + 60)
    cue(f_m, "pop", 0.6)
    # Byte im Studio
    K_ST = ST.p(1.95, -0.95, 0)
    B4 = M0 + V(-0.6, -1.0, 1.1)
    setze(k, S[3][0], S[9][0], K_ST, 0.55)
    setze(b, S[3][0], S[9][0], B4, 0.0, 1.3)
    T.set(b.root, "location", lambda f: tuple(B4.lerp(M0 + V(0.0, 0.0, 1.35), ease_in_out(clamp01((f - scan_a + 12) / 14)))), f4a, f4b)
    C.byte_face(T, b, [(f4a, "staunen"), (f5a, "neutral"), (S[6][0], "zweifel"), (S[9][0], "neutral")], f4a, S[9][0])
    T.set(b.root, "location", lambda f: tuple((M0 + V(0.0, 0.0, 1.35)).lerp(haus_w + V(-0.6, -0.5, 0.7), ease_in_out(clamp01((f - f5a) / 16)))),
          f5a, f5b)
    C.kalle_look(T, k, lambda f: haus_w + V(0, 0, 0.2), f4a, S[9][0], strength=0.8, ramp=6)
    # Kameras Szene 4 und 5
    cen = M0 + V(0, 0.1, 0.05)
    A4 = (M0 + V(-2.0, -4.2, 2.0), cen + V(0, 0, -1.25), 30.0)
    B4c = (M0 + V(1.4, -4.0, 2.2), cen + V(0, 0, -1.25), 30.0)
    cam.whips.append((f4a, -1))
    cue(f4a - 2, "whoosh", 0.5)
    cam.add_shot(f4a, f4b, fahrt(f4a, f4b, A4, B4c, ease=ease_in_out))
    A5 = (M0 + V(1.0, -4.0, 2.0), haus_w + V(0, 0, 0.05), 30.0)
    cam.add_shot(f5a, f5b, push_in(f5a, f5b, A5, k=0.35))

    # ------------------------------------------------------------ Szene 6: Kalle tippt aufs Haus, Muenzen fliegen
    f6a, f6b = S[5]
    T.set(k.root, "location", lambda f: tuple(K_ST.lerp(haus_w + V(0.85, -0.75, -0.72), ease_in_out(clamp01((f - f6a) / 12)))), f6a, S[6][1])
    T.set(k.root, "rotation_euler", lambda f: (0, 0, 0.55 + 0.35 * ease_in_out(clamp01((f - f6a) / 12))), f6a, S[6][1])
    tipp = f6a + 18
    C.pose(T, k, {"sh_L": (-1.6, -0.2, -0.2), "el_L": (-0.2, 0, 0), "hips": (0.25, 0, 0), "head": (0.12, 0, 0)}, f6a + 6, tipp + 8, 8, 8)
    T.add(zo, "rotation_euler", lambda f: (0.12 * math.exp(-(f - tipp) / 8) * math.sin((f - tipp) * 1.3), 0, 0) if f >= tipp else (0, 0, 0),
          tipp, tipp + 30)
    C.kalle_react(T, k, "jubel", hl(5), hold=f6b - hl(5) - 2, speaking=True, hat=False)
    fang = {"sh_R": (-2.2, 0.45, 0.2), "sh_L": (-2.2, -0.45, -0.2), "el_R": (-0.8, 0, 0), "el_L": (-0.8, 0, 0)}
    C.pose(T, k, fang, t(5, 0.8), S[6][0] + 10, 6, 10)
    muenzen = [PR.coin(coll, f"flug{j}") for j in range(9)]
    f7a, f7b = S[6]
    freeze = f7a
    kopf = lambda: haus_w + V(0.85, -0.75, 1.1)      # noqa: E731
    for j, mz in enumerate(muenzen):
        st = t(5, 0.8) + 4 * j
        dur = 22

        def zeit(f):            # Zeitlupe: ab Szene 7 frieren die Muenzen fast ein
            return f if f < freeze else freeze + 0.04 * (f - freeze)

        def ml(f, st=st, j=j):
            u = clamp01((zeit(f) - st) / dur)
            a, z = haus_w + V(0, 0, 0.3), kopf() + V(0.1 * math.sin(j), 0, 0.1 * math.cos(j))
            return tuple(a.lerp(z, u) + V(0, 0, 0.7 * math.sin(math.pi * u)))
        T.set(mz, "location", ml, st - 1, S[7][0])
        T.set(mz, "scale", lambda f, st=st: (1.1,) * 3 if st <= f < S[7][0] and (f < freeze or True) and not (f < freeze and f >= st + dur) else
              (0, 0, 0), 0, N - 1)
        T.set(mz, "rotation_euler", lambda f: (math.pi / 2, 0, zeit(f) * 0.4), st - 1, S[7][0])
    KV.konfetti_gruen(T, coll, "konf6", tuple(haus_w + V(0, 0, 0.5)), t(5, 0.9))
    K6 = haus_w + V(0.85, -0.75, -0.72)
    A6 = (K6 + V(-1.2, -2.9, 1.8), K6 + V(-0.2, 0, 1.45), 30.0)
    B6 = (K6 + V(-0.9, -2.4, 1.95), K6 + V(-0.05, 0.05, 1.72), 34.0)
    cam.whips.append((f6a, 1))
    cam.add_shot(f6a, f6b, zoom_gesicht(f6a, f6b, A6, B6))

    # ------------------------------------------------------------ Szene 7: Muenzen frieren ein, Byte warnt, Bank
    bank = KV.bank_gebaeude(coll, "bank", s=1.6)
    BANK = M0 + V(-1.95, -0.7, -0.72)
    bank_ein = t(6, 1.0)
    T.set(bank.root, "location", lambda f: tuple(BANK + V(-2.5 * (1 - ease_out(clamp01((f - bank_ein) / 14))), 0, 0)) if S[6][0] <= f < S[8][1]
          else tuple(WEG), 0, N - 1)
    bank.root.rotation_euler = (0, 0, 0.4)
    KV.landen(T, bank.root, bank_ein + 14, staerke=0.18, dauer=10)
    KV.teppich_ausrollen(T, bank, bank_ein + 16, dauer=14, f1=N - 1)
    KV.schild_klappen(T, bank.schild, bank_ein + 28, f_aus=S[8][1])
    cue(bank_ein + 28, "pop", 0.6)
    f_rate = t(6, 2.5)
    KV.schild_klappen(T, bank.rate, max(f_rate, bank_ein + 36), f_aus=S[8][1])
    cue(max(f_rate, bank_ein + 36), "pop", 0.6)
    T.set(b.root, "location", lambda f: tuple((haus_w + V(-0.6, -0.5, 0.7)).lerp(haus_w + V(0.35, -1.0, 0.95), ease_in_out(clamp01((f - f7a) / 10)))),
          f7a, f7b)
    orange = L.srgb("#FF9A3D")
    for mt in ls.mats:
        base = tuple(mt.diffuse_color)
        for kk in range(3):
            T.set(mt, "diffuse_color", lambda f, b0=base, kk=kk: orange[kk] if f7a + 2 <= f < f7a + 40 else b0[kk], 0, N - 1, index=kk)
    cam.add_shot(f7a, f7b, schwenk(f7a + 6, f7b - 6, (M0 + V(0.9, -3.4, 2.2), haus_w + V(0, 0, 0.1), 32.0),
                                   (M0 + V(-0.9, -3.8, 2.1), BANK + V(0.3, 0, 0.6), 30.0)))

    # ------------------------------------------------------------ Szene 8: Waage faellt, kippt nach links
    f8a, f8b = S[7]
    waage = KV.waage_kippt(coll, "waage")
    WAAGE = M0 + V(-0.75, -1.5, -0.72)
    fall = f8a + 2
    T.set(waage.root, "location", lambda f: tuple(WAAGE + V(0, 0, 3.5 * (1 - ease_in(clamp01((f - fall) / 9))))) if (S[7][0] <= f < S[8][1] or
          S[11][0] <= f < S[11][1]) else tuple(WEG), 0, N - 1)
    KV.landen(T, waage.root, fall + 9, staerke=0.25, dauer=12)
    kipp = t(7, 0.8)
    rot = KV.scheibe(coll, "s_rot", "1.000 €", "#D8323C", r=0.24)
    grn = KV.scheibe(coll, "s_gruen", "750 €", "#2FB86E", r=0.17)
    for sch, hang, st in ((rot, waage.schalen[0], fall + 12), (grn, waage.schalen[1], fall + 18)):
        sch.root.parent = hang
        sch.root.location = (0, 0, -0.55)
        T.set(sch.root, "location", lambda f, st=st: (0, 0, -0.55 + 1.2 * (1 - ease_in(clamp01((f - st + 6) / 6)))), st - 7, st + 1)
        T.set(sch.root, "scale", lambda f, st=st: (1, 1, 1) if (st - 6 <= f < S[8][1]) else (0, 0, 0), 0, N - 1)
        KV.landen(T, sch.root, st, staerke=0.35, dauer=10)
        cue(st, "pop", 0.45)
    T.add(grn.root, "location", lambda f: (0, 0, 0.3 * max(0.0, math.sin(math.pi * clamp01((f - kipp) / 10)))), kipp, kipp + 11)
    KV.landen(T, grn.root, kipp + 10, staerke=0.3, dauer=8)
    cue(kipp, "buzz", 0.8)
    PR.burst(T, coll, "staub_waage", "puff", tuple(WAAGE + V(-0.86, 0, 0.9)), kipp + 2, 14, 51, speed=(0.6, 1.2), up=0.5, gravity=-0.4,
             life=(18, 26), size=(1.6, 2.6), drag=2.0, ring=True)
    f12a, f12b = S[11]

    def winkel(f):
        if f < kipp:
            return 0.04 * math.sin((f - fall) * 0.5) * math.exp(-(f - fall) / 10)
        if f < S[8][1]:
            return 0.32 * ease_out_back(clamp01((f - kipp) / 7), 2.0) + 0.02 * math.sin(f * 0.2)
        if f12a <= f:                                   # Szene 12: pendelt langsam aus bis ins Gleichgewicht
            return 0.25 * math.exp(-(f - f12a) / 22) * math.cos((f - f12a) * 0.22)
        return 0.0
    KV.kippen(T, waage, winkel, 0, N - 1)
    C.kalle_react(T, k, "schock", hl(7), hold=f8b - hl(7), speaking=True, hat=False)
    C.pose(T, k, "glasses", kipp, f8b, 4, 6)
    T.set(k.root, "location", lambda f: tuple(K_ST), f8a, S[9][0])
    T.set(k.root, "rotation_euler", lambda f: (0, 0, 0.55), f8a, S[9][0])
    T.set(b.root, "location", lambda f: tuple(WAAGE + V(0.9, -0.3, 2.0)), f8a, S[9][0])
    A8 = (K_ST + V(-1.9, -3.4, 1.9), WAAGE + V(0.8, 0, 1.1), 30.0)
    B8 = (K_ST + V(-0.8, -2.3, 1.95), K_ST + V(0.05, 0.1, 1.78), 32.0)
    cam.whips.append((f8a, -1))
    zoom8 = min(kipp + 14, f8b - 20)
    cam.add_shot(f8a, f8b, lambda f: fahrt(zoom8, zoom8 + 6, A8, B8, ease=ease_out)(f))

    # ------------------------------------------------------------ Szene 9: Portemonnaie tropft, -250
    f9a, f9b = S[8]
    pm = KV.portemonnaie_tropft(coll, "pm", n=10)
    pm.root.parent = waage.schalen[0]
    pm.root.location = (0, 0, -0.85)
    T.set(pm.root, "scale", lambda f: (1.6,) * 3 if f9a <= f < f9b + 2 else (0, 0, 0), 0, N - 1)
    T.set(pm.root, "rotation_euler", lambda f: (0, 0, 0.08 * math.sin(f * 0.12)), 0, N - 1)
    bpy.context.view_layer.update()
    pm_w = WAAGE + V(-0.86 * math.cos(0.32), 0, 1.5 - 0.86 * math.sin(0.32) - 0.85 * 1.0)
    for j, mz in enumerate(pm.muenzen):
        st = f9a + 4 + 11 * j
        if st > f9b - 8:
            mz.scale = (0, 0, 0)
            continue
        fall_n = 10

        def mloc(f, st=st, j=j):
            u = clamp01((f - st) / fall_n)
            z = pm_w.z - 0.1 - (pm_w.z - 0.12) * u * u
            if f > st + fall_n:
                z = 0.03 + 0.05 * max(0.0, math.sin(math.pi * clamp01((f - st - fall_n) / 6)))
            return (pm_w.x + 0.06 * (j % 3 - 1), pm_w.y - 0.05 * (j % 2), z)
        T.set(mz, "location", mloc, st - 1, N - 1)
        T.set(mz, "scale", lambda f, st=st: (1.2,) * 3 if st <= f < f9b + 2 else (0, 0, 0), 0, N - 1)
        T.set(mz, "rotation_euler", lambda f, st=st: (math.pi / 2 * (1 - clamp01((f - st) / fall_n)), 0, f * 0.3), st - 1, N - 1)
        KV.landen(T, mz, st + fall_n, staerke=0.4, dauer=8)
        cue(st + fall_n, "pop", 0.22)
    et = KV.etikett_kette(coll, "etikett")
    ET = WAAGE + V(0.5, -0.45, 1.25)
    f_et = t(8, 1.5)
    T.set(et.root, "location", lambda f: tuple(ET + V(1.4 * (1 - ease_out(clamp01((f - f_et) / 10))), 0, 0)) if f9a <= f < f9b + 2 else tuple(WEG),
          0, N - 1)
    KV.schwingen(T, et.root, f_et, f9b + 2, amp=0.4)
    cue(f_et, "pop", 0.5)
    # Studio-Licht einen Tick kuehler
    for nm in ("studio_floor", "studio_back"):
        o = bpy.data.objects.get(nm)
        if o is not None and o.active_material is not None:
            mt = o.active_material
            for kk, fac in enumerate((0.88, 0.94, 1.08)):
                T.mul(mt, "diffuse_color", lambda f, fac=fac: 1 + (fac - 1) * clamp01((f - f9a - 10) / 20) if f9a <= f < f9b else 1.0,
                      f9a, f9b, index=kk)
    cam.add_shot(f9a, f9b, fahrt(f9a, f9b, (WAAGE + V(0.5, -3.8, 2.3), WAAGE + V(0.2, 0, 1.2), 30.0),
                                 (WAAGE + V(0.4, -3.4, 1.3), pm_w + V(0.25, 0, -0.15), 30.0)))

    # ============================================================ THEKE Abend (Szene 10): leiser Moment
    f10a, f10b = S[9]
    cam.whips.append((f10a, 1))
    setze(k, f10a, S[10][0], K_TH + V(-0.15, 0, 0), 0.15)
    C.pose(T, k, {"hips": (-0.18, 0, 0), "head": (0.18, 0, 0), "sh_R": (-0.7, 0.2, 0.2), "el_R": (-0.9, 0, 0)}, f10a, f10b, 10, 10)
    C.kalle_react(T, k, "traurig", f10a + 10, hold=f10b - f10a - 12, speaking=True)
    setze(b, f10a, S[10][0], WEG)
    sb2 = KV.sparbuch(coll, "sparbuch_th")
    SB_TH = TH.p(-0.15, -0.55, TOP)
    T.set(sb2.root, "location", lambda f: tuple(SB_TH + V(0.0, -0.18 * ease_in_out(clamp01((f - f10a - 20) / 40)), 0)) if f < S[12][0] else
          tuple(SB_TH.lerp(K_TH + V(-0.05, -0.18, 0.95), ease_in_out(clamp01((f - S[12][0] - 8) / 14)))), 0, N - 1)
    T.set(sb2.root, "scale", lambda f: (1.5,) * 3 if f10a <= f < S[12][0] + 22 else (0, 0, 0), 0, N - 1)
    T.set(sb2.root, "rotation_euler", lambda f: (0, 0, 0.3), 0, N - 1)
    # Abendlicht: warm und gedaempft (Toenung), schraeger Lichtstrahl mit Staubkoernchen
    abend = (0.78, 0.62, 0.5)
    for mt in list(bpy.data.materials):
        if mt.name.startswith(("byte", "antenna", "helper", "spark", "screen", "bl_", "abendstrahl")):
            continue
        for kk in range(3):
            T.mul(mt, "diffuse_color", lambda f, kk=kk: abend[kk] if f10a <= f < f10b else 1.0, f10a - 1, f10b + 1, index=kk)
    strahl = L.box("abendstrahl", (0.7, 3.2, 0.02), L.mat("abendstrahl", "#FFC27A", 0.4, emit="#FFC27A", strength=1.5, alpha=0.16),
                   None, TH.p(-0.4, 0.6, 2.0), coll)
    strahl.rotation_euler = (0.65, 0.0, -0.55)
    T.set(strahl, "scale", lambda f: (1, 1, 1) if f10a <= f < f10b else (0, 0, 0), 0, N - 1)
    KV.mehlstaub(T, coll, "staub_abend", TH.p(-0.4, -0.2, 1.7), (0.5, 0.6, 0.6), f10a, f10b, count=30, seed=61)
    A10 = (TH.p(0.6, -3.0, 1.6), K_TH + V(-0.15, 0, 1.45), 32.0)
    cam.add_shot(f10a, f10b, push_in(f10a, f10b, A10, k=0.12))

    # ============================================================ STUDIO Nacht (Szene 11): Nachtsuche
    cam.whips.append((f11a, -1))
    KV.nacht(T, sm, f11a, 0, N - 1, dauer=18)
    setze(b, f11a, S[12][0], M0 + V(0, 0, 1.3), 0.0, 1.35)
    T.set(b.root, "location", lambda f: tuple(M0 + V(1.1 * math.cos((f - f11a) * 0.05), 0.7 * math.sin((f - f11a) * 0.05), 1.25)), f11a, f11b)
    C.byte_face(T, b, [(f11a, "staunen"), (f12a, "neutral")], f11a, S[12][0])
    rnd = random.Random(5)
    for j, p in enumerate(pins[:-1]):
        blinks = [f11a + 24 + rnd.randint(0, max(1, f11b - f11a - 40)) for _ in range(2)]
        T.set(p.root, "scale", lambda f, bl=blinks: (pop(f, bl[0], 5, 1.2) * unpop(f, bl[0] + 8, 5),) * 3 if bl[0] <= f < bl[0] + 14 else
              ((pop(f, bl[1], 5, 1.2) * unpop(f, bl[1] + 8, 5),) * 3 if bl[1] <= f < bl[1] + 14 else (0, 0, 0)), f11a, f11b)
    T.set(pins[-1].root, "scale", lambda f: (0, 0, 0), f11a, N - 1)
    setze(k, f11a, S[12][0], WEG)
    cam.add_shot(f11a, f11b, lambda f: (lambda p: (p[0], p[1] + V(0, 0, -1.5), p[2]))(orbit(M0 + V(0, 0.1, 0.1), 4.2, 2.3, 30, -25, 25, f11a, f11b)(f)))

    # ------------------------------------------------------------ Szene 12: Waage im Gleichgewicht, Haken, gruener Impuls
    T.set(waage.root, "location", lambda f: tuple(WAAGE + V(0, 0, 3.0 * (1 - ease_out(clamp01((f - f12a) / 10))))), f12a, f12b)
    gl_l = KV.scheibe(coll, "s_gl_l", "", "#2FB86E", r=0.2)
    gl_r = KV.scheibe(coll, "s_gl_r", "", "#2FB86E", r=0.2)
    for sch, hang in ((gl_l, waage.schalen[0]), (gl_r, waage.schalen[1])):
        sch.root.parent = hang
        sch.root.location = (0, 0, -0.55)
        T.set(sch.root, "scale", lambda f: (1, 1, 1) if f12a <= f < f12b + 2 else (0, 0, 0), 0, N - 1)
    haken = KV.haken_gruen(coll, "haken", s=0.32)
    haken.root.location = WAAGE + V(0, -0.15, 2.05)
    f_h = t(11, 1.5)
    T.set(haken.root, "scale", lambda f: (pop(f, f_h, 8, 1.25),) * 3 if f_h <= f < f12b + 2 else (0, 0, 0), 0, N - 1)
    cue(f_h, "ding", 0.7)
    KV.lichtring_welle(T, coll, "puls12", tuple(M0 + V(0, 0, 0.04)), f_h + 2, dauer=24, r_end=2.0, farbe="#3DDC84")
    T.set(b.root, "location", lambda f: tuple(WAAGE + V(1.0, -0.2, 2.1)), f12a, f12b)
    cam.add_shot(f12a, f12b, push_in(f12a, f12b, (WAAGE + V(0.7, -3.4, 2.0), WAAGE + V(0, 0, 1.2), 32.0), k=0.25))

    # ============================================================ THEKE Morgen (Szene 13): Kalle entscheidet, Loop
    f13a, f13b = S[12]
    setze(k, f13a, N, K_TH, 0.0)
    C.kalle_react(T, k, "jubel", hl(12), hold=f13b - hl(12) - 20, speaking=True, hat=False)
    C.pose(T, k, {"hips": (0.08, 0, 0), "head": (-0.06, 0, 0)}, f13a, f13b - 18, 8, 12)        # richtet sich auf
    C.pose(T, k, {"sh_R": (-1.3, 0.2, 0.2), "el_R": (-0.9, 0, 0)}, f13a + 4, f13a + 26, 6, 8)   # Sparbuch in die Schuerze
    T.set(b.root, "location", lambda f: tuple(m_pos), f13a, N)
    T.set(b.root, "scale", lambda f: (1.25 * (unpop(f, f_split - 2, 6) if f >= f_split - 2 else 1),) * 3 if f < f_split + 6 else (0, 0, 0),
          f13a, N)
    cue(f_split - 2, "whoosh", 0.8)
    KV.lichtring_welle(T, coll, "ring_s13", TH.p(0.6, -0.32, TOP + 0.01), f_split, dauer=18, r_end=1.6)
    for h in H:
        def aus_byte(f, h=h):
            u = clamp01((f - f_split) / 14)
            return tuple(m_pos.lerp(weg(h.n, f), ease_out(u)))
        T.set(h.root, "location", aus_byte, f_split - 1, f_split + 14)
        T.set(h.root, "scale", lambda f: (0.62 * pop(f, f_split, 8, 1.15),) * 3, f_split - 1, f_split + 9)
    C.byte_face(T, b, [(f13a, "jubel")], f13a, N)
    # Kamera: Rueckfahrt exakt auf die Startposition von Szene 1
    A13 = (TH.p(0.25, -2.4, 1.78), K_TH + V(0.02, 0, 1.72), 40.0)
    cam.add_shot(f13a, f13b, fahrt(f13a + 4, f13b - 6, A13, A1, ease=ease_in_out))

    # ============================================================ Byte-Lichtschein ueber die ganze Folge
    def staerke(f):
        if f < f_merge:
            return 0.0
        if S[9][0] <= f < S[10][0]:
            return 0.0
        base = 1.0 + 0.6 * clamp01((f - f_merge) / 30)
        if S[3][0] <= f < S[4][0] and f >= scan_a:
            base += 0.4 * window(f, scan_a, scan_a + 30, 4, 10)
        if S[11][0] <= f < S[11][1] and f >= f_h:
            base += 0.5 * window(f, f_h, f_h + 30, 3, 14)
        if f >= f_split:
            return 0.0
        return base * (1 + 0.08 * math.sin(f * 0.3))
    lichtpos = lambda f: (lambda p: (p[0], p[1], flaeche(f)))(T.loc(b.root, f))      # noqa: E731
    KV.lichtschein_steuern(T, ls, staerke, lichtpos, 0, N - 1)
