"""Procedural Roblox-style locations. Characters stand near y=0 facing -Y (camera side).
Every builder returns a dict: {'cam_scale': float, 'indoor': bool}."""
import bpy, math, random
from .core import *
from .stage import point_light, area_light
from . import props

def M(name, color, rough=0.6, kind='plain', **kw): return make_mat(name, color, rough, kind, **kw)
def B(name, size, loc, mat, bevel=0.06, rot=(0, 0, 0), parent=None): return box(name, size, loc, mat, parent, bevel, rot)

HOUSE_WALLS = [(250, 205, 120), (150, 205, 250), (240, 160, 175), (180, 225, 150), (235, 235, 240), (250, 170, 110), (190, 170, 235), (120, 200, 190)]
ROOFS = [(200, 80, 60), (70, 90, 170), (120, 70, 160), (45, 120, 90), (230, 130, 40), (90, 90, 105)]
DOORS = [(80, 60, 200), (200, 80, 60), (60, 150, 90), (240, 190, 60), (60, 60, 70)]

def window_mat(tod, lit=None):
    night = tod in ('night', 'dusk', 'dark')
    lit = night if lit is None else lit
    if lit: return M('win_lit', (255, 214, 120), 0.2, emit=2.6)
    return M('win_day', (150, 205, 245), 0.08, emit=0.15, metal=0.2)

def ground(size=900, kind='grass', color=(96, 170, 78)):
    col2 = shade_c(color, 0.8)
    return plane('ground', (size / 2, size / 2), (0, 0, -0.02), M('ground', color, 0.95, kind, color2=col2, scale=0.35, bump=0.25))

def road_x(y0, y1, tod, lanes_line=True, color=(78, 80, 90), length=700):
    r = B('road', (length, y1 - y0, 0.2), (0, (y0 + y1) / 2, 0.02), M('asph', color, 0.9, 'asphalt', color2=shade_c(color, 0.85), scale=0.5, bump=0.2), 0.0)
    if lanes_line:
        lm = M('lane', (245, 205, 60), 0.6)
        x = -length / 2
        while x < length / 2:
            B('dash', (3.0, 0.35, 0.05), (x, (y0 + y1) / 2, 0.14), lm, 0.0); x += 6.0
    for sy in (y0, y1):
        B('curb', (length, 0.6, 0.4), (0, sy + (0.3 if sy == y0 else -0.3), 0.15), M('curb', (170, 170, 178), 0.8), 0.04)
    return r

def sidewalk(y0, y1, length=700):
    B('sidewalk', (length, y1 - y0, 0.35), (0, (y0 + y1) / 2, 0.1), M('sidewalk', (212, 208, 205), 0.85, 'checker', color2=(200, 196, 194), scale=0.5), 0.0)

def house(x, y, w, d, h, wall, roof, door, tod, rng, front='-y', mailbox=True, lawn=True):
    root = empty(f'house_{x:.0f}_{y:.0f}', (x, y, 0))
    wm = M(f'wall{wall}', wall, 0.8, 'noise', color2=shade_c(wall, 0.92), scale=1.5, bump=0.05)
    B('body', (w, d, h), (0, 0, h / 2), wm, 0.12, parent=root)
    prism_roof('roof', w, d, h * 0.45, (0, 0, h), M(f'roof{roof}', roof, 0.7, 'noise', color2=shade_c(roof, 0.8), scale=2.2, bump=0.3), root, 1.0)
    B('chimney', (1.2, 1.2, 3.0), (w * 0.28, d * 0.15, h + 2.4), M('chim', (150, 85, 70), 0.8, 'brick', color2=(130, 70, 60)), 0.05, parent=root)
    fy = -d / 2 - 0.05
    fr = M('frame', (250, 250, 250), 0.6)
    B('door', (2.0, 0.25, 4.2), (0, fy - 0.03, 2.1), M(f'door{door}', door, 0.6), 0.04, parent=root)
    B('doorfr', (2.7, 0.2, 4.6), (0, fy + 0.02, 2.3), fr, 0.04, parent=root)
    B('step', (3.0, 1.2, 0.3), (0, fy - 0.6, 0.15), M('step', (190, 188, 190), 0.8), 0.04, parent=root)
    for sx in (-1, 1):
        wx = sx * w * 0.3
        B('winfr', (2.5, 0.2, 2.5), (wx, fy + 0.02, h * 0.55), fr, 0.04, parent=root)
        B('win', (2.1, 0.22, 2.1), (wx, fy - 0.03, h * 0.55), window_mat(tod), 0.0, parent=root)
        B('winbar', (0.1, 0.25, 2.1), (wx, fy - 0.05, h * 0.55), fr, 0.0, parent=root); B('winbar2', (2.1, 0.25, 0.1), (wx, fy - 0.05, h * 0.55), fr, 0.0, parent=root)
    if lawn:
        B('lawn', (w + 4, 6.0, 0.15), (0, fy - 3.6, 0.07), M('lawn', (96, 176, 78), 0.95, 'grass', color2=(78, 150, 62), scale=0.6, bump=0.2), 0.0, parent=root)
    if mailbox:
        cyl('mbpost', 0.1, 1.8, (w * 0.5 + 1.2, fy - 5.0, 0), M('post', 'brown', 0.8), root, seg=6)
        B('mbox', (0.8, 1.2, 0.7), (w * 0.5 + 1.2, fy - 5.0, 2.0), M('mbox', (210, 40, 50), 0.5), 0.1, parent=root)
    return root

def skyscraper(x, y, w, d, h, color, tod, rng):
    gm = M(f'glass{color}', color, 0.1, 'windows', color2=shade_c(color, 0.78), scale=0.5 if tod not in ('night', 'dark') else 0.5, metal=0.0)
    root = empty(f'sky_{x:.0f}', (x, y, 0))
    B('tower', (w, d, h), (0, 0, h / 2), gm, 0.2, parent=root)
    B('cap', (w * 0.8, d * 0.8, 1.2), (0, 0, h + 0.6), M('cap', (210, 215, 225), 0.5), 0.1, parent=root)
    if rng.random() < 0.5: cyl('ant', 0.15, 6.0, (0, 0, h + 1.2), M('ant', 'darkgrey', 0.5), root, seg=6)
    return root

def hills(tod, rng, y=300):
    cols = [(104, 178, 98), (88, 160, 92), (118, 188, 108)]
    for i in range(7):
        x = -420 + i * 140 + rng.uniform(-30, 30)
        sphere(f'hill{i}', rng.uniform(70, 110), (x, y + rng.uniform(-30, 60), -18), M('hillm', cols[i % 3], 0.95, 'noise', color2=shade_c(cols[i % 3], 0.9), scale=0.01, bump=0.0), None, scale=(1.6, 1.0, 0.8), seg=18, rings=10)
    for i in range(10):
        x = -450 + i * 100 + rng.uniform(-20, 20); h = rng.uniform(70, 120)
        cyl(f'far{i}', 55, h, (x, y + 150, -20), M('farm', (150, 190, 225) if tod in ('day', 'indoor') else (60, 70, 120), 0.95), None, r2=4, seg=6)

def scatter_trees(rng, xs, ys, count, kinds=('tree',), skip=None, scale=(0.9, 1.3)):
    for i in range(count):
        x = rng.uniform(*xs); y = rng.uniform(*ys)
        if skip and skip(x, y): continue
        k = rng.choice(kinds); o = props.REGISTRY[k](f'{k}{i}', rng, None)
        o.location = (x, y, 0); s = rng.uniform(*scale); o.scale = (s, s, s); o.rotation_euler = (0, 0, rng.uniform(0, 6.28))

def lamp_row(x0, x1, y, step, tod, rng):
    x = x0
    while x <= x1:
        o = props.lamppost(f'lp{x:.0f}', rng); o.location = (x, y, 0)
        if tod in ('night', 'dusk', 'dark'):
            point_light(f'lpl{x:.0f}', (x, y, 8.8), (255, 215, 140), 900, 0.6)
        x += step

# ======================= exterior locations =======================
def street(sc, tod, rng, variant=0, **kw):
    ground(); hills(tod, rng)
    sidewalk(-7, 7); road_x(-30, -9, tod); sidewalk(-38, -30)
    x = -150
    while x < 150:
        w = rng.uniform(13, 17); h = rng.uniform(8, 11)
        house(x, 24, w, 12, h, rng.choice(HOUSE_WALLS), rng.choice(ROOFS), rng.choice(DOORS), tod, rng, mailbox=False); x += w + rng.uniform(3, 6)
    # houses behind first row (fill) and across street, partly visible in wide shots
    scatter_trees(rng, (-120, 120), (11, 15), 16, ('tree',), lambda a, b: abs(a) < 8 and False)
    scatter_trees(rng, (-120, 120), (-50, -42), 12, ('tree',))
    lamp_row(-60, 60, -8.2, 24, tod, rng)
    for i, cx in enumerate((-18, 22)):
        c = props.car(f'car{i}', rng, rng.choice([(220, 60, 60), (60, 120, 220), (240, 200, 60), (250, 250, 250)])); c.location = (cx, -20 + (i * 4 - 2) * 0.5, 0); c.rotation_euler = (0, 0, math.pi / 2)
    return {'cam_scale': 1.0, 'indoor': False}

def city(sc, tod, rng, **kw):
    ground(color=(150, 156, 160), kind='concrete'); 
    sidewalk(-7, 7); road_x(-34, -9, tod, color=(70, 72, 82)); sidewalk(-42, -34)
    # crosswalk
    for i in range(10): B('cw', (0.9, 24, 0.04), (-8 + i * 1.8, -21.5, 0.14), M('cw', (240, 240, 240), 0.7), 0.0)
    cols = [(140, 200, 240), (120, 185, 225), (160, 215, 245), (100, 170, 215), (180, 225, 245)]
    x = -150
    while x < 150:
        w = rng.uniform(12, 20); h = rng.uniform(26, 90)
        skyscraper(x + w / 2, 30 + rng.uniform(0, 10), w, 14, h, rng.choice(cols), tod, rng); x += w + rng.uniform(0.5, 3)
    for i in range(7):
        x = -120 + i * 40 + rng.uniform(-8, 8); skyscraper(x, 85 + rng.uniform(0, 25), rng.uniform(16, 24), 16, rng.uniform(60, 130), rng.choice(cols), tod, rng)
    # shop fronts (low colorful buildings) along sidewalk
    scatter_trees(rng, (-100, 100), (-6, -5.4), 8, ('tree',), scale=(0.55, 0.7))
    lamp_row(-60, 60, -8.2, 20, tod, rng)
    for i, cx in enumerate((-30, 10, 40)):
        c = props.car(f'car{i}', rng, rng.choice([(220, 60, 60), (60, 120, 220), (240, 200, 60), (40, 40, 48)])); c.location = (cx, -26 + (i % 2) * 8, 0); c.rotation_euler = (0, 0, math.pi / 2 * (1 if i % 2 else -1))
    return {'cam_scale': 1.0, 'indoor': False}

def park(sc, tod, rng, **kw):
    ground(); hills(tod, rng, 260)
    B('path', (400, 7, 0.1), (0, 0, 0.04), M('path', (215, 190, 150), 0.9, 'noise', scale=1.5), 0.0)
    scatter_trees(rng, (-100, 100), (14, 80), 40, ('tree', 'tree', 'pine'), None)
    scatter_trees(rng, (-100, 100), (-80, -26), 14, ('tree',), None)
    for x in (-12, 14):
        b = props.bench(f'bench{x}', rng); b.location = (x, 5.5, 0); b.rotation_euler = (0, 0, math.pi)
    # pond
    cyl('pond', 12, 0.1, (26, 22, 0.02), M('pond', (70, 150, 220), 0.1, metal=0.3), None, seg=24)
    # playground slide
    B('slideL', (1.4, 6.0, 0.4), (-30, 18, 2.2), M('sl', (240, 200, 50), 0.4), 0.05, rot=(0.7, 0, 0)); B('slideT', (3, 3, 0.4), (-30, 21.5, 4.4), M('st', (230, 70, 70), 0.5), 0.05)
    for sx in (-1, 1): B('slidel', (0.3, 0.3, 4.4), (-30 + sx * 1.3, 21.6, 2.2), M('sp', (90, 90, 100), 0.5), 0.03)
    lamp_row(-50, 50, 9, 25, tod, rng)
    return {'cam_scale': 1.0, 'indoor': False}

def forest(sc, tod, rng, **kw):
    ground(color=(70, 130, 70)); hills(tod, rng, 280)
    B('path', (400, 5, 0.1), (0, 0, 0.04), M('path', (150, 120, 85), 0.95, 'noise', scale=1.5), 0.0)
    scatter_trees(rng, (-120, 120), (7, 90), 80, ('pine', 'pine', 'tree'), None, (0.9, 1.5))
    scatter_trees(rng, (-120, 120), (-60, -8), 25, ('pine', 'tree'), None, (0.9, 1.4))
    for i in range(6):
        x = rng.uniform(-30, 30); sphere(f'rock{i}', rng.uniform(1.0, 2.2), (x, rng.uniform(4, 16), 0.5), M('rock', (140, 140, 145), 0.9, 'noise', scale=1.0), None, scale=(1, 0.8, 0.7), seg=8, rings=5)
    return {'cam_scale': 1.0, 'indoor': False}

def mountain(sc, tod, rng, **kw):
    ground(color=(120, 150, 100)); 
    for i in range(9):
        x = -300 + i * 75 + rng.uniform(-15, 15); h = rng.uniform(120, 220)
        cyl(f'm{i}', rng.uniform(80, 120), h, (x, 140 + rng.uniform(0, 60), -2), M('mt', (140, 140, 150), 0.95, 'noise', color2=(105, 105, 115), scale=0.03, bump=0.0), None, r2=3, seg=7)
        cyl(f'ms{i}', rng.uniform(22, 32), h * 0.28, (x, 140 + rng.uniform(0, 60) * 0 + 0, h * 0.74), M('snow', (245, 248, 255), 0.7), None, r2=3, seg=7)
    B('trail', (400, 6, 0.1), (0, 0, 0.04), M('trail', (170, 140, 105), 0.95, 'noise', scale=1.0), 0.0)
    scatter_trees(rng, (-100, 100), (10, 60), 24, ('pine',), None, (0.9, 1.4))
    return {'cam_scale': 1.0, 'indoor': False}

def beach(sc, tod, rng, **kw):
    ground(color=(240, 220, 160), kind='noise')
    B('sea', (800, 400, 0.2), (0, 230, 0.1), M('sea', (60, 160, 225), 0.05, metal=0.2, emit=0.2), 0.0)
    B('foam', (800, 3, 0.25), (0, 30, 0.12), M('foam', (240, 250, 255), 0.4), 0.0)
    for i, x in enumerate((-22, 18, 40)):
        p = props.tree(f'palm{i}', rng, (60, 170, 80)); p.location = (x, 14 + i * 3, 0)
    for i, x in enumerate((-10, 12)):
        u = props.umbrella(f'umb{i}', rng, rng.choice([(230, 60, 60), (60, 120, 220)])); u.location = (x, 8, 0)
    return {'cam_scale': 1.0, 'indoor': False}

def house_ext(sc, tod, rng, **kw):
    ground(); hills(tod, rng, 280); road_x(-34, -14, tod); sidewalk(-14, -7)
    house(0, 20, 24, 14, 11, rng.choice(HOUSE_WALLS), rng.choice(ROOFS), rng.choice(DOORS), tod, rng)
    B('path', (4, 20, 0.12), (0, 0, 0.06), M('hp', (210, 205, 200), 0.85), 0.0)
    for x in (-32, 32):
        house(x, 26, 14, 11, 8, rng.choice(HOUSE_WALLS), rng.choice(ROOFS), rng.choice(DOORS), tod, rng, mailbox=False)
    scatter_trees(rng, (-90, 90), (30, 60), 18, ('tree', 'pine'), None)
    for i in range(14): B('fence', (0.4, 0.3, 2.2), (-26 + i * 4, 0.6, 1.1), M('fence', 'white', 0.6), 0.04)
    B('fencer', (56, 0.25, 0.35), (0, 0.6, 1.5), M('fence', 'white', 0.6), 0.03)
    lamp_row(-40, 40, -8.0, 40, tod, rng)
    return {'cam_scale': 1.0, 'indoor': False}

# ======================= interior locations =======================
def room(w=34, d=26, h=13, wall=(235, 215, 185), floor='wood', floor_color=(170, 120, 75), tod='indoor', light=(255, 232, 200), light_power=2600, wall_kind='noise'):
    wm = M('wall', wall, 0.85, wall_kind, color2=shade_c(wall, 0.93), scale=0.5, bump=0.05)
    fm = M('floor', floor_color, 0.5, 'wood' if floor == 'wood' else 'checker', color2=shade_c(floor_color, 0.85), scale=0.6 if floor == 'wood' else 0.7)
    B('floor', (w + 40, d + 40, 0.4), (0, d / 2 - 6, -0.2), fm, 0.0)
    B('back', (w + 2, 0.6, h), (0, d - 6, h / 2), wm, 0.0)
    B('left', (0.6, d + 4, h), (-w / 2, d / 2 - 6, h / 2), wm, 0.0); B('right', (0.6, d + 4, h), (w / 2, d / 2 - 6, h / 2), wm, 0.0)
    B('ceil', (w + 2, d + 4, 0.5), (0, d / 2 - 6, h + 0.25), M('ceil', (245, 245, 248), 0.9), 0.0)
    B('base', (w, 0.3, 0.7), (0, d - 6.2, 0.35), M('bb', 'white', 0.7), 0.0)
    area_light('roomlight', (0, d / 2 - 4, h - 0.8), size=12, power=light_power, color=light, rot=(0, 0, 0))
    return {'cam_scale': 0.62, 'indoor': True, 'back_y': d - 6, 'w': w, 'h': h}

def window_on_wall(x, y, z, w, h, tod, side='back'):
    sky = (150, 205, 245) if tod not in ('night', 'dark') else (30, 40, 90)
    B('winfr', (w + 0.8, 0.5, h + 0.8), (x, y - 0.05, z), M('wf', 'white', 0.6), 0.04)
    B('win', (w, 0.3, h), (x, y - 0.2, z), M('winsky', sky, 0.1, emit=1.6 if tod not in ('night', 'dark') else 0.6), 0.0)
    B('wb1', (0.15, 0.35, h), (x, y - 0.25, z), M('wf', 'white', 0.6), 0.0); B('wb2', (w, 0.35, 0.15), (x, y - 0.25, z), M('wf', 'white', 0.6), 0.0)

def living_room(sc, tod, rng, **kw):
    info = room(wall=(245, 225, 195), floor_color=(165, 115, 70), tod=tod)
    by = info['back_y']
    window_on_wall(-9, by, 6.5, 6.0, 5.0, tod); window_on_wall(9, by, 6.5, 6.0, 5.0, tod)
    s = props.sofa('sofa', rng); s.location = (0, by - 3.0, 0); s.rotation_euler = (0, 0, math.pi)
    t = props.tv('tv', rng); t.location = (-12, by - 1.2, 0)
    bs = props.bookshelf('bs', rng); bs.location = (13, by - 1.2, 0)
    B('rug', (11, 7, 0.08), (0, 3, 0.04), M('rug', (170, 70, 80), 0.95, 'knit', color2=(140, 55, 65), scale=1.0), 0.0)
    pl = props.plant('pl', rng); pl.location = (-15, by - 2, 0)
    ck = props.clock('ck', rng); ck.location = (3.5, by - 0.5, 4.0)
    return info

def bedroom(sc, tod, rng, **kw):
    info = room(wall=(190, 215, 245), floor_color=(170, 125, 85), tod=tod, light=(255, 235, 210), light_power=2000)
    by = info['back_y']
    window_on_wall(10, by, 6.5, 6.0, 5.0, tod)
    b = props.bed('bed', rng, (225, 90, 110)); b.location = (-8, by - 5.5, 0)
    ns = props.table('ns', rng); ns.location = (-1.6, by - 2.0, 0); ns.scale = (0.45, 0.45, 0.55)
    lp = props.lamp('lamp', rng); lp.location = (-1.6, by - 2.0, 1.65)
    cb = props.cabinet('cab', rng); cb.location = (-14, by - 1.2, 0); cb.location = (13, by - 1.5, 0)
    B('rug', (9, 6, 0.08), (3, 4, 0.04), M('rug2', (110, 90, 170), 0.95, 'knit', scale=1.0), 0.0)
    mr = props.mirror('mir', rng); mr.location = (-14.5, by - 0.7, 0)
    return info

def kitchen(sc, tod, rng, **kw):
    info = room(wall=(255, 240, 205), floor='tiles', floor_color=(235, 225, 205), tod=tod, light=(255, 245, 225), light_power=3000)
    by = info['back_y']
    window_on_wall(6, by, 7.0, 6.0, 4.0, tod)
    f = props.fridge('fr', rng); f.location = (-13, by - 2.0, 0)
    B('counter', (18, 2.6, 3.4), (2, by - 1.7, 1.7), M('ct', (230, 215, 190), 0.6), 0.1); B('top', (18.4, 2.8, 0.3), (2, by - 1.7, 3.5), M('ctt', (90, 85, 90), 0.4, 'noise', scale=2), 0.04)
    B('stove', (3.2, 2.4, 0.2), (-3, by - 1.7, 3.7), M('stv', 'black', 0.3), 0.04)
    for k in range(4): B('cup', (4.2, 1.4, 3.0), (-3 + k * 4.4 - 2.2, by - 1.0, 9.2), M('upper', (240, 220, 180), 0.6), 0.08)
    t = props.table('tb', rng); t.location = (2, 4, 0); 
    for sx in (-1, 1): ch = props.chair(f'chr{sx}', rng); ch.location = (2 + sx * 4.2, 4, 0); ch.rotation_euler = (0, 0, math.pi / 2 * -sx)
    return info

def classroom(sc, tod, rng, **kw):
    info = room(w=40, wall=(240, 235, 205), floor='tiles', floor_color=(225, 205, 160), tod=tod, light=(255, 250, 235), light_power=3600)
    by = info['back_y']
    B('board', (14, 0.3, 6.0), (0, by - 0.5, 7.0), M('bd', (40, 90, 70), 0.9), 0.06); B('bfr', (14.6, 0.2, 6.6), (0, by - 0.35, 7.0), M('bfw', (150, 100, 60), 0.6, 'wood'), 0.06)
    B('chalk', (6, 0.3, 0.2), (0, by - 0.7, 3.8), M('ch', 'white', 0.6), 0.0)
    window_on_wall(-14, by, 7.0, 6.0, 5.0, tod); window_on_wall(14, by, 7.0, 6.0, 5.0, tod)
    for rx in range(-3, 4, 2):
        for ry in (3, 8, 13):
            if ry < 6 or abs(rx) > 1:
                d = props.desk(f'ds{rx}{ry}', rng, (200, 160, 110)); d.scale = (0.38, 0.38, 0.55); d.location = (rx * 4.5, ry, 0)
                c = props.chair(f'ch{rx}{ry}', rng); c.location = (rx * 4.5, ry - 1.6, 0); c.rotation_euler = (0, 0, math.pi)
    td = props.desk('tdesk', rng, (150, 100, 60)); td.location = (-12, by - 4, 0); td.scale = (0.8, 0.8, 1.0)
    ck = props.clock('ck', rng); ck.location = (17, by - 0.5, 5.5)
    return info

def shop(sc, tod, rng, variant=0, **kw):
    info = room(w=40, wall=(255, 205, 225), floor='tiles', floor_color=(245, 235, 235), tod=tod, light=(255, 245, 235), light_power=3600)
    by = info['back_y']
    for i in range(3):
        B(f'sh{i}', (11, 1.8, 8.0), (-12 + i * 12, by - 1.4, 4.0), M('shelf', (240, 240, 245), 0.6), 0.08)
        for j in range(4):
            B(f'shs{i}{j}', (10.5, 1.9, 0.2), (-12 + i * 12, by - 1.4, 1.8 + j * 1.9), M('shb', (200, 200, 210), 0.5), 0.02)
            for k in range(6): B(f'prod{i}{j}{k}', (1.2, 1.0, 1.0), (-16.2 + i * 12 + k * 1.7, by - 1.5, 2.5 + j * 1.9), M(f'pr{rng.randint(0, 7)}', rng.choice([(240, 90, 90), (90, 160, 240), (250, 210, 70), (110, 210, 120), (200, 120, 230)]), 0.5), 0.1)
    B('counter', (13, 3.0, 3.6), (8, 6, 1.8), M('ctr', (150, 100, 70), 0.5, 'wood'), 0.1); B('reg', (2.4, 1.8, 1.6), (10, 6, 4.4), M('rg', (50, 50, 60), 0.4), 0.1)
    B('signb', (16, 0.4, 3.0), (0, by - 0.4, 10.5), M('sgn', (240, 90, 140), 0.5), 0.1)
    return info

def office(sc, tod, rng, **kw):
    info = room(w=42, wall=(228, 232, 238), floor='tiles', floor_color=(150, 155, 165), tod=tod, light=(235, 245, 255), light_power=3600, wall_kind='plain')
    by = info['back_y']
    for x in (-14, 0, 14): window_on_wall(x, by, 6.5, 9.0, 7.0, tod)
    for i, x in enumerate((-12, 2, 14)):
        c = props.computer(f'pc{i}', rng); c.location = (x, 5 + (i % 2) * 5, 0); c.scale = (0.9, 0.9, 0.9)
        ch = props.chair(f'oc{i}', rng, (60, 60, 70)); ch.location = (x, 2.8 + (i % 2) * 5, 0); ch.rotation_euler = (0, 0, math.pi)
    pl = props.plant('plant', rng); pl.location = (-18, by - 2, 0)
    return info

def basement(sc, tod, rng, **kw):
    info = room(w=34, wall=(110, 110, 120), floor='tiles', floor_color=(80, 82, 90), tod='dark', light=(255, 200, 120), light_power=500, wall_kind='concrete')
    by = info['back_y']
    cyl('bulbw', 0.03, 3.0, (0, by / 2 - 4, 10.2), M('wire', 'black', 0.5), None, seg=4)
    sphere('bulb', 0.5, (0, by / 2 - 4, 9.7), M('bulb', (255, 220, 140), 0.2, emit=8), None)
    for x in (-10, 8): B('pipe', (0.8, 0.8, 12), (x, by - 0.9, 6), M('pipe', (130, 135, 145), 0.4, metal=0.6), 0.2)
    c = props.chest('chest', rng); c.location = (9, 6, 0)
    for i in range(5): B('crate', (2.5, 2.5, 2.5), (-12 + i * 2.8, by - 2, 1.25 + (i % 2) * 2.5), M('crate', (150, 105, 60), 0.7, 'wood'), 0.06)
    return info

def underwater(sc, tod, rng, **kw):
    ground(color=(210, 190, 140), kind='noise')
    for i in range(40):
        x = rng.uniform(-80, 80); y = rng.uniform(6, 90); c = M('coral', rng.choice([(240, 100, 140), (250, 160, 60), (160, 90, 220)]), 0.6)
        cyl(f'coral{i}', rng.uniform(0.4, 1.0), rng.uniform(2, 6), (x, y, 0), c, None, r2=0.1, seg=6)
    for i in range(14):
        f = sphere(f'fish{i}', 0.9, (rng.uniform(-30, 30), rng.uniform(5, 40), rng.uniform(3, 12)), M('fish', rng.choice([(250, 150, 50), (80, 170, 240), (240, 90, 120)]), 0.4), None, scale=(1.6, 0.5, 0.9))
    return {'cam_scale': 1.0, 'indoor': False}

REGISTRY = {
    'street': street, 'city': city, 'park': park, 'forest': forest, 'mountain': mountain, 'beach': beach, 'house': house_ext,
    'living_room': living_room, 'bedroom': bedroom, 'kitchen': kitchen, 'classroom': classroom, 'shop': shop, 'office': office,
    'basement': basement, 'underwater': underwater,
}
ALIASES = {'school': 'classroom', 'home': 'living_room', 'room': 'bedroom', 'store': 'shop', 'market': 'shop', 'cafe': 'shop', 'downtown': 'city',
           'road': 'street', 'neighborhood': 'street', 'town': 'street', 'garden': 'park', 'woods': 'forest', 'jungle': 'forest', 'sea': 'beach',
           'ocean': 'underwater', 'cellar': 'basement', 'attic': 'basement', 'house_exterior': 'house', 'outside_house': 'house', 'workplace': 'office'}
