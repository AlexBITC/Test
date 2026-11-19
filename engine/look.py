"""Feste Palette, Materialien und Mesh-Helfer (Low-Poly, Flat Shading)."""
import math

import bpy
import bmesh
from mathutils import Vector


def srgb(h: str, a: float = 1.0):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, a)


# Feste Palette (Vorgabe) – keine anderen grellen Farben
BG = "#1b1830"
TURQ = "#2EE6D6"
GOLD = "#F2B45A"
FLOUR = "#F5F1E8"
RED = "#FF5A5F"
GREEN = "#3DDC84"
YELLOW = "#FFE14D"
# gedeckte Nebenfarben (nicht grell) fuer Haut, Holz, Stoffe
SKIN = "#E7B08A"
SKIN_DARK = "#D9906E"
CHEEK = "#E8977E"
HAIR = "#3A2A22"
PANTS = "#34497A"
SHIRT = "#7C8DB5"
APRON = "#F0EADD"
WOOD = "#9A6A43"
WOOD_DARK = "#5E3E2B"
WOOD_LIGHT = "#C08A55"
NAVY = "#141228"
NAVY2 = "#24204a"
METAL = "#7E8299"
BURLAP = "#D8C19A"
VIOLET = "#6B55C9"
CRUST = "#C98A4B"

_MATS = {}


def mat(name, color, rough=0.6, emit=None, strength=0.0, metallic=0.0, alpha=None, spec=0.35):
    key = name
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(color) if isinstance(color, str) else color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Specular IOR Level"].default_value = spec
    if emit:
        b.inputs["Emission Color"].default_value = srgb(emit) if isinstance(emit, str) else emit
        b.inputs["Emission Strength"].default_value = strength
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
        m.use_transparency_overlap = False
    base = srgb(color) if isinstance(color, str) else color
    if emit and strength >= 1.0:
        # Workbench kennt keine Emission: leuchtende Teile ueber helle Objektfarbe nachbilden
        e = srgb(emit) if isinstance(emit, str) else emit
        k = min(1.0, 0.45 + 0.12 * strength)
        base = tuple(min(1.0, (b * (1 - k) + c * k) * (1.0 + 0.25 * k)) for b, c in zip(base[:3], e[:3])) + (1.0,)
    if alpha is not None:          # Workbench: Transparenz kommt aus dem Alpha der Objektfarbe
        base = tuple(base[:3]) + (alpha,)
    m.diffuse_color = base
    _MATS[key] = m
    return m


def img_mat(name, path, emit=0.9, alpha=True, interp="Linear"):
    """Material mit Bildtextur (Website-Screenshot, Code-Zeile). Leuchtet leicht (Screen-Look);
    in Workbench (Farbmodus TEXTURE) wird das aktive Bild-Node direkt angezeigt."""
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(str(path), check_existing=True)
    t.interpolation = interp
    t.extension = "CLIP"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if emit:
        nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emit
    b.inputs["Roughness"].default_value = 0.6
    if alpha:
        nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
        m.surface_render_method = "BLENDED"
    nt.nodes.active = t
    m.diffuse_color = (1, 1, 1, 1)
    _MATS[name] = m
    return m


def img_size(path):
    im = bpy.data.images.load(str(path), check_existing=True)
    return im.size[0], im.size[1]


def tplane(name, path, height=None, width=None, parent=None, loc=(0, 0, 0), coll=None, emit=0.9, alpha=True,
           origin="center", mat=None):
    """Flache Ebene (XZ, Vorderseite -Y) mit Bild im richtigen Seitenverhaeltnis. origin: center|top|bottom|left."""
    w_px, h_px = img_size(path)
    asp = w_px / max(1, h_px)
    if height is None:
        height = width / asp
    if width is None:
        width = height * asp
    bm = bmesh.new()
    oz = {"center": 0.0, "top": -height / 2, "bottom": height / 2, "left": 0.0}[origin]
    ox = width / 2 if origin == "left" else 0.0
    vs = [bm.verts.new((ox - width / 2, 0, oz - height / 2)), bm.verts.new((ox + width / 2, 0, oz - height / 2)),
          bm.verts.new((ox + width / 2, 0, oz + height / 2)), bm.verts.new((ox - width / 2, 0, oz + height / 2))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new("UVMap")
    for lp, co in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        lp[uv].uv = co
    f.normal_update()
    o = _mesh_obj(name, bm, mat or img_mat(f"img_{path}", path, emit, alpha), parent, loc, coll)
    o["w"], o["h"] = width, height
    return o


def unique_mat(base: bpy.types.Material, name: str):
    m = base.copy()
    m.name = name
    return m


def bsdf(m):
    return m.node_tree.nodes["Principled BSDF"]


def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def empty(name, parent=None, loc=(0, 0, 0), coll=None, rot=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    o.empty_display_size = 0.1
    link(o, coll)
    o.parent = parent
    o.location = loc
    o.rotation_euler = rot
    return o


def _mesh_obj(name, bm, material, parent, loc, coll, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    o = bpy.data.objects.new(name, me)
    if material is not None:
        if isinstance(material, (list, tuple)):
            for mm in material:
                me.materials.append(mm)
        else:
            me.materials.append(material)
    link(o, coll)
    o.parent = parent
    o.location = loc
    return o


def from_bm(name, bm, material=None, parent=None, loc=(0, 0, 0), coll=None, smooth=False):
    return _mesh_obj(name, bm, material, parent, loc, coll, smooth)


def sphere(name, r=1.0, seg=12, rings=8, scale=(1, 1, 1), material=None, parent=None, loc=(0, 0, 0),
           coll=None, smooth=False):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    return _mesh_obj(name, bm, material, parent, loc, coll, smooth)


def ico(name, r=1.0, sub=1, scale=(1, 1, 1), material=None, parent=None, loc=(0, 0, 0), coll=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    return _mesh_obj(name, bm, material, parent, loc, coll)


def box(name, size=(1, 1, 1), material=None, parent=None, loc=(0, 0, 0), coll=None, bevel=0.0, origin="center",
        seg=1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if origin == "bottom":
        bmesh.ops.translate(bm, vec=Vector((0, 0, size[2] / 2)), verts=bm.verts)
    elif origin == "top":
        bmesh.ops.translate(bm, vec=Vector((0, 0, -size[2] / 2)), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=seg, affect="EDGES", profile=0.5)
    return _mesh_obj(name, bm, material, parent, loc, coll)


def cyl(name, r=1.0, depth=1.0, seg=10, material=None, parent=None, loc=(0, 0, 0), coll=None, r2=None,
        origin="center", axis="Z", cap=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r,
                          radius2=r if r2 is None else r2, depth=depth)
    if origin == "bottom":
        bmesh.ops.translate(bm, vec=Vector((0, 0, depth / 2)), verts=bm.verts)
    elif origin == "top":
        bmesh.ops.translate(bm, vec=Vector((0, 0, -depth / 2)), verts=bm.verts)
    if axis == "Y":
        bmesh.ops.rotate(bm, cent=Vector(), matrix=__import__("mathutils").Matrix.Rotation(math.pi / 2, 3, "X"),
                         verts=bm.verts)
    elif axis == "X":
        bmesh.ops.rotate(bm, cent=Vector(), matrix=__import__("mathutils").Matrix.Rotation(math.pi / 2, 3, "Y"),
                         verts=bm.verts)
    return _mesh_obj(name, bm, material, parent, loc, coll)


def torus(name, R=1.0, r=0.1, seg=16, tseg=6, material=None, parent=None, loc=(0, 0, 0), coll=None, axis="Z"):
    bm = bmesh.new()
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(tseg):
            b = 2 * math.pi * j / tseg
            x = (R + r * math.cos(b)) * math.cos(a)
            y = (R + r * math.cos(b)) * math.sin(a)
            z = r * math.sin(b)
            if axis == "Y":
                x, y, z = x, z, y
            elif axis == "X":
                x, y, z = z, y, x
            ring.append(bm.verts.new((x, y, z)))
        verts.append(ring)
    for i in range(seg):
        for j in range(tseg):
            a, b = verts[i][j], verts[(i + 1) % seg][j]
            c, d = verts[(i + 1) % seg][(j + 1) % tseg], verts[i][(j + 1) % tseg]
            bm.faces.new((a, b, c, d))
    return _mesh_obj(name, bm, material, parent, loc, coll)


def text(name, body, size=0.2, material=None, parent=None, loc=(0, 0, 0), coll=None, extrude=0.008,
         align="CENTER", rot=(math.pi / 2, 0, 0), font=None):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = "CENTER"
    if font is not None:
        cu.font = font
    o = bpy.data.objects.new(name, cu)
    if material is not None:
        cu.materials.append(material)
    link(o, coll)
    o.parent = parent
    o.location = loc
    o.rotation_euler = rot
    return o


_FONT = None


def font():
    global _FONT
    if _FONT is None:
        import os
        p = os.path.join(os.path.dirname(__file__), "fonts", "LilitaOne-Regular.ttf")
        _FONT = bpy.data.fonts.load(p)
    return _FONT


def poly_flat(name, pts2d, depth=0.02, material=None, parent=None, loc=(0, 0, 0), coll=None, plane="XZ"):
    """Extrudiertes 2D-Polygon (z. B. Haken, Pfeil). pts2d in der XZ-Ebene, Tiefe in Y."""
    bm = bmesh.new()
    vs = []
    for x, z in pts2d:
        vs.append(bm.verts.new((x, -depth / 2, z) if plane == "XZ" else (x, z, 0)))
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((0, depth, 0)) if plane == "XZ" else Vector((0, 0, depth)), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _mesh_obj(name, bm, material, parent, loc, coll)


def light(name, kind, energy, color, loc, rot=(0, 0, 0), size=1.0, parent=None, coll=None, shadow=True,
          cutoff=None, spot=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = srgb(color)[:3]
    ld.use_shadow = shadow
    if kind == "AREA":
        ld.size = size
        ld.shape = "DISK"
    elif kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = size
    if kind == "SPOT" and spot:
        ld.spot_size = spot
        ld.spot_blend = 0.6
    if cutoff:
        ld.use_custom_distance = True
        ld.cutoff_distance = cutoff
    o = bpy.data.objects.new(name, ld)
    link(o, coll)
    o.parent = parent
    o.location = loc
    o.rotation_euler = rot
    return o


def look_rot(src, dst):
    """Euler-Rotation, mit der -Z (Licht/Kamera) von src nach dst zeigt."""
    d = Vector(dst) - Vector(src)
    return d.to_track_quat("-Z", "Y").to_euler()
