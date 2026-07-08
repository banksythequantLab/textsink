#!/usr/bin/env python3
"""TextSink CC - styled closed captions that track the video in time.

Pipeline per clip:
  1. sample frames evenly with timestamps
  2. one vision call -> time-segmented scene beats JSON
  3. per style: one call writes a CC line per beat in a consistent voice
     (callbacks to earlier beats encouraged - it's a comedy track)
  4. emit per style: .srt (soft subs), .ass (CC box look), burned .mp4
     plus cc.json with all four timed tracks

Usage:
  python tools/textsink_cc.py --clip <video> [--out cc_out] [--burn]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from captioner import frames as F                       # noqa: E402
from captioner import styles as S                       # noqa: E402
from captioner.config import Config                     # noqa: E402
from captioner.fireworks_client import (                # noqa: E402
    FireworksClient, image_content, text_content)
from captioner.schema import STYLES                     # noqa: E402

BEATS_SYSTEM = (
    "You are a precise video analyst. You receive frames sampled from one "
    "short clip, each labeled with its timestamp in seconds. Segment the clip "
    "into 4-8 sequential beats that cover the full duration. For each beat "
    "report only what is visibly happening. Strict JSON only: "
    '{"beats":[{"start":sec,"end":sec,"what":"..."}]}'
)

CC_RULES = (
    "You are writing a CLOSED-CAPTION comedy track for this clip in the "
    "style: {label}.\nTONE CONTRACT: {contract}\n"
    "Rules:\n"
    "1. Exactly one caption line per beat, in time order.\n"
    "2. Each line is short - max 12 words - present tense, punchy.\n"
    "3. Keep ONE consistent voice across all lines; later lines may call "
    "back to earlier ones (running gags welcome).\n"
    "4. Only reference what the beats describe. Never invent objects or "
    "events.\n"
    "5. Strict JSON only: {{\"lines\":[{{\"start\":sec,\"end\":sec,"
    "\"text\":\"...\"}}]}} - keep the given beat times.\n"
)


def _coerce(raw: str, key: str) -> list:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        nl = raw.find("\n")
        if nl != -1:
            raw = raw[nl + 1:]
    try:
        return json.loads(raw).get(key, [])
    except json.JSONDecodeError:
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e > s:
            try:
                return json.loads(raw[s:e + 1]).get(key, [])
            except json.JSONDecodeError:
                pass
    return []


def get_beats(client, cfg, path, n_frames=20):
    sampled = F.sample_frames(path, 0.5, 10, n_frames, cfg.frame_width)
    dur = sampled.duration
    n = len(sampled.frames)
    content = [text_content(
        f"Clip duration: {dur:.1f}s. {n} frames follow, evenly sampled.")]
    for i, fb in enumerate(sampled.frames):
        t = (i + 0.5) * dur / n
        content.append(text_content(f"frame at t={t:.1f}s:"))
        content.append(image_content(fb))
    msgs = [{"role": "system", "content": BEATS_SYSTEM},
            {"role": "user", "content": content}]
    beats = []
    for attempt, rf in ((1, {"type": "json_object"}), (2, None), (3, None)):
        raw = client.chat(model=cfg.vision_model, messages=msgs,
                          temperature=0.2 + 0.2 * (attempt - 1),
                          max_tokens=cfg.scene_max_tokens,
                          reasoning_effort=cfg.reasoning_effort,
                          response_format=rf)
        beats = [b for b in _coerce(raw, "beats")
                 if isinstance(b, dict) and b.get("what")]
        if beats:
            break
        # keep the evidence: dump the raw model response for post-mortem
        dbg = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "beats_failures.log")
        with open(dbg, "a", encoding="utf-8") as fh:
            fh.write(f"--- {os.path.basename(path)} attempt {attempt} "
                     f"rf={'json' if rf else 'text'} ---\n{raw[:800]}\n")
        print(f"[cc] beats empty (attempt {attempt}/3), retrying ...",
              file=sys.stderr)
    if not beats:
        raise RuntimeError("no beats extracted after 3 attempts")
    return beats, dur


def cc_lines(client, cfg, style, beats):
    spec = S.STYLE_SPECS[style]
    prompt = CC_RULES.format(label=spec["label"], contract=spec["contract"])
    user = prompt + "\nBEATS:\n" + json.dumps({"beats": beats}, indent=1)
    msgs = [{"role": "system", "content": "You are an expert caption writer."},
            {"role": "user", "content": user}]
    temp = 0.4 if style == "formal" else 0.85
    raw = client.chat(model=cfg.caption_model, messages=msgs,
                      temperature=temp, max_tokens=1200,
                      reasoning_effort=cfg.reasoning_effort,
                      response_format={"type": "json_object"})
    lines = [l for l in _coerce(raw, "lines")
             if isinstance(l, dict) and l.get("text")]
    if not lines:
        raise RuntimeError(f"no CC lines for {style}")
    return lines


CC_FONTS = {
    "formal": ("Georgia", "&H00FFFFFF"),
    "sarcastic": ("Courier New", "&H00FFFFFF"),
    "humorous_tech": ("Consolas", "&H0050FF50"),
    "humorous_non_tech": ("Segoe UI", "&H0007C1FF"),
}

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CC,{font},46,{color},{color},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,4,3,0,2,80,80,44,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ts_ass(sec: float) -> str:
    h = int(sec // 3600); m = int(sec % 3600 // 60); s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _ts_srt(sec: float) -> str:
    h = int(sec // 3600); m = int(sec % 3600 // 60)
    s = int(sec % 60); ms = int((sec % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_tracks(style, lines, dur, out_dir, base):
    font, color = CC_FONTS[style]
    ass = ASS_HEAD.format(font=font, color=color)
    srt = []
    for i, ln in enumerate(lines):
        s = max(float(ln.get("start", 0)), 0.0)
        e = min(float(ln.get("end", s + 4)), dur)
        if e <= s:
            e = min(s + 3.0, dur)
        txt = str(ln["text"]).strip()
        ass += (f"Dialogue: 0,{_ts_ass(s)},{_ts_ass(e)},CC,,0,0,0,,"
                f"{{\\fad(120,120)}}{txt}\n")
        srt.append(f"{i + 1}\n{_ts_srt(s)} --> {_ts_srt(e)}\n{txt}\n")
    ass_p = os.path.join(out_dir, f"{base}_{style}.ass")
    srt_p = os.path.join(out_dir, f"{base}_{style}.srt")
    with open(ass_p, "w", encoding="utf-8-sig") as fh:
        fh.write(ass)
    with open(srt_p, "w", encoding="utf-8") as fh:
        fh.write("\n".join(srt))
    return ass_p


def burn(clip, ass_path, out_path):
    ass_ff = ass_path.replace("\\", "/").replace(":", "\\:")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", clip,
         "-vf", f"scale=-2:720,ass='{ass_ff}'",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-movflags", "+faststart", out_path], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="TextSink CC")
    ap.add_argument("--clip", required=True)
    ap.add_argument("--out", default="cc_out")
    ap.add_argument("--burn", action="store_true")
    ap.add_argument("--styles", default=",".join(STYLES))
    args = ap.parse_args()

    cfg = Config.from_env()
    client = FireworksClient(cfg.api_key, cfg.base_url, cfg.request_timeout)
    os.makedirs(args.out, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.clip))[0]

    print(f"[cc] segmenting {base} ...", file=sys.stderr)
    beats, dur = get_beats(client, cfg, args.clip)
    print(f"[cc] {len(beats)} beats over {dur:.1f}s", file=sys.stderr)

    tracks = {}
    for style in args.styles.split(","):
        style = style.strip()
        print(f"[cc] writing {style} track ...", file=sys.stderr)
        lines = cc_lines(client, cfg, style, beats)
        tracks[style] = lines
        ass_p = write_tracks(style, lines, dur, args.out, base)
        if args.burn:
            print(f"[cc] burning {style} ...", file=sys.stderr)
            burn(args.clip, ass_p, os.path.join(args.out,
                                                f"{base}_{style}_cc.mp4"))

    with open(os.path.join(args.out, f"{base}_cc.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"clip": os.path.basename(args.clip), "duration": dur,
                   "beats": beats, "tracks": tracks}, fh, indent=2,
                  ensure_ascii=False)
    print(f"[cc] done -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
