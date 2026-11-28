"""Runs INSIDE Blender:  blender -b -P render_shard.py -- plan.json START_FRAME END_FRAME OUT_DIR
Builds every shot that overlaps [START_FRAME, END_FRAME) and renders those frames as PNGs named by global frame number."""
import sys, os, json, math, random, time, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from rbx.core import *
from rbx import stage, locations, props
from rbx.character import Character

DEFAULT_LOOKS = [
    dict(body='teen', skin='peach', hair='short', hair_color='brown', top='blue', outfit='hoodie', bottom='jeans'),
    dict(body='girl', skin='tan', hair='long', hair_color='darkbrown', top='pink', outfit='tee', bottom='navy'),
    dict(body='man', skin='light', hair='short', hair_color='black', top='red', outfit='jacket', top2='white', bottom='darkgrey'),
    dict(body='woman', skin='brown', hair='bun', hair_color='black', top='teal', outfit='dress', bottom='teal'),
    dict(body='kid', skin='peach', hair='messy', hair_color='ginger', top='yellow', pattern='stripes', top2='white', outfit='tee', bottom='khaki'),
    dict(body='old', skin='pale', hair='short', hair_color='white', top='green', pattern='knit', outfit='jacket', top2='cream', bottom='brown', acc='glasses'),
]

def spec_for(name, cast):
    if name in cast: return cast[name]
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    return dict(DEFAULT_LOOKS[h % len(DEFAULT_LOOKS)])

def hfov_half(dist, lens):  # half visible width at distance
    v = 2 * math.atan(12.0 / lens); return dist * math.tan(v / 2) * 9 / 16

def build_shot(plan, shot, out_dir, f_from, f_to):
    W, H, fps = plan['width'], plan['height'], plan['fps']
    sc = reset_scene()
    stage.setup_render(sc, W, H, fps, samples=plan.get('samples', 16))
    tod = shot.get('tod', 'day'); loc = shot['loc']
    stage.build_world(sc, tod)
    rng = random.Random(f"{plan.get('seed', 1)}-{loc}-{tod}")
    builder = locations.REGISTRY.get(locations.ALIASES.get(loc, loc), locations.street)
    info = builder(sc, tod, rng)
    cs = info.get('cam_scale', 1.0)
    srng = random.Random(shot['id'] * 7919 + plan.get('seed', 1))
    cam, tgt = stage.make_camera(sc, W, H)
    fs, fe = shot['start_f'], shot['end_f']      # absolute frames [fs, fe)
    last = fe - 1
    kind = shot['cam']; move = shot.get('move', 'push')
    n = len(shot['chars'])
    ct = stage.CAM_TYPES.get(kind, stage.CAM_TYPES['medium'])
    # ---- characters
    chars = []
    spacing = {'wide': 5.2, 'establish': 6.0, 'medium': 3.5, 'low': 3.5, 'high': 4.5, 'over': 3.4, 'dutch': 3.5, 'closeup': 3.0, 'close': 3.0, 'extreme': 3.0, 'insert': 3.4}.get(kind, 3.5)
    focus_idx = 0
    for i, c in enumerate(shot['chars']):
        if c.get('focus'): focus_idx = i
    insert_only = (kind == 'insert' and shot.get('props'))
    for i, c in enumerate(shot['chars']):
        ch = Character(f"{c['name']}_{i}", spec_for(c['name'], plan.get('cast', {})), os.path.join(out_dir, '_faces'))
        x = (i - (n - 1) / 2) * spacing + (-1.0 if shot.get('props') and n == 1 and not insert_only else 0.0)
        y = 0.0 + (0.35 if i % 2 else 0.0) * 1.0
        yaw = -0.30 * (x / max(spacing, 1)) * (1 if n > 1 else 0) + (srng.uniform(-0.15, 0.15) if n == 1 else 0)
        act = c.get('action', 'idle')
        path = None
        if act in ('walk', 'run', 'sneak', 'walk_l', 'run_l', 'approach', 'leave'):
            dur = (fe - fs) / fps; sp = 4.5 if act.startswith('walk') or act in ('approach', 'leave') else 8.5
            d = min(sp * dur, 16.0)
            if act in ('walk', 'run', 'sneak'): path = ((x - d / 2, y), (x + d / 2, y)); yaw = math.pi / 2
            elif act in ('walk_l', 'run_l'): path = ((x + d / 2, y), (x - d / 2, y)); yaw = -math.pi / 2
            elif act == 'approach': path = ((x, y + d * 0.8), (x, y - d * 0.35)); yaw = math.pi
            else: path = ((x, y), (x, y + d)); yaw = 0.0
            if act in ('walk_l', 'run_l'): base = 'walk' if act == 'walk_l' else 'run'
            elif act == 'approach' or act == 'leave': base = 'walk'
            else: base = act
        else: base = act
        ch.place(x, y, yaw)
        # expression timeline (absolute frames)
        expr = c.get('expr', 'neutral'); exprs = c.get('exprs') or [expr]
        tl = []
        for k, e in enumerate(exprs): tl.append((fs + int((fe - fs) * k / len(exprs)), e))
        ch.set_expression_timeline(tl, fps)
        # keep root keyed through animate
        if path: ch.root.location = (path[0][0], path[0][1], 0)
        ch.animate(base, fs, last, fps, path=path, intensity=1.0, rng=srng)
        chars.append((ch, path, base))
    # ---- props
    prop_objs = []
    pcount = len(shot.get('props', []))
    for j, pdef in enumerate(shot.get('props', [])):
        kindp = pdef['kind']; fn = props.REGISTRY.get(kindp)
        if not fn: continue
        po = fn(f'P{j}_{kindp}', srng, pdef.get('color'))
        big = kindp in props.BIG
        if kind == 'insert':
            px, py, sc_ = (0.0 + (j - (pcount - 1) / 2) * 5.0, 0.0, 1.0 if big else 2.1)
        else:
            half = hfov_half(ct['dist'] * (cs if info.get('indoor') else 1.0), ct['lens'])
            side = -1 if j % 2 == 0 else 1
            px = side * (half * 0.78 + (1.0 if big else 0.0)) * (1.0 if n else 0.0) if n else 0.0
            py = 2.2 if big else -1.6
            sc_ = 0.85 if big else 1.4
            if n == 0: px = (j - (pcount - 1) / 2) * 6.0; py = 0.0
        po.location = (px, py, 0.0); po.rotation_euler = (0, 0, srng.uniform(-0.2, 0.2) if not big else 0.0); po.scale = (sc_, sc_, sc_)
        # pop-in animation only for objects that appear while the shot is already running
        if pdef.get('at_f') and pdef['at_f'] > fs + 1:
            ap = pdef['at_f']; pop = max(2, int(0.18 * fps))
            key_scale(po, fs, (0.001, 0.001, 0.001)); key_scale(po, ap - 1, (0.001, 0.001, 0.001))
            key_scale(po, ap + pop, (sc_ * 1.12,) * 3); key_scale(po, ap + pop + max(2, int(0.1 * fps)), (sc_,) * 3)
        if kindp in ('dog', 'cat', 'puppy', 'bird'):
            for f in range(fs, fe, 6):
                po.rotation_euler = (0, 0, math.sin((f - fs) / fps * 3) * 0.12); po.keyframe_insert('rotation_euler', frame=f)
        prop_objs.append((po, px, py, sc_))
    # ---- lights extra for night
    if tod in ('night', 'dusk', 'dark') and not info.get('indoor'):
        for ch, _, _ in chars: stage.point_light('fill', (ch.pos.x, ch.pos.y - 6, 7), (200, 215, 255), 500, 1.0)
    elif info.get('indoor'):
        pass
    # ---- camera
    if n:
        ch0, path0, _ = chars[focus_idx]
        if path0: fa, fb = path0[0], path0[1]
        else: fa = fb = (ch0.pos.x, ch0.pos.y)
        # frame all characters horizontally: use centroid for multi-char
        if n > 1 and not path0:
            cx = sum(c_.pos.x for c_, _, _ in chars) / n
            if kind in ('closeup', 'close', 'extreme'): cx = ch0.pos.x
            fa = fb = (cx, 0.0)
        subj_h = ch0.height
    else:
        fa = fb = (0.0, 0.0); subj_h = 5.4
    if kind == 'insert' and prop_objs:
        po, px, py, s_ = prop_objs[0]; fa = fb = (px if len(prop_objs) == 1 else 0.0, py); subj_h = 4.2 * s_ if s_ < 1.5 else 4.2
    old = {k: dict(v) for k, v in stage.CAM_TYPES.items()}
    for kk, v in stage.CAM_TYPES.items(): v['dist'] = v['dist'] * cs
    if n > 1 and kind in ('medium', 'low', 'over', 'dutch') and not path0:  # widen to fit all characters
        stage.CAM_TYPES[kind]['dist'] = max(stage.CAM_TYPES[kind]['dist'], (spacing * (n - 1) + 4.2) / (2 * math.tan(math.radians(29) / 2)) * 1.0)
    if prop_objs and kind in ('medium', 'low', 'over', 'dutch', 'closeup', 'close', 'wide') and n:
        stage.CAM_TYPES[kind]['dist'] = max(stage.CAM_TYPES[kind]['dist'], stage.CAM_TYPES['wide']['dist'] * 0.62 * cs)
    stage.setup_shot_camera(cam, tgt, kind, fa, fb, fs, last, fps, srng, move, side=shot.get('side'), subject_h=subj_h)
    for kk, v in old.items(): stage.CAM_TYPES[kk].update(v)
    # fix linear interpolation on animated stuff only for cam; characters keep bezier
    # ---- render
    sc.frame_start = max(fs, f_from); sc.frame_end = min(last, f_to - 1)
    if sc.frame_end < sc.frame_start: return 0
    sc.render.filepath = os.path.join(out_dir, 'f_')
    bpy.ops.render.render(animation=True)
    return sc.frame_end - sc.frame_start + 1

def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    plan = json.load(open(argv[0])); f0 = int(argv[1]); f1 = int(argv[2]); out = argv[3]
    os.makedirs(out, exist_ok=True)
    only_shot = int(argv[4]) if len(argv) > 4 else None
    t0 = time.time(); done = 0
    for shot in plan['shots']:
        if only_shot is not None and shot['id'] != only_shot: continue
        if shot['end_f'] <= f0 or shot['start_f'] >= f1: continue
        a = time.time()
        try:
            n = build_shot(plan, shot, out, f0, f1)
        except Exception as e:
            import traceback; traceback.print_exc()
            print('SHOT_FAILED', shot['id'], e)
            n = fallback_render(plan, shot, out, f0, f1)
        done += n
        print(f"SHOT {shot['id']} frames={n} t={time.time()-a:.1f}s total={done} elapsed={time.time()-t0:.0f}s", flush=True)
    print('SHARD_DONE', done, flush=True)

def fallback_render(plan, shot, out, f0, f1):
    """If a shot fails to build, render a plain sky + ground shot so the video never has holes."""
    try:
        sc = reset_scene(); stage.setup_render(sc, plan['width'], plan['height'], plan['fps'], samples=8)
        stage.build_world(sc, shot.get('tod', 'day')); locations.ground()
        cam, tgt = stage.make_camera(sc, plan['width'], plan['height']); cam.location = (0, -20, 6); tgt.location = (0, 0, 3)
        sc.frame_start = max(shot['start_f'], f0); sc.frame_end = min(shot['end_f'] - 1, f1 - 1)
        sc.render.filepath = os.path.join(out, 'f_'); bpy.ops.render.render(animation=True)
        return sc.frame_end - sc.frame_start + 1
    except Exception as e:
        print('FALLBACK_FAILED', e); return 0

main()
