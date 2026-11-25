#!/usr/bin/env bash
# Parcalari birlestirir, sesi + muzigi ekler, dist/video.mp4 uretir.
set -euo pipefail
mkdir -p dist
ls "$PWD"/chunks/*.mp4 | sort | sed "s/^/file '/;s/$/'/" > dist/list.txt
echo "Birlestirilen parca sayisi: $(wc -l < dist/list.txt)"
ffmpeg -y -loglevel error -f concat -safe 0 -i dist/list.txt -c copy dist/video_only.mp4

MUSIC=$(ls assets/music.* 2>/dev/null | head -1 || true)
if [ -n "$MUSIC" ]; then
  echo "Muzik bulundu: $MUSIC"
  ffmpeg -y -loglevel error -i dist/video_only.mp4 -i work/voice.wav -stream_loop -1 -i "$MUSIC" \
    -filter_complex "[1:a]volume=0.8[v];[2:a]volume=0.2[m];[v][m]amix=inputs=2:duration=first:normalize=0[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart dist/video.mp4
else
  echo "Muzik yok, sadece ses ekleniyor."
  ffmpeg -y -loglevel error -i dist/video_only.mp4 -i work/voice.wav \
    -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart dist/video.mp4
fi
ls -lh dist/video.mp4
