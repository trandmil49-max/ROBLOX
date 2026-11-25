"""
DEMO RENDERER (pipeline testi icin).

Bu dosya gercek video stilinin yerine gecici olarak durur: koyu mavi arka plan,
ustte parca bilgisi, ortada o saniyelerde okunan senaryo kelimeleri.

GERCEK STIL KODU BU DOSYANIN YERINE GECECEK. Ayni komut satirini kabul etmesi yeterli:

    python3 renderer/render_chunk.py --work work --chunk 3 --out out/chunk_0003.mp4

work/plan.json  : fps, w, h, duration, chunk_frames, total_frames, n_chunks
work/script.txt : senaryo metni
work/voice.wav  : ses
Cikti: TAM olarak [chunk*chunk_frames, ...) araligindaki kareleri iceren,
       fps'te sabit kare hizli, yuv420p, sesi OLMAYAN bir mp4 (h264).
"""
import argparse
import json
import os
import subprocess
import textwrap

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]


def find_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit("Yazi tipi bulunamadi (DejaVuSans-Bold).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="work")
    ap.add_argument("--chunk", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    plan = json.load(open(os.path.join(a.work, "plan.json")))
    fps, w, h = plan["fps"], plan["w"], plan["h"]
    start = a.chunk * plan["chunk_frames"]
    n = min(plan["chunk_frames"], plan["total_frames"] - start)
    if n <= 0:
        raise SystemExit("Bu parca bos.")
    t0 = start / fps
    t1 = (start + n) / fps

    script = open(os.path.join(a.work, "script.txt"), encoding="utf-8").read().split()
    dur = plan["duration"]
    i0 = int(len(script) * min(t0 / dur, 1.0))
    i1 = max(i0, int(len(script) * min(t1 / dur, 1.0)))
    caption = textwrap.fill(" ".join(script[i0:i1]) or " ", width=34)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    cap_file = os.path.abspath(a.out) + ".txt"
    with open(cap_file, "w", encoding="utf-8") as f:
        f.write(caption)

    font = find_font()
    vf = (
        f"drawtext=fontfile={font}:text='DEMO RENDER  parca {a.chunk + 1}/{plan['n_chunks']}':"
        f"fontcolor=white:fontsize={h // 20}:x=(w-text_w)/2:y={h // 14},"
        f"drawtext=fontfile={font}:textfile={cap_file}:fontcolor=white:fontsize={h // 14}:"
        f"line_spacing=12:x=(w-text_w)/2:y=(h-text_h)/2,"
        f"drawtext=fontfile={font}:text='%{{eif\\:t+{t0:.3f}\\:d}} sn':"
        f"fontcolor=yellow:fontsize={h // 20}:x=(w-text_w)/2:y=h-{h // 7}"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"color=c=0x14213d:s={w}x{h}:r={fps}",
        "-vf", vf, "-frames:v", str(n),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(fps), "-g", str(fps), "-keyint_min", str(fps),
        "-sc_threshold", "0", "-an", a.out,
    ]
    subprocess.run(cmd, check=True)
    os.remove(cap_file)
    print(f"parca {a.chunk}: {n} kare -> {a.out}")


if __name__ == "__main__":
    main()
