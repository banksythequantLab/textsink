#!/usr/bin/env bash
# Generate a short synthetic test clip (video + tone audio) to verify the
# frame-sampling and audio-extraction pipeline locally without real footage.
set -euo pipefail
OUT="${1:-test_clip.mp4}"
DUR="${2:-40}"
ffmpeg -y \
  -f lavfi -i "testsrc=duration=${DUR}:size=640x360:rate=25" \
  -f lavfi -i "sine=frequency=440:duration=${DUR}" \
  -shortest -pix_fmt yuv420p -c:v libx264 -c:a aac "${OUT}"
echo "wrote ${OUT} (${DUR}s)"
