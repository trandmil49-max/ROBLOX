"""Sesi hazirlar, videoyu parcalara boler (plan.json) ve GitHub'a parca listesini verir."""
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import tg  # noqa: E402

WORK = "work"
FPS = int(os.environ.get("VIDEO_FPS", "60"))
W = int(os.environ.get("VIDEO_W", "1920"))
H = int(os.environ.get("VIDEO_H", "1080"))
CHUNK_SECONDS = int(os.environ.get("CHUNK_SECONDS", "10"))
TAIL_SECONDS = 0.5
MAX_MINUTES = 20


def sh(*cmd):
    subprocess.run(cmd, check=True)


def main():
    os.makedirs(WORK, exist_ok=True)
    file_id = os.environ["AUDIO_FILE_ID"].strip()
    script = os.environ.get("SCRIPT", "").strip()

    if file_id == "TEST":
        sh("ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
           "anullsrc=r=48000:cl=stereo", "-t", "25", f"{WORK}/voice.wav")
    else:
        raw = f"{WORK}/voice_raw"
        tg.download_file(file_id, raw)
        sh("ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-vn", "-ar", "48000", "-ac", "2", f"{WORK}/voice.wav")
        os.remove(raw)

    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", f"{WORK}/voice.wav"],
        capture_output=True, text=True, check=True).stdout.strip()
    duration = float(out)
    if duration < 1:
        raise SystemExit("Ses dosyasi cok kisa veya okunamadi.")
    if duration > MAX_MINUTES * 60:
        raise SystemExit(f"Ses {MAX_MINUTES} dakikadan uzun.")

    chunk_frames = CHUNK_SECONDS * FPS
    total_frames = math.ceil((duration + TAIL_SECONDS) * FPS)
    n_chunks = math.ceil(total_frames / chunk_frames)

    with open(f"{WORK}/script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    plan = {"fps": FPS, "w": W, "h": H, "duration": duration, "chunk_frames": chunk_frames,
            "total_frames": total_frames, "n_chunks": n_chunks}
    with open(f"{WORK}/plan.json", "w") as f:
        json.dump(plan, f)

    print(f"Sure: {duration:.1f}s, kare: {total_frames}, parca: {n_chunks}")
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write(f"chunks={json.dumps(list(range(n_chunks)))}\n")


if __name__ == "__main__":
    main()
