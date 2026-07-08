# TextSink — Continuation / Handoff
_Saved 2026-07-08. AMD Developer Hackathon ACT II — Track 2 (Video Captioning) + $6,000 "Best Use of Gemma 4" bonus. Deadline: Fri Jul 11, 2026, 12:00 PM ET._

## What this is
Containerized agent: one 30s–2min clip → four captions (formal, sarcastic, humorous-tech, humorous-non-tech). Runs entirely on Gemma 4 (same model does visual grounding AND the four captions).

## Status: WORKING and verified
- Real Gemma 4 run confirmed: accurate scene grounding + 4 clean, on-tone captions (no CoT leak).
- Mock mode runs offline; all modules compile on Python 3.11.
- Repo, turnkey .env, README, and submission assets are on B:.

## Where everything lives (B: drive)
- Code: B:\amd-track2-captioner\ (compiles on Python 3.11.9)
- Config/secrets: B:\amd-track2-captioner\.env (gitignored — API key + Gemma 4 deployment refs)
- Submission assets: B:\amd-track2-captioner\submission\
  - cover.png / cover.svg (TextSink cover, 1280x720)
  - TextSink_Track2.pptx / .pdf (8-slide judge deck)
  - demo_script.md (2:45 video script, shot-by-shot)

## Fireworks / Gemma 4 deployment (the important part)
- Account: banksythequant | API key in .env (FIREWORKS_API_KEY). ~US$56 credits.
- Gemma 4 is DEPLOY-ONLY on Fireworks (not serverless). Deployment exists:
  - name: accounts/banksythequant/deployments/gemma4cap
  - model: gemma-4-26b-a4b-it (26B MoE) on 1x NVIDIA_H200_141GB, scale-to-zero (min 0 / max 1, 300s window). Currently idled at 0 replicas (not billing).
  - Inference model ref: accounts/fireworks/models/gemma-4-26b-a4b-it#accounts/banksythequant/deployments/gemma4cap
  - First call cold-starts ~3-5 min (weight load), then scales to zero after 5 min idle.
- CRITICAL: Gemma 4 needs REASONING_EFFORT=none (emits "thought" preamble otherwise). gpt-oss needs "low".
- MI300X not supported for this model on Fireworks (VLLM) — use an NVIDIA shape.
- Serverless fallback (no deploy, no bonus): VISION_MODEL=accounts/fireworks/models/qwen3p7-plus, CAPTION_MODEL=accounts/fireworks/models/gpt-oss-120b, REASONING_EFFORT=low.

## Architecture / code map
clip → ffmpeg sample 8-16 frames (+opt Whisper audio) → Gemma 4 vision → scene JSON (facts) → 4 per-style tone-contract prompts → Gemma 4 → 4 captions → captions.json
- run.py CLI entry (auto-loads .env); --mock offline; --list-models.
- captioner/config.py env config (defaults to Gemma 4 base id + reasoning none).
- captioner/fireworks_client.py OpenAI-compatible REST client (+ _strip_reasoning, reasoning_effort passthrough).
- captioner/vision.py frames→scene JSON; captioner/styles.py the 4 tone contracts + few-shot (the differentiator); captioner/pipeline.py orchestration; captioner/mock.py offline client; captioner/judge.py + eval/run_eval.py self-eval.

## How to run
```
cd B:\amd-track2-captioner
python run.py --input <folder-of-clips>      # auto-loads .env -> Gemma 4 (first call cold-starts ~5 min)
python run.py --input test_clip.mp4 --mock   # offline wiring test, no key
```
Bare runs need `pip install requests` + ffmpeg on PATH; or use the Dockerfile (bundles both).

## Gotchas learned
- Correct sandbox session path uses ...ff7179b1782a... (typo'd 1852a fails).
- Windows<->sandbox(mnt) file sync lags; write via bash heredoc to mnt path is reliable.
- rm on mnt outputs often "Operation not permitted" — use .gitignore/zip exclusions. Deletion fine on B: via PowerShell.
- Sync to B:: rebuild bundle zip, then Expand-Archive -Force to B:\.

## Brand
TextSink (wordmark: "Text" white + "Sink" amber). Tagline: "Four voices. One truth."
Repo folder stays amd-track2-captioner (avoid breaking paths); GitHub repo name: textsink. MIT LICENSE included.

## Scale-to-zero when done
PATCH .../deployments/gemma4cap:scale {"replicaCount":0}

## LEFT TO DO — see task.md
