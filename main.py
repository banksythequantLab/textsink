#!/usr/bin/env python3
"""Track 2 judging-harness entry point.

Contract (verified against the official harness flow):
  reads  /input/tasks.json   [{task_id, video_url, styles[]}, ...]
  writes /output/results.json [{task_id, captions:{formal, sarcastic,
                                humorous_tech, humorous_non_tech}}, ...]
Paths overridable via INPUT_PATH / OUTPUT_PATH for local testing.

Strategy: all-in on the Gemma 4 deployment, with a survival parachute -
if the deployment is unreachable/cold past its time budget, remaining
tasks cut over to serverless models so no task ever scores zero.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import os
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from captioner.config import Config                    # noqa: E402
from captioner.fireworks_client import FireworksClient  # noqa: E402
from captioner.pipeline import process_clip             # noqa: E402
from captioner.schema import STYLES                     # noqa: E402

INPUT_PATH = os.environ.get("INPUT_PATH", "/input/tasks.json")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "/output/results.json")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "4"))
# Hard wall-clock budget (harness limit is 10 min; leave a write margin).
TIME_BUDGET_SEC = int(os.environ.get("TIME_BUDGET_SEC", "540"))

SERVERLESS_VISION = "accounts/fireworks/models/qwen3p7-plus"
SERVERLESS_CAPTION = "accounts/fireworks/models/gpt-oss-120b"


def _download(url: str, dest_dir: str, task_id: str) -> str:
    ext = os.path.splitext(url.split("?")[0])[1] or ".mp4"
    dest = os.path.join(dest_dir, f"{task_id}{ext}")
    req = urllib.request.Request(url, headers={"User-Agent": "textsink/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    return dest


def _fallback_cfg(cfg: Config) -> Config:
    import copy
    c = copy.copy(cfg)
    c.vision_model = SERVERLESS_VISION
    c.caption_model = SERVERLESS_CAPTION
    c.reasoning_effort = "low"
    return c


def _one_task(task: dict, cfg: Config, client, td: str, deadline: float) -> dict:
    task_id = task.get("task_id", "unknown")
    captions = {s: "" for s in STYLES}
    try:
        path = _download(task["video_url"], td, task_id)
        try:
            result = process_clip(path, client, cfg)
            captions.update(result.captions)
        except Exception as e:
            print(f"[main] {task_id}: primary (Gemma) failed: {e}; "
                  f"cutting over to serverless", file=sys.stderr)
            if time.time() < deadline:
                result = process_clip(path, client, _fallback_cfg(cfg))
                captions.update(result.captions)
    except Exception as e:
        print(f"[main] {task_id}: FAILED entirely: {e}", file=sys.stderr)
    return {"task_id": task_id, "captions": captions}


def main() -> int:
    start = time.time()
    deadline = start + TIME_BUDGET_SEC
    with open(INPUT_PATH, encoding="utf-8") as fh:
        tasks = json.load(fh)
    print(f"[main] {len(tasks)} task(s); budget {TIME_BUDGET_SEC}s; "
          f"workers {MAX_WORKERS}", file=sys.stderr)

    cfg = Config.from_env()
    client = FireworksClient(cfg.api_key, cfg.base_url, cfg.request_timeout)

    results = []
    with tempfile.TemporaryDirectory() as td:
        with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(_one_task, t, cfg, client, td, deadline): t
                    for t in tasks}
            for fut in cf.as_completed(futs):
                results.append(fut.result())
                done = len(results)
                print(f"[main] {done}/{len(tasks)} done "
                      f"({time.time() - start:.0f}s elapsed)", file=sys.stderr)

    # Preserve input order for the grader.
    order = {t.get("task_id"): i for i, t in enumerate(tasks)}
    results.sort(key=lambda r: order.get(r["task_id"], 1 << 30))

    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_PATH)), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    print(f"[main] wrote {len(results)} result(s) -> {OUTPUT_PATH} "
          f"in {time.time() - start:.0f}s", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
