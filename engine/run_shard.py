"""Renders one chunk of one shard: Blender frames -> finished frames -> mini video. Usage:
   python3 engine/run_shard.py --plan plan.json --work work --index 3 --chunk 2 --chunks 5"""
import os, sys, json, subprocess, argparse, shutil, glob
HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', required=True); ap.add_argument('--work', required=True); ap.add_argument('--index', type=int, required=True)
    ap.add_argument('--chunk', type=int, default=0); ap.add_argument('--chunks', type=int, default=1); ap.add_argument('--faces')
    a = ap.parse_args()
    plan = json.load(open(a.plan)); f0, f1 = plan['shards'][a.index] if a.index < len(plan['shards']) else (0, 0)
    n = f1 - f0
    c0 = f0 + n * a.chunk // a.chunks; c1 = f0 + n * (a.chunk + 1) // a.chunks
    if c1 <= c0: print('empty chunk'); return
    fr = os.path.join(a.work, f'frames_{a.index}_{a.chunk}'); os.makedirs(fr, exist_ok=True)
    if a.faces and os.path.isdir(a.faces): shutil.copytree(a.faces, os.path.join(fr, '_faces'), dirs_exist_ok=True)
    blender = os.environ.get('BLENDER', 'blender')
    cmd = ['xvfb-run', '-a', '-s', '-screen 0 1280x1024x24', blender, '-b', '--factory-startup', '-P', os.path.join(HERE, 'render_shard.py'), '--', a.plan, str(c0), str(c1), fr]
    if shutil.which('xvfb-run') is None: cmd = cmd[3:]
    print('RUN', ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=False)
    os.makedirs(os.path.join(a.work, 'parts'), exist_ok=True)
    out = os.path.join(a.work, 'parts', f'mini_{a.index:03d}_{a.chunk:02d}.mp4')
    env = dict(os.environ)
    subprocess.run([sys.executable, os.path.join(HERE, 'post.py'), a.plan, str(c0), str(c1), fr, out], check=True, env=env)
    shutil.rmtree(fr, ignore_errors=True)

if __name__ == '__main__': main()
