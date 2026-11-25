#!/usr/bin/env bash
# Kullanim: bash bot/cleanup.sh 24   -> 24 saatten eski videolari siler
#           bash bot/cleanup.sh all  -> hepsini siler
set -uo pipefail
ARG="${1:-24}"
NOW=$(date +%s)
gh release list --limit 100 --json tagName,createdAt 2>/dev/null | jq -r '.[] | "\(.tagName) \(.createdAt)"' | while read -r TAG CREATED; do
  if [ "$ARG" = "all" ]; then
    DEL=1
  else
    AGE=$(( NOW - $(date -d "$CREATED" +%s) ))
    if [ "$AGE" -gt $(( ARG * 3600 )) ]; then DEL=1; else DEL=0; fi
  fi
  if [ "$DEL" = "1" ]; then
    echo "Siliniyor: $TAG"
    gh release delete "$TAG" --yes --cleanup-tag || true
  fi
done
exit 0
