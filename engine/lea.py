"""Lea, die Azubi (Engine 2.4). Gleicher Low-Poly-Stil und gleiche Gelenk-Logik wie Kalle (Pivot-Empties,
gleiche Attributnamen), deshalb funktionieren kalle_lipsync, kalle_look, pose, kalle_haende und kalle_react auch fuer Lea.

Merkmale: schlanker und juenger, dunkelbrauner Zopf (schwingt nach, faellt bei 'traurig' nach vorn), weisses
Baeckerkaeppi, weisse Schuerze ohne Mehlfleck, Aermel hochgekrempelt, grosse Augen mit Lidern und Brauen, Mehl an den
Fingern (Menge einstellbar), optional AR-Brille (schmal, transparent, tuerkiser Rand; auf der Nase oder in der Stirn).

Animation: lea_idle (Atmen, Gewicht, Zopf, unregelmaessiges Blinzeln), lea_lipsync (Mund nach Lautstaerke),
lea_react (alle Reaktionen inkl. 'traurig' und 'geruehrt'), haende_rollen / haende_schlingen / kalle_haende('kneten')
(auch fuer Kalle), lea_mehl (Mehl an den Fingern), lea_brille (Brille: 'ab', 'auf', 'stirn', Aufleuchten).
Figur schaut nach -Y (zur Kamera), ihre rechte Seite liegt bei -X.
"""
import math
import random

import bmesh
from mathutils import Vector

import look as L
import characters as C
from anim import window, ease_in_out, ease_out, spring

FPS = 30
HAAR = "#4A2E22"
SHIRT = "#6E9FB0"
SKIN = "#EDBB98"


class Lea:
    def __init__(self, coll):
        c = coll
        self.coll = coll
        m_skin = L.mat("lea_skin", SKIN, 0.62)
        m_skin2 = L.mat("lea_skin_dark", "#E0A07E", 0.62)
        m_cheek = L.mat("lea_cheek", "#EE9C88", 0.7)
        m_hair = L.mat("lea_hair", HAAR, 0.65)
        m_pants = L.mat("lea_pants", "#3B4A6E", 0.68)
        m_shirt = L.mat("lea_shirt", SHIRT, 0.66)
        m_apron = L.mat("lea_apron", "#FBFAF6", 0.62)
        m_white = L.mat("lea_cap", L.FLOUR, 0.6)
        m_eye = L.mat("eyewhite", "#FBF8F2", 0.5)
        m_pupil = L.mat("lea_pupil", "#3A2418", 0.5)
        m_glint = L.mat("glint", "#FFFFFF", 0.4, emit="#FFFFFF", strength=2.0)
        m_mouth = L.mat("mouth", "#4A1E26", 0.7)
        m_tongue = L.mat("tongue", "#C9656B", 0.6)
        m_shoe = L.mat("lea_shoe", "#2A2238", 0.6)
        self.root = L.empty("lea_root", coll=c)
        self.body = L.empty("lea_body", self.root, (0, 0, 0), c)
        # Beine (schlank, etwas laenger)
        self.hip, self.knee = {}, {}
        for side, sx in (("R", -1), ("L", 1)):
            hp = L.empty(f"l_hip_{side}", self.body, (sx * 0.12, 0, 0.84), c)
            L.cyl(f"l_thigh_{side}", 0.095, 0.44, 8, m_pants, hp, (0, 0, -0.2), c, r2=0.085)
            kn = L.empty(f"l_knee_{side}", hp, (0, 0, -0.41), c)
            L.cyl(f"l_shin_{side}", 0.08, 0.38, 8, m_pants, kn, (0, 0, -0.18), c, r2=0.07)
            L.box(f"l_shoe_{side}", (0.15, 0.26, 0.09), m_shoe, kn, (0, -0.05, -0.39), c, bevel=0.03)
            self.hip[side], self.knee[side] = hp, kn
        # Rumpf (schlank)
        self.hips = L.empty("l_hips", self.body, (0, 0, 0.84), c)
        self.torso = L.empty("l_torso", self.hips, (0, 0, 0.0), c)
        L.sphere("l_belly", 1.0, 14, 9, (0.3, 0.24, 0.42), m_shirt, self.torso, (0, 0, 0.36), c)
        # Schuerze (sauber, neu): Latz + Rock
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=9, radius=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.312, 0.252, 0.432)), verts=bm.verts)
        kill = [v for v in bm.verts if v.co.y > -0.08 or abs(v.co.x) > 0.25 or (v.co.z > 0.12 and abs(v.co.x) > 0.15)
                or v.co.z > 0.33]
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        L.from_bm("l_apron", bm, m_apron, self.torso, (0, 0, 0.36), c)
        L.torus("l_apronstrap", 0.1, 0.014, 12, 4, m_apron, self.torso, (0, -0.05, 0.72), c, axis="Z")
        self.skirt = L.empty("l_skirt", self.hips, (0, -0.16, -0.02), c)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=False, segments=14, radius1=0.34, radius2=0.29, depth=0.5)
        kill = [v for v in bm.verts if v.co.y > -0.04]
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bmesh.ops.translate(bm, vec=Vector((0, 0.16, -0.25)), verts=bm.verts)
        L.from_bm("l_apron_skirt", bm, m_apron, self.skirt, (0, 0, 0), c)
        for sx in (-1, 1):
            o = L.box(f"l_apronband{sx}", (0.24, 0.016, 0.03), m_apron, self.torso, (sx * 0.19, 0.15, 0.36), c)
            o.rotation_euler = (0, 0, sx * -0.95)
        bow = L.empty("l_apronbow", self.torso, (0, 0.26, 0.36), c)
        for sx in (-1, 1):
            L.sphere(f"l_apronloop{sx}", 0.04, 8, 5, (1.2, 0.35, 0.7), m_apron, bow, (sx * 0.04, 0, 0), c)
        self.apron_ends = []
        for sx in (-1, 1):
            e = L.empty(f"l_aproned{sx}", bow, (sx * 0.015, 0.01, -0.01), c)
            L.box(f"l_apronendm{sx}", (0.025, 0.01, 0.18), m_apron, e, (0, 0, -0.09), c)
            e.rotation_euler = (0, sx * 0.25, 0)
            self.apron_ends.append(e)
        self.apron_anchor = L.empty("l_apron_anchor", self.torso, (0.09, -0.27, 0.28), c)   # fuer den ersten Mehlfleck
        # Arme: Aermel hochgekrempelt (Stulpe am Oberarm), Unterarm Haut
        self.sh, self.el, self.hand, self.finger = {}, {}, {}, {}
        self.mehl = {}
        m_flour = L.mat("lea_mehl", "#FFFFFF", 0.9)
        rr = random.Random(41)
        for side, sx in (("R", -1), ("L", 1)):
            sh = L.empty(f"l_shoulder_{side}", self.torso, (sx * 0.29, 0, 0.62), c)
            L.sphere(f"l_sleeve_{side}", 0.095, 10, 6, (1, 1, 1), m_shirt, sh, (0, 0, 0), c)
            L.cyl(f"l_upper_{side}", 0.08, 0.22, 8, m_shirt, sh, (0, 0, -0.1), c, r2=0.078)
            L.torus(f"l_rollcuff_{side}", 0.08, 0.026, 10, 5, m_shirt, sh, (0, 0, -0.22), c)
            L.cyl(f"l_upperskin_{side}", 0.065, 0.16, 8, m_skin, sh, (0, 0, -0.29), c, r2=0.06)
            el = L.empty(f"l_elbow_{side}", sh, (0, 0, -0.36), c)
            L.cyl(f"l_fore_{side}", 0.06, 0.32, 8, m_skin, el, (0, 0, -0.17), c, r2=0.052)
            hd = L.empty(f"l_hand_{side}", el, (0, 0, -0.35), c)
            L.sphere(f"l_palm_{side}", 0.08, 10, 7, (0.85, 0.7, 1.0), m_skin, hd, (0, 0, 0), c)
            L.sphere(f"l_thumb_{side}", 0.032, 6, 4, (1, 1, 1.4), m_skin, hd, (-sx * 0.055, -0.04, 0.02), c)
            fg = L.empty(f"l_finger_{side}", hd, (0, -0.016, -0.055), c)
            L.cyl(f"l_index_{side}", 0.02, 0.1, 6, m_skin, fg, (0, 0, -0.04), c)
            fg.scale = (1, 1, 0.35)
            # Mehl an den Fingern (Staerke ueber lea_mehl)
            mp = L.empty(f"l_mehlpiv_{side}", hd, (0, 0, 0), c)
            for j in range(6):
                L.sphere(f"l_mehl_{side}{j}", rr.uniform(0.013, 0.02), 6, 4, (1.3, 0.4, 1.0), m_flour, mp,
                         (rr.uniform(-0.04, 0.04), -0.07, rr.uniform(-0.07, 0.01)), c)
            mp.scale = (0, 0, 0)
            self.mehl[side] = mp
            self.sh[side], self.el[side], self.hand[side], self.finger[side] = sh, el, hd, fg
        # Kopf
        self.neck = L.empty("l_neck", self.torso, (0, 0, 0.74), c)
        L.cyl("l_neckmesh", 0.085, 0.14, 8, m_skin, self.neck, (0, 0, 0.02), c)
        self.head = L.empty("l_head", self.neck, (0, 0, 0.08), c)
        L.sphere("l_headmesh", 0.27, 14, 10, (0.94, 0.92, 1.02), m_skin, self.head, (0, 0, 0.27), c)
        for side, sx in (("R", -1), ("L", 1)):
            L.sphere(f"l_ear_{side}", 0.05, 8, 5, (0.55, 1, 1), m_skin2, self.head, (sx * 0.255, 0.0, 0.26), c)
            L.sphere(f"l_cheek_{side}", 0.05, 8, 5, (1, 0.5, 0.7), m_cheek, self.head, (sx * 0.15, -0.215, 0.16), c)
        L.sphere("l_nose", 0.04, 8, 5, (0.9, 0.9, 1.0), m_skin2, self.head, (0, -0.265, 0.22), c)
        # Haare: Kappe hinten, Pony vorn unter dem Kaeppi
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.285)
        kill = [v for v in bm.verts if v.co.z < -0.02 or (v.co.y < -0.16 and v.co.z < 0.15)]
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        L.from_bm("l_hair", bm, m_hair, self.head, (0, 0.012, 0.3), c)
        for j, x in enumerate((-0.14, -0.05, 0.06, 0.15)):
            o = L.sphere(f"l_pony{j}", 0.07, 8, 5, (1.1, 0.5, 0.55), m_hair, self.head, (x, -0.235, 0.47 - 0.01 * abs(x) * 3), c)
            o.rotation_euler = (0.3, 0, x)
        for side, sx in (("R", -1), ("L", 1)):                       # Straehnen seitlich (rahmen das Gesicht)
            o = L.sphere(f"l_straehne_{side}", 0.055, 8, 5, (0.55, 0.75, 1.9), m_hair, self.head, (sx * 0.235, -0.12, 0.25), c)
            o.rotation_euler = (0.15, 0, -sx * 0.12)
        # Augen: gross und ausdrucksstark
        self.eye, self.pupil = {}, {}
        for side, sx in (("R", -1), ("L", 1)):
            e = L.empty(f"l_eye_{side}", self.head, (sx * 0.1, -0.215, 0.32), c)
            L.sphere(f"l_eyeball_{side}", 0.085, 12, 8, (1, 0.78, 1.15), m_eye, e, (0, 0, 0), c)
            pp = L.empty(f"l_pupilpiv_{side}", e, (0, 0, 0), c)
            L.sphere(f"l_iris_{side}", 0.05, 10, 6, (1, 0.6, 1.1), L.mat("lea_iris", "#6B4A2E", 0.5), pp, (0, -0.06, 0), c)
            L.sphere(f"l_pupil_{side}", 0.03, 10, 6, (1, 0.6, 1.1), m_pupil, pp, (0, -0.07, 0), c)
            L.sphere(f"l_glint_{side}", 0.014, 6, 4, (1, 1, 1), m_glint, pp, (0.018, -0.09, 0.024), c)
            # Wimpern (aussen)
            lsh = L.box(f"l_lash_{side}", (0.03, 0.01, 0.012), m_hair, e, (sx * 0.075, -0.035, 0.05), c)
            lsh.rotation_euler = (0, sx * 0.6, 0)
            self.eye[side], self.pupil[side] = e, pp
        self.reflect = {s: L.empty(f"l_reflect_{s}", self.pupil[s], (0, 0, 0), c) for s in ("R", "L")}
        # Lider (wie Kalle 2.2: Kuppel ueber dem Augapfel)
        self.lid = {}
        for side in ("R", "L"):
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.092)
            kill = [v for v in bm.verts if v.co.z < -0.004]
            bmesh.ops.delete(bm, geom=kill, context="VERTS")
            bmesh.ops.scale(bm, vec=Vector((1.04, 0.86, 1.15)), verts=bm.verts)
            piv = L.empty(f"l_lidpiv_{side}", self.eye[side], (0, 0, 0), c)
            L.from_bm(f"l_lid_{side}", bm, m_skin, piv, (0, 0, 0), c)
            piv.rotation_euler = (-1.3, 0, 0)
            piv.scale = (0, 0, 0)
            self.lid[side] = piv
        # Brauen (schmal, dunkelbraun)
        self.brow = {}
        for side, sx in (("R", -1), ("L", 1)):
            b = L.empty(f"l_brow_{side}", self.head, (sx * 0.105, -0.245, 0.435), c)
            L.box(f"l_browmesh_{side}", (0.11, 0.025, 0.022), m_hair, b, (0, 0, 0), c, bevel=0.009)
            b.rotation_euler = (0, sx * -0.18, 0)
            self.brow[side] = b
        # Mund (Formen ueber Scale), Mundwinkel, Laecheln
        self.mouth = L.empty("l_mouth", self.head, (0, -0.25, 0.1), c)
        L.sphere("l_mouthmesh", 1.0, 12, 7, (0.065, 0.035, 0.05), m_mouth, self.mouth, (0, 0, 0), c)
        L.sphere("l_tongue", 1.0, 8, 5, (0.04, 0.025, 0.02), m_tongue, self.mouth, (0, -0.01, -0.025), c)
        self.mouth.scale = (1, 1, 0.18)
        self.stache = L.empty("l_stache_dummy", self.head, (0, -0.26, 0.14), c)    # kein Bart: leerer Pivot
        self.frown = L.empty("l_frown", self.head, (0, -0.262, 0.075), c)
        bm = bmesh.new()
        pts = [(0.05 * math.cos(math.pi * i / 10), 0.022 * math.sin(math.pi * i / 10)) for i in range(11)]
        w = 0.014
        vo = [bm.verts.new((x, 0, z + w / 2)) for x, z in pts]
        vi = [bm.verts.new((x * 0.93, 0, z - w / 2)) for x, z in pts]
        for i in range(10):
            bm.faces.new((vi[i], vi[i + 1], vo[i + 1], vo[i]))
        L.from_bm("l_frownmesh", bm, m_mouth, self.frown, (0, 0, 0), c)
        self.frown.scale = (0, 0, 0)
        C._geruehrt_teile(self, c, "l", mouth_z=0.092, mouth_w=0.052, smile_y=-0.262)
        # Baeckerkaeppi (weiss, flach)
        self.hat = L.empty("l_cap", self.head, (0, 0.03, 0.47), c)
        L.cyl("l_capband", 0.235, 0.09, 16, m_white, self.hat, (0, 0, 0.03), c, r2=0.24)
        L.sphere("l_captop", 0.24, 14, 7, (1, 1, 0.45), m_white, self.hat, (0, 0, 0.08), c)
        L.box("l_capfold", (0.3, 0.02, 0.05), L.mat("lea_capfold", "#E9E4D8", 0.6), self.hat, (0, -0.225, 0.035), c)
        # Zopf: Kette aus Gliedern hinten rechts, schwingt nach
        self.zopf = []
        parent = L.empty("l_zopfroot", self.head, (-0.1, 0.2, 0.2), c)
        self.zopf_root = parent
        L.sphere("l_zopfansatz", 0.06, 8, 5, (1, 1, 1), m_hair, parent, (0, 0, 0), c)
        for j in range(5):
            seg = L.empty(f"l_zopf{j}", parent, (0, 0, -0.06 if j == 0 else -0.085), c)
            r = 0.05 - 0.006 * j
            L.sphere(f"l_zopfm{j}", r, 8, 5, (1, 0.9, 1.15), m_hair, seg, (0, 0, -0.04), c)
            self.zopf.append(seg)
            parent = seg
        L.cyl("l_zopfband", 0.022, 0.025, 8, L.mat("lea_band", "#2EE6D6", 0.5), parent, (0, 0, -0.085), c)
        L.sphere("l_zopfende", 0.03, 8, 5, (1, 1, 1.4), m_hair, parent, (0, 0, -0.12), c)
        self.zopf_root.rotation_euler = (0.25, 0, 0)
        # AR-Brille (schmal, transparent, tuerkiser Rand), standardmaessig ab
        self.brille = L.empty("l_brille", self.head, (0, -0.29, 0.33), c)
        m_rand = L.mat("lea_brillenrand", "#2EE6D6", 0.4, emit="#2EE6D6", strength=2.0)
        self.m_glas = L.unique_mat(L.mat("lea_brillenglas", "#BFF7F2", 0.2, alpha=0.28), "lea_brillenglas_m")
        for sx in (-1, 1):
            L.box(f"l_br_glas{sx}", (0.15, 0.006, 0.075), self.m_glas, self.brille, (sx * 0.1, 0, 0), c, bevel=0.02)
            L.box(f"l_br_ro{sx}", (0.16, 0.012, 0.012), m_rand, self.brille, (sx * 0.1, -0.004, 0.04), c)
            L.box(f"l_br_ru{sx}", (0.16, 0.012, 0.008), m_rand, self.brille, (sx * 0.1, -0.004, -0.04), c)
            L.box(f"l_br_buegel{sx}", (0.012, 0.25, 0.012), m_rand, self.brille, (sx * 0.19, 0.12, 0.03), c)
        L.box("l_br_steg", (0.05, 0.012, 0.012), m_rand, self.brille, (0, -0.004, 0.02), c)
        self.brille.scale = (0, 0, 0)

    def scale_all(self, s):
        self.root.scale = (s, s, s)


# ------------------------------------------------------------------ Animation
def lea_idle(T, l, f0, f1, seed=17):
    """Atmen und Gewicht wie Kalle, Zopf und Schuerzenbaender schwingen nach, unregelmaessiges Blinzeln."""
    C.kalle_idle(T, l, f0, f1, seed=seed, blink=False)
    for j, seg in enumerate(l.zopf):
        C.follow_through(T, seg, l.head, "rotation_euler", 2, 1.4 + 0.4 * j, 3 + j, f0, f1, out_idx=1)
        C.follow_through(T, seg, l.head, "rotation_euler", 0, 1.2 + 0.3 * j, 3 + j, f0, f1, out_idx=0)
        C.follow_through(T, seg, l.hips, "rotation_euler", 1, 1.5, 4 + j, f0, f1, out_idx=1)
        T.add(seg, "rotation_euler", lambda f, j=j: (0.03 * math.sin(f * 0.11 + j * 0.7), 0.04 * math.sin(f * 0.07 + j), 0),
              f0, f1)
    lea_blinks(T, l, f0, f1, seed=seed)


def lea_blinks(T, l, f0, f1, seed=17, ruhig=None):
    """Natuerliches, unregelmaessiges Blinzeln: Abstaende 1,5-5 s, gelegentlich doppelt, Dauer 4-7 Frames.
    ruhig(f) -> True: in langsamen Szenen etwas haeufiger (wirkt lebendig, nicht starr)."""
    r = random.Random(seed)
    t = f0 + r.randint(8, 40)
    while t < f1:
        dur = r.randint(4, 7)
        for b in ([t, t + dur + r.randint(3, 5)] if r.random() < 0.18 else [t]):
            for side in ("R", "L"):
                T.mul(l.eye[side], "scale", lambda f, b=b, d=dur: (1, 1, 1 - 0.93 * window(f, b, b + d, 2, d - 2)), b, b + dur)
        gap = r.uniform(1.5, 5.0)
        if ruhig and ruhig(t):
            gap *= 0.75
        t += int(gap * FPS)


def lea_lipsync(T, l, scene, f0, f1):
    """Mund nach Lautstaerke (wie Kalle), dazu leichtes Kopfnicken bei betonten Woertern."""
    C.kalle_lipsync(T, l, scene, f0, f1)
    for w in scene["words"]:
        if w["hl"]:
            a0, a1 = w["f0"] - 2, w["f1"] + 6
            T.add(l.head, "rotation_euler", lambda f, a0=a0, a1=a1: (0.06 * window(f, a0, a1, 3, 6), 0, 0), a0, a1)


def lea_traurig(T, l, f0, f1, speaking=False, ramp=14, weg=1.0):
    """Traurig (Lea): Kopf gesenkt, Zopf faellt nach vorn ueber die Schulter, Schultern ziehen hoch, Blick weicht aus
    (Kopf und Pupillen zur Seite, weg = Richtung +1 / -1), Lider halb gesenkt, Brauen innen hoch, Mundwinkel unten."""
    env = lambda x: window(x, f0, f1, ramp, ramp)  # noqa: E731
    for side, sx in (("R", -1), ("L", 1)):
        T.set(l.lid[side], "scale", lambda x: (1, 1, 1) if env(x) > 0.01 else (0, 0, 0), f0 - 1, f1 + 1)
        T.set(l.lid[side], "scale", lambda x: (0, 0, 0), f1 + 1, f1 + 2)
        T.add(l.lid[side], "rotation_euler", lambda x: (1.15 * env(x), 0, 0), f0, f1)
        T.add(l.brow[side], "rotation_euler", lambda x, sx=sx: (0, sx * 0.45 * env(x), 0), f0, f1)
        T.add(l.brow[side], "location", lambda x, sx=sx: (-sx * 0.01 * env(x), 0, 0.012 * env(x)), f0, f1)
        T.add(l.sh[side], "location", lambda x: (0, 0.0, 0.05 * env(x)), f0, f1)          # Schultern ziehen hoch
        T.add(l.sh[side], "rotation_euler", lambda x, sx=sx: (-0.1 * env(x), 0, -sx * 0.1 * env(x)), f0, f1)
        T.add(l.pupil[side], "rotation_euler", lambda x: (0.3 * env(x), 0, weg * 0.45 * env(x)), f0, f1)
    T.add(l.head, "rotation_euler", lambda x: (0.32 * env(x), 0, weg * 0.3 * env(x)), f0, f1)
    T.add(l.hips, "rotation_euler", lambda x: (0.06 * env(x), 0, 0), f0, f1)
    T.add(l.zopf_root, "rotation_euler", lambda x: (-1.9 * env(x), 0, -0.9 * env(x)), f0, f1)   # nach vorn
    T.set(l.frown, "scale", lambda x: (1, 1, 1) if env(x) > 0.25 else (0, 0, 0), f0 - 1, f1 + 1)
    T.set(l.frown, "scale", lambda x: (0, 0, 0), f1 + 1, f1 + 2)
    if not speaking:
        T.mul(l.mouth, "scale", lambda x: (1 - 0.35 * env(x), 1, 1 - 0.4 * env(x)), f0, f1)


def lea_react(T, l, kind, f, hold=40, speaking=False, weg=1.0):
    """Alle Reaktionen: neutral, zweifel, staunen, schock, jubel, traurig, geruehrt."""
    if kind == "traurig":
        lea_traurig(T, l, f - 6, f + hold, speaking=speaking, weg=weg)
        return
    if kind == "geruehrt":
        C.kalle_geruehrt(T, l, f - 6, f + hold, speaking=speaking)
        T.add(l.zopf_root, "rotation_euler", lambda x: (0, 0, 0.2 * window(x, f - 6, f + hold, 12, 12)), f - 6, f + hold)
        return
    C.kalle_react(T, l, kind, f, hold, speaking=speaking, hat=(kind != "schock"))
    if kind == "jubel":                                   # Zopf wippt
        T.add(l.zopf_root, "rotation_euler", lambda x: (0.5 * spring((x - f) / FPS, 3.0, 0.25) * (x >= f), 0, 0), f, f + 40)


def lea_mehl(T, l, fn, f0, f1):
    """Mehl an den Fingern: fn(f) 0..1 (waechst, je mehr sie arbeitet)."""
    for side in ("R", "L"):
        T.set(l.mehl[side], "scale", lambda f: (max(0.0, min(1.0, fn(f))),) * 3, f0, f1)


def lea_brille(T, l, plan, f0, f1, aufleuchten=()):
    """Brille: plan = [(frame, 'ab' | 'auf' | 'stirn'), ...], weicher Wechsel (8 Frames).
    aufleuchten: Frames, an denen die Glaeser kurz tuerkis aufleuchten."""
    plan = sorted(plan)
    pos = {"auf": (0, -0.29, 0.33), "stirn": (0, -0.2, 0.52), "ab": (0, -0.29, 0.33)}
    rot = {"auf": (0, 0, 0), "stirn": (-0.55, 0, 0), "ab": (0, 0, 0)}

    def state(f):
        cur, prev, t0 = plan[0][1], plan[0][1], plan[0][0]
        for fr, st in plan:
            if fr <= f:
                prev, cur, t0 = cur, st, fr
        return prev, cur, min(1.0, max(0.0, (f - t0) / 8))

    def lerp3(a, b, t):
        return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
    T.set(l.brille, "location", lambda f: lerp3(pos[state(f)[0]], pos[state(f)[1]], ease_in_out(state(f)[2])), f0, f1)
    T.set(l.brille, "rotation_euler", lambda f: lerp3(rot[state(f)[0]], rot[state(f)[1]], ease_in_out(state(f)[2])), f0, f1)

    def sc(f):
        a, b_, t = state(f)
        va = 0.0 if a == "ab" else 1.0
        vb = 0.0 if b_ == "ab" else 1.0
        v = va + (vb - va) * ease_out(t)
        return (v, v, v)
    T.set(l.brille, "scale", sc, f0, f1)
    if aufleuchten:
        base = tuple(l.m_glas.diffuse_color)
        hell = L.srgb("#2EE6D6", 0.75)
        T.set(l.m_glas, "diffuse_color", lambda f: tuple(
            base[i] + (hell[i] - base[i]) * max([window(f, a, a + 14, 2, 10) for a in aufleuchten] + [0.0]) for i in range(4)),
            f0, f1)


# ------------------------------------------------------------------ Haende (Kalle und Lea)
def haende_rollen(T, k, f0, f1, ramp=6, amp=0.16, speed=0.35):
    """Teigstrang rollen: beide Haende flach auf dem Tisch, gleiten im Takt vor und zurueck und auseinander."""
    C.pose(T, k, {"sh_R": (-0.75, 0, 0.35), "sh_L": (-0.75, 0, -0.35), "el_R": (-0.55, 0, 0), "el_L": (-0.55, 0, 0),
                  "hips": (0.1, 0, 0)}, f0, f1, ramp, ramp)
    for side, sx in (("R", -1), ("L", 1)):
        T.add(k.sh[side], "rotation_euler",
              lambda x, sx=sx: (amp * math.sin(x * speed) * window(x, f0, f1, ramp, ramp),
                                0, sx * 0.08 * (x - f0) / max(1, f1 - f0) * window(x, f0, f1, ramp, ramp)), f0, f1)
        T.add(k.hand[side], "rotation_euler", lambda x: (-0.8 * window(x, f0, f1, ramp, ramp), 0, 0), f0, f1)


def haende_schlingen(T, k, f0, f1, ramp=6, schwung=True, zeit=None):
    """Brezel schlingen: Strangenden anheben (1), kreuzen (2), mit kleinem Schwung aus dem Handgelenk drehen (3),
    andruecken (4). zeit(f) -> 0..1 erlaubt Zeitlupe (Regie). schwung=False: flache Bewegung ohne Bogen (wie Lea vorher)."""
    zt = zeit or (lambda x: (x - f0) / max(1, f1 - f0))
    env = lambda x: window(x, f0, f1, ramp, ramp)  # noqa: E731

    def phase(x):
        return max(0.0, min(1.0, zt(x)))
    for side, sx in (("R", -1), ("L", 1)):
        def sh(x, sx=sx):
            p = phase(x)
            lift = math.sin(math.pi * min(1.0, p / 0.6))                       # heben und kreuzen
            cross = ease_in_out(min(1.0, max(0.0, (p - 0.2) / 0.4)))
            press = ease_in_out(max(0.0, (p - 0.8) / 0.2))
            return (env(x) * (-0.9 - 0.5 * lift + 0.3 * press), 0, env(x) * sx * (0.35 - 0.7 * cross))
        T.add(k.sh[side], "rotation_euler", sh, f0, f1)
        T.add(k.el[side], "rotation_euler", lambda x: (-0.6 * env(x), 0, 0), f0, f1)

        def wrist(x, sx=sx):
            p = phase(x)
            bogen = math.sin(math.pi * max(0.0, min(1.0, (p - 0.45) / 0.3))) if schwung else 0.0
            return (-0.3 * env(x), sx * 0.9 * bogen * env(x), 1.1 * bogen * env(x) * sx)
        T.add(k.hand[side], "rotation_euler", wrist, f0, f1)
