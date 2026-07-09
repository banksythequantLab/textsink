#!/usr/bin/env python3
"""Full Hecklers matrix: every clip x every flavor (45 tracks), then unpin."""
import glob
import os
import subprocess
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
os.environ.setdefault("SCENE_MAX_TOKENS", "3000")
FLAVORS = ["sarcastic", "humorous_tech", "humorous_non_tech"]


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
for _ in range(60):
    if ready():
        print("GPU ready", flush=True)
        break
    time.sleep(10)

clips = sorted(glob.glob(os.path.join(ROOT, "official_clips", "*.mp4")))
todo = []
for clip in clips:
    base = os.path.splitext(os.path.basename(clip))[0]
    for flavor in FLAVORS:
        if not os.path.exists(f"heckle_out/{base}_hecklers_{flavor}.json"):
            todo.append((clip, base, flavor))
print(f"{len(todo)} runs to do", flush=True)

ok = fail = 0
for i, (clip, base, flavor) in enumerate(todo, 1):
    print(f"=== ({i}/{len(todo)}) {base} [{flavor}]", flush=True)
    r = subprocess.run([sys.executable, "-u", "tools/hecklers.py",
                        "--clip", clip, "--out", "heckle_out", "--burn",
                        "--spice", "eleven", "--flavor", flavor],
                       capture_output=True, text=True)
    tail = (r.stderr or "").strip().splitlines()[-1:] or ["?"]
    print(f"    exit={r.returncode} {tail[0]}", flush=True)
    ok, fail = ok + (r.returncode == 0), fail + (r.returncode != 0)

# one retry pass for stragglers (model flakiness is transient)
for clip, base, flavor in todo:
    if not os.path.exists(f"heckle_out/{base}_hecklers_{flavor}.json"):
        print(f"=== RETRY {base} [{flavor}]", flush=True)
        r = subprocess.run([sys.executable, "-u", "tools/hecklers.py",
                            "--clip", clip, "--out", "heckle_out", "--burn",
                            "--spice", "eleven", "--flavor", flavor],
                           capture_output=True, text=True)
        print(f"    exit={r.returncode}", flush=True)

done = len(glob.glob("heckle_out/*_hecklers_*.json"))
scale(0)
print(f"MATRIX DONE: {done} flavor tracks on disk", flush=True)
