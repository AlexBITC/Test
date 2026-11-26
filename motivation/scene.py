"""Blender-Szene fuer das Motivationsvideo (headless).

  blender -b --factory-startup --python motivation/scene.py -- <timeline.json> <outdir> [frames]
    frames: "all" (Standard) oder Liste "12,240,600"

Alles ist Emission auf fast schwarzem Grund: weisse Neon-Linien, goldene Akzente (#F5C451),
Glow ueber den Bloom-Glare im Compositor. Staub, Bokeh, Texte kommen in der 2D-Nachbearbeitung.
Koordinaten: Kamera blickt entlang +Y, Bildhoehe 16 Einheiten = 1920 px (120 px pro Einheit).
"""
import math
import os
import random
import sys
import json

import bpy
import bmesh
from mathutils import Vector, Matrix, Euler
from mathutils import geometry as mgeo

argv = sys.argv[sys.argv.index("--") + 1:]
TL = json.load(open(argv[0]))
OUTDIR = argv[1]
FRAMES = argv[2] if len(argv) > 2 else "all"
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = TL["fps"]
N = TL["n_frames"]
SAMPLES = int(os.environ.get("CYCLES_SAMPLES", "20"))
SCALE = float(os.environ.get("RENDER_SCALE", "1.0"))

GOLD = (0.913, 0.546, 0.0823)      # #F5C451 linear
WHITE = (1.0, 1.0, 1.0)
PI = math.pi
TAU = 2 * PI


# ------------------------------------------------------------------ Zeit-Helfer
def fr(t):
    return t * FPS


SENT = {s["id"]: s for s in TL["sentences"]}


def S(i):           # Satzanfang (Frame)
    return fr(SENT[i]["start"])


def E(i):           # Satzende (Frame)
    return fr(SENT[i]["end"])


def W(i, word):     # Wortanfang (Frame); word = Index oder Text (erstes Vorkommen, ohne Satzzeichen)
    ws = SENT[i]["words"]
    if isinstance(word, int):
        return fr(ws[word]["start"])
    for w in ws:
        if w["w"].lower().strip(".,?!") == word.lower():
            return fr(w["start"])
    raise KeyError(f"{word!r} nicht in Satz {i}")


def WE(i, word):
    ws = SENT[i]["words"]
    for w in ws:
        if w["w"].lower().strip(".,?!") == word.lower():
            return fr(w["end"])
    raise KeyError(word)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lin(f, a, b):
    if b == a:
        return 1.0 if f >= b else 0.0
    return clamp((f - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def ease_out_back(x, s=1.7):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def win(f, a, b, fade_in=6, fade_out=6):
    """Sichtbarkeit 0..1 fuer Fenster [a, b] mit weichen Raendern."""
    return smooth(lin(f, a - fade_in, a)) * (1 - smooth(lin(f, b, b + fade_out)))


def noise1(x, seed=0):
    """glattes 1D-Rauschen (Summe von Sinus mit Seed), Bereich ca. -1..1"""
    r = random.Random(seed)
    v = 0.0
    for k in range(4):
        fq = r.uniform(0.6, 1.8) * (1.9 ** k)
        ph = r.uniform(0, TAU)
        v += math.sin(x * fq + ph) / (1.6 ** k)
    return v / 1.9


def pnoise(f, period_frames, seed=0, harmonics=(1, 2, 3)):
    """periodisches Rauschen mit Periode N (nahtloser Loop)."""
    r = random.Random(seed)
    v = 0.0
    for h in harmonics:
        v += math.sin(TAU * h * f / period_frames + r.uniform(0, TAU)) / h
    return v / 1.6


# ------------------------------------------------------------------ Bake-Helfer
BAKES = []   # (idblock, data_path, index, values[N], interp)


def anim(idblock, path, fn, index=-1, interp="LINEAR", frames=None):
    """fn(f) -> Wert (Skalar oder Tupel). Wird fuer alle Frames 0..N-1 ausgewertet und gebacken."""
    BAKES.append((idblock, path, index, fn, interp))


def _channelbag(idblock):
    ad = idblock.animation_data
    from bpy_extras import anim_utils
    return anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)


def do_bake():
    interp_id = {"CONSTANT": 0, "LINEAR": 1}
    jobs = []
    for idblock, path, index, fn, interp in BAKES:
        vals = [fn(f) for f in range(N)]
        if isinstance(vals[0], (tuple, list, Vector, Euler)):
            for k in range(len(vals[0])):
                jobs.append((idblock, path, k, [float(v[k]) for v in vals], interp))
        else:
            jobs.append((idblock, path, index, [float(v) for v in vals], interp))
    for idblock, path, index, vals, interp in jobs:
        # nur Lauf-Endpunkte konstanter Abschnitte behalten
        keep = [0]
        for f in range(1, N - 1):
            if not (abs(vals[f] - vals[f - 1]) < 1e-6 and abs(vals[f + 1] - vals[f]) < 1e-6):
                keep.append(f)
        keep.append(N - 1)
        if interp == "CONSTANT":
            keep = [f for f in range(N) if f == 0 or abs(vals[f] - vals[f - 1]) > 1e-9]
        # Owner fuer keyframe_insert finden
        if isinstance(idblock, tuple):          # (node_tree, socket) fuer Material-Eingaenge
            idblock, path = idblock[1], "default_value"
        if not isinstance(idblock, bpy.types.ID):   # Struct in einer ID (Socket, ShapeKey)
            if index < 0:
                idblock.keyframe_insert(path, frame=0)
            else:
                idblock.keyframe_insert(path, index=index, frame=0)
            owner = idblock.id_data
            full = idblock.path_from_id(path)
        else:
            owner = idblock
            if index < 0:
                idblock.keyframe_insert(path, frame=0)
            else:
                idblock.keyframe_insert(path, index=index, frame=0)
            full = path
        cb = _channelbag(owner)
        fc = cb.fcurves.find(full, index=max(index, 0))
        fc.keyframe_points.clear()
        fc.keyframe_points.add(len(keep))
        co = []
        for f in keep:
            co += [float(f), vals[f]]
        fc.keyframe_points.foreach_set("co", co)
        try:
            fc.keyframe_points.foreach_set("interpolation", [interp_id[interp]] * len(keep))
        except Exception:  # noqa: BLE001
            for kp in fc.keyframe_points:
                kp.interpolation = interp
        fc.update()


# ------------------------------------------------------------------ Szene / Render
def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def setup_render(sc):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.03
    sc.cycles.adaptive_min_samples = 4
    sc.cycles.max_bounces = 0
    sc.cycles.use_denoising = False
    sc.cycles.pixel_filter_type = "BLACKMAN_HARRIS"
    sc.cycles.filter_width = 1.6
    sc.render.use_persistent_data = True
    sc.render.resolution_x = 1080
    sc.render.resolution_y = 1920
    sc.render.resolution_percentage = int(round(SCALE * 100))
    sc.render.fps = FPS
    sc.frame_start = 0
    sc.frame_end = N - 1
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "8"
    sc.render.image_settings.compression = 10
    sc.render.use_motion_blur = False
    sc.render.motion_blur_shutter = 0.45
    w = bpy.data.worlds.new("world")
    sc.world = w
    w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    # Bloom
    ng = bpy.data.node_groups.new("comp", "CompositorNodeTree")
    sc.compositing_node_group = ng
    rl = ng.nodes.new("CompositorNodeRLayers")
    g1 = ng.nodes.new("CompositorNodeGlare")
    g1.inputs["Type"].default_value = "Bloom"
    g1.inputs["Quality"].default_value = "High"
    g1.inputs["Threshold"].default_value = 0.35
    g1.inputs["Strength"].default_value = 0.85
    g1.inputs["Size"].default_value = 0.55
    g2 = ng.nodes.new("CompositorNodeGlare")       # enger Kern-Glow
    g2.inputs["Type"].default_value = "Bloom"
    g2.inputs["Quality"].default_value = "High"
    g2.inputs["Threshold"].default_value = 0.6
    g2.inputs["Strength"].default_value = 0.5
    g2.inputs["Size"].default_value = 0.25
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    out = ng.nodes.new("NodeGroupOutput")
    ng.links.new(rl.outputs["Image"], g2.inputs["Image"])
    ng.links.new(g2.outputs["Image"], g1.inputs["Image"])
    ng.links.new(g1.outputs["Image"], out.inputs[0])
    sc.render.use_compositing = True


SC = bpy.context.scene
reset()
setup_render(SC)
COLL = SC.collection


def link(o, parent=None):
    COLL.objects.link(o)
    if parent is not None:
        o.parent = parent
    return o


def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None)
    o.location = loc
    return link(o, parent)


MATS = {}


def emat(name, color=WHITE, strength=3.0):
    """Emissionsmaterial; Rueckgabe Material. Staerke ueber fade(mat, fn) animierbar."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    MATS[name] = (m, em, strength)
    return m


def black_mat():
    m = bpy.data.materials.new("occluder")
    nt = m.node_tree
    nt.nodes.clear()
    ho = nt.nodes.new("ShaderNodeHoldout")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(ho.outputs[0], out.inputs["Surface"])
    return m


def fade(mat, fn):
    """Emissionsstaerke = Grundstaerke * fn(f)."""
    m, em, base = MATS[mat.name]
    sock = em.inputs["Strength"]
    anim((m.node_tree, sock, None), None, lambda f: base * max(0.0, fn(f)))


def hide_when(obj, fn_visible):
    anim(obj, "hide_render", lambda f: 0.0 if fn_visible(f) else 1.0, interp="CONSTANT")


def poly(name, pts, radius, mat, cyclic=False, parent=None, smooth_curve=False):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER" if smooth_curve else "POLY")
    if smooth_curve:
        sp.bezier_points.add(len(pts) - 1)
        for p, c in zip(sp.bezier_points, pts):
            p.co = c
            p.handle_left_type = p.handle_right_type = "AUTO"
        cu.resolution_u = 16
    else:
        sp.points.add(len(pts) - 1)
        for p, c in zip(sp.points, pts):
            p.co = (*c, 1)
    sp.use_cyclic_u = cyclic
    o = bpy.data.objects.new(name, cu)
    o.data.materials.append(mat)
    return link(o, parent)


def circle_pts(r, n=64, cx=0, cz=0, y=0, a0=0.0, a1=TAU):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), y, cz + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def rect_pts(w, h, r=0.18, cx=0, cz=0, y=0, seg=6):
    pts = []
    corners = [(w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, PI / 2), (-w / 2 + r, -h / 2 + r, PI), (w / 2 - r, -h / 2 + r, 1.5 * PI)]
    for (x, z, a) in corners:
        for k in range(seg + 1):
            t = a + (PI / 2) * k / seg
            pts.append((cx + x + r * math.cos(t), y, cz + z + r * math.sin(t)))
    return pts


FONT_ANTON = bpy.data.fonts.load(os.path.join(HERE, "fonts", "Anton-Regular.ttf"))


def text(name, body, size, mat, outline=0.022, parent=None, loc=(0, 0, 0), font=FONT_ANTON, fill=False):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = font
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.fill_mode = "FRONT" if fill else "NONE"
    cu.bevel_depth = 0 if fill else outline
    cu.bevel_resolution = 2
    cu.resolution_u = 6
    o = bpy.data.objects.new(name, cu)
    o.rotation_euler = (PI / 2, 0, 0)        # Textebene XY -> Bildebene XZ
    o.location = loc
    o.data.materials.append(mat)
    return link(o, parent)


def bevel_reveal(obj, fn):
    """Strich wird entlang der Kurve gezeichnet: fn(f) 0..1"""
    anim(obj.data, "bevel_factor_end", lambda f: clamp(fn(f)))


OCC = black_mat()

# ------------------------------------------------------------------ Kamera
CAM_D = 31.0
cd = bpy.data.cameras.new("cam")
cd.sensor_fit = "VERTICAL"
cd.sensor_height = 36
cd.lens = 70
cd.clip_start = 1
cd.clip_end = 200
CAM = link(bpy.data.objects.new("cam", cd))
SC.camera = CAM

# Szenenfenster (Frames)
A0, A1 = 0, S(3) - 3
B0, B1 = S(3) - 4, S(4) - 3
C0, C1 = S(4) - 5, S(5) - 2
D0, D1 = S(5) - 4, S(8) - 6
E0, E1 = S(8) - 10, S(9) - 3
F0, F1 = S(9) - 5, N
NOW = W(10, "now")
LOOP0 = N - 16           # ab hier baut sich der Kalender (Anfangsbild) wieder auf
FLASH_PEAK = N - 10

# ================================================================== FIGUR
class Figure:
    """Abstrakte Neon-Figur ohne Gesicht: Low-Poly-Kopf (Drahtgitter), Glieder als Leuchtroehren,
    goldener Kern in der Brust. Seitenansicht, laeuft nach +X. Ferne Seite gedimmt und dahinter."""

    def __init__(self, name, scale=1.0):
        self.name = name
        self.s = scale
        self.m_near = emat(name + "_near", WHITE, 3.2)
        self.m_far = emat(name + "_far", WHITE, 1.3)
        self.m_core = emat(name + "_core", GOLD, 6.0)
        self.root = empty(name + "_root")
        self.root.scale = (scale, scale, scale)
        L = self.L = {"thigh": 0.52, "shin": 0.5, "torso": 0.72, "neck": 0.12, "upper": 0.38, "fore": 0.36}
        r = 0.055
        self.pelvis = empty(name + "_pelvis", parent=self.root)
        self.torso = self._limb("torso", L["torso"], r * 1.25, self.m_near, self.pelvis, up=True)
        self.neck = empty(name + "_neck", (0, 0, L["torso"]), parent=self.torso)
        self.head = self._head(self.neck)
        core = bpy.data.meshes.new(name + "_coreme")
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.075)
        bm.to_mesh(core)
        bm.free()
        c = link(bpy.data.objects.new(name + "_core", core), self.torso)
        c.location = (0.03, -0.08, L["torso"] * 0.68)
        c.data.materials.append(self.m_core)
        self.parts = {}
        for side, mat, dy in (("n", self.m_near, -0.07), ("f", self.m_far, 0.09)):
            hip = empty(f"{name}_hip{side}", (0, dy, 0), parent=self.pelvis)
            th = self._limb("thigh" + side, L["thigh"], r, mat, hip)
            knee = empty(f"{name}_knee{side}", (0, 0, -L["thigh"]), parent=th)
            sh = self._limb("shin" + side, L["shin"], r * 0.95, mat, knee)
            sho = empty(f"{name}_sho{side}", (0, dy, L["torso"] * 0.93), parent=self.torso)
            ua = self._limb("upper" + side, L["upper"], r * 0.9, mat, sho)
            elb = empty(f"{name}_elb{side}", (0, 0, -L["upper"]), parent=ua)
            fa = self._limb("fore" + side, L["fore"], r * 0.85, mat, elb)
            self.parts[side] = {"hip": hip, "knee": knee, "sho": sho, "elb": elb, "th": th, "sh": sh}

    def _limb(self, nm, length, r, mat, parent, up=False):
        me = bpy.data.meshes.new(self.name + nm)
        bm = bmesh.new()
        segs = 10
        # Kapsel: Zylinder + Halbkugeln
        bmesh.ops.create_cone(bm, cap_ends=False, segments=segs, radius1=r, radius2=r, depth=length)
        for v in bm.verts:
            v.co.z += length / 2 if up else -length / 2
        for zc in (0.0, length if up else -length):
            ret = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=6, radius=r)
            for v in ret["verts"]:
                v.co.z += zc
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        o = link(bpy.data.objects.new(self.name + "_" + nm, me), parent)
        o.data.materials.append(mat)
        return o

    def _head(self, parent):
        me = bpy.data.meshes.new(self.name + "_head")
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.25)
        bm.to_mesh(me)
        bm.free()
        o = link(bpy.data.objects.new(self.name + "_head", me), parent)
        o.location = (0, 0, 0.27)
        o.scale = (0.92, 0.92, 1.05)
        o.rotation_euler = (0.3, 0.5, 0.2)
        mod = o.modifiers.new("wire", "WIREFRAME")
        mod.thickness = 0.034
        mod.use_even_offset = True
        mod.use_relative_offset = False
        o.data.materials.append(self.m_near)
        # dunkler Kern, damit die Rueckseite des Gitters ruhiger wirkt
        inner = link(bpy.data.objects.new(self.name + "_headocc", me.copy()), o)
        inner.scale = (0.86, 0.86, 0.86)
        inner.data.materials.clear()
        inner.data.materials.append(OCC)
        return o

    # Pose: dict mit Winkeln in Grad. Positive Winkel = nach vorn (+X).
    def pose_fk(self, P):
        """Vorwaertskinematik in 2D (x vorwaerts, z hoch) fuer Fussposition relativ zum Becken."""
        L = self.L
        res = {}
        for side in ("n", "f"):
            a_th = math.radians(P["hip_" + side])
            a_sh = a_th - math.radians(P["knee_" + side])
            kx, kz = math.sin(a_th) * L["thigh"], -math.cos(a_th) * L["thigh"]
            fx, fz = kx + math.sin(a_sh) * L["shin"], kz - math.cos(a_sh) * L["shin"]
            res[side] = (fx, fz)
        return res

    def bake(self, pose_fn, root_fn, vis_fn):
        """pose_fn(f) -> Posen-Dict; root_fn(f, feet) -> (x, z, lean_deg); vis_fn(f) -> 0..1"""
        poses = [pose_fn(f) for f in range(N)]
        roots = [root_fn(f, self.pose_fk(poses[f]), poses[f]) for f in range(N)]
        s = self.s
        anim(self.root, "location", lambda f: (roots[f][0], 0.0, roots[f][1]))
        anim(self.torso, "rotation_euler", lambda f: (0.0, math.radians(poses[f].get("spine", 0) + roots[f][2]), 0.0))
        anim(self.neck, "rotation_euler", lambda f: (0.0, math.radians(poses[f].get("head", 0)), 0.0))
        for side in ("n", "f"):
            p = self.parts[side]
            anim(p["hip"], "rotation_euler", lambda f, sd=side: (0.0, -math.radians(poses[f]["hip_" + sd]), 0.0))
            anim(p["knee"], "rotation_euler", lambda f, sd=side: (0.0, math.radians(poses[f]["knee_" + sd]), 0.0))
            anim(p["sho"], "rotation_euler", lambda f, sd=side: (0.0, -math.radians(poses[f]["sho_" + sd]), 0.0))
            anim(p["elb"], "rotation_euler", lambda f, sd=side: (0.0, -math.radians(poses[f]["elb_" + sd]), 0.0))
        for m in (self.m_near, self.m_far, self.m_core):
            fade(m, vis_fn)
        vis = [vis_fn(f) > 0.002 for f in range(N)]
        for o in [self.root] + list(self.root.children_recursive):
            if o.type != "EMPTY":
                anim(o, "hide_render", lambda f: 0.0 if vis[f] else 1.0, interp="CONSTANT")


def pose_stand(f, seed=0, look_up=0.0):
    br = math.sin(TAU * f / 95 + seed)       # Atmen
    return {"hip_n": 2, "knee_n": 4, "hip_f": -3, "knee_f": 3,
            "sho_n": -6 + 2 * br, "elb_n": 12, "sho_f": 5 - 2 * br, "elb_f": 10,
            "spine": 1.5 * br - 4 * look_up, "head": -22 * look_up + 1.5 * br}


def pose_walk(ph, amp=1.0):
    """ph: Phase in Zyklen. amp skaliert die Schrittweite."""
    p = TAU * ph
    P = {}
    for side, off in (("n", 0.0), ("f", PI)):
        q = p + off
        P["hip_" + side] = amp * (24 * math.sin(q) + 4)
        P["knee_" + side] = 6 + amp * 40 * max(0.0, math.cos(q + 0.25)) ** 1.5   # Knie beugt beim Vorschwingen
        P["sho_" + side] = -amp * 26 * math.sin(q) + 2
        P["elb_" + side] = 22 + amp * 10 * max(0.0, -math.sin(q))
    P["spine"] = 5 * amp
    P["head"] = 2
    return P


def pose_run(ph):
    p = TAU * ph
    P = {}
    for side, off in (("n", 0.0), ("f", PI)):
        q = p + off
        P["hip_" + side] = 42 * math.sin(q) + 10
        P["knee_" + side] = 18 + 95 * max(0.0, math.cos(q + 0.35)) ** 1.2
        P["sho_" + side] = -55 * math.sin(q) + 5
        P["elb_" + side] = 85
    P["spine"] = 13
    P["head"] = -6
    return P


def mix_pose(a, b, t):
    return {k: a[k] * (1 - t) + b[k] * t for k in a}


def foot_locked_root(poses, feet_fn, x0, ground, start, figure):
    """Becken-x so integrieren, dass der Standfuss nicht rutscht; z so, dass der tiefste Fuss den
    Boden beruehrt. Rueckgabe Listen x[f], z[f]."""
    xs, zs = [x0] * N, [ground] * N
    prev = None
    x = x0
    for f in range(N):
        feet = figure.pose_fk(poses[f])
        stance = "n" if feet["n"][1] < feet["f"][1] else "f"
        if prev is not None and f > start:
            pf = prev[stance]
            x -= (feet[stance][0] - pf[0]) * figure.s
        xs[f] = x
        zs[f] = ground - min(feet["n"][1], feet["f"][1]) * figure.s
        prev = feet
    return xs, zs


# ================================================================== SZENE A: Kalender
GROUND = -2.65
cal_white = emat("cal_white", WHITE, 3.0)
cal_gold = emat("cal_gold", GOLD, 4.5)
cal_vis = lambda f: max(win(f, A0, A1, 0, 8), smooth(lin(f, LOOP0, FLASH_PEAK + 4)))
fade(cal_white, cal_vis)
fade(cal_gold, cal_vis)
cal = empty("calendar", (0, 0, 0.55))
CW, CH = 4.7, 5.3
poly("cal_body", rect_pts(CW, CH, 0.25), 0.03, cal_white, cyclic=True, parent=cal)
poly("cal_band", [(-CW / 2, -0.02, CH / 2 - 1.05), (CW / 2, -0.02, CH / 2 - 1.05)], 0.025, cal_white, parent=cal)
for xr in (-1.3, 1.3):
    ring = poly("cal_ring", circle_pts(0.2, 32, xr, CH / 2 + 0.02, -0.05), 0.04, cal_gold, cyclic=True, parent=cal)
mon = text("cal_month", "DAY", 1.0, cal_white, 0.018, parent=cal, loc=(0, -0.03, CH / 2 - 0.55))
bpy.context.view_layer.update()
mon.data.size = 1.0 * 0.6 / max(0.01, mon.dimensions.y)
# Seiten: oberste zuerst; jede Seite hat eine schwarze Rueckwand, damit darunterliegende verdeckt sind
PAGE_NUMS = [1, 2, 3, 5, 8, 13, 21, 45, 90, 150, 220, 300, 365]
pages = []
flip_a = W(2, "that") - 2
flip_b = WE(2, "ago") - 4
for k, num in enumerate(PAGE_NUMS):
    y = -0.1 - 0.06 * (len(PAGE_NUMS) - k)      # oberste Seite am weitesten vorn
    m = emat(f"page{k}", WHITE, 3.0)
    hinge = empty(f"page{k}_hinge", (0, y, CH / 2 - 1.1), parent=cal)
    pw, ph_ = CW - 0.35, CH - 1.35
    me = bpy.data.meshes.new(f"page{k}_occ")
    me.from_pydata([(-pw / 2, 0.004, 0), (pw / 2, 0.004, 0), (pw / 2, 0.004, -ph_), (-pw / 2, 0.004, -ph_)], [], [(0, 1, 2, 3)])
    occ = link(bpy.data.objects.new(f"page{k}_occ", me), hinge)
    occ.data.materials.append(OCC)
    poly(f"page{k}_edge", rect_pts(pw, ph_, 0.12, 0, -ph_ / 2), 0.02, m, cyclic=True, parent=hinge)
    t = text(f"page{k}_num", str(num), 2.0, m, 0.032, parent=hinge, loc=(0, -0.014, -ph_ / 2 - 0.05))
    bpy.context.view_layer.update()
    t.data.size = 2.0 * min(2.5 / max(0.01, t.dimensions.y), 3.7 / max(0.01, t.dimensions.x))
    for o in (t, occ, hinge.children[1]):
        o.cycles.use_motion_blur = False
    pages.append((hinge, m, num))
# Blaetterzeiten: erst langsam, dann schneller (ease-in), letzte Seite (365) bleibt
n_fly = len(PAGE_NUMS) - 1
fly_t = [flip_a + (flip_b - flip_a) * (1 - (1 - (i / (n_fly - 1))) ** 1.6) for i in range(n_fly)]
for k, (hinge, m, num) in enumerate(pages):
    r = random.Random(k)
    if k < n_fly:
        t0 = fly_t[k]
        dur = 13
        sx, sz = r.uniform(-1, 1), r.uniform(0.6, 1.2)
        spin = r.uniform(-1, 1)

        def loc_fn(f, t0=t0, hinge=hinge, sx=sx, sz=sz):
            u = (f - t0) / dur
            if f < t0 or f > LOOP0 - 1:
                return (0, HINGE_Y[hinge.name], CH / 2 - 1.1)
            u = clamp(u, 0, 3)
            return (sx * 3.2 * u ** 1.4, HINGE_Y[hinge.name] - 4.0 * u, CH / 2 - 1.1 + sz * 2.6 * u ** 1.2)

        def rot_fn(f, t0=t0, spin=spin):
            if f < t0 or f > LOOP0 - 1:
                return (0, 0, 0)
            u = clamp((f - t0) / dur, 0, 3)
            return (-2.2 * ease_out(u) - 0.6 * u, spin * 1.2 * u, spin * 0.8 * u)

        fade(m, lambda f, t0=t0: cal_vis(f) * (1.0 if (f < t0 + 2 or f > LOOP0 - 1) else max(0.0, 1 - (f - t0 - 2) / 10)))
        pages[k] = (hinge, m, num, loc_fn, rot_fn)
    else:
        fade(m, cal_vis)
        pages[k] = (hinge, m, num, None, None)
HINGE_Y = {p[0].name: p[0].location.y for p in pages}
for hinge, m, num, lf, rf in pages:
    if lf:
        anim(hinge, "location", lf)
        anim(hinge, "rotation_euler", rf)
# Gold-Kreis um die "1" bei "start" (Satz 1)
circ = poly("cal_circle", [(math.cos(a) * 1.45, -1.05, 0.75 * math.sin(a) * 1.45 - 0.22 - 0.1) for a in
                           [PI * 0.6 + TAU * 1.08 * i / 80 for i in range(81)]], 0.035, cal_gold, parent=cal)
c_t0, c_t1 = W(1, "start") - 2, W(1, "tomorrow") + 6
bevel_reveal(circ, lambda f: 0.0 if f >= LOOP0 else smooth(lin(f, c_t0, c_t1)))
anim(circ, "hide_render", lambda f: 0.0 if (c_t0 - 1 <= f < fly_t[0] + 2) else 1.0, interp="CONSTANT")
# Kalender: leichtes Schweben, kleiner Ruck bei jedem Blatt
anim(cal, "rotation_euler", lambda f: (0.05 * pnoise(f, N, 3), 0.03 * pnoise(f, N, 4), 0.12 * pnoise(f, N, 5)))
anim(cal, "location", lambda f: (0, 0, 0.55 + 0.06 * pnoise(f, N, 6)))
cal_objs = [cal] + list(cal.children_recursive)
for o in cal_objs:
    if o.type != "EMPTY" and o is not circ:
        hide_when(o, lambda f: cal_vis(f) > 0.002)

# ================================================================== SZENE B: TOMORROW zerbricht
tm_white = emat("tm_white", WHITE, 3.4)
tm_gold = emat("tm_gold", GOLD, 6.0)
crack_t0, crack_t1 = W(3, "dangerous") - 2, WE(3, "dangerous") + 2
shatter = W(3, "know") + 2
tm_in = S(3) - 2
tm_vis = lambda f: smooth(lin(f, tm_in, tm_in + 7))
word = text("tomorrow_src", "TOMORROW", 2.0, tm_white, 0.03, loc=(0, 0, 0.6))
bpy.context.view_layer.update()
word.data.size = 2.0 * 7.4 / max(0.1, word.dimensions.x)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
src_me = bpy.data.meshes.new_from_object(word.evaluated_get(dg))
src_me.transform(word.matrix_world)
bb = [v.co for v in src_me.vertices]
xmin, xmax = min(v.x for v in bb), max(v.x for v in bb)
zmin, zmax = min(v.z for v in bb), max(v.z for v in bb)
bpy.data.objects.remove(word)
# Zellen: 8 Buchstaben (gleich breit genug fuer Anton), Schnitt pro Zelle mit schraeger Ebene
rng = random.Random(7)
ncell = 8
edges_x = [xmin + (xmax - xmin) * i / ncell for i in range(ncell + 1)]
zc = (zmin + zmax) / 2
cuts = []
for i in range(ncell):
    a = rng.uniform(-0.55, 0.55)
    z0 = zc + rng.uniform(-0.35, 0.35)
    cuts.append((a, z0))
pieces = []
for i in range(ncell):
    for half in (0, 1):
        bm = bmesh.new()
        bm.from_mesh(src_me)
        gx = lambda: bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=gx(), plane_co=(edges_x[i], 0, 0), plane_no=(1, 0, 0), clear_inner=True)
        bmesh.ops.bisect_plane(bm, geom=gx(), plane_co=(edges_x[i + 1], 0, 0), plane_no=(1, 0, 0), clear_outer=True)
        a, z0 = cuts[i]
        cx = (edges_x[i] + edges_x[i + 1]) / 2
        nrm = Vector((-math.sin(a), 0, math.cos(a)))
        if half == 0:
            bmesh.ops.bisect_plane(bm, geom=gx(), plane_co=(cx, 0, z0), plane_no=nrm, clear_inner=True)
        else:
            bmesh.ops.bisect_plane(bm, geom=gx(), plane_co=(cx, 0, z0), plane_no=nrm, clear_outer=True)
        if not bm.verts:
            bm.free()
            continue
        cen = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
        for v in bm.verts:
            v.co -= cen
        me = bpy.data.meshes.new(f"tm_piece{i}_{half}")
        bm.to_mesh(me)
        bm.free()
        o = link(bpy.data.objects.new(me.name, me))
        o.location = cen
        o.data.materials.append(tm_white)
        pieces.append((o, cen.copy(), i, half))
# Risslinien (exakt die Schnitte), gold, werden bei "dangerous" gezeichnet
crack_pts = []
for i in range(ncell):
    a, z0 = cuts[i]
    cx = (edges_x[i] + edges_x[i + 1]) / 2
    for x in (edges_x[i], edges_x[i + 1]):
        crack_pts.append((x, -0.08, z0 + math.tan(a) * (x - cx)))
crack = poly("tm_crack", crack_pts, 0.028, tm_gold)
bevel_reveal(crack, lambda f: ease_out(lin(f, crack_t0, crack_t1)))
fade(tm_gold, lambda f: (f >= crack_t0) * (1 - smooth(lin(f, shatter, shatter + 8))) * (1 + 0.5 * math.sin(f * 1.7)))
hide_when(crack, lambda f: crack_t0 - 1 <= f <= shatter + 9)
for o, cen, i, half in pieces:
    r = random.Random(100 + i * 2 + half)
    dirv = Vector((cen.x * 0.55 + r.uniform(-0.6, 0.6), -r.uniform(2.0, 6.0), (cen.z - 0.6) * 1.5 + (0.9 if half == 0 else -0.6) + r.uniform(-0.4, 0.4)))
    rot = Vector((r.uniform(-5, 5), r.uniform(-5, 5), r.uniform(-5, 5)))
    jit = r.uniform(0, 2.5)

    def lf(f, cen=cen, dirv=dirv, jit=jit, i=i):
        shake = 0.0
        if crack_t0 <= f < shatter:
            shake = 0.025 * math.sin(f * 2.9 + i)
        pre = 0.0
        if tm_in <= f < tm_in + 8:     # Aufpoppen
            pre = (1 - ease_out_back(lin(f, tm_in, tm_in + 8))) * -0.0
        if f < shatter + jit:
            return (cen.x + shake, cen.y, cen.z + shake * 0.6)
        u = (f - shatter - jit) / FPS
        return (cen.x + dirv.x * u, cen.y + dirv.y * u, cen.z + dirv.z * u - 2.5 * u * u)

    def rf(f, rot=rot, jit=jit):
        if f < shatter + jit:
            return (0, 0, 0)
        u = (f - shatter - jit) / FPS
        return (rot.x * u, rot.y * u, rot.z * u)

    def sf(f):
        k = ease_out_back(lin(f, tm_in, tm_in + 9), 2.2)
        return (k, k, k)
    anim(o, "location", lf)
    anim(o, "rotation_euler", rf)
    anim(o, "scale", sf)
    hide_when(o, lambda f: tm_in - 1 <= f <= shatter + 26)
fade_tm_pieces = lambda f: tm_vis(f) * (1 - smooth(lin(f, shatter + 6, shatter + 24)))
fade(tm_white, lambda f: fade_tm_pieces(f) * (1 + 0.4 * (crack_t0 <= f <= crack_t1 and (int(f) % 4 < 2))))
# Funken beim Zerbrechen
spark_m = emat("tm_spark", GOLD, 8.0)
fade(spark_m, lambda f: 1 - smooth(lin(f, shatter, shatter + 22)))
sp_me = bpy.data.meshes.new("spark")
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.045)
bm.to_mesh(sp_me)
bm.free()
for k in range(36):
    r = random.Random(500 + k)
    o = link(bpy.data.objects.new(f"tm_spark{k}", sp_me))
    if not o.data.materials:
        o.data.materials.append(spark_m)
    st = Vector((r.uniform(xmin, xmax), -0.1, zc + r.uniform(-0.5, 0.5)))
    v = Vector((r.uniform(-1, 1) * 4, -r.uniform(1, 5), r.uniform(-0.5, 1.5) * 3.5))
    anim(o, "location", lambda f, st=st, v=v: tuple(st + v * max(0, (f - shatter) / FPS) * (1 - 0.35 * max(0, (f - shatter) / FPS)) + Vector((0, 0, -1.8 * max(0, (f - shatter) / FPS) ** 2))))
    hide_when(o, lambda f: shatter <= f <= shatter + 22)

# ================================================================== SZENE C/D: Berg, Figur, Weg
mt_white = emat("mt_white", WHITE, 2.4)
mt_gold = emat("mt_gold", GOLD, 5.0)
mt_vis = lambda f: win(f, C0, D1, 8, 10) * (1.0 - 0.6 * smooth(lin(f, D0, D0 + 20)))
fade(mt_white, mt_vis)
fade(mt_gold, lambda f: win(f, C0, D1, 8, 10))


def build_mountain():
    rng = random.Random(21)
    w = 7.6
    ridge = [(-w / 2, 0.0), (-2.9, 0.9), (-2.2, 1.6), (-1.5, 2.1), (-0.9, 3.3), (-0.4, 4.1), (0.15, 5.0),
             (0.6, 4.3), (1.1, 3.6), (1.6, 3.9), (2.2, 2.6), (2.9, 1.5), (w / 2, 0.0)]
    pts = [Vector((x, z, 0)) for x, z in ridge]
    # Innenpunkte
    inner = []
    for _ in range(26):
        for _try in range(50):
            x = rng.uniform(-w / 2 + 0.3, w / 2 - 0.3)
            z = rng.uniform(0.2, 4.6)
            # unter der Kammlinie?
            for (x0, z0), (x1, z1) in zip(ridge, ridge[1:]):
                if x0 <= x <= x1:
                    zr = z0 + (z1 - z0) * (x - x0) / (x1 - x0)
                    break
            if z < zr - 0.35 and all((Vector((x, z, 0)) - q).length > 0.7 for q in inner):
                inner.append(Vector((x, z, 0)))
                break
    base = [Vector((x, 0, 0)) for x in (-2.4, -1.2, 0.0, 1.2, 2.4)]
    verts = pts + inner + base
    edges = [(i, i + 1) for i in range(len(pts) - 1)] + [(len(pts) - 1, 0)]
    out = mgeo.delaunay_2d_cdt([v.to_2d() for v in verts], edges, [], 0, 1e-5)
    vco, _, faces = out[0], out[1], out[2]
    # 2D (x, hoehe) -> 3D (x, tiefe, z); Tiefe waechst zur Mitte (Bergkoerper)
    v3 = []
    for v in vco:
        x, z = v.x, v.y
        depth = -0.0 if (z < 0.05) else -min(1.6, 0.45 * z + 0.3) * (1 - abs(x) / (w / 2 + 0.2)) * rng.uniform(0.7, 1.2)
        v3.append((x, depth, z))
    # nur Dreiecke innerhalb der Kammlinie (CDT liefert konvexe Huelle)
    def inside(cx, cz):
        for (x0, z0), (x1, z1) in zip(ridge, ridge[1:]):
            if x0 <= cx <= x1:
                return cz <= z0 + (z1 - z0) * (cx - x0) / (x1 - x0) + 1e-4
        return False
    fs = [f for f in faces if inside(sum(vco[i].x for i in f) / 3, sum(vco[i].y for i in f) / 3)]
    me = bpy.data.meshes.new("mountain")
    me.from_pydata(v3, [], fs)
    me.update()
    o = link(bpy.data.objects.new("mountain", me))
    mod = o.modifiers.new("wire", "WIREFRAME")
    mod.thickness = 0.04
    mod.use_even_offset = True
    mod.use_relative_offset = False
    mod.use_replace = True
    o.data.materials.append(mt_white)
    # Schluessel: klein (Basis) -> gross (Shape Key)
    o.shape_key_add(name="small")
    big = o.shape_key_add(name="big")
    for i, v in enumerate(me.vertices):
        x, y, z = v.co
        o.data.shape_keys.key_blocks["small"].data[i].co = (x * 0.75, y * 0.5, z * 0.34)
        big.data[i].co = (x * 1.08, y, z * 1.0)
    o.data.shape_keys.key_blocks["small"].relative_key = o.data.shape_keys.key_blocks["small"]
    # Basis-Form auf "small" setzen
    for i, v in enumerate(me.vertices):
        v.co = o.data.shape_keys.key_blocks["small"].data[i].co
    big.relative_key = o.data.shape_keys.key_blocks["small"]
    # dunkle Flaechen als Verdecker (Rueckseite des Gitters)
    occ = link(bpy.data.objects.new("mountain_occ", me), o)
    occ.location = (0, 0.25, 0)
    occ.material_slots[0].link = "OBJECT"
    occ.material_slots[0].material = OCC
    peak = ridge[6]
    return o, big, peak, ridge


mount, mbig, mpeak, mridge = build_mountain()
MX0 = 1.0


def mount_x(f):
    """Berg bleibt im Bildausschnitt (folgt der Kamera) und weicht ab 'never' nach rechts aus,
    damit die Figur davor frei steht."""
    off = MX0 + 2.7 * smooth(lin(f, W(5, "never"), WE(5, "think") + 8))
    return CAMX[f] + off


anim(mount, "location", lambda f: (mount_x(f), 2.5, GROUND))
# Wachstum: 0 (klein) -> 1 (gross); Stufen bei "day", "wait", grosser Ruck bei "taller"; ab Satz 5 schrumpft er
g_steps = [(W(4, "every"), 0.18), (W(4, "day"), 0.36), (W(4, "wait"), 0.55), (W(4, "mountain"), 0.7), (W(4, "taller"), 1.0)]


def m_grow(f):
    v = 0.0
    prev = 0.0
    for t, val in g_steps:
        v = max(v, prev + (val - prev) * ease_out_back(lin(f, t, t + 10), 1.4))
        prev = val
    shrink = smooth(lin(f, W(5, "never"), WE(5, "think") + 6))
    return v * (1 - 0.55 * shrink)


anim(mbig, "value", m_grow)
hide_when(mount, lambda f: mt_vis(f) > 0.002)
hide_when(mount.children[0], lambda f: mt_vis(f) > 0.002)
# Gipfel-Glanz (gold) als kleiner Stern, waechst mit
peak_star = empty("peak_star")
for k in range(4):
    a = k * PI / 4
    poly(f"peak_ray{k}", [(-0.28 * math.cos(a), -0.3, -0.28 * math.sin(a)), (0.28 * math.cos(a), -0.3, 0.28 * math.sin(a))], 0.022, mt_gold, parent=peak_star)


def peak_loc(f):
    g = m_grow(f)
    sx = 0.75 + (1.08 - 0.75) * g
    sz = 0.34 + 0.66 * g
    mx = mount_x(f)
    return (mx + mpeak[0] * sx, 1.2, GROUND + mpeak[1] * sz + 0.15)


anim(peak_star, "location", peak_loc)
anim(peak_star, "rotation_euler", lambda f: (0, f * 0.02, 0))
anim(peak_star, "scale", lambda f: (lambda s: (s, s, s))(0.6 + 0.6 * m_grow(f) + 0.15 * math.sin(f * 0.3)))
for o in peak_star.children:
    hide_when(o, lambda f: mt_vis(f) > 0.002)
# Boden-Linie
ground_m = emat("ground", WHITE, 1.2)
fade(ground_m, lambda f: win(f, C0, D1, 8, 10))
gl = poly("ground_line", [(-8, 0.3, GROUND), (30, 0.3, GROUND)], 0.016, ground_m)
hide_when(gl, lambda f: C0 - 9 <= f <= D1 + 11)

# Weg aus Segmenten, leuchten gold, wenn die Figur darauf tritt
path_dim = emat("path_dim", WHITE, 0.9)
fade(path_dim, lambda f: win(f, C0 + 6, D1, 10, 10))
fig = Figure("hero", 1.0)
FIG_X0 = -2.75
step1 = W(5, "step") - 8
# Ablauf der Figur in C/D: Stehen (schaut zum Berg hoch) -> erster Schritt -> Gehen (stolpern bei badly,
# zittern bei scared) -> entschlossen bei "today"
walk_start = step1
badly0, badly1 = W(7, "badly") - 3, WE(7, "badly") + 6
scared0, scared1 = W(7, "scared") - 3, WE(7, "scared") + 8
just0 = W(7, "just") - 2
cad = 0.95 / FPS          # Schrittzyklen pro Frame (Gehen)


def hero_phase():
    ph, acc = [0.0] * N, 0.0
    for f in range(N):
        if f > walk_start:
            k = 1.0
            if badly0 <= f <= badly1:
                k = 0.7
            if scared0 <= f <= scared1:
                k = 0.55
            if f >= just0:
                k = 1.25
            if f < walk_start + 10:
                k *= lin(f, walk_start, walk_start + 10) + 0.05
            acc += cad * k
        ph[f] = acc
    return ph


HPH = hero_phase()


def hero_pose(f):
    look = smooth(lin(f, W(4, "every"), W(4, "every") + 15)) * (1 - smooth(lin(f, walk_start - 10, walk_start)))
    st = pose_stand(f, 0.0, look)
    if f <= walk_start:
        return st
    amp = 0.55 + 0.45 * smooth(lin(f, walk_start, walk_start + 18))
    if f >= just0:
        amp = 1.0 + 0.2 * smooth(lin(f, just0, just0 + 10))
    w = pose_walk(HPH[f] + 0.0, amp)
    P = mix_pose(st, w, smooth(lin(f, walk_start, walk_start + 8)))
    if badly0 <= f <= badly1:          # Stolpern: Arme rudern, Oberkoerper kippt
        u = lin(f, badly0, badly1)
        k = math.sin(PI * u)
        P["spine"] += 24 * k
        P["sho_n"] += 70 * k * math.sin(f * 0.9)
        P["sho_f"] += 60 * k * math.sin(f * 0.9 + 2)
        P["elb_n"] += 30 * k
        P["head"] += 15 * k
    if scared0 <= f <= scared1:        # Zittern, geduckt
        u = lin(f, scared0, scared1)
        k = math.sin(PI * u)
        P["spine"] -= 8 * k
        P["head"] += 14 * k
        for j in ("sho_n", "sho_f"):
            P[j] = P[j] * (1 - k) + (25 + 6 * math.sin(f * 3.1)) * k
        for j in ("elb_n", "elb_f"):
            P[j] += 60 * k
        P["knee_n"] += 12 * k
        P["knee_f"] += 12 * k
    return P


poses_h = [hero_pose(f) for f in range(N)]
hx, hz = foot_locked_root(poses_h, None, FIG_X0, GROUND, walk_start, fig)


def hero_root(f, feet, P):
    trem = 0.0
    if scared0 <= f <= scared1:
        trem = 0.02 * math.sin(f * 3.7) * math.sin(PI * lin(f, scared0, scared1))
    lean = 0.0
    if f > walk_start:
        lean = 4 + (6 if f >= just0 else 0) * smooth(lin(f, just0, just0 + 10))
    return (hx[f] + trem, hz[f], lean)


hero_vis = lambda f: win(f, C0 + 4, D1, 10, 10)
fig.bake(lambda f: poses_h[f], hero_root, hero_vis)

# Wegsegmente: ab Figur-Start nach rechts; leuchten gold, sobald die Figur sie erreicht
seg_n = 34
seg_len = 0.42
seg_gap = 0.2
segs = []
for k in range(seg_n):
    x0 = FIG_X0 + 0.25 + k * (seg_len + seg_gap)
    m = emat(f"seg{k}", GOLD, 6.0)
    o_dim = poly(f"seg{k}_dim", [(x0, -0.6, GROUND - 0.02), (x0 + seg_len, -0.6, GROUND - 0.02)], 0.03, path_dim)
    o_gold = poly(f"seg{k}_gold", [(x0, -0.62, GROUND - 0.02), (x0 + seg_len, -0.62, GROUND - 0.02)], 0.04, m)
    # wann erreicht die Figur das Segment?
    t_hit = next((f for f in range(N) if hx[f] + 0.25 >= x0 and f > walk_start), N)
    segs.append((x0, t_hit))
    fade(m, lambda f, t=t_hit: (f >= t) * (1.0 + 1.8 * math.exp(-(f - t) / 6.0)) * win(f, C0, D1, 8, 10))
    hide_when(o_gold, lambda f, t=t_hit: t <= f <= D1 + 11)
    hide_when(o_dim, lambda f: C0 - 9 <= f <= D1 + 11)
# Gold-Ring (5 Minuten) um die Figur, gezeichnet von "Five" bis "begin"
ring_m = emat("ring5", GOLD, 4.0)
ring_t0, ring_t1 = W(6, "five") - 2, WE(6, "begin")
fade(ring_m, lambda f: win(f, ring_t0, ring_t1 + 10, 4, 12))
ring = poly("ring5", [(0.0 + 1.5 * math.sin(a), -0.7, 1.5 * math.cos(a)) for a in [TAU * i / 96 for i in range(97)]], 0.03, ring_m)
tick_root = empty("ring5_ticks")
for k in range(12):
    a = TAU * k / 12
    poly(f"tick{k}", [(1.3 * math.sin(a), -0.7, 1.3 * math.cos(a)), (1.42 * math.sin(a), -0.7, 1.42 * math.cos(a))], 0.018, ring_m, parent=tick_root)
bevel_reveal(ring, lambda f: smooth(lin(f, ring_t0, ring_t1)))
for o in [ring] + list(tick_root.children):
    hide_when(o, lambda f: ring_t0 - 1 <= f <= ring_t1 + 23)
ring_c = lambda f: (hx[f] + 0.15, 0, hz[f] + 0.55)
anim(ring, "location", ring_c)
anim(tick_root, "location", ring_c)
anim(tick_root, "rotation_euler", lambda f: (0, 0.03 * f, 0))

# Gold-Puls bei "today"
today = W(7, "today")
burst_m = emat("today_burst", GOLD, 5.0)
fade(burst_m, lambda f: (1 - smooth(lin(f, today, today + 16))) * (f >= today))
bring = poly("today_ring", circle_pts(1.0, 64, 0, 0, -0.7), 0.035, burst_m, cyclic=True)
anim(bring, "location", lambda f: (hx[min(N - 1, int(today))] + 0.2, 0, GROUND + 0.02))
anim(bring, "scale", lambda f: (lambda s: (s, 1, s * 0.3))(0.2 + 3.0 * ease_out(lin(f, today, today + 16))))
hide_when(bring, lambda f: today <= f <= today + 17)

# ================================================================== SZENE E: Sanduhr
hg_white = emat("hg_white", WHITE, 2.4)
hg_gold = emat("hg_gold", GOLD, 4.0)
hg_sand = emat("hg_sand", GOLD, 1.6)
hg_vis = lambda f: win(f, E0, E1, 10, 6)
for m in (hg_white, hg_gold, hg_sand):
    fade(m, hg_vis)
hg = empty("hourglass", (0, 0, 0.75))
H = 1.95


def hg_r(z):
    u = min(1.0, abs(z) / H)
    if u < 0.62:
        return 0.1 + (1.15 - 0.1) * math.sin(PI / 2 * u / 0.62) ** 0.9
    return 1.15 - (1.15 - 0.92) * ((u - 0.62) / 0.38) ** 2


for k in range(10):
    a = TAU * k / 10
    pts = [(hg_r(z) * math.cos(a), hg_r(z) * math.sin(a), z) for z in [-H + 2 * H * i / 60 for i in range(61)]]
    poly(f"hg_mer{k}", pts, 0.018, hg_white, parent=hg)
for z in (-H, -H * 0.62, H * 0.62, H):
    r = hg_r(z)
    poly(f"hg_ring{z:.2f}", [(r * math.cos(a), r * math.sin(a), z) for a in [TAU * i / 64 for i in range(65)]], 0.018, hg_white, parent=hg)
for z in (-H - 0.12, H + 0.12):     # goldene Rahmenplatten
    poly(f"hg_cap{z:.2f}", [(1.35 * math.cos(a), 1.35 * math.sin(a), z) for a in [TAU * i / 64 for i in range(65)]], 0.05, hg_gold, parent=hg)
for k in range(3):
    a = TAU * k / 3 + 0.4
    poly(f"hg_post{k}", [(1.35 * math.cos(a), 1.35 * math.sin(a), -H - 0.12), (1.35 * math.cos(a), 1.35 * math.sin(a), H + 0.12)], 0.035, hg_gold, parent=hg)


def lathe(name, prof, parent):
    """prof: Liste (r, z) von unten nach oben; ergibt geschlossenen Rotationskoerper."""
    bm = bmesh.new()
    seg = 28
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * math.cos(TAU * i / seg), r * math.sin(TAU * i / seg), z)) for i in range(seg)])
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me), parent)
    o.data.materials.append(hg_sand)
    return o


# Sand oben: Trichter vom Hals (Ursprung) bis Fuellhoehe; schrumpft gleichmaessig zum Hals
top_prof = [(0.06, 0.0)] + [(hg_r(z) * 0.93, z) for z in [0.1 + (H * 0.72 - 0.1) * i / 14 for i in range(15)]]
sand_top = lathe("sand_top", top_prof, hg)
sand_top.location = (0, 0, 0.02)
bot_prof = [(hg_r(-H) * 0.93, 0.0), (hg_r(-H) * 0.9, 0.12), (0.75, 0.45), (0.35, 0.75), (0.02, 0.9)]
sand_bot = lathe("sand_bot", bot_prof, hg)
sand_bot.location = (0, 0, -H + 0.02)
sand0, sand1 = S(8) - 6, WE(8, "left") + 1


def sand_u(f):
    return 0.15 + 0.85 * lin(f, sand0, sand1)


anim(sand_top, "scale", lambda f: (lambda s: (s, s, s))(max(0.001, (1 - sand_u(f)) ** 0.5)))
anim(sand_bot, "scale", lambda f: (lambda s: (max(0.35, s), max(0.35, s), max(0.001, s)))(0.25 + 0.75 * sand_u(f) ** 0.6))
stream = poly("sand_stream", [(0, 0, 0.0), (0, 0, -H + 0.1)], 0.022, hg_sand, parent=hg)
anim(stream, "scale", lambda f: (1, 1, 1 - 0.45 * sand_u(f)))
hide_when(stream, lambda f: E0 - 10 <= f < sand1)
# Koerner im Strahl
for k in range(10):
    o = link(bpy.data.objects.new(f"grain{k}", sp_me), hg)
    o.scale = (0.7, 0.7, 0.7)
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = hg_sand
    off = k / 10

    def gl_(f, off=off, k=k):
        u = ((f / 14.0) + off) % 1.0
        return (0.02 * math.sin(k * 7 + f), 0.0, -0.05 - u * (H - 0.3 - 0.8 * sand_u(f)))
    anim(o, "location", gl_)
    hide_when(o, lambda f: E0 - 10 <= f < sand1 - 3)
# letztes Korn faellt bei "left"
last = link(bpy.data.objects.new("grain_last", sp_me), hg)
last.material_slots[0].link = "OBJECT"
last.material_slots[0].material = hg_sand
anim(last, "location", lambda f: (0, 0, -0.05 - 1.15 * ease_in(lin(f, sand1 - 3, sand1 + 12))))
hide_when(last, lambda f: sand1 - 3 <= f <= sand1 + 12)
anim(hg, "rotation_euler", lambda f: (0.18, 0.0, 0.35 * math.sin(TAU * (f - E0) / 260) + 0.25))
anim(hg, "location", lambda f: (0, 0, 0.75 + 0.05 * math.sin(f * 0.05)))
for o in hg.children_recursive:
    if o.type != "EMPTY" and not o.name.startswith("grain"):
        hide_when(o, lambda f: E0 - 11 <= f <= E1 + 7)

# ================================================================== SZENE F: Laufen + Lichtexplosion
run = Figure("runner", 1.25)
RGROUND = -2.4
run_start = W(9, "waiting") - 4
ready0 = W(9, "stop") - 4
rcad = 1.55 / FPS


def run_phase():
    ph, acc = [0.0] * N, 0.0
    for f in range(N):
        if f > run_start:
            acc += rcad * (0.4 + 0.6 * smooth(lin(f, run_start, run_start + 14)))
        ph[f] = acc
    return ph


RPH = run_phase()


def runner_pose(f):
    st = pose_stand(f, 1.0, 0.0)
    crouch = {"hip_n": 30, "knee_n": 70, "hip_f": -15, "knee_f": 40, "sho_n": -40, "elb_n": 70, "sho_f": 35,
              "elb_f": 80, "spine": 25, "head": -10}
    P = mix_pose(st, crouch, smooth(lin(f, ready0, ready0 + 10)))
    if f > run_start:
        P = mix_pose(P, pose_run(RPH[f]), smooth(lin(f, run_start, run_start + 8)))
    if f > NOW - 2:   # in das Licht springen: Arme hoch
        jump = {"hip_n": 35, "knee_n": 50, "hip_f": -25, "knee_f": 30, "sho_n": 165, "elb_n": 10, "sho_f": 150,
                "elb_f": 15, "spine": -5, "head": -18}
        P = mix_pose(P, jump, smooth(lin(f, NOW - 2, NOW + 8)))
    return P


poses_r = [runner_pose(f) for f in range(N)]
rx, rz = foot_locked_root(poses_r, None, -1.2, RGROUND, run_start, run)


def runner_root(f, feet, P):
    lean = 0.0
    if f > ready0:
        lean = 10 * smooth(lin(f, ready0, ready0 + 10))
    if f > run_start:
        lean = 10 + 8 * smooth(lin(f, run_start, run_start + 10))
    if f > NOW - 2:
        lean *= 1 - smooth(lin(f, NOW - 2, NOW + 8))
    z = rz[f]
    if f > NOW - 2:
        z += 0.9 * math.sin(PI * clamp(lin(f, NOW - 2, NOW + 30))) ** 0.8
    return (rx[f], z, lean)


run_vis = lambda f: win(f, F0 + 2, LOOP0, 8, 0) * (1 - 0.85 * smooth(lin(f, NOW + 4, NOW + 30)))
run.bake(lambda f: poses_r[f], runner_root, run_vis)
# Bodenlinie und Tempolinien (laufen mit, Kamera folgt der Figur)
r_ground = emat("r_ground", WHITE, 1.6)
r_gold = emat("r_gold", GOLD, 5.0)
fade(r_ground, lambda f: win(f, F0, NOW + 10, 8, 14))
fade(r_gold, lambda f: win(f, F0, NOW + 10, 8, 14) * smooth(lin(f, run_start - 4, run_start + 10)))
rg = poly("r_groundline", [(-8, 0.3, RGROUND), (40, 0.3, RGROUND)], 0.016, r_ground)
hide_when(rg, lambda f: F0 - 9 <= f <= NOW + 25)
# goldener Weg unter dem Laeufer: leuchtet vor ihm auf
rp = poly("r_path", [(-1.5, -0.5, RGROUND - 0.01), (40, -0.5, RGROUND - 0.01)], 0.04, r_gold)
bevel_reveal(rp, lambda f: smooth(lin(f, run_start - 4, NOW)) * 0.6)
hide_when(rp, lambda f: run_start - 5 <= f <= NOW + 25)
for k in range(16):
    r = random.Random(900 + k)
    z = RGROUND + r.uniform(0.3, 6.5)
    ln = r.uniform(0.6, 2.4)
    y = r.uniform(0.5, 3.0)
    o = poly(f"speed{k}", [(0, y, z), (ln, y, z)], 0.012, r_ground)
    sp = r.uniform(0.25, 0.5)
    ph = r.uniform(0, 30)

    def spl(f, sp=sp, ph=ph):
        cx = CAMX[f]
        u = ((f * sp + ph) % 30) / 30.0
        return (cx + 6 - 13 * u, 0, 0)
    anim(o, "location", spl)
    hide_when(o, lambda f: run_start <= f <= NOW + 4)
# Explosion
ex_white = emat("ex_white", WHITE, 4.5)
ex_gold = emat("ex_gold", GOLD, 5.0)
ex_core = emat("ex_core", (1.0, 0.85, 0.55), 12.0)
ex_end = FLASH_PEAK + 2
fade(ex_white, lambda f: (f >= NOW) * (1 - 0.6 * smooth(lin(f, NOW, NOW + 40))) * (1 - smooth(lin(f, LOOP0 - 6, FLASH_PEAK))))
fade(ex_gold, lambda f: (f >= NOW - 3) * (1 - 0.5 * smooth(lin(f, NOW + 6, NOW + 50))) * (1 - smooth(lin(f, LOOP0 - 6, FLASH_PEAK))))
fade(ex_core, lambda f: smooth(lin(f, NOW - 3, NOW + 1)) * (0.35 + 0.65 * math.exp(-max(0, f - NOW) / 10)) * (1 - smooth(lin(f, LOOP0 - 6, FLASH_PEAK))))
ex = empty("explosion")
EXC = lambda f: (rx[min(N - 1, int(NOW))] + 0.2, -1.0, rz[min(N - 1, int(NOW))] + 1.6)
anim(ex, "location", EXC)
core_me = bpy.data.meshes.new("ex_core")
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.5)
bm.to_mesh(core_me)
bm.free()
core = link(bpy.data.objects.new("ex_core", core_me), ex)
core.data.materials.append(ex_core)
anim(core, "scale", lambda f: (lambda s: (s, s, s))(max(0.001, 1.1 * ease_out(lin(f, NOW - 3, NOW + 6)) * (0.85 + 0.15 * math.sin(f * 0.4)))))
hide_when(core, lambda f: NOW - 3 <= f <= ex_end)
for k in range(3):
    o = poly(f"ex_ring{k}", circle_pts(1.0, 96), 0.03 + 0.01 * k, ex_gold if k != 1 else ex_white, cyclic=True, parent=ex)
    d = 4 * k
    anim(o, "scale", lambda f, d=d, k=k: (lambda s: (s, s, s))(max(0.001, (0.6 + 3.4 * ease_out(lin(f, NOW + d, NOW + d + 30))) * (1 + 0.03 * math.sin(f * 0.2 + k)))))
    anim(o, "rotation_euler", lambda f, k=k: (0.25 * k, 0.0, 0.0))
    hide_when(o, lambda f, d=d: NOW + d <= f <= ex_end)
for k in range(28):
    r = random.Random(1300 + k)
    a = TAU * k / 28 + r.uniform(-0.08, 0.08)
    ln = r.uniform(4.0, 9.0)
    o = poly(f"ex_ray{k}", [(0.6 * math.cos(a), 0, 0.6 * math.sin(a)), (ln * math.cos(a), 0, ln * math.sin(a))], 0.018 + 0.01 * (k % 3 == 0),
             ex_gold if k % 2 else ex_white, parent=ex)
    dl = r.uniform(0, 4)
    bevel_reveal(o, lambda f, dl=dl: ease_out(lin(f, NOW + dl, NOW + dl + 12)))
    hide_when(o, lambda f, dl=dl: NOW + dl <= f <= ex_end)
rays_root = ex
anim(ex, "rotation_euler", lambda f: (0, -0.004 * max(0, f - NOW), 0))
for k in range(70):
    r = random.Random(1500 + k)
    o = link(bpy.data.objects.new(f"ex_spark{k}", sp_me), ex)
    a = r.uniform(0, TAU)
    sp = r.uniform(2.5, 9)
    vy = r.uniform(-3, 1)
    s0 = r.uniform(0.6, 1.6)
    o.scale = (s0, s0, s0)

    def spk(f, a=a, sp=sp, vy=vy):
        u = max(0.0, (f - NOW) / FPS)
        d = sp * (1 - math.exp(-u * 1.6)) / 1.6
        return (d * math.cos(a), vy * d * 0.3, d * math.sin(a) - 0.25 * u * u)
    anim(o, "location", spk)
    hide_when(o, lambda f: NOW <= f <= ex_end)
spark_ex = emat("ex_spark", GOLD, 9.0)
fade(spark_ex, lambda f: (f >= NOW) * (1 - smooth(lin(f, NOW + 20, FLASH_PEAK))))
for o in ex.children:
    if o.name.startswith("ex_spark"):
        o.material_slots[0].link = "OBJECT"
        o.material_slots[0].material = spark_ex

# ================================================================== Kamera-Fahrt
def cam_state(f):
    """(x, z, lens, roll) je Szene, weich ueberblendet."""
    # A: langsames Ranfahren
    a = (0.0, 0.15, 70 + 8 * smooth(lin(f, 0, A1)) * (f < LOOP0 - 20), 0.0)
    # B: leicht naeher, Wackeln beim Riss
    shake = 0.0
    if crack_t0 <= f <= shatter + 10:
        shake = 0.04 * math.sin(f * 2.3) * (1 if f < shatter else math.exp(-(f - shatter) / 5) * 3)
    b = (shake, 0.55 + shake * 0.5, 74 + 6 * smooth(lin(f, B0, B1)), 0.0)
    # C: aufziehen, waehrend der Berg waechst; Ruckler bei "taller"
    tl = W(4, "taller")
    c_sh = 0.06 * math.sin(f * 2.1) * math.exp(-max(0, f - tl) / 6) * (f >= tl)
    c = (0.0 + c_sh, -0.15 + c_sh, 74 - 12 * smooth(lin(f, C0, C1)), 0.0)
    # D: Figur folgen
    tx = hx[int(clamp(f, 0, N - 1))] + 1.4
    d = (tx * 0.9, -0.35, 66 + 6 * smooth(lin(f, D0, D1)), 0.0)
    # E: Sanduhr, langsam ran
    e = (0.0, 0.6, 72 + 10 * smooth(lin(f, E0, E1)), 0.0)
    # F: Laeufer folgen, Wackeln bei der Explosion
    fx = rx[int(clamp(f, 0, N - 1))] + 1.0
    if f > NOW:
        fx = rx[int(NOW)] + 1.0 + 0.4 * smooth(lin(f, NOW, NOW + 30))
    ex_sh = 0.12 * math.sin(f * 2.7) * math.exp(-max(0, f - NOW) / 7) * (f >= NOW)
    fz = -0.1 + ex_sh
    fl = 64 - 10 * smooth(lin(f, NOW - 4, NOW + 30))
    fs = (fx + ex_sh, fz, fl, 0.0)
    seq = [(A0, a), (B0, b), (C0, c), (D0, d), (E0, e), (F0, fs), (LOOP0, a)]
    cur = seq[0][1]
    for t0, st in seq[1:]:
        k = smooth(lin(f, t0 - 2, t0 + 8))
        cur = tuple(p * (1 - k) + q * k for p, q in zip(cur, st))
    return cur


CAMS = [cam_state(f) for f in range(N)]
CAMX = [c[0] for c in CAMS]
for f in range(N):        # Speed-Lines brauchen CAMX -> schon oben per Closure referenziert
    pass
anim(CAM, "location", lambda f: (CAMS[f][0] + 0.05 * pnoise(f, N, 11), -CAM_D, CAMS[f][1] + 0.05 * pnoise(f, N, 12)))
anim(CAM, "rotation_euler", lambda f: (PI / 2 + 0.006 * pnoise(f, N, 13), 0.004 * pnoise(f, N, 14) + CAMS[f][3], 0.0))
anim(cd, "lens", lambda f: CAMS[f][2])

# ================================================================== Ereignisse fuer den Ton
if os.environ.get("EVENTS_OUT"):
    steps_run = [f for f in range(1, N) if f > run_start and f < NOW and int(RPH[f] * 2) != int(RPH[f - 1] * 2)]
    steps_walk = [f for f in range(1, N) if f > walk_start and f < D1 and int(HPH[f] * 2) != int(HPH[f - 1] * 2)]
    ev = {"fps": FPS, "n": N, "flips": fly_t, "circle": [c_t0, c_t1], "tm_in": tm_in, "crack": [crack_t0, crack_t1],
          "shatter": shatter, "grow": [t for t, _ in g_steps], "shrink": [W(5, "never"), WE(5, "think")],
          "seg_hits": sorted(t for _, t in segs if t < D1), "walk_steps": steps_walk, "ring": [ring_t0, ring_t1],
          "today": today, "badly": badly0, "scared": scared0, "sand": [sand0, sand1], "ready": ready0,
          "run_start": run_start, "run_steps": steps_run, "now": NOW, "loop0": LOOP0, "flash_peak": FLASH_PEAK,
          "scenes": {"A": [A0, A1], "B": [B0, B1], "C": [C0, C1], "D": [D0, D1], "E": [E0, E1], "F": [F0, F1]}}
    json.dump(ev, open(os.environ["EVENTS_OUT"], "w"), indent=1)
    sys.exit(0)

# ================================================================== Backen + Rendern
do_bake()
SC.frame_set(0)
os.makedirs(OUTDIR, exist_ok=True)
if os.environ.get("SAVE_BLEND"):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR, "scene.blend"))
frames = range(N) if FRAMES == "all" else [int(x) for x in FRAMES.split(",")]
import time
for f in frames:
    p = os.path.join(OUTDIR, f"f{f:05d}.png")
    if os.path.exists(p) and FRAMES == "all":
        continue
    t = time.time()
    SC.frame_set(f)
    SC.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print(f"FRAME {f} {time.time() - t:.2f}s", flush=True)
