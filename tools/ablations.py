#!/usr/bin/env python3
"""Ablation study: do the Gemma-designed mechanisms cause the quality?

Three configs generate captions for all 15 official clips x 4 styles,
from identical Gemma 4 scene facts (stored in dataset/report.json), using
the serverless caption model (the harness fallback - the path most likely
to be graded):

  A  mechanisms + best-of-3 self-judge   (the shipped system)
  B  mechanisms + best-of-1              (ablate the self-judge)
  C  generic adjectives + best-of-3      (ablate the comedic mechanisms)

Final captions from every config are then scored blind by TWO judges
(gpt-oss-120b and qwen3p7-plus) on accuracy + tone.

Outputs: eval/ablations_raw.json + eval/ABLATIONS.md
"""
import concurrent.futures as cf
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from captioner import styles as S
from captioner.config import Config
from captioner.fireworks_client import FireworksClient
from captioner.judge import judge_caption
from captioner.pipeline import _clean, _is_refusal
from captioner.schema import STYLES

CAPTION_MODEL = "accounts/fireworks/models/gpt-oss-120b"
JUDGES = {"gpt-oss-120b": "accounts/fireworks/models/gpt-oss-120b",
          "qwen3p7-plus": "accounts/fireworks/models/qwen3p7-plus"}

GENERIC = {
    "formal": "Write a formal caption for this video.",
    "sarcastic": "Write a sarcastic caption for this video.",
    "humorous_tech": "Write a funny tech-humor caption for this video.",
    "humorous_non_tech": ("Write a funny caption for this video with no "
                          "tech jargon."),
}

cfg = Config.from_env()
client = FireworksClient(cfg.api_key, cfg.base_url, cfg.request_timeout)
report = json.load(open("dataset/report.json", encoding="utf-8"))
scenes = {r["clip"]: r["scene_text"] for r in report}


def gen(style, scene_text, generic=False, temp=0.4):
    if generic:
        user = (f"{GENERIC[style]}\nSCENE FACTS: {scene_text}\n"
                f"TRANSCRIPT: (no discernible speech)\nCAPTION:")
        msgs = [{"role": "system", "content": S.SYSTEM},
                {"role": "user", "content": user}]
    else:
        msgs = S.build_messages(style, scene_text, "")
    cap = _clean(client.chat(model=CAPTION_MODEL, messages=msgs,
                             temperature=temp, max_tokens=320,
                             reasoning_effort="low"))
    return "" if _is_refusal(cap) else cap


def best_of(style, scene_text, n, generic=False):
    spec = S.STYLE_SPECS[style]
    drafts = []
    for k in range(n):
        t = 0.4 if k == 0 else (0.6 if style == "formal" else 0.95)
        c = gen(style, scene_text, generic=generic, temp=t)
        if c and c not in drafts:
            drafts.append(c)
    if not drafts:
        return ""
    if len(drafts) == 1:
        return drafts[0]
    best, key = drafts[0], (-1, -1)
    for d in drafts:
        s = judge_caption(client, CAPTION_MODEL, spec["label"],
                          spec["contract"], scene_text, "", d,
                          reasoning_effort="low")
        k2 = (int(s.get("accuracy", 0)), int(s.get("tone", 0)))
        if k2 > key:
            best, key = d, k2
    return best


def one_cell(clip, style):
    st = scenes[clip]
    return clip, style, {
        "A_mech_bo3": best_of(style, st, 3),
        "B_mech_bo1": best_of(style, st, 1),
        "C_generic_bo3": best_of(style, st, 3, generic=True),
    }


cells = [(c, s) for c in scenes for s in STYLES]
results = {}
with cf.ThreadPoolExecutor(max_workers=2) as ex:
    futs = [ex.submit(one_cell, c, s) for c, s in cells]
    for i, f in enumerate(cf.as_completed(futs), 1):
        clip, style, caps = f.result()
        results.setdefault(clip, {})[style] = caps
        print(f"gen {i}/{len(cells)}", flush=True)


def score(judge_model, spec, scene_text, cap):
    if not cap:
        return 0
    s = judge_caption(client, judge_model, spec["label"], spec["contract"],
                      scene_text, "", cap, reasoning_effort="low")
    a, t = int(s.get("accuracy", 0)), int(s.get("tone", 0))
    return None if (a == 0 and t == 0) else a + t


rows = []


def score_cell(clip, style):
    spec = S.STYLE_SPECS[style]
    st = scenes[clip]
    row = {"clip": clip, "style": style}
    for cfg_name, cap in results[clip][style].items():
        row[cfg_name] = {"caption": cap}
        for jn, jm in JUDGES.items():
            row[cfg_name][jn] = score(jm, spec, st, cap)
    return row


with cf.ThreadPoolExecutor(max_workers=2) as ex:
    futs = [ex.submit(score_cell, c, s) for c, s in cells]
    for i, f in enumerate(cf.as_completed(futs), 1):
        rows.append(f.result())
        print(f"score {i}/{len(cells)}", flush=True)

os.makedirs("eval", exist_ok=True)
json.dump(rows, open("eval/ablations_raw.json", "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)

# aggregate
CONFIGS = ["A_mech_bo3", "B_mech_bo1", "C_generic_bo3"]
md = ["# Ablations — do the designed mechanisms cause the quality?", "",
      "All configs caption the same 15 official clips from identical "
      "Gemma 4 scene facts, using the serverless fallback caption model "
      "(gpt-oss-120b) — the path most likely to be graded. Two independent "
      "judges score accuracy + tone (sum, max 10). Unparseable judge "
      "responses are excluded, not imputed. Raw data: "
      "`ablations_raw.json`.", "",
      "| config | " + " | ".join(JUDGES) + " | n |",
      "|---|---|---|---|"]
for cn in CONFIGS:
    parts = []
    ns = []
    for jn in JUDGES:
        vals = [r[cn][jn] for r in rows if r[cn][jn] is not None]
        parts.append(f"{sum(vals)/len(vals):.2f}" if vals else "-")
        ns.append(len(vals))
    md.append(f"| {cn} | " + " | ".join(parts) + f" | {min(ns)} |")

md += ["", "## Head-to-head (both judges agree on winner)", ""]
for a, b in (("A_mech_bo3", "B_mech_bo1"), ("A_mech_bo3", "C_generic_bo3")):
    wa = wb = tie = 0
    for r in rows:
        va = [r[a][j] for j in JUDGES if r[a][j] is not None]
        vb = [r[b][j] for j in JUDGES if r[b][j] is not None]
        if not va or not vb:
            continue
        sa, sb = sum(va) / len(va), sum(vb) / len(vb)
        if sa > sb: wa += 1
        elif sb > sa: wb += 1
        else: tie += 1
    md.append(f"- **{a} vs {b}**: {wa}–{wb} ({tie} ties)")

open("eval/ABLATIONS.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("DONE — eval/ABLATIONS.md written", flush=True)
