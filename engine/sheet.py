"""Kontaktbogen Figuren + Requisiten (Abnahme Stufe A), Workbench wie im Video.
  blender -b --factory-startup --python engine/sheet.py -- <out_dir>
Rendert: Kalle vorn, Kalle 3/4, Byte vorn, alle neuen Requisiten. render.py setzt die Bilder zusammen."""
import math
import os
import sys

ENGINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ENGINE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import characters as C  # noqa: E402
import look as L  # noqa: E402
import props as PR  # noqa: E402
import scene as SC  # noqa: E402


def cam_at(sc, pos, tgt, lens):
    cd = bpy.data.cameras.new("c")
    cd.sensor_fit = "VERTICAL"
    cd.sensor_height = 36
    cd.lens = lens
    o = bpy.data.objects.new("c", cd)
    sc.collection.objects.link(o)
    d = Vector(tgt) - Vector(pos)
    o.location = pos
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = o
    return o


def main():
    out = sys.argv[sys.argv.index("--") + 1]
    os.makedirs(out, exist_ok=True)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    sc = bpy.context.scene
    coll = sc.collection
    SC.ENGINE_NAME = "workbench"
    SC.setup_render(sc, 1.0)
    sc.display.shading.use_dof = False
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1080
    k = C.Kalle(coll, extras=True)
    b = C.Byte(coll, light_energy=26.0)
    b.add_ear_rings()
    b.root.location = (1.4, 0, 2.0)
    floor = L.box("floor", (12, 12, 0.02), L.mat("studio_floor", "#17142C", 0.32), None, (0, 0, -0.01), coll)
    shots = {"kalle_vorn": ((0, -3.4, 1.7), (0, 0, 1.45), 50), "kalle_34": ((-2.4, -2.5, 1.8), (0, 0, 1.5), 50),
             "kalle_kopf": ((0.0, -1.6, 2.15), (0, 0, 2.05), 60), "byte_vorn": ((1.4, -1.2, 2.0), (1.4, 0, 2.0), 50)}
    for name, (p, t, ln) in shots.items():
        cam_at(sc, p, t, ln)
        sc.render.filepath = os.path.join(out, f"{name}.png")
        bpy.ops.render.render(write_still=True)
    # Requisiten in einer Reihe (Kalle/Byte ausblenden)
    k.root.scale = (0, 0, 0)
    b.root.scale = (0, 0, 0)
    X = 10.0
    items = []
    mo = PR.moth(coll, "moth")
    mo.root.scale = (4, 4, 4)
    items.append((mo.root, "Motte (x4)"))
    iv = PR.invoice(coll, "inv")
    iv.stamp.scale = (1, 1, 1)
    items.append((iv.root, "Rechnung + Stempel"))
    st = PR.coin_stack(coll, "coins", 18)
    items.append((st.root, "Münzsäule 18"))
    g = PR.konto_glas(coll, "glas")
    g.fill.scale = (1, 1, 0.6 * 0.58)
    g.top.location = (0, 0, 0.02 + 0.6 * 0.58)
    g.gap.scale = (1, 1, 0.4 * 0.58)
    items.append((g.root, "Kontoglas 60 %"))
    cs = PR.calendar_sheet(coll, "cal")
    cs.scale = (2, 2, 2)
    items.append((cs, "Kalenderblatt (x2)"))
    sw = PR.stopwatch(coll, "sw")
    items.append((sw.root, "Stoppuhr"))
    en = PR.envelope_mail(coll, "env")
    items.append((en.root, "Umschlag"))
    mz = PR.muehlrad_zettel(coll, "mz")
    mz.check.scale = (1, 1, 1)
    mz.root.scale = (2, 2, 2)
    items.append((mz.root, "Mühlrad-Zettel (x2)"))
    vt = PR.vitrine(coll, "vit")
    items.append((vt.root, "Vitrine 20 %"))
    for i, (o, lab) in enumerate(items):
        col, row = i % 3, i // 3
        o.location = (X + (col - 1) * 0.8, 0, 0.9 - row * 0.62 + (0.05 if "Kontoglas" not in lab else -0.25))
        o.rotation_euler = (0, 0, 0) if "Kontoglas" not in lab and "Vitrine" not in lab else (0.25, 0, 0)
        if "Motte" in lab:
            o.rotation_euler = (math.radians(70), 0, 0)
        if "Münz" in lab:
            o.location.z -= 0.1
    cam_at(sc, (X, -4.2, 0.35), (X, 0, 0.35), 50)
    sc.render.filepath = os.path.join(out, "requisiten.png")
    bpy.ops.render.render(write_still=True)
    with open(os.path.join(out, "requisiten.txt"), "w") as fh:
        fh.write("\n".join(lab for _, lab in items))


if __name__ == "__main__":
    main()
