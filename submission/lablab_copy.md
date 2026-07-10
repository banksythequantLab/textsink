# lablab.ai submission — paste-ready copy

## Project Title
TextSink — Four Voices. One Truth.

## Short Description (blurb)
TextSink watches a video and speaks in four perfect tones. Gemma 4 grounds
every clip in visual facts, then writes formal, sarcastic, humorous-tech
and humorous-non-tech captions — plus live styled closed captions and two
AIs arguing about what they're watching, at spice level eleven.

## Long Description
TextSink is a containerized Track 2 captioning agent built end-to-end on
Gemma 4 (26B MoE) via a dedicated Fireworks deployment — the same model
does the visual grounding AND all four caption styles.

THE SCORED PIPELINE. ffmpeg samples frames across the whole clip; Gemma 4
extracts scene facts as strict JSON. If grounding comes back empty,
TextSink retries and refuses to caption blind — captions may only use
extracted facts, so accuracy holds on any hidden clip. Four tone
contracts with distinct comedic mechanisms (broadcast precision, deadpan
irony, dev-culture metaphor, warm relatability) produce four captions the
LLM judge can blind-sort. The container implements the standard
/input/tasks.json -> /output/results.json harness contract, runs clips
concurrently (3 official clips in ~30s warm), and if the Gemma deployment
is unreachable it cuts over per-task to serverless models so no task ever
scores zero.

BEYOND THE CONTRACT. The same grounding powers TextSink CC — real timed
closed-caption tracks (.srt/.ass + burned video) where each style keeps
one consistent voice with running gags across the clip. And The
Hecklers: two competing models (Gemma 4 vs gpt-oss-120b) argue about the
video turn by turn, every line generated live — sarcastic old men STAN &
GUS, code-reviewer-vs-vibe-coder LINT & VIBE, and gossiping neighbors
DORIS & PEARL, matching the three humor styles.

GEMMA TEACHES GEMMA — AND THE STUDENT WINS. Gemma 4 drafted candidates
at high temperature, judged its own drafts on accuracy and tone, and the
winners became a self-distilled SFT dataset. We fine-tuned
textsink-g3-captioner (Gemma-3-27B LoRA, Fireworks managed SFT) on those
judged winners: under a neutral LLM judge it beats its teacher's
prompted best-of-3 output 18-4 head-to-head, scoring higher on every
style (ab_results.json in the repo).

EVIDENCE, NOT CLAIMS. Three judge artifacts in the repo back every
statement above: GEMMA_PROVENANCE.md (where Gemma authored the entry),
eval/ABLATIONS.md (the designed mechanisms beat generic prompts 11-5
under two judges, on the fallback model itself), and
submission/fallback_verification (forced foreign-key run - zero empty
captions).

All demo material was generated on the official hackathon clips. MIT
licensed. Python 3.11, ffmpeg, plain requests — no framework lock-in.

## Technology tags
Gemma, Fireworks AI, AMD Developer Cloud, Docker, FFmpeg, Python

## Category tags
Video Captioning (Track 2), Best Use of Gemma

## Links
- GitHub: https://github.com/banksythequantLab/textsink
- Application URL: https://banksythequantlab.github.io/textsink/
- Video presentation: https://youtu.be/KpnMdaLMZTg
  (or upload demo_kit/TextSink_demo_final.mp4 directly)
- Slides: submission/TextSink_Track2.pdf
- Cover image: submission/cover_3x2.png (3:2, sponsors prominent)
- Container: ghcr.io/banksythequantlab/textsink:latest (public)
