"""Joins shard videos, mixes audio (voice 80% + music 20%), writes final.mp4 and a Telegram-sized preview."""
import os, sys, json, subprocess, glob, math

def run(cmd): subprocess.run(cmd, check=True)
def dur(path): return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip())

def assemble(parts_dir, plan_path, voice, music, out_dir, voice_gain=0.8, music_gain=0.2):
    plan = json.load(open(plan_path)); os.makedirs(out_dir, exist_ok=True)
    parts = sorted(glob.glob(os.path.join(parts_dir, 'part_*.mp4')))
    if not parts: raise SystemExit('no parts found')
    lst = os.path.join(out_dir, 'parts.txt')
    with open(lst, 'w') as f:
        for p in parts: f.write(f"file '{os.path.abspath(p)}'\n")
    silent = os.path.join(out_dir, 'silent.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent])
    T = plan['total_frames'] / plan['fps']; lead = plan.get('lead_in', 0.35); d_ms = int(lead * 1000)
    final = os.path.join(out_dir, 'final.mp4')
    fc = (f"[1:a]aresample=48000,adelay={d_ms}|{d_ms},loudnorm=I=-16:TP=-1.5:LRA=11,volume={voice_gain}[v];"
          f"[2:a]aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=11,volume={music_gain},afade=t=in:st=0:d=1.0,afade=t=out:st={max(0.1, T - 2.2):.2f}:d=2.0[m];"
          f"[v][m]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:{T:.3f}[a]")
    run(['ffmpeg', '-v', 'error', '-y', '-i', silent, '-i', voice, '-stream_loop', '-1', '-i', music, '-filter_complex', fc, '-map', '0:v', '-map', '[a]',
         '-t', f'{T:.3f}', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', final])
    size = os.path.getsize(final)
    # Telegram-sized preview (bots may upload up to ~50 MB)
    prev = os.path.join(out_dir, 'preview.mp4'); target = 44 * 1024 * 1024
    if size <= 48 * 1024 * 1024:
        prev = final
    else:
        vb = int((target * 8 / T - 128000) / 1000)
        run(['ffmpeg', '-v', 'error', '-y', '-i', final, '-vf', 'scale=720:1280', '-r', '30', '-c:v', 'libx264', '-preset', 'medium', '-b:v', f'{max(400, vb)}k',
             '-maxrate', f'{int(max(400, vb) * 1.3)}k', '-bufsize', f'{int(max(400, vb) * 2)}k', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', prev])
    info = dict(final=final, preview=prev, size_mb=round(size / 1048576, 1), preview_mb=round(os.path.getsize(prev) / 1048576, 1), duration=round(T, 2))
    json.dump(info, open(os.path.join(out_dir, 'info.json'), 'w'))
    return info

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--parts'); ap.add_argument('--plan'); ap.add_argument('--voice'); ap.add_argument('--music'); ap.add_argument('--out')
    a = ap.parse_args(); print(assemble(a.parts, a.plan, a.voice, a.music, a.out))
