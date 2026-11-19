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


class Byte:
    def __init__(self, coll, name="byte", scale=1.0, light_energy=60.0, emissive=1.0):
        self.name = name
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
        L.cyl(f"{name}_screenrim", 0.16, 0.05, 16, m_rim, self.body, (0, -0.185, 0.0), c, axis="Y")
        L.cyl(f"{name}_screen", 0.145, 0.05, 16, m_screen, self.body, (0, -0.195, 0.0), c, axis="Y")
        self.m_pix = L.unique_mat(L.mat("byte_pixel", L.TURQ, 0.5, emit=L.TURQ, strength=5.0), f"{name}_pixmat")
        self.face = L.empty(f"{name}_face", self.body, (0, -0.222, 0.0), c)
        self.expr = {}
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
        # Antenne mit Leuchtpunkt
        self.ant = L.empty(f"{name}_ant", self.body, (0.03, 0, 0.2), c)
        L.cyl(f"{name}_antstalk", 0.011, 0.16, 6, L.mat("antenna", L.METAL, 0.5, metallic=0.4), self.ant,
              (0, 0, 0.08), c)
        self.m_tip = L.unique_mat(L.mat("byte_tip", L.YELLOW, 0.4, emit=L.YELLOW, strength=4.0), f"{name}_tipmat")
        self.tip = L.ico(f"{name}_tip", 0.032, 1, (1, 1, 1), self.m_tip, self.ant, (0, 0, 0.17), c)
        # Glow-Licht (wirft tuerkises Licht auf Kalle)
        self.light = L.light(f"{name}_light", "POINT", light_energy, L.TURQ, (0, -0.25, 0), size=0.25,
                             parent=self.body, coll=c, shadow=False, cutoff=4.0)
        self.extra = L.empty(f"{name}_extra", self.body, (0, 0, 0), c)
        self.ears = []

    def add_ear_rings(self):
        """Ohr-Ringe links/rechts (neuere Folgen)."""
        m = L.mat("byte_earring", L.NAVY2, 0.45, emit=L.TURQ, strength=0.6)
        m2 = L.mat("byte_earglow", L.TURQ, 0.4, emit=L.TURQ, strength=4.0)
        for sx in (-1, 1):
            e = L.torus(f"{self.name}_earring{sx}", 0.075, 0.018, 16, 5, m, self.body, (sx * 0.215, 0, 0.0),
                        self.coll, axis="X")
            L.torus(f"{self.name}_earglow{sx}", 0.05, 0.008, 14, 4, m2, e, (sx * 0.012, 0, 0), self.coll, axis="X")
            self.ears.append(e)


def byte_idle(T, b, f0, f1, seed=3, amp=0.03):
    """Schweben als Sinus (0,8 Hz), Antenne schwingt bei Richtungswechsel nach, Leuchtpunkt pulsiert."""
    ph = random.Random(seed).uniform(0, 6.28)
    T.add(b.bob, "location", lambda f: (0, 0, amp * math.sin(2 * math.pi * 0.8 * f / FPS + ph)), f0, f1)
    T.add(b.bob, "rotation_euler", lambda f: (0.05 * math.sin(2 * math.pi * 0.4 * f / FPS + ph), 0,
                                              0.06 * math.sin(2 * math.pi * 0.27 * f / FPS + ph)), f0, f1)
    tip = L.bsdf(b.m_tip).inputs["Emission Strength"]
    T.set(tip, "default_value", lambda f: 3.0 + 2.0 * (0.5 + 0.5 * math.sin(2 * math.pi * 1.1 * f / FPS + ph)), f0, f1)


def antenna_spring(T, b, f0, f1, gain=7.0):
    """Antenne: gedaempfte Feder, angetrieben von der Beschleunigung der Byte-Bewegung."""
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


def byte_face(T, b, schedule, f0, f1):
    """schedule: [(frame, ausdruck), ...] – Wechsel mit 3-Frame-Pop."""
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
        super().__init__(coll, name=f"helper{n}", scale=0.45, light_energy=25.0, emissive=1.1)
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
