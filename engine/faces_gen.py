"""Draws Roblox-style cartoon face decals (transparent PNG) with PIL. Runs outside Blender."""
import math, os
from PIL import Image, ImageDraw

S = 1024            # supersampled canvas
INK = (22, 20, 26, 255)
WHITE = (255, 255, 255, 255)
RED = (190, 40, 55, 255)
PINK = (240, 120, 140, 255)
TEETH = (250, 250, 250, 255)
TEAR = (120, 200, 255, 255)
BLUSH = (255, 120, 120, 150)

EXPRESSIONS = ['neutral', 'happy', 'grin', 'laugh', 'sad', 'cry', 'angry', 'furious', 'surprised', 'shocked', 'scared',
               'worried', 'sleepy', 'smirk', 'wink', 'love', 'dizzy', 'disgusted', 'evil', 'embarrassed', 'thinking',
               'excited', 'tired', 'serious']

def _p(x, y): return (x * S, y * S)

def _eye_dot(d, cx, cy, rx=0.045, ry=0.075, shine=True):
    d.ellipse([_p(cx - rx, cy - ry), _p(cx + rx, cy + ry)], fill=INK)
    if shine:
        d.ellipse([_p(cx - rx * 0.1, cy - ry * 0.65), _p(cx + rx * 0.55, cy - ry * 0.05)], fill=WHITE)

def _eye_open(d, cx, cy, r=0.11, pupil=0.04, ring=True):
    d.ellipse([_p(cx - r, cy - r * 1.15), _p(cx + r, cy + r * 1.15)], fill=WHITE, outline=INK, width=int(S * 0.012))
    d.ellipse([_p(cx - pupil, cy - pupil * 1.3), _p(cx + pupil, cy + pupil * 1.3)], fill=INK)

def _arc(d, box, a0, a1, w=0.022, fill=INK):
    (x0, y0), (x1, y1) = box
    d.arc([_p(x0, y0), _p(x1, y1)], a0, a1, fill=fill, width=int(S * w))

def _line(d, pts, w=0.022, fill=INK):
    d.line([_p(*p) for p in pts], fill=fill, width=int(S * w), joint='curve')
    for p in (pts[0], pts[-1]):
        r = w / 2
        d.ellipse([_p(p[0] - r, p[1] - r), _p(p[0] + r, p[1] + r)], fill=fill)

def _brow(d, cx, cy, tilt=0.0, w=0.12, th=0.026):
    _line(d, [(cx - w / 2, cy + tilt), (cx + w / 2, cy - tilt)], th)

def _mouth_open(d, cx, cy, w, h, teeth=False, tongue=True):
    d.ellipse([_p(cx - w, cy - h), _p(cx + w, cy + h)], fill=RED if not teeth else INK, outline=INK, width=int(S * 0.015))
    if teeth:
        d.rectangle([_p(cx - w * 0.8, cy - h * 0.8), _p(cx + w * 0.8, cy - h * 0.05)], fill=TEETH)
    if tongue and not teeth:
        d.ellipse([_p(cx - w * 0.5, cy + h * 0.1), _p(cx + w * 0.5, cy + h * 0.95)], fill=PINK)

def _smile(d, cx, cy, w, depth, th=0.024):
    pts = []
    for i in range(21):
        t = i / 20.0
        x = cx - w + 2 * w * t
        y = cy + depth * (1 - (2 * t - 1) ** 2)
        pts.append((x, y))
    _line(d, pts, th)

def _frown(d, cx, cy, w, depth, th=0.024):
    pts = []
    for i in range(21):
        t = i / 20.0
        pts.append((cx - w + 2 * w * t, cy - depth * (1 - (2 * t - 1) ** 2)))
    _line(d, pts, th)

def _grid_teeth(d, cx, cy, w, h):
    d.rounded_rectangle([_p(cx - w, cy - h), _p(cx + w, cy + h)], radius=int(S * 0.03), fill=TEETH, outline=INK, width=int(S * 0.015))
    n = 6
    for i in range(1, n):
        x = cx - w + 2 * w * i / n
        d.line([_p(x, cy - h), _p(x, cy + h)], fill=INK, width=int(S * 0.008))
    d.line([_p(cx - w, cy), _p(cx + w, cy)], fill=INK, width=int(S * 0.008))

def draw_expression(d, e):
    ex1, ex2, ey = 0.31, 0.69, 0.42
    if e == 'neutral':
        _eye_dot(d, ex1, ey); _eye_dot(d, ex2, ey); _line(d, [(0.4, 0.72), (0.6, 0.72)], 0.02)
    elif e == 'happy':
        _eye_dot(d, ex1, ey); _eye_dot(d, ex2, ey); _smile(d, 0.5, 0.66, 0.15, 0.1)
    elif e == 'grin':
        _eye_dot(d, ex1, ey); _eye_dot(d, ex2, ey); _grid_teeth(d, 0.5, 0.7, 0.17, 0.065)
    elif e == 'laugh':
        _arc(d, ((ex1 - 0.07, ey - 0.06), (ex1 + 0.07, ey + 0.1)), 190, 350, 0.025)
        _arc(d, ((ex2 - 0.07, ey - 0.06), (ex2 + 0.07, ey + 0.1)), 190, 350, 0.025)
        _mouth_open(d, 0.5, 0.7, 0.19, 0.13)
        d.ellipse([_p(0.05, 0.55), _p(0.19, 0.67)], fill=BLUSH); d.ellipse([_p(0.81, 0.55), _p(0.95, 0.67)], fill=BLUSH)
    elif e == 'sad':
        _eye_dot(d, ex1, ey + 0.02); _eye_dot(d, ex2, ey + 0.02)
        _brow(d, ex1, ey - 0.1, -0.03); _brow(d, ex2, ey - 0.1, 0.03)
        _frown(d, 0.5, 0.78, 0.12, 0.07)
    elif e == 'cry':
        _eye_dot(d, ex1, ey + 0.02, shine=True); _eye_dot(d, ex2, ey + 0.02)
        _brow(d, ex1, ey - 0.1, -0.035); _brow(d, ex2, ey - 0.1, 0.035)
        for cx in (ex1, ex2):
            d.polygon([_p(cx - 0.035, ey + 0.1), _p(cx + 0.035, ey + 0.1), _p(cx + 0.05, 0.92), _p(cx - 0.05, 0.92)], fill=TEAR)
        _mouth_open(d, 0.5, 0.76, 0.12, 0.08, tongue=False)
    elif e == 'angry':
        _eye_dot(d, ex1, ey + 0.03, shine=False); _eye_dot(d, ex2, ey + 0.03, shine=False)
        _brow(d, ex1, ey - 0.07, 0.05, 0.16, 0.035); _brow(d, ex2, ey - 0.07, -0.05, 0.16, 0.035)
        _frown(d, 0.5, 0.76, 0.13, 0.05)
    elif e == 'furious':
        _eye_dot(d, ex1, ey + 0.03, 0.04, 0.05, False); _eye_dot(d, ex2, ey + 0.03, 0.04, 0.05, False)
        _brow(d, ex1, ey - 0.07, 0.065, 0.17, 0.04); _brow(d, ex2, ey - 0.07, -0.065, 0.17, 0.04)
        _grid_teeth(d, 0.5, 0.74, 0.17, 0.06)
        d.line([_p(0.12, 0.2), _p(0.2, 0.26)], fill=RED, width=int(S * 0.012))
    elif e == 'surprised':
        _eye_open(d, ex1, ey, 0.085, 0.03); _eye_open(d, ex2, ey, 0.085, 0.03)
        _brow(d, ex1, ey - 0.16, 0.02); _brow(d, ex2, ey - 0.16, -0.02)
        _mouth_open(d, 0.5, 0.73, 0.06, 0.08, tongue=False)
    elif e == 'shocked':
        _eye_open(d, ex1, ey, 0.12, 0.022); _eye_open(d, ex2, ey, 0.12, 0.022)
        _mouth_open(d, 0.5, 0.74, 0.1, 0.12, tongue=True)
        d.ellipse([_p(0.82, 0.12), _p(0.88, 0.24)], fill=TEAR)
    elif e == 'scared':
        _eye_open(d, ex1, ey, 0.115, 0.02); _eye_open(d, ex2, ey, 0.115, 0.02)
        _brow(d, ex1 - 0.01, ey - 0.17, -0.04, 0.13); _brow(d, ex2 + 0.01, ey - 0.17, 0.04, 0.13)
        _mouth_open(d, 0.5, 0.75, 0.13, 0.08, teeth=True)
        d.ellipse([_p(0.84, 0.14), _p(0.9, 0.27)], fill=TEAR); d.ellipse([_p(0.08, 0.3), _p(0.13, 0.4)], fill=TEAR)
    elif e == 'worried':
        _eye_dot(d, ex1, ey + 0.01); _eye_dot(d, ex2, ey + 0.01)
        _brow(d, ex1, ey - 0.11, -0.04); _brow(d, ex2, ey - 0.11, 0.04)
        pts = [(0.38 + i * 0.02, 0.74 + (0.015 if i % 2 else -0.015)) for i in range(7)]
        _line(d, pts, 0.018)
        d.ellipse([_p(0.84, 0.16), _p(0.9, 0.28)], fill=TEAR)
    elif e == 'sleepy':
        _line(d, [(ex1 - 0.07, ey), (ex1 + 0.07, ey + 0.015)], 0.026); _line(d, [(ex2 - 0.07, ey + 0.015), (ex2 + 0.07, ey)], 0.026)
        _mouth_open(d, 0.5, 0.74, 0.05, 0.05, tongue=False)
        d.text(_p(0.78, 0.08), 'z', fill=INK)
    elif e == 'smirk':
        _eye_dot(d, ex1, ey); _eye_dot(d, ex2, ey); _brow(d, ex2, ey - 0.11, 0.045)
        _line(d, [(0.42, 0.72), (0.56, 0.72), (0.66, 0.65)], 0.022)
    elif e == 'wink':
        _eye_dot(d, ex1, ey); _arc(d, ((ex2 - 0.07, ey - 0.07), (ex2 + 0.07, ey + 0.09)), 190, 350, 0.025)
        _smile(d, 0.5, 0.67, 0.15, 0.09)
    elif e == 'love':
        for cx in (ex1, ex2):
            _heart(d, cx, ey, 0.085)
        _mouth_open(d, 0.5, 0.7, 0.13, 0.09)
    elif e == 'dizzy':
        for cx in (ex1, ex2):
            _line(d, [(cx - 0.07, ey - 0.07), (cx + 0.07, ey + 0.07)], 0.022); _line(d, [(cx - 0.07, ey + 0.07), (cx + 0.07, ey - 0.07)], 0.022)
        _line(d, [(0.38 + i * 0.03, 0.74 + (0.025 if i % 2 else -0.025)) for i in range(6)], 0.02)
    elif e == 'disgusted':
        _line(d, [(ex1 - 0.07, ey), (ex1 + 0.07, ey - 0.02)], 0.03); _line(d, [(ex2 - 0.07, ey - 0.02), (ex2 + 0.07, ey)], 0.03)
        _brow(d, ex1, ey - 0.1, 0.04); _brow(d, ex2, ey - 0.1, -0.04)
        _line(d, [(0.36, 0.76), (0.44, 0.7), (0.5, 0.77), (0.56, 0.7), (0.64, 0.76)], 0.02)
    elif e == 'evil':
        _eye_dot(d, ex1, ey + 0.02, 0.04, 0.05, False); _eye_dot(d, ex2, ey + 0.02, 0.04, 0.05, False)
        _brow(d, ex1, ey - 0.08, 0.06, 0.16, 0.035); _brow(d, ex2, ey - 0.08, -0.06, 0.16, 0.035)
        _grid_teeth(d, 0.5, 0.72, 0.21, 0.07); _smile(d, 0.5, 0.68, 0.23, 0.05, 0.02)
    elif e == 'embarrassed':
        _eye_dot(d, ex1, ey); _eye_dot(d, ex2, ey)
        d.ellipse([_p(0.08, 0.5), _p(0.26, 0.64)], fill=BLUSH); d.ellipse([_p(0.74, 0.5), _p(0.92, 0.64)], fill=BLUSH)
        _smile(d, 0.5, 0.7, 0.09, 0.05); d.ellipse([_p(0.82, 0.12), _p(0.88, 0.25)], fill=TEAR)
    elif e == 'thinking':
        _eye_dot(d, ex1, ey); _eye_dot(d, ex2, ey); _brow(d, ex2, ey - 0.12, 0.05); _brow(d, ex1, ey - 0.09, 0.0)
        _line(d, [(0.42, 0.74), (0.58, 0.72)], 0.02)
    elif e == 'excited':
        for cx in (ex1, ex2):
            _eye_open(d, cx, ey, 0.09, 0.05)
            d.ellipse([_p(cx - 0.02, ey - 0.07), _p(cx + 0.015, ey - 0.03)], fill=WHITE)
        _mouth_open(d, 0.5, 0.7, 0.17, 0.12)
        d.ellipse([_p(0.07, 0.52), _p(0.21, 0.63)], fill=BLUSH); d.ellipse([_p(0.79, 0.52), _p(0.93, 0.63)], fill=BLUSH)
    elif e == 'tired':
        _eye_dot(d, ex1, ey + 0.02, 0.045, 0.045, False); _eye_dot(d, ex2, ey + 0.02, 0.045, 0.045, False)
        _arc(d, ((ex1 - 0.08, ey + 0.03), (ex1 + 0.08, ey + 0.13)), 20, 160, 0.012); _arc(d, ((ex2 - 0.08, ey + 0.03), (ex2 + 0.08, ey + 0.13)), 20, 160, 0.012)
        _frown(d, 0.5, 0.76, 0.1, 0.03)
    else:  # serious
        _eye_dot(d, ex1, ey, shine=False); _eye_dot(d, ex2, ey, shine=False)
        _brow(d, ex1, ey - 0.1, 0.015, 0.14); _brow(d, ex2, ey - 0.1, -0.015, 0.14)
        _line(d, [(0.4, 0.74), (0.6, 0.74)], 0.022)

def _heart(d, cx, cy, r):
    col = (230, 40, 90, 255)
    d.ellipse([_p(cx - r, cy - r), _p(cx, cy + r * 0.2)], fill=col)
    d.ellipse([_p(cx, cy - r), _p(cx + r, cy + r * 0.2)], fill=col)
    d.polygon([_p(cx - r * 0.98, cy - r * 0.15), _p(cx + r * 0.98, cy - r * 0.15), _p(cx, cy + r * 1.1)], fill=col)

def make_face(expr, glasses=False, mustache=False, lashes=False, freckles=False, mustache_color=(60, 40, 30)):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if freckles:
        for (x, y) in [(0.2, 0.58), (0.26, 0.62), (0.15, 0.62), (0.8, 0.58), (0.74, 0.62), (0.85, 0.62)]:
            d.ellipse([_p(x - 0.008, y - 0.008), _p(x + 0.008, y + 0.008)], fill=(150, 90, 60, 220))
    draw_expression(d, expr)
    if lashes:
        for cx in (0.31, 0.69):
            for k, (dx, dy) in enumerate([(-0.07, -0.02), (-0.05, -0.06), (0.05, -0.06), (0.07, -0.02)]):
                d.line([_p(cx + dx * 0.6, 0.42 + dy * 0.6), _p(cx + dx * 1.5, 0.42 + dy * 1.6)], fill=INK, width=int(S * 0.012))
    if mustache:
        mc = tuple(mustache_color) + (255,)
        d.ellipse([_p(0.33, 0.6), _p(0.5, 0.69)], fill=mc); d.ellipse([_p(0.5, 0.6), _p(0.67, 0.69)], fill=mc)
    if glasses:
        w = int(S * 0.018)
        for cx in (0.31, 0.69):
            d.rounded_rectangle([_p(cx - 0.15, 0.27), _p(cx + 0.15, 0.57)], radius=int(S * 0.08), outline=INK, width=w)
        d.line([_p(0.46, 0.38), _p(0.54, 0.38)], fill=INK, width=w)
    return im.resize((512, 512), Image.LANCZOS)

def face_key(expr, glasses=False, mustache=False, lashes=False, freckles=False):
    return f"{expr}{'_g' if glasses else ''}{'_m' if mustache else ''}{'_l' if lashes else ''}{'_f' if freckles else ''}"

def ensure_face(outdir, expr, glasses=False, mustache=False, lashes=False, freckles=False):
    os.makedirs(outdir, exist_ok=True)
    if expr not in EXPRESSIONS: expr = 'neutral'
    path = os.path.join(outdir, face_key(expr, glasses, mustache, lashes, freckles) + '.png')
    if not os.path.exists(path):
        make_face(expr, glasses, mustache, lashes, freckles).save(path)
    return path

if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else 'faces_preview'
    os.makedirs(out, exist_ok=True)
    sheet = Image.new('RGBA', (256 * 8, 256 * 3), (240, 190, 150, 255))
    for i, e in enumerate(EXPRESSIONS):
        f = make_face(e).resize((256, 256), Image.LANCZOS)
        sheet.alpha_composite(f, ((i % 8) * 256, (i // 8) * 256))
    sheet.convert('RGB').save(os.path.join(out, 'sheet.jpg'))
