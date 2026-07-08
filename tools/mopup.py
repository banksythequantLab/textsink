#!/usr/bin/env python3
"""Targeted rerun: only clips missing CC or Hecklers output, then unpin."""
import glob
import os
import subprocess
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
os.environ.setdefault("SCENE_MAX_TOKENS", "3000")


def key():
    for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
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


scale(1)
for i in range(60):
    if ready():
        print("GPU ready", flush=True)
        break
    time.sleep(10)

clips = sorted(glob.glob(os.path.join(ROOT, "official_clips", "*.mp4")))
for clip in clips:
    base = os.path.splitext(os.path.basename(clip))[0]
    jobs = []
    if not os.path.exists(f"cc_out/{base}_cc.json"):
        jobs.append(("tools/textsink_cc.py", "cc_out"))
    if not (os.path.exists(f"heckle_out/{base}_hecklers_sarcastic.json")
            or os.path.exists(f"heckle_out/{base}_hecklers.json")):
        jobs.append(("tools/hecklers.py", "heckle_out"))
    for tool, out in jobs:
        print(f"=== {base} {tool}", flush=True)
        r = subprocess.run([sys.executable, "-u", tool, "--clip", clip,
                            "--out", out, "--burn"],
                           capture_output=True, text=True)
        tail = (r.stderr or "").strip().splitlines()[-1:] or ["?"]
        print(f"    exit={r.returncode} {tail[0]}", flush=True)

scale(0)
print("MOPUP DONE", flush=True)
