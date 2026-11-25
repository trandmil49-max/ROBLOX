#!/usr/bin/env bash
# dist/video.mp4'u herkese acik ama tahmin edilemez bir linkle yayinlar ve Telegram'a yollar.
set -euo pipefail
TAG="v$(date +%s)-$RANDOM$RANDOM"
gh release create "$TAG" dist/video.mp4 --title "Video $TAG" --notes "Gecici video, 24 saat sonra silinir."
LINK="https://github.com/${GITHUB_REPOSITORY}/releases/download/${TAG}/video.mp4"
SIZE=$(du -h dist/video.mp4 | cut -f1)
python3 bot/notify.py "Video hazir ($SIZE)

$LINK

Link 24 saat sonra otomatik silinir. Indirdikten sonra hemen silmek icin /sil yaz."
bash bot/cleanup.sh 24
