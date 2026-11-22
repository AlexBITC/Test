"""Figuren: Kalle (Baeckermeister), Byte (KI-Kugel) und Helfer-Bytes.

Aufbau mit Pivot-Empties (kein Armature noetig). Alle Animationen laufen ueber anim.Tracks.
Konventionen: Figuren schauen nach -Y (zur Kamera). Kalles rechte Seite liegt bei -X.
"""
import math
import random

import bmesh
from mathutils import Vector

import anim
import look as L
from anim import (ease_in_out, ease_out, ease_out_back, spring, tween, window, pop, Noise)

FPS = 30


# =================================================================== Kalle
class Kalle:
    def __init__(self, coll, extras=False):
        self.coll = coll
        self.extras = extras
        m_skin = L.mat("skin", L.SKIN, 0.62)
        m_skin2 = L.mat("skin_dark", L.SKIN_DARK, 0.62)
        m_cheek = L.mat("cheek", L.CHEEK, 0.7)
        m_hair = L.mat("hair", L.HAIR, 0.65)
        m_pants = L.mat("pants", L.PANTS, 0.68)
        m_shirt = L.mat("shirt", L.SHIRT, 0.66)
        m_apron = L.mat("apron", L.APRON, 0.66)
        m_stain = L.mat("flourstain", "#FFFFFF", 0.9)
        m_stain2 = L.mat("flourstain2", "#E4DACA", 0.8)
        m_white = L.mat("hatwhite", L.FLOUR, 0.6)
        m_eye = L.mat("eyewhite", "#FBF8F2", 0.5)
        m_pupil = L.mat("pupil", "#17142a", 0.5)
        m_glint = L.mat("glint", "#FFFFFF", 0.4, emit="#FFFFFF", strength=2.0)
        m_mouth = L.mat("mouth", "#4A1E26", 0.7)
        m_tongue = L.mat("tongue", "#C9656B", 0.6)
        m_shoe = L.mat("shoe", "#2A2238", 0.6)
        c = coll

        self.root = L.empty("kalle_root", coll=c)
        self.body = L.empty("kalle_body", self.root, (0, 0, 0), c)          # Sprung / Gewicht
        # Beine
        self.hip = {}
        self.knee = {}
        for side, sx in (("R", -1), ("L", 1)):
            hp = L.empty(f"k_hip_{side}", self.body, (sx * 0.17, 0, 0.80), c)
            L.cyl(f"k_thigh_{side}", 0.125, 0.42, 8, m_pants, hp, (0, 0, -0.19), c)
            kn = L.empty(f"k_knee_{side}", hp, (0, 0, -0.38), c)
            L.cyl(f"k_shin_{side}", 0.11, 0.36, 8, m_pants, kn, (0, 0, -0.17), c)
            L.box(f"k_shoe_{side}", (0.2, 0.3, 0.1), m_shoe, kn, (0, -0.06, -0.38), c, bevel=0.03)
            self.hip[side], self.knee[side] = hp, kn
        # Rumpf
        self.hips = L.empty("k_hips", self.body, (0, 0, 0.80), c)
        self.torso = L.empty("k_torso", self.hips, (0, 0, 0.0), c)             # Atmen (Scale)
        L.sphere("k_belly", 1.0, 14, 9, (0.43, 0.35, 0.47), m_shirt, self.torso, (0, 0, 0.34), c)
        # Schuerze: Schale vor dem Bauch + Rock mit Nachschwing-Pivot
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=9, radius=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.445, 0.365, 0.485)), verts=bm.verts)
        kill = [v for v in bm.verts if v.co.y > -0.12 or abs(v.co.x) > 0.36 or
                (v.co.z > 0.12 and abs(v.co.x) > 0.21) or v.co.z > 0.36]
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        L.from_bm("k_apron", bm, m_apron, self.torso, (0, 0, 0.34), c)
        st1 = L.sphere("k_stain1", 0.075, 8, 5, (1.25, 0.12, 0.8), m_stain2, self.torso, (0.14, -0.352, 0.24), c)
        st1.rotation_euler = (0.25, 0, 0.3)
        L.sphere("k_stain2", 0.04, 8, 5, (1.0, 0.12, 0.8), m_stain2, self.torso, (0.24, -0.325, 0.16), c)
        # Schuerzenband am Hals
        L.torus("k_apronstrap", 0.15, 0.018, 12, 4, m_apron, self.torso, (0, -0.07, 0.72), c, axis="Z")
        self.skirt = L.empty("k_skirt", self.hips, (0, -0.22, -0.02), c)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=False, segments=14, radius1=0.47, radius2=0.40, depth=0.5)
        kill = [v for v in bm.verts if v.co.y > -0.05]
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bmesh.ops.translate(bm, vec=Vector((0, 0.22, -0.25)), verts=bm.verts)
        L.from_bm("k_apron_skirt", bm, m_apron, self.skirt, (0, 0, 0), c)
        # Arme
        self.sh, self.el, self.hand, self.finger = {}, {}, {}, {}
        for side, sx in (("R", -1), ("L", 1)):
            sh = L.empty(f"k_shoulder_{side}", self.torso, (sx * 0.40, 0, 0.62), c)
            L.sphere(f"k_sleeve_{side}", 0.12, 10, 6, (1, 1, 1), m_shirt, sh, (0, 0, 0), c)
            L.cyl(f"k_upper_{side}", 0.105, 0.38, 8, m_shirt, sh, (0, 0, -0.18), c, r2=0.095)
            el = L.empty(f"k_elbow_{side}", sh, (0, 0, -0.36), c)
            L.cyl(f"k_cuff_{side}", 0.1, 0.08, 8, m_shirt, el, (0, 0, -0.02), c)
            L.cyl(f"k_fore_{side}", 0.08, 0.32, 8, m_skin, el, (0, 0, -0.18), c, r2=0.07)
            hd = L.empty(f"k_hand_{side}", el, (0, 0, -0.36), c)
            L.sphere(f"k_palm_{side}", 0.1, 10, 7, (0.9, 0.75, 1.0), m_skin, hd, (0, 0, 0), c)
            L.sphere(f"k_thumb_{side}", 0.04, 6, 4, (1, 1, 1.4), m_skin, hd, (-sx * 0.07, -0.05, 0.02), c)
            fg = L.empty(f"k_finger_{side}", hd, (0, -0.02, -0.07), c)
            L.cyl(f"k_index_{side}", 0.026, 0.12, 6, m_skin, fg, (0, 0, -0.05), c)
            fg.scale = (1, 1, 0.35)
            self.sh[side], self.el[side], self.hand[side], self.finger[side] = sh, el, hd, fg
        # Kopf
        self.neck = L.empty("k_neck", self.torso, (0, 0, 0.76), c)
        L.cyl("k_neckmesh", 0.13, 0.14, 8, m_skin, self.neck, (0, 0, 0.02), c)
        self.head = L.empty("k_head", self.neck, (0, 0, 0.08), c)
        hc = (0, 0, 0.28)
        L.sphere("k_headmesh", 0.31, 14, 10, (1.0, 0.93, 0.98), m_skin, self.head, hc, c)
        for side, sx in (("R", -1), ("L", 1)):
            L.sphere(f"k_ear_{side}", 0.065, 8, 5, (0.6, 1, 1), m_skin2, self.head, (sx * 0.305, 0.0, 0.27), c)
            L.sphere(f"k_cheek_{side}", 0.06, 8, 5, (1, 0.5, 0.75), m_cheek, self.head,
                     (sx * 0.17, -0.245, 0.18), c)
        L.sphere("k_nose", 0.072, 10, 6, (1.0, 0.95, 0.9), m_skin2, self.head, (0, -0.31, 0.24), c)
        # Augen (gross, Kugelaugen)
        self.eye, self.pupil = {}, {}
        for side, sx in (("R", -1), ("L", 1)):
            e = L.empty(f"k_eye_{side}", self.head, (sx * 0.115, -0.245, 0.35), c)
            L.sphere(f"k_eyeball_{side}", 0.088, 12, 8, (1, 0.8, 1.08), m_eye, e, (0, 0, 0), c)
            pp = L.empty(f"k_pupilpiv_{side}", e, (0, 0, 0), c)
            L.sphere(f"k_pupil_{side}", 0.045, 10, 6, (1, 0.6, 1.1), m_pupil, pp, (0, -0.066, 0), c)
            L.sphere(f"k_glint_{side}", 0.013, 6, 4, (1, 1, 1), m_glint, pp, (0.018, -0.094, 0.022), c)
            self.eye[side], self.pupil[side] = e, pp
        # Spiegelungen in den Kugelaugen (drei leuchtende Geraete, Szene 'Des gibt's doch net!')
        self.reflect = {}
        m_ref = L.mat("eye_reflect", "#BFFFF8", 0.4, emit="#BFFFF8", strength=4.0)
        for side, sx in (("R", -1), ("L", 1)):
            rf = L.empty(f"k_reflect_{side}", self.pupil[side], (0, -0.093, 0.006), c)
            for j, (w, h) in enumerate([(0.008, 0.015), (0.016, 0.013), (0.022, 0.012)]):
                L.box(f"k_refl_{side}{j}", (w, 0.002, h), m_ref, rf, (-0.022 + j * 0.019, 0, 0), c)
            rf.scale = (0, 0, 0)
            self.reflect[side] = rf
        # Brauen
        self.brow = {}
        for side, sx in (("R", -1), ("L", 1)):
            b = L.empty(f"k_brow_{side}", self.head, (sx * 0.12, -0.265, 0.47), c)
            L.box(f"k_browmesh_{side}", (0.13, 0.04, 0.035), m_hair, b, (0, 0, 0), c, bevel=0.012)
            b.rotation_euler = (0, sx * -0.12, 0)
            self.brow[side] = b
        # Mund (3 Formen ueber Scale) + Schnurrbart
        self.mouth = L.empty("k_mouth", self.head, (0, -0.268, 0.105), c)
        L.sphere("k_mouthmesh", 1.0, 12, 7, (0.085, 0.04, 0.06), m_mouth, self.mouth, (0, 0, 0), c)
        L.sphere("k_tongue", 1.0, 8, 5, (0.05, 0.03, 0.025), m_tongue, self.mouth, (0, -0.012, -0.03), c)
        self.mouth.scale = (1, 1, 0.18)
        self.stache = L.empty("k_stache", self.head, (0, -0.30, 0.165), c)
        for side, sx in (("R", -1), ("L", 1)):
            s1 = L.sphere(f"k_stache_{side}", 1.0, 10, 6, (0.12, 0.05, 0.048), m_hair, self.stache,
                          (sx * 0.085, 0, 0), c)
            s1.rotation_euler = (0, sx * 0.32, sx * 0.08)
            s2 = L.sphere(f"k_stachetip_{side}", 1.0, 8, 5, (0.05, 0.035, 0.035), m_hair, self.stache,
                          (sx * 0.185, 0.01, 0.035), c)
            s2.rotation_euler = (0, sx * -0.6, 0)
        # Baeckermuetze
        self.hat = L.empty("k_hat", self.head, (0, 0.01, 0.53), c)
        L.cyl("k_hatband", 0.255, 0.16, 14, m_white, self.hat, (0, 0, 0.06), c, r2=0.27)
        for i, (x, y, z, r) in enumerate([(0, 0, 0.26, 0.24), (-0.14, 0.02, 0.22, 0.16), (0.14, 0.02, 0.22, 0.16),
                                          (0, -0.12, 0.23, 0.15), (0, 0.13, 0.23, 0.15)]):
            L.sphere(f"k_hatpuff{i}", r, 10, 7, (1, 1, 0.75), m_white, self.hat, (x, y, z), c)
        # Tuch (Szene 1) und Lesebrille (Szene 6)
        self.cloth = L.box("k_cloth", (0.2, 0.16, 0.035), L.mat("cloth", "#8FA6C7", 0.8), self.hand["R"],
                           (0, -0.02, -0.08), c, bevel=0.012)
        self.glasses = None
        if extras:
            self._extras(c, m_white)
        self._details_v22(c)

    def _details_v22(self, c):
        """Engine 2.2: Augenlider (standardmaessig unsichtbar), Lachfalten, Mehlspuren an Haenden und Unterarmen,
        Mehlstaub auf der Muetze, Schuerzenbaender am Ruecken, Mundwinkel fuer 'traurig' (standardmaessig unsichtbar)."""
        m_skin = L.mat("skin", L.SKIN, 0.62)
        m_line = L.mat("lachfalte", "#B9744F", 0.7)
        m_flour = L.mat("flourstain", "#FFFFFF", 0.9)
        m_dust = L.mat("mehlstaub_muetze", "#ECE4D4", 0.8)
        m_apron = L.mat("apron", L.APRON, 0.66)
        # Augenlider: Kuppel ueber dem Augapfel, gesenkt ueber Rotation um X (0 = halb zu)
        self.lid = {}
        for side in ("R", "L"):
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.095)
            kill = [v for v in bm.verts if v.co.z < -0.004]
            bmesh.ops.delete(bm, geom=kill, context="VERTS")
            bmesh.ops.scale(bm, vec=Vector((1.04, 0.86, 1.12)), verts=bm.verts)
            piv = L.empty(f"k_lidpiv_{side}", self.eye[side], (0, 0, 0), c)
            L.from_bm(f"k_lid_{side}", bm, m_skin, piv, (0, 0, 0), c)
            piv.rotation_euler = (-1.3, 0, 0)
            piv.scale = (0, 0, 0)
            self.lid[side] = piv
        # Lachfalten an den aeusseren Augenwinkeln
        for side, sx in (("R", -1), ("L", 1)):
            for j, (dz, rot) in enumerate([(0.03, 0.35), (-0.005, 0.0), (-0.04, -0.35)]):
                o = L.box(f"k_lachfalte_{side}{j}", (0.045, 0.012, 0.009), m_line, self.head,
                          (sx * 0.232, -0.2, 0.35 + dz), c)
                o.rotation_euler = (0, sx * rot, sx * 0.55)
        # Mehlspuren auf Haenden und Unterarmen
        rr = random.Random(22)
        for side in ("R", "L"):
            for j in range(3):
                L.sphere(f"k_mehl_arm_{side}{j}", rr.uniform(0.012, 0.018), 6, 4, (1.4, 0.3, 1.0), m_flour, self.el[side],
                         (rr.uniform(-0.03, 0.03), -0.072, -0.12 - 0.07 * j), c)
            for j in range(2):
                L.sphere(f"k_mehl_hand_{side}{j}", rr.uniform(0.012, 0.016), 6, 4, (1.3, 0.35, 1), m_flour, self.hand[side],
                         (rr.uniform(-0.04, 0.04), -0.088, rr.uniform(-0.03, 0.03)), c)
        # Mehlstaub auf der Muetze
        for j in range(8):
            a = math.radians(-90 + rr.uniform(-60, 60))
            o = L.sphere(f"k_mehl_muetze{j}", rr.uniform(0.02, 0.032), 6, 4, (1.8, 0.2, 0.8), m_dust, self.hat,
                         (0.262 * math.cos(a), 0.262 * math.sin(a), rr.uniform(0.02, 0.13)), c)
            o.rotation_euler = (0, rr.uniform(-0.5, 0.5), a + math.pi / 2)
        # Schuerzenbaender am Ruecken mit Schleife und haengenden Enden
        for sx in (-1, 1):
            o = L.box(f"k_apronband{sx}", (0.33, 0.02, 0.035), m_apron, self.torso, (sx * 0.26, 0.2, 0.36), c)
            o.rotation_euler = (0, 0, sx * -0.95)
        self.apron_bow = L.empty("k_apronbow", self.torso, (0, 0.37, 0.36), c)
        for sx in (-1, 1):
            lp = L.sphere(f"k_apronloop{sx}", 0.05, 8, 5, (1.2, 0.35, 0.7), m_apron, self.apron_bow, (sx * 0.05, 0, 0), c)
        L.sphere("k_apronknot", 0.025, 8, 5, (1, 0.6, 1), m_apron, self.apron_bow, (0, 0.005, 0), c)
        self.apron_ends = []
        for sx in (-1, 1):
            e = L.empty(f"k_aproned{sx}", self.apron_bow, (sx * 0.02, 0.01, -0.01), c)
            L.box(f"k_apronendm{sx}", (0.03, 0.012, 0.22), m_apron, e, (0, 0, -0.11), c)
            e.rotation_euler = (0, sx * 0.25, 0)
            self.apron_ends.append(e)
        # Mundwinkel nach unten (Bogen), nur bei 'traurig' sichtbar
        self.frown = L.empty("k_frown", self.head, (0, -0.29, 0.072), c)
        bm = bmesh.new()
        n = 10
        pts = []
        for i in range(n + 1):
            t = math.pi * i / n
            pts.append((0.068 * math.cos(t), 0.03 * math.sin(t)))
        w = 0.018
        vs_o = [bm.verts.new((x, 0, z + w / 2)) for x, z in pts]
        vs_i = [bm.verts.new((x * 0.93, 0, z - w / 2)) for x, z in pts]
        for i in range(n):
            f = bm.faces.new((vs_i[i], vs_i[i + 1], vs_o[i + 1], vs_o[i]))
        L.from_bm("k_frownmesh", bm, L.mat("mouth", "#4A1E26", 0.7), self.frown, (0, 0, 0), c)
        self.frown.scale = (0, 0, 0)

    def _extras(self, c, m_white):
        """Merkmale fuer neuere Folgen (zuschaltbar, aeltere Folgen bleiben unveraendert):
        6. Mueztzen-Puff + Neigung 5 Grad nach rechts (Bildsicht), graue Schlaefen, 2 Knoepfe,
        kariertes Geschirrtuch an der Schuerze."""
        L.sphere("k_hatpuff5", 0.13, 10, 7, (1, 1, 0.75), m_white, self.hat, (0.09, -0.1, 0.3), c)
        self.hat.rotation_euler = (0, math.radians(5), 0)
        m_grey = L.mat("temple_grey", "#A9A5A0", 0.7)
        for side, sx in (("R", -1), ("L", 1)):
            o = L.sphere(f"k_temple_{side}", 0.058, 8, 6, (0.5, 0.85, 1.15), m_grey, self.head,
                         (sx * 0.288, -0.04, 0.38), c)
            o.rotation_euler = (0, sx * 0.25, 0)
        m_btn = L.mat("button", "#5E3E2B", 0.5)
        for k, z in enumerate((0.58, 0.47)):
            L.cyl(f"k_button{k}", 0.024, 0.02, 10, m_btn, self.torso, (0, -0.372 - 0.012 * k, z), c, axis="Y")
        self.towel = L.empty("k_towelpiv", self.hips, (0.3, -0.25, 0.06), c)
        import os
        tex = os.path.join(os.path.dirname(__file__), "fonts", "..", "textures", "geschirrtuch.png")
        L.tplane("k_towel", tex, height=0.3, parent=self.towel, loc=(0, -0.004, -0.15), coll=c, emit=0.0,
                 alpha=False)
        L.box("k_towel_back", (0.14, 0.006, 0.3), L.mat("towel_back", "#E8E2D6", 0.8), self.towel,
              (0, 0.002, -0.15), c)
        self.towel.rotation_euler = (0, 0, -0.25)

    # ---------------------------------------------------------- Hilfen
    def scale_all(self, s):
        self.root.scale = (s, s, s)


def kalle_idle(T, k, f0, f1, seed=7, blink=True):
    """Atmen (Brust +-2 %, 0,25 Hz), Blinzeln alle 3-5 s, Gewichtsverlagerung, Nachschwingen."""
    nz = Noise(seed, 3, 0.12)
    nz2 = Noise(seed + 1, 2, 0.2)
    T.add(k.torso, "scale", lambda f: (0.012 * math.sin(2 * math.pi * 0.25 * f / FPS),
                                       0.015 * math.sin(2 * math.pi * 0.25 * f / FPS),
                                       0.02 * math.sin(2 * math.pi * 0.25 * f / FPS)), f0, f1)
    T.add(k.hips, "location", lambda f: (0.025 * nz(f / FPS), 0, 0.006 * math.sin(2 * math.pi * 0.25 * f / FPS)),
          f0, f1)
    T.add(k.hips, "rotation_euler", lambda f: (0.01 * nz2(f / FPS), 0.035 * nz(f / FPS + 3), 0.02 * nz2(f / FPS + 7)),
          f0, f1)
    T.add(k.head, "rotation_euler", lambda f: (0.03 * nz2(f / FPS + 1), -0.02 * nz(f / FPS + 5), 0.04 * nz(f / FPS + 9)),
          f0, f1)
    # Arme pendeln leicht
    for side, sx in (("R", -1), ("L", 1)):
        T.add(k.sh[side], "rotation_euler", lambda f, s=sx: (0.03 * nz2(f / FPS + s), 0.02 * s * nz(f / FPS + 2), 0),
              f0, f1)
    if getattr(k, "apron_ends", None):                # 2.2: Schuerzenbaender schwingen mit
        for j, e in enumerate(k.apron_ends):
            follow_through(T, e, k.hips, "rotation_euler", 1, 2.2, 4, f0, f1, out_idx=1)
            follow_through(T, e, k.hips, "rotation_euler", 0, 1.8, 4, f0, f1, out_idx=0)
            T.add(e, "rotation_euler", lambda f, j=j: (0.05 * math.sin(f * 0.13 + j), 0, 0), f0, f1)
    if blink:
        r = random.Random(seed)
        blinks, t = [], f0 + r.randint(20, 60)
        while t < f1:
            blinks.append(t)
            t += int(r.uniform(3.0, 5.0) * FPS)
        for b in blinks:
            for side in ("R", "L"):
                T.mul(k.eye[side], "scale", lambda f, b=b: (1, 1, 1 - 0.92 * window(f, b, b + 6, 2, 4)), b, b + 6)


def follow_through(T, child, src, path, idx, gain, delay=3, f0=0, f1=0, out_idx=None):
    """Sekundaerbewegung: child dreht sich gegen die Bewegung von src (verzoegert)."""
    def fn(f):
        a = T.val(src, path, idx, f - delay)
        b = T.val(src, path, idx, f)
        return gain * (a - b)
    T.add(child, "rotation_euler", fn, f0, f1, index=out_idx if out_idx is not None else idx)


def kalle_lipsync(T, k, scene, f0, f1, open_boost=None):
    """Kiefer/Mund in 3 Formen (zu, halb, offen) nach Lautstaerke, Schnurrbart wippt,
    Brauen betonen Highlight-Woerter."""
    amp = scene["amp"]
    base = scene["f0"]

    def a(f):
        i = int(f) - base
        if 0 <= i < len(amp):
            # leicht geglaettet
            vals = [amp[j] for j in range(max(0, i - 1), min(len(amp), i + 2))]
            return sum(vals) / len(vals)
        return 0.0

    def shape(f):
        v = a(f)
        return 0.18 if v < 0.12 else 0.62 if v < 0.45 else 1.0

    def mouth_scale(f):
        s = 0.5 * shape(f) + 0.25 * shape(f - 1) + 0.25 * shape(f + 1)
        return (1 + 0.15 * (s - 0.18), 1, s)

    T.set(k.mouth, "scale", mouth_scale, f0, f1)
    T.add(k.mouth, "location", lambda f: (0, 0, -0.03 * (shape(f) - 0.18)), f0, f1)
    T.add(k.stache, "rotation_euler", lambda f: (0.12 * (a(f) - a(f - 2)), 0, 0), f0, f1)
    T.add(k.stache, "location", lambda f: (0, 0, 0.012 * shape(f)), f0, f1)
    T.add(k.head, "rotation_euler", lambda f: (-0.05 * a(f), 0, 0), f0, f1)
    for w in scene["words"]:
        if w["hl"]:
            a0, a1 = w["f0"] - 2, w["f1"] + 6
            for side in ("R", "L"):
                T.add(k.brow[side], "location", lambda f, a0=a0, a1=a1: (0, 0, 0.035 * window(f, a0, a1, 3, 6)),
                      a0, a1)


def kalle_look(T, k, target_fn, f0, f1, strength=1.0, ramp=6):
    """Pupillen schauen auf einen Weltpunkt (target_fn(f) -> Vector)."""
    def rot(f, side):
        root = Vector(T.loc(k.root, f))
        eye = root + Vector((0.115 * (1 if side == "L" else -1), -0.25, 2.03))
        d = Vector(target_fn(f)) - eye
        yaw = math.atan2(d.x, -d.y)
        pitch = math.atan2(d.z, math.hypot(d.x, d.y))
        w = strength * window(f, f0, f1, ramp, ramp)
        return (-max(-0.45, min(0.45, pitch)) * w, 0, max(-0.6, min(0.6, yaw)) * w)
    for side in ("R", "L"):
        T.add(k.pupil[side], "rotation_euler", lambda f, s=side: rot(f, s), f0, f1)


# --------------------------------------------------------- Reaktionen
def _mouth(T, k, speaking, fn, f0, f1):
    """Mund-Reaktion: ueberschreibt nur, wenn Kalle gerade nicht spricht; sonst nur verbreitern."""
    if speaking:
        T.mul(k.mouth, "scale", lambda x: (1.15, 1, 1.0 + 0.4 * window(x, f0, f1, 3, 10)), f0, f1)
    else:
        T.set(k.mouth, "scale", fn, f0, f1)
        T.set(k.mouth, "scale", lambda x: (1, 1, 0.18), f1, f1 + 1)


def kalle_react(T, k, kind, f, hold=40, props=None, speaking=False, hat=True):
    """Reaktion mit Antizipation -> Hauptbewegung -> Nachschwingen. f = Hauptakzent."""
    if kind == "neutral":
        T.add(k.head, "rotation_euler", lambda x: (0.06 * window(x, f - 4, f + 14, 4, 10), 0, 0), f - 4, f + 14)
        return
    if kind == "zweifel":
        a0 = f - 5
        env = lambda x: window(x, a0, f + hold, 5, 10, ease_out)  # noqa: E731
        ant = lambda x: window(x, a0, f + 2, 3, 3)                # noqa: E731
        T.add(k.brow["R"], "location", lambda x: (0, 0, 0.07 * env(x) * (1 + 0.15 * spring((x - f) / FPS, 3, 0.3))),
              a0, f + hold)
        T.add(k.brow["R"], "rotation_euler", lambda x: (0, 0.25 * env(x), 0), a0, f + hold)
        T.add(k.brow["L"], "location", lambda x: (0, 0, -0.02 * env(x)), a0, f + hold)
        T.add(k.head, "rotation_euler", lambda x: (0.04 * ant(x), -0.175 * env(x) * (1 + 0.12 * spring((x - f) / FPS, 2, 0.3)),
                                                   0.06 * env(x)), a0, f + hold)
        T.add(k.stache, "rotation_euler",
              lambda x: (0, 0.12 * math.sin((x - f) * 1.6) * window(x, f, f + 14, 1, 8), 0), f, f + 14)
        for side in ("R", "L"):
            T.mul(k.eye[side], "scale", lambda x, s=side: (1, 1, 1 - (0.25 if s == "L" else -0.08) * env(x)), a0, f + hold)
        return
    if kind == "staunen":
        a0 = f - 4
        T.add(k.head, "rotation_euler", lambda x: (0.12 * window(x, a0, f + 1, 3, 1) - 0.08 * window(x, f, f + hold, 3, 12), 0, 0),
              a0, f + hold)
        T.add(k.head, "location", lambda x: (0, 0, -0.03 * window(x, a0, f + 1, 3, 1) + 0.04 * window(x, f, f + hold, 3, 12)),
              a0, f + hold)

        def eyes(x):
            if x < f:
                return 1 - 0.15 * window(x, a0, f, 3, 1)
            t = (x - f) / 5
            grow = 1 + 0.6 * ease_out_back(min(1, t), 2.6)
            rel = window(x, f, f + hold, 1, 12)
            return 1 + (grow - 1) * rel
        for side in ("R", "L"):
            T.mul(k.eye[side], "scale", lambda x: (eyes(x),) * 3, a0, f + hold)
        _mouth(T, k, speaking, lambda x: (1.15, 1, 0.18 + 2.0 * window(x, f, f + hold, 3, 12) *
                                          (1 + 0.1 * spring((x - f) / FPS, 3, 0.3))), f, f + hold)
        T.add(k.mouth, "location", lambda x: (0, 0, -0.07 * window(x, f, f + hold, 3, 12)), f, f + hold)
        # Muetze huepft zweimal
        T.add(k.hat, "location", lambda x: (0, 0, 0.12 * max(0, math.sin(math.pi * (x - f) / 7)) *
                                            (1 if x - f < 7 else 0.45 if x - f < 14 else 0)), f, f + 14)
        T.mul(k.hat, "scale", lambda x: (1, 1, 1 + 0.1 * spring((x - f) / FPS, 4, 0.3)), f, f + 20)
        for side in ("R", "L"):
            T.add(k.brow[side], "location", lambda x: (0, 0, 0.06 * window(x, f, f + hold, 3, 12)), f, f + hold)
        return
    if kind == "schock":
        a0 = f - 4
        T.add(k.body, "location", lambda x: (0, 0.06 * window(x, f, f + hold, 3, 15), -0.04 * window(x, a0, f + 2, 3, 2)),
              a0, f + hold)
        T.add(k.hips, "rotation_euler", lambda x: (0.08 * window(x, f, f + hold, 3, 15), 0, 0), f, f + hold)
        for side in ("R", "L"):
            T.mul(k.eye[side], "scale", lambda x: (1 + 0.7 * window(x, f, f + hold, 2, 10) * ease_out_back(min(1, (x - f) / 5), 2.5),) * 3,
                  f, f + hold)
        _mouth(T, k, speaking, lambda x: (0.8, 1, 0.18 + 1.6 * window(x, f, f + hold, 2, 10)), f, f + hold)
        # Muetze schiesst hoch, rotiert, landet
        def hatz(x):
            t = (x - f) / 22
            if t <= 0 or t >= 1:
                return 0.0
            return 0.9 * 4 * t * (1 - t)
        if hat:
            T.add(k.hat, "location", lambda x: (0, 0, hatz(x)), f, f + 22)
            T.add(k.hat, "rotation_euler", lambda x: (0, 0, 2 * math.pi * ease_in_out((x - f) / 22)), f, f + 22)
            T.mul(k.hat, "scale", lambda x: (1, 1, 1 - 0.18 * spring((x - f - 22) / FPS, 4, 0.3) if x > f + 22 else 1),
                  f + 22, f + 40)
        for side, sx in (("R", -1), ("L", 1)):
            T.add(k.sh[side], "rotation_euler", lambda x, s=sx: (0, -s * 0.5 * window(x, f, f + hold, 3, 15), 0),
                  f, f + hold)
        return
    if kind == "traurig":
        kalle_traurig(T, k, f - 6, f + hold, speaking=speaking)
        return
    if kind == "jubel":
        a0 = f - 5
        def up(x):
            if x < f:
                return -0.15 * window(x, a0, f, 3, 1)
            return window(x, f, f + hold, 4, 14) * (1 + 0.08 * spring((x - f) / FPS, 2.5, 0.3))
        for side, sx in (("R", -1), ("L", 1)):
            T.add(k.sh[side], "rotation_euler", lambda x, s=sx: (-0.25 * up(x), -s * 2.45 * up(x), 0), a0, f + hold)
            T.add(k.el[side], "rotation_euler", lambda x, s=sx: (-0.35 * up(x), 0, 0), a0, f + hold)
        def jump(x):
            t = (x - f) / 14
            return 0.28 * 4 * t * (1 - t) if 0 < t < 1 else 0
        T.add(k.body, "location", lambda x: (0, 0, jump(x) - 0.06 * window(x, a0, f + 1, 3, 1)), a0, f + 16)
        T.mul(k.torso, "scale", lambda x: (1, 1, 1 + 0.06 * spring((x - f - 14) / FPS, 3, 0.3) if x > f + 14 else 1), f + 14, f + 34)
        if hat:
            T.add(k.hat, "location", lambda x: (0, 0, 0.25 * 4 * ((x - f - 2) / 16) * (1 - (x - f - 2) / 16)
                                                if 0 < x - f - 2 < 16 else 0), f, f + 20)
        _mouth(T, k, speaking, lambda x: (1.3, 1, 0.18 + 1.2 * window(x, f, f + hold, 3, 10)), f, f + hold)
        for side in ("R", "L"):
            T.add(k.brow[side], "location", lambda x: (0, 0, 0.05 * window(x, f, f + hold, 3, 12)), f, f + hold)
        return


# Erlaubte Werte fuer "reaktion" (Episoden-JSON): neutral, zweifel, staunen, schock, jubel, traurig (ab 2.2)
REAKTIONEN = ("neutral", "zweifel", "staunen", "schock", "jubel", "traurig")


def kalle_traurig(T, k, f0, f1, speaking=False, ramp=14, staerke=1.0):
    """Traurig (2.2): Lider halb gesenkt, Brauen schraeg nach innen, Mundwinkel nach unten, Schultern haengen,
    Kopf gesenkt, Blick nach unten. Langsame Rampe (ramp Frames)."""
    env = lambda x: staerke * window(x, f0, f1, ramp, ramp)  # noqa: E731
    for side, sx in (("R", -1), ("L", 1)):
        T.set(k.lid[side], "scale", lambda x: (1, 1, 1) if env(x) > 0.01 else (0, 0, 0), f0 - 1, f1 + 1)
        T.set(k.lid[side], "scale", lambda x: (0, 0, 0), f1 + 1, f1 + 2)
        T.add(k.lid[side], "rotation_euler", lambda x: (1.3 * env(x), 0, 0), f0, f1)
        T.add(k.brow[side], "rotation_euler", lambda x, sx=sx: (0, sx * 0.42 * env(x), 0), f0, f1)
        T.add(k.brow[side], "location", lambda x, sx=sx: (-sx * 0.012 * env(x), 0, 0.012 * env(x)), f0, f1)
        T.add(k.sh[side], "location", lambda x: (0, 0.02 * env(x), -0.06 * env(x)), f0, f1)
        T.add(k.sh[side], "rotation_euler", lambda x, sx=sx: (0.12 * env(x), 0, sx * 0.08 * env(x)), f0, f1)
        T.add(k.pupil[side], "rotation_euler", lambda x: (0.32 * env(x), 0, 0), f0, f1)
    T.add(k.head, "rotation_euler", lambda x: (0.26 * env(x), 0, 0), f0, f1)
    T.add(k.hips, "rotation_euler", lambda x: (0.1 * env(x), 0, 0), f0, f1)
    T.add(k.neck, "location", lambda x: (0, -0.02 * env(x), -0.03 * env(x)), f0, f1)
    T.set(k.frown, "scale", lambda x: (1, 1, 1) if env(x) > 0.25 else (0, 0, 0), f0 - 1, f1 + 1)
    T.set(k.frown, "scale", lambda x: (0, 0, 0), f1 + 1, f1 + 2)
    if not speaking:
        T.mul(k.mouth, "scale", lambda x: (1 - 0.35 * env(x), 1, 1 - 0.4 * env(x)), f0, f1)
    T.add(k.stache, "location", lambda x: (0, 0, -0.012 * env(x)), f0, f1)


def kalle_haende(T, k, art, f0, f1, ramp=6):
    """Haende (2.2): 'kneten' (beide Haende druecken abwechselnd), 'greifen' (Finger eingerollt),
    'stuetzen' (Haende flach auf den Tisch gestuetzt)."""
    if art == "stuetzen":
        pose(T, k, {"sh_R": (-0.55, 0, 0.25), "sh_L": (-0.55, 0, -0.25), "el_R": (-0.35, 0, 0), "el_L": (-0.35, 0, 0),
                    "hips": (0.12, 0, 0)}, f0, f1, ramp, ramp)
        for side in ("R", "L"):
            T.add(k.hand[side], "rotation_euler", lambda x: (-0.9 * window(x, f0, f1, ramp, ramp), 0, 0), f0, f1 + ramp)
        return
    if art == "kneten":
        pose(T, k, {"sh_R": (-0.85, 0, 0.3), "sh_L": (-0.85, 0, -0.3), "el_R": (-0.75, 0, 0), "el_L": (-0.75, 0, 0)},
             f0, f1, ramp, ramp)
        for side, ph in (("R", 0.0), ("L", math.pi)):
            T.add(k.sh[side], "rotation_euler",
                  lambda x, ph=ph: (0.18 * math.sin(x * 0.45 + ph) * window(x, f0, f1, ramp, ramp), 0, 0), f0, f1)
            T.add(k.hand[side], "rotation_euler",
                  lambda x, ph=ph: (-0.4 - 0.3 * math.sin(x * 0.45 + ph), 0, 0) if f0 <= x <= f1 else (0, 0, 0), f0, f1)
        return
    if art == "greifen":
        for side in ("R", "L"):
            T.mul(k.finger[side], "scale", lambda x: (1, 1, 1 - 0.5 * window(x, f0, f1, 3, 3)), f0, f1)
            T.add(k.finger[side], "rotation_euler", lambda x: (-1.2 * window(x, f0, f1, 3, 3), 0, 0), f0, f1)


def reaction(T, coll, k, kind, f, hold=40, speaking=False, seed=0, hat=True):
    """Reaktion inkl. Effekten: staunen -> '!'-Partikel, jubel -> Mehlwolke + Konfetti.
    (schock: harter Kamera-Zoom macht die Regie)."""
    import props as PR
    kalle_react(T, k, kind, f, hold, speaking=speaking, hat=hat)
    head = lambda: Vector(T.loc(k.root, f)) + Vector((0, -0.1, 2.45))  # noqa: E731
    if kind == "staunen":
        PR.burst(T, coll, f"bang_{f}_{seed}", "bang", tuple(head()), f + 1, 5, 900 + seed, speed=(0.8, 1.3),
                 up=1.2, spread=0.9, gravity=-1.5, life=(16, 22), size=(0.8, 1.2), spin=1.0, drag=2.0)
    elif kind == "jubel":
        base = Vector(T.loc(k.root, f))
        PR.burst(T, coll, f"jflour_{f}_{seed}", "puff", tuple(base + Vector((0, -0.2, 1.4))), f, 26, 910 + seed,
                 speed=(1.0, 2.0), up=0.6, gravity=-0.5, life=(22, 34), size=(1.0, 2.0), drag=3.0, ring=True)
        PR.burst(T, coll, f"jconf_{f}_{seed}", "confetti", tuple(base + Vector((0, -0.2, 2.7))), f + 2, 48,
                 920 + seed, speed=(1.8, 3.2), up=1.4, spread=1.2, gravity=-3.0, life=(34, 48), size=(1.0, 1.5),
                 drag=1.6, spin=10.0, flutter=0.6, wobble=0.04,
                 kinds=["confetti_#FFE14D", "confetti_#2EE6D6", "confetti_#FF5A5F", "confetti_#3DDC84",
                        "confetti_#F5F1E8"])


# =================================================================== Byte
PIX = 0.024


def _pixels(name, cells, mat, parent, coll, z0=0.0, y=0.0, px=PIX):
    """Pixel-Grafik als ein Mesh: cells = [(col, row), ...] relativ zur Mitte."""
    bm = bmesh.new()
    s = px * 0.86
    for cx, cy in cells:
        x, z = cx * px, cy * px + z0
        vs = [bm.verts.new((x - s / 2, y, z - s / 2)), bm.verts.new((x + s / 2, y, z - s / 2)),
              bm.verts.new((x + s / 2, y, z + s / 2)), bm.verts.new((x - s / 2, y, z + s / 2))]
        f = bm.faces.new(vs)
        f.normal_update()
    for f in bm.faces:
        if f.normal.y > 0:
            f.normal_flip()
    return L.from_bm(name, bm, mat, parent, (0, 0, 0), coll)


def _eye_cells(kind):
    """Pixel-Augen (linkes Auge, rechtes wird gespiegelt) – Mitte (0,0)."""
    if kind == "neutral":
        return [(0, 0), (1, 0), (0, 1), (1, 1)]
    if kind == "happy":      # ^
        return [(-1, 0), (0, 1), (1, 2), (2, 1), (3, 0)]
    if kind == "serious":    # Strich
        return [(-1, 0), (0, 0), (1, 0), (2, 0)]
    if kind == "surprised":  # O
        return [(0, -1), (1, -1), (-1, 0), (2, 0), (-1, 1), (2, 1), (0, 2), (1, 2)]
    if kind == "blink":
        return [(-1, 0), (0, 0), (1, 0), (2, 0)]
    if kind == "worried":    # schraeg nach aussen abfallend
        return [(-1, 2), (0, 1), (1, 1), (2, 0)]
    if kind == "curious":    # gross, Punkt oben
        return [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)]
    return []


EXPRS = ["neutral", "happy", "serious", "surprised", "wink", "curious", "worried"]

# ------------------------------------------------------------------ Byte 2.1: Display-Augen je Reaktion
BYTE_EYES = ["neutral", "jubel", "staunen", "schock", "zweifel", "wink", "traurig"]
# aeltere Ausdrucksnamen der Regie-Dateien -> Reaktion (Byte 2.1)
EYE_ALIAS = {"happy": "jubel", "surprised": "staunen", "curious": "staunen", "worried": "schock",
             "serious": "zweifel", "rund": "neutral"}
EYE_X, EYE_Z = 0.056, 0.024


def _poly_mesh(name, polys, mat, parent, coll, y=0.0):
    """Flache Polygone (x, z) in der XZ-Ebene, Vorderseite -Y."""
    bm = bmesh.new()
    for pts in polys:
        vs = [bm.verts.new((x, y, z)) for x, z in pts]
        f = bm.faces.new(vs)
        f.normal_update()
        if f.normal.y > 0:
            f.normal_flip()
    return L.from_bm(name, bm, mat, parent, (0, 0, 0), coll)


def _disc(cx, cz, r, n=22, sz=1.0):
    return [(cx + r * math.cos(2 * math.pi * k / n), cz + r * sz * math.sin(2 * math.pi * k / n)) for k in range(n)]


def _arc(cx, cz, R, w, a0, a1, n=12):
    out = []
    ro, ri = R + w / 2, R - w / 2
    for k in range(n):
        t0, t1 = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
        out.append([(cx + ri * math.cos(t0), cz + ri * math.sin(t0)), (cx + ro * math.cos(t0), cz + ro * math.sin(t0)),
                    (cx + ro * math.cos(t1), cz + ro * math.sin(t1)), (cx + ri * math.cos(t1), cz + ri * math.sin(t1))])
    for t in (a0, a1):                     # runde Enden
        out.append(_disc(cx + R * math.cos(t), cz + R * math.sin(t), w / 2, 10))
    return out


def _stroke(pts, w):
    out = []
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        dx, dz = x1 - x0, z1 - z0
        ln = math.hypot(dx, dz)
        nx, nz = -dz / ln * w / 2, dx / ln * w / 2
        out.append([(x0 + nx, z0 + nz), (x0 - nx, z0 - nz), (x1 - nx, z1 - nz), (x1 + nx, z1 + nz)])
    for x, z in pts:
        out.append(_disc(x, z, w / 2, 10))
    return out


def _eye_polys(kind, cx, cz, outer):
    """Ein Auge (outer = Richtung nach aussen, -1 links / +1 rechts). Rueckgabe: (Polygone, Glanzpunkte)."""
    if kind == "neutral":                  # rund
        return [_disc(cx, cz, 0.03)], []
    if kind == "jubel":                    # Halbmond (Bogen nach oben)
        return _arc(cx, cz - 0.012, 0.027, 0.015, 0.0, math.pi), []
    if kind == "staunen":                  # gross mit Glanzpunkt
        return [_disc(cx, cz + 0.004, 0.044, 28)], [_disc(cx + 0.016, cz + 0.022, 0.012, 14),
                                                   _disc(cx - 0.015, cz - 0.012, 0.006, 10)]
    if kind == "schock":                   # Zickzack
        pts = [(cx - 0.036 + 0.012 * k, cz + (0.011 if k % 2 else -0.011)) for k in range(7)]
        return _stroke(pts, 0.009), []
    if kind == "traurig":                  # 2.2: flache, nach unten gebogene Boegen, aussen tiefer (haengend)
        pts = []
        for i in range(9):
            t = i / 8
            x = cx + outer * (-0.034 + 0.068 * t)          # von innen nach aussen
            z = cz - 0.002 + 0.007 * math.sin(math.pi * t) - 0.034 * t
            pts.append((x, z))
        return _stroke(pts, 0.011), []
    if kind == "zweifel":                  # schraeg, halb geschlossen (aussen hoch, innen tief)
        r = 0.031
        hi, lo = 0.016, -0.002
        top_out, top_in = (cx + outer * r, cz + hi), (cx - outer * r, cz + lo)
        arc = [(cx + r * math.cos(t), cz + 0.85 * r * math.sin(t))
               for t in [math.pi + math.pi * k / 14 for k in range(15)]]
        if outer < 0:
            pts = [top_out] + arc + [top_in]
        else:
            pts = [top_in] + arc + [top_out]
        return [pts], []
    return [], []


def _eyes_mesh(name, kind, mat, glint_mat, parent, coll):
    ee = L.empty(name, parent, (0, 0, 0), coll)
    polys, glints = [], []
    for side, outer in ((-1, -1), (1, 1)):
        k = kind
        if kind == "wink":
            k = "neutral" if side < 0 else "jubel"
        p, g = _eye_polys(k, side * EYE_X, EYE_Z, outer)
        polys += p
        glints += g
    _poly_mesh(f"{name}_m", polys, mat, ee, coll)
    if glints:
        _poly_mesh(f"{name}_glint", glints, glint_mat, ee, coll, y=-0.0015)
    return ee


class Byte:
    """Byte (KI-Kugel). Ab Version 2.1 (v21=True): Display-Gesicht mit Augen je Reaktion, leuchtende Nahtlinien,
    Lueftungsgitter, Status-LED auf der Brust, leuchtende Antennenspitze mit Nachschwingen, kleine Arme mit Haenden,
    Schwebeschatten am Boden. Form, Farbe, Groesse und Antenne bleiben wie bisher."""

    def __init__(self, coll, name="byte", scale=1.0, light_energy=60.0, emissive=1.0, v21=True):
        self.name = name
        self.v21 = v21
        c = coll
        self.coll = coll
        self.base_scale = scale
        self.root = L.empty(f"{name}_root", coll=c)
        self.root.scale = (scale,) * 3
        self.bob = L.empty(f"{name}_bob", self.root, (0, 0, 0), c)
        self.body = L.empty(f"{name}_body", self.bob, (0, 0, 0), c)           # Spin, Squash
        self.m_shell = L.unique_mat(L.mat("byte_shell", L.TURQ, 0.55, emit=L.TURQ, strength=0.45), f"{name}_shellmat")
        L.bsdf(self.m_shell).inputs["Emission Strength"].default_value = 0.42 * emissive
        self.shell = L.ico(f"{name}_shell", 0.22, 1, (1, 1, 1), self.m_shell, self.body, (0, 0, 0), c)
        inner = L.mat("byte_core", L.TURQ, 0.5, emit=L.TURQ, strength=3.0)
        L.ico(f"{name}_core", 0.205, 2, (1, 1, 1), inner, self.body, (0, 0, 0), c)
        # Bildschirm-Gesicht
        m_screen = L.mat("byte_screen", L.NAVY, 0.45)
        m_rim = L.mat("byte_rim", L.NAVY2, 0.5)
        L.cyl(f"{name}_screenrim", 0.16, 0.05, 16 if not v21 else 28, m_rim, self.body, (0, -0.185, 0.0), c, axis="Y")
        L.cyl(f"{name}_screen", 0.145, 0.05, 16 if not v21 else 28, m_screen, self.body, (0, -0.195, 0.0), c, axis="Y")
        self.m_pix = L.unique_mat(L.mat("byte_pixel", L.TURQ, 0.5, emit=L.TURQ, strength=5.0), f"{name}_pixmat")
        self.face = L.empty(f"{name}_face", self.body, (0, -0.222, 0.0), c)
        self.expr = {}
        if v21:
            m_glint = L.mat("byte_glint", "#FFFFFF", 0.4, emit="#FFFFFF", strength=4.0)
            for e in BYTE_EYES:
                ee = _eyes_mesh(f"{name}_ex_{e}", e, self.m_pix, m_glint, self.face, c)
                ee.scale = (0, 0, 0) if e != "neutral" else (1, 1, 1)
                self.expr[e] = ee
        else:
            for e in EXPRS:
                ee = L.empty(f"{name}_ex_{e}", self.face, (0, 0, 0), c)
                if e == "wink":
                    lc, rc = _eye_cells("neutral"), _eye_cells("happy")
                else:
                    lc = rc = _eye_cells(e)
                lc2 = [(x - 3, z + 1) for x, z in lc]
                rc2 = [(-x + 3 + (1 if e in ("neutral", "surprised", "curious") else 0) - 1, z + 1) for x, z in rc]
                _pixels(f"{name}_px_{e}", lc2 + rc2, self.m_pix, ee, c)
                ee.scale = (0, 0, 0) if e != "neutral" else (1, 1, 1)
                self.expr[e] = ee
        # Code-Gesicht: laufende Mini-Code-Zeilen statt Pixelaugen (beim Code-Schreiben)
        ce = L.empty(f"{name}_ex_code", self.face, (0, 0, 0), c)
        ce.scale = (0, 0, 0)
        self.expr["code"] = ce
        rr = random.Random(77)
        cols = [L.TURQ, L.YELLOW, "#FF9F43", "#FFFFFF"]
        self.code_rows = []
        for i in range(8):
            row = L.empty(f"{name}_coderow{i}", ce, (0, -0.002, 0), c)
            x = -0.11 + rr.uniform(0, 0.03)
            for k in range(rr.randint(2, 3)):
                w = rr.uniform(0.025, 0.07)
                col = cols[(i + k) % 4] if k else L.TURQ
                L.box(f"{name}_codeseg{i}_{k}", (w, 0.004, 0.014), L.mat(f"codeseg_{col}", col, 0.5, emit=col,
                                                                          strength=4.0), row, (x + w / 2, 0, 0), c)
                x += w + 0.014
            self.code_rows.append(row)
        # Mund: kleiner Strich (still) und Equalizer (sprechen)
        self.mouth_idle = L.empty(f"{name}_mouthidle", self.face, (0, 0, 0), c)
        _pixels(f"{name}_px_mouth", [(-1, -3), (0, -3), (1, -3)], self.m_pix, self.mouth_idle, c)
        self.eq = []
        for i in range(5):
            bar = L.empty(f"{name}_eq{i}", self.face, ((i - 2) * PIX, 0, -3 * PIX - PIX / 2), c)
            L.box(f"{name}_eqbar{i}", (PIX * 0.8, 0.004, PIX * 3), self.m_pix, bar, (0, 0, 0), c, origin="bottom")
            bar.scale = (1, 1, 0.0)
            self.eq.append(bar)
        # Antenne mit Leuchtpunkt (2.1: zwei Glieder, Spitze schwingt verzoegert nach)
        self.ant = L.empty(f"{name}_ant", self.body, (0.03, 0, 0.2), c)
        m_ant = L.mat("antenna", L.METAL, 0.5, metallic=0.4)
        self.m_tip = L.unique_mat(L.mat("byte_tip", L.YELLOW, 0.4, emit=L.YELLOW, strength=4.0), f"{name}_tipmat")
        if v21:
            L.cyl(f"{name}_antstalk", 0.011, 0.09, 6, m_ant, self.ant, (0, 0, 0.045), c)
            self.ant2 = L.empty(f"{name}_ant2", self.ant, (0, 0, 0.09), c)
            L.sphere(f"{name}_antjoint", 0.012, 8, 5, (1, 1, 1), m_ant, self.ant2, (0, 0, 0), c)
            L.cyl(f"{name}_antstalk2", 0.009, 0.08, 6, m_ant, self.ant2, (0, 0, 0.04), c)
            self.tip = L.ico(f"{name}_tip", 0.032, 1, (1, 1, 1), self.m_tip, self.ant2, (0, 0, 0.082), c)
            self.halo = L.ico(f"{name}_tiphalo", 0.056, 2, (1, 1, 1),
                              L.mat("byte_tiphalo", L.YELLOW, 0.4, emit=L.YELLOW, strength=2.0, alpha=0.28),
                              self.ant2, (0, 0, 0.082), c)
            self.tiplight = L.light(f"{name}_tiplight", "POINT", 6.0, L.YELLOW, (0, 0, 0.09), size=0.05,
                                    parent=self.ant2, coll=c, shadow=False, cutoff=1.5)
        else:
            L.cyl(f"{name}_antstalk", 0.011, 0.16, 6, m_ant, self.ant, (0, 0, 0.08), c)
            self.ant2 = None
            self.tip = L.ico(f"{name}_tip", 0.032, 1, (1, 1, 1), self.m_tip, self.ant, (0, 0, 0.17), c)
        # Glow-Licht (wirft tuerkises Licht auf Kalle)
        self.light = L.light(f"{name}_light", "POINT", light_energy, L.TURQ, (0, -0.25, 0), size=0.25,
                             parent=self.body, coll=c, shadow=False, cutoff=4.0)
        self.extra = L.empty(f"{name}_extra", self.body, (0, 0, 0), c)
        self.ears = []
        self.arm, self.hand, self.fing = {}, {}, {}
        self.shadow = None
        if v21:
            self._details()
            self._arms()
            self._shadow()

    # ---------------------------------------------------------- 2.1: Details
    def _details(self):
        c, name = self.coll, self.name
        # Display: Glasreflex oben links und leuchtender Innenrand
        m_glare = L.mat("byte_glare", "#FFFFFF", 0.3, emit="#FFFFFF", strength=1.0, alpha=0.22)
        _poly_mesh(f"{name}_glare", _arc(0, 0, 0.118, 0.014, 1.85, 2.7, 8)[:8], m_glare, self.face, c, y=-0.003)
        L.torus(f"{name}_screenglow", 0.139, 0.0045, 32, 4, L.mat("byte_screenglow", L.TURQ, 0.4, emit=L.TURQ,
                                                                  strength=2.5), self.body, (0, -0.221, 0), c, axis="Y")
        # Nahtlinien entlang der Kanten der Huelle (nicht auf der Vorderseite)
        m_seam = L.mat("byte_seam", "#F2FFFE", 0.4, emit="#FFFFFF", strength=4.0)
        me = self.shell.data
        bm = bmesh.new()
        for e in me.edges:
            a, b = Vector(me.vertices[e.vertices[0]].co), Vector(me.vertices[e.vertices[1]].co)
            mid = (a + b) / 2
            if mid.y < -0.07:
                continue
            n = mid.normalized()
            d = (b - a).normalized()
            side = d.cross(n).normalized() * 0.005
            a2, b2 = a * 1.012 + n * 0.001, b * 1.012 + n * 0.001
            vs = [bm.verts.new(a2 - side), bm.verts.new(a2 + side), bm.verts.new(b2 + side), bm.verts.new(b2 - side)]
            bm.faces.new(vs)
        L.from_bm(f"{name}_seams", bm, m_seam, self.body, (0, 0, 0), c)
        # Lueftungsgitter (oben seitlich)
        d = Vector((0.7, -0.15, 0.68)).normalized()
        vent = L.empty(f"{name}_vent", self.body, tuple(d * 0.2), c)
        vent.rotation_euler = d.to_track_quat("-Y", "Z").to_euler()
        L.box(f"{name}_ventplate", (0.075, 0.012, 0.055), L.mat("byte_vent", L.NAVY2, 0.5), vent, (0, 0, 0), c,
              bevel=0.006)
        m_slat = L.mat("byte_slat", "#0E0C1E", 0.6)
        for k in range(4):
            L.box(f"{name}_ventslat{k}", (0.058, 0.004, 0.006), m_slat, vent, (0, -0.0065, -0.018 + 0.012 * k), c)
        # Status-LED auf der Brust (pulsiert beim Sprechen)
        self.m_led = L.unique_mat(L.mat("byte_led", L.GREEN, 0.4, emit=L.GREEN, strength=4.0), f"{name}_ledmat")
        led_p = Vector((0.0, -0.118, -0.183))
        bez = L.empty(f"{name}_ledbez", self.body, tuple(led_p), c)
        bez.rotation_euler = led_p.normalized().to_track_quat("-Y", "Z").to_euler()
        L.cyl(f"{name}_ledring", 0.02, 0.012, 14, L.mat("byte_rim", L.NAVY2, 0.5), bez, (0, 0, 0), c, axis="Y")
        self.led = L.sphere(f"{name}_led", 0.013, 10, 6, (1, 0.6, 1), self.m_led, bez, (0, -0.007, 0), c)
        full = tuple(self.m_led.diffuse_color)
        self.led_dim = tuple(0.55 * x for x in full[:3])
        self.m_led.diffuse_color = self.led_dim + (1.0,)

    def _arms(self):
        c, name = self.coll, self.name
        m_arm = L.mat("byte_arm", L.NAVY2, 0.5)
        m_joint = L.mat("byte_joint", L.TURQ, 0.5, emit=L.TURQ, strength=1.2)
        m_hand = L.mat("byte_hand", "#D9FBF7", 0.5, emit=L.TURQ, strength=0.3)
        self.arm_base = {}
        for side, sx in (("R", -1), ("L", 1)):
            sh = L.empty(f"{name}_arm_{side}", self.body, (sx * 0.19, 0.0, -0.085), c)
            L.sphere(f"{name}_shoulder_{side}", 0.026, 10, 6, (1, 1, 1), m_joint, sh, (0, 0, 0), c)
            L.cyl(f"{name}_upper_{side}", 0.013, 0.1, 8, m_arm, sh, (0, 0, -0.055), c)
            hd = L.empty(f"{name}_hand_{side}", sh, (0, 0, -0.112), c)
            L.sphere(f"{name}_palm_{side}", 0.028, 10, 7, (1.0, 0.8, 0.95), m_hand, hd, (0, 0, -0.016), c)
            fing = {}
            for fn, (fx, fy, fz, ln) in {"index": (-sx * 0.011, -0.012, -0.036, 0.034),
                                          "middle": (sx * 0.011, -0.012, -0.036, 0.032),
                                          "thumb": (-sx * 0.026, -0.012, -0.012, 0.026)}.items():
                fp = L.empty(f"{name}_{fn}_{side}", hd, (fx, fy, fz), c)
                L.cyl(f"{name}_{fn}seg_{side}", 0.0085, ln, 6, m_hand, fp, (0, 0, -ln / 2), c)
                L.sphere(f"{name}_{fn}tip_{side}", 0.0095, 8, 5, (1, 1, 1), m_hand, fp, (0, 0, -ln), c)
                fing[fn] = fp
            fing["thumb"].rotation_euler = (0, -sx * 0.7, 0)
            base = (0.15, -sx * 0.5, 0.0)
            sh.rotation_euler = base
            self.arm_base[side] = base
            self.arm[side], self.hand[side], self.fing[side] = sh, hd, fing
            for fn, cu in HAND_POSES["rest"].items():
                fing[fn].rotation_euler[0] = -1.5 * cu

    def _shadow(self):
        m = L.mat("byte_shadow", "#05040C", 0.9, alpha=0.38)
        bm = bmesh.new()
        n = 28
        vs = [bm.verts.new((math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n), 0)) for k in range(n)]
        bm.faces.new(vs)
        self.shadow = L.from_bm(f"{self.name}_shadow", bm, m, None, (0, 0, -50), self.coll)
        self.shadow.scale = (0, 0, 0)

    def add_ear_rings(self):
        """Ohr-Ringe links/rechts (neuere Folgen)."""
        m = L.mat("byte_earring", L.NAVY2, 0.45, emit=L.TURQ, strength=0.6)
        m2 = L.mat("byte_earglow", L.TURQ, 0.4, emit=L.TURQ, strength=4.0)
        for sx in (-1, 1):
            e = L.torus(f"{self.name}_earring{sx}", 0.075, 0.018, 16, 5, m, self.body, (sx * 0.215, 0, 0.0),
                        self.coll, axis="X")
            L.torus(f"{self.name}_earglow{sx}", 0.05, 0.008, 14, 4, m2, e, (sx * 0.012, 0, 0), self.coll, axis="X")
            self.ears.append(e)


# Handhaltungen: Kruemmung je Finger (0 gestreckt .. 1 eingerollt)
HAND_POSES = {"rest": {"index": 0.3, "middle": 0.35, "thumb": 0.2},
              "offen": {"index": 0.0, "middle": 0.0, "thumb": 0.0},
              "point": {"index": 0.0, "middle": 1.0, "thumb": 0.8},
              "grab": {"index": 0.95, "middle": 1.0, "thumb": 0.9},
              "snap": {"index": 0.4, "middle": 0.45, "thumb": 0.75}}


def byte_hand(T, b, side, kind, f_in, f_out=None, ramp=4):
    """Handhaltung (greifen, zeigen, schnippen, offen) als additiver Layer ueber der Ruhehaltung."""
    if not b.v21:
        return
    end = f_out + ramp if f_out is not None else 10 ** 6

    def env(f):
        a = ease_out(min(1.0, max(0.0, (f - f_in) / ramp)))
        if f_out is not None and f > f_out:
            a *= 1 - ease_out(min(1.0, (f - f_out) / ramp))
        return a
    for fn, cu in HAND_POSES[kind].items():
        d = -1.5 * (cu - HAND_POSES["rest"][fn])
        T.add(b.fing[side][fn], "rotation_euler", lambda f, d=d: (d * env(f), 0, 0), f_in - 1, min(end, f_in + 10 ** 5))


def byte_arm(T, b, side, rot, f_in, f_out=None, ramp=5, ramp_out=7, overshoot=1.6):
    """Arm in eine Zielrotation (absolut, Euler) mit Overshoot; zurueck in die Ruhehaltung ab f_out."""
    if not b.v21:
        return
    base = b.arm_base[side]
    d = [r - b0 for r, b0 in zip(rot, base)]
    end = f_out + ramp_out if f_out is not None else 10 ** 6

    def env(f):
        if f < f_in:
            return 0.0
        a = ease_out_back(min(1.0, (f - f_in) / ramp), overshoot)
        if f_out is not None and f > f_out:
            a *= 1 - ease_in_out(min(1.0, (f - f_out) / ramp_out))
        return a
    T.add(b.arm[side], "rotation_euler", lambda f: (d[0] * env(f), d[1] * env(f), d[2] * env(f)), f_in - 1,
          min(end, f_in + 10 ** 5))
    return env


def byte_snap(T, b, side, f, raise_arm=True):
    """Schnippen: Daumen und Mittelfinger druecken (f-4), Mittelfinger schnellt bei f, Hand federt."""
    if not b.v21:
        return f
    sx = -1 if side == "R" else 1
    if raise_arm:
        byte_arm(T, b, side, (-1.9, -sx * 0.55, 0.0), f - 7, f + 8, ramp=4, ramp_out=6)
    byte_hand(T, b, side, "snap", f - 5, f, ramp=3)
    T.add(b.fing[side]["middle"], "rotation_euler", lambda x: (-1.2 * window(x, f, f + 8, 1, 6), 0, 0), f, f + 8)
    T.add(b.fing[side]["thumb"], "rotation_euler", lambda x: (0.6 * window(x, f, f + 8, 1, 6), 0, 0), f, f + 8)
    T.add(b.hand[side], "rotation_euler", lambda x: (0.35 * spring((x - f) / FPS, 5, 0.3), 0, 0), f, f + 12)
    return f


def byte_type(T, b, f0, f1, speed=4):
    """Tippen mit beiden Haenden (abwechselnd, schnell)."""
    if not b.v21:
        return
    for side, sx in (("R", -1), ("L", 1)):
        byte_arm(T, b, side, (-0.75, -sx * 0.25, 0.0), f0, f1, ramp=4, ramp_out=6)
        byte_hand(T, b, side, "point", f0, f1, ramp=3)
        ph = 0 if side == "R" else speed / 2
        T.add(b.arm[side], "rotation_euler",
              lambda f, ph=ph: (0.28 * max(0.0, math.sin(2 * math.pi * (f + ph) / speed)) * window(f, f0, f1, 3, 3), 0, 0),
              f0, f1)


def byte_idle(T, b, f0, f1, seed=3, amp=0.03):
    """Schweben als Sinus (0,8 Hz), Antenne schwingt bei Richtungswechsel nach, Leuchtpunkt pulsiert.
    2.1: Arme pendeln, Status-LED atmet, Antennenspitze leuchtet, Schatten am Boden."""
    ph = random.Random(seed).uniform(0, 6.28)
    T.add(b.bob, "location", lambda f: (0, 0, amp * math.sin(2 * math.pi * 0.8 * f / FPS + ph)), f0, f1)
    T.add(b.bob, "rotation_euler", lambda f: (0.05 * math.sin(2 * math.pi * 0.4 * f / FPS + ph), 0,
                                              0.06 * math.sin(2 * math.pi * 0.27 * f / FPS + ph)), f0, f1)
    tip = L.bsdf(b.m_tip).inputs["Emission Strength"]
    T.set(tip, "default_value", lambda f: 3.0 + 2.0 * (0.5 + 0.5 * math.sin(2 * math.pi * 1.1 * f / FPS + ph)), f0, f1)
    if not b.v21:
        return
    # Leuchtende Spitze: Halo pulsiert (auch in Workbench sichtbar)
    T.set(b.halo, "scale", lambda f: (0.9 + 0.25 * (0.5 + 0.5 * math.sin(2 * math.pi * 1.1 * f / FPS + ph)),) * 3, f0, f1)
    # Arme pendeln leicht gegen das Schweben
    for side, sx in (("R", -1), ("L", 1)):
        T.add(b.arm[side], "rotation_euler",
              lambda f, sx=sx: (0.12 * math.sin(2 * math.pi * 0.8 * f / FPS + ph - 0.9),
                                sx * 0.06 * math.sin(2 * math.pi * 0.4 * f / FPS + ph + sx), 0), f0, f1)
    # Status-LED: ruhiges Atmen
    T.mul(b.led, "scale", lambda f: (1 + 0.12 * math.sin(2 * math.pi * 0.5 * f / FPS + ph),) * 3, f0, f1)
    byte_shadow(T, b, f0, f1)


def byte_shadow(T, b, f0, f1, radius=0.19):
    """Schwebeschatten: Scheibe auf der Flaeche unter Byte (Raycast gegen die statische Szene),
    kleiner und schwaecher, je hoeher Byte schwebt."""
    import bpy
    cache = {}

    def compute():
        if cache:
            return cache
        anim_ptrs = {ch["t"].as_pointer() for ch in T.ch.values() if isinstance(ch["t"], bpy.types.Object)}
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        sc = bpy.context.scene

        def ok(o):
            while o is not None:
                if o.as_pointer() in anim_ptrs or o.name.startswith(b.name):
                    return False
                o = o.parent
            return True
        for f in range(f0, f1 + 1):
            s = T.val(b.root, "scale", 0, f)
            p = Vector(T.loc(b.root, f)) + Vector(T.loc(b.bob, f)) * s
            if s < 0.05:
                cache[f] = None
                continue
            org = p - Vector((0, 0, 0.2 * s))
            hit = None
            for _ in range(12):
                res, loc, nrm, _i, obj, _m = sc.ray_cast(dg, org, Vector((0, 0, -1)), distance=6.0)
                if not res:
                    break
                orig = obj.original if hasattr(obj, "original") else obj
                if ok(orig) and nrm.z > 0.5:
                    hit = loc
                    break
                org = loc - Vector((0, 0, 1e-3))
            if hit is None:
                cache[f] = None
                continue
            h = p.z - hit.z
            k = max(0.35, min(1.05, 1.15 - 0.3 * h))
            cache[f] = (hit + Vector((0, 0, 0.004)), radius * s * k)
        return cache

    T.set(b.shadow, "location", lambda f: tuple(compute()[f][0]) if compute().get(f) else (0, 0, -50), f0, f1)
    T.set(b.shadow, "scale", lambda f: (compute()[f][1], compute()[f][1], 1) if compute().get(f) else (0, 0, 0), f0, f1)


def antenna_spring(T, b, f0, f1, gain=7.0):
    """Antenne: gedaempfte Feder, angetrieben von der Beschleunigung der Byte-Bewegung.
    2.1: das obere Glied mit der Spitze folgt verzoegert (Peitschen-Effekt)."""
    cache = {}

    def sim():
        if cache:
            return cache
        pos = {}
        for f in range(f0 - 2, f1 + 1):
            p = Vector(T.loc(b.root, f)) + Vector(T.loc(b.bob, f))
            pos[f] = p
        th = Vector((0, 0)); om = Vector((0, 0))
        w, z, dt = 2 * math.pi * 2.2, 0.22, 1 / FPS
        for f in range(f0, f1 + 1):
            acc = (pos[f] - 2 * pos[f - 1] + pos[f - 2]) / (dt * dt)
            drive = Vector((acc.y, -acc.x)) * (gain / 1000.0)  # Neigung entgegen der Beschleunigung
            spin = T.val(b.body, "rotation_euler", 2, f) - T.val(b.body, "rotation_euler", 2, f - 1)
            drive += Vector((0, spin * 2.5))
            a = -w * w * th - 2 * z * w * om + drive * w * w
            om = om + a * dt
            th = th + om * dt
            cache[f] = (max(-0.9, min(0.9, th.x)), max(-0.9, min(0.9, th.y)))
        return cache
    T.add(b.ant, "rotation_euler", lambda f: (sim()[f][0], sim()[f][1], 0) if f in sim() else (0, 0, 0), f0, f1)
    if getattr(b, "ant2", None) is not None:
        def lag(f, k):
            d = 3
            if f in sim() and f - d in sim():
                return 0.8 * (sim()[f - d][k] - 0.5 * sim()[f][k])
            return 0.0
        T.add(b.ant2, "rotation_euler", lambda f: (lag(f, 0), lag(f, 1), 0), f0, f1)


def byte_face(T, b, schedule, f0, f1):
    """schedule: [(frame, ausdruck), ...] – Wechsel mit 3-Frame-Pop.
    2.1: Ausdruecke sind Reaktionen (neutral, jubel, staunen, schock, zweifel, wink, code);
    alte Namen (happy, surprised, worried, serious, curious) werden umgesetzt."""
    if getattr(b, "v21", False):
        schedule = [(fr, EYE_ALIAS.get(e, e)) for fr, e in schedule]
    schedule = sorted(schedule)

    def active(f):
        cur = schedule[0][1]
        for fr, e in schedule:
            if fr <= f:
                cur = e
        return cur

    def last_change(f):
        lc = schedule[0][0]
        for fr, e in schedule:
            if fr <= f:
                lc = fr
        return lc

    if getattr(b, "v21", False) or "traurig" in b.expr:
        spans, cur = [], None
        for fr, e in schedule + [(f1 + 1, "_ende")]:
            if e == "traurig" and cur is None:
                cur = fr
            elif e != "traurig" and cur is not None:
                spans.append((max(f0, cur), min(f1, fr)))
                cur = None
        for a, z in spans:
            byte_traurig(T, b, a, z)

    for e, obj in b.expr.items():
        def sc(f, e=e):
            if active(f) != e:
                # ausblenden in 2 Frames
                prev = active(f - 2)
                return (0, 0, 0) if prev != e else (1, 1, max(0.0, 1 - (f - last_change(f) + 1) / 2))
            t = (f - last_change(f)) / 4
            s = ease_out_back(min(1, t), 2.5) if last_change(f) > schedule[0][0] - 1 else 1
            return (1, 1, max(0.05, s))
        T.set(obj, "scale", sc, f0, f1)


def byte_traurig(T, b, f0, f1, ramp=20):
    """2.2: Antenne knickt langsam ein, Brust-LED pulsiert langsamer und gedimmt (ohne v21: nur die Antenne)."""
    env = lambda x: window(x, f0, f1, ramp, ramp)  # noqa: E731
    T.add(b.ant, "rotation_euler", lambda x: (0.75 * env(x), 0.15 * env(x), 0), f0, f1)
    if getattr(b, "ant2", None) is not None:
        T.add(b.ant2, "rotation_euler", lambda x: (0.85 * env(x), 0, 0), f0, f1)
    if getattr(b, "v21", False):
        T.mul(b.led, "scale", lambda x: (1 - env(x) * (0.25 - 0.15 * math.sin(2 * math.pi * 0.25 * x / FPS)),) * 3, f0, f1)
        for k_ in range(3):
            T.mul(b.m_led, "diffuse_color", lambda x: 1 - 0.55 * env(x), f0, f1, index=k_)
        T.mul(b.halo, "scale", lambda x: (1 - 0.35 * env(x),) * 3, f0, f1)


def byte_code_face(T, b, f0, f1, speed=0.09):
    """Code-Zeilen laufen nach oben ueber den Bildschirm (Endlos-Band), Breite folgt dem runden Rand."""
    n = len(b.code_rows)
    span = 0.26
    r = 0.135

    for i, row in enumerate(b.code_rows):
        def z(f, i=i):
            return ((i * span / n + speed * (f - f0) / FPS) % span) - span / 2

        def scl(f, i=i):
            zz = z(f)
            w = math.sqrt(max(0.0, 1 - (zz / r) ** 2))
            return (w, 1, 1 if abs(zz) < r - 0.01 else 0)
        T.set(row, "location", lambda f, i=i: (0, -0.002, z(f, i)), f0, f1)
        T.set(row, "scale", scl, f0, f1)


def byte_blinks(T, b, f0, f1, seed=11):
    r = random.Random(seed)
    t = f0 + r.randint(25, 60)
    while t < f1 - 8:
        T.mul(b.face, "scale", lambda f, t=t: (1, 1, 1 - 0.85 * window(f, t, t + 6, 2, 4)), t, t + 6)
        t += int(r.uniform(2.6, 4.2) * FPS)


def byte_speak(T, b, scene, f0, f1):
    """Pixel-Equalizer im Takt der Lautstaerke, Lichtpuls bei Highlight-Woertern."""
    eq = scene["eq"]
    amp = scene["amp"]
    base = scene["f0"]

    def band(f, k):
        i = int(f) - base
        if 0 <= i < len(eq):
            return min(1.0, eq[i][k] * (0.6 + 0.6 * amp[i]))
        return 0.0

    def talking(f):
        i = int(f) - base
        return 0 <= i < len(amp) and amp[i] > 0.05

    if getattr(b, "v21", False):           # 2.1: Status-LED pulsiert mit der Lautstaerke
        def amp_f(f):
            i = int(f) - base
            return amp[i] if 0 <= i < len(amp) else 0.0
        T.mul(b.led, "scale", lambda f: (1 + 1.1 * amp_f(f),) * 3, f0, f1)
        for k in range(3):
            T.add(b.m_led, "diffuse_color", lambda f, k=k: 0.55 * amp_f(f) * (1.0 - b.led_dim[k]), f0, f1, index=k)
    for k, bar in enumerate(b.eq):
        T.set(bar, "scale", lambda f, k=k: (1, 1, (0.15 + 0.85 * band(f, k)) if talking(f) else 0.0), f0, f1)
    T.set(b.mouth_idle, "scale", lambda f: (0, 0, 0) if talking(f) else (1, 1, 1), f0, f1)
    shell = L.bsdf(b.m_shell).inputs["Emission Strength"]
    T.add(b.light.data, "energy", lambda f: 25 * (amp[int(f) - base] if 0 <= int(f) - base < len(amp) else 0), f0, f1)
    for w in scene["words"]:
        if w["hl"]:
            a0 = w["f0"] - 2
            T.add(shell, "default_value", lambda f, a0=a0: 1.2 * window(f, a0, a0 + 12, 2, 9), a0, a0 + 12)
            T.add(b.light.data, "energy", lambda f, a0=a0: 160 * window(f, a0, a0 + 12, 2, 9), a0, a0 + 12)
            T.mul(b.body, "scale", lambda f, a0=a0: (1 + 0.1 * window(f, a0, a0 + 10, 2, 7),) * 3, a0, a0 + 10)


# =================================================================== Helfer
class Helper(Byte):
    def __init__(self, coll, n, mark):
        super().__init__(coll, name=f"helper{n}", scale=0.45, light_energy=25.0, emissive=1.1, v21=False)
        c = coll
        self.n = n
        badge = L.empty(f"helper{n}_badge", self.body, (0.17, -0.12, 0.15), c)
        L.cyl(f"helper{n}_badgedisc", 0.075, 0.03, 14, L.mat("badge", L.GOLD, 0.5, emit=L.GOLD, strength=0.4),
              badge, (0, 0, 0), c, axis="Y")
        L.text(f"helper{n}_badgenum", str(n), 0.11, L.mat("badgenum", L.NAVY, 0.5), badge, (0, -0.02, -0.005), c,
               extrude=0.004, font=L.font())
        self.badge = badge
        mk = L.empty(f"helper{n}_mark", self.body, (0, 0, 0), c)
        self.mark = mk
        if mark == "scan":       # Scan-Brille
            m_g = L.mat("scanglass", L.TURQ, 0.3, emit=L.TURQ, strength=2.5, alpha=0.55)
            m_f = L.mat("scanframe", L.NAVY2, 0.5)
            for sx in (-1, 1):
                L.box(f"helper{n}_lens{sx}", (0.11, 0.012, 0.075), m_g, mk, (sx * 0.075, -0.235, 0.03), c)
                L.box(f"helper{n}_frame{sx}", (0.13, 0.01, 0.095), m_f, mk, (sx * 0.075, -0.228, 0.03), c)
            L.box(f"helper{n}_bridge", (0.05, 0.012, 0.015), m_f, mk, (0, -0.235, 0.05), c)
            L.box(f"helper{n}_strap", (0.46, 0.4, 0.03), m_f, mk, (0, -0.02, 0.03), c, bevel=0.01)
        elif mark == "digits":   # kreisende Ziffern
            self.orbit = L.empty(f"helper{n}_orbit", self.body, (0, 0, 0.02), c)
            mdig = L.mat("digit", L.YELLOW, 0.4, emit=L.YELLOW, strength=3.0)
            for i, d in enumerate("2+5×0="[:4]):
                a = 2 * math.pi * i / 4
                piv = L.empty(f"helper{n}_dpiv{i}", self.orbit, (0.36 * math.cos(a), 0.36 * math.sin(a), 0), c)
                L.text(f"helper{n}_digit{i}", "0123"[i] if False else ["2", "5", "×", "0"][i], 0.15, mdig, piv,
                       (0, 0, 0), c, extrude=0.01, font=L.font())
        elif mark == "feather":  # kleine Feder
            fp = L.empty(f"helper{n}_featherpiv", self.body, (-0.16, 0.0, 0.17), c)
            fp.rotation_euler = (0, -0.5, 0)
            L.sphere(f"helper{n}_vane", 1.0, 10, 6, (0.045, 0.012, 0.17), L.mat("feather", L.FLOUR, 0.6), fp,
                     (0, 0, 0.14), c)
            L.cyl(f"helper{n}_quill", 0.008, 0.32, 5, L.mat("quill", L.GOLD, 0.5), fp, (0, -0.005, 0.12), c)
            self.feather = fp


def trail(T, coll, name, pos_fn, f0, f1, n=7, size=0.07, color=None, lag=1.5, strength=6.0):
    """Lichtspur: Kette kleiner Leuchtkugeln, die der Bahn verzoegert folgen und schrumpfen."""
    m = L.mat(f"trail_{color or L.TURQ}", color or L.TURQ, 0.5, emit=color or L.TURQ, strength=strength)
    objs = []
    for k in range(1, n + 1):
        o = L.ico(f"{name}_tr{k}", size * (1 - (k - 1) / (n + 1)), 1, (1, 1, 1), m, None, (0, 0, 0), coll)
        T.set(o, "location", lambda f, k=k: tuple(pos_fn(f - k * lag)), f0 - 1, f1 + 1)
        T.set(o, "scale", lambda f, k=k: (window(f, f0 + k, f1, 3, 6),) * 3, f0 - 1, f1 + 1)
        objs.append(o)
    return objs


# =================================================================== Posen
# Rotations-Deltas (rad) pro Gelenk. sh = Schulter, el = Ellbogen, R = Kalles rechte Seite (Bild links).
POSES = {
    "wipe": {"sh_R": (-0.80, 0.10, 0.25), "el_R": (-0.75, 0, 0), "hips": (-0.06, 0, 0), "head": (0.12, 0, 0)},
    "hands_up": {"sh_R": (-0.45, 1.0, 0), "sh_L": (-0.45, -1.0, 0), "el_R": (-1.75, 0, 0.35),
                 "el_L": (-1.75, 0, -0.35), "head": (-0.08, 0, 0)},
    "scratch": {"sh_R": (-2.35, 0.55, 0.3), "el_R": (-1.75, 0, 0), "head": (0.05, 0.12, 0)},
    "point_wind": {"sh_L": (-2.5, -0.35, 0), "el_L": (-0.9, 0, 0), "hips": (0.05, 0, 0)},
    "point_hit": {"sh_L": (-1.2, -0.1, 0), "el_L": (-0.15, 0, 0), "hips": (-0.1, 0, 0), "head": (0.18, 0, 0)},
    "lean": {"hips": (-0.2, 0, 0), "head": (0.08, 0, 0)},
    "glasses": {"sh_R": (-2.1, 0.25, 0.4), "el_R": (-1.9, 0, 0)},
    "arms_rest": {"sh_R": (-0.15, 0.12, 0), "sh_L": (-0.15, -0.12, 0), "el_R": (-0.35, 0, 0), "el_L": (-0.35, 0, 0)},
    "sit": {"hip_R": (-1.5, 0, 0.1), "hip_L": (-1.5, 0, -0.1), "knee_R": (1.45, 0, 0), "knee_L": (1.45, 0, 0),
            "skirt": (-0.85, 0, 0)},
    "desk_hands": {"sh_R": (-0.9, 0.05, 0), "sh_L": (-0.9, -0.05, 0), "el_R": (-0.6, 0, 0), "el_L": (-0.6, 0, 0)},
}


def joint(k, name):
    if name in ("hips", "head", "skirt", "neck", "body", "torso"):
        return {"hips": k.hips, "head": k.head, "skirt": k.skirt, "neck": k.neck, "body": k.body, "torso": k.torso}[name]
    kind, side = name.split("_")
    return {"sh": k.sh, "el": k.el, "hip": k.hip, "knee": k.knee, "hand": k.hand}[kind][side]


def pose(T, k, name, f_in, f_out=None, ramp_in=6, ramp_out=8, weight=1.0, overshoot=0.12, settle=True):
    """Pose als additiver Layer mit Ease-In/Out und Overshoot beim Ankommen."""
    p = POSES[name] if isinstance(name, str) else name
    end = f_out + ramp_out if f_out is not None else 10 ** 6

    def env(f):
        if f < f_in:
            return 0.0
        a = ease_out_back(min(1.0, (f - f_in) / ramp_in), 1.70158 * overshoot / 0.1) if settle else \
            ease_in_out(min(1.0, (f - f_in) / ramp_in))
        if f_out is not None and f > f_out:
            a *= 1 - ease_in_out((f - f_out) / ramp_out)
        return a * weight

    for jn, rot in p.items():
        j = joint(k, jn)
        T.add(j, "rotation_euler", lambda f, rot=rot: (rot[0] * env(f), rot[1] * env(f), rot[2] * env(f)),
              f_in, min(end, f_in + 10 ** 5))
    return env
