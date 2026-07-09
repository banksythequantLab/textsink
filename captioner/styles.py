"""The four-style caption engine — the scoring differentiator.

Judging scores each caption on ACCURACY (faithful to the clip) and TONE (how
well it matches the requested style). We attack both:

* ACCURACY: captions are generated from a grounded scene description + transcript
  with a hard "only use given facts" rule (see SYSTEM).
* TONE: each style carries an explicit *tone contract* plus few-shot exemplars
  so the model produces a distinct, well-executed voice per style.

Styles required by Track 2: formal, sarcastic, humorous-tech, humorous-non-tech.
"""
from __future__ import annotations

from typing import Any

STYLE_SPECS: dict[str, dict[str, Any]] = {
    "formal": {
        "label": "Formal",
        "contract": (
            "Neutral, precise, broadcast/documentary register. Third person, "
            "present tense. State what happens plainly. No jokes, no opinion, "
            "no first person, no exclamation marks."
        ),
        "exemplars": [
            ("A person in a lab coat pours a blue liquid into a beaker; it fizzes.",
             "A researcher combines two solutions in a beaker, producing a rapid "
             "effervescent reaction."),
            ("Children kick a soccer ball in a park at sunset; one scores.",
             "Children play soccer in a park at dusk as one player scores a goal."),
        ],
    },
    "sarcastic": {
        "label": "Sarcastic",
        "contract": (
            "Dry, ironic, understated snark; deadpan wit and faux-enthusiasm. "
            "Observational and slightly weary, never try-hard edgy. "
            "Never cruel and never punching down — the target is the situation, "
            "not a person's identity or appearance. One sharp line."
        ),
        "exemplars": [
            ("A person confidently assembles furniture; parts are clearly left over.",
             "Ah yes, the classic 'three extra screws' finish — clearly decorative, "
             "nothing structural."),
            ("A cat stares at a glass it has knocked onto the floor.",
             "A true mystery for the ages: no witnesses, no suspects, just vibes."),
        ],
    },
    "humorous_tech": {
        "label": "Humorous (tech)",
        "contract": (
            "Playful humor drawn from developer / startup / CS culture. Map ONE "
            "specific technical concept (latency, overfitting, cold start, "
            "memory leak, race condition, feature flag, merge conflict...) "
            "directly onto something actually visible in THIS scene. The joke "
            "must be scene-specific — never generic 'AI agent learning' or "
            "stock 'deploy to prod' framing unless the scene truly is one. "
            "One or two lines."
        ),
        "exemplars": [
            ("A dog knocks over a stack of boxes that domino across a room.",
             "Live look at one tiny change in prod triggering a full cascade of "
             "downstream failures. Rollback, rollback!"),
            ("A person frantically searches a messy desk for keys.",
             "When the bug only repros in production and you're grepping every "
             "drawer for the stack trace."),
        ],
    },
    "humorous_non_tech": {
        "label": "Humorous (non-tech)",
        "contract": (
            "Warm, relatable, everyday humor — observational, wordplay welcome. "
            "The kind of thing a clever kid would say out loud while watching, "
            "not a stand-up bit. Absolutely NO tech jargon. Lands for any "
            "audience. One or two lines."
        ),
        "exemplars": [
            ("A toddler refuses broccoli and pushes the plate away.",
             "A seasoned negotiator holds the line: no deal will be reached on the "
             "broccoli front tonight."),
            ("A person naps on a couch while a movie plays.",
             "He didn't fall asleep during the movie — he was resting his eyes for "
             "the entire second half."),
        ],
    },
}

SYSTEM = (
    "You are an expert video caption writer. You will be given a factual, "
    "grounded description of a short video clip (scene facts + any spoken "
    "transcript). Write ONE caption in the requested STYLE.\n"
    "HARD RULES:\n"
    "1. Be faithful: use ONLY facts present in the scene description or "
    "transcript. Never invent objects, people, brands, or events.\n"
    "2. Match the STYLE's tone contract exactly.\n"
    "3. 1-2 sentences, max ~40 words. No hashtags, no emojis, no surrounding "
    "quotation marks.\n"
    "4. Output only the caption text — no preamble, no style label."
)


def build_messages(style: str, scene_text: str, transcript: str) -> list:
    spec = STYLE_SPECS[style]
    shots = "\n\n".join(
        f"SCENE: {scene}\nSTYLE: {spec['label']}\nCAPTION: {cap}"
        for scene, cap in spec["exemplars"]
    )
    tr = (transcript or "").strip() or "(no discernible speech)"
    user = (
        f"STYLE = {spec['label']}\n"
        f"TONE CONTRACT: {spec['contract']}\n\n"
        f"Examples of this style:\n{shots}\n\n"
        f"Now caption this clip.\n"
        f"SCENE FACTS: {scene_text}\n"
        f"TRANSCRIPT: {tr}\n\n"
        f"CAPTION:"
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]
