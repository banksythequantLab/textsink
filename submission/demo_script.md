# TextSink — 2:45 demo script (v2, post-Hecklers)

**Voice:** confident, dry, lets the captions do the joking.
**Screen:** terminal + rendered videos. No slides in the video itself.

---

## COLD OPEN — 0:00–0:20 (the grid)
**SHOW:** `kitten_cc_fourvoices.mp4` full screen, all four quadrants
captioning live.
**SAY:** "One video. Four voices. A formal narrator, a deadpan cynic, a
developer who's seen things, and your favorite neighbor. This is
TextSink — and everything you're about to see was written by Gemma 4,
live, about the actual competition clips."

## THE CONTRACT — 0:20–0:50 (terminal, real run)
**SHOW:** terminal: `docker run … textsink` with `/input/tasks.json`
mounted; then `results.json` opening in an editor.
**SAY:** "Under the hood it's the official Track 2 contract — tasks.json
in, results.json out, containerized, four exact style keys. Frames are
sampled across the whole clip; Gemma 4 extracts scene facts as strict
JSON, and captions can only use those facts. If grounding ever comes back
empty, TextSink refuses to caption blind. Three official clips, thirty
seconds, zero hallucinations."

## FOUR MECHANISMS — 0:50–1:20 (captions on screen)
**SHOW:** the four kitten captions side by side (slide-style frame).
**SAY:** "Four styles isn't one prompt with four adjectives. Formal is
broadcast precision. Sarcastic is scale-mismatch irony — a fierce
predator, one tiny uncoordinated step at a time. Humorous-tech maps the
scene onto dev culture — an AI agent navigating its first training
environment. Non-tech is warm and relatable. An LLM judge can blind-sort
these — that's the tone score."

## TEXTSINK CC — 1:20–1:50 (the product)
**SHOW:** `sarcastic` CC track playing: lines appearing in time.
**SAY:** "Then we went further. The same grounding, segmented into time
beats, becomes real closed captions — an .srt you can toggle — where each
voice stays in character across the whole clip. 'A tiny orange predator
prepares for total world domination… the menace is closing in. Send
help.' That's a comedy track, timed like broadcast CC."

## THE HECKLERS — 1:50–2:25 (the showstopper)
**SHOW:** `kitten_doris_and_pearl.mp4`, then a beat of
`office_lint_vs_vibe.mp4`.
**SAY:** "And because one voice arguing is a monologue: The Hecklers.
Two different models — Gemma 4 versus GPT-OSS — watch the same clip and
argue about it, turn by turn, every line generated live. Old men on a
balcony. A code reviewer versus a vibe coder. Two neighbors over the
fence: 'That's exactly how my ex-husband looked before he lied.' The
models wrote that. About a kitten."

## CLOSE — 2:25–2:45
**SHOW:** cover frame: TextSink wordmark, "Four voices. One truth.",
repo URL.
**SAY:** "Grounded enough for the leaderboard, funny enough to heckle.
TextSink — four voices, one truth. Built on Gemma 4 and Fireworks for
AMD ACT II. github.com/banksythequantLab/textsink."

---

### Recording checklist
- [ ] Re-pin GPU (min=1) before recording so runs are instant
- [ ] Terminal font ≥ 18pt, dark theme
- [ ] Capture at 1080p; OBS; mic check
- [ ] Export MP4 < 200MB for lablab upload
