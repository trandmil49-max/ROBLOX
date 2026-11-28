"""Frame finishing (colour grade, vignette, single-word captions) and per-shard video encoding. Pure Python + OpenCV/Pillow."""
import os, re, sys, json, glob, subprocess, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT_LATIN = os.path.join(ROOT, 'assets', 'fonts', 'Poppins-Bold.ttf')
ARABIC_CANDIDATES = ['/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf', '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf',
                     '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
CAP_Y = 0.725          # vertical centre of the caption (fraction of frame height) - lower third, inside the area he marked
CAP_CAP_HEIGHT = 0.032 # capital-letter height as a fraction of frame height (matches the reference image)

def has_arabic(s): return bool(re.search('[\u0600-\u06ff]', s))

def shape_text(t, lang):
    if has_arabic(t):
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            return get_display(arabic_reshaper.reshape(t))
        except Exception: return t
    return t

def upper(t, lang):
    if has_arabic(t): return t
    if lang == 'tr': t = t.replace('i', '\u0130').replace('\u0131', 'I')
    return t.upper()

def find_font(text, size):
    if has_arabic(text):
        for p in ARABIC_CANDIDATES:
            if os.path.exists(p): return ImageFont.truetype(p, size)
    if os.path.exists(FONT_LATIN): return ImageFont.truetype(FONT_LATIN, size)
    for p in ('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

class Captions:
    def __init__(self, plan):
        self.plan = plan; self.W = plan['width']; self.H = plan['height']; self.lang = plan.get('lang', 'en')
        self.cache = {}; self.items = plan.get('captions', []); self.i = 0
        self.size = int(self.H * CAP_CAP_HEIGHT / 0.70)     # font size from cap height (Poppins cap height ~ 0.70 em)
        self.stroke = max(3, int(self.size * 0.09))
    def sprite(self, text):
        if text in self.cache: return self.cache[text]
        t = shape_text(upper(text, self.lang), self.lang)
        font = find_font(t, self.size)
        pad = self.stroke * 3
        tmp = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
        bb = tmp.textbbox((0, 0), t, font=font, stroke_width=self.stroke)
        w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        # soft drop shadow like the references
        sh = Image.new('RGBA', (w, h), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        sd.text((pad - bb[0], pad - bb[1] + self.stroke * 0.5), t, font=font, fill=(0, 0, 0, 150), stroke_width=self.stroke, stroke_fill=(0, 0, 0, 150))
        im.alpha_composite(sh.filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(self.stroke * 0.6)))
        d.text((pad - bb[0], pad - bb[1]), t, font=font, fill=(255, 255, 255, 255), stroke_width=self.stroke, stroke_fill=(0, 0, 0, 255))
        a = np.array(im); self.cache[text] = a; return a
    def active(self, f):
        for c in self.items:
            if c['start_f'] <= f < c['end_f']: return c
        return None
    def draw(self, frame, f):
        c = self.active(f)
        if not c: return frame
        spr = self.sprite(c['text']); k = f - c['start_f']; fps = self.plan['fps']
        pop = max(2, int(0.1 * fps))
        sc = 1.0
        if k < pop: sc = 0.82 + 0.3 * (k / pop) if k < pop * 0.6 else 1.12 - 0.12 * ((k - pop * 0.6) / (pop * 0.4))
        maxw = int(self.W * 0.94)
        if spr.shape[1] * sc > maxw: sc = maxw / spr.shape[1]
        if abs(sc - 1.0) > 0.01: spr = cv2.resize(spr, (max(2, int(spr.shape[1] * sc)), max(2, int(spr.shape[0] * sc))), interpolation=cv2.INTER_AREA)
        h, w = spr.shape[:2]
        x0 = (self.W - w) // 2; y0 = int(self.H * CAP_Y - h / 2)
        xs, ys = max(0, x0), max(0, y0); xe, ye = min(self.W, x0 + w), min(self.H, y0 + h)
        if xe <= xs or ye <= ys: return frame
        sub = spr[ys - y0:ye - y0, xs - x0:xe - x0]
        a = sub[:, :, 3:4].astype(np.float32) / 255.0
        roi = frame[ys:ye, xs:xe].astype(np.float32)
        frame[ys:ye, xs:xe] = (roi * (1 - a) + sub[:, :, 2::-1].astype(np.float32) * a).astype(np.uint8)
        return frame

class Grader:
    def __init__(self, W, H):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = ((xx - W / 2) / (W / 2)) ** 2 * 0.65 + ((yy - H / 2) / (H / 2)) ** 2 * 0.45
        self.vig = (1 - 0.20 * r)[:, :, None].astype(np.float32)
    def __call__(self, bgr):
        f = bgr.astype(np.float32)
        g = f.mean(axis=2, keepdims=True)
        f = g + (f - g) * 1.10
        f = (f - 128.0) * 1.04 + 128.0 + 3.0
        f *= self.vig
        return np.clip(f, 0, 255).astype(np.uint8)

def fade_factor(f, total, fps):
    k = 1.0
    if f < int(0.15 * fps): k *= 0.35 + 0.65 * f / max(1, int(0.15 * fps))
    if f > total - int(0.5 * fps): k *= max(0.0, (total - f) / max(1, int(0.5 * fps)))
    return k

def encode_shard(plan, frames_dir, f0, f1, out_mp4, crf=16, preset='medium'):
    W, H, fps = plan['width'], plan['height'], plan['fps']
    files = {}
    for p in glob.glob(os.path.join(frames_dir, 'f_*.png')):
        m = re.search(r'f_(\d+)\.png$', p)
        if m: files[int(m.group(1))] = p
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-', '-an',
           '-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-pix_fmt', 'yuv420p', '-g', str(fps * 2), '-keyint_min', str(fps * 2), '-sc_threshold', '0',
           '-x264-params', 'open-gop=0', '-movflags', '+faststart', out_mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    caps = Captions(plan); grade = Grader(W, H); last = None; missing = 0; total = plan['total_frames']
    for f in range(f0, f1):
        img = None
        if f in files: img = cv2.imread(files[f])
        if img is None or img.shape[1] != W:
            missing += 1; img = last if last is not None else np.zeros((H, W, 3), np.uint8)
        last = img
        out = grade(img)
        out = caps.draw(out, f)
        k = fade_factor(f, total, fps)
        if k < 0.999: out = (out.astype(np.float32) * k).astype(np.uint8)
        p.stdin.write(out.tobytes())
    p.stdin.close(); p.wait()
    return missing

if __name__ == '__main__':
    plan = json.load(open(sys.argv[1])); f0, f1 = int(sys.argv[2]), int(sys.argv[3])
    miss = encode_shard(plan, sys.argv[4], f0, f1, sys.argv[5], crf=int(os.environ.get('CRF', '16')), preset=os.environ.get('X264_PRESET', 'medium'))
    print('ENCODED', f0, f1, 'missing_frames=', miss)
