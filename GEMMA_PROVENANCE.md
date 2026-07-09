# Gemma Provenance — where Gemma 4 authored this entry

This is the receipts document. Every claim links to an artifact in this
repo. The point: Gemma 4 was not "the model we called" — it was the
system's designer, author, judge, and teacher. The 90-second read is the
bold lines; everything else is evidence.

## 1. Gemma 4 wrote every demonstration you can see

**All sample captions, all 57 closed-caption tracks, all Gemma-side
Heckler lines in this repo and on the showcase site are Gemma 4's own
output** (`gemma-4-26b-a4b-it`, dedicated Fireworks deployment), generated
against the official hackathon clips. Nothing was hand-written or
cherry-edited. Examples: the README's kitten captions, the sunset roast
battle, every video in `docs/grids/` and `docs/hecklers/`.

## 2. Gemma 4 stress-tested the system into its final design

The reliability architecture exists because Gemma's real failure modes
were caught and engineered around during development on the official
clips — each fix is in the git history:

- **Refuse-to-caption-blind gate**: early runs let unparseable grounding
  leak junk into the caption stage; the model then emitted refusal text
  ("I cannot fulfill this request...") which would have shipped as
  scored captions. The dress rehearsal caught 5/15 clips doing this →
  the sane-scene gate + refusal filter in `captioner/pipeline.py`.
- **Schema-drift-proof parsing**: Gemma (and fallback models) variously
  emitted `start_time/end_time` keys, tool-call wrappers with
  python-quoted payloads, markdown beat lists, and compressed timelines
  (beats ending at 10s on a 57s clip). The parser in
  `tools/textsink_cc.py` normalizes all of it; timestamps rescale to
  true duration.
- **Reasoning suppression**: Gemma 4 emits a thought preamble unless
  `REASONING_EFFORT=none` — documented in `.env.example` so nobody
  rediscovers it the hard way.

## 3. Gemma 4 judged its own drafts — the scored path runs on its taste

The best-of-3 mechanism (`captioner/pipeline.py::_best_caption`) drafts
at high temperature and has the same model score each draft on accuracy
and tone (`captioner/judge.py`), shipping the winner. This self-judgment
loop was developed and validated entirely on Gemma 4 against the 15
official clips: 199 seconds, zero refusals, all captions filled.

## 4. Gemma 4 taught its successor — and the student wins

`tools/build_dataset.py` had Gemma 4 draft 3 candidates per style per
official clip, judge them itself, and keep only winners scoring 5/5
accuracy — a 60-row self-distilled SFT set built without a single human
label. That trained `textsink-g3-captioner` (Gemma-3-27B LoRA, Fireworks
managed SFT). Under a *neutral* judge (gpt-oss-120b, not Gemma), the
student beats the teacher's prompted best-of-3 **18–4 with 9 ties** on
the 31 cleanly-judged pairs — raw data in `ab_results.json`, exclusion
methodology in `tools/ab_clean.py`, caveats disclosed in the README.
Gemma designing its own training data and producing a model that
outperforms its own prompted ceiling is, we think, the deepest possible
"use of Gemma" in a captioning system.

## 5. The style mechanisms are Gemma-validated design, not adjectives

The four tone contracts in `captioner/styles.py` encode distinct comedic
*mechanisms* — broadcast precision; deadpan scale-mismatch irony;
scene-specific dev-culture mapping (with generic "AI agent learning"
jokes explicitly banned after Gemma's own outputs exposed that failure
mode); warm observational relatability. Each revision was validated by
regenerating against the official clips and judging the delta — e.g. the
tech-humor contract rewrite moved outputs from stock deploy jokes to
"The ultimate race condition: passengers trying to exit the train while
others simultaneously attempt to board."

## 6. The runtime constraint, owned

Gemma 4 is deploy-only on Fireworks (no serverless), and deployments are
account-scoped. So a grading run under a foreign API key cannot
physically reach Gemma — the container detects this at startup, logs it,
and falls back to serverless models that inherit every Gemma-designed
mechanism above (verified: `submission/fallback_verification/`). Gemma's
fingerprint is in the architecture, contracts, judging logic, and
training data — which is to say: in every caption the system produces,
whichever model utters it.
