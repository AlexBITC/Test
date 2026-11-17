"""Baut die Asset-Bibliothek in Blender: loopbare Figuren-Clips (RGBA) und Set-Plates (Hinter-/Vordergrund).

Einmal rendern, danach setzt engine/compose.py jede Episode in 2D zusammen (kein Blender pro Episode).

Aufruf (durch engine/build_assets.py):
  blender -b --factory-startup --python engine/assets_blender.py -- clip  <name> <outdir> <samples> [pass]
  blender -b --factory-startup --python engine/assets_blender.py -- plate <set>  <outdir> <samples>

Clip-Konventionen
  * Figur steht im Ursprung, kanonische Kamera (Blick +Y), feste Pixel pro Meter (PPM).
  * Reaktionen: 'in' (Antizipation -> Pose) + 'loop' (Pose gehalten, nahtlos). neutral nur 'loop'.
  * Kalle hat Mund-Varianten (Visemes zu/halb/auf) als kleine Ausschnitte um den Mund:
    gleiche Bewegung (gleiche Seeds), nur der Mund ist anders -> compose tauscht den Ausschnitt.
"""
import json
import math
import os
import sys

ENGINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ENGINE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402

import anim  # noqa: E402
import characters as C  # noqa: E402
import look as L  # noqa: E402
import sets as S  # noqa: E402

FPS = 30
LOOP = int(os.environ.get("CLIP_LOOP", "75"))                 # 2,5 s: Byte-Schweben (0,8 Hz) und Kippeln (0,4 Hz) gehen glatt auf
CLOSE = 14                # die letzten Frames gleiten exakt auf den Loop-Anfang zurueck
SENSOR = 36.0             # vertikal
PPM = float(os.environ.get("CLIP_PPM", "440"))   # Pixel pro Meter in der Ebene der Figur (Clips)
CAM_DIST = 3.8
# Reaktion: Hauptakzent-Frame und Laenge des 'in'-Teils (Bewegung hat sich gesetzt)
REACT_F = 6
IN_LEN = {"neutral": 0, "zweifel": 20, "staunen": 24, "schock": 44, "jubel": 38}
VISEMES = {"zu": 0.18, "halb": 0.62, "auf": 1.0}

CLIPS = {
    "kalle_neutral": ("kalle", "neutral"), "kalle_zweifel": ("kalle", "zweifel"),
    "kalle_staunen": ("kalle", "staunen"), "kalle_schock": ("kalle", "schock"), "kalle_jubel": ("kalle", "jubel"),
    "byte_schweben": ("byte", "schweben"), "byte_sprechen": ("byte", "sprechen"),
}
# Bildausschnitt der Clips in Metern (Breite, Hoehe, Mitte z)
FRAME_M = {"kalle": (1.9, 3.45, 1.45), "byte": (1.0, 1.15, 0.05)}
# Plates: Kamera wie die Standard-Einstellung der alten Regie, aber weitwinkliger (Overscan fuer 2D-Kamera)
PLATE_W, PLATE_H = 1620, 2880          # 1,5 x 1080x1920
PLATE_LENS = 28.0                      # 2D-Zoom 1,25 entspricht 35 mm, 1,6 entspricht 45 mm


# ------------------------------------------------------------------ Grundsetup
def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)


def setup_render(sc, w, h, samples, transparent):
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = samples
    sc.eevee.use_shadows = True
    sc.eevee.shadow_ray_count = 1
    sc.eevee.shadow_step_count = 4
    sc.eevee.use_raytracing = False
    sc.eevee.use_fast_gi = True
    sc.eevee.fast_gi_distance = 0.6
    sc.render.use_motion_blur = False
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.render.film_transparent = transparent
    sc.render.filter_size = 1.2
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = -0.45
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    sc.render.image_settings.compression = 15
    w_ = bpy.data.worlds.new("world")
    sc.world = w_
    bg = w_.node_tree.nodes["Background"]
    bg.inputs[0].default_value = L.srgb(L.BG)
    bg.inputs[1].default_value = 0.6
    try:  # Glow fuer Emission (wie in der alten Engine)
        ng = bpy.data.node_groups.new("comp", "CompositorNodeTree")
        sc.compositing_node_group = ng
        rl = ng.nodes.new("CompositorNodeRLayers")
        g = ng.nodes.new("CompositorNodeGlare")
        g.inputs["Type"].default_value = "Bloom"
        g.inputs["Quality"].default_value = "Medium"
        g.inputs["Threshold"].default_value = 0.95
        g.inputs["Strength"].default_value = 0.45
        g.inputs["Size"].default_value = 0.5
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        out = ng.nodes.new("NodeGroupOutput")
        ng.links.new(rl.outputs["Image"], g.inputs["Image"])
        ng.links.new(g.outputs["Image"], out.inputs[0])
        sc.render.use_compositing = True
    except Exception as e:  # noqa: BLE001
        print("WARN Compositor:", e)


def camera(sc, pos, tgt, lens):
    cd = bpy.data.cameras.new("cam")
    cd.sensor_fit = "VERTICAL"
    cd.sensor_height = SENSOR
    cd.lens = lens
    cd.clip_start = 0.05
    cd.clip_end = 80
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.rotation_mode = "QUATERNION"
    cam.location = pos
    cam.rotation_quaternion = (Vector(tgt) - Vector(pos)).normalized().to_track_quat("-Z", "Y")
    bpy.context.view_layer.update()
    return cam


def project(sc, cam, p):
    v = world_to_camera_view(sc, cam, Vector(p))
    return [round(v.x * sc.render.resolution_x, 2), round((1 - v.y) * sc.render.resolution_y, 2), round(v.z, 4)]


def ppm_at(sc, cam, p):
    a, b = project(sc, cam, p), project(sc, cam, Vector(p) + Vector((0, 0, 1)))
    return round(math.hypot(a[0] - b[0], a[1] - b[1]), 2)


def clip_lights(coll):
    """Neutrales 3-Punkt-Licht (warmes Key, kuehles Fill, violettes Rim) wie in den Sets."""
    for name, kind, e, col, pos, size in (("key", "AREA", 420, "#FFD6A0", (-2.6, -3.2, 4.2), 2.6),
                                          ("fill", "AREA", 110, "#9DB2FF", (3.2, -2.8, 1.8), 3.0),
                                          ("rim", "AREA", 340, L.VIOLET, (1.6, 2.0, 3.6), 1.6),
                                          ("rim2", "AREA", 230, L.TURQ, (-1.8, 1.8, 3.2), 1.4)):
        L.light(f"clip_{name}", kind, e, col, pos, L.look_rot(pos, (0, 0.2, 1.6)), size=size, coll=coll,
                shadow=name == "key")


# ------------------------------------------------------------------ Clips
def synth_speech(n, seed):
    """Kuenstliche Lautstaerke/Equalizer-Kurven fuer Bytes Sprech-Loop (Silben ~5 Hz)."""
    nz = [anim.Noise(seed + k, 3, 0.9) for k in range(6)]
    amp, eq = [], []
    for f in range(n):
        t = f / FPS
        syl = 0.5 + 0.5 * math.sin(2 * math.pi * 4.8 * t + 1.3 * math.sin(2 * math.pi * 0.8 * t))
        amp.append(max(0.15, min(1.0, 0.35 + 0.55 * syl + 0.15 * nz[0](t))))
        eq.append([max(0.05, min(1.0, 0.55 + 0.45 * nz[k + 1](t) * (0.6 + 0.4 * syl))) for k in range(5)])
    return {"f0": 0, "amp": amp, "eq": eq, "words": []}


def build_clip(name, viseme=None):
    who, kind = CLIPS[name]
    sc = bpy.context.scene
    coll = sc.collection
    T = anim.Tracks(FPS)
    n_in = IN_LEN.get(kind, 0)
    N = n_in + LOOP
    clip_lights(coll)
    fw, fh, cz = FRAME_M[who]
    W_, H_ = int(round(fw * PPM / 2) * 2), int(round(fh * PPM / 2) * 2)
    lens = PPM * SENSOR * CAM_DIST / H_
    cam = camera(sc, (0, -CAM_DIST, cz), (0, 0, cz), lens)
    info = {"name": name, "who": who, "kind": kind, "fps": FPS, "n_in": n_in, "n_loop": LOOP,
            "size": [W_, H_], "ppm": PPM}
    if who == "kalle":
        k = C.Kalle(coll)
        k.cloth.scale = (0, 0, 0)
        C.kalle_idle(T, k, 0, N - 1, seed=7)
        speaking = viseme is not None
        if speaking:
            s = VISEMES[viseme]
            T.set(k.mouth, "scale", lambda f: (1 + 0.15 * (s - 0.18), 1, s), 0, N)
            T.add(k.mouth, "location", lambda f: (0, 0, -0.03 * (s - 0.18)), 0, N)
        if kind != "neutral":
            C.kalle_react(T, k, kind, REACT_F, hold=10 ** 5, speaking=speaking)
        if kind == "jubel":     # Loop lebt: kleines Wippen mit Periode 25 Frames (geht in 75 auf)
            T.add(k.body, "location", lambda f: (0, 0, 0.03 * max(0.0, math.sin(2 * math.pi * f / 25)) *
                                                 anim.window(f, n_in - 4, 10 ** 6, 8, 1)), n_in - 4, N)
        T.bake(0, N - 1, loop_frames=CLOSE, loop_start=n_in)
        info["mouth_obj"] = k.mouth.name
        return sc, cam, info, k
    b = C.Byte(coll, light_energy=26.0)
    C.byte_idle(T, b, 0, N - 1, seed=3)
    C.byte_blinks(T, b, 0, N - 1, seed=11)
    C.antenna_spring(T, b, 2, N - 1)
    C.byte_face(T, b, [(0, "neutral")], 0, N - 1)
    if kind == "sprechen":
        C.byte_speak(T, b, synth_speech(N, 5), 0, N - 1)
    T.bake(0, N - 1, loop_frames=CLOSE, loop_start=n_in)
    return sc, cam, info, b


def render_clip(name, outdir, samples, viseme=None):
    sc, cam, info, ch = build_clip(name, viseme)
    W_, H_ = info["size"]
    setup_render(sc, W_, H_, samples, transparent=True)
    sc.frame_set(0)
    info["anchor"] = project(sc, cam, (0, 0, 0))      # Kalle: Fusspunkt, Byte: Koerpermitte
    os.makedirs(outdir, exist_ok=True)
    frames = [("in", i, i) for i in range(info["n_in"])] + [("loop", i, info["n_in"] + i) for i in range(LOOP)]
    if viseme is None:
        for part, i, f in frames:
            p = os.path.join(outdir, f"{part}_{i:04d}.png")
            if os.path.exists(p):
                continue
            sc.frame_set(f)
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
        with open(os.path.join(outdir, "meta.json"), "w") as fh:
            json.dump(info, fh, indent=1)
        return
    # Mund-Ausschnitt: Region um den Mund (je Frame aus der Projektion), Border-Render
    mouth = bpy.data.objects[info["mouth_obj"]]
    bw, bh = int(0.62 * PPM) // 2 * 2, int(0.42 * PPM) // 2 * 2
    sc.render.use_border = True
    sc.render.use_crop_to_border = True
    boxes = {}
    vdir = os.path.join(outdir, f"mund_{viseme}")
    os.makedirs(vdir, exist_ok=True)
    for part, i, f in frames:
        sc.frame_set(f)
        x, y, _ = project(sc, cam, mouth.matrix_world.translation)
        x0 = int(min(max(0, round(x - bw / 2)), W_ - bw))
        y0 = int(min(max(0, round(y - bh * 0.45)), H_ - bh))
        boxes.setdefault(part, []).append([x0, y0])
        p = os.path.join(vdir, f"{part}_{i:04d}.png")
        if os.path.exists(p):
            continue
        sc.render.border_min_x, sc.render.border_max_x = x0 / W_, (x0 + bw) / W_
        sc.render.border_max_y, sc.render.border_min_y = 1 - y0 / H_, 1 - (y0 + bh) / H_
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
    with open(os.path.join(vdir, "boxes.json"), "w") as fh:
        json.dump({"size": [bw, bh], "boxes": boxes}, fh)


# ------------------------------------------------------------------ Plates
def render_plate(name, outdir, samples):
    sc = bpy.context.scene
    coll = sc.collection
    st = {"theke": S.build_theke, "buero": S.build_buero, "studio": S.build_studio}[name](coll)
    o = st.o
    cam = camera(sc, o + Vector((0.25, -3.5, 2.2)), o + Vector((0.1, 0.2, 1.95)), PLATE_LENS)
    setup_render(sc, PLATE_W, PLATE_H, samples, transparent=False)
    sc.frame_set(0)
    bpy.context.view_layer.update()
    os.makedirs(outdir, exist_ok=True)
    # andere Sets liegen weit weg; Lichter mit Energie 0 aus
    meta = {"name": name, "size": [PLATE_W, PLATE_H], "lens": PLATE_LENS, "out_size": [1080, 1920],
            "kalle": {"anchor": project(sc, cam, st.kalle), "ppm": ppm_at(sc, cam, st.kalle)},
            "byte": {"anchor": project(sc, cam, st.byte), "ppm": ppm_at(sc, cam, st.byte)}}
    scr = st.objs.get("screen")
    if scr is not None:
        disp = bpy.data.objects["screen_display"]
        mw = disp.matrix_world
        hw, hd = 3.25 / 2, 1.85 / 2
        corners = [mw @ Vector((sx * hw, -0.011, sz * hd)) for sx, sz in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
        meta["screen"] = [project(sc, cam, c)[:2] for c in corners]     # oben links, oben rechts, unten rechts, unten links
    # Vordergrund = alles, was komplett vor Kalle liegt (Theke, Schreibtisch ...)
    ky = st.kalle.y
    fg = []
    for ob in bpy.data.objects:
        if ob.type not in ("MESH", "CURVE", "FONT"):
            continue
        ys = [(ob.matrix_world @ Vector(c)).y for c in ob.bound_box]
        if max(ys) < ky - 0.05 and abs(ob.matrix_world.translation.x - o.x) < 20:
            fg.append(ob)
    meta["foreground"] = sorted(ob.name for ob in fg)
    # 1) Hintergrund (ohne Vordergrund)
    for ob in fg:
        ob.hide_render = True
    sc.render.filepath = os.path.join(outdir, "bg.png")
    bpy.ops.render.render(write_still=True)
    # 2) Vordergrund mit Alpha: Rest ist Holdout, Licht/Schatten bleiben
    if fg:
        for ob in fg:
            ob.hide_render = False
        fgset = set(fg)
        for ob in bpy.data.objects:
            if ob.type in ("MESH", "CURVE", "FONT") and ob not in fgset:
                ob.is_holdout = True
        sc.render.film_transparent = True
        sc.render.image_settings.color_mode = "RGBA"
        sc.render.filepath = os.path.join(outdir, "fg.png")
        bpy.ops.render.render(write_still=True)
    with open(os.path.join(outdir, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    mode, name, outdir, samples = argv[0], argv[1], argv[2], int(argv[3])
    reset()
    if mode == "clip":
        viseme = argv[4] if len(argv) > 4 and argv[4] != "base" else None
        render_clip(name, outdir, samples, viseme)
    elif mode == "plate":
        render_plate(name, outdir, samples)


if __name__ == "__main__":
    main()
