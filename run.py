#!/usr/bin/env python3
"""AMD Developer Hackathon: ACT II — Track 2 video-captioning agent.

Usage:
  python run.py --input videos/ --output captions.json   # real run (needs API key)
  python run.py --input clip.mp4 --mock                   # offline wiring test
  python run.py --list-models                             # discover Gemma model id
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import sys

# Windows consoles default to cp1252; captions contain Unicode. Force UTF-8.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)

# make the package importable when run as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from captioner.config import Config          # noqa: E402
from captioner.pipeline import process_clip   # noqa: E402
from captioner.schema import dumps            # noqa: E402

VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v")


def _client(cfg: Config, mock: bool):
    if mock:
        from captioner.mock import MockClient
        return MockClient()
    from captioner.fireworks_client import FireworksClient
    return FireworksClient(cfg.api_key, cfg.base_url, cfg.request_timeout)


def _collect(inp: str) -> list:
    if os.path.isdir(inp):
        files: list = []
        for e in VIDEO_EXT:
            files += glob.glob(os.path.join(inp, f"*{e}"))
        return sorted(files)
    return [inp]


def main() -> int:
    ap = argparse.ArgumentParser(description="Track 2 video captioner")
    ap.add_argument("--input", "-i", help="video file or directory")
    ap.add_argument("--output", "-o", default="captions.json")
    ap.add_argument("--mock", action="store_true",
                    help="offline dry run (no API key, deterministic)")
    ap.add_argument("--list-models", action="store_true",
                    help="print available model ids and exit")
    args = ap.parse_args()

    cfg = Config.from_env()

    if args.list_models:
        for m in _client(cfg, mock=args.mock).list_models():
            print(m.get("id", m) if isinstance(m, dict) else m)
        return 0

    if not args.input:
        ap.error("--input is required (unless --list-models)")

    clips = _collect(args.input)
    if not clips:
        print(f"No videos found in {args.input}", file=sys.stderr)
        return 2

    client = _client(cfg, mock=args.mock)
    results = []
    for path in clips:
        print(f"[captioner] processing {path} ...", file=sys.stderr)
        try:
            results.append(process_clip(path, client, cfg))
        except Exception as e:
            print(f"[captioner] ERROR on {path}: {e}", file=sys.stderr)

    out = dumps(results)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"[captioner] wrote {len(results)} result(s) -> {args.output}",
          file=sys.stderr)
    print(out)  # echo for graders that read stdout
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
