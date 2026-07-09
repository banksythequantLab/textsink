#!/usr/bin/env python3
"""Delete heckler jsons whose dialogue ends >2s before clip end, so
heckler_matrix.py regenerates them with the full-duration argue loop."""
import glob
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def dur_of(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True).stdout.strip()
    return float(out or 0)


durs = {os.path.splitext(os.path.basename(p))[0]: dur_of(p)
        for p in glob.glob("official_clips/*.mp4")}

n = 0
for p in sorted(glob.glob("heckle_out/*_hecklers_*.json")):
    d = json.load(open(p, encoding="utf-8"))
    base = os.path.basename(p).split("_hecklers_")[0]
    if not d.get("dialogue"):
        os.remove(p)
        n += 1
        continue
    last = max(float(l["end"]) for l in d["dialogue"])
    if durs.get(base, 0) - last > 2.0:
        os.remove(p)
        print(f"purged {os.path.basename(p)} (ends {last:.1f}s of "
              f"{durs.get(base, 0):.1f}s)", flush=True)
        n += 1
print(f"purged {n} short tracks", flush=True)
