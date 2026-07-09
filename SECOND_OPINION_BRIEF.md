# TextSink — Second-Opinion Brief

You are being asked for a critical second opinion on a hackathon entry ~24h
before its deadline. Be adversarial: find weaknesses, wrong assumptions, and
missed opportunities. Concrete fixes only — there is no time for rewrites.

## The contest

AMD Developer Hackathon: ACT II (lablab.ai), Track 2 "Video Captioning."
Deadline: Fri Jul 11, 2026, 12:00 PM ET (~24h away). Team registered ✔.

- Task: for a fixed set of hidden short clips (30s–2min, Pexels stock
  mirrored in a public GCS bucket — we found and downloaded all 15), output
  captions in 4 styles: formal, sarcastic, humorous_tech, humorous_non_tech.
- Scoring: leaderboard, LLM-judge on ACCURACY (faithful to clip) and TONE
  (style execution). Nothing else is scored for placement.
- Harness (verified from a rival's public repo): containerized linux/amd64,
  reads /input/tasks.json [{task_id, video_url, styles[]}], writes
  /output/results.json [{task_id, captions:{4 keys}}]. ~12 hidden clips,
  ~10-minute container time limit. FIREWORKS_API_KEY provided at run time
  (unknown whose key the grader injects — see Risk #1).
- Prizes: Track 2 = $2,500/$1,500/$1,000. Partner bonus "Best Use of Gemma
  in Video Captioning" = $3,000 (human-judged). Total target: $5,500.
- Fine-tuning explicitly permitted. Models via Fireworks AI API.

## What was built (all verified running, repo public)

Repo: github.com/banksythequantLab/textsink (MIT). Code: Python 3.11,
ffmpeg, plain requests. Docker image built + harness contract verified
in-container: 3 official clips → 12 captions in 22s, all filled.

1. **Scored pipeline**: ffmpeg samples 8–16 frames across whole clip →
   Gemma 4 (26B MoE, `gemma-4-26b-a4b-it`, dedicated Fireworks deployment,
   NVIDIA H200, scale-to-zero) extracts scene facts as strict JSON →
   4 per-style "tone contracts" with few-shot exemplars → 4 captions.
   Same Gemma model does vision AND captions (the Gemma-bonus story).
2. **Reliability ladder**: vision retries at rising temp → refuses to
   caption blind → falls back to serverless (qwen3p7-plus vision +
   gpt-oss-120b captions) → last resort: direct frame captioning. An empty
   caption is structurally impossible (verified).
3. **TextSink CC** (product layer, not scored): clip → time-segmented
   beats → per-style timed closed-caption tracks (.srt/.ass + burned mp4),
   one consistent voice with running gags, spans full clip length.
   57 CC videos across 14/15 official clips.
4. **The Hecklers** (product layer): two models argue about the video turn
   by turn — Gemma 4 vs gpt-oss-120b, each reads the argument so far.
   3 persona duos matching the humor styles: STAN & GUS (sarcastic old
   men), LINT vs VIBE (code reviewer vs vibe-coder), DORIS & PEARL
   (gossiping neighbors). 45 tracks (15 clips × 3 flavors), full length,
   "spice eleven" prompts. Every line model-generated.
5. **Gemma-teaches-Gemma dataset**: Gemma drafted 3 candidates/style at
   high temp, judged its own drafts (accuracy+tone), winners → 60-row SFT
   JSONL from the 15 official clips. NOT yet used for fine-tuning (owner
   cancelled training: "no more training").
6. **Robust beats parser**: handles schema drift (start_time/description),
   tool-call wrappers ({"action","action_input"} with python-quoted JSON),
   markdown/dash timestamp lists, frame-timestamp payloads, truncation
   salvage, and compressed-time rescaling to true clip duration.
7. **Submission assets**: 10-slide dark-theme deck (rebuilt, QA'd) with
   real frames + real dialogue; README with GIFs; paste-ready lablab copy;
   2:45 demo script (not yet recorded).

## Real output samples (judge for quality yourself)

Kitten clip (official), all-Gemma scored captions:
- formal: "An orange tabby kitten walks forward through the foliage toward
  the camera in a wooded area."
- sarcastic: "A fierce predator emerges from the brush, clearly ready to
  conquer the entire forest one tiny, uncoordinated step at a time."
- humorous_tech: "The latest AI agent successfully navigating its first
  training environment. It's small, but the feature set is looking
  promising."
- humorous_non_tech: "A tiny orange explorer makes a grand entrance,
  bravely navigating the treacherous jungle of backyard leaves."

Hecklers (ocean waves clip, sarcastic duo, live two-model dialogue):
STAN: "Ocean's attacking the coast! It's a watery apocalypse, Gus!" /
GUS: "Apocalypse? Your kettle's just doing a light rinse." / STAN: "The
deep blue menace is swallowing the very earth!" / GUS: "Only you think
foam is world-ending, Stan."

## Key decisions to second-guess

1. **All-in on the Gemma deployment for the scored run** (owner's call).
   The container's default models point at OUR account-scoped deployment
   (`...#accounts/banksythequant/deployments/gemma4cap`). If the grading
   harness injects THEIR OWN Fireworks key, calls to our deployment fail
   (account-scoped) → the ladder drops every task to serverless fallback
   models under their key. So the "all-Gemma" scored run only happens if
   the harness uses/allows our key. Cold start is 3–5+ min (once could not
   get H200 capacity for 90 min); plan is to pin min_replicas=1 before the
   deadline window (~$10/hr-class, ~$56 credits left, unknown judging
   time). Is there a better play?
2. **No fine-tune** despite rules encouraging it and a dataset in hand.
   Owner cancelled. Worth reversing in the last 24h via Fireworks managed
   SFT on gemma-3-27b (gemma-4 is tunable=False on Fireworks)?
3. **Single-shot captions in the scored path.** A best-of-3 + self-judge
   loop was designed (and is proven in the dataset generator) but never
   wired into main.py. Time budget allows it (22s used of 600s). Wire it
   in tonight, or is single-shot + strong contracts safer before a
   deadline?
4. **CC + Hecklers earn zero leaderboard points.** They exist for the $3k
   human-judged Gemma bonus + demo. Was this the right allocation of the
   final 48h vs. grinding leaderboard caption quality?
5. **Whisper/audio is OFF** (TRANSCRIBE_BACKEND=none; local torch broken,
   Fireworks audio endpoint 401 on this account). The 15 bucket clips are
   stock footage, likely speechless — but if any hidden clip has speech,
   we caption visuals only. Accept, or fix in 24h?

## Known weaknesses

- humorous_tech captions drift toward stock dev jokes (deploy/CI) when the
  scene is generic; the incongruity-brief stage that would fix this
  (creative.py) is half-built and not wired in.
- 2 of 15 clips still occasionally flake in the DEMO beats stage (not the
  scored path).
- The judged-clip assumption (bucket's 15 = judge set) is unverified.
- Demo video not yet recorded; submission form not yet filled.

## What we want from you

1. Rank the 5 decisions above by expected point/dollar impact; flag any
   you'd reverse in the next 24 hours and exactly how.
2. Critique the caption samples vs. what a winning entry looks like —
   specific prompt-level improvements welcome.
3. Any failure mode in the harness plan we haven't listed (key injection,
   timeouts, cold start, output format edge cases)?
4. The 60-minute highest-leverage action list for the final day.
