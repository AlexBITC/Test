"""Baut aus timeline.json die Blender-Szene (Sets, Figuren, Requisiten, Keyframes, Kamera, Beats)
und rendert Frames.

Aufruf (durch render.py):
  blender -b --factory-startup --python engine/scene.py -- <timeline.json> frames <liste.txt> <outdir> <scale>
  blender -b --factory-startup --python engine/scene.py -- <timeline.json> anchors <out.json>
"""
import importlib
import json
import math
import os
import sys
import time

ENGINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ENGINE)

import bpy  # noqa: E402
from mathutils import Vector, Quaternion  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402

import anim  # noqa: E402
import characters as C  # noqa: E402
import look as L  # noqa: E402
import props as PR  # noqa: E402
import build_world as BW  # noqa: E402
from anim import ease_in, ease_out, ease_in_out, window, Noise  # noqa: E402

FPS = 30
SAMPLES = int(os.environ.get("EEVEE_SAMPLES", "4"))


# ------------------------------------------------------------------ Grundsetup
def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


ENGINE_NAME = os.environ.get("RENDER_ENGINE", "eevee").lower()


def setup_render(sc, scale):
    """Render-Engine nach RENDER_ENGINE: eevee (Standard) | cycles (CPU, 16 Samples, Denoiser) |
    workbench (Flat Lighting, Objektfarben/Texturen, Kavitaet)."""
    if ENGINE_NAME == "workbench":
        sc.render.engine = "BLENDER_WORKBENCH"
        sh = sc.display.shading
        sh.light = "FLAT"
        sh.color_type = "TEXTURE"
        sh.show_cavity = True
        sh.cavity_type = "BOTH"
        sh.cavity_ridge_factor = 1.0
        sh.cavity_valley_factor = 1.6
        sh.curvature_ridge_factor = 0.6
        sh.curvature_valley_factor = 1.2
        sh.use_dof = True
        sh.show_object_outline = False
        sc.display.render_aa = "8"
    elif ENGINE_NAME == "cycles":
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.samples = 16
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 4
    else:
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = SAMPLES
        sc.eevee.use_shadows = True
        sc.eevee.shadow_ray_count = 1
        sc.eevee.shadow_step_count = 4
        sc.eevee.shadow_resolution_scale = 0.5
        sc.eevee.use_raytracing = False
        sc.eevee.use_fast_gi = True          # Ambient Occlusion / Nahfeld-GI
        sc.eevee.fast_gi_distance = 0.6
        sc.render.use_motion_blur = True
        sc.render.motion_blur_shutter = 0.5
        sc.eevee.motion_blur_steps = 1
        sc.eevee.motion_blur_max = 48
    sc.render.resolution_x = 1080
    sc.render.resolution_y = 1920
    sc.render.resolution_percentage = int(round(scale * 100))
    sc.render.fps = FPS
    sc.render.film_transparent = False
    sc.render.filter_size = 1.2
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = -0.45 if ENGINE_NAME != "workbench" else 0.0
    sc.view_settings.gamma = 1.0
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.compression = 15
    w = bpy.data.worlds.new("world")
    sc.world = w
    w.color = L.srgb(L.BG)[:3]
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = L.srgb(L.BG)
    bg.inputs[1].default_value = 0.6
    setup_compositor(sc)


def setup_compositor(sc):
    """Glow (Bloom) fuer Emission: Byte, Helfer, Screen, Funken."""
    try:
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


def export_anchors(W, out_path):
    sc = W.sc
    names = list(W.anchors.keys())
    res = {"frames": W.n, "anchors": {k: [] for k in names}, "cues": W.cues, "labels": W.labels,
           "whips": W.cam.whips}
    rx, ry = 1080, 1920
    for f in range(W.n):
        sc.frame_set(f)
        for k in names:
            ob = W.anchors[k]
            p = ob.matrix_world.translation
            v = world_to_camera_view(sc, W.cam.cam, p)
            res["anchors"][k].append([round(v.x * rx, 1), round((1 - v.y) * ry, 1), round(v.z, 3)])
    with open(out_path, "w") as fh:
        json.dump(res, fh)


SET_X = {"theke": 0.0, "buero": 40.0, "studio": 80.0}


def cull(W, f):
    """Blendet fuer diesen Frame alles aus, was nicht beitragen kann: andere Sets,
    Objekte mit Scale 0 (noch nicht aufgepoppt / schon weg), ausgeschaltete Lichter."""
    s = [x for x in W.tl["scenes"] if x["f0"] <= f < x["f1"]] or [W.tl["scenes"][-1]]
    ax = SET_X[s[0]["set"]]
    n = 0
    for o in bpy.data.objects:
        if o.type not in ("MESH", "CURVE", "FONT", "LIGHT"):
            continue
        m = o.matrix_world
        hide = abs(m.translation.x - ax) > 20 or abs(m.determinant()) < 1e-12 or \
            (o.type == "LIGHT" and o.data.energy <= 0.01)
        if o.hide_render != hide:
            o.hide_render = hide
        n += not hide
    return n


def render_frames(W, frames, outdir):
    sc = W.sc
    os.makedirs(outdir, exist_ok=True)
    for f in frames:
        p = os.path.join(outdir, f"{f:05d}.png")
        if os.path.exists(p):
            continue
        sc.frame_set(f)
        cull(W, f)
        sc.render.filepath = p + ".tmp.png"
        t = time.time()
        bpy.ops.render.render(write_still=True)
        os.replace(p + ".tmp.png", p)
        print(f"[scene] Frame {f} {time.time()-t:.1f}s", flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    tl_path, mode = argv[0], argv[1]
    tl = json.load(open(tl_path))
    work = os.path.dirname(tl_path)
    screen_dir = os.path.join(work, "screen")
    W = BW.build(tl, screen_dir)
    if mode == "frames":
        lst, outdir, scale = argv[2], argv[3], float(argv[4])
        setup_render(W.sc, scale)

        frames = [int(x) for x in open(lst).read().split(",") if x.strip()]
        render_frames(W, frames, outdir)
    elif mode == "anchors":
        setup_render(W.sc, 1.0)
        export_anchors(W, argv[2])
    elif mode == "blend":
        setup_render(W.sc, 1.0)
        bpy.ops.wm.save_as_mainfile(filepath=argv[2])


if __name__ == "__main__":
    main()
