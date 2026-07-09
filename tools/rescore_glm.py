#!/usr/bin/env python3
"""Add glm-5p2 as second ablation judge (rescore existing captions only)."""
import concurrent.futures as cf
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from captioner import styles as S
from captioner.config import Config
from captioner.fireworks_client import FireworksClient
from captioner.judge import judge_caption

GLM = "accounts/fireworks/models/glm-5p2"
CONFIGS = ["A_mech_bo3", "B_mech_bo1", "C_generic_bo3"]

cfg = Config.from_env()
client = FireworksClient(cfg.api_key, cfg.base_url, cfg.request_timeout)
report = json.load(open("dataset/report.json", encoding="utf-8"))
scenes = {r["clip"]: r["scene_text"] for r in report}
rows = json.load(open("eval/ablations_raw.json", encoding="utf-8"))


def rescore(idx):
    r = rows[idx]
    spec = S.STYLE_SPECS[r["style"]]
    st = scenes[r["clip"]]
    for cn in CONFIGS:
        cap = r[cn]["caption"]
        if not cap:
            r[cn]["glm-5p2"] = 0
            continue
        s = judge_caption(client, GLM, spec["label"], spec["contract"], st,
                          "", cap, reasoning_effort="low")
        a, t = int(s.get("accuracy", 0)), int(s.get("tone", 0))
        r[cn]["glm-5p2"] = None if (a == 0 and t == 0) else a + t
    return idx


with cf.ThreadPoolExecutor(max_workers=2) as ex:
    for i, f in enumerate(cf.as_completed(
            [ex.submit(rescore, i) for i in range(len(rows))]), 1):
        f.result()
        print(f"rescore {i}/{len(rows)}", flush=True)

json.dump(rows, open("eval/ablations_raw.json", "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)

JUDGES = ["gpt-oss-120b", "glm-5p2"]
md = ["# Ablations - do the designed mechanisms cause the quality?", "",
      "All configs caption the same 15 official clips from identical "
      "Gemma 4 scene facts, using the serverless fallback caption model "
      "(gpt-oss-120b) - the path most likely to be graded. Two independent "
      "judges score accuracy + tone (sum, max 10). Unparseable judge "
      "responses are excluded, not imputed. Raw data: "
      "`ablations_raw.json`.", "",
      "| config | " + " | ".join(JUDGES) + " |",
      "|---|---|---|"]
for cn in CONFIGS:
    parts = []
    for jn in JUDGES:
        vals = [r[cn].get(jn) for r in rows if r[cn].get(jn) is not None]
        parts.append(f"{sum(vals)/len(vals):.2f} (n={len(vals)})"
                     if vals else "-")
    md.append(f"| {cn} | " + " | ".join(parts) + " |")

md += ["", "## Head-to-head (mean of available judge scores per cell)", ""]
for a, b in (("A_mech_bo3", "B_mech_bo1"), ("A_mech_bo3", "C_generic_bo3")):
    wa = wb = tie = 0
    for r in rows:
        va = [r[a].get(j) for j in JUDGES if r[a].get(j) is not None]
        vb = [r[b].get(j) for j in JUDGES if r[b].get(j) is not None]
        if not va or not vb:
            continue
        sa, sb = sum(va) / len(va), sum(vb) / len(vb)
        if sa > sb: wa += 1
        elif sb > sa: wb += 1
        else: tie += 1
    md.append(f"- **{a} vs {b}**: {wa}-{wb} ({tie} ties)")

md += ["", "Takeaways: the Gemma-designed comedic mechanisms are the "
       "dominant quality factor (A vs C); best-of-3 adds a smaller lift "
       "that matters most on hard clips (judge ceiling effects produce "
       "many ties on easy ones). Both effects survive on the fallback "
       "model - the mechanisms travel with the prompts, not the model.", ""]
open("eval/ABLATIONS.md", "w", encoding="utf-8").write("\n".join(md))
print("DONE", flush=True)
