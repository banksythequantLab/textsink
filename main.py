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


def _last_resort(path: str, client, cfg: Config) -> dict:
    """Grounding failed everywhere: caption directly from raw frames.

    One permissive multimodal call per style - degraded accuracy beats an
    empty string, which is a guaranteed zero."""
    from captioner import frames as F
    from captioner import styles as S
    from captioner.fireworks_client import image_content, text_content
    sampled = F.sample_frames(path, cfg.fps_sample, 4, 6, cfg.frame_width)
    captions = {}
    for style in STYLES:
        spec = S.STYLE_SPECS[style]
        content = [text_content(
            f"Frames from one short video clip. Write ONE caption in this "
            f"style - {spec['label']}: {spec['contract']} 1-2 sentences, "
            f"max 40 words, describe only what you can actually see. "
            f"Output only the caption.")]
        content += [image_content(fb) for fb in sampled.frames]
        try:
            from captioner.pipeline import _is_refusal
            cap = client.chat(model=cfg.vision_model,
                              messages=[{"role": "user", "content": content}],
                              temperature=0.6, max_tokens=cfg.max_tokens,
                              reasoning_effort=cfg.reasoning_effort)
            cap = (cap or "").strip().strip('"')
            captions[style] = "" if _is_refusal(cap) else cap
        except Exception:
            captions[style] = ""
    return captions


def _one_task(task: dict, cfg: Config, client, td: str, deadline: float) -> dict:
    task_id = task.get("task_id", "unknown")
    captions = {s: "" for s in STYLES}
    try:
        path = _download(task["video_url"], td, task_id)
        try:
            result = process_clip(path, client, cfg, deadline=deadline)
            captions.update(result.captions)
        except Exception as e:
            print(f"[main] {task_id}: primary failed: {e}; "
                  f"cutting over to serverless", file=sys.stderr)
            if time.time() < deadline:
                try:
                    result = process_clip(path, client, _fallback_cfg(cfg),
                                          deadline=deadline)
                    captions.update(result.captions)
                except Exception as e2:
                    print(f"[main] {task_id}: fallback failed too: {e2}; "
                          f"last-resort frame captioning", file=sys.stderr)
                    captions.update(_last_resort(path, client, cfg))
    except Exception as e:
        print(f"[main] {task_id}: FAILED entirely: {e}", file=sys.stderr)
    if not any(v.strip() for v in captions.values()):
        print(f"[main] {task_id}: WARNING - empty captions in output",
              file=sys.stderr)
    return {"task_id": task_id, "captions": captions}


def _probe_models(cfg: Config, client) -> Config:
    """Decide once at startup which models this run can actually use.

    The Gemma deployment is account-scoped: under the grader's own API key
    it 404s instantly -> switch to serverless before wasting any budget.
    Under our key a cold deployment returns 503 -> wait a bounded amount
    (it is scaling up), then decide.
    """
    if "#" not in cfg.caption_model:
        return cfg  # already serverless
    try:
        # retries=6 -> waits up to ~2.5 min through a cold start
        client.chat(model=cfg.caption_model,
                    messages=[{"role": "user", "content": "Say OK."}],
                    max_tokens=5, reasoning_effort=cfg.reasoning_effort,
                    retries=6)
        print("[main] probe: Gemma deployment reachable - all-Gemma run",
              file=sys.stderr)
        return cfg
    except Exception as e:
        print(f"[main] probe: deployment unreachable ({str(e)[:120]}) - "
              f"switching to serverless models", file=sys.stderr)
        return _fallback_cfg(cfg)


def main() -> int:
    start = time.time()
    deadline = start + TIME_BUDGET_SEC
    with open(INPUT_PATH, encoding="utf-8-sig") as fh:  # BOM-tolerant
        tasks = json.load(fh)
    print(f"[main] {len(tasks)} task(s); budget {TIME_BUDGET_SEC}s; "
          f"workers {MAX_WORKERS}", file=sys.stderr)

    cfg = Config.from_env()
    client = FireworksClient(cfg.api_key, cfg.base_url, cfg.request_timeout)
    cfg = _probe_models(cfg, client)

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
