#!/usr/bin/env python3
"""Dataset generator: Gemma 4 teaches its own captioner.

For every clip in --clips:
  frames -> Gemma 4 scene JSON -> per style: N drafts (high temp)
  -> Gemma 4 judge scores each draft (accuracy, tone)
  -> winners (accuracy >= acc-min and tone >= tone-min) become JSONL
     training rows:  system=tone contract, user=scene facts, assistant=caption

Outputs:
  --out dataset.jsonl        training rows (OpenAI chat format, Fireworks SFT)
  --report report.json       everything: scenes, drafts, scores, winners
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from captioner import styles as S                       # noqa: E402
from captioner import vision as V                       # noqa: E402
from captioner import frames as F                       # noqa: E402
from captioner.config import Config                     # noqa: E402
from captioner.fireworks_client import FireworksClient  # noqa: E402
from captioner.judge import judge_caption               # noqa: E402
from captioner.schema import STYLES                     # noqa: E402

VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v")


def drafts_for_style(client, cfg, style, scene_text, transcript, n=3):
    """N independent drafts at high temperature for diversity."""
    out = []
    temp = 0.5 if style == "formal" else 0.95
    for _ in range(n):
        msgs = S.build_messages(style, scene_text, transcript)
        cap = client.chat(model=cfg.caption_model, messages=msgs,
                          temperature=temp, max_tokens=cfg.max_tokens,
                          reasoning_effort=cfg.reasoning_effort)
        cap = (cap or "").strip().strip('"').strip()
        if cap and cap not in out:
            out.append(cap)
    return out


def process(client, cfg, path, n_drafts, acc_min, tone_min):
    sampled = F.sample_frames(path, cfg.fps_sample, cfg.min_frames,
                              cfg.max_frames, cfg.frame_width)
    transcript = ""
    scene = V.describe_scene(client, cfg.vision_model, sampled.frames,
                             transcript, max_tokens=cfg.scene_max_tokens,
                             reasoning_effort=cfg.reasoning_effort)
    scene_text = V.scene_to_text(scene)
    if not (scene.get("subjects") or scene.get("actions")):
        raise RuntimeError("empty scene - skipping clip")
    clip_rows, clip_report = [], {"clip": os.path.basename(path),
                                  "scene_text": scene_text, "styles": {}}
    for style in STYLES:
        spec = S.STYLE_SPECS[style]
        drafts = drafts_for_style(client, cfg, style, scene_text, transcript,
                                  n_drafts)
        scored = []
        for d in drafts:
            s = judge_caption(client, cfg.caption_model, spec["label"],
                              spec["contract"], scene_text, transcript, d,
                              reasoning_effort=cfg.reasoning_effort)
            scored.append({"caption": d, "accuracy": s.get("accuracy", 0),
                           "tone": s.get("tone", 0),
                           "reason": s.get("reason", "")})
        scored.sort(key=lambda x: (x["accuracy"], x["tone"]), reverse=True)
        clip_report["styles"][style] = scored
        best = scored[0] if scored else None
        if best and best["accuracy"] >= acc_min and best["tone"] >= tone_min:
            clip_rows.append({"messages": [
                {"role": "system", "content": S.SYSTEM},
                {"role": "user",
                 "content": S.build_messages(style, scene_text,
                                             transcript)[1]["content"]},
                {"role": "assistant", "content": best["caption"]},
            ]})
    return clip_rows, clip_report


def main() -> int:
    ap = argparse.ArgumentParser(description="TextSink dataset generator")
    ap.add_argument("--clips", required=True, help="folder of video clips")
    ap.add_argument("--out", default="dataset.jsonl")
    ap.add_argument("--report", default="dataset_report.json")
    ap.add_argument("--n-drafts", type=int, default=3)
    ap.add_argument("--acc-min", type=int, default=5)
    ap.add_argument("--tone-min", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="max clips (0=all)")
    args = ap.parse_args()

    cfg = Config.from_env()
    client = FireworksClient(cfg.api_key, cfg.base_url, cfg.request_timeout)

    clips = []
    for e in VIDEO_EXT:
        clips += glob.glob(os.path.join(args.clips, f"*{e}"))
    clips.sort()
    if args.limit:
        clips = clips[:args.limit]

    rows, reports = [], []
    for i, path in enumerate(clips, 1):
        print(f"[dataset] ({i}/{len(clips)}) {os.path.basename(path)}",
              file=sys.stderr)
        try:
            clip_rows, clip_report = process(client, cfg, path,
                                             args.n_drafts, args.acc_min,
                                             args.tone_min)
            rows += clip_rows
            reports.append(clip_report)
            print(f"[dataset]   +{len(clip_rows)} rows "
                  f"(total {len(rows)})", file=sys.stderr)
        except Exception as e:
            print(f"[dataset]   SKIP: {e}", file=sys.stderr)
        # checkpoint after every clip - crash-safe
        with open(args.out, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(reports, fh, indent=2, ensure_ascii=False)

    print(f"[dataset] DONE: {len(rows)} training rows from "
          f"{len(reports)} clips -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
