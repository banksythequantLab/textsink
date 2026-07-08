#!/usr/bin/env python3
"""Local eval harness: caption a folder, then self-judge accuracy + tone.

This is a DEV tool to iterate on prompts/exemplars before submitting. It is not
the official contest scoring. Run with --mock to verify wiring offline.

  python eval/run_eval.py --input videos/            # real (needs API key)
  python eval/run_eval.py --input test_clip.mp4 --mock
"""
from __future__ import annotations

import argparse
import glob
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from captioner.config import Config          # noqa: E402
from captioner.judge import judge_caption     # noqa: E402
from captioner.pipeline import process_clip   # noqa: E402
from captioner.styles import STYLE_SPECS      # noqa: E402
from captioner.vision import scene_to_text    # noqa: E402

EXT = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v")


def _client(cfg, mock):
    if mock:
        from captioner.mock import MockClient
        return MockClient()
    from captioner.fireworks_client import FireworksClient
    return FireworksClient(cfg.api_key, cfg.base_url, cfg.request_timeout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", "-i", required=True)
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    cfg = Config.from_env()
    client = _client(cfg, args.mock)

    if os.path.isdir(args.input):
        clips = sorted(sum((glob.glob(os.path.join(args.input, f"*{e}"))
                            for e in EXT), []))
    else:
        clips = [args.input]

    scores = {s: {"accuracy": [], "tone": []} for s in STYLE_SPECS}
    for path in clips:
        r = process_clip(path, client, cfg)
        st = scene_to_text(r.scene)
        for style, spec in STYLE_SPECS.items():
            j = judge_caption(client, cfg.judge_model, spec["label"],
                              spec["contract"], st, r.transcript,
                              r.captions[style])
            scores[style]["accuracy"].append(j.get("accuracy", 0))
            scores[style]["tone"].append(j.get("tone", 0))
            print(f"{os.path.basename(path)} [{style}] "
                  f"acc={j.get('accuracy')} tone={j.get('tone')} :: "
                  f"{r.captions[style]}")

    print("\n=== averages ===")
    for style, sc in scores.items():
        acc = statistics.mean(sc["accuracy"]) if sc["accuracy"] else 0
        tone = statistics.mean(sc["tone"]) if sc["tone"] else 0
        print(f"{style:20s} accuracy={acc:.2f} tone={tone:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
