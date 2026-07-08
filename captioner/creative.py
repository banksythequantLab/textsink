"""Creative engine: comedy brief -> N drafts -> self-judged best pick.

Every call runs on the same Gemma 4 model. This loop IS the "Best Use of
Gemma 4" story: the model grounds the scene, finds the comedic angle,
drafts three captions per style, then judges its own drafts and ships the
winner.
"""
from __future__ import annotations

import json

BRIEF_SYSTEM = (
    "You are a comedy writer's researcher. Given factual notes about a short "
    "video clip, extract the raw material a caption writer needs. Be concrete "
    "and specific - name the exact detail, not a category. Never invent facts "
    "that are not in the notes. Strict JSON only."
)

BRIEF_INSTRUCTION = (
    "From these scene facts, respond with JSON using exactly these keys:\n"
    "hook: the single most distinctive, concrete detail in the clip (one phrase)\n"
    "incongruity: the funniest contrast or unexpected element, if any\n"
    "irony: what a deadpan observer would dryly note about this situation\n"
    "tech_metaphor: one parallel between this scene and software/dev culture\n"
    "everyday_parallel: one relatable everyday-life parallel any adult knows\n"
    "Use an empty string when nothing fits. JSON only, no commentary."
)
