"""Procedural Roblox-style props. Each builder returns a root empty; origin on the ground, front toward -Y."""
import bpy, math, random
from .core import *

def M(name, color, rough=0.6, kind='plain', **kw): return make_mat(name, color, rough, kind, **kw)
def B(root, name, size, loc, mat, bevel=0.06, rot=(0, 0, 0)): return box(name, size, loc, mat, root, bevel, rot)

def _root(name): return empty(name)

# ---------------- furniture ----------------
def cabinet(n, rng, color=None, **k):
    r = _root(n); wood = M(n + 'w', color or (150, 95, 55), 0.55, 'wood', color2=(120, 72, 40), scale=0.8)
    B(r, n + 'body', (4.6, 1.8, 7.6), (0, 0, 3.8), wood, 0.12)
    dm = M(n + 'd', (118, 72, 42), 0.5, 'wood', color2=(95, 58, 34), scale=0.8)
    B(r, n + 'dL', (2.1, 0.12, 7.0), (-1.13, -0.95, 3.8), dm, 0.05); B(r, n + 'dR', (2.1, 0.12, 7.0), (1.13, -0.95, 3.8), dm, 0.05)
    g = M(n + 'g', 'gold', 0.25, metal=0.8)
    B(r, n + 'hL', (0.18, 0.2, 1.1), (-0.25, -1.1, 3.8), g, 0.04); B(r, n + 'hR', (0.18, 0.2, 1.1), (0.25, -1.1, 3.8), g, 0.04)
    return r

def desk(n, rng, color=None, **k):
    r = _root(n); wood = M(n + 'w', color or (170, 120, 70), 0.55, 'wood', color2=(140, 95, 55), scale=1.0)
    B(r, n + 'top', (6.0, 2.8, 0.35), (0, 0, 2.6), wood, 0.06)
    for sx in (-1, 1):
        for sy in (-1, 1): B(r, f'{n}leg{sx}{sy}', (0.35, 0.35, 2.5), (sx * 2.7, sy * 1.15, 1.25), wood, 0.04)
    return r

def computer(n, rng, color=None, **k):
    r = desk(n + 'dk', rng); 
    sm = M(n + 's', (40, 60, 90), 0.2, emit=1.4, color2=(60, 120, 200)); frame = M(n + 'f', (30, 30, 36), 0.4)
    B(r, n + 'mon', (3.4, 0.35, 2.3), (0, 0.4, 4.0), frame, 0.08); B(r, n + 'scr', (3.0, 0.05, 1.95), (0, 0.2, 4.0), M(n + 'scr', (90, 170, 255), 0.2, emit=2.2), 0.0)
    B(r, n + 'stand', (0.5, 0.5, 0.8), (0, 0.45, 2.95), frame, 0.05); B(r, n + 'kb', (2.4, 0.9, 0.12), (0, -0.7, 2.83), M(n + 'k', (200, 200, 205), 0.5), 0.04)
    B(r, n + 'tower', (0.9, 1.6, 1.8), (2.2, 0.3, 3.6), M(n + 't', (60, 60, 68), 0.4), 0.08)
    return r

def laptop(n, rng, color=None, **k):
    r = _root(n); b = M(n + 'b', color or (190, 195, 205), 0.35, metal=0.5)
    B(r, n + 'base', (3.2, 2.2, 0.18), (0, 0, 0.1), b, 0.05); B(r, n + 'lid', (3.2, 0.14, 2.2), (0, 1.0, 1.2), b, 0.05, rot=(-0.28, 0, 0))
    B(r, n + 'scr', (2.85, 0.05, 1.85), (0, 0.88, 1.2), M(n + 'sc', (110, 180, 255), 0.2, emit=2.2), 0.0, rot=(-0.28, 0, 0))
    return r

def phone(n, rng, color=None, **k):
    r = _root(n); B(r, n + 'b', (1.4, 0.2, 2.8), (0, 0, 1.4), M(n + 'b', (25, 25, 30), 0.3), 0.12, rot=(-0.15, 0, 0))
    B(r, n + 's', (1.2, 0.04, 2.5), (0, -0.12, 1.42), M(n + 's', (120, 200, 255), 0.2, emit=2.4), 0.0, rot=(-0.15, 0, 0)); return r

def headphones(n, rng, color=None, **k):
    r = _root(n); m = M(n + 'm', color or (20, 20, 24), 0.35); a = M(n + 'a', (230, 60, 70), 0.4)
    for i in range(9):
        t = (i / 8) * math.pi; B(r, f'{n}band{i}', (0.4, 0.4, 0.55), (math.cos(t) * 1.5, 0, 1.7 + math.sin(t) * 1.5), m, 0.05, rot=(0, -t + math.pi / 2, 0))
    for sx in (-1, 1): B(r, f'{n}cup{sx}', (0.8, 1.2, 1.5), (sx * 1.55, 0, 1.7), m, 0.2); B(r, f'{n}pad{sx}', (0.2, 0.95, 1.2), (sx * 1.2, 0, 1.7), a, 0.1)
    return r

def tv(n, rng, color=None, **k):
    r = _root(n); fr = M(n + 'f', (28, 28, 32), 0.4)
    B(r, n + 'stand', (5.5, 1.6, 1.8), (0, 0, 0.9), M(n + 'st', (110, 78, 55), 0.5, 'wood', scale=1.0), 0.08)
    B(r, n + 'tv', (5.0, 0.4, 3.0), (0, 0, 3.3), fr, 0.08); B(r, n + 'sc', (4.6, 0.06, 2.65), (0, -0.2, 3.3), M(n + 'sc', (70, 150, 255), 0.2, emit=2.0, color2=(255, 90, 140), kind='stripes'), 0.0)
    return r

def bed(n, rng, color=None, **k):
    r = _root(n); wood = M(n + 'w', (130, 82, 50), 0.55, 'wood', scale=1.0)
    B(r, n + 'fr', (5.6, 8.2, 1.6), (0, 0, 0.8), wood, 0.1); B(r, n + 'mat', (5.2, 7.8, 0.9), (0, 0, 2.0), M(n + 'm', 'white', 0.9), 0.2)
    B(r, n + 'blk', (5.25, 5.0, 0.55), (0, -1.4, 2.35), M(n + 'b', color or (70, 130, 220), 0.9, 'plaid', color2=(240, 240, 250), scale=0.7), 0.15)
    B(r, n + 'pil', (3.2, 1.6, 0.6), (0, 3.1, 2.7), M(n + 'p', 'white', 0.9), 0.25); B(r, n + 'hd', (5.8, 0.5, 3.6), (0, 4.3, 2.2), wood, 0.1)
    return r

def sofa(n, rng, color=None, **k):
    r = _root(n); m = M(n + 'm', color or (180, 80, 90), 0.85, 'knit', scale=1.0, color2=(150, 60, 70))
    B(r, n + 'base', (7.4, 3.0, 1.6), (0, 0, 0.9), m, 0.2); B(r, n + 'back', (7.4, 0.9, 2.8), (0, 1.35, 2.3), m, 0.2)
    for sx in (-1, 1): B(r, f'{n}arm{sx}', (0.9, 3.0, 2.6), (sx * 3.35, 0, 1.7), m, 0.2)
    for sx in (-1, 1): B(r, f'{n}cu{sx}', (3.0, 2.6, 0.5), (sx * 1.6, -0.1, 1.85), shade_m(n + 'cu', color or (180, 80, 90), 1.12), 0.15)
    return r

def shade_m(name, color, f): return M(name, shade_c(color, f), 0.85)

def table(n, rng, color=None, **k):
    r = _root(n); wood = M(n + 'w', color or (165, 115, 70), 0.55, 'wood', scale=1.0)
    B(r, n + 't', (5.5, 3.5, 0.4), (0, 0, 2.5), wood, 0.08)
    for sx in (-1, 1):
        for sy in (-1, 1): B(r, f'{n}l{sx}{sy}', (0.4, 0.4, 2.4), (sx * 2.4, sy * 1.4, 1.2), wood, 0.05)
    return r

def chair(n, rng, color=None, **k):
    r = _root(n); wood = M(n + 'w', color or (150, 100, 60), 0.55, 'wood', scale=1.2)
    B(r, n + 's', (2.0, 2.0, 0.3), (0, 0, 1.7), wood, 0.06); B(r, n + 'b', (2.0, 0.3, 2.4), (0, 0.9, 2.9), wood, 0.06)
    for sx in (-1, 1):
        for sy in (-1, 1): B(r, f'{n}l{sx}{sy}', (0.25, 0.25, 1.6), (sx * 0.8, sy * 0.8, 0.8), wood, 0.03)
    return r

def lamp(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'p', 0.12, 4.0, (0, 0, 0), M(n + 'p', 'darkgrey', 0.4), r)
    cyl(n + 'sh', 0.9, 1.2, (0, 0, 3.6), M(n + 's', (255, 230, 160), 0.6, emit=1.2), r, r2=0.55); cyl(n + 'b', 0.6, 0.15, (0, 0, 0), M(n + 'b', 'darkgrey', 0.4), r); return r

def door(n, rng, color=None, **k):
    r = _root(n); fr = M(n + 'f', 'white', 0.6); d = M(n + 'd', color or (110, 70, 160), 0.5)
    B(r, n + 'fr', (4.2, 0.6, 7.8), (0, 0.1, 3.9), fr, 0.06); B(r, n + 'd', (3.5, 0.4, 7.2), (0, -0.2, 3.6), d, 0.05)
    B(r, n + 'k', (0.3, 0.3, 0.3), (1.2, -0.55, 3.5), M(n + 'k', 'gold', 0.25, metal=0.8), 0.1); return r

def fridge(n, rng, color=None, **k):
    r = _root(n); m = M(n + 'm', color or (225, 228, 235), 0.35, metal=0.2)
    B(r, n + 'b', (3.6, 3.0, 7.0), (0, 0, 3.5), m, 0.15); B(r, n + 'l', (3.4, 0.05, 0.1), (0, -1.52, 4.6), M(n + 'l', 'darkgrey', 0.5), 0.0)
    B(r, n + 'h1', (0.2, 0.3, 1.6), (1.4, -1.6, 5.8), M(n + 'h', 'silver', 0.3, metal=0.8), 0.05); B(r, n + 'h2', (0.2, 0.3, 1.6), (1.4, -1.6, 3.2), M(n + 'h', 'silver', 0.3, metal=0.8), 0.05); return r

def bookshelf(n, rng, color=None, **k):
    r = _root(n); wood = M(n + 'w', (140, 90, 55), 0.55, 'wood', scale=1.0)
    B(r, n + 'b', (5.0, 1.4, 7.4), (0, 0.3, 3.7), wood, 0.1)
    for i in range(4):
        z = 1.1 + i * 1.75; B(r, f'{n}sh{i}', (4.6, 1.2, 0.15), (0, 0.2, z - 0.8), wood, 0.03)
        x = -2.0
        while x < 2.0:
            w = rng.uniform(0.3, 0.55); hh = rng.uniform(1.0, 1.4); B(r, f'{n}bk{i}_{x:.1f}', (w, 0.9, hh), (x + w / 2, 0.0, z + hh / 2 - 0.72), M(f'{n}bc{rng.randint(0, 6)}', rng.choice(['red', 'blue', 'green', 'orange', 'purple', 'teal', 'yellow']), 0.6), 0.03); x += w + 0.03
    return r

def book(n, rng, color=None, **k):
    r = _root(n); B(r, n + 'c', (1.8, 2.4, 0.35), (0, 0, 0.18), M(n + 'c', color or (190, 50, 60), 0.6), 0.05); B(r, n + 'p', (1.65, 2.25, 0.25), (0.05, 0, 0.2), M(n + 'p', 'cream', 0.8), 0.02); return r

def backpack(n, rng, color=None, **k):
    r = _root(n); m = M(n + 'm', color or (240, 130, 40), 0.7)
    B(r, n + 'b', (2.2, 1.2, 2.6), (0, 0, 1.4), m, 0.2); B(r, n + 'p', (1.7, 0.4, 1.3), (0, -0.7, 1.0), shade_m(n + 'p', color or (240, 130, 40), 0.8), 0.1)
    for sx in (-1, 1): B(r, f'{n}s{sx}', (0.25, 0.15, 1.6), (sx * 0.6, -0.65, 1.7), M(n + 's', 'darkgrey', 0.7), 0.04)
    return r

# ---------------- food ----------------
def pizza(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'b', 1.9, 0.25, (0, 0, 0.13), M(n + 'b', (225, 170, 90), 0.8), r, seg=18)
    cyl(n + 'c', 1.7, 0.1, (0, 0, 0.3), M(n + 'c', (250, 190, 70), 0.7), r, seg=18)
    for i in range(7):
        a = i * 0.9; cyl(f'{n}pp{i}', 0.28, 0.08, (math.cos(a) * 0.9 * (0.4 + (i % 3) * 0.3), math.sin(a) * 0.9 * (0.4 + (i % 3) * 0.3), 0.38), M(n + 'pp', (190, 50, 45), 0.6), r, seg=10)
    return r

def burger(n, rng, color=None, **k):
    r = _root(n); bun = M(n + 'b', (225, 160, 75), 0.7)
    sphere(n + 'top', 1.4, (0, 0, 1.45), bun, r, scale=(1, 1, 0.55)); cyl(n + 'pat', 1.35, 0.35, (0, 0, 0.75), M(n + 'p', (95, 55, 35), 0.8), r, seg=16)
    cyl(n + 'let', 1.5, 0.15, (0, 0, 1.0), M(n + 'l', (80, 190, 70), 0.7), r, seg=16); cyl(n + 'ch', 1.45, 0.12, (0, 0, 1.12), M(n + 'ch', (250, 200, 50), 0.6), r, seg=4)
    sphere(n + 'bot', 1.4, (0, 0, 0.35), bun, r, scale=(1, 1, 0.4)); return r

def cake(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'l1', 2.2, 1.1, (0, 0, 0), M(n + 'l1', color or (250, 170, 200), 0.6), r, seg=20); cyl(n + 'l2', 1.5, 1.0, (0, 0, 1.1), M(n + 'l2', (250, 235, 210), 0.6), r, seg=20)
    for i, x in enumerate((-0.5, 0.0, 0.5)):
        cyl(f'{n}c{i}', 0.08, 0.7, (x, 0, 2.1), M(n + 'cn', 'blue', 0.5), r, seg=6); sphere(f'{n}f{i}', 0.14, (x, 0, 2.9), M(n + 'fl', (255, 200, 50), 0.3, emit=4), r)
    return r

def apple(n, rng, color=None, **k):
    r = _root(n); sphere(n + 'a', 1.0, (0, 0, 1.0), M(n + 'a', color or (210, 40, 40), 0.35), r); cyl(n + 's', 0.06, 0.45, (0, 0, 1.9), M(n + 's', 'brown', 0.7), r, seg=6)
    box(n + 'lf', (0.5, 0.05, 0.3), (0.3, 0, 2.15), M(n + 'lf', 'green', 0.6), r, 0.0, rot=(0, 0.4, 0.4)); return r

def coffee(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'c', 0.85, 1.5, (0, 0, 0), M(n + 'c', color or 'white', 0.35), r, seg=16); cyl(n + 'l', 0.75, 0.05, (0, 0, 1.45), M(n + 'l', (80, 45, 25), 0.3), r, seg=16)
    B(r, n + 'h', (0.15, 0.7, 0.8), (0.95, 0, 0.8), M(n + 'h', 'white', 0.35), 0.05); return r

def money(n, rng, color=None, **k):
    r = _root(n)
    for i in range(3):
        B(r, f'{n}s{i}', (3.2, 1.7, 0.7), (0, 0, 0.36 + i * 0.72), M(n + 'g', (95, 175, 100), 0.6), 0.05, rot=(0, 0, (i - 1) * 0.12))
        B(r, f'{n}b{i}', (0.7, 1.75, 0.74), (0, 0, 0.36 + i * 0.72), M(n + 'bd', (230, 220, 190), 0.6), 0.02, rot=(0, 0, (i - 1) * 0.12))
    return r

def coin(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'c', 1.5, 0.3, (0, 0, 1.5), M(n + 'c', 'gold', 0.25, metal=0.9), r, seg=24, rot=(math.pi / 2, 0, 0)); return r

def gift(n, rng, color=None, **k):
    r = _root(n); m = M(n + 'm', color or (220, 50, 70), 0.55); rb = M(n + 'r', 'gold', 0.4)
    B(r, n + 'b', (3.0, 3.0, 2.6), (0, 0, 1.3), m, 0.1); B(r, n + 'r1', (0.5, 3.1, 2.7), (0, 0, 1.3), rb, 0.03); B(r, n + 'r2', (3.1, 0.5, 2.7), (0, 0, 1.3), rb, 0.03)
    B(r, n + 'bw1', (0.9, 0.5, 0.7), (-0.5, 0, 2.9), rb, 0.15, rot=(0, 0.5, 0)); B(r, n + 'bw2', (0.9, 0.5, 0.7), (0.5, 0, 2.9), rb, 0.15, rot=(0, -0.5, 0)); return r

def trophy(n, rng, color=None, **k):
    r = _root(n); g = M(n + 'g', 'gold', 0.2, metal=0.9)
    B(r, n + 'base', (2.0, 2.0, 0.6), (0, 0, 0.3), M(n + 'bs', (60, 40, 30), 0.5), 0.05); cyl(n + 'st', 0.25, 1.4, (0, 0, 0.6), g, r); cyl(n + 'cup', 0.5, 1.6, (0, 0, 2.0), g, r, r2=1.1, seg=16)
    for sx in (-1, 1): B(r, f'{n}hd{sx}', (0.2, 0.2, 0.9), (sx * 1.25, 0, 2.9), g, 0.05)
    return r

def ball(n, rng, color=None, **k):
    r = _root(n); sphere(n + 'b', 1.3, (0, 0, 1.3), M(n + 'b', color or 'white', 0.45), r)
    for i, (x, y, z) in enumerate([(0, -1.1, 1.3), (1.0, -0.5, 1.9), (-1.0, -0.5, 1.9), (0.6, -0.5, 0.5), (-0.6, -0.5, 0.5)]):
        sphere(f'{n}p{i}', 0.38, (x, y, z), M(n + 'pt', 'black', 0.5), r, scale=(1, 0.4, 1))
    return r

def balloon(n, rng, color=None, **k):
    r = _root(n); sphere(n + 'b', 1.3, (0, 0, 5.0), M(n + 'b', color or (230, 50, 70), 0.2), r, scale=(1, 1, 1.2)); cyl(n + 's', 0.03, 3.6, (0, 0, 1.3), M(n + 's', 'white', 0.6), r, seg=4); return r

def flower(n, rng, color=None, **k):
    r = _root(n); cyl(n + 's', 0.1, 2.2, (0, 0, 0), M(n + 's', 'green', 0.7), r, seg=6)
    for i in range(6):
        a = i * math.pi / 3; sphere(f'{n}p{i}', 0.42, (math.cos(a) * 0.55, -0.0, 2.2 + math.sin(a) * 0.55), M(n + 'p', color or (245, 90, 150), 0.6), r)
    sphere(n + 'c', 0.35, (0, -0.2, 2.2), M(n + 'c', 'yellow', 0.5), r); return r

def plant(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'pot', 0.9, 1.4, (0, 0, 0), M(n + 'pot', (190, 100, 70), 0.7), r, r2=0.7)
    for i in range(7):
        a = i * 0.9; box(f'{n}l{i}', (0.4, 0.15, 2.0), (math.cos(a) * 0.5, math.sin(a) * 0.5, 2.0), M(n + 'lf', (60, 160, 70), 0.6), r, 0.05, rot=(math.sin(a) * 0.5, -math.cos(a) * 0.5, a)); 
    return r

def clock(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'f', 1.5, 0.3, (0, 0, 4.0), M(n + 'f', 'white', 0.4), r, seg=24, rot=(math.pi / 2, 0, 0))
    B(r, n + 'h1', (0.12, 0.1, 1.0), (0, -0.2, 4.4), M(n + 'h', 'black', 0.5), 0.0); B(r, n + 'h2', (0.1, 0.1, 0.7), (0.3, -0.2, 4.0), M(n + 'h', 'black', 0.5), 0.0, rot=(0, 1.2, 0)); return r

def mirror(n, rng, color=None, **k):
    r = _root(n); B(r, n + 'fr', (3.0, 0.3, 5.6), (0, 0, 3.4), M(n + 'f', 'gold', 0.3, metal=0.8), 0.08); B(r, n + 'g', (2.6, 0.1, 5.2), (0, -0.2, 3.4), M(n + 'g', (200, 225, 245), 0.05, metal=0.6), 0.0); return r

def bag(n, rng, color=None, **k):
    r = _root(n); B(r, n + 'b', (2.2, 1.2, 2.6), (0, 0, 1.3), M(n + 'b', color or (240, 200, 90), 0.8), 0.1)
    for sx in (-1, 1): B(r, f'{n}h{sx}', (0.15, 0.15, 1.2), (sx * 0.5, 0, 3.0), M(n + 'h', 'white', 0.7), 0.03)
    return r

def umbrella(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'p', 0.08, 4.6, (0, 0, 0), M(n + 'p', 'darkgrey', 0.4), r, seg=6); cyl(n + 'c', 2.8, 1.0, (0, 0, 4.4), M(n + 'c', color or (230, 50, 60), 0.6, 'stripes', color2='white', scale=0.6), r, r2=0.1, seg=12); return r

def key(n, rng, color=None, **k):
    r = _root(n); g = M(n + 'g', 'gold', 0.25, metal=0.9); cyl(n + 'r', 0.8, 0.2, (0, 0, 2.2), g, r, seg=16, rot=(math.pi / 2, 0, 0)); B(r, n + 's', (0.25, 0.15, 2.2), (0, 0, 0.9), g, 0.03); B(r, n + 't', (0.7, 0.15, 0.3), (0.35, 0, 0.3), g, 0.03); return r

def chest(n, rng, color=None, **k):
    r = _root(n); w = M(n + 'w', (135, 85, 45), 0.6, 'wood', scale=1.0); g = M(n + 'g', 'gold', 0.25, metal=0.8)
    B(r, n + 'b', (4.0, 2.4, 1.8), (0, 0, 0.9), w, 0.1); B(r, n + 'l', (4.0, 2.4, 1.2), (0, 0, 2.3), w, 0.35); B(r, n + 'g1', (0.4, 2.5, 3.0), (-1.3, 0, 1.5), g, 0.05); B(r, n + 'g2', (0.4, 2.5, 3.0), (1.3, 0, 1.5), g, 0.05); return r

def pumpkin(n, rng, color=None, **k):
    r = _root(n); sphere(n + 'p', 1.6, (0, 0, 1.3), M(n + 'p', (245, 130, 30), 0.5), r, scale=(1, 1, 0.85)); cyl(n + 's', 0.2, 0.6, (0, 0, 2.4), M(n + 's', 'green', 0.7), r, seg=6)
    for sx in (-1, 1): B(r, f'{n}e{sx}', (0.4, 0.1, 0.4), (sx * 0.55, -1.55, 1.7), M(n + 'e', (255, 220, 80), 0.3, emit=3), 0.0, rot=(0, 0, 0.7 * sx))
    B(r, n + 'm', (1.0, 0.1, 0.35), (0, -1.55, 0.85), M(n + 'm', (255, 220, 80), 0.3, emit=3), 0.0); return r

def icecream(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'c', 0.7, 2.0, (0, 0, 0), M(n + 'c', (225, 170, 90), 0.8), r, r2=0.05, seg=8, rot=(math.pi, 0, 0)); r.children[0].location = (0, 0, 1.0)
    sphere(n + 's1', 0.85, (0, 0, 2.3), M(n + 's1', color or (250, 170, 200), 0.5), r); sphere(n + 's2', 0.75, (0, 0, 3.0), M(n + 's2', (250, 235, 200), 0.5), r); return r

def bottle(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'b', 0.7, 2.6, (0, 0, 0), M(n + 'b', color or (90, 190, 230), 0.15, alpha=0.9), r); cyl(n + 'n', 0.3, 0.9, (0, 0, 2.6), M(n + 'n', color or (90, 190, 230), 0.15), r); cyl(n + 'c', 0.34, 0.3, (0, 0, 3.4), M(n + 'cp', 'red', 0.5), r); return r

# ---------------- vehicles / animals / creatures ----------------
def car(n, rng, color=None, **k):
    r = _root(n); c = M(n + 'c', color or (220, 60, 60), 0.25, metal=0.2); gl = M(n + 'g', (150, 200, 235), 0.1)
    B(r, n + 'b', (5.2, 10.0, 2.0), (0, 0, 1.6), c, 0.3); B(r, n + 'r', (4.6, 5.0, 1.8), (0, -0.4, 3.2), c, 0.35)
    B(r, n + 'ws', (4.4, 0.1, 1.4), (0, -2.9, 3.2), gl, 0.0, rot=(0.0, 0, 0)); B(r, n + 'rw', (4.4, 0.1, 1.3), (0, 2.1, 3.2), gl, 0.0)
    for sx in (-1, 1): B(r, f'{n}sw{sx}', (0.1, 4.2, 1.3), (sx * 2.34, -0.4, 3.2), gl, 0.0)
    wm = M(n + 'w', (25, 25, 28), 0.7)
    for sx in (-1, 1):
        for sy in (-1, 1): cyl(f'{n}wh{sx}{sy}', 0.95, 0.7, (sx * 2.5, sy * 3.1, 0.95), wm, r, seg=14, rot=(0, math.pi / 2, 0))
    for sx in (-1, 1): sphere(f'{n}hl{sx}', 0.35, (sx * 1.7, -5.0, 1.8), M(n + 'hl', (255, 245, 200), 0.2, emit=3), r)
    return r

def _animal(n, rng, color, ears='dog', tail=True, size=1.0):
    r = _root(n); c = M(n + 'c', color, 0.7); d = M(n + 'd', shade_c(color, 0.75), 0.7)
    B(r, n + 'b', (1.6, 3.0, 1.5), (0, 0.2, 1.7), c, 0.2)
    B(r, n + 'h', (1.5, 1.4, 1.4), (0, -1.9, 2.5), c, 0.22); B(r, n + 'sn', (0.8, 0.7, 0.6), (0, -2.75, 2.25), M(n + 'sn', (250, 235, 215), 0.7), 0.1)
    B(r, n + 'ns', (0.28, 0.15, 0.22), (0, -3.12, 2.4), M(n + 'ns', 'black', 0.4), 0.04)
    for sx in (-1, 1):
        B(r, f'{n}e{sx}', (0.35, 0.9, 0.35) if ears == 'cat' else (0.45, 0.35, 0.9), (sx * 0.62, -1.8, 3.35 if ears == 'cat' else 2.9), d if ears != 'cat' else c, 0.08)
        B(r, f'{n}ey{sx}', (0.2, 0.1, 0.28), (sx * 0.38, -2.62, 2.75), M(n + 'ey', 'black', 0.3), 0.03)
        for sy in (-1, 1): B(r, f'{n}lg{sx}{sy}', (0.45, 0.45, 1.2), (sx * 0.55, 0.2 + sy * 1.0, 0.6), c, 0.08)
    if tail: B(r, n + 't', (0.35, 0.35, 1.5), (0, 1.9, 2.4), d, 0.1, rot=(0.7, 0, 0))
    r.scale = (size, size, size)
    return r

def dog(n, rng, color=None, **k): return _animal(n, rng, color or (215, 160, 90), 'dog', True, 1.1)
def cat(n, rng, color=None, **k): return _animal(n, rng, color or (230, 140, 60), 'cat', True, 0.85)
def puppy(n, rng, color=None, **k): return _animal(n, rng, color or (240, 225, 200), 'dog', True, 0.7)

def bird(n, rng, color=None, **k):
    r = _root(n); c = M(n + 'c', color or (80, 150, 240), 0.6)
    sphere(n + 'b', 0.9, (0, 0, 1.2), c, r, scale=(0.8, 1.1, 0.9)); sphere(n + 'h', 0.55, (0, -0.8, 2.0), c, r); B(r, n + 'bk', (0.2, 0.5, 0.2), (0, -1.3, 1.95), M(n + 'bk', 'orange', 0.5), 0.04)
    for sx in (-1, 1): B(r, f'{n}w{sx}', (1.3, 0.8, 0.12), (sx * 1.0, 0.1, 1.5), shade_m(n + 'w', color or (80, 150, 240), 0.8), 0.04, rot=(0, sx * 0.4, 0))
    return r

def ghost(n, rng, color=None, **k):
    r = _root(n); m = M(n + 'm', (245, 245, 255), 0.5, emit=0.25, alpha=0.92)
    sphere(n + 'h', 1.6, (0, 0, 4.4), m, r); cyl(n + 'b', 1.6, 3.4, (0, 0, 1.0), m, r, r2=1.7, seg=14)
    for sx in (-1, 1): sphere(f'{n}e{sx}', 0.28, (sx * 0.6, -1.5, 4.6), M(n + 'e', 'black', 0.3), r, scale=(1, 0.5, 1.4))
    sphere(n + 'm', 0.3, (0, -1.55, 3.8), M(n + 'mo', 'black', 0.3), r, scale=(1, 0.5, 1.5)); return r

def monster(n, rng, color=None, **k):
    r = _root(n); m = M(n + 'm', color or (22, 20, 30), 0.8)
    B(r, n + 'b', (3.0, 2.0, 5.0), (0, 0, 4.5), m, 0.4); sphere(n + 'h', 1.5, (0, 0, 8.1), m, r, scale=(1, 0.9, 1.1))
    for sx in (-1, 1):
        sphere(f'{n}e{sx}', 0.38, (sx * 0.65, -1.15, 8.4), M(n + 'e', (255, 235, 90), 0.2, emit=8), r, scale=(1, 0.5, 1.2))
        B(r, f'{n}a{sx}', (0.7, 0.7, 5.6), (sx * 2.1, 0, 4.2), m, 0.2, rot=(0, sx * 0.15, 0)); B(r, f'{n}l{sx}', (0.9, 0.9, 2.6), (sx * 0.9, 0, 1.3), m, 0.2)
        for i in range(3): B(r, f'{n}cl{sx}{i}', (0.12, 0.12, 1.4), (sx * (2.2 + 0.2 * i), -0.25 * i, 1.0), M(n + 'cl', (230, 230, 230), 0.3), 0.02, rot=(0.3, 0, 0))
    B(r, n + 'mo', (1.5, 0.15, 0.45), (0, -1.38, 7.5), M(n + 'mo', (240, 240, 240), 0.4), 0.02); return r

def tree(n, rng, color=None, **k):
    r = _root(n); cyl(n + 't', 0.7, 4.0, (0, 0, 0), M(n + 't', (110, 75, 45), 0.8, 'noise', scale=2), r, seg=8)
    gm = M(n + 'g', color or (70, 165, 70), 0.8, 'noise', color2=(55, 135, 60), scale=0.7, bump=0.2)
    sphere(n + 'g1', 3.2, (0, 0, 6.6), gm, r, scale=(1, 1, 1.05), seg=12, rings=8); sphere(n + 'g2', 2.2, (1.6, 0.4, 8.0), gm, r); sphere(n + 'g3', 2.0, (-1.6, -0.4, 7.9), gm, r); return r

def pine(n, rng, color=None, **k):
    r = _root(n); cyl(n + 't', 0.5, 2.5, (0, 0, 0), M(n + 't', (100, 70, 45), 0.8), r, seg=6); gm = M(n + 'g', color or (35, 110, 65), 0.8, 'noise', scale=0.7)
    for i, (rad, z) in enumerate([(3.0, 2.0), (2.4, 4.3), (1.7, 6.4)]): cyl(f'{n}c{i}', rad, 3.0, (0, 0, z), gm, r, r2=0.05, seg=9)
    return r

def bench(n, rng, color=None, **k):
    r = _root(n); w = M(n + 'w', (150, 100, 60), 0.6, 'wood', scale=1.2); m = M(n + 'm', 'darkgrey', 0.4)
    B(r, n + 's', (5.4, 1.6, 0.3), (0, 0, 1.7), w, 0.05); B(r, n + 'b', (5.4, 0.3, 1.6), (0, 0.8, 2.6), w, 0.05)
    for sx in (-1, 1): B(r, f'{n}l{sx}', (0.3, 1.6, 1.7), (sx * 2.4, 0, 0.85), m, 0.04)
    return r

def lamppost(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'p', 0.22, 9.0, (0, 0, 0), M(n + 'p', (45, 45, 52), 0.4), r, seg=8, r2=0.16)
    B(r, n + 'h', (1.3, 1.3, 1.9), (0, 0, 9.6), M(n + 'h', (255, 225, 140), 0.3, emit=3.5), 0.1); B(r, n + 'tp', (1.6, 1.6, 0.25), (0, 0, 10.7), M(n + 'tp', (45, 45, 52), 0.4), 0.05); return r

def rocket(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'b', 1.3, 5.0, (0, 0, 1.5), M(n + 'b', 'white', 0.3), r, seg=14); cyl(n + 'n', 1.3, 1.8, (0, 0, 6.5), M(n + 'n', 'red', 0.4), r, r2=0.05, seg=14)
    for i in range(3):
        a = i * 2.09; B(r, f'{n}f{i}', (0.2, 1.5, 1.8), (math.cos(a) * 1.5, math.sin(a) * 1.5, 1.4), M(n + 'f', 'red', 0.4), 0.03, rot=(0, 0, a + 1.57))
    sphere(n + 'w', 0.5, (0, -1.25, 4.5), M(n + 'w', (150, 210, 255), 0.1), r); return r

def sign(n, rng, color=None, **k):
    r = _root(n); cyl(n + 'p', 0.15, 4.0, (0, 0, 0), M(n + 'p', 'darkgrey', 0.4), r, seg=6); B(r, n + 'b', (3.2, 0.2, 2.0), (0, -0.1, 4.6), M(n + 'b', color or (240, 190, 40), 0.5), 0.06); return r

def crowd_person(n, rng, color=None, **k):
    r = _root(n); sk = M(n + 's', rng.choice([(238, 188, 150), (214, 160, 110), (160, 105, 70)]), 0.6); sh = M(n + 'sh', rng.choice(list(COLORS.values())), 0.8)
    B(r, n + 'l', (1.6, 1.0, 2.0), (0, 0, 1.0), M(n + 'pa', (60, 70, 100), 0.8), 0.08); B(r, n + 't', (2.0, 1.0, 2.0), (0, 0, 3.0), sh, 0.1); B(r, n + 'h', (1.6, 1.5, 1.4), (0, 0, 4.7), sk, 0.3); return r

REGISTRY = {
    'cabinet': cabinet, 'wardrobe': cabinet, 'closet': cabinet, 'desk': desk, 'computer': computer, 'laptop': laptop, 'phone': phone, 'headphones': headphones,
    'tv': tv, 'bed': bed, 'sofa': sofa, 'table': table, 'chair': chair, 'lamp': lamp, 'door': door, 'fridge': fridge, 'bookshelf': bookshelf, 'book': book,
    'backpack': backpack, 'pizza': pizza, 'burger': burger, 'cake': cake, 'apple': apple, 'coffee': coffee, 'money': money, 'coin': coin, 'gift': gift,
    'trophy': trophy, 'ball': ball, 'balloon': balloon, 'flower': flower, 'plant': plant, 'clock': clock, 'mirror': mirror, 'bag': bag, 'umbrella': umbrella,
    'key': key, 'chest': chest, 'pumpkin': pumpkin, 'icecream': icecream, 'bottle': bottle, 'car': car, 'dog': dog, 'cat': cat, 'puppy': puppy, 'bird': bird,
    'ghost': ghost, 'monster': monster, 'tree': tree, 'pine': pine, 'bench': bench, 'lamppost': lamppost, 'rocket': rocket, 'sign': sign,
}
# props that sit on the floor large (not hand-held), used by the planner for placement
BIG = {'cabinet', 'wardrobe', 'closet', 'desk', 'bed', 'sofa', 'table', 'fridge', 'bookshelf', 'tv', 'car', 'door', 'monster', 'ghost', 'tree', 'pine', 'bench', 'lamppost', 'rocket', 'chest', 'computer', 'mirror'}
