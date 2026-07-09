#!/usr/bin/env python3
"""List tracks whose dialogue/captions end early vs actual clip duration."""
import glob
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True).stdout.strip()
    return float(out or 0)


durs = {os.path.splitext(os.path.basename(p))[0]: dur(p)
        for p in glob.glob("official_clips/*.mp4")}

short_h, short_c = [], []
for p in glob.glob("heckle_out/*_hecklers_*.json"):
    d = json.load(open(p, encoding="utf-8"))
    base = os.path.basename(p).split("_hecklers_")[0]
    flavor = os.path.basename(p).split("_hecklers_")[1].replace(".json", "")
    if not d.get("dialogue"):
        continue
    last = max(float(l["end"]) for l in d["dialogue"])
    total = durs.get(base, 0)
    if total - last > 2.0:
        short_h.append((base, flavor, round(last, 1), round(total, 1)))

for p in glob.glob("cc_out/*_cc.json"):
    d = json.load(open(p, encoding="utf-8"))
    base = os.path.basename(p).replace("_cc.json", "")
    total = durs.get(base, 0)
    for style, lines in d.get("tracks", {}).items():
        if not lines:
            continue
        ends = [float(l.get("end", l.get("start", 0) or 0)) for l in lines]
        last = max(ends) if ends else 0
        if total - last > 2.0:
            short_c.append((base, style, round(last, 1), round(total, 1)))

print(f"HECKLERS short: {len(short_h)}")
for r in short_h:
    print("  ", r)
print(f"CC short: {len(short_c)}")
for r in short_c:
    print("  ", r)
