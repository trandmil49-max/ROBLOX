"""Story file parser and shot planner (pure Python, no Blender)."""
import re, math, unicodedata, hashlib, json

LEAD_IN = 0.35     # seconds of picture before the voice starts
TAIL = 1.2         # seconds of picture after the last word
MAX_SHOT = 2.0     # no camera angle lasts longer than this (seconds)
MIN_SHOT = 0.7

CAM_ALIASES = {'cu': 'closeup', 'close': 'closeup', 'closeup': 'closeup', 'ecu': 'extreme', 'extreme': 'extreme', 'ws': 'wide', 'wide': 'wide', 'ms': 'medium',
               'medium': 'medium', 'ots': 'over', 'over': 'over', 'est': 'establish', 'establish': 'establish', 'establishing': 'establish', 'low': 'low',
               'high': 'high', 'insert': 'insert', 'dutch': 'dutch', 'full': 'wide'}
MOVES = ('push', 'pull', 'pan', 'static', 'orbit', 'handheld')
EXPR_ALIAS = {'smile': 'happy', 'joy': 'happy', 'glad': 'happy', 'laughing': 'laugh', 'lol': 'laugh', 'crying': 'cry', 'tears': 'cry', 'afraid': 'scared', 'fear': 'scared',
              'mad': 'angry', 'rage': 'furious', 'shock': 'shocked', 'surprise': 'surprised', 'amazed': 'surprised', 'nervous': 'worried', 'anxious': 'worried',
              'bored': 'tired', 'sleep': 'sleepy', 'cool': 'smirk', 'sneaky': 'evil', 'hearts': 'love', 'confused': 'thinking', 'embarrass': 'embarrassed', 'blush': 'embarrassed',
              'grinning': 'grin', 'sad': 'sad', 'neutral': 'neutral'}
ACTION_ALIAS = {'walking': 'walk', 'running': 'run', 'wave': 'wave', 'waving': 'wave', 'pointing': 'point', 'talking': 'talk', 'speak': 'talk', 'stand': 'idle', 'standing': 'idle',
                'sitting': 'sit', 'jumping': 'jump', 'dancing': 'dance', 'crying': 'cry', 'laughing': 'laugh', 'scream': 'shock', 'shocked': 'shock', 'cheer': 'celebrate',
                'thinking': 'think', 'falling': 'fall', 'sleeping': 'sleep', 'hugging': 'hug', 'eating': 'eat', 'drinking': 'drink', 'typing': 'type', 'hiding': 'hide',
                'sneaking': 'sneak', 'leaving': 'leave', 'approaching': 'approach', 'looking': 'look', 'knocking': 'knock'}
VALID_ACTIONS = {'idle', 'talk', 'listen', 'walk', 'walk_l', 'run', 'run_l', 'sneak', 'approach', 'leave', 'wave', 'point', 'shock', 'laugh', 'giggle', 'cry', 'sob', 'sad', 'sulk', 'angry', 'stomp',
                 'jump', 'celebrate', 'sit', 'think', 'fall', 'faint', 'sleep', 'hug', 'shrug', 'shake', 'scared', 'tremble', 'dance', 'eat', 'drink', 'type', 'work', 'look', 'peek', 'knock',
                 'push', 'pull', 'hide'}
from_faces = ['neutral', 'happy', 'grin', 'laugh', 'sad', 'cry', 'angry', 'furious', 'surprised', 'shocked', 'scared', 'worried', 'sleepy', 'smirk', 'wink', 'love', 'dizzy',
              'disgusted', 'evil', 'embarrassed', 'thinking', 'excited', 'tired', 'serious']

# ---------------- text normalisation (5 languages) ----------------
_TR = str.maketrans({'İ': 'i', 'I': 'ı'})
def fold(w):
    w = w.translate(_TR).lower()
    w = ''.join(c for c in unicodedata.normalize('NFKD', w) if not unicodedata.combining(c))
    w = w.replace('ı', 'i').replace('ß', 'ss').replace('ـ', '')
    w = re.sub('[\u064b-\u065f\u0670]', '', w)                    # arabic diacritics
    w = re.sub('[\u0622\u0623\u0625]', '\u0627', w).replace('\u0649', '\u064a').replace('\u0629', '\u0647')
    return re.sub(r"[^\w$%]", '', w)

def norm_tokens(text):
    return [fold(t) for t in text.split()]

def display_word(w):
    w = re.sub(r"^[^\w$%€£]+|[^\w$%€£]+$", '', w)
    return w

LEX = {
    'cabinet': 'cabinet wardrobe closet cupboard dolap dolab gardirop armario ropero armoire placard placards خزانه دولاب خزانة',
    'computer': 'computer pc bilgisayar computadora ordenador ordinateur كمبيوتر حاسوب حاسب',
    'laptop': 'laptop notebook dizustu portatil ordinateur-portable لابتوب',
    'phone': 'phone smartphone telefon celular movil telephone portable هاتف جوال موبايل',
    'headphones': 'headphones earphones headset kulaklik auriculares audifonos casque ecouteurs سماعات سماعه',
    'tv': 'tv television televizyon televisor television تلفزيون تلفاز',
    'bed': 'bed yatak yatag karyola cama lit سرير',
    'sofa': 'sofa couch koltuk kanepe sofa canape اريكه كنبه',
    'table': 'table masa mesa tabla طاوله',
    'chair': 'chair sandalye silla chaise كرسي',
    'desk': 'desk sira escritorio bureau مكتب',
    'lamp': 'lamp light abajur lamba lampara lampe مصباح',
    'door': 'door kapi puerta porte باب',
    'fridge': 'fridge refrigerator buzdolabi nevera refrigerador refrigerateur frigo ثلاجه',
    'bookshelf': 'bookshelf bookcase kitaplik estanteria etagere bibliotheque مكتبه',
    'book': 'book books kitap kitab libro libros livre livres كتاب',
    'backpack': 'backpack schoolbag canta sirt mochila sac-a-dos cartable حقيبه',
    'pizza': 'pizza بيتزا',
    'burger': 'burger hamburger hamburguesa hamburgre برجر همبرجر',
    'cake': 'cake pasta pastasi pastay torta gateau gâteau tarta كعكه كيكه',
    'apple': 'apple elma manzana pomme تفاحه',
    'coffee': 'coffee cup mug kahve fincan bardak cafe cafe tasse taza قهوه فنجان',
    'money': 'money cash dollars dollar para lira dolar dinero dolares argent euros مال فلوس نقود',
    'coin': 'coin coins gold altin madeni moneda pieza piece pièce عمله ذهب',
    'gift': 'gift present hediye regalo cadeau هديه',
    'trophy': 'trophy cup kupa trofeo trophee trophée كاس',
    'ball': 'ball top pelota balon balle كره',
    'balloon': 'balloon balon globo ballon بالون',
    'flower': 'flower flowers cicek flor flores fleur fleurs زهره ورده',
    'plant': 'plant plants bitki planta plante نبته',
    'clock': 'clock saat reloj horloge ساعه',
    'mirror': 'mirror ayna espejo miroir مرايه',
    'bag': 'bag bags canta bolsa bolso sac حقيبه',
    'umbrella': 'umbrella semsiye paraguas parapluie مظله',
    'key': 'key keys anahtar llave cle clef مفتاح',
    'chest': 'chest treasure hazine sandik cofre tresor coffre كنز صندوق',
    'pumpkin': 'pumpkin balkabagi calabaza citrouille قرع يقطين',
    'icecream': 'icecream dondurma helado glace gelato ايس-كريم بوظه',
    'bottle': 'bottle sise botella bouteille زجاجه',
    'car': 'car cars araba otomobil arabasi coche carro auto voiture سياره',
    'dog': 'dog dogs puppy kopek kopeg perro chien كلب',
    'cat': 'cat cats kedi gato chat قطه قط',
    'bird': 'bird birds kus pajaro oiseau عصفور طائر',
    'ghost': 'ghost hayalet fantasma fantome fantôme شبح',
    'monster': 'monster canavar monstruo monstre وحش',
    'rocket': 'rocket roket cohete fusee fusée صاروخ',
    'tree': 'tree trees agac arbol arbre شجره',
}
_LEX_IDX = {}
for kind, words in LEX.items():
    for w in words.split():
        f = fold(w.replace('-', ''))
        if f.startswith('ال') and len(f) > 3: f = f[2:]
        _LEX_IDX[f] = kind
_STEMS = sorted([(w, k) for w, k in _LEX_IDX.items() if len(w) >= 4], key=lambda x: -len(x[0]))

def lexicon_kind(norm):
    """Return the prop kind a (folded) word refers to, or None. Handles suffixes (Turkish), plurals and Arabic prefixes."""
    if not norm: return None
    n = norm
    for pre in ('ال', 'وال', 'بال', 'لل', 'ب', 'و'):
        if n.startswith(pre) and len(n) - len(pre) >= 3 and n[len(pre):] in _LEX_IDX: return _LEX_IDX[n[len(pre):]]
    if n in _LEX_IDX: return _LEX_IDX[n]
    for stem, kind in _STEMS:
        if len(stem) >= 5 and n.startswith(stem) and len(n) <= len(stem) + 5: return kind
        if len(stem) == 4 and n.startswith(stem) and len(n) <= len(stem) + 3 and not re.match(r'^(.)\1', n): return kind
    return None

# ---------------- parsing ----------------
def _kv(parts):
    d = {}
    for p in parts:
        if '=' in p:
            k, v = p.split('=', 1); d[k.strip().lower()] = v.strip()
    return d

def parse_cast_line(line):
    f = [x.strip() for x in line.split('|')]
    name = f[0]; spec = {}
    if len(f) > 1 and '=' not in f[1]: spec['body'] = f[1].lower()
    kv = _kv(f[1:])
    for k, v in kv.items():
        if k == 'hair':
            vv = [x.strip() for x in v.replace(':', ',').split(',')]
            spec['hair'] = vv[0].lower()
            if len(vv) > 1: spec['hair_color'] = vv[1].lower()
        elif k in ('skin', 'top', 'top2', 'bottom', 'shoes', 'outfit', 'pattern', 'acc', 'body', 'sleeves', 'size', 'hair_color', 'cap_color', 'hat_color', 'pack_color', 'tie'):
            spec[k] = float(v) if k == 'size' else v.lower()
    return name, spec

def parse_chars(field):
    out = []
    for item in [x.strip() for x in field.split(',') if x.strip()]:
        focus = item.startswith('*'); item = item.lstrip('*').strip()
        name = item; expr = 'neutral'; action = 'idle'
        if ':' in item: name, action = [x.strip() for x in item.split(':', 1)]
        if '=' in name: name, expr = [x.strip() for x in name.split('=', 1)]
        exprs = [EXPR_ALIAS.get(e.strip().lower(), e.strip().lower()) for e in expr.split('>')]
        exprs = [e if e in from_faces else 'neutral' for e in exprs]
        action = action.strip().lower(); action = ACTION_ALIAS.get(action, action)
        if action not in VALID_ACTIONS: action = 'idle'
        out.append(dict(name=name, expr=exprs[0], exprs=exprs, action=action, focus=focus))
    return out

def parse_story(text):
    lang = 'en'; cast = {}; shots = []; mode = None; last_loc = 'street@day'; last_tod = None
    for raw in text.replace('\r', '').split('\n'):
        line = raw.strip()
        if not line or line.startswith('#'): continue
        u = line.upper()
        if u.startswith('LANG:'): lang = line.split(':', 1)[1].strip().lower()[:2]; continue
        if u.startswith('TITLE:') or u.startswith('DESCRIPTION:') or u.startswith('SEED:'):
            continue
        if u.startswith('CAST'): mode = 'cast'; 
        if u.startswith('SHOTS'): mode = 'shots'; continue
        if mode == 'cast' or u.startswith('CAST |') or u.startswith('CHARACTER |'):
            if u.startswith('CAST') and ':' in line and '|' not in line: continue
            l2 = line.split('|', 1)[1] if u.startswith(('CAST |', 'CHARACTER |')) else line.lstrip('-* ').strip()
            if '|' in l2 or '=' in l2:
                n, s = parse_cast_line(l2); cast[n] = s
            continue
        # shot line
        if '::' not in line: continue
        head, narr = line.split('::', 1)
        head = re.sub(r'^\s*(SHOT\s*\d*\s*\|?|\d+\s*[.)|]\s*)', '', head, flags=re.I)
        f = [x.strip() for x in head.split('|')]
        loc = f[0] if f and f[0] else last_loc
        tod = None
        if '@' in loc: loc, tod = [x.strip() for x in loc.split('@', 1)]
        loc = loc.lower().replace(' ', '_') or 'street'; tod = (tod or last_tod or 'day').lower()
        cam = 'medium'; move = None
        if len(f) > 1 and f[1]:
            c = f[1].lower().split('/')
            cam = CAM_ALIASES.get(c[0].strip(), 'medium')
            if len(c) > 1 and c[1].strip() in MOVES: move = c[1].strip()
        chars = parse_chars(f[2]) if len(f) > 2 else []
        pr = []
        if len(f) > 3:
            pstr = f[3].split('=', 1)[1] if f[3].lower().startswith('props=') else f[3]
            pr = [p.strip().lower() for p in re.split(r'[,;]', pstr) if p.strip()]
        shots.append(dict(loc=loc, tod=tod, cam=cam, move=move, chars=chars, props=pr, narr=narr.strip()))
        last_loc = loc + '@' + tod; last_tod = tod
    return dict(lang=lang, cast=cast, shots=shots)

# ---------------- planning ----------------
def _cam_cycle(base, n_chars, k, seed):
    order = ['medium', 'closeup', 'wide', 'low', 'over', 'closeup', 'medium', 'dutch']
    if n_chars < 2: order = [c for c in order if c != 'over']
    if n_chars == 0: order = ['wide', 'establish', 'low', 'high']
    start = order.index(base) if base in order else 0
    return order[(start + k) % len(order)]

def build_plan(story, word_times, fps, width, height, samples, seed=1, total_audio=None):
    """word_times: list of (start,end) seconds for every narration token (all shots concatenated, same tokenisation as shot narrations)."""
    shots_in = story['shots']; toks_per = []; idx = 0; disp = []
    for sh in shots_in:
        ws = sh['narr'].split(); toks_per.append((idx, idx + len(ws))); idx += len(ws)
        for w in ws: disp.append(display_word(w))
    if idx != len(word_times): raise ValueError(f'word_times has {len(word_times)} entries but story has {idx} words')
    last_end = word_times[-1][1] if word_times else 1.0
    end_t = (total_audio or last_end) + LEAD_IN + TAIL
    # shot boundaries in video time
    starts = []
    for i, (a, b) in enumerate(toks_per):
        t = (word_times[a][0] + LEAD_IN) if b > a and a < len(word_times) else (starts[-1] if starts else 0.0)
        starts.append(max(0.0, t))
    starts[0] = 0.0
    for i in range(1, len(starts)): starts[i] = max(starts[i], starts[i - 1] + 0.05)
    bounds = starts + [end_t]
    plan_shots = []; sid = 0; auto_last = {}
    cast = story['cast']
    for i, sh in enumerate(shots_in):
        t0, t1 = bounds[i], bounds[i + 1]; dur = t1 - t0
        a, b = toks_per[i]
        # auto props from lexicon: (kind, time)
        auto = []
        for w_i in range(a, b):
            kind = lexicon_kind(fold(disp[w_i]))
            if kind and kind not in sh['props']:
                tw = word_times[w_i][0] + LEAD_IN
                if tw - auto_last.get(kind, -99) > 3.5: auto.append((kind, tw)); auto_last[kind] = tw
        explicit = list(sh['props'])
        n_sub = max(1, math.ceil(dur / MAX_SHOT - 1e-6)) if dur > MAX_SHOT else 1
        if dur / n_sub < MIN_SHOT: n_sub = max(1, int(dur / MIN_SHOT))
        cuts = [t0 + dur * k / n_sub for k in range(n_sub)] + [t1]
        # insert shot for auto props when the base camera is a close shot or there is no room
        for k in range(n_sub):
            s0, s1 = cuts[k], cuts[k + 1]
            cam = sh['cam'] if k == 0 else _cam_cycle(sh['cam'], len(sh['chars']), k, i)
            move = sh['move'] or MOVES[(sid + k) % 4 if (sid + k) % 6 else 5]
            if k > 0 and move == 'static': move = 'push'
            props_here = [dict(kind=p, at_f=None) for p in explicit]
            insert_props = []
            for kind, tw in auto:
                if s0 - 0.25 <= tw < s1:
                    if cam in ('closeup', 'extreme', 'close') or (s1 - s0) < 1.1: insert_props.append(kind)
                    else: props_here.append(dict(kind=kind, at_f=int(round(tw * fps))))
            if insert_props:
                cam = 'insert'; props_here = [dict(kind=insert_props[0], at_f=None)]
            ch = sh['chars']
            if cam == 'insert' and ch: ch = ch[:1]  # keep one character (off-frame partner) for continuity
            plan_shots.append(dict(id=sid, start_f=int(round(s0 * fps)), end_f=int(round(s1 * fps)), loc=sh['loc'], tod=sh['tod'], cam=cam, move=move, side=((sid * 37) % 41) - 20,
                                   chars=[dict(c) for c in ch], props=props_here, src=i))
            sid += 1
    # make frame ranges contiguous & non-empty
    for k, s in enumerate(plan_shots):
        if k + 1 < len(plan_shots): s['end_f'] = plan_shots[k + 1]['start_f']
        else: s['end_f'] = int(round(end_t * fps))
        if s['end_f'] <= s['start_f']: s['end_f'] = s['start_f'] + 1
    plan_shots[0]['start_f'] = 0
    total = plan_shots[-1]['end_f']
    # caption words
    caps = []
    for w_i, (ts, te) in enumerate(word_times):
        if not disp[w_i]: continue
        caps.append(dict(text=disp[w_i], start_f=int(round((ts + LEAD_IN) * fps)), end_f=int(round((te + LEAD_IN) * fps))))
    for k in range(len(caps) - 1):   # hold each word until the next one starts (single word on screen, never overlapping)
        if caps[k]['end_f'] > caps[k + 1]['start_f']: caps[k]['end_f'] = caps[k + 1]['start_f']
        if caps[k + 1]['start_f'] - caps[k]['end_f'] < int(0.25 * fps): caps[k]['end_f'] = caps[k + 1]['start_f']
        if caps[k]['end_f'] <= caps[k]['start_f']: caps[k]['end_f'] = caps[k]['start_f'] + 1
    if caps: caps[-1]['end_f'] = max(caps[-1]['end_f'], caps[-1]['start_f'] + int(0.4 * fps))
    return dict(fps=fps, width=width, height=height, samples=samples, seed=seed, lang=story['lang'], cast=cast, shots=plan_shots, captions=caps,
                total_frames=total, duration=total / fps, lead_in=LEAD_IN)

def needed_faces(plan):
    """List of (expr, flags) face images required by the plan."""
    out = set()
    for s in plan['shots']:
        for c in s['chars']:
            spec = plan['cast'].get(c['name'], {}); acc = spec.get('acc', '')
            flags = dict(glasses='glasses' in acc, mustache=('mustache' in acc or 'beard' in acc), lashes=spec.get('body') in ('girl', 'woman', 'granny'), freckles='freckles' in acc)
            for e in c.get('exprs') or [c['expr']]: out.add((e, tuple(sorted(flags.items()))))
    return out
