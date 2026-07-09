# TextSink demo — recording runbook (2:45 target)

Everything you need is in this folder. Files are numbered in play order.
Record at 1080p (OBS or Win+Alt+R Game Bar). Terminal font 18pt+, dark
theme. One clean take per segment is fine — we cut, not restart.

## Segment plan

**SEG 1 — 0:00–0:20 · COLD OPEN**
PLAY: 01_fourvoices_grid.mp4 (full screen)
SAY: "One video. Four voices. A formal narrator, a deadpan cynic, a
developer who's seen things, and your favorite neighbor. This is
TextSink — and every word you're seeing was written by Gemma 4, live,
about the actual competition clips."

**SEG 2 — 0:20–0:55 · THE GRADED RUN (live terminal)**
DO: open PowerShell in B:\amd-track2-captioner, run the command from
terminal_commands.txt. It probes the deployment, captions 3 official
clips with best-of-3 self-judging, writes results.json (~60-90s — record
it all; we timelapse the middle).
SAY: "Under the hood it's the official Track 2 contract. tasks.json in,
results.json out, containerized. The container probes its model access,
grounds every clip in scene facts, drafts three captions per style,
judges its own drafts, and ships the winner. If grounding ever comes
back empty it refuses to caption blind — an empty caption is
structurally impossible."

**SEG 3 — 0:55–1:20 · FOUR MECHANISMS**
SHOW: 02_captions_slide.jpg
SAY: "Four styles isn't one prompt with four adjectives. Broadcast
precision. Deadpan scale-mismatch irony. A dev-culture metaphor built
from what's actually on screen. And warm, everyday relatability. An LLM
judge can blind-sort these — that's the tone score."

**SEG 4 — 1:20–1:45 · TEXTSINK CC**
PLAY: 03_cc_sarcastic_kitten.mp4
SAY: "Then we kept going. The same grounding becomes real closed
captions — a timed .srt you can toggle — one consistent voice across the
whole clip. 'A tiny orange predator prepares for total world
domination... the menace is closing in. Send help.'"

**SEG 5 — 1:45–2:25 · THE HECKLERS**
PLAY: 04_hecklers_ocean_stan_gus.mp4 (~15s), then cut to
05_hecklers_kitten_doris_pearl.mp4 (~10s)
SAY: "And because one voice is a monologue: The Hecklers. Two different
models — Gemma 4 versus GPT-OSS — watch the clip and argue about it,
turn by turn, every line generated live. 'The deep blue menace is
swallowing the very earth!' — 'Only you think foam is world-ending,
Stan.' Three duos: old men, a code reviewer versus a vibe coder, and
two neighbors who think your kitten looks like a lying ex-husband."

**SEG 6 — 2:25–2:45 · CLOSE**
SHOW: 07_close_slide.jpg
SAY: "Gemma grounds it, writes it, argues it, judges it — and last
night, it trained its own captioner on the drafts it judged best.
TextSink. Four voices. One truth.
github.com/banksythequantLab/textsink."

## Checklist before hitting record
- [ ] GPU pinned (Claude did this — confirm ready before SEG 2)
- [ ] Terminal: cd B:\amd-track2-captioner, cls, font 18pt+
- [ ] Close notifications / Discord
- [ ] Mic check, one sentence, play it back
- [ ] Export MP4 1080p, under 200MB
