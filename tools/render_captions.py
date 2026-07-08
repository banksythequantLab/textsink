#!/usr/bin/env python3
"""TextSink Render - burn styled, animated vector-type captions into clips.

Four motion identities (ASS/libass kinetic type via ffmpeg):
  formal            broadcast lower-third, serif, slow fade
  sarcastic         deadpan typewriter, pregnant pause before the punch word
  humorous_tech     terminal: monospace green on dark box, typed with cursor
  humorous_non_tech warm rounded type, per-word bounce, amber accent

Usage:
  python tools/render_captions.py --results results.json --clips <folder>
         --out renders [--grid]
--grid additionally makes a 2x2 same-clip four-voices video per task.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys

AMBER = "&H0007C1FF"   # #FFC107 in ASS BGR
WHITE = "&H00FFFFFF"
GREEN = "&H0050FF50"
DARK = "&HA0101010"    # translucent dark box

STYLE_DEFS = {
    # font, size, text color, box color, bold
    "formal": ("Georgia", 50, WHITE, "&H60000000", -1),
    "sarcastic": ("Courier New", 52, WHITE, "&H60000000", -1),
    "humorous_tech": ("Consolas", 48, GREEN, "&H50101010", -1),
    "humorous_non_tech": ("Segoe UI", 54, AMBER, "&H60000000", -1),
}

ASS_HEADER = """[Script Info]
Title: TextSink
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{size},{color},{color},&H00000000,{back},{bold},0,0,0,100,100,0,0,4,3,2,2,60,60,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ts(sec: float) -> str:
    h = int(sec // 3600); m = int(sec % 3600 // 60); s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _events(style: str, caption: str, dur: float) -> list:
    """Kinetic-type dialogue events per style."""
    start, end = 0.8, max(dur - 0.4, 4.0)
    words = caption.split()
    if style == "formal":
        return [f"Dialogue: 0,{_ts(start)},{_ts(end)},Cap,,0,0,0,,"
                f"{{\\fad(600,500)}}{caption}"]
    if style == "sarcastic":
        # typewriter via karaoke; long beat before the final word
        cs_per_word = max(int((min(end, start + 6) - start) * 80 / max(len(words), 1)), 12)
        parts = []
        for i, w in enumerate(words):
            k = cs_per_word * 4 if i == len(words) - 1 else cs_per_word
            parts.append(f"{{\\k{k}}}{w} ")
        return [f"Dialogue: 0,{_ts(start)},{_ts(end)},Cap,,0,0,0,,"
                f"{{\\fad(150,400)}}" + "".join(parts).rstrip()]
    if style == "humorous_tech":
        cs = max(int(500 / max(len(caption), 1)), 2)
        typed = "".join(f"{{\\k{cs}}}{ch}" for ch in caption)
        return [f"Dialogue: 0,{_ts(start)},{_ts(end)},Cap,,0,0,0,,"
                f"{{\\fad(100,300)}}$ {typed}{{\\k30}}▌"]
    # humorous_non_tech: per-word bounce-in
    evs, t = [], start
    step = min(2.5 / max(len(words), 1), 0.28)
    shown = ""
    for w in words:
        shown = (shown + " " + w).strip()
        nxt = t + step
        evs.append(
            f"Dialogue: 0,{_ts(t)},{_ts(nxt)},Cap,,0,0,0,,"
            f"{{\\fscx118\\fscy118\\t(0,120,\\fscx100\\fscy100)}}{shown}")
        t = nxt
    evs.append(f"Dialogue: 0,{_ts(t)},{_ts(end)},Cap,,0,0,0,,"
               f"{{\\fad(0,400)}}{shown}")
    return evs


def build_ass(style: str, caption: str, dur: float) -> str:
    font, size, color, back, bold = STYLE_DEFS[style]
    head = ASS_HEADER.format(font=font, size=size, color=color, back=back,
                             bold=bold)
    return head + "\n".join(_events(style, caption, dur)) + "\n"


def _dur(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True).stdout.strip()
    return float(out or 10.0)


def _find_clip(clips_dir: str, task_id: str, tasks: dict) -> str:
    url = tasks.get(task_id, "")
    base = os.path.basename(url.split("?")[0]) if url else ""
    cand = os.path.join(clips_dir, base)
    if base and os.path.exists(cand):
        return cand
    hits = glob.glob(os.path.join(clips_dir, f"{task_id}.*"))
    if hits:
        return hits[0]
    raise FileNotFoundError(f"no clip for {task_id} in {clips_dir}")


def _burn(clip: str, ass_path: str, out_path: str) -> None:
    ass_ff = ass_path.replace("\\", "/").replace(":", "\\:")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", clip,
         "-vf", f"scale=-2:720,ass='{ass_ff}'",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-movflags", "+faststart", out_path], check=True)


def _grid(paths: list, out_path: str) -> None:
    inputs = []
    for p in paths:
        inputs += ["-i", p]
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", *inputs,
         "-filter_complex",
         "[0:v]scale=960:-2[a];[1:v]scale=960:-2[b];"
         "[2:v]scale=960:-2[c];[3:v]scale=960:-2[d];"
         "[a][b][c][d]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v]",
         "-map", "[v]", "-map", "0:a?", "-c:v", "libx264",
         "-preset", "veryfast", "-crf", "21", out_path], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="TextSink Render")
    ap.add_argument("--results", required=True)
    ap.add_argument("--clips", required=True)
    ap.add_argument("--tasks", default="", help="tasks.json to map ids->files")
    ap.add_argument("--out", default="renders")
    ap.add_argument("--grid", action="store_true",
                    help="also make 2x2 four-voices grid per task")
    args = ap.parse_args()

    tasks = {}
    if args.tasks:
        with open(args.tasks, encoding="utf-8") as fh:
            tasks = {t["task_id"]: t.get("video_url", "")
                     for t in json.load(fh)}
    with open(args.results, encoding="utf-8") as fh:
        results = json.load(fh)

    os.makedirs(args.out, exist_ok=True)
    for r in results:
        tid = r["task_id"]
        try:
            clip = _find_clip(args.clips, tid, tasks)
        except FileNotFoundError as e:
            print(f"[render] {e}", file=sys.stderr)
            continue
        dur = _dur(clip)
        style_outs = []
        for style, caption in r["captions"].items():
            if not caption:
                continue
            ass_path = os.path.join(args.out, f"{tid}_{style}.ass")
            with open(ass_path, "w", encoding="utf-8-sig") as fh:
                fh.write(build_ass(style, caption, dur))
            out_path = os.path.join(args.out, f"{tid}_{style}.mp4")
            print(f"[render] {tid} {style} ...", file=sys.stderr)
            _burn(clip, ass_path, out_path)
            style_outs.append(out_path)
        if args.grid and len(style_outs) == 4:
            print(f"[render] {tid} 2x2 grid ...", file=sys.stderr)
            _grid(style_outs, os.path.join(args.out, f"{tid}_fourvoices.mp4"))
    print(f"[render] done -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
