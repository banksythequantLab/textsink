# TextSink — Knockout Review Brief (for an AI with web access)

You are a hackathon judge and coach. Everything you need is public — read
it via the links below, then grade us and tell us how to turn a strong
entry into a knockout. Be adversarial and specific. We have LESS THAN 12
HOURS to the deadline (Fri Jul 11, 12:00 PM ET), so suggestions must be
executable by one person plus one AI assistant in hours, not days.

## Step 1 — Read the contest (the thing we're judged against)

- Hackathon page: https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii
  We're in **Track 2: Video Captioning**. Read that track's description
  and the "What to Submit" + "Judging Criteria" sections carefully.
- Key facts to anchor on: Track 2 is scored via **leaderboard — an
  LLM-judge rates caption ACCURACY and TONE** on a hidden set of short
  clips (30s–2min). Submissions must be containerized (linux/amd64),
  public GitHub repo, runnable per README. The judging harness runs
  containers with `/input/tasks.json` → `/output/results.json`.
- Separate prize we're chasing hard: **$3,000 "Best Use of Gemma in
  Video Captioning"** (human-judged, Google DeepMind partner prize).
  Track placement prizes: $2,500 / $1,500 / $1,000.

## Step 2 — Read our project (in this order, like a judge would)

1. Repo: https://github.com/banksythequantLab/textsink
2. Live showcase: https://banksythequantlab.github.io/textsink/
3. Evidence file behind our headline claim:
   https://raw.githubusercontent.com/banksythequantLab/textsink/master/ab_results.json
4. The scored entrypoint:
   https://raw.githubusercontent.com/banksythequantLab/textsink/master/main.py
5. The creative core:
   https://raw.githubusercontent.com/banksythequantLab/textsink/master/captioner/styles.py
   and https://raw.githubusercontent.com/banksythequantLab/textsink/master/tools/hecklers.py
6. Public container (verify it pulls anonymously):
   `docker pull ghcr.io/banksythequantlab/textsink:latest`

## Step 3 — Context you can't fully get from links

- **What TextSink is:** one pipeline — Gemma 4 (26B MoE, dedicated
  Fireworks deployment) grounds each clip in strict-JSON scene facts,
  then writes 4 style captions (formal / sarcastic / humorous_tech /
  humorous_non_tech) with best-of-3 drafting self-judged by the same
  model. Same grounding also powers two unscored showcase products:
  TextSink CC (timed .srt closed-caption comedy tracks) and The Hecklers
  (two models — Gemma 4 vs gpt-oss-120b — arguing about the video live,
  turn by turn, three persona duos).
- **The key unknown:** we don't know if the grading harness injects ITS
  OWN Fireworks API key or uses ours. Our Gemma deployment is
  account-scoped: under a foreign key it 404s, and the container probes
  this at startup, falling back to serverless models (qwen3p7-plus
  vision + gpt-oss-120b captions) so no task ever scores zero. There is
  NO serverless Gemma on Fireworks (verified) — so the fallback is
  necessarily non-Gemma, and the container logs which path served each
  run for auditability.
- **Fine-tune story:** Gemma 4's self-judged winning captions became a
  60-row SFT set; we fine-tuned textsink-g3-captioner (Gemma-3-27B LoRA,
  Fireworks managed SFT). Under a neutral judge it wins 18–4 (9 ties) on
  the 31 cleanly-judged pairs — caveats (judge noise, train/eval overlap
  as deliberate distribution targeting) are disclosed in the README.
  The tuned model is NOT in the scored path (serving it needs 2×H200).
- **Verified numbers:** full 15-clip dress rehearsal (same clips as the
  official sample bucket): 199s, all captions filled, zero refusals —
  about ⅓ of the harness's ~10-minute budget.
- **Already fixed after a prior adversarial review — don't re-flag:**
  internal docs removed from the repo; the 18–4 stat restated with
  methodology + caveats; Gemma-fallback transparency note added; GHCR
  image made public; degenerate-baseline concern acknowledged via the
  cleanly-judged-pairs framing.

## Step 4 — What we want from you

1. **Grade us** as a judge would: score /10 for (a) Track 2 placement
   potential and (b) the Gemma prize, each with 2–3 sentences of
   reasoning grounded in what you actually read.
2. **Falsification pass:** anything on the public path that is broken,
   contradictory, overclaimed, or unrendered? Exact URL + location.
3. **Knockout list:** the 3–5 highest-impact improvements still possible
   in under 12 hours (one person + one AI). For each: expected impact on
   which prize, and estimated time. Do NOT suggest: retraining, new
   product features, serverless Gemma (doesn't exist), or anything
   requiring the organizers.
4. **The one-liner:** if you had to pitch this project to another judge
   in one sentence, what is it? (We'll steal it for the submission form
   if it beats ours: "TextSink watches a video and speaks in four
   perfect tones — then two AIs argue about what they saw.")
