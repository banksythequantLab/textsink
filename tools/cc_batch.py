#!/usr/bin/env python3
"""Overnight driver: CC + Hecklers over all official clips, then unpin GPU."""
import glob
import os
import subprocess
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
os.environ.setdefault("SCENE_MAX_TOKENS", "3000")

clips = sorted(glob.glob(os.path.join(ROOT, "official_clips", "*.mp4")))
for i, clip in enumerate(clips, 1):
    print(f"=== ({i}/{len(clips)}) {os.path.basename(clip)}", flush=True)
    for tool, out in (("tools/textsink_cc.py", "cc_out"),
                      ("tools/hecklers.py", "heckle_out")):
        r = subprocess.run([sys.executable, "-u", tool, "--clip", clip,
                            "--out", out, "--burn"],
                           capture_output=True, text=True)
        tail = (r.stderr or "").strip().splitlines()[-1:] or ["?"]
        print(f"    {tool}: exit={r.returncode} {tail[0]}", flush=True)

# release the GPU
key = ""
for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    if line.startswith("FIREWORKS_API_KEY="):
        key = line.split("=", 1)[1].strip()
resp = requests.patch(
    "https://api.fireworks.ai/v1/accounts/banksythequant/deployments/"
    "gemma4cap?updateMask=min_replica_count",
    headers={"Authorization": f"Bearer {key}"},
    json={"minReplicaCount": 0}, timeout=30)
print(f"BATCH DONE - unpin status {resp.status_code}", flush=True)
