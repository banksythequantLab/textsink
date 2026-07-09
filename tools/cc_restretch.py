#!/usr/bin/env python3
"""Re-time short CC tracks to full clip duration and re-burn. No GPU.

The beat times in existing _cc.json files are compressed (model ignored
timestamp labels). Since frames were sampled evenly across the whole clip,
a proportional stretch restores sync. Last line holds to the end.
"""
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.textsink_cc import burn, write_tracks  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def dur_of(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True).stdout.strip()
    return float(out or 0)


fixed = 0
for jp in sorted(glob.glob("cc_out/*_cc.json")):
    base = os.path.basename(jp).replace("_cc.json", "")
    clip = None
    for c in glob.glob(f"official_clips/{base}.*"):
        clip = c
        break
    if not clip:
        continue
    dur = dur_of(clip)
    d = json.load(open(jp, encoding="utf-8"))
    changed = False
    for style, lines in d.get("tracks", {}).items():
        if not lines:
            continue
        ends = [float(l.get("end", 0) or 0) for l in lines]
        last = max(ends)
        if dur - last <= 2.0:
            continue
        k = dur / last if last > 0 else 1.0
        for l in lines:
            l["start"] = round(float(l.get("start", 0)) * k, 2)
            l["end"] = round(float(l.get("end", 0)) * k, 2)
        # hold the final caption to the very end
        lines[-1]["end"] = round(dur, 2)
        changed = True
        ass_p = write_tracks(style, lines, dur, "cc_out", base)
        burn(clip, ass_p, os.path.join("cc_out", f"{base}_{style}_cc.mp4"))
        print(f"restretched {base} [{style}] -> {dur:.1f}s", flush=True)
        fixed += 1
    if changed:
        d["duration"] = dur
        json.dump(d, open(jp, "w", encoding="utf-8"), indent=2,
                  ensure_ascii=False)

print(f"DONE: {fixed} tracks re-timed and re-burned", flush=True)
