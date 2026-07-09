#!/usr/bin/env python3
"""A/B: fine-tuned textsink-g3-captioner vs prompted Gemma 4 best-of-3.

Uses stored Gemma 4 scene facts (dataset/report.json) so only the caption
stage differs. Neutral judge: serverless gpt-oss-120b scores accuracy+tone
for BOTH sides. Scales the tuned deployment to zero at the end.
"""
import glob
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

from captioner import styles as S
from captioner.config import Config
from captioner.fireworks_client import FireworksClient
from captioner.judge import judge_caption
from captioner.schema import STYLES

TUNED = ("accounts/banksythequant/models/textsink-g3-captioner"
         "#accounts/banksythequant/deployments/tsg3cap2")
JUDGE = "accounts/fireworks/models/gpt-oss-120b"

cfg = Config.from_env()
client = FireworksClient(cfg.api_key, cfg.base_url, cfg.request_timeout)

# scene facts from the dataset build (same 15 clips, Gemma 4 grounding)
report = json.load(open("dataset/report.json", encoding="utf-8"))
scenes = {r["clip"]: r["scene_text"] for r in report}

# prompted side: the validated best-of-3 all-Gemma run (t1..t15 = sorted clips)
prompted = json.load(open("test_input/results_all15_v2.json",
                          encoding="utf-8"))
clip_names = sorted(os.path.basename(p)
                    for p in glob.glob("official_clips/*.mp4"))
tid_to_clip = {f"t{i+1}": n for i, n in enumerate(clip_names)}

totals = {"tuned": {"acc": 0, "tone": 0}, "prompted": {"acc": 0, "tone": 0}}
rows = []
for task in prompted:
    clip = tid_to_clip.get(task["task_id"])
    scene_text = scenes.get(clip)
    if not scene_text:
        continue
    for style in STYLES:
        spec = S.STYLE_SPECS[style]
        msgs = S.build_messages(style, scene_text, "")
        tuned_cap = (client.chat(model=TUNED, messages=msgs, temperature=0.4,
                                 max_tokens=320) or "").strip().strip('"')
        prom_cap = task["captions"][style]
        row = {"clip": clip, "style": style}
        for side, cap in (("tuned", tuned_cap), ("prompted", prom_cap)):
            s = judge_caption(client, JUDGE, spec["label"], spec["contract"],
                              scene_text, "", cap, reasoning_effort="low")
            row[side] = {"caption": cap, "accuracy": s.get("accuracy", 0),
                         "tone": s.get("tone", 0)}
            totals[side]["acc"] += int(s.get("accuracy", 0))
            totals[side]["tone"] += int(s.get("tone", 0))
        rows.append(row)
        print(f"{clip[:20]} {style[:12]:12} tuned "
              f"a{row['tuned']['accuracy']}/t{row['tuned']['tone']}  vs  "
              f"prompted a{row['prompted']['accuracy']}/"
              f"t{row['prompted']['tone']}", flush=True)

n = len(rows)
print("\n==== VERDICT ====", flush=True)
for side in ("tuned", "prompted"):
    print(f"{side:9} accuracy {totals[side]['acc']/n:.2f}  "
          f"tone {totals[side]['tone']/n:.2f}  "
          f"(sum {totals[side]['acc']+totals[side]['tone']})", flush=True)
json.dump({"totals": totals, "n": n, "rows": rows},
          open("ab_results.json", "w", encoding="utf-8"), indent=2,
          ensure_ascii=False)

# release the GPU
key = cfg.api_key
r = requests.patch(
    "https://api.fireworks.ai/v1/accounts/banksythequant/deployments/"
    "tsg3cap2?updateMask=min_replica_count",
    headers={"Authorization": f"Bearer {key}"},
    json={"minReplicaCount": 0}, timeout=30)
print(f"tsg3cap unpin: {r.status_code}", flush=True)
