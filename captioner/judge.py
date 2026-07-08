"""Optional LLM self-judge for local iteration (NOT the contest scoring)."""
from __future__ import annotations

import json

JUDGE_SYSTEM = (
    "You are a strict judge for a video-captioning contest. Score a caption on "
    "two axes, each an integer 1-5: ACCURACY (faithful to the scene facts and "
    "transcript, no hallucinations) and TONE (match to the target style). "
    'Respond with strict JSON: {"accuracy": int, "tone": int, "reason": string}.'
)


def judge_caption(client, model, style_label, contract, scene_text, transcript,
                  caption, reasoning_effort="low") -> dict:
    user = (
        f"TARGET STYLE: {style_label}\nCONTRACT: {contract}\n\n"
        f"SCENE FACTS: {scene_text}\nTRANSCRIPT: {transcript or '(none)'}\n\n"
        f"CAPTION TO SCORE: {caption}\n\nJSON:"
    )
    raw = client.chat(model=model, messages=[
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": user},
    ], temperature=0.0, max_tokens=200, reasoning_effort=reasoning_effort)
    try:
        s, e = raw.find("{"), raw.rfind("}")
        return json.loads(raw[s:e + 1])
    except Exception:
        return {"accuracy": 0, "tone": 0, "reason": "unparseable"}
