"""Blender-Szene fuer das Video "A year from now" (headless), schlichter Linien-Stil.

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

def make_person(name, mw, parent, s=1.0):
    head = lines_obj(name + "_head", [(arc(0, 0.62 * s, 0.3 * s, 0.3 * s, -PI / 2, -PI / 2 + TAU, 48), False)], mw, parent)
    body = lines_obj(name + "_body", [(arc(0, -0.55 * s, 0.58 * s, 0.78 * s, PI, 0, 40) + [P(-0.58 * s, -0.55 * s)], False)], mw, parent)
    return [head, body]




ANCHORS = []    # (name, objekt, label, alpha_fn) -> Bildschirmposition fuer Labels in der Nachbearbeitung


def anchor(name, loc, parent, label, alpha_fn):
    e = empty(name, loc, parent)
    ANCHORS.append((name, e, label, alpha_fn))
    return e



# ------------------------------------------------------------------ Szenenfenster und Geometrie
END = N - 1
B0 = S(3) - 6                    # flacher Weg
C0 = S(5) - 8                    # Kurve nach oben
D0 = S(8) - 6                    # gleiche Zeit
E0 = S(9) - 6                    # du, hoeher
F0 = S(10) - 8                   # zurueck zur Gabelung
FX, FZ = CX - 2.05, -0.45        # Gabelpunkt
LZ = FZ - 0.3                    # Hoehe des flachen Wegs
LX1 = FX + 5.15                  # Ende des flachen Wegs
STUB = 0.55                      # Laenge der Wegstummel in Szene 1
UPW, UPH = 4.9, 4.05             # Ausdehnung der Kurve nach oben


def up_pt(u):
    """ansteigende, geschwungene Kurve vom Gabelpunkt (u 0..1)"""
    x = FX + UPW * u
    z = FZ + UPH * (0.12 * u + 0.88 * (3 * u ** 2 - 2 * u ** 3)) + 0.12 * math.sin(PI * u)
    return x, z


def low_pt(u):
    """flacher Weg: kurzer Knick nach unten, dann waagerecht"""
    x = FX + (LX1 - FX) * u
    k = min(1.0, u / 0.08)
    return x, FZ + (LZ - FZ) * (3 * k ** 2 - 2 * k ** 3)


def arclen_param(fn, n=400):
    """u-Werte, die die Kurve in gleich lange Stuecke teilen"""
    pts = [fn(i / n) for i in range(n + 1)]
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return pts, d


UP_PTS, UP_D = arclen_param(up_pt)
LO_PTS, LO_D = arclen_param(low_pt)


def at_len(pts, d, frac):
    t = frac * d[-1]
    for i in range(1, len(d)):
        if d[i] >= t:
            a = (t - d[i - 1]) / max(1e-9, d[i] - d[i - 1])
            return (pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * a, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * a)
    return pts[-1]


def stub_frac(d, length):
    return length / d[-1]


# ================================================================== Person 1 + Gabelung (Szene 1, Loop)
mP1 = mats("p1")
p1 = empty("p1", (FX - 0.75, 0, FZ + 0.55 * 0.62))
p1.scale = (0.62, 0.62, 0.62)
p1_objs = make_person("p1", mP1, p1)
# Person 1 ist in Frame 0 sichtbar, wird ab Szene 3 grau (das alte Ich) und blendet in Satz 10 wieder voll ein
fade(mP1, lambda f: 1 - 0.6 * smooth(lin(f, C0, C0 + 20)) * (1 - smooth(lin(f, F0, F0 + 24))))
reveal_many(p1_objs, lambda f: 1.0)
mStem = mats("stem")
stem = lines_obj("stem", [([P(FX - 0.75 + 0.36, FZ), P(FX, FZ)], False)], mStem)
fade(mStem, lambda f: 1.0)
anchor("lbl_you1", (FX - 0.75, -0.2, FZ - 0.4), None, "YOU", lambda f: (1 - smooth(lin(f, B0 - 10, B0))) + smooth(lin(f, END - 30, END - 8)))


LOOP_V = 0.35          # Anteil des Stummels in Frame 0 und im letzten Frame (Loop-Naht)


def path_draw(f, t_full0, t_full1, retract=True):
    """Zeichen-Fortschritt eines Wegs (Anteil der Gesamtlaenge): Stummel in Szene 1, voll ab t_full,
    Rueckzug auf den Stummel in Satz 10 (Loop)."""
    stub = STUB
    v = LOOP_V + (1 - LOOP_V) * smooth(lin(f, 0, 30))      # Stummel zeichnen sich in der ersten 1 s fertig
    full = smooth(lin(f, t_full0, t_full1))
    back = smooth(lin(f, F0 + 6, END - 6)) if retract else 0.0
    return v, full, back


# ================================================================== Unterer, flacher Weg (Szene 2)
mLow = mats("low")
low = lines_obj("low", [([P(x, z) for x, z in LO_PTS], False)], mLow)
lo_stub = stub_frac(LO_D, STUB)
l0, l1 = W(3, "flat") - 4, WE(3, "familiar") + 6


def low_frac(f):
    v, full, back = path_draw(f, l0, l1)
    frac = lo_stub * v + (1 - lo_stub) * full
    return frac - (frac - lo_stub * LOOP_V) * back


bevel_reveal(low, low_frac)
fade(mLow, lambda f: 1 - 0.55 * smooth(lin(f, C0, C0 + 20)) * (1 - smooth(lin(f, D0, D0 + 12))) - 0.35 * smooth(lin(f, E0, E0 + 14)) * (1 - smooth(lin(f, F0, F0 + 20))))
mSame = mats("same", grey=True)
same_vis = lambda f: (1 - 0.5 * smooth(lin(f, C0, C0 + 20))) * (1 - smooth(lin(f, F0, F0 + 14)))
fade(mSame, same_vis)
for k, (word, lbl) in enumerate((("job", "SAME JOB"), ("habits", "SAME HABITS"), ("excuses", "SAME EXCUSES"))):
    x = FX + 1.2 + 1.55 * k
    t = W(4, word) - 3
    c = lines_obj(f"same{k}", [(arc(x, LZ + 0.2, 0.2, 0.2, -PI / 2, -PI / 2 + TAU, 40), False)], mSame)
    bevel_reveal(c, lambda f, t=t: smooth(lin(f, t, t + 12)))
    hide_when(c, lambda f, t=t: t - 1 <= f <= F0 + 15)
    anchor(f"lbl_same{k}", (x, -0.2, LZ - 0.32 if k != 1 else LZ + 0.68), None, lbl, lambda f, t=t: smooth(lin(f, t + 2, t + 14)) * same_vis(f))
t_still = WE(4, "excuses") + 4
mEnd = mats("lowend")
endpt = lines_obj("lowend", [(arc(LX1, LZ, 0.07, 0.07, 0, TAU, 24), False)], mEnd)
bevel_reveal(endpt, lambda f: smooth(lin(f, l1 - 4, l1 + 6)))
fade(mEnd, lambda f: same_vis(f))
hide_when(endpt, lambda f: l1 - 5 <= f <= F0 + 15)
anchor("lbl_still", (LX1 - 0.3, -0.2, LZ + 0.68), None, "STILL HERE", lambda f: smooth(lin(f, t_still, t_still + 14)) * same_vis(f))

# ================================================================== Oberer Weg: geschwungene Kurve (Szene 3)
mUp = mats("up")
up = lines_obj("up", [([P(x, z) for x, z in UP_PTS], False)], mUp)
up_stub = stub_frac(UP_D, STUB)
u0, u1 = W(5, "this") - 2, WE(7, "view") + 4      # waechst mit jedem Satzteil (siehe Haekchen)


def up_frac(f):
    v, full, back = path_draw(f, u0, u1)
    # in Etappen: jede Phrase bringt ein Stueck
    frac = up_stub * v + (1 - up_stub) * up_progress(f)
    return frac - (frac - up_stub * LOOP_V) * back


PHRASES = [(W(5, "this") - 2, WE(5, "up") + 2), (W(6, "one") - 2, WE(6, "day") + 2), (W(6, "claps") - 8, WE(6, "claps") + 2),
           (WE(6, "claps") + 6, WE(6, "watches") + 2), (W(7, "but") - 2, WE(7, "view") + 4)]


def up_progress(f):
    return sum(smooth(lin(f, a, b)) for a, b in PHRASES) / len(PHRASES)


bevel_reveal(up, up_frac)
fade(mUp, lambda f: 1 - 0.3 * smooth(lin(f, D0, D0 + 12)) * (1 - smooth(lin(f, E0, E0 + 12))))
mBox = mats("boxes")
box_vis = lambda f: 1 - smooth(lin(f, F0, F0 + 14))
fade(mBox, box_vis)
for k, (a, b) in enumerate(PHRASES):
    frac = 0.12 + 0.72 * k / (len(PHRASES) - 1)
    x, z = at_len(UP_PTS, UP_D, frac)
    # Normale nach oben-links neben die Kurve
    x2, z2 = at_len(UP_PTS, UP_D, min(1, frac + 0.01))
    nx, nz = -(z2 - z), (x2 - x)
    ln = math.hypot(nx, nz) or 1
    bx, bz = x + nx / ln * 0.42, z + nz / ln * 0.42
    s = 0.26
    box = lines_obj(f"box{k}", [(rect_pts(s, s, 0.03, bx, bz, 0, 3), True)], mBox)
    chk = lines_obj(f"chk{k}", [([P(bx - 0.075, bz + 0.0), P(bx - 0.02, bz - 0.06), P(bx + 0.085, bz + 0.07)], False)], mBox)
    tb = b - 4
    bevel_reveal(box, lambda f, t=tb: smooth(lin(f, t, t + 8)))
    bevel_reveal(chk, lambda f, t=tb: smooth(lin(f, t + 6, t + 11)))
    for o in (box, chk):
        hide_when(o, lambda f, t=tb: t - 1 <= f <= F0 + 15)

# ================================================================== Gleiche Zeit: 12 Monatsstriche auf beiden Wegen + Kalender (Szene 4)
mTick = mats("ticks", grey=True)
tick_vis = lambda f: smooth(lin(f, D0, D0 + 16)) * (1 - smooth(lin(f, F0, F0 + 14)))
fade(mTick, tick_vis)
ticks = []
for pts, d, name in ((UP_PTS, UP_D, "up"), (LO_PTS, LO_D, "lo")):
    strokes = []
    for k in range(1, 13):
        x, z = at_len(pts, d, k / 12)
        x2, z2 = at_len(pts, d, min(1, k / 12 + 0.005))
        tx, tz = x2 - x, z2 - z
        ln = math.hypot(tx, tz) or 1
        nx, nz = -tz / ln, tx / ln
        h = 0.13 if k % 3 else 0.2
        strokes.append(([P(x - nx * h, z - nz * h), P(x + nx * h, z + nz * h)], False))
    o = lines_obj(f"ticks_{name}", strokes, mTick)
    bevel_reveal(o, lambda f: smooth(lin(f, D0 + 2, W(8, "year") + 6)))
    hide_when(o, lambda f: D0 - 1 <= f <= F0 + 15)
    ticks.append(o)
mCal = mats("cal")
cal_vis = lambda f: smooth(lin(f, D0, D0 + 14)) * (1 - smooth(lin(f, E0 - 4, E0 + 10)))
fade(mCal, cal_vis)
CXc, CZc = FX + 0.3, FZ + 2.95
cal = lines_obj("cal", [(rect_pts(1.3, 1.25, 0.08, CXc, CZc, 0, 3), True),
                        ([P(CXc - 0.65, CZc + 0.32), P(CXc + 0.65, CZc + 0.32)], False),
                        ([P(CXc - 0.33, CZc + 0.5), P(CXc - 0.33, CZc + 0.72)], False),
                        ([P(CXc + 0.33, CZc + 0.5), P(CXc + 0.33, CZc + 0.72)], False)], mCal)
bevel_reveal(cal, lambda f: smooth(lin(f, D0 + 2, D0 + 26)))
hide_when(cal, lambda f: D0 - 1 <= f <= E0 + 11)
anchor("big_365", (CXc, -0.2, CZc - 0.12), None, "365", lambda f: smooth(lin(f, D0 + 14, D0 + 26)) * cal_vis(f))
anchor("lbl_sametime", (CXc, -0.2, CZc - 0.9), None, "SAME TIME", lambda f: smooth(lin(f, W(8, "exactly"), W(8, "exactly") + 14)) * cal_vis(f))

# ================================================================== Du, hoeher (Szene 5)
mP2 = mats("p2")
ux, uz = UP_PTS[-1]
p2 = empty("p2", (ux, 0, uz + 0.55 * 0.82 + 0.04))
p2.scale = (0.82, 0.82, 0.82)
p2_objs = make_person("p2", mP2, p2)
t_p2 = W(9, "only") - 2
reveal_many(p2_objs, lambda f: smooth(lin(f, t_p2, t_p2 + 26)))
fade(mP2, lambda f: smooth(lin(f, t_p2, t_p2 + 10)) * (1 - smooth(lin(f, F0, F0 + 16))))
for o in p2_objs:
    hide_when(o, lambda f: t_p2 - 1 <= f <= F0 + 17)
anchor("lbl_higher", (ux, -0.2, uz + 0.55 * 0.82 + 0.62 * 0.82 + 0.45), None, "YOU, HIGHER", lambda f: smooth(lin(f, W(9, "higher") - 4, W(9, "higher") + 10)) * (1 - smooth(lin(f, F0 - 8, F0 + 4))))

# ================================================================== Kamera
def cam_state(f):
    drift = (0.05 * pnoise(f, N, 11), 0.04 * pnoise(f, N, 12))
    # (x, z, lens) je Abschnitt; weich ueberblendet; Ende = Anfang (Loop)
    A = (FX - 0.35, 0.45, 72 + 3 * smooth(lin(f, 0, B0)) * (f < F0))
    B = (CX + 0.05, 0.55, 70)
    C = (CX + 0.15, 0.75 + 1.25 * up_progress(f), 68)
    D = (CX + 0.1, 1.3, 60)
    E = (CX + 0.4, 2.0, 66)
    Fs = (FX - 0.35, 0.45, 72)
    seq = [(0, A), (B0, B), (C0, C), (D0, D), (E0, E), (F0, Fs)]
    cur = seq[0][1]
    for t0, st in seq[1:]:
        k = smooth(lin(f, t0, t0 + (40 if st is Fs else 30)))
        cur = tuple(p * (1 - k) + q * k for p, q in zip(cur, st))
    return (cur[0] + (540 - 495) / 120 + drift[0], cur[1] + drift[1], cur[2])


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
    res["events"] = {"scenes": {"B": B0, "C": C0, "D": D0, "E": E0, "F": F0}, "phrases": PHRASES, "same": [W(4, w) for w in ("job", "habits", "excuses")]}
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
