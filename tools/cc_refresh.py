#!/usr/bin/env python3
"""Regenerate ALL CC tracks with the current (sharpened) style contracts.
Archives the old set to cc_out_v1 instead of overwriting. Rebuilds the
docs/grids four-ups. Self-manages the GPU."""
import glob
import os
import shutil
import subprocess
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
os.environ.setdefault("SCENE_MAX_TOKENS", "3000")


def key():
    for line in open(".env", encoding="utf-8"):
        if line.startswith("FIREWORKS_API_KEY="):
            return line.split("=", 1)[1].strip()
    return ""


def scale(n):
    r = requests.patch(
        "https://api.fireworks.ai/v1/accounts/banksythequant/deployments/"
        "gemma4cap?updateMask=min_replica_count",
        headers={"Authorization": f"Bearer {key()}"},
        json={"minReplicaCount": n}, timeout=30)
    print(f"scale min={n}: {r.status_code}", flush=True)


def ready():
    r = requests.get(
        "https://api.fireworks.ai/v1/accounts/banksythequant/deployments/"
        "gemma4cap", headers={"Authorization": f"Bearer {key()}"}, timeout=30)
    return r.json().get("replicaStats", {}).get("readyReplicaCount", 0) >= 1


# 1. archive old set (version, don't destroy)
if os.path.isdir("cc_out") and not os.path.isdir("cc_out_v1"):
    shutil.move("cc_out", "cc_out_v1")
    print("archived cc_out -> cc_out_v1", flush=True)
os.makedirs("cc_out", exist_ok=True)

# 2. wake GPU
scale(1)
for _ in range(60):
    if ready():
        print("GPU ready", flush=True)
        break
    time.sleep(10)

# 3. regenerate all 15 with current contracts (retry pass included)
clips = sorted(glob.glob("official_clips/*.mp4"))
for rnd in (1, 2):
    for clip in clips:
        base = os.path.splitext(os.path.basename(clip))[0]
        if os.path.exists(f"cc_out/{base}_cc.json"):
            continue
        print(f"=== r{rnd} {base}", flush=True)
        r = subprocess.run([sys.executable, "-u", "tools/textsink_cc.py",
                            "--clip", clip, "--out", "cc_out", "--burn"],
                           capture_output=True, text=True)
        tail = (r.stderr or "").strip().splitlines()[-1:] or ["?"]
        print(f"    exit={r.returncode} {tail[0]}", flush=True)

scale(0)

# 4. rebuild grids from the new tracks
for f in glob.glob("docs/grids/*.mp4"):
    os.remove(f)
r = subprocess.run([sys.executable, "-u", "tools/make_grids.py"],
                   capture_output=True, text=True)
print(r.stdout[-300:], flush=True)
print("CC REFRESH DONE", flush=True)
