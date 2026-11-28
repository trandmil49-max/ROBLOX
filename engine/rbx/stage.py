"""Render settings, sky/world, lighting and camera rigs."""
import bpy, math, random
from mathutils import Vector
from .core import *

TOD = {  # sky top, sky horizon, sun color, sun strength, sun elevation(deg), sun azimuth(deg), world strength, exposure
    'day':   dict(top=(70, 150, 245), hor=(190, 225, 255), sun=(255, 244, 225), sstr=3.6, elev=52, azim=-35, wstr=1.15, exp=0.0),
    'dawn':  dict(top=(110, 150, 230), hor=(255, 205, 170), sun=(255, 205, 160), sstr=3.0, elev=14, azim=-50, wstr=0.95, exp=0.0),
    'dusk':  dict(top=(60, 70, 160), hor=(255, 150, 95), sun=(255, 160, 100), sstr=3.2, elev=9, azim=-55, wstr=0.8, exp=0.0),
    'night': dict(top=(14, 18, 52), hor=(46, 52, 110), sun=(150, 175, 255), sstr=0.9, elev=40, azim=-30, wstr=0.5, exp=0.2),
    'overcast': dict(top=(150, 165, 185), hor=(205, 212, 222), sun=(235, 240, 250), sstr=1.4, elev=60, azim=-20, wstr=1.3, exp=0.0),
    'indoor': dict(top=(110, 165, 235), hor=(200, 228, 255), sun=(255, 240, 215), sstr=1.4, elev=45, azim=-30, wstr=0.5, exp=0.0),
    'dark':  dict(top=(8, 8, 20), hor=(25, 22, 45), sun=(120, 140, 220), sstr=0.35, elev=40, azim=-30, wstr=0.25, exp=0.3),
}

def setup_render(sc, w, h, fps, samples=16, preset='final'):
    r = sc.render
    r.resolution_x = w; r.resolution_y = h; r.resolution_percentage = 100
    r.fps = fps
    r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.compression = 15
    ver = bpy.app.version
    eng = 'BLENDER_EEVEE_NEXT' if ver >= (4, 2, 0) else 'BLENDER_EEVEE'
    r.engine = eng
    ee = sc.eevee
    def tryset(o, k, v):
        try: setattr(o, k, v)
        except Exception: pass
    tryset(ee, 'taa_render_samples', samples); tryset(ee, 'taa_samples', samples)
    tryset(ee, 'use_gtao', True); tryset(ee, 'gtao_distance', 1.2); tryset(ee, 'gtao_factor', 1.1)
    tryset(ee, 'use_soft_shadows', True); tryset(ee, 'shadow_cube_size', '1024'); tryset(ee, 'shadow_cascade_size', '2048')
    tryset(ee, 'use_bloom', True); tryset(ee, 'bloom_threshold', 0.9); tryset(ee, 'bloom_intensity', 0.06); tryset(ee, 'bloom_radius', 5.0)
    tryset(ee, 'use_ssr', False); tryset(ee, 'use_shadow_high_bitdepth', True)
    tryset(ee, 'use_raytracing', False)
    vs = sc.view_settings
    try: vs.view_transform = 'Standard'
    except Exception: pass
    try: vs.look = 'None'
    except Exception: pass
    sc.render.film_transparent = False
    sc.render.use_motion_blur = False
    try: sc.eevee.use_motion_blur = False
    except Exception: pass

def build_world(sc, tod='day', cloud=0.55):
    t = TOD.get(tod, TOD['day'])
    w = bpy.data.worlds.new('World'); w.use_nodes = True; sc.world = w
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.15; mr.inputs['From Max'].default_value = 0.85
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
    el = ramp.color_ramp.elements
    el[0].position = 0.12; el[0].color = rgb(shade_c(t['hor'], 0.9)); el[1].position = 1.0; el[1].color = rgb(t['top'])
    mid = el.new(0.2); mid.color = rgb(t['hor'])
    if cloud > 0 and tod in ('day', 'dawn', 'overcast', 'indoor'):
        noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 3.2; noise.inputs['Detail'].default_value = 5
        nt.links.new(tc.outputs['Generated'], noise.inputs['Vector'])
        cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = 0.5 + (0.12 * (1 - cloud)); cr.color_ramp.elements[1].position = 0.7
        nt.links.new(noise.outputs['Fac'], cr.inputs['Fac'])
        up = nt.nodes.new('ShaderNodeMath'); up.operation = 'MULTIPLY'
        zc = nt.nodes.new('ShaderNodeMapRange'); zc.inputs['From Min'].default_value = 0.08; zc.inputs['From Max'].default_value = 0.35
        nt.links.new(sep.outputs['Z'], zc.inputs['Value'])
        nt.links.new(cr.outputs['Color'], up.inputs[0]); nt.links.new(zc.outputs['Result'], up.inputs[1])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
        nt.links.new(up.outputs['Value'], mix.inputs['Factor']); nt.links.new(ramp.outputs['Color'], mix.inputs['A'])
        mix.inputs['B'].default_value = rgb((255, 255, 255) if tod != 'dawn' else (255, 225, 205))
        nt.links.new(mix.outputs['Result'], bg.inputs['Color'])
    else:
        nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = t['wstr']
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    # sun
    ld = bpy.data.lights.new('Sun', 'SUN'); ld.energy = t['sstr']; ld.color = tuple(c / 255 for c in t['sun'])
    ld.angle = math.radians(2.5)
    try: ld.use_contact_shadow = True
    except Exception: pass
    so = bpy.data.objects.new('Sun', ld); sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(90 - t['elev']), 0, math.radians(t['azim']))
    try: sc.view_settings.exposure = t['exp']
    except Exception: pass
    return so

def point_light(name, loc, color=(255, 220, 160), power=800, radius=0.3, parent=None):
    ld = bpy.data.lights.new(name, 'POINT'); ld.energy = power; ld.color = tuple(c / 255 for c in color); ld.shadow_soft_size = radius
    o = bpy.data.objects.new(name, ld); o.location = loc
    bpy.context.scene.collection.objects.link(o)
    if parent: o.parent = parent
    return o

def area_light(name, loc, size=3.0, power=600, color=(255, 235, 200), rot=(0, 0, 0)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = tuple(c / 255 for c in color)
    o = bpy.data.objects.new(name, ld); o.location = loc; o.rotation_euler = rot
    bpy.context.scene.collection.objects.link(o); return o

# ---------------- camera ----------------
CAM_TYPES = {  # distance factor, height factor (relative to subject height), look height fraction, lens (mm, vertical sensor 24)
    'wide':    dict(dist=26, h=6.5, look=0.45, lens=24),
    'establish': dict(dist=40, h=11.0, look=0.35, lens=24),
    'medium':  dict(dist=11.5, h=4.4, look=0.62, lens=26),
    'closeup': dict(dist=6.4, h=4.9, look=0.88, lens=28),
    'close':   dict(dist=6.4, h=4.9, look=0.88, lens=28),
    'extreme': dict(dist=3.9, h=5.0, look=0.92, lens=28),
    'low':     dict(dist=11.0, h=1.4, look=0.7, lens=24),
    'high':    dict(dist=15.0, h=13.0, look=0.4, lens=26),
    'over':    dict(dist=9.0, h=5.6, look=0.65, lens=27),
    'insert':  dict(dist=7.0, h=3.2, look=0.5, lens=30),
    'dutch':   dict(dist=9.0, h=4.6, look=0.7, lens=26),
}

def make_camera(sc, w, h):
    cd = bpy.data.cameras.new('Cam'); cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 24.0; cd.lens = 26
    cd.clip_start = 0.1; cd.clip_end = 600
    co = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(co); sc.camera = co
    tgt = bpy.data.objects.new('CamTarget', None); sc.collection.objects.link(tgt)
    c = co.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    return co, tgt

def setup_shot_camera(cam, tgt, kind, focus_a, focus_b, f0, f1, fps, rng, move='push', side=0.0, subject_h=5.4, orbit=None):
    """focus_a/focus_b: (x, y) subject position at shot start/end. Keys camera + target."""
    ct = CAM_TYPES.get(kind, CAM_TYPES['medium'])
    cam.data.lens = ct['lens']
    cam.constraints['Track To'].enabled = True
    ang = math.radians(side) if side else math.radians(rng.uniform(-18, 18))
    if orbit is not None: ang = math.radians(orbit)
    def pos_for(focus, k):
        fx, fy = focus
        d = ct['dist'] * k
        # camera sits at -Y of subject (yaw rotated by ang)
        cx = fx + math.sin(ang) * d; cy = fy - math.cos(ang) * d
        return (cx, cy, ct['h'] * (0.97 + 0.03 * k) * subject_h / 5.4)
    look_z = ct['look'] * subject_h
    kA = {'push': 1.0, 'pull': 0.9, 'static': 1.0, 'pan': 1.0, 'orbit': 1.0, 'handheld': 1.0}.get(move, 1.0)
    kB = {'push': 0.86, 'pull': 1.0, 'static': 0.99, 'pan': 1.0, 'orbit': 1.0, 'handheld': 1.0}.get(move, 1.0)
    if move == 'pull': kA, kB = 0.86, 1.0
    pa = pos_for(focus_a, kA); pb = pos_for(focus_b, kB)
    if move == 'pan':
        sgn = rng.choice([-1, 1]); pa = (pa[0] - sgn * 1.5, pa[1], pa[2]); pb = (pb[0] + sgn * 1.5, pb[1], pb[2])
    if move == 'orbit':
        sgn = rng.choice([-1, 1]); d = ct['dist']
        pa = (focus_a[0] + math.sin(ang - sgn * 0.18) * d, focus_a[1] - math.cos(ang - sgn * 0.18) * d, pa[2])
        pb = (focus_b[0] + math.sin(ang + sgn * 0.18) * d, focus_b[1] - math.cos(ang + sgn * 0.18) * d, pb[2])
    key_loc(cam, f0, pa); key_loc(cam, f1, pb)
    key_loc(tgt, f0, (focus_a[0], focus_a[1], look_z)); key_loc(tgt, f1, (focus_b[0], focus_b[1], look_z))
    if move == 'handheld':
        n = max(2, (f1 - f0) // 4)
        for i in range(1, n):
            f = f0 + i * (f1 - f0) // n
            u = i / n
            key_loc(cam, f, (pa[0] + (pb[0] - pa[0]) * u + rng.uniform(-0.12, 0.12), pa[1] + (pb[1] - pa[1]) * u, pa[2] + rng.uniform(-0.1, 0.1)))
    if kind == 'dutch':
        pass
    for o in (cam, tgt):
        ad = o.animation_data
        if ad and ad.action:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR' if move in ('push', 'pull', 'pan', 'orbit', 'handheld') else 'LINEAR'
