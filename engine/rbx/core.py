"""Core helpers: materials, primitives, keyframes. Z is up, characters face -Y (toward the default camera)."""
import bpy, bmesh, math, random
from mathutils import Vector, Euler

_MATS = {}

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()
    sc = bpy.context.scene
    return sc

def rgb(c):
    """Accept (r,g,b) 0-255, hex string or named color."""
    if isinstance(c, str):
        if c in COLORS: c = COLORS[c]
        elif c.startswith('#'):
            c = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
        else: c = COLORS['grey']
    r, g, b = c[:3]
    f = lambda v: pow(v / 255.0, 2.2)  # sRGB -> linear (approx)
    return (f(r), f(g), f(b), 1.0)

COLORS = {
    'white': (240, 240, 240), 'black': (28, 28, 32), 'grey': (140, 140, 148), 'lightgrey': (200, 200, 205), 'darkgrey': (70, 70, 78),
    'red': (210, 50, 50), 'darkred': (140, 30, 40), 'orange': (240, 140, 40), 'yellow': (245, 205, 50), 'green': (60, 160, 80),
    'darkgreen': (30, 100, 55), 'lime': (140, 200, 60), 'teal': (40, 170, 170), 'blue': (50, 110, 210), 'navy': (30, 50, 110),
    'lightblue': (140, 195, 235), 'purple': (130, 70, 180), 'pink': (240, 130, 175), 'hotpink': (235, 70, 140), 'brown': (110, 70, 45),
    'darkbrown': (60, 38, 28), 'tan': (205, 165, 120), 'beige': (225, 205, 170), 'cream': (245, 235, 205), 'gold': (240, 195, 60),
    'silver': (190, 195, 205), 'blonde': (225, 190, 95), 'ginger': (190, 90, 40), 'jeans': (60, 90, 160), 'khaki': (170, 150, 100),
}
SKINS = {
    'light': (245, 205, 175), 'peach': (238, 188, 150), 'tan': (214, 160, 110), 'brown': (160, 105, 70), 'dark': (105, 68, 48),
    'yellow': (245, 205, 60), 'pale': (250, 225, 205), 'green': (120, 190, 90), 'blue': (110, 170, 230), 'grey': (170, 175, 185),
}

def _node(nt, kind, loc=(0, 0)):
    n = nt.nodes.new(kind); n.location = loc; return n

def make_mat(name, color='grey', rough=0.55, kind='plain', color2=None, scale=1.0, emit=0.0, metal=0.0, alpha=1.0, bump=0.0):
    key = (name, str(color), rough, kind, str(color2), scale, emit, metal, alpha, bump)
    if key in _MATS: return _MATS[key]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = _node(nt, 'ShaderNodeOutputMaterial', (900, 0))
    bsdf = _node(nt, 'ShaderNodeBsdfPrincipled', (600, 0))
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    c1 = rgb(color); c2 = rgb(color2 if color2 is not None else shade_c(color, 0.72))
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    try: bsdf.inputs['Specular IOR Level'].default_value = 0.25
    except Exception:
        try: bsdf.inputs['Specular'].default_value = 0.25
        except Exception: pass
    col_out = None
    tc = _node(nt, 'ShaderNodeTexCoord', (-900, 0))
    mp = _node(nt, 'ShaderNodeMapping', (-700, 0))
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    if kind == 'plain':
        bsdf.inputs['Base Color'].default_value = c1
    else:
        mix = _node(nt, 'ShaderNodeMix', (300, 100)); mix.data_type = 'RGBA'
        mix.inputs['A'].default_value = c1; mix.inputs['B'].default_value = c2
        fac_out = None
        if kind in ('noise', 'grass', 'concrete', 'asphalt', 'dirt', 'knit'):
            t = _node(nt, 'ShaderNodeTexNoise', (-300, 100))
            t.inputs['Scale'].default_value = {'grass': 14, 'concrete': 6, 'asphalt': 22, 'dirt': 9, 'knit': 40, 'noise': 8}.get(kind, 8)
            t.inputs['Detail'].default_value = 6
            nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
            ramp = _node(nt, 'ShaderNodeValToRGB', (0, 100))
            ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[1].position = 0.65
            nt.links.new(t.outputs['Fac'], ramp.inputs['Fac']); fac_out = ramp.outputs['Color']
            if bump > 0 or kind in ('concrete', 'asphalt', 'knit', 'grass'):
                bn = _node(nt, 'ShaderNodeBump', (300, -250)); bn.inputs['Strength'].default_value = bump or 0.25
                nt.links.new(t.outputs['Fac'], bn.inputs['Height']); nt.links.new(bn.outputs['Normal'], bsdf.inputs['Normal'])
        elif kind in ('stripes', 'knitstripes'):
            t = _node(nt, 'ShaderNodeTexWave', (-300, 100)); t.wave_type = 'BANDS'; t.bands_direction = 'Z'
            t.inputs['Scale'].default_value = 3.5 if kind == 'stripes' else 5.0; t.inputs['Distortion'].default_value = 0.0
            nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
            ramp = _node(nt, 'ShaderNodeMath', (0, 100)); ramp.operation = 'GREATER_THAN'; ramp.inputs[1].default_value = 0.5
            nt.links.new(t.outputs['Fac'], ramp.inputs[0]); fac_out = ramp.outputs['Value']
        elif kind == 'wood':
            t = _node(nt, 'ShaderNodeTexWave', (-300, 100)); t.wave_type = 'BANDS'; t.bands_direction = 'X'
            t.inputs['Scale'].default_value = 5; t.inputs['Distortion'].default_value = 4; t.inputs['Detail'].default_value = 3
            nt.links.new(mp.outputs['Vector'], t.inputs['Vector']); fac_out = t.outputs['Fac']
        elif kind == 'plaid':
            a = _node(nt, 'ShaderNodeTexWave', (-300, 200)); a.wave_type = 'BANDS'; a.bands_direction = 'X'; a.inputs['Scale'].default_value = 3.2; a.inputs['Distortion'].default_value = 0
            b = _node(nt, 'ShaderNodeTexWave', (-300, 0)); b.wave_type = 'BANDS'; b.bands_direction = 'Z'; b.inputs['Scale'].default_value = 3.2; b.inputs['Distortion'].default_value = 0
            nt.links.new(mp.outputs['Vector'], a.inputs['Vector']); nt.links.new(mp.outputs['Vector'], b.inputs['Vector'])
            add = _node(nt, 'ShaderNodeMath', (0, 100)); add.operation = 'ADD'
            nt.links.new(a.outputs['Fac'], add.inputs[0]); nt.links.new(b.outputs['Fac'], add.inputs[1]); fac_out = add.outputs['Value']
        elif kind in ('checker', 'tiles'):
            t = _node(nt, 'ShaderNodeTexChecker', (-300, 100)); t.inputs['Scale'].default_value = 2.0 * (1 if kind == 'tiles' else 1)
            nt.links.new(mp.outputs['Vector'], t.inputs['Vector']); fac_out = t.outputs['Fac']
        elif kind == 'brick':
            t = _node(nt, 'ShaderNodeTexBrick', (-300, 100)); t.inputs['Scale'].default_value = 3.0
            t.inputs['Color1'].default_value = c1; t.inputs['Color2'].default_value = c2
            t.inputs['Mortar'].default_value = rgb((205, 200, 190)); t.inputs['Mortar Size'].default_value = 0.025
            nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
            bsdf_in = t.outputs['Color']
        elif kind == 'windows':
            # blue glass grid for skyscrapers
            t = _node(nt, 'ShaderNodeTexBrick', (-300, 100)); t.inputs['Scale'].default_value = 1.0
            t.inputs['Color1'].default_value = c2; t.inputs['Color2'].default_value = c2
            t.inputs['Mortar'].default_value = c1; t.inputs['Mortar Size'].default_value = 0.08
            t.inputs['Brick Width'].default_value = 0.5; t.inputs['Row Height'].default_value = 0.5
            nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
            bsdf_in = t.outputs['Color']
        if kind == 'brick' or kind == 'windows':
            nt.links.new(bsdf_in, bsdf.inputs['Base Color'])
        else:
            nt.links.new(fac_out, mix.inputs['Factor'])
            nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    if emit > 0:
        try:
            bsdf.inputs['Emission Color'].default_value = c1
        except Exception:
            bsdf.inputs['Emission'].default_value = c1
        bsdf.inputs['Emission Strength'].default_value = emit
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        try: m.blend_method = 'BLEND'
        except Exception: pass
    _MATS[key] = m
    return m

def shade_c(c, f):
    if isinstance(c, str): c = COLORS.get(c, COLORS['grey'])
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])

# ---------- primitives ----------
def _link(obj, parent=None):
    if obj.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(obj)
    if parent is not None: obj.parent = parent
    return obj

def empty(name, loc=(0, 0, 0), parent=None, rot=(0, 0, 0)):
    o = bpy.data.objects.new(name, None); o.empty_display_size = 0.2
    o.location = loc; o.rotation_euler = rot
    return _link(o, parent)

def mesh_obj(name, bm, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc; o.rotation_euler = rot
    if mat is not None: o.data.materials.append(mat)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    _link(o, parent)
    return o

def box(name, size, loc=(0, 0, 0), mat=None, parent=None, bevel=0.06, rot=(0, 0, 0), center=True):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = size
    for v in bm.verts: v.co.x *= sx; v.co.y *= sy; v.co.z *= sz
    o = mesh_obj(name, bm, parent, loc, rot, mat)
    if bevel and min(size) > bevel * 2.2:
        md = o.modifiers.new('bv', 'BEVEL'); md.width = min(bevel, min(size) * 0.45); md.segments = 2; md.limit_method = 'ANGLE'
        for p in o.data.polygons: p.use_smooth = True
    return o

def cyl(name, r, h, loc=(0, 0, 0), mat=None, parent=None, seg=14, rot=(0, 0, 0), r2=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=(r if r2 is None else r2), depth=h)
    o = mesh_obj(name, bm, parent, loc, rot, mat, smooth=True)
    return o

def sphere(name, r, loc=(0, 0, 0), mat=None, parent=None, scale=(1, 1, 1), seg=14, rings=8):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    for v in bm.verts: v.co.x *= scale[0]; v.co.y *= scale[1]; v.co.z *= scale[2]
    return mesh_obj(name, bm, parent, loc, (0, 0, 0), mat, smooth=True)

def plane(name, size, loc=(0, 0, 0), mat=None, parent=None, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts: v.co.x *= size[0] * 2; v.co.y *= size[1] * 2
    return mesh_obj(name, bm, parent, loc, rot, mat)

def prism_roof(name, w, d, h, loc, mat, parent=None, overhang=0.8):
    """Gable roof, ridge along X."""
    bm = bmesh.new(); W = w / 2 + overhang; D = d / 2 + overhang
    v = [bm.verts.new(p) for p in [(-W, -D, 0), (W, -D, 0), (W, D, 0), (-W, D, 0), (-W, 0, h), (W, 0, h)]]
    bm.faces.new([v[0], v[1], v[5], v[4]]); bm.faces.new([v[2], v[3], v[4], v[5]])
    bm.faces.new([v[0], v[4], v[3]]); bm.faces.new([v[1], v[2], v[5]]); bm.faces.new([v[0], v[3], v[2], v[1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, parent, loc, (0, 0, 0), mat)

# ---------- animation helpers ----------
def key_rot(o, frame, rot):
    o.rotation_euler = rot
    o.keyframe_insert('rotation_euler', frame=frame)

def key_loc(o, frame, loc):
    o.location = loc
    o.keyframe_insert('location', frame=frame)

def key_scale(o, frame, s):
    o.scale = s if hasattr(s, '__len__') else (s, s, s)
    o.keyframe_insert('scale', frame=frame)

def key_hide(o, frame, hidden):
    o.hide_render = hidden; o.hide_viewport = hidden
    o.keyframe_insert('hide_render', frame=frame); o.keyframe_insert('hide_viewport', frame=frame)

def set_interp(obj, kind='BEZIER'):
    ad = obj.animation_data
    if not ad or not ad.action: return
    for fc in ad.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = kind

def descendants(o):
    out = [o]
    for c in o.children: out += descendants(c)
    return out
