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

GEMMA TEACHES GEMMA. Gemma 4 drafted candidates at high temperature,
judged its own drafts on accuracy and tone, and the winners became a
self-distilled SFT dataset — the model bootstrapping its own captioner
(tools/build_dataset.py, dataset included in the repo pipeline).

All demo material was generated on the official hackathon clips. MIT
licensed. Python 3.11, ffmpeg, plain requests — no framework lock-in.

## Technology tags
Gemma, Fireworks AI, AMD Developer Cloud, Docker, FFmpeg, Python

## Category tags
Video Captioning (Track 2), Best Use of Gemma

## Links (fill at submit time)
- GitHub: https://github.com/banksythequantLab/textsink
- Video presentation: (upload 2:45 demo)
- Slides: submission/TextSink_Track2.pdf (re-export with real captions)
- Cover image: submission/cover.png
- Demo URL: (Streamlit or repo GIF page)
