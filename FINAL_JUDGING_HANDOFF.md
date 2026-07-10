# TextSink — Final Judging Handoff (v3, for independent AI reviewers)

You are one of three independent reviewers grading this hackathon entry
before submission. Use web access to read everything yourself — trust
the links, not our summary. Deadline is ~30 hours away; suggestions must
be executable by one person + one AI assistant in HOURS. Use the exact
response format at the bottom so the three reviews can be compared.

## The contest

- Event: https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii
  — Track 2: Video Captioning. Read the track card, "What to Submit,"
  and "Judging Criteria."
- Scoring: Track 2 placement is a **leaderboard — an LLM judge scores
  caption ACCURACY and TONE** on hidden 30s–2min clips. The harness runs
  containers: `/input/tasks.json` → `/output/results.json`, linux/amd64.
  Separately, a human-judged **$3,000 "Best Use of Gemma in Video
  Captioning"** partner prize (Google DeepMind).

## The judge path (read in this order)

1. Repo + README: https://github.com/banksythequantLab/textsink
   — note the "For judges" section near the top.
2. Provenance receipts:
   https://github.com/banksythequantLab/textsink/blob/master/GEMMA_PROVENANCE.md
3. Ablation study:
   https://github.com/banksythequantLab/textsink/blob/master/eval/ABLATIONS.md
   (raw: eval/ablations_raw.json)
4. Fine-tune A/B evidence:
   https://raw.githubusercontent.com/banksythequantLab/textsink/master/ab_results.json
   (methodology: tools/ab_test.py, tools/ab_clean.py)
5. Fallback verification:
   https://github.com/banksythequantLab/textsink/tree/master/submission/fallback_verification
6. Live showcase (galleries of real output on all 15 official sample
   clips): https://banksythequantlab.github.io/textsink/
7. Public image (verify anonymously):
   `docker pull ghcr.io/banksythequantlab/textsink:latest`
8. Scored entrypoint: main.py · creative core: captioner/styles.py,
   tools/hecklers.py

## Current state (facts, so you don't re-derive them)

- **Architecture:** Gemma 4 (deploy-only on Fireworks, account-scoped
  deployment) grounds clips in strict-JSON scene facts → 4 tone
  contracts with distinct comedic mechanisms → best-of-3 drafts,
  self-judged, winner ships. Startup probe: if the grading key can't
  reach the Gemma deployment (404), the container logs it and runs
  serverless fallback (qwen3p7-plus vision + gpt-oss-120b captions) —
  same contracts, same gates. There is NO serverless Gemma (verified);
  this constraint is owned openly in the README.
- **Evidence shipped:** ablations (mechanisms beat generic prompts 11–5
  head-to-head under two judges, best-of-3 beats single-shot 8–6 —
  measured ON the fallback model, i.e. quality travels with the
  Gemma-designed prompts, not the model); fine-tune A/B (Gemma-taught
  student wins 18–4 on the 31 cleanly-judged pairs, caveats disclosed);
  forced-foreign-key fallback run (3 official clips, 62s, zero empties).
- **Reliability:** 15-clip dress rehearsal 199s / zero refusals / all
  filled (~⅓ of harness budget). Refusal filter + sane-scene gate +
  3-tier ladder mean an empty caption is structurally impossible.
- **Showcase:** 14 four-voice CC grids + 31 live two-model argument
  videos (The Hecklers: Gemma 4 vs gpt-oss, three persona duos) on
  GitHub Pages; 2:45 demo video narrated in the builder's cloned voice.
- **Posture:** everything judge-facing is a static artifact; no live
  infrastructure is required post-deadline. ~$17 of API credit reserved
  solely as fuel if the harness bills our key. Deployment is
  scale-to-zero; the probe waits out a cold start if our key is used.
- **Already executed from two prior adversarial reviews (don't
  re-flag):** repo hygiene (internal docs removed); honest restatement
  of the 18–4 with methodology + train/eval-overlap disclosure;
  front-loaded "For judges" transparency; fallback verification
  artifact; instruction-following rule in the caption contract;
  package made public + relinked to correct repo; ablations added.

## Required response format (so 3 reviews can be compared)

1. **Scores:** Track 2 placement potential: X/10. Gemma prize: X/10.
   Two sentences of reasoning each, grounded in what you read.
2. **Falsification:** list anything broken / contradictory /
   overclaimed on the judge path, with exact URL + location. If nothing:
   say "clean."
3. **Top-1 action:** the single highest-impact improvement still doable
   in hours. One only. Include estimated time and which prize it moves.
4. **Up to 3 more suggestions** (optional), each ≤2 sentences, ranked.
5. **One-liner pitch:** your best one-sentence pitch for this entry.
6. **Submit verdict:** "submit as-is" or "fix X first, then submit."
