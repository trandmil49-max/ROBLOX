"""Roblox-style blocky characters with swappable face decals and procedural animation."""
import bpy, math, random
from mathutils import Vector
from .core import *

HAIR_COLORS = {'black': (26, 22, 26), 'brown': (92, 58, 36), 'darkbrown': (58, 36, 26), 'blonde': (226, 190, 100), 'ginger': (190, 90, 40),
               'white': (235, 235, 235), 'grey': (150, 150, 155), 'red': (170, 40, 40), 'blue': (60, 90, 200), 'pink': (240, 130, 180),
               'green': (80, 190, 90), 'purple': (140, 80, 190)}

def _c(v, table=None):
    if isinstance(v, (tuple, list)): return tuple(v)
    for t in (table or {}, COLORS):
        if v in t: return t[v]
    return COLORS['grey']

BODIES = {  # scale, head scale, torso width
    'boy': (0.92, 1.05), 'girl': (0.9, 1.05), 'kid': (0.72, 1.18), 'teen': (1.0, 1.0), 'man': (1.1, 0.95), 'woman': (1.0, 0.98),
    'old': (0.98, 1.0), 'granny': (0.95, 1.0), 'baby': (0.5, 1.4), 'big': (1.25, 0.95),
}

class Character:
    def __init__(self, name, spec, face_dir):
        self.name = name; self.spec = spec; self.face_dir = face_dir
        body = spec.get('body', 'teen'); sc, hs = BODIES.get(body, BODIES['teen'])
        self.scale = sc * spec.get('size', 1.0)
        skin = _c(spec.get('skin', 'peach'), SKINS)
        top = _c(spec.get('top', 'blue')); top2 = _c(spec.get('top2', 'white'))
        bottom = _c(spec.get('bottom', 'jeans')); shoes = _c(spec.get('shoes', 'darkgrey'))
        self.skin = skin
        self.root = empty(f'{name}_root')
        self.root.scale = (self.scale,) * 3
        pat = spec.get('pattern', 'plain'); outfit = spec.get('outfit', 'tee')
        mtop = make_mat(f'{name}_top', top, 0.8, {'plain': 'plain', 'stripes': 'stripes', 'plaid': 'plaid', 'knit': 'knit'}.get(pat, 'plain'), color2=top2 if pat != 'plain' else None, scale=1.0, bump=0.3)
        mtop_plain = make_mat(f'{name}_topp', top, 0.8)
        mskin = make_mat(f'{name}_skin', skin, 0.55)
        mbot = make_mat(f'{name}_bot', bottom, 0.8, 'noise' if bottom == COLORS['jeans'] else 'plain', color2=shade_c(bottom, 0.85), scale=3.0, bump=0.1)
        mshoe = make_mat(f'{name}_shoe', shoes, 0.5)
        sleeve_short = spec.get('sleeves', 'long') == 'short' or outfit in ('tee', 'dress_short')
        # pivots
        self.hips = empty(f'{name}_hips', (0, 0, 2.0), self.root)
        self.torso_p = empty(f'{name}_torso', (0, 0, 0), self.hips)     # torso lean pivot
        self.neck = empty(f'{name}_neck', (0, 0, 2.0), self.torso_p)
        self.shL = empty(f'{name}_shL', (-1.5, 0, 1.85), self.torso_p)
        self.shR = empty(f'{name}_shR', (1.5, 0, 1.85), self.torso_p)
        self.hipL = empty(f'{name}_hipL', (-0.5, 0, 0), self.hips)
        self.hipR = empty(f'{name}_hipR', (0.5, 0, 0), self.hips)
        # torso & legs
        box(f'{name}_torsoM', (2.0, 1.0, 2.0), (0, 0, 1.0), mtop, self.torso_p, 0.12)
        if outfit in ('jacket', 'suit'):
            inner = make_mat(f'{name}_inner', top2, 0.8)
            box(f'{name}_inner', (0.9, 0.04, 2.0), (0, -0.51, 1.0), inner, self.torso_p, 0.0)
        if outfit == 'hoodie':
            box(f'{name}_pocket', (1.2, 0.06, 0.6), (0, -0.52, 0.4), make_mat(f'{name}_pk', shade_c(top, 0.85), 0.8), self.torso_p, 0.0)
            box(f'{name}_hood', (1.9, 0.5, 0.35), (0, 0.38, 1.95), mtop, self.torso_p, 0.12)
        if outfit == 'suit':
            if outfit == 'suit':
                box(f'{name}_tie', (0.28, 0.05, 1.3), (0, -0.53, 1.2), make_mat(f'{name}_tie', spec.get('tie', 'red'), 0.6), self.torso_p, 0.0)
        if outfit in ('dress', 'dress_short'):
            skirt = box(f'{name}_skirt', (2.3, 1.3, 1.1 if outfit == 'dress_short' else 1.7), (0, 0, -0.35), mtop, self.hips, 0.14)
        if outfit == 'apron':
            box(f'{name}_apron', (1.7, 0.06, 1.8), (0, -0.52, 0.95), make_mat(f'{name}_apr', 'white', 0.7), self.torso_p, 0.0)
        legcol = mbot
        if outfit in ('dress',): legcol = mskin
        for hp, side in ((self.hipL, 'L'), (self.hipR, 'R')):
            box(f'{name}_leg{side}', (0.98, 1.0, 1.7), (0, 0, -0.85), legcol, hp, 0.1)
            box(f'{name}_shoe{side}', (1.04, 1.25, 0.4), (0, -0.1, -1.82), mshoe, hp, 0.1)
        # arms: sleeve + hand
        for sh, side in ((self.shL, 'L'), (self.shR, 'R')):
            if sleeve_short:
                box(f'{name}_sleeve{side}', (1.02, 1.02, 0.85), (0, 0, -0.43), mtop, sh, 0.1)
                box(f'{name}_hand{side}', (0.96, 0.96, 1.2), (0, 0, -1.4), mskin, sh, 0.08)
            else:
                box(f'{name}_sleeve{side}', (1.02, 1.02, 1.55), (0, 0, -0.78), mtop, sh, 0.1)
                box(f'{name}_hand{side}', (0.96, 0.96, 0.55), (0, 0, -1.8), mskin, sh, 0.08)
        # head
        self.head = empty(f'{name}_head', (0, 0, 0.75 * hs), self.neck)
        hw, hh = 1.75 * hs, 1.55 * hs
        self.hw, self.hh = hw, hh
        box(f'{name}_headM', (hw, hw * 0.92, hh), (0, 0, 0.0), mskin, self.head, 0.32)
        self._hair(name, spec, hw, hh, hs)
        self._extras(name, spec, hw, hh)
        # faces (planes toggled by keyframes)
        self.faces = {}
        self.expr_now = None
        self.height = 5.2 * self.scale + 0.6 * hs
        self.pos = Vector((0, 0, 0)); self.yaw = 0.0

    # ---- hair & accessories
    def _hair(self, name, spec, hw, hh, hs):
        style = spec.get('hair', 'short'); col = _c(spec.get('hair_color', 'brown'), HAIR_COLORS)
        mh = make_mat(f'{name}_hair', col, 0.55, 'noise', color2=shade_c(col, 0.75), scale=4, bump=0.15)
        h = self.head; top = hh / 2; d = hw * 0.92
        if style == 'bald': return
        if style in ('short', 'messy', 'curly', 'old'):
            box(f'{name}_hair1', (hw + 0.14, d + 0.14, 0.5), (0, 0.02, top + 0.05), mh, h, 0.18)
            box(f'{name}_hair2', (hw + 0.14, 0.55, hh * 0.85), (0, d / 2 - 0.1, 0.0), mh, h, 0.2)
            box(f'{name}_hair3', (0.4, d, hh * 0.55), (-hw / 2 - 0.02, 0.05, 0.25), mh, h, 0.12); box(f'{name}_hair4', (0.4, d, hh * 0.55), (hw / 2 + 0.02, 0.05, 0.25), mh, h, 0.12)
            if style == 'messy':
                for i, x in enumerate((-0.6, 0.0, 0.6)): box(f'{name}_tuft{i}', (0.5, 0.6, 0.5), (x, -0.1, top + 0.4), mh, h, 0.12, rot=(0, 0.3 * (i - 1), 0))
        if style == 'spiky':
            box(f'{name}_hair1', (hw + 0.12, d + 0.12, 0.45), (0, 0.02, top + 0.04), mh, h, 0.16)
            box(f'{name}_hair2', (hw + 0.12, 0.5, hh * 0.8), (0, d / 2 - 0.1, 0.0), mh, h, 0.18)
            for i, x in enumerate((-0.7, -0.35, 0, 0.35, 0.7)):
                cone = cyl(f'{name}_spike{i}', 0.28, 0.75 + 0.15 * (i % 2), (x, -0.1, top + 0.55), mh, h, seg=4, r2=0.02)
        if style == 'curly':
            for i in range(9):
                a = i * 0.7; sphere(f'{name}_curl{i}', 0.42, (math.cos(a) * hw * 0.45, math.sin(a) * d * 0.3 + 0.05, top + 0.12 + 0.12 * (i % 2)), mh, h)
        if style == 'afro':
            sphere(f'{name}_afro', hw * 0.78, (0, 0.2, top - 0.25), mh, h, scale=(1.05, 1.0, 0.95))
        if style in ('long', 'bob', 'ponytail', 'bun'):
            box(f'{name}_hair1', (hw + 0.2, d + 0.2, 0.5), (0, 0.02, top + 0.05), mh, h, 0.18)
            box(f'{name}_hair2', (hw + 0.2, 0.6, hh * 0.95 + (2.0 if style == 'long' else 0.4 if style == 'bob' else 0.0)), (0, d / 2 + 0.05, -(1.0 if style == 'long' else 0.2 if style == 'bob' else 0.0)), mh, h, 0.2)
            for sx in (-1, 1):
                box(f'{name}_side{sx}', (0.4, d * 0.9, hh * 0.7 + (1.6 if style == 'long' else 0.2 if style == 'bob' else 0)), (sx * (hw / 2 + 0.03), 0.1, 0.1 - (0.8 if style == 'long' else 0.1 if style == 'bob' else 0)), mh, h, 0.14)
            box(f'{name}_fringe', (hw * 0.85, 0.3, 0.45), (0, -d / 2 - 0.02, top - 0.15), mh, h, 0.1)
            if style == 'ponytail': box(f'{name}_tail', (0.5, 0.5, 1.8), (0, d / 2 + 0.55, -0.4), mh, h, 0.15, rot=(-0.35, 0, 0))
            if style == 'bun': sphere(f'{name}_bun', 0.55, (0, 0.1, top + 0.55), mh, h)
        if style == 'cap':
            cm = make_mat(f'{name}_cap', _c(spec.get('cap_color', 'red')), 0.6)
            box(f'{name}_cap1', (hw + 0.2, d + 0.2, 0.6), (0, 0.02, top + 0.1), cm, h, 0.2)
            box(f'{name}_brim', (hw * 0.8, 0.9, 0.12), (0, -d / 2 - 0.4, top - 0.12), cm, h, 0.04)
            box(f'{name}_hair2', (hw + 0.12, 0.45, hh * 0.7), (0, d / 2 - 0.05, -0.1), mh, h, 0.15)

    def _extras(self, name, spec, hw, hh):
        acc = spec.get('acc', '')
        if 'beanie' in acc:
            bm = make_mat(f'{name}_beanie', _c(spec.get('hat_color', 'red')), 0.9, 'knit', scale=2)
            box(f'{name}_beanie', (hw + 0.28, hw * 0.92 + 0.28, 0.9), (0, 0, hh / 2 + 0.1), bm, self.head, 0.25)
        if 'crown' in acc:
            gm = make_mat(f'{name}_crown', 'gold', 0.25, metal=0.8)
            box(f'{name}_crown', (hw * 0.9, hw * 0.8, 0.5), (0, 0, hh / 2 + 0.55), gm, self.head, 0.05)
        if 'backpack' in acc:
            box(f'{name}_pack', (1.5, 0.8, 1.7), (0, 0.9, 1.0), make_mat(f'{name}_pack', spec.get('pack_color', 'orange'), 0.7), self.torso_p, 0.15)
        if 'headphones' in acc:
            hm = make_mat(f'{name}_hp', 'black', 0.4)
            box(f'{name}_hpband', (hw + 0.5, 0.25, 0.25), (0, 0.0, hh / 2 + 0.2), hm, self.head, 0.08)
            for sx in (-1, 1): box(f'{name}_hpcup{sx}', (0.35, 0.8, 0.85), (sx * (hw / 2 + 0.18), 0.0, 0.0), hm, self.head, 0.1)
        if 'cape' in acc:
            box(f'{name}_cape', (2.2, 0.12, 2.8), (0, 0.6, 0.6), make_mat(f'{name}_cape', 'red', 0.7), self.torso_p, 0.0, rot=(0.08, 0, 0))
        if 'tie' in acc:
            box(f'{name}_tieb', (0.28, 0.05, 1.3), (0, -0.53, 1.2), make_mat(f'{name}_tieb', 'red', 0.6), self.torso_p, 0.0)
        if 'labcoat' in acc:
            box(f'{name}_coat', (2.15, 1.12, 1.9), (0, 0, 0.95), make_mat(f'{name}_coat', 'white', 0.7), self.torso_p, 0.12)

    # ---- faces
    def face_flags(self):
        s = self.spec; acc = s.get('acc', '')
        return dict(glasses='glasses' in acc, mustache='mustache' in acc or 'beard' in acc, lashes=s.get('body') in ('girl', 'woman', 'granny') and s.get('lashes', True), freckles='freckles' in acc)

    def _face_plane(self, expr_key, path):
        fm = bpy.data.materials.new(f'{self.name}_face_{expr_key}'); fm.use_nodes = True
        nt = fm.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial'); b = nt.nodes.new('ShaderNodeBsdfPrincipled')
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(path); tex.extension = 'CLIP'
        nt.links.new(tex.outputs['Color'], b.inputs['Base Color']); nt.links.new(tex.outputs['Alpha'], b.inputs['Alpha'])
        b.inputs['Roughness'].default_value = 0.7
        try: b.inputs['Specular IOR Level'].default_value = 0.0
        except Exception: pass
        nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
        try: fm.blend_method = 'BLEND'
        except Exception: pass
        try: fm.shadow_method = 'NONE'
        except Exception: pass
        sz = self.hw * 0.9
        pl = plane(f'{self.name}_face_{expr_key}', (sz / 2, sz / 2), (0, -(self.hw * 0.92) / 2 - 0.03, 0.02), fm, self.head, rot=(math.pi / 2, 0, 0))
        pl.data.uv_layers.new() if not pl.data.uv_layers else None
        # grid primitive has UVs; flip handled by rotation
        return pl

    def set_expression_timeline(self, timeline, fps):
        """timeline: list of (frame, expr) sorted by frame. Creates planes lazily and toggles visibility."""
        import os
        from engine_faces import ensure_face
        flags = self.face_flags()
        exprs = {e for _, e in timeline}
        for e in exprs:
            path = ensure_face(self.face_dir, e, **flags)
            self.faces[e] = self._face_plane(e, path)
        for e, pl in self.faces.items():
            first = True
            for (f, e2) in timeline:
                key_hide(pl, f, e2 != e)
            ad = pl.animation_data
            if ad and ad.action:
                for fc in ad.action.fcurves:
                    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

    # ---- placement
    def place(self, x, y, yaw=0.0):
        self.pos = Vector((x, y, 0)); self.yaw = yaw
        self.root.location = (x, y, 0); self.root.rotation_euler = (0, 0, yaw)

    # ---- animation
    def _kp(self, o, f, rot): key_rot(o, f, rot)

    def animate(self, action, f0, f1, fps, path=None, intensity=1.0, rng=None):
        """Insert keyframes for `action` over frames f0..f1. path = ((x0,y0),(x1,y1)) for moving actions."""
        rng = rng or random.Random(1)
        n = max(2, f1 - f0)
        step = 2
        loc0 = self.root.location.copy()
        for f in list(range(f0, f1 + 1, step)) + [f1]:
            t = (f - f0) / fps; u = (f - f0) / max(1, (f1 - f0))
            pose = self._pose(action, t, u, intensity)
            self._apply(pose, f)
            if path:
                (x0, y0), (x1, y1) = path
                key_loc(self.root, f, (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, pose.get('lift', 0.0) * self.scale))
            elif 'lift' in pose or 'sink' in pose:
                key_loc(self.root, f, (loc0.x, loc0.y, (pose.get('lift', 0.0) + pose.get('sink', 0.0)) * self.scale))
            else:
                key_loc(self.root, f, (loc0.x, loc0.y, 0.0))
            if 'yaw' in pose:
                key_rot(self.root, f, (pose.get('roll', 0.0), 0, self.yaw + pose['yaw']))
            else:
                key_rot(self.root, f, (pose.get('roll', 0.0), 0, self.yaw))

    def _apply(self, p, f):
        g = p.get
        key_rot(self.shL, f, (g('shL', 0.0), g('shLy', 0.0), g('shLz', 0.0)))
        key_rot(self.shR, f, (g('shR', 0.0), g('shRy', 0.0), g('shRz', 0.0)))
        key_rot(self.hipL, f, (g('hipL', 0.0), 0, g('hipLz', 0.0)))
        key_rot(self.hipR, f, (g('hipR', 0.0), 0, g('hipRz', 0.0)))
        key_rot(self.head, f, (g('headx', 0.0), g('heady', 0.0), g('headz', 0.0)))
        key_rot(self.torso_p, f, (g('lean', 0.0), g('twist_y', 0.0), g('twist', 0.0)))
        key_loc(self.hips, f, (0, 0, 2.0 + g('hipz', 0.0)))

    def _pose(self, a, t, u, k):
        s = math.sin; c = math.cos; P = math.pi
        if a in ('idle', 'talk', 'stand', 'listen'):
            br = s(t * 2.2) * 0.02
            p = dict(shL=0.04 + br, shR=0.04 - br, shLz=-0.06, shRz=0.06, headx=s(t * 1.7) * 0.03, heady=s(t * 1.1) * 0.04, hipz=s(t * 2.2) * 0.02)
            if a == 'talk':
                p.update(shR=-0.5 + s(t * 6.0) * 0.35 * k, shRz=0.25, headx=s(t * 7.0) * 0.07 * k, heady=s(t * 2.0) * 0.1)
            return p
        if a in ('walk', 'run', 'sneak'):
            sp = {'walk': 7.0, 'run': 11.0, 'sneak': 4.0}[a]; amp = {'walk': 0.65, 'run': 1.0, 'sneak': 0.35}[a] * k
            return dict(shL=s(t * sp) * amp * 1.1, shR=-s(t * sp) * amp * 1.1, hipL=-s(t * sp) * amp, hipR=s(t * sp) * amp, lift=abs(s(t * sp)) * 0.14 * (2 if a == 'run' else 1),
                        lean=0.08 if a == 'run' else 0.0, headx=s(t * sp * 2) * 0.03)
        if a == 'wave':
            return dict(shR=-2.6 + s(t * 9) * 0.1, shRz=0.5 + s(t * 9) * 0.45, shL=0.04, shLz=-0.06, heady=0.1, headz=s(t * 4) * 0.04)
        if a == 'point':
            return dict(shR=-1.45, shRz=0.1, shL=0.04, headz=0.05, lean=0.04)
        if a in ('shock', 'scream'):
            j = min(1.0, t * 6)
            return dict(shL=-2.4 * j, shR=-2.4 * j, shLz=-0.5 * j, shRz=0.5 * j, headx=-0.25 * j, lean=-0.12 * j, hipz=0.12 * j + s(t * 30) * 0.02 * k, lift=0.1 * j)
        if a in ('laugh', 'giggle'):
            return dict(shL=-0.6, shR=-0.6, shLz=-0.3, shRz=0.3, lean=-0.18 + s(t * 14) * 0.08, headx=-0.3 + s(t * 14) * 0.1, hipz=abs(s(t * 14)) * 0.09, lift=abs(s(t * 14)) * 0.12)
        if a in ('cry', 'sob'):
            return dict(shL=-1.9, shR=-1.9, shLz=-0.35, shRz=0.35, headx=0.35 + s(t * 10) * 0.05, lean=0.28 + s(t * 10) * 0.03, hipz=-0.05)
        if a in ('sad', 'sulk'):
            return dict(shL=0.15, shR=0.15, headx=0.45, lean=0.22, hipz=-0.04)
        if a in ('angry', 'stomp'):
            return dict(shL=-0.4 + s(t * 8) * 0.2, shR=-0.4 - s(t * 8) * 0.2, shLz=-0.2, shRz=0.2, headx=0.2, lean=0.12, hipL=abs(s(t * 6)) * 0.5, hipz=-0.03, headz=s(t * 18) * 0.03 * k)
        if a == 'jump':
            h = max(0.0, s(min(1.0, u) * P)) * 2.2
            return dict(shL=-2.8 * min(1, h), shR=-2.8 * min(1, h), shLz=-0.6, shRz=0.6, hipL=-0.4, hipR=-0.4, lift=h)
        if a in ('celebrate', 'cheer'):
            return dict(shL=-2.9 + s(t * 10) * 0.3, shR=-2.9 - s(t * 10) * 0.3, shLz=-0.4, shRz=0.4, lift=abs(s(t * 8)) * 0.9, headx=-0.15)
        if a == 'sit':
            return dict(hipL=-1.55, hipR=-1.55, hipz=-1.55, shL=-0.5, shR=-0.5, headx=0.05, heady=s(t * 1.1) * 0.05)
        if a in ('think', 'ponder'):
            return dict(shR=-2.0, shRz=0.2, shRy=0.2, headx=0.2, heady=s(t * 0.8) * 0.15, headz=0.12)
        if a in ('fall', 'faint'):
            return dict(roll=-min(1.5, t * 3.0), shL=-1.2, shR=-1.2, shLz=-0.5, shRz=0.5, sink=-min(1.4, t * 2.8))
        if a in ('sleep', 'lie'):
            return dict(roll=-1.5, sink=-1.9, headx=0.1)
        if a == 'run_away':
            return self._pose('run', t, u, k)
        if a in ('hug', 'embrace'):
            return dict(shL=-1.2, shR=-1.2, shLz=0.7, shRz=-0.7, headz=0.12, lean=0.06)
        if a in ('shrug',):
            return dict(shL=-0.3, shR=-0.3, shLz=-0.9, shRz=0.9, headz=0.15, hipz=0.04)
        if a in ('shake', 'scared', 'tremble'):
            return dict(shL=-0.8, shR=-0.8, shLz=-0.3, shRz=0.3, headx=0.1, lean=-0.06, hipz=-0.05, lift=0.0, headz=s(t * 40) * 0.05 * k, heady=s(t * 33) * 0.04 * k)
        if a in ('dance',):
            return dict(shL=-2.2 * abs(s(t * 6)), shR=-2.2 * abs(c(t * 6)), shLz=-0.4, shRz=0.4, hipL=s(t * 6) * 0.4, hipR=-s(t * 6) * 0.4, lift=abs(s(t * 6)) * 0.3, yaw=s(t * 3) * 0.4)
        if a in ('eat', 'drink'):
            return dict(shR=-1.8 + s(t * 5) * 0.25, shRz=0.1, headx=0.1 + s(t * 5) * 0.08)
        if a in ('type', 'work'):
            return dict(shL=-1.2 + s(t * 14) * 0.08, shR=-1.2 - s(t * 14) * 0.08, headx=0.18, lean=0.1)
        if a in ('look', 'peek'):
            return dict(heady=s(t * 1.4) * 0.5, headx=0.05, shL=0.04, shR=0.04)
        if a in ('knock',):
            return dict(shR=-1.5 + s(t * 10) * 0.25, shRz=0.1, lean=0.05)
        if a in ('push', 'pull'):
            return dict(shL=-1.5, shR=-1.5, lean=0.25 if a == 'push' else -0.15)
        if a in ('hide',):
            return dict(shL=-1.8, shR=-1.8, shLz=-0.2, shRz=0.2, headx=0.4, lean=0.3, hipz=-0.6, hipL=-0.6, hipR=-0.6)
        return self._pose('idle', t, u, k)
