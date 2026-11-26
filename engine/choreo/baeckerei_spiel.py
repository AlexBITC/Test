"""Regie fuer 'Diese Stadt ist ein Spiel' (folge-11-baeckerei-spiel). Szenen-Index 0..13 = Szene 1..14.

Bogen: 1-2 Trailer (Erzaehler, Spielwelt), 3-4 Ueberraschung im Buero (Byte hat das Spiel gebaut, Kalle haelt den
Controller verkehrt herum), 5-8 Kalle spielt (Preis 0,50 -> Verlust, Regen, 500 Brezeln, PLEITE), 9-11 Lea spielt
(Preis 1,20, nach Wetter backen, ab 17 Uhr halber Preis, Null Reste, Tag 30, Filiale 2), 12 Kalles Stolz,
13 Planspiel im Studio (NOCHMAL, Rueckspulen), 14 echte Welt (Schild auf OFFEN) und Rueckverwandlung in die Spielstadt
(Loop auf Szene 1).
Kulissen: spielwelt -> buero -> spielwelt -> buero -> spielwelt -> buero -> studio -> theke (+ Morph in die Spielwelt).
Uebergaenge echte Welt <-> Spiel nur ueber ins_spiel, aus_spiel und welt_zu_spiel, sonst kurze Wischer (Whips).
Kameras nie zweimal hintereinander gleich: spiel_stadt, spiel_flug, aus_spiel+rueckfahrt, zoom_gesicht,
ins_spiel+spiel_laden(schwenk), spiel_laden(push_in), spiel_stadt+spiel_flug, spiel_laden(harter Stopp),
aus_spiel+rueckfahrt, ins_spiel+spiel_laden(schwenk), spiel_flug+spiel_stadt, aus_spiel+zoom_gesicht, kreisfahrt,
durchs_fenster+welt_zu_spiel.
Running Gags: Controller verkehrt herum (S3, S4), Tonne 'RESTE' (voll in S8, leer in S10, zurueckgesetzt in S13).
Requisiten: assets/props/baeckerei_spiel.py, Bildschirm: assets/screens/baeckerei_spiel.py.
"""
import math
import os
import sys

import bpy
from mathutils import Vector, Matrix

import characters as C
import look as L
import lea as LE
import kameras as KA
import spielwelt as SW
from anim import (ease_out, ease_in_out, window, pop, lerp, clamp01)
from choreo.common import Ctx, V
from choreo.mehlpreis import fahrt, push_in

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "props"))
import baeckerei_spiel as BSP  # noqa: E402
import viral as VP  # noqa: E402

FPS = 30
zoom_gesicht = rueckfahrt = schwenk = fahrt
WEG = V(300, 0, 0)            # ausserhalb aller Sets (immer ausgeblendet)
HALTEN = {"sh_R": (-1.1, 0.25, 0.35), "sh_L": (-1.1, -0.25, -0.35), "el_R": (-1.2, 0, 0.3), "el_L": (-1.2, 0, -0.3)}


def _griff(fig, pose, loc, rz, extra=()):
    """Lokale Matrix des Controllers relativ zur rechten Hand: Mitte zwischen beiden Haenden, Oberseite nach oben zum
    Gesicht geneigt (aus der Pose einmalig ausgewertet)."""
    alt = [(fig.root, "location", tuple(fig.root.location)), (fig.root, "rotation_euler", tuple(fig.root.rotation_euler))]
    fig.root.location = loc
    fig.root.rotation_euler = (0, 0, rz)
    for name, val in list(pose.items()) + list(extra):
        j = C.joint(fig, name)
        alt.append((j, "rotation_euler", tuple(j.rotation_euler)))
        j.rotation_euler = tuple(a + b for a, b in zip(j.rotation_euler, val))
    bpy.context.view_layer.update()
    hr, hl = fig.hand["R"].matrix_world.copy(), fig.hand["L"].matrix_world.copy()
    for o, p, v in reversed(alt):
        setattr(o, p, v)
    bpy.context.view_layer.update()
    mid = (hr.translation + hl.translation) / 2
    fwd = Vector((math.sin(rz), -math.cos(rz), 0))
    x = (hl.translation - hr.translation)
    x.z = 0
    x = x.normalized() if x.length > 1e-4 else Vector((math.cos(rz), math.sin(rz), 0))
    z = (Vector((0, 0, 1)) * 0.8 - fwd * 0.6).normalized()
    y = z.cross(x).normalized()
    z = x.cross(y).normalized()
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = mid + fwd * 0.04 + Vector((0, 0, 0.02))
    return hr.inverted() @ m


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    l = W.lea
    SP, BU, ST, TH = c.sets["spielwelt"], c.sets["buero"], c.sets["studio"], c.sets["theke"]
    sc = c.sc
    S = [(s["f0"], s["f1"]) for s in sc]
    coll = W.coll
    cam = W.cam
    I = SP.inst
    KAT = SW.katalog
    WA, KU, GB = KAT("ware"), KAT("kunde"), KAT("gedankenblase")
    LO = SP.laden_o

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

    def ende(i):
        ws = sc[i]["words"]
        return ws[-1]["f1"] if ws and "f1" in ws[-1] else S[i][1] - 6

    def cue(f, kind, g=1.0):
        c.cue(int(f), kind, g)

    def lp(x, y, z=0.0):
        return LO + V(x, y, z)

    W.loop_frames = 14                              # Kanaele ueber die ganze Folge gleiten am Ende auf Frame 0 zurueck
    W.anchors["kalle_face"] = L.empty("anchor_kalle_face", k.head, (0, -0.25, 0.28), coll)
    W.anchors["lea_face"] = L.empty("anchor_lea_face", l.head, (0, -0.22, 0.28), coll)
    W.anchors["byte"] = b.body

    # ------------------------------------------------------------ Grundbewegung
    C.kalle_idle(T, k, 0, N - 1, seed=7)
    LE.lea_idle(T, l, 0, N - 1, seed=23)
    C.byte_idle(T, b, 0, N - 1, seed=3, amp=0.02)
    C.byte_blinks(T, b, 0, N - 1, seed=11)
    C.antenna_spring(T, b, 2, N - 1)
    C.follow_through(T, k.hat, k.head, "rotation_euler", 2, 0.9, 3, 0, N - 1)
    C.follow_through(T, k.skirt, k.hips, "rotation_euler", 1, 1.2, 4, 0, N - 1)
    C.follow_through(T, l.skirt, l.hips, "rotation_euler", 1, 1.2, 4, 0, N - 1)
    C.pose(T, k, "arms_rest", -10, None, 1, 1, weight=0.6, settle=False)
    C.pose(T, l, "arms_rest", -10, None, 1, 1, weight=0.6, settle=False)
    erz = [i for i, s in enumerate(sc) if s["sprecher"] == "erzaehler"]
    for i, s in enumerate(sc):
        if s["sprecher"] == "kalle":
            C.kalle_lipsync(T, k, s, s["f0"], s["f1"])
        elif s["sprecher"] == "lea":
            LE.lea_lipsync(T, l, s, s["f0"], s["f1"])
        elif s["sprecher"] == "byte":
            C.byte_speak(T, b, s, s["f0"], s["f1"])
        if i not in erz and i != 11:
            for w in s["words"]:
                if w["hl"]:
                    cam.punch.append(w["f0"])
    cam.drift_env = lambda f: min(1.0, f / 10.0, max(0.0, (N - 7 - f) / 10.0)) * \
        (0.3 if any(S[i][0] <= f < S[i][1] for i in erz + [11]) else 1.0)
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

    # ============================================================ Buero: Aufbau (Abend)
    BU.objs["laptop"].root.scale = (0, 0, 0)
    mon = BSP.monitor_buero(coll, "mon")
    mon.root.location = BU.p(0.52, 0.12, 0.98)
    mon.root.rotation_euler = (0, 0, -0.62)
    lampe = VP.schreibtischlampe(coll, "sl_spiel")
    lampe.root.location = BU.p(1.3, 0.2, 0.98)
    lampe.root.rotation_euler = (0, 0, 2.6)
    fenster = VP.fenster_tageszeit(coll, "fz_spiel")
    fenster.root.location = BU.p(-2.3, 2.36, 1.95)
    VP.tageszeit(T, fenster, [(0, "daemmerung")])
    bpy.context.view_layer.update()
    MON_M, MON_N = BSP.display_mitte(mon)
    K_SITZ = V(BU.kalle) + V(0.0, -0.1, -0.25)
    K_RZ = 0.42
    L_STEH = BU.p(-1.25, -0.35, 0)
    L_RZ = 0.55
    B_MON = BU.p(0.52, 0.16, 2.08)
    # Controller: einer fuer Kalle, einer fuer Lea (Uebergabe in S9)
    ck = BSP.controller(coll, "ctrl_k")
    cl = BSP.controller(coll, "ctrl_l")
    for cc, fig, pose, loc, rz in ((ck, k, HALTEN, K_SITZ, K_RZ), (cl, l, HALTEN, L_STEH, L_RZ)):
        mloc = _griff(fig, pose, loc, rz, extra=(("hip_R", (-1.5, 0, 0.1)), ("hip_L", (-1.5, 0, -0.1)),
                                                  ("knee_R", (1.45, 0, 0)), ("knee_L", (1.45, 0, 0))) if fig is k else ())
        cc.root.parent = fig.hand["R"]
        cc.root.matrix_parent_inverse = Matrix.Identity(4)
        cc.root.matrix_basis = mloc
        cc.root.scale = (2.6, 2.6, 2.6)
        for o in cc.root.children_recursive:
            o.scale = o.scale
    f_uebergabe = None                                   # gesetzt in Szene 9

    # Kalle sitzt im Buero (Szenen 1-12), in Szene 14 in der echten Baeckerei
    setze(k, 0, S[12][0], K_SITZ, K_RZ)
    C.pose(T, k, "sit", -2, S[12][0], 1, 4, settle=False)
    T.set(BU.objs["chair_spin"], "rotation_euler", lambda f: (0, 0, K_RZ), 0, 1)
    C.pose(T, k, HALTEN, -2, S[8][0] + 24, 1, 10, settle=False)
    setze(l, 0, S[8][0], WEG)
    setze_byte(0, S[2][0], B_MON)

    # ============================================================ Spielwelt: Leben, Wetter, Figuren
    f_alle = (0, N - 1)
    for name, o in I.items():
        if name.startswith("sw_baum"):
            KAT("baum").wiegen(T, o, *f_alle)
    # Wetter-Plan: Szene 7 Zeitraffer (abend, nacht, Sonne = Tag 2, dann Regen), Szene 8 Abend, Szene 10 neues Spiel
    f7a, f7b = S[6]
    f10a, f10b = S[9]
    regen7 = f7a + int(0.42 * (f7b - f7a))
    regen10 = f10a + int(0.32 * (f10b - f10a))
    uhr17 = wd(9, "siebzehn") if any(w["w"].lower().startswith("17") or "siebzehn" in w["w"].lower() for w in sc[9]["words"]) \
        else f10a + int(0.62 * (f10b - f10a))
    uhr17 = max(uhr17, wd(9, "Uhr") - 10)
    plan = [(0, "sonne"), (f7a + 4, "abend"), (f7a + 16, "nacht"), (f7a + 30, "sonne"), (regen7, "regen"),
            (S[7][0], "abend"), (f10a, "sonne"), (regen10, "regen"), (uhr17, "abend"), (S[10][0], "sonne")]
    SW.wetter(T, SP, plan, *f_alle)
    SW.regen(T, SP, coll, SP.p(0, 0, 0), (24, 46, 9), 240, *f_alle, lambda f: SP.wetter_an("regen", f), seed=5)
    SW.regen(T, SP, coll, LO + V(0, 0, 0), (12, 10, 7), 90, *f_alle, lambda f: SP.wetter_an("regen", f), seed=9)

    # Fussgaenger in der Stadt (Chibi-Figuren auf Wegpunkten), Dichte je Szene
    y_ow = -1.75
    wege = {
        "ow_s": [(-10.5, y_ow - 0.95), (10.5, y_ow - 0.95), (10.5, y_ow - 1.05), (-10.5, y_ow - 1.05)],
        "ow_n": [(10.5, y_ow + 0.95), (-10.5, y_ow + 0.95), (-10.5, y_ow + 1.05), (10.5, y_ow + 1.05)],
        "markt": [(-5.0 + 2.8 * math.cos(a * math.pi / 6), 3.0 + 2.8 * math.sin(a * math.pi / 6)) for a in range(12)],
        "ns": [(0.25, -4.0), (0.25, 17.0), (1.85, 17.0), (1.85, -4.0)],
        "kalle": [(-6.7, y_ow - 0.9), (-6.7, -10.5), (-3.8, -10.5), (-3.8, -10.0), (-6.3, -10.0), (-6.3, y_ow - 0.9)],
        "bhf": [(1.5, -6.0), (8.6, -6.0), (8.6, -6.6), (1.5, -6.6)],
        "neu": [(2.6, 6.0), (10.0, 6.0), (10.0, 12.0), (2.6, 12.0)],
    }
    typen = KU.TYPEN
    walker = []
    n_w = 0
    for weg, anz, tempo in (("ow_s", 7, 0.9), ("ow_n", 7, 0.85), ("markt", 8, 0.7), ("ns", 6, 0.9), ("kalle", 5, 0.8),
                            ("bhf", 8, 1.0), ("neu", 5, 0.75)):
        pts = [SP.p(x, y, 0.05) for x, y in wege[weg]]
        laenge = sum((Vector(a) - Vector(bb)).length for a, bb in zip(pts, pts[1:] + pts[:1]))
        for j in range(anz):
            typ = typen[(n_w * 3 + j) % 5] if (n_w + j) % 9 else "familie"
            w = KU.bauen(coll, f"fg_{weg}{j}", typ=typ)
            SW.zusammenfassen(w)
            SW.outlines_fuer(w.root, 0.025)
            SW.schatten(w.root.name, coll, 0.45, 0.4, 0.4, parent=w.root, rund=True)
            fn = SW.wegpunkte_fn(pts, tempo, phase=laenge * j / anz)
            SW.laufen(T, w, fn, *f_alle, beine=w.beine)
            KU.schirm_bei_regen(T, w, SP, *f_alle)
            walker.append((w, fn, weg, (n_w * 0.618) % 1.0))
            n_w += 1

    def dichte(weg, f):
        """Anteil sichtbarer Fussgaenger: Regen leert die Strassen, morgens am Bahnhof viele Pendler (Szene 11)."""
        r = SP.wetter_an("regen", f)
        base = 1.0 - 0.75 * r
        if weg == "bhf":
            base = max(base, 1.0 if S[10][0] <= f < S[10][1] else 0.0)
        return base
    for w, fn, weg, schwelle in walker:
        T.set(w.root, "scale", lambda f, weg=weg, s_=schwelle: (1, 1, 1) if s_ < dichte(weg, f) else (0, 0, 0), *f_alle)
    # Schirm-Gedankenblasen (Regen in Szene 7: man bleibt zu Hause)
    for j, (w, fn, weg, s_) in enumerate([x for x in walker if x[2] in ("ow_s", "ow_n", "markt")][:7]):
        gb = GB.bauen(coll, f"gb_schirm{j}", symbol="schirm", s=1.1)
        GB.zeigen(T, gb, lambda f, fn=fn: fn(f)[0] + V(0, 0, 1.75), regen7 + 4 + 3 * j, f7b - 4, *f_alle)
    # Fahrzeuge auf der Strasse
    for name, spur, tempo, ph in (("sw_auto_rot", 0, 3.2, 0.0), ("sw_auto_blau", 1, 2.6, 9.0), ("sw_bus", 1, 2.2, 25.0)):
        y = y_ow + (0.35 if spur == 0 else -0.35)
        pts = [SP.p(-10.8, y, 0.02), SP.p(10.8, y, 0.02)] if spur == 0 else [SP.p(10.8, y, 0.02), SP.p(-10.8, y, 0.02)]
        lauf = SW.wegpunkte_fn(pts, tempo, phase=ph, loop=True)
        fn = (lambda f, lauf=lauf, pts=pts: (lauf(f)[0], Vector(pts[1]) - Vector(pts[0])))
        SW.laufen(T, I[name], fn, *f_alle, huepfen=0.0, wippen=False)
    # Zug: faehrt in Szene 1 ein, in Szene 11 wieder (mit Pendlern)
    zug = I["sw_zug"]
    gy = I["sw_bahnhof"].root.location.y + I["sw_bahnhof"].gleis_y
    x_halt = SP.p(4.2, 0, 0).x
    x_weg = SP.p(18.0, 0, 0).x
    T.set(zug.root, "location", lambda f: (x_weg + (x_halt - x_weg) * ease_out(clamp01((f - 6) / 70)) if f < S[1][1]
                                           else (x_weg + (x_halt - x_weg) * ease_out(clamp01((f - S[10][0] - 8) / 50))
                                                 if f >= S[10][0] else x_halt), gy, 0.15), *f_alle)
    KAT("bahnhof").uhr_stellen(T, I["sw_bahnhof"], lambda f: 7 * 60 + 15, *f_alle)
    # Spieler-Marker senkt sich in Szene 2 auf Kalles Laden; Filiale 2: Bauplatz -> Baustelle -> eroeffnet (S11),
    # nach NOCHMAL (S13) wieder Bauplatz
    f2a, f2b = S[1]
    KAT("spieler_marker").zustand(T, I["sw_marker"], [(0, "aus"), (f2a + 6, "senkt"), (S[2][0], "aus")], *f_alle)
    f11a, f11b = S[10]
    f_bau = f11a + int(0.52 * (f11b - f11a))
    f_auf = f_bau + 15                                   # Kran und Staubwolke 0,5 s
    KAT("filiale").zustand(T, I["sw_filiale"], [(0, "bauplatz"), (f_bau, "baustelle"), (f_auf, "eroeffnet"), (S[12][0], "bauplatz")],
                           *f_alle, coll=coll)
    KAT("sternchen").an(T, I["sw_sterne_filiale"], f_auf + 2, f_auf + 50, *f_alle)
    cue(f_auf + 2, "ding8", 0.8)
    # Mini-Lea am Bauplatz (S11): Daumen hoch nach der Eroeffnung
    ml_s = KAT("mini_lea").bauen(coll, "ml_stadt")
    SW.zusammenfassen(ml_s)
    SW.outlines_fuer(ml_s.root, 0.025)
    SW.schatten(ml_s.root.name, coll, 0.45, 0.4, 0.4, parent=ml_s.root, rund=True)
    fil = I["sw_filiale"].root.location
    T.set(ml_s.root, "location", lambda f: tuple(fil + V(-1.9, -1.4, 0.05)) if f11a <= f < f11b else tuple(WEG), *f_alle)
    T.set(ml_s.root, "rotation_euler", lambda f: (0, 0, -0.5), *f_alle)
    KAT("mini_lea").animation(T, ml_s, "daumen_hoch", f_auf + 4, f11b)
    # Pendler-Schlange vor der Filiale nach der Eroeffnung, mit Herz-Gedankenblasen
    for j in range(7):
        pk = KU.bauen(coll, f"pendler_q{j}", typ=["pendler", "pendler", "schueler", "oma", "joggerin", "pendler", "familie"][j])
        SW.zusammenfassen(pk)
        SW.outlines_fuer(pk.root, 0.025)
        SW.schatten(pk.root.name, coll, 0.45, 0.4, 0.4, parent=pk.root, rund=True)
        ziel = fil + V(-0.6 + 0.0 * j, -1.6 - 0.75 * j, 0.05)
        start = fil + V(6.0 - 0.4 * j, -2.8 - 0.3 * j, 0.05)
        ft = f_auf + 4 + 3 * j
        T.set(pk.root, "location", lambda f, a=start, z=ziel, ft=ft: tuple(Vector(a).lerp(Vector(z), ease_out(clamp01((f - ft) / 18))))
              if f11a <= f < f11b else tuple(WEG), *f_alle)
        T.set(pk.root, "rotation_euler", lambda f: (0, 0, -1.2), *f_alle)
        if j < 3:
            gb = GB.bauen(coll, f"gb_herz{j}", symbol="herz", s=1.0)
            GB.zeigen(T, gb, lambda f, z=ziel: Vector(z) + V(0, 0, 1.6), ft + 20, f11b - 2, *f_alle)

    # ============================================================ Laden (Puppenhaus): Figuren, Kunden, Waren
    m_weg = SW.m("weg", "weg", 0.8)
    L.box("laden_gehweg", (5.4, 1.7, 0.3), m_weg, None, lp(-6.95, -1.75, -0.12), coll)
    L.box("laden_gehweg_rand", (5.6, 1.9, 0.5), SW.m("erde", "erde", 0.8), None, lp(-6.95, -1.75, -0.45), coll)
    theke, kasse, tonne, ofen, lager = I["sw_theke"], I["sw_kasse"], I["sw_tonne"], I["sw_ofen"], I["sw_lager"]
    # Preisschild Brezel: 1,20 (Lea, Standard) oder 0,50 (Kalle, Szenen 5-8); andere Faecher ohne Zahl
    tag0 = theke.schilder[0]
    t120 = bpy.data.objects[f"{'sw_theke'}_pst0"]
    t050 = SW.text("sw_theke_pst0_050", "0,50 €", 0.15, SW.m("preis_rot", "#C9302C", 0.5), tag0, (0, -0.03, -0.05), coll)
    for j in (1, 2):
        bpy.data.objects[f"sw_theke_pst{j}"].scale = (0, 0, 0)
    kalle_preis = lambda f: S[4][0] <= f < S[8][0]     # noqa: E731
    T.set(t120, "scale", lambda f: (0, 0, 0) if kalle_preis(f) else (1, 1, 1), *f_alle)
    T.set(t050, "scale", lambda f: (1, 1, 1) if kalle_preis(f) else (0, 0, 0), *f_alle)
    # Mini-Kalle hinter der Theke (S5-S8), Mini-Lea (S10), Mini-Byte (S6)
    mk = KAT("mini_kalle").bauen(coll, "mk")
    mlf = KAT("mini_lea").bauen(coll, "ml_laden")
    mb = KAT("mini_byte").bauen(coll, "mb")
    for o in (mk, mlf):
        SW.zusammenfassen(o)
        SW.outlines_fuer(o.root, 0.025)
        SW.schatten(o.root.name, coll, 0.45, 0.4, 0.4, parent=o.root, rund=True)
    f5a, f5b = S[4]
    f6a, f6b = S[5]
    f8a, f8b = S[7]
    sack_mk = lp(1.0, 0.1, 0.06)
    T.set(mk.root, "location", lambda f: tuple(lp(-0.6, -0.1, 0.06)) if f5a - 10 <= f < f8a + 4 else
          (tuple(sack_mk + V(0, 0, 0.5)) if f8a + 4 <= f < f8b + 2 else tuple(WEG)), *f_alle)
    T.set(mk.root, "rotation_euler", lambda f: (0, 0, 0.0), *f_alle)
    KAT("mini_kalle").animation(T, mk, "kassieren", f5a - 10, f8a + 4)
    KAT("mini_kalle").animation(T, mk, "verzweifelt", f8a + 4, f8b + 2)
    sack = L.empty("mk_sack", None, sack_mk, coll)
    SW.rbox("mk_sack_m", (0.5, 0.4, 0.5), SW.m("sack", "#E3CFA4", 0.8), sack, (0, 0, 0.25), coll, r=0.14)
    SW.text("mk_sack_t", "WEIZEN 550", 0.07, SW.m("sack_ink", "#8A5A2E", 0.6), sack, (0, -0.21, 0.22), coll)
    SW.outlines_fuer(sack, 0.025)
    T.set(sack, "scale", lambda f: (1, 1, 1) if f8a <= f < f8b + 2 else (0, 0, 0), *f_alle)
    W.anchors["minikalle"] = mk.root
    T.set(mlf.root, "location", lambda f: tuple(lp(-0.6, -0.1, 0.06)) if f10a - 10 <= f < f10b + 4 else tuple(WEG), *f_alle)
    KAT("mini_lea").animation(T, mlf, "kassieren", f10a - 10, f10b + 4)
    mb_pos = lambda f: lp(2.0, -0.84, 2.3) if f6a - 4 <= f < f6b + 4 else WEG    # noqa: E731
    KAT("mini_byte").schweben(T, mb, mb_pos, *f_alle)
    T.set(mb.pfeil, "scale", lambda f: (1, 1, 1) if f6a + 6 <= f < f6b else (0, 0, 0), *f_alle)
    T.set(mb.pfeil, "rotation_euler", lambda f: (math.pi, 0, 0), *f_alle)
    T.set(mb.pfeil, "location", lambda f: (0, 0, 0.55 + 0.1 * abs(math.sin(f * 0.25))), *f_alle)

    # Kunden-Schlange: Gehweg -> Tuer -> Theke -> Kasse -> raus (Szenen 5-6 viele, Szene 10 weniger)
    q_pts = [lp(-9.4, -1.45, 0.06), lp(-3.6, -1.45, 0.06), lp(-1.6, -1.65, 0.06), lp(1.5, -1.65, 0.06), lp(2.0, -1.8, 0.06),
             lp(1.5, -2.5, 0.06), lp(-3.6, -2.05, 0.06), lp(-9.4, -2.05, 0.06)]
    q_len = sum((Vector(a) - Vector(bb)).length for a, bb in zip(q_pts, q_pts[1:] + q_pts[:1]))
    d_kasse = sum((Vector(a) - Vector(bb)).length for a, bb in zip(q_pts[:4], q_pts[1:5]))

    def schlange(pre, n, tempo, fa, fb, typ_ofs=0, blasen=0):
        verk = []
        for j in range(n):
            typ = typen[(j + typ_ofs) % 5]
            ku = KU.bauen(coll, f"{pre}{j}", typ=typ)
            SW.zusammenfassen(ku)
            SW.outlines_fuer(ku.root, 0.025)
            SW.schatten(ku.root.name, coll, 0.45, 0.4, 0.4, parent=ku.root, rund=True)
            ph = q_len * j / n
            fn = SW.wegpunkte_fn(q_pts, tempo, phase=ph - (fa / FPS) * tempo)
            SW.laufen(T, ku, fn, fa - 2, fb + 2, beine=ku.beine)
            KU.schirm_bei_regen(T, ku, SP, fa - 2, fb + 2)
            T.set(ku.root, "scale", lambda f, fn=fn: (1, 1, 1) if fa - 2 <= f < fb + 2 and fn(f)[0].x > LO.x - 9.2 else (0, 0, 0),
                  *f_alle)
            # Verkaufszeitpunkte (Vorbeigehen an der Kasse)
            for f in range(fa, fb):
                d0 = (ph - (fa / FPS) * tempo + (f - 1) * tempo / FPS) % q_len
                d1 = (ph - (fa / FPS) * tempo + f * tempo / FPS) % q_len
                if d0 < d_kasse <= d1:
                    verk.append(f)
            if j < blasen:
                gb = GB.bauen(coll, f"gb_{pre}{j}", symbol="brezel", s=1.0)
                GB.zeigen(T, gb, lambda f, fn=fn: fn(f)[0] + V(0, 0, 1.5), fa + 4 + 4 * j, fb - 2, *f_alle)
        return sorted(verk)
    verk5 = schlange("ks", 11, 1.4, f5a, f6b, 0, blasen=5)
    verk10 = schlange("kl", 6, 1.0, f10a, uhr17 + 30, 2, blasen=0)
    KAT("kasse").verkaeufe(T, kasse, verk5 + verk10, *f_alle)
    KAT("muenz_pop").ausloesen(T, I["sw_muenzen"], [v for v in verk5 if v < f6b] + verk10, *f_alle)
    for j, v in enumerate([v for v in verk5 if v < f5b]):
        if j % 2 == 0:
            cue(v, "pop8", 0.45)
    # Herz-Gedankenblasen bei Lea (zufriedene Kunden)
    # Auslage: Brezel-Fach (0) nach Verkaeufen, Szene 7 voll (500 Brezeln), Szene 8 Reste -> Tonne, Szene 10 ausverkauft
    flug8_0 = f8a + 6

    def brezeln(f):
        if f < f5a:
            return 9
        if f < f6b:
            return max(3, 12 - sum(1 for v in verk5 if v <= f))
        if f < f7a + int(0.8 * (f7b - f7a)):
            return 4
        if f < flug8_0:
            return 12
        if f < S[8][0]:
            return max(0, 12 - int((f - flug8_0) / 2.5))
        if f < f10a:
            return 0
        if f < uhr17 + 40:
            return max(0, 10 - sum(1 for v in verk10 if v <= f) - (4 if f >= uhr17 + 10 else 0) - (3 if f >= uhr17 + 22 else 0))
        return 0 if f < S[12][0] else 9
    WA_TH = KAT("theke_auslage")
    WA_TH.menge(T, theke, 0, brezeln, *f_alle)
    WA_TH.menge(T, theke, 1, lambda f: 6, *f_alle)
    WA_TH.menge(T, theke, 2, lambda f: 4, *f_alle)
    WA_TH.halbpreis(T, theke, uhr17 + 4, *f_alle)
    T.set(theke.halbpreis, "scale", lambda f: (1, 1, 1) if uhr17 + 12 <= f < f10b + 2 else
          ((pop(f, uhr17 + 4, 8),) * 3 if uhr17 + 4 <= f < uhr17 + 12 else (0, 0, 0)), *f_alle)
    for w in theke.stapel[0]:
        WA.farbe(T, w, [(0, "fertig"), (f8a, "rest"), (S[8][0], "fertig")], *f_alle)
    # Reste fliegen in die Tonne (S8)
    ton_pos = tonne.root.location + V(0, 0, 1.0)
    for j in range(12):
        w = WA.bauen(coll, f"rest_flug{j}", art="brezel", s=1.1)
        WA.farbe(T, w, [(0, "rest")], *f_alle)
        st = flug8_0 + int(2.5 * j)
        von = theke.root.location + V(-1.5 + 0.3 * (j % 3), -0.15, 1.1)
        WA.flug(T, w, von, ton_pos, st, dauer=12, hoehe=1.2, f0=0, f1=N - 1)
        T.set(w.root, "scale", lambda f, st=st: (1.1,) * 3 if st <= f < st + 12 else (0, 0, 0), *f_alle)
    # Tonne: leer, in S8 voll (Deckel springt auf), bleibt voll bis zum neuen Spiel (S10 leer)
    KAT("tonne_reste").fuellstand(T, tonne, lambda f: (clamp01((f - flug8_0) / 32) if f8a <= f < S[9][0] else 0.0), *f_alle)
    # Ofen: S7 backt 500 Brezeln (glueht), S8 fertig, S10 backt -> fertig
    f7_laden = f7a + int(0.7 * (f7b - f7a))
    KAT("ofen").zustand(T, ofen, [(0, "aus"), (f7_laden - 10, "backt"), (f8a, "fertig"), (S[8][0], "aus"), (f10a + 10, "backt"),
                                  (f10a + 70, "fertig"), (S[10][0], "aus")],
                        lambda f: clamp01((f - f7_laden + 10) / 40) if f < f8a else clamp01((f - f10a - 10) / 60), *f_alle)
    KAT("lagerregal").anzahl(T, lager, lambda f: 6 if f < f7_laden else (max(1, 6 - int((f - f7_laden) / 8)) if f < S[8][0]
                                                                        else (6 if f < f10a + 10 else 5)), *f_alle)
    KAT("duftlinien").an(T, I["sw_duft_wagen"], f7_laden + 20, f8a, *f_alle)
    KAT("duftlinien").an(T, I["sw_duft_theke"], f10a + 75, uhr17, *f_alle)

    # ============================================================ Kameras Spielwelt
    stadt1 = SW.spiel_stadt(SP, 0, N, abstand=66.0)
    laden_cam = SW.spiel_laden(SP, 0, N, ziel=LO + V(-1.3, -0.9, 1.2), abstand=25.0)
    kalle_nah = SW._iso(I["sw_kalle"].root.location + V(0, 1.0, 0.8), 26.0, 50.0)
    bhf_nah = SW._iso(I["sw_filiale"].root.location + V(0, -1.2, 0.6), 34.0, 50.0)

    # ------------------------------------------------------------ Szene 1: Totale (Hook), keine Spielanzeige
    f1a, f1b = S[0]
    cam.add_shot(f1a, f1b, stadt1)

    # ------------------------------------------------------------ Szene 2: Flug zum Laden, Mission, Anzeige baut sich auf
    flug2 = SW.spiel_flug(stadt1, kalle_nah, f2a + 4, f2a + int(0.55 * (f2b - f2a)))

    # ------------------------------------------------------------ Szene 3: aus_spiel -> Buero, Byte auf dem Monitor
    f3a, f3b = S[2]
    cue(f3a - 2, "whoosh", 0.8)
    A3 = (BU.p(-0.85, -3.3, 1.65), BU.p(0.1, 0.05, 1.3), 30.0)
    aus3 = KA.aus_spiel(W, flug2, MON_M, MON_N, f3a, A3, abflug=26)
    cam.add_shot(f2a, f2b, aus3)
    cam.add_shot(f3a, f3b, aus3)
    C.byte_face(T, b, [(f3a, "jubel"), (f3a + 40, "neutral"), (S[3][0], "zweifel")], f3a, S[4][0])
    C.byte_arm(T, b, "R", (-0.4, 0.0, 1.9), f3a + 6, wd(2, "gebaut") + 4, ramp=6)    # zeigt stolz auf den Monitor
    C.kalle_look(T, k, lambda f: MON_M, 0, N - 1, strength=0.7, ramp=4)
    C.kalle_react(T, k, "staunen", f3a + 10, hold=30, hat=False)
    verkehrt = lambda f: 1.0 if f < S[3][1] - 32 else 1.0 - ease_in_out(clamp01((f - (S[3][1] - 32)) / 12))   # noqa: E731
    T.set(ck.body, "rotation_euler", lambda f: (math.pi * verkehrt(f), 0, 0), *f_alle)
    cl.body.rotation_euler = (0, 0, 0)

    # ------------------------------------------------------------ Szene 4: Kalle ratlos, Controller vibriert, Byte dreht ihn
    f4a, f4b = S[3]
    cam.whips.append((f4a, 1))
    cue(f4a - 2, "whoosh", 0.6)
    A4 = (BU.p(-1.05, -2.5, 1.6), K_SITZ + V(0.05, 0, 1.38), 32.0)
    B4 = (BU.p(-0.9, -1.9, 1.62), K_SITZ + V(0.05, 0, 1.42), 36.0)
    zg4 = zoom_gesicht(f4a, f4b - 14, A4, B4)
    C.kalle_react(T, k, "zweifel", hl(3), hold=f4b - hl(3) - 4, speaking=True, hat=False)
    T.add(ck.root, "rotation_euler", lambda f: (0, 0.5 * math.sin((f - f4a) * 0.25) * window(f, f4a + 2, f4a + 30, 4, 6), 0),
          f4a, f4a + 32)
    vib = f4a + 32
    BSP.knopf_druck(T, ck, vib - 2, 1)
    BSP.vibrieren(T, ck, vib, dur=14, amp=0.01)
    C.kalle_react(T, k, "schock", vib + 2, hold=8, speaking=True, hat=False)
    flip = f4b - 34
    setze_byte(f3a, f4a, B_MON)
    T.set(b.root, "location", lambda f: tuple(B_MON.lerp(K_SITZ + V(0.55, -0.55, 1.55), ease_in_out(clamp01((f - flip + 16) / 14)))),
          flip - 16, f4b)
    C.byte_arm(T, b, "R", (-1.2, 0.0, 0.6), flip - 4, f4b - 2, ramp=5)
    C.byte_arm(T, b, "L", (-1.2, 0.0, -0.6), flip - 4, f4b - 2, ramp=5)
    C.byte_hand(T, b, "R", "grab", flip - 2, f4b - 4)
    C.byte_hand(T, b, "L", "grab", flip - 2, f4b - 4)

    # ------------------------------------------------------------ Szene 5: ins_spiel -> Laden, Preis 0,50, Schlange
    cue(f5a - 2, "whoosh", 0.8)
    L5a = laden_cam
    L5b = SW.spiel_laden(SP, 0, N, ziel=LO + V(-4.9, -1.8, 1.2), abstand=25.0)
    schwenk5 = lambda f: (lambda a, bb, t: (Vector(a[0]).lerp(Vector(bb[0]), t), Vector(a[1]).lerp(Vector(bb[1]), t), a[2]))(  # noqa: E731
        L5a(f), L5b(f), ease_in_out(clamp01((f - f5a - 40) / max(1, f5b - f5a - 44))))
    ins5 = KA.ins_spiel(W, zg4, MON_M, MON_N, f5a, schwenk5, anflug=14)
    cam.add_shot(f4a, f4b, ins5)
    cam.add_shot(f5a, f5b, ins5)
    T.set(b.root, "location", lambda f: tuple(K_SITZ + V(1.2, -0.2, 2.0)), f5a, S[8][0])
    C.kalle_react(T, k, "jubel", hl(4), hold=f5b - hl(4) - 2, speaking=True, hat=False)
    for j, fk in enumerate(range(f5a + 4, f5b - 4, 7)):
        BSP.knopf_druck(T, ck, fk, j % 4)
    T.add(ck.root, "location", lambda f: (0.012 * math.sin(f * 1.7), 0, 0.01 * math.sin(f * 2.3)), f5a, f5b)

    # ------------------------------------------------------------ Szene 6: Mini-Byte zeigt auf den Geld-Balken
    cam.whips.append((f6a, -1))
    cam.add_shot(f6a, f6b, push_in(f6a, f6b, laden_cam(f6a), k=0.12))
    rot6 = wd(5, "neunzig")
    cue(rot6, "buzz", 0.55)
    C.kalle_react(T, k, "zweifel", f6a + 6, hold=f6b - f6a - 8, hat=False)

    # ------------------------------------------------------------ Szene 7: Zeitraffer, TAG 2, Regen, 500 im Ofen
    cam.whips.append((f7a, 1))
    stadt7 = SW.spiel_stadt(SP, 0, N, abstand=66.0, drift=2.0)
    cam.add_shot(f7a, f7b, SW.spiel_flug(stadt7, laden_cam, f7_laden - 22, f7_laden + 6))
    C.kalle_react(T, k, "neutral", f7a + 10, hold=20, hat=False)

    # ------------------------------------------------------------ Szene 8: Reste in die Tonne, PLEITE
    pleite = wd(7, "pleite") + 2
    pleite = max(pleite, flug8_0 + 34)
    pleite = min(pleite, f8b - 24)
    stopp8 = lambda f: laden_cam(min(f, pleite))       # noqa: E731  harter Stopp beim PLEITE
    cue(pleite, "buzz", 0.8)
    W.wackeln = [[pleite, 14, 12]]
    C.kalle_react(T, k, "schock", hl(7), hold=f8b - hl(7), speaking=True, hat=False)
    C.pose(T, k, "hands_up", hl(7) - 2, S[8][0] + 6, 4, 10)
    T.add(ck.root, "location", lambda f: (0, 0, 0.06 * window(f, hl(7) - 2, hl(7) + 10, 3, 8)), hl(7) - 3, hl(7) + 12)

    # ------------------------------------------------------------ Szene 9: aus_spiel, Lea kommt, nimmt den Controller
    f9a, f9b = S[8]
    cue(f9a - 2, "whoosh", 0.8)
    A9 = (BU.p(-1.25, -3.9, 1.75), BU.p(-0.75, -0.1, 1.42), 27.0)
    aus9 = KA.aus_spiel(W, stopp8, MON_M, MON_N, f9a, A9, abflug=24)
    cam.add_shot(f8a, f8b, aus9)
    L_TUER = BU.p(-3.0, -0.4, 0)
    L_DA = L_STEH
    T.set(l.root, "location", lambda f: tuple(L_TUER.lerp(L_DA, ease_in_out(clamp01((f - f9a - 2) / 18)))), f9a, f9b)
    T.set(l.root, "rotation_euler", lambda f: (0, 0, -0.9 + (L_RZ + 0.9) * ease_in_out(clamp01((f - f9a - 2) / 18))), f9a, f9b)
    T.set(l.root, "scale", lambda f: (1, 1, 1), f9a, f9b)
    f_uebergabe = wd(8, "mal")
    C.pose(T, l, {"sh_R": (-1.3, 0.4, 0.2), "el_R": (-0.6, 0, 0)}, f_uebergabe - 10, f_uebergabe + 4, 6, 6)
    C.pose(T, l, HALTEN, f_uebergabe + 2, None, 8, 1, settle=False)
    T.set(ck.root, "scale", lambda f: (1, 1, 1) if f < f_uebergabe else (0, 0, 0), *f_alle)
    T.set(cl.root, "scale", lambda f: (1, 1, 1) if f >= f_uebergabe else (0, 0, 0), *f_alle)
    LE.lea_react(T, l, "jubel", hl(8), hold=f9b - hl(8) - 2, speaking=True)
    C.kalle_look(T, l, lambda f: K_SITZ + V(0, 0, 1.5) if f < f_uebergabe + 6 else MON_M, f9a, N - 1, ramp=6)
    # Kalle rutscht zur Seite, verschraenkt die Arme
    T.add(k.root, "location", lambda f: (-0.28 * ease_in_out(clamp01((f - f_uebergabe) / 12)), 0, 0), f_uebergabe, S[12][0])
    arme_vor = {"sh_R": (-1.2, -0.55, 0.0), "sh_L": (-1.2, 0.55, 0.0), "el_R": (-1.9, 0, -0.5), "el_L": (-1.9, 0, 0.5)}
    f12a, f12b = S[11]
    C.pose(T, k, arme_vor, f_uebergabe + 4, f12a + 20, 8, 10)
    C.kalle_react(T, k, "zweifel", f_uebergabe + 6, hold=f9b - f_uebergabe - 6, hat=False)
    C.kalle_look(T, k, lambda f: L_DA + V(0, 0, 1.6), f9a + 4, f_uebergabe + 20, ramp=6)

    # ------------------------------------------------------------ Szene 10: ins_spiel -> Leas Spiel (Laden)
    cue(f10a - 2, "whoosh", 0.8)
    L10a = laden_cam
    L10b = SW.spiel_laden(SP, 0, N, ziel=LO + V(0.2, -0.6, 1.2), abstand=24.0)
    schwenk10 = lambda f: (lambda a, bb, t: (Vector(a[0]).lerp(Vector(bb[0]), t), Vector(a[1]).lerp(Vector(bb[1]), t), a[2]))(  # noqa: E731
        L10a(f), L10b(f), ease_in_out(clamp01((f - uhr17 + 10) / 40)))
    ins10 = KA.ins_spiel(W, aus9, MON_M, MON_N, f10a, schwenk10, anflug=16)
    cam.add_shot(f9a, f9b, ins10)
    cam.add_shot(f10a, f10b, ins10)
    erfolg10 = min(f10b - 34, uhr17 + 44)
    cue(erfolg10 + 2, "pop8", 0.6)
    T.set(b.root, "location", lambda f: tuple(K_SITZ + V(1.25, -0.1, 2.0)), f9a, S[12][0])
    LE.lea_react(T, l, "jubel", f10a + 8, hold=f10b - f10a - 10)

    # ------------------------------------------------------------ Szene 11: Tag 30, Flug zum Bahnhof, Filiale 2
    cam.whips.append((f11a, 1))
    flug11 = SW.spiel_flug(lambda f: SW._iso(I["sw_kalle"].root.location + V(0, 2.0, 0.8), 34.0, 50.0), bhf_nah, f11a + 4, f_bau - 6)
    LE.lea_react(T, l, "jubel", f_auf, hold=f11b - f_auf - 2)
    C.pose(T, l, "hands_up", f_auf, f11b, 4, 8)

    # ------------------------------------------------------------ Szene 12: aus_spiel, Kalle geruehrt
    cue(f12a - 2, "whoosh", 0.7)
    A12 = (BU.p(-1.15, -2.4, 1.6), K_SITZ + V(-0.1, 0, 1.4), 34.0)
    B12 = (BU.p(-1.0, -2.0, 1.62), K_SITZ + V(-0.2, 0, 1.42), 38.0)
    zg12 = zoom_gesicht(f12a + 26, f12b, A12, B12, ease=ease_in_out)
    aus12 = KA.aus_spiel(W, flug11, MON_M, MON_N, f12a, zg12, abflug=26)
    cam.add_shot(f11a, f11b, aus12)
    cam.add_shot(f12a, f12b, aus12)
    C.kalle_look(T, k, lambda f: (L_DA + V(0, 0, 1.6)) if (f < f12a + 14 or f > f12a + 32) else MON_M, f12a, f12b, ramp=8)
    C.kalle_react(T, k, "geruehrt", hl(11) - 6, hold=f12b - hl(11) + 2, speaking=True, hat=False)
    klopf = hl(11) + 10
    C.pose(T, k, {"sh_L": (-1.4, 0.9, 0.2), "el_L": (-0.7, 0, 0)}, klopf - 8, f12b - 2, 8, 8)
    T.add(k.el["L"], "rotation_euler", lambda f: (0.25 * math.sin((f - klopf) * 0.9) * window(f, klopf, klopf + 16, 2, 4), 0, 0),
          klopf - 1, klopf + 17)
    LE.lea_react(T, l, "geruehrt" if "geruehrt" in getattr(C, "REAKTIONEN", ()) else "jubel", hl(11) + 4, hold=f12b - hl(11) - 4)

    # ------------------------------------------------------------ Szene 13: Studio, Modell, NOCHMAL, Rueckspulen
    f13a, f13b = S[12]
    cam.whips.append((f13a, -1))
    cue(f13a - 2, "whoosh", 0.6)
    setze(k, f13a, S[13][0], WEG)
    setze(l, f13a, N, WEG)
    mod = BSP.spielstadt_modell(coll, "modell", s=0.085)
    M_POS = ST.p(-0.15, -0.35, 1.25)
    T.set(mod.root, "location", lambda f: tuple(M_POS + V(0, 0, 0.03 * math.sin(f * 0.1))), *f_alle)
    T.set(mod.root, "rotation_euler", lambda f: (0, 0, 0.15 * math.sin(f * 0.02)), *f_alle)
    T.set(mod.root, "scale", lambda f: (1, 1, 1) if f13a - 2 <= f < f13b + 2 else (0, 0, 0), *f_alle)
    druck = wd(12, "kosten") - 4
    BSP.rueckspulen(T, mod, druck, dauer=26, f0=0, f1=N - 1)
    knopf_w = mod.knopf.matrix_world.translation if False else M_POS + V(0.33, -0.36, 0.1)
    B13 = M_POS + V(0.72, 0.3, 0.5)
    T.set(b.root, "location", lambda f: tuple(B13.lerp(knopf_w + V(0.25, -0.15, 0.32), window(f, druck - 10, druck + 6, 8, 8))),
          f13a, f13b)
    C.byte_arm(T, b, "R", (-1.4, 0.0, 0.9), druck - 6, druck + 6, ramp=4)
    C.byte_hand(T, b, "R", "point", druck - 6, druck + 6)
    C.byte_face(T, b, [(f13a, "neutral"), (druck, "jubel"), (druck + 30, "neutral")], f13a, f13b)
    cue(druck, "pop8", 0.5)

    def kreis(f, a0=-35, a1=30, r=2.4, z=1.75, lens=30):
        t = ease_in_out(clamp01((f - f13a) / max(1, f13b - f13a)))
        a = math.radians(lerp(a0, a1, t))
        cen = M_POS + V(0.2, 0, 0.2)
        return (cen + V(r * math.sin(a), -r * math.cos(a), z - cen.z + 0.6), cen + V(0, 0, 0.05), lens)
    cam.add_shot(f13a, f13b, kreis)

    # ------------------------------------------------------------ Szene 14: echte Welt, OFFEN, Rueckverwandlung
    f14a, f14b = S[13]
    cam.whips.append((f14a, 1))
    sf = KA.schaufenster(coll, TH)
    KA.schaufenster_zeigen(T, sf, f14a - 1, N + 2)
    setze(k, f14a, N, TH.p(-0.9, -3.6, 0), 0.0)
    setze_byte(f14a, N, WEG)
    schild = BSP.schild_offen(coll, "schild")
    schild.root.location = TH.p(-0.9, -4.62, 2.35)
    T.set(schild.root, "scale", lambda f: (1, 1, 1) if f >= f14a - 1 else (0, 0, 0), *f_alle)
    f_schluessel = f14a + 4
    f_glocke = f14a + 18
    f_dreh = f14a + 30
    cue(f_schluessel, "schluessel", 0.35)
    cue(f_glocke, "tuerglocke", 0.35)
    BSP.drehen(T, schild, f_dreh, dur=16, f1=N - 1)
    C.pose(T, k, {"sh_R": (-2.3, 0.2, 0.2), "el_R": (-1.1, 0, 0)}, f_dreh - 10, f_dreh + 16, 6, 8)
    C.kalle_react(T, k, "geruehrt", f_dreh + 18, hold=f14b - f_dreh - 18, hat=False)
    fen = KA.durchs_fenster(sf, f14a, f14b, ziel=TH.p(-0.6, -3.6, 1.65), abstand=2.6, hoehe=1.7, lens=32.0, schwenk=0.2)
    # Morph: letzte Sekunde, nach 'Deine nicht' (mind. 0,25 s Luft); endet exakt wie Szene 1, Frame 0
    m_dauer = 30
    m0 = max(ende(13) + 8, f14b - m_dauer)
    m0 = min(m0, f14b - 12)
    m_dauer = f14b - m0
    cam.add_shot(f14a, f14b, KA.welt_zu_spiel(W, fen, m0 - 16, m0, lambda f: stadt1(0), dauer=m_dauer, hoehe=9.0))
    KA.zweitbild(W, m0, f14b, "spielwelt", lambda f: stadt1(0), "morph")
    W.morph = [{"f0": m0, "dauer": m_dauer}]

    # ============================================================ Facecam (Zweitbild): echte Figur reagiert live
    def facecam_shot(anker):
        def fn(f):
            hd = (k.head if anker == "kalle_face" else l.head).matrix_world
            face = W.anchors[anker].matrix_world.translation
            fwd = hd.to_3x3() @ Vector((0, -1, 0))
            fwd.z = 0
            fwd = fwd.normalized() if fwd.length > 1e-4 else Vector((0, -1, 0))
            return (face + fwd * 1.15 + Vector((0, 0, 0.06)), face + Vector((0, 0, -0.04)), 50.0)
        return fn
    fc = {4: "kalle_face", 5: "kalle_face", 7: "kalle_face", 9: "lea_face", 10: "lea_face"}
    for i, anker in fc.items():
        a_, z_ = S[i]
        KA.zweitbild(W, a_ + 2, z_ - 1, "buero", facecam_shot(anker), "facecam", groesse=(324, 400))

    # ============================================================ Spielanzeige [GAME] pro Frame
    def tag_bei(f):
        if f < f7a + 30:
            return 1
        if f < f10a:
            return 2
        if f < f11a:
            return 1
        return min(30, 1 + int(29 * clamp01((f - f11a - 4) / 36)))

    def geld(f):
        if f < f6a:
            return 0.5 + 0.08 * clamp01((f - f5a) / 30), True
        if f < f7a:
            t = clamp01((f - f6a - 6) / max(1, rot6 - f6a))
            return 0.58 - 0.4 * t, t < 0.5
        if f < f8a:
            return 0.18, False
        if f < S[8][0]:
            return max(0.02, 0.18 - 0.16 * clamp01((f - f8a) / max(1, pleite - f8a))), False
        if f < f11a:
            return 0.5 + 0.25 * clamp01((f - f10a) / max(1, f10b - f10a)), True
        return 0.75 + 0.25 * clamp01((f - f11a) / 40), True

    def top(f):
        g, gewinn = geld(f)
        nacht = (f7a + 12 <= f < f7a + 30) or (f8a <= f < S[8][0])
        t = {"tag": tag_bei(f), "geld": g, "gewinn": gewinn, "gefahr": (not gewinn) and g < 0.25, "nacht": nacht,
             "herzen": (5 if f < f6a else (3 if f < f7a else (2 if f < f8a else 1))) if f < S[8][0] else 5,
             "mehl": 1.0 if f < f7_laden else (max(0.0, 1 - (f - f7_laden) / 40) if f < S[8][0] else (0.85 if f < f11a else 1.0))}
        if f10a <= f < f10b and f >= uhr17:
            t["uhr"] = "17:00"
        if f5a <= f < f6b and any(0 <= f - v < 8 for v in verk5):
            t["blitz"] = max(v for v in verk5 if v <= f)
        return t

    def hud(f):
        if f2a <= f < f2b:
            t = f - f2a
            h = {"mission": {"f0": f2a + 8}}
            if t > 30:
                h["top"] = dict({"tag": 1, "geld": 0.5, "gewinn": True, "herzen": 5, "mehl": 1.0}, a=clamp01((t - 30) / 8))
            if t > 44:
                h["aktion"] = {"a": clamp01((t - 44) / 8)}
            return h
        if f5a <= f < f6b:
            h = {"top": top(f), "aktion": {"gedrueckt": "PREIS", "f_druck": f5a + 6},
                 "regler": {"f0": f5a + 2, "preis": "0,50 €" if f >= f5a + 18 else "1,20 €",
                            "pos": 0.55 - 0.45 * ease_in_out(clamp01((f - f5a - 6) / 12)), "farbe": "rot" if f >= rot6 else None},
                 "facecam": {"f0": f5a + 2, "f1": f6b - 1}}
            if f >= f6a:
                h["tipp"] = {"f0": f6a + 8, "text": "Kosten 0,90 €\n> Preis 0,50 €", "xy": (404, 852), "ziel": (330, 640)}
            return h
        if f7a <= f < f7b:
            h = {"top": top(f), "aktion": {"gedrueckt": "BACKEN", "f_druck": f7_laden - 4}}
            if f7a + 30 <= f < regen7 - 2:
                h["banner"] = {"f0": f7a + 30, "f1": regen7 - 4, "text": "TAG 2", "icon": "stern", "farbe": "gold"}
            if f >= regen7:
                h["banner"] = {"f0": regen7, "f1": f7_laden - 26, "text": "REGEN!", "icon": "wolke"}
            if f >= f7_laden - 10:
                h["menge"] = {"f0": f7_laden - 10, "wert": 500, "klick": "+", "f_klick": f7_laden - 2, "gross": True}
            return h
        if f8a <= f < f8b:
            h = {"top": top(f), "facecam": {"f0": f8a + 2, "f1": f8b - 1}}
            if f >= pleite:
                h["pleite"] = {"f0": pleite, "spot": "minikalle", "knopf_nach": 18, "x": 662, "y": 930}
            return h
        if f10a <= f < f10b:
            h = {"top": top(f), "facecam": {"f0": f10a + 2, "f1": f10b - 1},
                 "regler": {"f0": f10a + 4, "preis": "1,20 €", "pos": 0.25 + 0.3 * ease_in_out(clamp01((f - f10a - 8) / 12))},
                 "aktion": {"gedrueckt": "PREIS" if f < regen10 else "BACKEN", "f_druck": f10a + 8 if f < regen10 else regen10 + 10}}
            if regen10 <= f < uhr17:
                h["banner"] = {"f0": regen10, "f1": regen10 + 34, "text": "REGEN!", "icon": "wolke"}
                h["menge"] = {"f0": regen10 + 8, "wert": None, "stufe": 1.0 - 0.6 * ease_in_out(clamp01((f - regen10 - 14) / 10)),
                              "klick": "-", "f_klick": regen10 + 16, "y0": 846}
            if f >= erfolg10:
                h["erfolg"] = {"f0": erfolg10, "text": "Null Reste!", "dauer": f10b - erfolg10, "hoch": True}
            return h
        if f11a <= f < f11b:
            h = {"top": top(f), "facecam": {"f0": f11a + 2, "f1": f11b - 1},
                 "aktion": {"gedrueckt": "BAUEN", "f_druck": f_bau - 4, "dauer": 16}}
            if f >= f_auf:
                h["levelup"] = {"f0": f_auf, "y": 900}
            return h
        return None
    W.hud_fn = hud
