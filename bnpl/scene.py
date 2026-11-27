"""Blender-Szene fuer das BNPL-Video (headless), schlichter Linien-Stil.

  blender -b --factory-startup --python bnpl/scene.py -- <timeline.json> <outdir> [frames|anchors]

Reines Schwarz, duenne weisse Linien (2-3 px), flache Symbole in Weiss/Grau, kein Neon, keine
Partikel, kein Lichteffekt (nur ein sehr dezenter Schimmer). Linien zeichnen sich, Kamera faehrt
sanft. Texte (Schlagzeilen, Labels, Zaehler, Untertitel) kommen in der 2D-Nachbearbeitung; dafuer
exportiert der Modus "anchors" die Bildschirmpositionen der Label-Anker.
Koordinaten: Kamera blickt entlang +Y, Bildhoehe 16 Einheiten = 1920 px (120 px pro Einheit).
"""
import math
import os
import random
import sys
import json

import bpy
import bmesh
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index("--") + 1:]
TL = json.load(open(argv[0]))
OUTDIR = argv[1]
FRAMES = argv[2] if len(argv) > 2 else "all"
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = TL["fps"]
N = TL["n_frames"]
SAMPLES = int(os.environ.get("CYCLES_SAMPLES", "16"))
SCALE = float(os.environ.get("RENDER_SCALE", "1.0"))

WHITE = (1.0, 1.0, 1.0)
GREY = (0.26, 0.26, 0.26)          # ergibt ca. #8C8C8C
PI = math.pi
TAU = 2 * PI
R = 0.0105                          # Linienradius: 2,5 px Strichstaerke
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
        if w["w"].lower().strip(".,?!'\":…") == word.lower():
            return fr(w["start"])
    raise KeyError(f"{word!r} nicht in Satz {i}")


def WE(i, word):
    ws = SENT[i]["words"]
    for w in ws:
        if w["w"].lower().strip(".,?!'\":…") == word.lower():
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
    g1.inputs["Threshold"].default_value = 0.8
    g1.inputs["Strength"].default_value = 0.08     # nur ein Hauch Schimmer, kein Glow
    g1.inputs["Size"].default_value = 0.3
    g2 = ng.nodes.new("CompositorNodeGlare")       # enger Kern-Glow
    g2.inputs["Type"].default_value = "Bloom"
    g2.inputs["Quality"].default_value = "High"
    g2.inputs["Threshold"].default_value = 0.9
    g2.inputs["Strength"].default_value = 0.0
    g2.inputs["Size"].default_value = 0.1
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


FONT_ANTON = bpy.data.fonts.load(os.path.join(HERE, "fonts", "Inter-ExtraBold.otf"))


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
CX, CZ = -0.3, 0.6               # Bildmitte; leicht links (rechts 150 px TikTok-Leiste frei)
cd = bpy.data.cameras.new("cam")
cd.sensor_fit = "VERTICAL"
cd.sensor_height = 36
cd.lens = 70
cd.clip_start = 1
cd.clip_end = 200
CAM = link(bpy.data.objects.new("cam", cd))
SC.camera = CAM

NUM_FONT = FONT_ANTON


def mats(name, grey=False):
    return emat(name, GREY if grey else WHITE, 1.0)


def lines_obj(name, strokes, mat, parent=None, radius=R):
    """mehrere Polylinien als ein Kurvenobjekt (ein Material, gemeinsamer Zeichen-Fortschritt)"""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    for pts, cyc in strokes:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for p, c in zip(sp.points, pts):
            p.co = (c[0], c[1], c[2], 1)
        sp.use_cyclic_u = cyc
    o = bpy.data.objects.new(name, cu)
    o.data.materials.append(mat)
    return link(o, parent)


def P(x, z, y=0.0):
    return (x, y, z)


def arc(cx, cz, rx, rz, a0, a1, n=40):
    return [P(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cz + rz * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def reveal_many(objs, fn, stagger=0.0):
    """mehrere Objekte nacheinander zeichnen; fn(f) 0..1 Gesamtfortschritt"""
    n = len(objs)
    for k, o in enumerate(objs):
        a = k / n * (1 - stagger) if stagger else 0
        def g(f, k=k):
            u = fn(f) * n - k if not stagger else (fn(f) - k / n * stagger) / (1 - stagger)
            return clamp(u)
        bevel_reveal(o, g)


# ------------------------------------------------------------------ Symbole
def make_cart(name, mw, mg, parent):
    """Einkaufswagen aus Linien. Rueckgabe Liste der Kurvenobjekte in Zeichen-Reihenfolge."""
    body = lines_obj(name + "_body", [([P(-1.5, 1.1), P(-1.15, 1.1), P(-0.95, 0.75), P(1.25, 0.75), P(1.0, -0.35),
                                         P(-0.7, -0.35), P(-0.95, 0.75)], False)], mw, parent)
    base = lines_obj(name + "_base", [([P(-0.7, -0.35), P(-0.6, -0.65), P(1.05, -0.65)], False)], mw, parent)
    grid = lines_obj(name + "_grid", [([P(-0.2, 0.75), P(-0.1, -0.35)], False), ([P(0.55, 0.75), P(0.5, -0.35)], False),
                                       ([P(-0.84, 0.2), P(1.12, 0.2)], False)], mg, parent)
    w1 = lines_obj(name + "_w1", [(arc(-0.35, -0.88, 0.16, 0.16, PI / 2, PI / 2 + TAU), False)], mw, parent)
    w2 = lines_obj(name + "_w2", [(arc(0.85, -0.88, 0.16, 0.16, PI / 2, PI / 2 + TAU), False)], mw, parent)
    return [body, base, grid, w1, w2]


def make_person(name, mw, parent, s=1.0):
    head = lines_obj(name + "_head", [(arc(0, 0.62 * s, 0.3 * s, 0.3 * s, -PI / 2, -PI / 2 + TAU, 48), False)], mw, parent)
    body = lines_obj(name + "_body", [(arc(0, -0.55 * s, 0.58 * s, 0.78 * s, PI, 0, 40) + [P(-0.58 * s, -0.55 * s)], False)], mw, parent)
    return [head, body]


def make_cash(name, mw, mg, parent):
    rect = lines_obj(name + "_rect", [(rect_pts(2.1, 1.15, 0.08, 0, 0, 0, 3), True)], mw, parent)
    inner = lines_obj(name + "_c", [(arc(0, 0, 0.28, 0.28, PI / 2, PI / 2 + TAU, 40), False),
                                    ([P(-0.8, 0.38), P(-0.62, 0.38)], False), ([P(0.62, -0.38), P(0.8, -0.38)], False)], mg, parent)
    return [rect, inner]


def chain_links(name, p0, p1, n, mw, parent, sag=0.35):
    """Kette aus n Gliedern entlang einer leicht durchhaengenden Linie. Rueckgabe Liste Objekte."""
    out = []
    for k in range(n):
        u = (k + 0.5) / n
        x = p0[0] + (p1[0] - p0[0]) * u
        z = p0[1] + (p1[1] - p0[1]) * u - sag * math.sin(PI * u)
        dx = (p1[0] - p0[0]) / n
        dz = (p1[1] - p0[1]) / n - sag * PI / n * math.cos(PI * u)
        ang = math.atan2(dz, dx)
        L = math.hypot(dx, dz) * 0.62
        if k % 2 == 0:   # Glied von vorn: Langloch
            pts = [P(x + math.cos(ang) * L * math.cos(t) - math.sin(ang) * 0.075 * math.sin(t),
                     z + math.sin(ang) * L * math.cos(t) + math.cos(ang) * 0.075 * math.sin(t)) for t in [PI / 2 + TAU * i / 40 for i in range(41)]]
        else:            # Glied von der Seite: Strich
            pts = [P(x - math.cos(ang) * L * 0.95, z - math.sin(ang) * L * 0.95), P(x + math.cos(ang) * L * 0.95, z + math.sin(ang) * L * 0.95)]
        out.append(lines_obj(f"{name}{k}", [(pts, False)], mw, parent))
    return out


ANCHORS = []    # (name, objekt, label, alpha_fn) -> Bildschirmposition fuer Labels in der Nachbearbeitung


def anchor(name, loc, parent, label, alpha_fn):
    e = empty(name, loc, parent)
    ANCHORS.append((name, e, label, alpha_fn))
    return e


# ------------------------------------------------------------------ Szenenfenster
END = N - 1
LOOP_R = 0.12          # Zeichen-Fortschritt des Wagens in Frame 0 und im letzten Frame (Loop-Naht)
A1 = S(3) - 4
B0, B1 = S(3) - 6, S(4) - 4
C0, C1 = S(4) - 6, S(6) - 5
D0, D1 = S(6) - 6, S(8) - 6
E0, E1 = S(8) - 8, S(10) - 4
F0 = S(10) - 6
TAIL0 = E(10) + 12     # nach "this?": Wagen zieht sich bis zur Loop-Naht zurueck

# ================================================================== Szene 1/2: Wagen, Kette, Person
mA_w, mA_g = mats("cartA_w"), mats("cartA_g", True)
cartA = empty("cartA", (CX, 0, 0.9))
cartA_objs = make_cart("cartA", mA_w, mA_g, cartA)
cartA_vis = lambda f: (1 - smooth(lin(f, A1 - 4, A1 + 8))) + smooth(lin(f, F0, F0 + 12))
fade(mA_w, lambda f: min(1.0, cartA_vis(f)))
fade(mA_g, lambda f: min(1.0, cartA_vis(f)))


def cartA_draw(f):
    if f < A1 + 20:
        return LOOP_R + (1 - LOOP_R) * smooth(lin(f, 0, 38))
    if f < TAIL0:
        return smooth(lin(f, F0 + 2, F0 + 40))
    return 1 - (1 - LOOP_R) * smooth(lin(f, TAIL0, END))


reveal_many(cartA_objs, cartA_draw)
# Wagen rueckt in Satz 2 nach links, Person erscheint rechts, Kette dazwischen
mv0, mv1 = S(2) - 4, W(2, "freedom") + 4


def cartA_loc(f):
    if f >= F0 - 2:
        return (CX, 0, 0.9)
    u = smooth(lin(f, mv0, mv1))
    return (CX - 1.85 * u, 0, 0.9 - 0.1 * u)


anim(cartA, "location", cartA_loc)
CART_S = 1.25
anim(cartA, "scale", lambda f: (lambda s: (s, s, s))(CART_S if f >= F0 - 2 else CART_S * (1 - 0.4 * smooth(lin(f, mv0, mv1)))))
mP_w = mats("personA_w")
personA = empty("personA", (CX + 1.85, 0, 0.95))
personA.scale = (0.8, 0.8, 0.8)
pA_objs = make_person("personA", mP_w, personA)
pA_t0 = W(2, "freedom") - 2
fade(mP_w, lambda f: (1 - smooth(lin(f, A1 - 4, A1 + 8))))
reveal_many(pA_objs, lambda f: smooth(lin(f, pA_t0, pA_t0 + 24)))
mC = mats("chainA")
fade(mC, lambda f: (1 - smooth(lin(f, A1 - 4, A1 + 8))))
links = chain_links("chainA", (CX - 0.95, 0.7), (CX + 1.4, 0.45), 9, mC, None, sag=0.3)
ch0, ch1 = W(2, "it's") - 3, WE(2, "not") + 10
for k, o in enumerate(links):
    t = ch0 + (ch1 - ch0) * k / len(links)
    bevel_reveal(o, lambda f, t=t: smooth(lin(f, t, t + 6)))
for o in cartA_objs + pA_objs + links:
    hide_when(o, lambda f: f < A1 + 10 or f > F0 - 1)
for o in pA_objs + links:
    hide_when(o, lambda f: pA_t0 - 2 < f < A1 + 10)
anchor("lbl_cart", (0, -0.2, -1.35), cartA, "CART", lambda f: smooth(lin(f, 14, 34)) * (1 - smooth(lin(f, A1 - 6, A1 + 4))))
anchor("lbl_you", (0, -0.2, -1.65), personA, "YOU", lambda f: smooth(lin(f, pA_t0 + 8, pA_t0 + 22)) * (1 - smooth(lin(f, A1 - 6, A1 + 4))))

# ================================================================== Szene 3: Daten (Zaehler in der Nachbearbeitung)
mB_w, mB_g = mats("dataB_w"), mats("dataB_g", True)
visB = lambda f: smooth(lin(f, B0, B0 + 10)) * (1 - smooth(lin(f, B1, B1 + 10)))
fade(mB_w, visB)
fade(mB_g, visB)
cnt0, cnt1 = W(3, "spend") - 2, WE(3, "dollars")
base_line = lines_obj("dataB_line", [([P(CX - 2.6, 0.35), P(CX + 2.6, 0.35)], False)], mB_w)
bevel_reveal(base_line, lambda f: smooth(lin(f, cnt0, cnt1)))
ticks = lines_obj("dataB_ticks", [([P(CX - 2.6 + 5.2 * k / 10, 0.35), P(CX - 2.6 + 5.2 * k / 10, 0.35 - (0.16 if k % 5 == 0 else 0.08))], False)
                                    for k in range(11)], mB_g)
bevel_reveal(ticks, lambda f: smooth(lin(f, B0 + 4, cnt0 + 20)))
for o in (base_line, ticks):
    hide_when(o, lambda f: B0 - 1 <= f <= B1 + 11)

# ================================================================== Szene 4/5: Raten-Boxen ziehen die Person nach unten
mC_w, mC_g = mats("payC_w"), mats("payC_g", True)
visC = lambda f: smooth(lin(f, C0, C0 + 10)) * (1 - smooth(lin(f, C1, C1 + 10)))
fade(mC_g, visC)
pay_t = [W(4, "small") - 2, W(4, "payments") + 4, W(4, "big") - 2, W(4, "chains") + 2]
box_x = [CX - 2.25, CX - 0.75, CX + 0.75, CX + 2.25]
BOX_Z = -1.15
JZ = -0.15                      # Knotenpunkt der Zugleinen
personC = empty("personC")
pC_w = mats("personC_w")
pC_objs = make_person("personC", pC_w, personC, 0.95)
sold = W(5, "sold")


def pC_z(f):
    steps = sum(smooth(lin(f, t + 3, t + 14)) for t in pay_t)
    later = smooth(lin(f, W(5, "every"), sold + 8))
    return 2.75 - 0.22 * steps - 0.5 * later


anim(personC, "location", lambda f: (CX, 0, pC_z(f)))
fade(pC_w, lambda f: visC(f) * (1 - 0.55 * smooth(lin(f, W(5, "future"), sold + 6))))     # verblasst zu Grau
reveal_many(pC_objs, lambda f: smooth(lin(f, C0 + 2, C0 + 22)))
box_objs = []
for k, (x, t) in enumerate(zip(box_x, pay_t)):
    m = mats(f"box{k}")
    fade(m, visC)
    box = lines_obj(f"box{k}", [(rect_pts(0.56, 0.56, 0.05, x, BOX_Z, 0, 3), True)], m)
    chk = lines_obj(f"chk{k}", [([P(x - 0.15, BOX_Z + 0.0), P(x - 0.04, BOX_Z - 0.12), P(x + 0.17, BOX_Z + 0.14)], False)], m)
    bevel_reveal(box, lambda f, t=t: smooth(lin(f, t, t + 10)))
    bevel_reveal(chk, lambda f, t=t: smooth(lin(f, t + 8, t + 14)))
    # Zugleine von der Box zum Knoten
    rope = lines_obj(f"rope{k}", [([P(x, BOX_Z + 0.3), P(CX, JZ)], False)], mC_g)
    bevel_reveal(rope, lambda f, t=t: smooth(lin(f, t + 4, t + 14)))
    box_objs += [box, chk, rope]
    anchor(f"lbl_pay{k}", (x, -0.2, BOX_Z - 0.55), None, f"PAYMENT {k + 1}", lambda f, t=t: smooth(lin(f, t + 2, t + 12)) * visC(f))
# Hauptleine vom Knoten zu den Fuessen der Person (Laenge folgt der Person)
main_rope = lines_obj("rope_main", [([P(0, 0), P(0, 1)], False)], mC_g)
anim(main_rope, "location", lambda f: (CX, 0, JZ))
anim(main_rope, "scale", lambda f: (1, 1, max(0.001, pC_z(f) - 0.55 * 0.95 - JZ)))
bevel_reveal(main_rope, lambda f: smooth(lin(f, pay_t[0] + 2, pay_t[0] + 14)))
for o in pC_objs + box_objs + [main_rope]:
    hide_when(o, lambda f: C0 - 1 <= f <= C1 + 11)

# ================================================================== Szene 6/7: Wagen und Geld tauschen die Plaetze
mD_w, mD_g = mats("swapD_w"), mats("swapD_g", True)
visD = lambda f: smooth(lin(f, D0, D0 + 12)) * (1 - smooth(lin(f, D1, D1 + 10)))
fade(mD_w, visD)
fade(mD_g, visD)
cartD = empty("cartD")
cartD.scale = (0.62, 0.62, 0.62)
cD = make_cart("cartD", mD_w, mD_g, cartD)
cashD = empty("cashD")
cashD.scale = (0.8, 0.8, 0.8)
kD = make_cash("cashD", mD_w, mD_g, cashD)
reveal_many(cD + kD, lambda f: smooth(lin(f, D0 + 2, D0 + 34)))
sw0, sw1 = W(7, "pay") - 4, WE(7, "later") + 4
LX, RX, DZ = CX - 1.45, CX + 1.45, 0.85


def swap_pos(f, start_left):
    u = smooth(lin(f, sw0, sw1))
    a = PI * u
    x = (CX + (LX - CX) * math.cos(a)) if start_left else (CX + (RX - CX) * math.cos(a))
    z = DZ + (0.7 if start_left else -0.7) * math.sin(a)
    return (x, 0, z)


anim(cartD, "location", lambda f: swap_pos(f, True))
anim(cashD, "location", lambda f: swap_pos(f, False))
for o in cD + kD:
    hide_when(o, lambda f: D0 - 1 <= f <= D1 + 11)
anchor("lbl_buy", (0, -0.2, -1.55), cartD, "BUY", lambda f: visD(f) * smooth(lin(f, D0 + 16, D0 + 30)))
anchor("lbl_pay", (0, -0.2, -1.05), cashD, "PAY", lambda f: visD(f) * smooth(lin(f, D0 + 16, D0 + 30)))

# ================================================================== Szene 8/9: Weg nach oben
mE_w, mE_g = mats("pathE_w"), mats("pathE_g", True)
visE = lambda f: smooth(lin(f, E0, E0 + 12)) * (1 - smooth(lin(f, E1, E1 + 12)))
fade(mE_w, visE)
fade(mE_g, visE)


def path_pt(u):
    """geschwungener Weg von unten links nach oben rechts (u 0..1)"""
    x = CX - 2.0 + 3.6 * u + 0.75 * math.sin(TAU * u * 0.95)
    z = -2.0 + 4.6 * u - 0.25 * math.sin(PI * u)
    return (x, z)


path_pts = [P(*path_pt(i / 120)) for i in range(121)]
path = lines_obj("pathE", [(path_pts, False)], mE_g)
path_dr = lambda f: smooth(lin(f, E0 + 2, W(8, "wait") + 26))
bevel_reveal(path, path_dr)
gx, gz = path_pt(1.0)
goal = lines_obj("goalE", [(arc(gx + 0.0, gz + 0.48, 0.42, 0.42, -PI / 2, -PI / 2 + TAU, 64), False)], mE_w)
bevel_reveal(goal, lambda f: smooth(lin(f, W(9, "freedom") - 6, W(9, "freedom") + 18)))
walker = empty("walkerE")
walker.scale = (0.42, 0.42, 0.42)
wk = make_person("walkerE", mE_w, walker)
reveal_many(wk, lambda f: smooth(lin(f, W(8, "wait") - 2, W(8, "wait") + 16)))
walk_u = lambda f: 0.02 + 0.80 * smooth(lin(f, W(8, "save"), E1 - 6))


def walker_loc(f):
    u = walk_u(f)
    x, z = path_pt(u)
    bob = 0.03 * abs(math.sin(f * 0.25)) * (0.0 < lin(f, W(8, "save"), E1 - 6) < 1.0)
    return (x, -0.05, z + 0.95 * 0.42 + bob)


anim(walker, "location", walker_loc)
miles = [("WAIT", 0.16, W(8, "wait")), ("SAVE", 0.40, W(8, "save")), ("BUY", 0.64, W(8, "then"))]
mticks = []
for lbl, u, t in miles:
    x, z = path_pt(u)
    tk = lines_obj(f"mile_{lbl}", [([P(x + 0.18, z), P(x + 0.36, z)], False)], mE_w)
    bevel_reveal(tk, lambda f, t=t: smooth(lin(f, t - 2, t + 6)))
    mticks.append(tk)
    anchor(f"lbl_m_{lbl}", (x + 0.78, -0.2, z), None, lbl, lambda f, t=t: smooth(lin(f, t, t + 10)) * visE(f))
for o in [path, goal] + wk + mticks:
    hide_when(o, lambda f: E0 - 1 <= f <= E1 + 13)

# ================================================================== Kamera
def cam_state(f):
    drift = (0.06 * pnoise(f, N, 11), 0.05 * pnoise(f, N, 12))
    lens = 70.0
    # sanfte Ranfahrt je Szene (wieder auf 70 mm zum Loop)
    for a, b, d in ((0, A1, 4), (B0, B1, 5), (C0, C1, 4), (D0, D1, 4), (E0, E1, 3)):
        lens += d * smooth(lin(f, a, b)) * (1 - smooth(lin(f, b, b + 14)))
    zoff = -0.15 * smooth(lin(f, C0, C0 + 40)) * (1 - smooth(lin(f, C1, C1 + 14)))
    # Kamera so, dass CX auf x = 495 px landet (Mitte der Safe-Zone 60..930 px)
    return (CX + (540 - 495) / 120 + drift[0], CZ + drift[1] + zoff, lens)


anim(CAM, "location", lambda f: (cam_state(f)[0], -CAM_D, cam_state(f)[1]))
anim(CAM, "rotation_euler", lambda f: (PI / 2 + 0.004 * pnoise(f, N, 13), 0.003 * pnoise(f, N, 14), 0.0))
anim(cd, "lens", lambda f: cam_state(f)[2])

# ================================================================== Backen, Anker, Rendern
do_bake()
os.makedirs(OUTDIR, exist_ok=True)
if FRAMES == "anchors":
    from bpy_extras.object_utils import world_to_camera_view
    res = {"labels": {}, "n": N}
    for name, e, label, fn in ANCHORS:
        res["labels"][name] = {"text": label, "track": []}
    for f in range(N):
        SC.frame_set(f)
        for name, e, label, fn in ANCHORS:
            a = float(fn(f))
            if a < 0.003:
                res["labels"][name]["track"].append(None)
                continue
            v = world_to_camera_view(SC, CAM, e.matrix_world.translation)
            res["labels"][name]["track"].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1), round(a, 3)])
    ev = {"cnt": [cnt0, cnt1], "pay": pay_t, "swap": [sw0, sw1], "scenes": {"A1": A1, "B": [B0, B1], "C": [C0, C1],
          "D": [D0, D1], "E": [E0, E1], "F0": F0, "tail": TAIL0}}
    res["events"] = ev
    json.dump(res, open(os.path.join(OUTDIR, "anchors.json"), "w"))
    sys.exit(0)
SC.frame_set(0)
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
