"""Step 1 of a render: story file + voice recording -> plan.json (+ face images). Pure Python."""
import os, sys, json, argparse, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import story as S, align as A
from faces_gen import ensure_face

PRESETS = {  # width, height, fps, samples
    'final': (1080, 1920, 60, 10),
    'draft': (540, 960, 30, 8),
    'test':  (540, 960, 30, 6),
    'tiny':  (360, 640, 12, 6),
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--story', required=True); ap.add_argument('--voice', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--quality', default='final'); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--fps', type=int); ap.add_argument('--shards', type=int, default=20)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    text = open(a.story, encoding='utf-8').read()
    st = S.parse_story(text)
    if not st['shots']: raise SystemExit('The story file has no shots. Each shot line needs "::" before the narration.')
    tokens = []
    for sh in st['shots']: tokens += sh['narr'].split()
    times, total, info = A.word_times(a.voice, tokens, st['lang'], os.path.join(a.out, 'audio'))
    W, H, fps, samples = PRESETS.get(a.quality, PRESETS['final'])
    if a.fps: fps = a.fps
    plan = S.build_plan(st, times, fps, W, H, samples, a.seed, total)
    plan['align'] = info
    faces_dir = os.path.join(a.out, 'frames', '_faces')
    for expr, flags in S.needed_faces(plan): ensure_face(faces_dir, expr, **dict(flags))
    # shard boundaries (cut on shot boundaries where possible so that shots are not rebuilt twice)
    n = max(1, min(a.shards, math.ceil(plan['total_frames'] / (fps * 2))))
    per = math.ceil(plan['total_frames'] / n)
    shards = []
    for i in range(n):
        f0 = i * per; f1 = min(plan['total_frames'], (i + 1) * per)
        if f1 > f0: shards.append([f0, f1])
    plan['shards'] = shards
    json.dump(plan, open(os.path.join(a.out, 'plan.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(dict(frames=plan['total_frames'], seconds=round(plan['duration'], 1), shots=len(plan['shots']), shards=len(shards), align=info, fps=fps, size=f'{W}x{H}')))

if __name__ == '__main__': main()
