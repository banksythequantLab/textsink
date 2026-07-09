#!/usr/bin/env python3
"""2x2 four-voices CC grid for every clip that has all four style tracks.
Output: docs/grids/<clip>_fourvoices.mp4 (1280x720, no audio, web-ready)."""
import glob
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
os.makedirs("docs/grids", exist_ok=True)

STYLES = ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]
made = skipped = 0
for clip in sorted(glob.glob("official_clips/*.mp4")):
    base = os.path.splitext(os.path.basename(clip))[0]
    srcs = [f"cc_out/{base}_{s}_cc.mp4" for s in STYLES]
    if not all(os.path.exists(s) for s in srcs):
        print(f"skip {base}: missing style track(s)", flush=True)
        skipped += 1
        continue
    out = f"docs/grids/{base}_fourvoices.mp4"
    if os.path.exists(out):
        made += 1
        continue
    args = ["ffmpeg", "-y", "-v", "error"]
    for s in srcs:
        args += ["-i", s]
    args += ["-filter_complex",
             "[0:v]scale=640:-2[a];[1:v]scale=640:-2[b];"
             "[2:v]scale=640:-2[c];[3:v]scale=640:-2[d];"
             "[a][b][c][d]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0,"
             # letterbox below the grid so player controls never cover
             # the bottom quadrants' captions (esp. in fullscreen)
             "pad=iw:ih+84:0:0:0x0A0D16,format=yuv420p[v]",
             "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "24", "-movflags", "+faststart", out]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode == 0:
        mb = os.path.getsize(out) / 1e6
        print(f"grid {base} ({mb:.1f} MB)", flush=True)
        made += 1
    else:
        print(f"FAIL {base}: {r.stderr[-200:]}", flush=True)

total = sum(os.path.getsize(p) for p in glob.glob("docs/grids/*.mp4")) / 1e6
print(f"DONE: {made} grids, {skipped} skipped, {total:.0f} MB total",
      flush=True)
