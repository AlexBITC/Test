"""Regie fuer 'Ein Video – und der Laden platzt' (folge-13-laden-platzt). Szenen-Index 0..11 = Szene 1..12.

Bogen: 1 heute: Schlange durch die offene Tuer bis auf den Gehweg, Kalle reicht hektisch Tueten; 2 Zurueckspulen auf
gestern (leer, entsaettigt, Stempel GESTERN); 3 Byte am Schaufenster, Passanten mit Fragezeichen; 4 Kalle mit Teigstrang;
5 Linse klappt auf, Brezel in Zeitlupe (FILMEN); 6-7 Studio: Zeitleiste, Lichtschnitt, drei Kacheln -> Hochkant-Handy
(SCHNEIDEN); 8 Buero am Abend: 19:00, Papierflieger aus dem Fenster (POSTEN); 9 Morgen: Handy vibriert, Zaehler 50.000;
10 Studio: Mini-Baeckerei, Wellenringe, Figuren; 11 Vorspulen auf heute (Stempel HEUTE), Kunden stroemen herein, Korb hoch;
12 Byte zwinkert, Haken 'Mehl bestellt', Rueckfahrt exakt auf die Startposition von Szene 1 (Loop).
Jede Szene: Hauptaktion, Nebenbewegung (Dampf, Mehlstaub, Glocke, Wippen, Licht, Baum) und Kamera.
Byte wirft tuerkises Licht (Lichtschein, Lichtfleck darunter, Schimmer auf Scheibe und auf Kalle in seiner Naehe).
Requisiten: assets/props/laden_platzt.py, Bildschirm (Studio-Screen und Laptop-Displays): assets/screens/laden_platzt.py.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector, Matrix

import characters as C
import look as L
import props as PR
from anim import ease_in, ease_out, ease_in_out, ease_out_back, window, pop, unpop, lerp, clamp01, spring
from choreo.common import Ctx, V, path
from choreo.mehlpreis import fahrt, push_in, harter_zoom
from choreo.viral import laptop_display

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "props"))
import laden_platzt as LP  # noqa: E402
import viral as VP  # noqa: E402
import kalle_vermieter as KV  # noqa: E402
import brezel_geheimnis as BG  # noqa: E402

FPS = 30
WEG = V(400, 0, 0)
zoom_gesicht = rueckfahrt = schwenk = fahrt


def orbit(cen, r, z, lens, a0, a1, f0, f1):
    def fn(f):
        t = ease_in_out(clamp01((f - f0) / max(1, f1 - f0)))
        a = math.radians(lerp(a0, a1, t))
        return (cen + V(r * math.sin(a), -r * math.cos(a), z - cen.z), cen, lens)
    return fn


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    TH, ST, BU = c.sets["theke"], c.sets["studio"], c.sets["buero"]
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
    cam.focus_fn = lambda f: Vector(cam.base(f)[1])
    W.anchors["kalle_face"] = L.empty("anchor_kalle_face", k.head, (0, -0.25, 0.28), coll)
    W.anchors["byte"] = b.body
    W.uebergaenge = [(S[1][0], "zurueck"), (S[10][0], "vor")]        # Pixel-Flackern beim Zurueck- und Vorspulen

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
        if i not in (1, 3):                                   # leise Zeilen ohne Punch-in
            for w in s["words"]:
                if w["hl"]:
                    cam.punch.append(w["f0"])
    cam.drift_env = lambda f: min(1.0, f / 10.0, max(0.0, (N - 7 - f) / 10.0))
    for o in (b.body, b.root, k.root):
        T.set(o, "rotation_euler", lambda f: (0, 0, 0), 0, 1)
    if getattr(k, "cloth", None) is not None:
        k.cloth.scale = (0, 0, 0)

    def setze(fig, f0, f1, loc, rz=0.0, s=1.0):
        T.set(fig.root, "location", lambda f, loc=loc: tuple(loc), f0, f1)
        T.set(fig.root, "rotation_euler", lambda f, rz=rz: (0, 0, rz), f0, f1)
        T.set(fig.root, "scale", lambda f, s=s: (s, s, s), f0, f1)

    def szene(f):
        return next((j for j, x in enumerate(sc) if x["f0"] <= f < x["f1"]), len(sc) - 1)

    def tint(mats, f0, f1, faktor, ramp=8):
        """Farbstimmung (Workbench): Objektfarben multiplikativ, mit weicher Rampe; ausserhalb unveraendert."""
        for m in mats:
            for kk in range(3):
                T.mul(m, "diffuse_color", lambda f, kk=kk: 1 + (faktor[kk] - 1) * window(f, f0, f1, ramp, ramp), f0, f1, index=kk)

    # Materialien von Byte (und seinem Licht) bleiben in Farbstimmungen unberuehrt
    byte_mats = set()
    for o in [b.root] + list(b.root.children_recursive):
        if getattr(o, "material_slots", None):
            for sl in o.material_slots:
                if sl.material:
                    byte_mats.add(sl.material.name)

    def welt_mats(ausnahmen=("fz_", "bl_", "kl_", "pf_", "hh_", "heart_", "sb_", "trail_", "screen_display", "lp_himmel",
                             "lp_wolke", "st_", "lichtring", "zl_schnitt", "dampf", "mehlwolke")):
        out = []
        for m in bpy.data.materials:
            if m.name in byte_mats or any(m.name.startswith(a) for a in ausnahmen):
                continue
            out.append(m)
        return out

    # ------------------------------------------------------------ Byte: tuerkises Licht
    ls = KV.byte_lichtschein(coll, "bl", b.body)
    K_TH = V(TH.kalle)
    K_SITZ = V(BU.kalle) + V(0.0, -0.1, -0.25)
    K_RZ = 0.42

    def flaeche(f, p):
        st = sc[szene(f)]["set"]
        if st == "theke":
            q = p - TH.o
            return TOP + 0.005 if abs(q.x) < 1.72 and -0.75 < q.y < 0.11 else 0.005
        if st == "buero":
            q = p - BU.o
            return 0.985 if -0.1 < q.x < 1.6 and -0.48 < q.y < 0.38 else 0.005
        return 0.012

    def b_pos(f):
        return V(T.loc(b.root, f))

    def staerke(f):
        i = szene(f)
        return {4: 1.45, 9: 1.35, 5: 1.2, 6: 1.2}.get(i, 1.0)
    KV.lichtschein_steuern(T, ls, staerke, lambda f: (lambda p: (p.x, p.y, flaeche(f, p)))(b_pos(f)), 0, N - 1)
    # tuerkiser Schimmer auf Kalle, wenn Byte nahe ist
    for mn in ("skin", "shirt", "apron", "hatwhite"):
        m = bpy.data.materials.get(mn)
        if m is None:
            continue
        for kk, g in enumerate((0.9, 1.06, 1.08)):
            T.mul(m, "diffuse_color", lambda f, g=g: 1 + (g - 1) * clamp01(1 - ((b_pos(f) - (V(T.loc(k.root, f)) + V(0, 0, 1.8))).length - 0.55) / 0.7),
                  0, N - 1, index=kk)

    # ============================================================ THEKE: Ladenseite, Glocke, Schlange
    lsd = LP.ladenseite(coll, "ls", TH, X=2.45)
    wr = bpy.data.objects.get("theke_wall_r")
    if wr is not None:
        wr.scale = (0, 0, 0)
    T.set(lsd.krone, "rotation_euler", lambda f: (0.05 * math.sin(2 * math.pi * f / (N / 22)), 0.04 * math.sin(2 * math.pi * f / (N / 17)), 0), 0, N - 1)
    # Byte-Licht faellt auf die Scheibe (Szene 3-4)
    g0 = tuple(lsd.m_glas.diffuse_color)
    tq = L.srgb(LP.TURQ)

    def glas(f, kk):
        d = (b_pos(f) - lsd.fenster_mitte).length
        w = clamp01(1 - (d - 0.35) / 0.8)
        if kk == 3:
            return g0[3] + 0.07 * w
        return lerp(g0[kk], tq[kk], 0.4 * w)
    for kk in range(4):
        T.set(lsd.m_glas, "diffuse_color", lambda f, kk=kk: glas(f, kk), 0, N - 1, index=kk)

    glocke = LP.tuerglocke(coll, "glocke")
    glocke.root.location = TH.p(2.33, -1.4, 2.62)
    glocke.root.rotation_euler = (0, 0, -math.pi / 2)
    glocke.root.scale = (1.5,) * 3
    f2a, f2b = S[1]
    f11a, f11b = S[10]

    def glocke_st(f):
        if f < f2a:
            return 1.0
        if f < f11a + 6:
            return 0.0 if f > f2a + 8 else 0.6 * (1 - (f - f2a) / 8)
        return min(1.0, (f - f11a - 6) / 6)
    LP.bimmeln(T, glocke, glocke_st, 0, N - 1)
    for f_ in list(range(0, f2a - 10, 38)) + list(range(f11a + 8, N - 20, 40)):
        cue(f_, "tuerglocke", 0.45)

    Q = [TH.p(0.32, -1.2, 0), TH.p(1.0, -1.32, 0), TH.p(1.75, -1.4, 0), TH.p(2.45, -1.4, 0), TH.p(3.2, -1.15, 0),
         TH.p(3.38, -0.25, 0), TH.p(3.45, 0.7, 0), TH.p(3.5, 1.6, 0), TH.p(3.55, 2.25, 0)]
    qpos, qrich, qlen = LP.pfad(Q)
    NK = 8
    SP = 0.78
    kunden = LP.kundenschlange(coll, "kunde", NK, seed=13)
    s_weg = qlen + 0.3
    s_far = qlen + 1.6
    ankunft = {}

    def s_fn(i, f):
        s0 = SP * i
        if f < f2a:
            return s0
        if f < f11a:
            st = f2a + 2 * (NK - 1 - i)
            if f < st:
                return s0
            s = s0 + 0.32 * (f - st)
            return s if s < s_weg else None
        st = f11a + 2 + 3 * i
        d = s_far - s0
        dur = max(8, int(d / 0.22))
        ankunft[i] = st + dur
        if f < st:
            return None
        return s_far - d * ease_out(clamp01((f - st) / dur))
    for i in range(NK):
        s_fn(i, f11a)                                          # Ankunftszeiten berechnen
    LP.schlange_bewegen(T, kunden, qpos, qrich, s_fn, 0, N - 1, s_weg=s_weg)
    for i, ku in enumerate(kunden):
        LP.landen(T, ku.root, ankunft[i], staerke=0.18, dauer=9)

    # Passanten (Szene 2-3): laufen draussen am Fenster vorbei, schauen nicht herein
    passanten = []
    for q, (col, dy) in enumerate((("#4E6B8A", 0.0), ("#B5524F", 1.7))):
        p_ = VP.kunde_mit_handy(coll, f"passant{q}", col, s=0.95, seed=40 + q, handy=False)
        st = f2a + 16
        y0 = 2.2 + dy
        weg = lambda f, st=st, y0=y0, q=q: TH.p(3.95 + 0.25 * q, y0 - 0.55 * max(0, f - st) / FPS, 0)    # noqa: E731
        T.set(p_.root, "location", lambda f, weg=weg: tuple(weg(f)), f2a, S[3][0])
        T.set(p_.root, "rotation_euler", lambda f: (0, 0, 0.0), f2a, S[3][0])
        T.set(p_.root, "scale", lambda f, st=st, weg=weg: (0.95,) * 3 if st <= f < S[3][0] and (weg(f) - TH.o).y < 2.2 else (0, 0, 0), 0, N - 1)
        T.add(p_.body, "location", lambda f, q=q: (0, 0, 0.04 * abs(math.sin(f * 0.42 + q))), f2a, S[3][0])
        T.add(p_.arm, "rotation_euler", lambda f, q=q: (0.5 * math.sin(f * 0.42 + q), 0, 0), f2a, S[3][0])
        T.add(p_.body, "rotation_euler", lambda f, q=q: (0, 0.05 * math.sin(f * 0.42 + q), 0), f2a, S[3][0])
        passanten.append((p_, weg, st))

    # ------------------------------------------------------------ Theke: Laptop, Korb, Tueten, Dampf, Staub
    lap = TH.objs["laptop"]
    laptop_display(lap)
    laptop_display(BU.objs["laptop"])
    LAP_SCR = TH.p(0.36, -0.25, TOP + 0.24)
    lap_out = LAP_SCR + V(0, -0.15, 0.02)
    korb = TH.objs["basket"]
    rolls = TH.objs.get("rolls", [])
    for j, r_ in enumerate(rolls):
        sc0 = tuple(r_.scale)
        T.set(r_, "scale", lambda f, j=j, sc0=sc0: sc0 if (j == 0 and S[1][0] <= f < S[5][0]) else (0, 0, 0), 0, N - 1)
    dampf_fn = lambda f: 1.0 if (f < f2a or f >= f11a) else 0.35        # noqa: E731
    KV.dampf_loop(T, coll, "dampf_korb", TH.p(0.9, -0.42, TOP + 0.14), 0, N - 1, n=10, staerke_fn=dampf_fn, hoehe=0.6)
    KV.mehlstaub(T, coll, "staub_th", TH.p(0.2, -0.3, 1.8), (1.4, 0.7, 0.6), 0, N - 1, count=36)
    KV.mehlstaub(T, coll, "staub_bu", BU.p(0.5, -0.1, 1.6), (1.4, 0.8, 0.6), 0, N - 1, count=20, seed=17)
    PR.ambient_motes(T, coll, "st_funken", tuple(ST.p(0.3, 0.4, 2.2)), (2.6, 1.6, 1.2), 30, 602, 0, N - 1,
                     color_kind="sparkt", drift=0.06, scale=0.6)

    # Kalle reicht Tueten ueber die Theke (periodisch: Szene 1 und 12 -> Loop)
    PER = N / (3 * max(1, round(N / (3 * 34))))                # ganzzahlig oft im Video -> Loop
    STAPEL = TH.p(-0.62, -0.5, TOP)
    MITTE = TH.p(0.02, -0.6, TOP + 0.42)
    KUNDE = TH.p(0.3, -0.98, 1.2)

    def reichen(f):
        return f < f2a or f >= S[11][0] + 4

    for j in range(3):
        tu = BG.papiertuete(coll, f"tuete{j}")
        tu.root.scale = (0, 0, 0)

        def tloc(f, j=j):
            u = (f / PER) % 3.0
            if not (j <= u < j + 1):
                return tuple(STAPEL)
            u -= j
            if u < 0.35:
                return tuple(STAPEL.lerp(MITTE, ease_in_out(u / 0.35)))
            if u < 0.7:
                v = ease_in_out((u - 0.35) / 0.35)
                return tuple(MITTE.lerp(KUNDE, v) + V(0, 0, 0.25 * math.sin(math.pi * v)))
            return tuple(KUNDE)

        def tscale(f, j=j):
            u = (f / PER) % 3.0
            if not reichen(f) or not (j <= u < j + 1):
                return (0, 0, 0)
            u -= j
            s_ = 1.15 * min(1.0, u / 0.08)
            if u > 0.85:
                s_ *= max(0.0, 1 - (u - 0.85) / 0.15)
            return (s_,) * 3
        T.set(tu.root, "location", tloc, 0, N - 1)
        T.set(tu.root, "scale", tscale, 0, N - 1)
        T.set(tu.root, "rotation_euler", lambda f: (0, 0, 0.3 * math.sin(f * 0.4)), 0, N - 1)
    for j in range(4):                                        # Stapel liegt bereit
        st_ = BG.papiertuete(coll, f"stapel{j}")
        st_.root.location = STAPEL + V(-0.05 * (j % 2), 0.08 * (j // 2), 0.0)
        st_.root.rotation_euler = (0, 0, 0.2 * j)
    # Arme: rechte Hand holt vom Stapel, linke reicht hinueber (periodisch, nur wenn gereicht wird)
    def arm(f, seite):
        if not reichen(f):
            return (0, 0, 0)
        u = (f / PER) % 1.0
        if seite == "R":
            w = math.sin(math.pi * clamp01(u / 0.45))
            return (-1.0 * w, 0.3 * w, 0.35 * w)
        w = math.sin(math.pi * clamp01((u - 0.3) / 0.6))
        return (-1.35 * w, -0.25 * w, -0.45 * w)
    T.add(k.sh["R"], "rotation_euler", lambda f: arm(f, "R"), 0, N - 1)
    T.add(k.sh["L"], "rotation_euler", lambda f: arm(f, "L"), 0, N - 1)
    T.add(k.el["L"], "rotation_euler", lambda f: (0.6 * arm(f, "L")[0] * -0.4, 0, 0), 0, N - 1)
    T.add(k.hips, "rotation_euler", lambda f: (0.06 * math.sin(2 * math.pi * f / PER) if reichen(f) else 0, 0,
                                               0.08 * math.sin(2 * math.pi * f / PER) if reichen(f) else 0), 0, N - 1)
    for cyc in range(int(N / PER) + 1):
        fz = int(cyc * PER + 0.5 * PER)
        if reichen(fz) and fz < N - 6:
            PR.burst(T, coll, f"tuetenmehl{cyc}", "flourdust", tuple(MITTE + V(0, 0, 0.1)), fz, 6, 300 + cyc, speed=(0.3, 0.7),
                     up=0.5, gravity=-0.6, life=(14, 22), size=(0.6, 1.0))
            if cyc % 2 == 0:
                cue(fz, "rascheln", 0.3)

    # Brezelblech (leer) links auf der Theke, Linse fuer Byte
    blech = VP.brezelblech(coll, "blech", n=0)
    BLECH = TH.p(-0.95, -0.45, TOP)
    blech.root.location = BLECH
    linse = LP.kameralinse_byte(coll, "linse")
    linse.root.parent = b.body
    linse.root.location = (0.07, -0.25, 0.05)

    # ------------------------------------------------------------ Kalle: Positionen
    setze(k, 0, S[4][1], K_TH, 0.0)
    setze(k, S[5][0], S[6][1], WEG)
    setze(k, S[7][0], S[8][1], K_SITZ, K_RZ)
    setze(k, S[9][0], S[9][1], WEG)
    setze(k, S[10][0], N, K_TH, 0.0)
    C.pose(T, k, "sit", S[7][0] - 1, S[8][1], 1, 1, settle=False)
    T.set(BU.objs["chair_spin"], "rotation_euler", lambda f: (0, 0, K_RZ), 0, 1)

    B_LOOP = TH.p(1.05, -0.85, 2.45)

    # =================================================================== SZENE 1 – Schlange bis zur Strasse
    f1a, f1b = S[0]
    T.set(b.root, "location", lambda f: tuple(B_LOOP), 0, f2a)
    C.kalle_react(T, k, "schock", hl(0), hold=f1b - hl(0) - 4, speaking=True, hat=False)
    C.kalle_look(T, k, lambda f: KUNDE + V(0, 0, 0.5), 0, f1b, ramp=1)
    A1 = (TH.p(0.4, -5.2, 2.35), TH.p(1.15, -0.6, 1.4), 21.0)
    B1 = (TH.p(0.35, -6.3, 2.75), TH.p(1.3, -0.6, 1.3), 20.0)
    cam.add_shot(f1a, f1b, rueckfahrt(f1a, f1b, A1, B1, ease=ease_in_out))

    # =================================================================== SZENE 2 – Zurueckspulen: gestern
    cue(f2a - 2, "whoosh", 1.0)
    rein = f2a + 12
    T.set(b.root, "location", lambda f: tuple(B_LOOP.lerp(lap_out, ease_in(clamp01((f - f2a) / 12)))), f2a, S[2][0])
    T.set(b.root, "scale", lambda f: ((1 - ease_in(clamp01((f - f2a - 4) / 8))) if f < S[2][0] else 1,) * 3, f2a, S[2][0])
    C.trail(T, coll, "s2trail", lambda f: tuple(b_pos(f)), f2a, rein + 3, n=6, size=0.05)
    tint(welt_mats(), f2a, S[2][0] + 14, (0.78, 0.8, 0.86), ramp=6)
    # entsaettigt: Farbe Richtung Grau (pro Material aus der Grundfarbe)
    for m in welt_mats():
        cc = tuple(m.diffuse_color)
        lum = 0.2126 * cc[0] + 0.7152 * cc[1] + 0.0722 * cc[2]
        for kk in range(3):
            fak = (0.45 + 0.55 * lum / cc[kk]) if cc[kk] > 1e-4 else 1.0
            T.mul(m, "diffuse_color", lambda f, fak=fak: 1 + (fak - 1) * window(f, f2a, S[2][0] + 14, 6, 14), f2a, S[2][0] + 14, index=kk)
    st_g = LP.stempel(coll, "stempel_gestern", "GESTERN", farbe="#5E6E8F")
    LP.stempel_klappen(T, st_g, f2a + 6, f2b - 3)
    kinn = {"sh_R": (-1.35, 0.15, 0.55), "el_R": (-2.15, 0, 0), "hips": (0.16, 0, 0), "head": (0.12, 0, 0.1)}
    C.pose(T, k, kinn, f2a + 16, f2b + 2, 8, 6)
    C.kalle_react(T, k, "zweifel", hl(1) - 2, hold=f2b - hl(1), speaking=True, hat=False)
    C.kalle_look(T, k, lambda f: TH.p(3.0, 0.4, 1.7), f2a + 20, f2b, ramp=8)
    A2 = (TH.p(-0.3, -3.7, 2.0), K_TH + V(0.05, -0.2, 1.72), 30.0)
    cam.add_shot(f2a, f2b, push_in(f2a, f2b, A2, k=0.18))

    # Stempel am Bildrand oben links, in der Schaerfeebene der Kamera (wie ein Overlay)
    def an_kamera(obj, f0, f1, sx=-0.36, sy=0.72, breite_bild=0.5, breite_obj=0.9):
        def m_(f):
            pos, ziel, lens = cam.base(f)[:3]
            pos, ziel = V(pos), V(ziel)
            d = ziel - pos
            D = d.length
            d.normalize()
            r = d.cross(V(0, 0, 1)).normalized()
            u = r.cross(d)
            h = D * 18.0 / lens
            w = h * 1080 / 1920
            p = ziel + r * (sx * w) + u * (sy * h)
            return p, Matrix((r, d, u)).transposed().to_euler(), breite_bild * 2 * w / breite_obj
        T.set(obj, "location", lambda f: tuple(m_(f)[0]), f0, f1)
        T.set(obj, "rotation_euler", lambda f: tuple(m_(f)[1]), f0, f1)
        T.mul(obj, "scale", lambda f: (m_(f)[2],) * 3, f0, f1)
    an_kamera(st_g.root, f2a, f2b + 4)

    # =================================================================== SZENE 3 – Byte am Schaufenster
    f3a, f3b = S[2]
    B3 = TH.p(2.1, 1.25, 1.9)
    raus = f3a + 2
    b3 = path([(raus, lap_out), (raus + 6, lap_out + V(0.3, -0.25, 0.35)), (raus + 16, B3 + V(-0.2, -0.15, 0.1)), (raus + 22, B3)], ease_out)
    T.set(b.root, "location", lambda f: b3(f), f3a, S[3][1])
    T.set(b.root, "scale", lambda f: (min(1.0, 0.3 + 0.7 * ease_out(clamp01((f - raus) / 8))),) * 3, f3a, f3a + 12)
    T.mul(b.body, "scale", lambda f: (1 - 0.16 * window(f, raus + 21, raus + 32, 1, 7), 1, 1 + 0.18 * window(f, raus + 21, raus + 32, 1, 7)),
          raus + 20, raus + 33)
    C.trail(T, coll, "s3trail", lambda f: b3(f), raus, raus + 24, n=8, size=0.06)
    cue(raus, "whoosh", 0.9)
    T.set(b.body, "rotation_euler", lambda f: (0, 0, -1.1 * window(f, raus + 20, t(2, 2.6), 6, 10)), f3a, f3b)    # schaut hinaus
    for q, (p_, weg, st) in enumerate(passanten):
        fq = t(2, 1.0 + 0.45 * q)
        fz = LP.fragezeichen(coll, f"frage{q}")
        LP.fragezeichen_an(T, fz, fq, 34, lambda f, weg=weg: weg(f) + V(0, 0, 2.05), rz=-math.pi / 2)
        cue(fq, "pop", 0.35)
    C.kalle_look(T, k, lambda f: b_pos(f), f3a + 8, f3b, ramp=8)
    C.kalle_react(T, k, "zweifel", t(2, 2.0), hold=f3b - t(2, 2.0), hat=False)
    A3 = (TH.p(0.3, -0.2, 1.9), TH.p(2.45, 0.6, 1.6), 20.0)
    B3c = (TH.p(0.25, -3.3, 1.95), K_TH + V(0.45, -0.2, 1.62), 28.0)
    cam.add_shot(f3a, f3b, schwenk(t(2, 1.8), f3b - 4, A3, B3c))

    # =================================================================== SZENE 4 – Ich kann doch nur backen
    f4a, f4b = S[3]
    strang = LP.teigstrang(coll, "strang_hand")
    strang.root.parent = k.hand["R"]
    strang.root.location = (0, -0.05, -0.12)
    strang.root.rotation_euler = (0, 0.3, 0)
    hoch = t(3, 0.8)
    wurf = t(4, 1.0)
    T.set(strang.root, "scale", lambda f: (pop(f, f4a + 4, 6),) * 3 if f4a + 4 <= f < wurf else (0, 0, 0), 0, N - 1)
    C.pose(T, k, {"sh_R": (-1.55, 0.35, 0.2), "el_R": (-1.2, 0, 0), "head": (0.08, 0, 0.12)}, hoch - 6, f4b + 2, 6, 6)
    zucken = hl(3) - 4
    for side, sx in (("R", 1), ("L", -1)):
        T.add(k.sh[side], "rotation_euler", lambda f, sx=sx: (0, 0, sx * 0.22 * (window(f, f4a + 6, f4a + 22, 4, 6) + window(f, zucken, zucken + 14, 3, 6))),
              f4a, f4b)
    PR.burst(T, coll, "s4mehl", "flourdust", tuple(K_TH + V(-0.3, -0.55, 1.55)), hoch + 4, 14, 401, speed=(0.1, 0.3), up=0.1,
             gravity=-0.8, life=(26, 36), size=(0.6, 1.0), drag=2.0)
    C.kalle_react(T, k, "zweifel", hl(3) - 2, hold=f4b - hl(3), speaking=True, hat=False)
    C.kalle_look(T, k, lambda f: b_pos(f), f4a, hoch, ramp=6)
    A4 = (TH.p(0.1, -3.5, 1.9), K_TH + V(0.1, -0.2, 1.62), 30.0)
    B4 = (K_TH + V(0.1, -2.45, 1.85), K_TH + V(0.02, -0.2, 1.72), 40.0)
    cam.add_shot(f4a, f4b, zoom_gesicht(f4a, f4b, A4, B4))

    # =================================================================== SZENE 5 – Linse, Brezel in Zeitlupe (FILMEN)
    f5a, f5b = S[4]
    B5 = K_TH + V(0.82, -0.42, 1.88)
    b5 = path([(f4b - 30, B3), (f5a + 8, B5)], ease_in_out)
    T.set(b.root, "location", lambda f: b5(f), f4b - 30, S[5][0])
    T.set(b.body, "rotation_euler", lambda f: (0, 0, -0.55 * window(f, f5a, f5b, 6, 6)), f3b, f5b + 1)
    f_linse = f5a + 4
    LP.linse_aufklappen(T, linse, f_linse, f_aus=f5b - 4, f_ende=f5b)
    cue(f_linse + 2, "pop", 0.9)
    start = K_TH + V(-0.25, -0.55, 1.45)
    st5, brz5, f_land = LP.brezel_schlingen(T, coll, "schlingen", start, BLECH + V(0, 0, 0.02), wurf, max(30, t(4, 2.3) - wurf),
                                            s=1.6, hoehe=0.85)
    T.set(brz5, "scale", lambda f: (0, 0, 0), S[5][0], N - 1)                # Brezel nur in Szene 5 auf dem Blech
    cue(f_land, "pop", 0.55)
    C.pose(T, k, {"sh_R": (-1.2, 0.1, 0.3), "sh_L": (-1.2, -0.1, -0.3), "el_R": (-0.9, 0, 0), "el_L": (-0.9, 0, 0)}, f5a, wurf + 2, 6, 4)
    C.pose(T, k, {"sh_R": (-2.3, 0.3, 0.2), "el_R": (-0.4, 0, 0), "hips": (-0.08, 0, 0)}, wurf - 2, wurf + 14, 3, 8)
    C.kalle_look(T, k, lambda f: V(T.loc(st5.root, f)) if f < f_land else BLECH, wurf, f5b, ramp=4)
    C.kalle_react(T, k, "staunen", f_land, hold=f5b - f_land, hat=False)
    C5 = K_TH + V(0.2, -0.55, 1.45)
    cam.add_shot(f5a, f5b, orbit(C5, 3.1, 2.05, 30.0, -28, 18, f5a, f5b))

    # ============================================================ STUDIO: Zeitleiste (Szene 6), Handy (Szene 7)
    f6a, f6b = S[5]
    f7a, f7b = S[6]
    cam.whips.append((f6a, 1))
    cue(f6a - 3, "whoosh", 0.6)
    ZS = 0.8
    ZL = ST.p(0.35, 0.7, 2.45)
    zl = LP.zeitleiste_clips(coll, "zeitleiste", n=12)
    zl.root.location = ZL
    zl.root.scale = (0, 0, 0)
    T.set(zl.root, "scale", lambda f: (ZS * pop(f, f6a + 2, 8, 1.12),) * 3 if f6a + 2 <= f < f7a + 12 else (0, 0, 0), 0, N - 1)
    T.add(zl.root, "location", lambda f: (0, 0, 0.03 * math.sin(f * 0.12)), f6a, f7a)
    f_cut = t(5, 1.0)
    pops = LP.zeitleiste_schneiden(T, zl, f_cut, 34, -ZL.z / ZS + 0.02, f_cut + 40)
    cue(f_cut, "whoosh", 1.0)
    for p_ in pops:
        cue(p_, "pop", 0.8)
    B6 = ST.p(-1.25, 0.0, 3.05)
    b6 = path([(f6a, B6 + V(-0.6, -0.3, 0.3)), (f6a + 12, B6)], ease_out)
    T.set(b.root, "location", lambda f: b6(f), f6a, f7a)
    C.byte_arm(T, b, "R", (-1.4, 0.4, -0.3), f_cut - 6, f_cut + 30, ramp=4)
    C.byte_hand(T, b, "R", "point", f_cut - 6, f_cut + 30)
    T.set(b.body, "rotation_euler", lambda f: (0, 0, -0.5 * window(f, f6a, f7b, 6, 6)), f6a, f7b + 1)
    A6 = (ST.p(-0.95, -2.3, 2.55), ST.p(-0.6, 0.7, 2.75), 28.0)
    B6c = (ST.p(0.45, -2.5, 2.6), ST.p(0.35, 0.7, 2.75), 28.0)
    cam.add_shot(f6a, f6b, fahrt(f6a, f6b, A6, B6c, ease=ease_in_out))

    # SZENE 7 – Kacheln falten sich zum Hochkant-Handy
    hh = LP.handy_hochkant(coll, "handy_gross", h=1.45)
    HH = ST.p(0.35, 0.7, 2.05)
    hh.root.location = HH
    f_handy = f7a + 8
    T.set(hh.root, "scale", lambda f: (pop(f, f_handy, 9, 1.15),) * 3 if f_handy <= f < f7b + 2 else (0, 0, 0), 0, N - 1)
    LP.landen(T, hh.root, f_handy + 9, staerke=0.18, dauer=10)
    cue(f_handy, "pop", 0.9)
    gute = [kk for kk in zl.kacheln if kk.gut]
    for j, kk in enumerate(gute):
        T.add(kk.root, "rotation_euler", lambda f, j=j: (0, 0, (1.4 if j != 1 else 0) * (1 if j == 0 else -1) * ease_in_out(clamp01((f - f7a) / 8))),
              f7a, f7a + 12)
    T.add(zl.streifen, "scale", lambda f: (-ease_in(clamp01((f - f7a) / 6)), 0, 0), f7a, f7a + 12)
    f_worte = wd(6, "untertitel")
    f_titel = max(t(6, 1.5), wd(6, "satz") - 2)
    LP.handy_abspielen(T, hh, f_handy, f7b + 2, f_titel, f_worte=f_worte, intervall=7, f_noten=wd(6, "musik") - 4)
    cue(f_titel, "pop", 0.8)
    B7 = ST.p(-0.75, 0.35, 2.85)
    T.set(b.root, "location", lambda f: tuple(B6.lerp(B7, ease_in_out(clamp01((f - f7a) / 12)))), f7a, S[7][0])
    for wi, wort in enumerate(("untertitel", "musik", "satz")):
        fs = wd(6, wort) + 1
        C.byte_snap(T, b, "L", fs)
        cue(fs, "pop", 0.5)
        PR.burst(T, coll, f"s7snap{wort}", "sparkt", tuple(B7 + V(-0.25, -0.15, 0.3)), fs, 8, 701 + wi, speed=(0.5, 1.0),
                 up=0.3, gravity=-0.5, life=(10, 16), size=(0.8, 1.2))
    A7 = (ST.p(0.35, -3.0, 2.1), HH + V(0, 0, 0.05), 30.0)
    cam.add_shot(f7a, f7b, push_in(f7a, f7b, A7, k=0.3))

    # ============================================================ BUERO: Abend 19:00 (Szene 8), Morgen 50.000 (Szene 9)
    f8a, f8b = S[7]
    f9a, f9b = S[8]
    cam.whips.append((f8a, -1))
    cue(f8a - 3, "whoosh", 0.6)
    fz_bu = VP.fenster_tageszeit(coll, "fz_bu", 0.72, 0.82)
    FENSTER = BU.p(0.38, 2.36, 1.95)
    fz_bu.root.location = FENSTER
    VP.tageszeit(T, fz_bu, [(0, "daemmerung"), (f8a, "daemmerung"), (f8b - 10, "nacht"), (f9a, "morgen"), (N - 1, "morgen")])
    mats_bu = welt_mats()
    tint(mats_bu, f8a, f8b, (0.62, 0.62, 0.86), ramp=6)
    tint(mats_bu, f9a, f9b, (1.06, 0.98, 0.88), ramp=6)
    lampe = VP.schreibtischlampe(coll, "lampe")
    lampe.root.location = BU.p(1.45, 0.3, 0.98)
    lampe.root.rotation_euler = (0, 0, math.radians(200))
    # 19:00 auf dem Laptop (Bildschirm), Ding
    f_uhr = f8a + 16
    cue(f_uhr, "ding", 1.0)
    # kleines Handy mit dem Video faltet sich zum Papierflieger
    hk = LP.handy_hochkant(coll, "handy_klein", h=0.36, titel="Brezel in 3 Sekunden?", woerter=("…",))
    HK = BU.p(0.3, -0.2, 0.98 + 0.19)
    hk.root.location = HK
    hk.root.rotation_euler = (-0.18, 0, 0.25)
    f_falt = t(7, 0.8)
    T.set(hk.root, "scale", lambda f: ((1 - ease_in(clamp01((f - f_falt) / 7))) if f >= f_falt else 1, 1, 1) if f8a <= f < f_falt + 8 else (0, 0, 0),
          0, N - 1)
    LP.handy_abspielen(T, hk, f8a, f_falt + 8, f8a + 1)
    pf = LP.papierflieger_licht(coll, "flieger", s=0.6)
    p_aus = FENSTER + V(0, 0.4, 0.05)
    flug_pfad = path([(f_falt + 4, HK + V(0, -0.05, 0.05)), (f_falt + 12, HK + V(-0.25, -0.35, 0.5)), (f_falt + 24, BU.p(0.9, 0.6, 1.9)),
                      (f_falt + 36, FENSTER + V(0.1, -0.5, 0.0)), (f_falt + 46, p_aus)], ease_in_out)
    LP.flug(T, pf, flug_pfad, f_falt + 4, f_falt + 46)
    T.set(pf.root, "scale", lambda f: (pop(f, f_falt + 4, 6, 1.2) * (1 - ease_in(clamp01((f - f_falt - 36) / 10))),) * 3 if f_falt + 4 <= f < f_falt + 47 else (0, 0, 0),
          0, N - 1)
    C.trail(T, coll, "flugspur", flug_pfad, f_falt + 6, f_falt + 46, n=10, size=0.035, lag=2.0)
    cue(f_falt + 6, "whoosh", 1.0)
    B8 = BU.p(1.2, -0.3, 1.55)
    T.set(b.root, "location", lambda f: tuple(B8 + V(0, 0, 0.04 * math.sin(f * 0.15))), f8a, f9a)
    C.byte_arm(T, b, "L", (-1.6, -0.6, 0.0), f_falt - 4, f_falt + 20, ramp=4)
    C.byte_hand(T, b, "L", "point", f_falt - 4, f_falt + 20)
    C.kalle_look(T, k, lambda f: V(T.loc(pf.root, f)) if f_falt + 4 <= f < f_falt + 46 else V(BU.p(0.82, 0.0, 1.2)), f8a, f8b, ramp=4)
    C.kalle_react(T, k, "neutral", f8a + 2, hold=f8b - f8a - 4, hat=False)
    A8 = (BU.p(0.95, -2.5, 1.55), BU.p(0.7, 0.15, 1.2), 30.0)
    B8c = (BU.p(0.55, -2.4, 1.75), FENSTER + V(-0.05, 0, -0.15), 30.0)
    cam.add_shot(f8a, f8b, schwenk(f_falt, f8b - 2, A8, B8c))

    # SZENE 9 – Handy vibriert, Zaehler rollt bis 50.000, Kalle faellt fast vom Stuhl
    hv = LP.handy_vibriert(coll, "handy_tisch")
    hv.root.location = BU.p(0.15, -0.12, 0.985)
    T.set(hv.root, "scale", lambda f: (1.6,) * 3 if f9a - 1 <= f < f9b + 2 else (0, 0, 0), 0, N - 1)
    f_roll = t(8, 0.6)
    buzz = LP.vibrieren(T, hv, f9a + 1, f_roll + 6, BU.p(0.15, -0.12, 0.985), BU.p(0.02, -0.3, 0.985))
    for fb_ in buzz[::2]:
        cue(fb_, "buzz", 0.55)
    f_stop = f_roll + int(0.4 * (f9b - f_roll))
    W.anchors["zaehler"] = L.empty("anchor_zaehler", None, tuple(BU.p(0.82, 0.12, 1.62)), coll)
    W.labels.append({"anchor": "zaehler", "f0": f_roll, "f1": f9b - 3, "count_f0": f_roll, "count_f1": f_stop, "from": 0,
                     "to": 50000, "fmt": "{}", "dy": -30})
    W.labels[-1]["f1"] = f_stop + 10
    cue(f_stop, "ding", 0.9)
    VP.herzchen(T, coll, "herz9", tuple(BU.p(0.82, -0.05, 1.3)), f_stop - 2, 14, 909, f_end=f9b + 6)
    LP.sprechblasen(T, coll, "blasen9", tuple(BU.p(0.85, -0.05, 1.3)), f_stop, 6, 919, f_end=f9b + 6)
    kipp = f_stop + 12
    T.add(k.hips, "rotation_euler", lambda f: (0.4 * window(f, kipp, kipp + 22, 3, 10) * (1 + 0.15 * math.sin((f - kipp) * 0.9)), 0, 0), kipp - 1, kipp + 23)
    T.add(k.root, "location", lambda f: (0, 0.12 * window(f, kipp, kipp + 22, 3, 10), -0.05 * window(f, kipp, kipp + 22, 3, 10)), kipp - 1, kipp + 23)
    C.pose(T, k, "hands_up", kipp, kipp + 18, 3, 8)
    T.add(BU.objs["chair_spin"], "rotation_euler", lambda f: (0, 0, 0.3 * window(f, kipp, kipp + 24, 3, 12) * math.sin((f - kipp) * 0.35)), kipp - 1, kipp + 25)
    cam.shakes.append((kipp, 0.02, 10))
    C.kalle_react(T, k, "schock", hl(8) - 2, hold=f9b - hl(8), speaking=True, hat=True)
    B9 = BU.p(1.25, -0.25, 1.65)
    T.set(b.root, "location", lambda f: tuple(B9), f9a, f9b)
    A9 = (BU.p(0.3, -3.1, 1.55), BU.p(0.4, 0.05, 1.3), 28.0)
    face9 = K_SITZ + V(0.0, -0.25, 1.62)
    Z9 = (face9 + V(0.35, -1.9, 0.08), face9 + V(0, 0, -0.02), 42.0)
    cam.add_shot(f9a, f9b, harter_zoom(f9a, f9b, A9, Z9, f_stop + 13, dur=5))

    # ============================================================ STUDIO: Reichweite (Szene 10)
    f10a, f10b = S[9]
    cam.whips.append((f10a, 1))
    cue(f10a - 3, "whoosh", 0.6)
    MB = ST.p(0.35, 0.5, 0.0)
    mb = LP.mini_baeckerei(coll, "mini_bk", s=1.7)
    mb.root.location = MB
    T.set(mb.root, "scale", lambda f: (1.7 * pop(f, f10a + 2, 8, 1.15),) * 3 if f10a + 2 <= f < f10b + 2 else (0, 0, 0), 0, N - 1)
    LP.landen(T, mb.root, f10a + 10, staerke=0.25, dauer=10)
    T.set(mb.schild, "rotation_euler", lambda f: (0.25 * math.sin(f * 0.25), 0, 0), f10a, f10b)
    KV.dampf_loop(T, coll, "dampf_mini", MB + V(0.37, 0.2, 1.75), f10a + 8, f10b, n=6, staerke_fn=lambda f: 0.8, hoehe=0.5, seed=8)
    starts, radius = LP.wellenringe(T, coll, "welle", MB + V(0, 0, 0.03), f10a + 10, n=5, abstand=int(max(10, (f10b - f10a - 30) / 5)),
                                    dauer=34, r_end=4.6)
    for q, st in enumerate(starts):
        cue(st, "whoosh", 0.7 - 0.08 * q)
    figs = LP.figuren_feld(coll, "fig", MB, 64, 77, r_min=1.05, r_max=4.4, s=0.5)

    def f_pop(g):
        for f in range(f10a + 10, f10b):
            if radius(f) >= g.r:
                return f
        return f10b - 4
    LP.figuren_poppen(T, figs, f_pop, f10b + 2, lambda g: math.atan2(-math.cos(g.a), math.sin(g.a)))
    for g in figs:
        T.set(g.root, "scale", lambda f: (0, 0, 0), f10b + 2, N - 1)
    fp_sorted = sorted(f_pop(g) for g in figs)
    for fp_ in fp_sorted[::11]:
        cue(fp_, "pop", 0.45)
    B10 = MB + V(1.0, -0.5, 1.9)
    T.set(b.root, "location", lambda f: tuple(B10 + V(0, 0, 0.05 * math.sin(f * 0.12))), f10a, f11a)
    T.set(b.body, "rotation_euler", lambda f: (0, 0, 0.5), f10a, f10b)
    T.set(b.body, "rotation_euler", lambda f: (0, 0, 0), f10b, f10b + 1)
    A10 = (MB + V(0.0, -2.4, 1.55), MB + V(0, 0, 0.55), 30.0)
    B10c = (MB + V(0.0, -7.2, 4.6), MB + V(0, 0.4, 0.6), 26.0)
    cam.add_shot(f10a, f10b, rueckfahrt(f10a, f10b, A10, B10c, ease=ease_out))

    # =================================================================== SZENE 11 – Vorspulen: heute
    cue(f11a - 2, "whoosh", 1.0)
    T.set(b.root, "location", lambda f: tuple(B_LOOP), f11a, N)
    T.set(b.root, "scale", lambda f: (pop(f, f11a, 6, 1.1),) * 3, f11a - 1, f11a + 7)
    st_h = LP.stempel(coll, "stempel_heute", "HEUTE", farbe=LP.ROT)
    LP.stempel_klappen(T, st_h, f11a + 6, f11b - 3)
    korb_hoch = t(10, 1.0)
    K0 = V(korb.location)
    KH = K_TH + V(0.05, -0.42, 2.38)
    zurueck = S[11][0] + 2

    def korb_loc(f):
        if f < korb_hoch or f >= zurueck + 12:
            return tuple(K0)
        if f < zurueck:
            u = ease_out_back(clamp01((f - korb_hoch) / 10), 1.4)
            return tuple(K0.lerp(KH, u) + V(0.04 * math.sin(f * 0.8) * (f > korb_hoch + 10), 0, 0.03 * abs(math.sin(f * 0.8))))
        return tuple(KH.lerp(K0, ease_in_out((f - zurueck) / 12)))
    T.set(korb, "location", korb_loc, 0, N - 1)
    T.set(korb, "rotation_euler", lambda f: (0.25 * window(f, korb_hoch, zurueck + 10, 6, 8), 0, 0.15 * math.sin(f * 0.5) * window(f, korb_hoch, zurueck, 6, 6)), 0, N - 1)
    C.pose(T, k, "hands_up", korb_hoch - 4, zurueck + 8, 6, 8)
    C.kalle_react(T, k, "jubel", hl(10) - 6, hold=S[11][1] - hl(10), speaking=True, hat=False)
    PR.burst(T, coll, "korbkruemel", "crumb", tuple(KH + V(0, 0, -0.1)), korb_hoch + 8, 10, 1101, speed=(0.3, 0.7), up=0.3,
             gravity=-5.0, life=(14, 20), size=(1.0, 1.5))
    A11 = (TH.p(-0.35, -4.4, 2.2), K_TH + V(0.6, -0.4, 1.6), 24.0)
    cam.add_shot(f11a, f11b, push_in(f11a, f11b, A11, k=0.22))
    an_kamera(st_h.root, f11a, f11b + 4)

    # =================================================================== SZENE 12 – Schon bestellt (Loop)
    f12a, f12b = S[11]
    haken = KV.haken_gruen(coll, "haken", s=0.16)
    haken.root.location = LAP_SCR + V(0.0, -0.12, 0.42)
    f_h = f12a + 8
    T.set(haken.root, "scale", lambda f: (pop(f, f_h, 8, 1.3),) * 3 if f_h <= f < N - 16 else ((unpop(f, N - 16, 8),) * 3 if f >= N - 16 else (0, 0, 0)), 0, N - 1)
    cue(f_h, "ding", 1.0)
    KV.konfetti_gruen(T, coll, "konfetti12", tuple(LAP_SCR + V(0, -0.1, 0.45)), f_h + 2, count=16, seed=12)
    C.kalle_react(T, k, "jubel", f12a, hold=f12b - f12a - 18, hat=False)
    S11_ende = push_in(f11a, f11b, A11, k=0.22)(f11b - 1)
    cam.add_shot(f12a, N, rueckfahrt(f12a + 2, N - 8, S11_ende, A1, ease=ease_in_out))

    # ------------------------------------------------------------ Bytes Display-Augen
    eyes = ["jubel", "neutral", "zweifel", "neutral", "staunen", "neutral", "staunen", "neutral", "jubel", "staunen", "jubel", "jubel"]
    sched = [(0, "jubel")] + [(S[i][0], e) for i, e in enumerate(eyes)]
    sched += [(f12a + 3, "wink"), (f12a + 16, "jubel")]
    C.byte_face(T, b, sched, 0, N - 1)
