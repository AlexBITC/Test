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
import sets as S  # noqa: E402
from anim import ease_in, ease_out, ease_in_out, window, Noise  # noqa: E402

FPS = 30
SAMPLES = int(os.environ.get("EEVEE_SAMPLES", "4"))


# ------------------------------------------------------------------ Grundsetup
def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def setup_render(sc, scale):
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = SAMPLES
    sc.eevee.use_shadows = True
    sc.eevee.shadow_ray_count = 1
    sc.eevee.shadow_step_count = 4
    sc.eevee.shadow_resolution_scale = 0.5
    sc.eevee.use_raytracing = False
    sc.eevee.use_fast_gi = True          # Ambient Occlusion / Nahfeld-GI
    sc.eevee.fast_gi_distance = 0.6
    sc.eevee.use_shadow_jitter_viewport = False
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
    sc.view_settings.exposure = -0.45
    sc.view_settings.gamma = 1.0
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.compression = 15
    w = bpy.data.worlds.new("world")
    sc.world = w
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


# ------------------------------------------------------------------ Kamera
class CamRig:
    """Kamera aus Shot-Funktionen: shot(f) -> (pos, ziel, brennweite). Dazu Handheld-Drift (Seed),
    Punch-ins (3 %, 6 Frames), Shakes und Whip-Pans (8 Frames, Gierwinkel)."""

    def __init__(self, sc, n_frames):
        cd = bpy.data.cameras.new("cam")
        cd.sensor_fit = "VERTICAL"
        cd.sensor_height = 36
        cd.clip_start = 0.05
        cd.clip_end = 80
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = 2.2
        self.cam = bpy.data.objects.new("cam", cd)
        sc.collection.objects.link(self.cam)
        sc.camera = self.cam
        self.cam.rotation_mode = "QUATERNION"
        self.focus = L.empty("cam_focus")
        cd.dof.focus_object = self.focus
        self.n = n_frames
        self.shots = []      # (f0, f1, fn)
        self.punch = []      # frames
        self.shakes = []     # (f, amp, dur)
        self.whips = []      # (frame_boundary, direction)
        self.focus_fn = None
        self.drift = (Noise(101, 3, 0.25), Noise(202, 3, 0.22), Noise(303, 3, 0.2), Noise(404, 2, 0.3))
        self.drift_amp = 1.0
        self._cache = {}

    def add_shot(self, f0, f1, fn):
        self.shots.append((f0, f1, fn))

    def base(self, f):
        for f0, f1, fn in self.shots:
            if f0 <= f < f1:
                return fn(f)
        f0, f1, fn = self.shots[-1] if f >= self.shots[-1][1] else self.shots[0]
        return fn(min(max(f, f0), f1 - 1))

    def state(self, f):
        if f in self._cache:
            return self._cache[f]
        pos, tgt, lens = self.base(f)
        pos, tgt = Vector(pos), Vector(tgt)
        t = f / FPS
        d = self.drift
        a = 0.022 * self.drift_amp
        pos = pos + Vector((a * d[0](t), a * 0.5 * d[1](t), a * d[2](t)))
        tgt = tgt + Vector((a * 0.6 * d[1](t + 3), 0, a * 0.6 * d[0](t + 7)))
        roll = 0.012 * self.drift_amp * d[3](t)
        # Punch-ins (3 %, 6 Frames)
        for pf in self.punch:
            lens *= 1 + 0.03 * window(f, pf - 1, pf + 6, 2, 4)
        # Shakes
        for sf, amp, dur in self.shakes:
            if sf <= f <= sf + dur:
                k = 1 - (f - sf) / dur
                pos = pos + Vector((amp * k * math.sin(f * 2.7), 0, amp * k * math.cos(f * 3.3)))
        fwd = (tgt - pos).normalized()
        q = fwd.to_track_quat("-Z", "Y")
        # Whip-Pans: Gier-Offset um die Hochachse
        yaw = 0.0
        for wb, dirn in self.whips:
            if wb - 4 <= f < wb:
                yaw = dirn * 0.95 * ease_in((f - (wb - 4) + 1) / 4)
            elif wb <= f < wb + 4:
                yaw = -dirn * 0.95 * (1 - ease_out((f - wb + 1) / 4))
        if yaw:
            q = Quaternion((0, 0, 1), -yaw) @ q
        q = q @ Quaternion((0, 0, 1), roll)
        self._cache[f] = (pos, q, lens, tgt)
        return self._cache[f]

    def register(self, T):
        quats = {}
        prev = None
        for f in range(0, self.n):
            p, q, ln, tg = self.state(f)
            if prev is not None and prev.dot(q) < 0:
                q = -q
            quats[f] = q
            prev = q
        T.set(self.cam, "location", lambda f: tuple(self.state(int(f))[0]), 0, self.n - 1)
        T.set(self.cam, "rotation_quaternion", lambda f: tuple(quats[int(min(max(f, 0), self.n - 1))]), 0, self.n - 1)
        T.set(self.cam.data, "lens", lambda f: self.state(int(f))[2], 0, self.n - 1)
        if self.focus_fn:
            T.set(self.focus, "location", lambda f: tuple(self.focus_fn(int(f))), 0, self.n - 1)


# ------------------------------------------------------------------ Welt bauen
class World:
    pass


def build(tl, screen_dir):
    reset()
    sc = bpy.context.scene
    W = World()
    W.tl = tl
    W.sc = sc
    W.n = tl["frames"]
    W.T = anim.Tracks(FPS)
    coll = sc.collection
    W.coll = coll
    W.sets = {"theke": S.build_theke(coll), "buero": S.build_buero(coll),
              "studio": S.build_studio(coll, screen_dir, W.n)}
    W.kalle = C.Kalle(coll)
    W.byte = C.Byte(coll, light_energy=26.0)
    W.helpers = [C.Helper(coll, 1, "scan"), C.Helper(coll, 2, "digits"), C.Helper(coll, 3, "feather")]
    W.cam = CamRig(sc, W.n)
    W.cues = []        # Soundeffekte: (frame, art)
    W.anchors = {}     # Name -> Objekt (fuer Overlay-Projektion)
    W.labels = []      # 3D-verankerte Overlay-Zahlen
    slug = tl["slug"].replace("-", "_")
    try:
        mod = importlib.import_module(f"choreo.{slug}")
    except ModuleNotFoundError:
        mod = importlib.import_module("choreo.generic")
    mod.direct(W)
    W.cam.register(W.T)
    t0 = time.time()
    n = W.T.bake(0, W.n - 1, loop_frames=getattr(W, "loop_frames", 0))
    print(f"[scene] {n} Keys gebacken in {time.time()-t0:.1f}s", flush=True)
    return W


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
    W = build(tl, screen_dir)
    if mode == "frames":
        lst, outdir, scale = argv[2], argv[3], float(argv[4])
        setup_render(W.sc, scale)
        if len(argv) > 5:
            W.sc.eevee.taa_render_samples = int(argv[5])
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
