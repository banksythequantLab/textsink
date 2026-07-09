#!/usr/bin/env python3
"""Letterboxed web copies of the heckler videos for the Pages gallery.
Sarcastic (STAN & GUS) + humorous_tech (LINT vs VIBE) for every clip."""
import glob
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
os.makedirs("docs/hecklers", exist_ok=True)

FLAVORS = ["sarcastic", "humorous_tech"]
made = 0
for clip in sorted(glob.glob("official_clips/*.mp4")):
    base = os.path.splitext(os.path.basename(clip))[0]
    for fl in FLAVORS:
        src = f"heckle_out/{base}_hecklers_{fl}.mp4"
        out = f"docs/hecklers/{base}_{fl}.mp4"
        if not os.path.exists(src) or os.path.exists(out):
            continue
        r = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", src,
             "-vf", "scale=1280:-2,pad=iw:ih+84:0:0:0x0A0D16,format=yuv420p",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
             "-an", "-movflags", "+faststart", out],
            capture_output=True, text=True)
        if r.returncode == 0:
            made += 1
            print(f"{base} [{fl}] ok", flush=True)
        else:
            print(f"{base} [{fl}] FAIL {r.stderr[-120:]}", flush=True)

total = sum(os.path.getsize(p) for p in glob.glob("docs/hecklers/*.mp4")) / 1e6
print(f"DONE: {made} heckler videos, {total:.0f} MB", flush=True)
