# TextSink

**Four voices. One truth.**

AMD Developer Hackathon: ACT II — Track 2 (Video Captioning), built for the
**Best Use of Gemma** challenge. One 30s–2min clip goes in; four
perfectly-toned captions come out — plus live styled closed captions and
two AIs arguing about what they're watching.

![Four voices, one clip](assets/fourvoices.gif)

*One clip, four voices — formal, sarcastic, humorous-tech,
humorous-non-tech — rendered as live closed captions. Every word grounded
in what's actually on screen. Every word written by Gemma 4.*

## What the judges' harness gets (Track 2 contract)

The container implements the standard Track 2 flow:

```
/input/tasks.json  ->  /output/results.json
```

```json
[{"task_id": "v2",
  "captions": {
    "formal": "An orange tabby kitten walks forward through the foliage toward the camera in a wooded area.",
    "sarcastic": "A fierce predator emerges from the brush, clearly ready to conquer the entire forest one tiny, uncoordinated step at a time.",
    "humorous_tech": "The latest AI agent successfully navigating its first training environment. It's small, but the feature set is looking promising.",
    "humorous_non_tech": "A tiny orange explorer makes a grand entrance, bravely navigating the treacherous jungle of backyard leaves."}}]
```

Those are real outputs from the official sample clips, generated end-to-end
by **Gemma 4** (`gemma-4-26b-a4b-it`, 26B MoE) on a dedicated Fireworks
deployment — the same model does the visual grounding AND all four styles.

## Why it isn't vanilla

**1. Grounding you can trust.** Frames are sampled across the whole clip
and Gemma 4 extracts scene facts as strict JSON. If grounding comes back
empty, TextSink retries at rising temperature and **refuses to caption
blind** rather than hallucinating. Captions may only use extracted facts.

**2. Four voices with different comedic mechanisms** (not one prompt with
four adjectives): formal = broadcast precision; sarcastic = deadpan
scale-mismatch irony; humorous-tech = the scene mapped onto dev culture;
humorous-non-tech = warm "we've all been there" relatability.

**3. Gemma teaches Gemma — and the student wins.** Gemma 4 drafted
candidate captions at high temperature, judged its own drafts on
accuracy + tone, and the winners became a self-distilled training set
(`tools/build_dataset.py`). We fine-tuned `textsink-g3-captioner`
(Gemma-3-27B LoRA, Fireworks managed SFT) on those 60 judged winners:
under a neutral LLM judge it beats its teacher's prompted best-of-3
output **18–4 head-to-head** (9 ties), scoring higher on every style
(`tools/ab_test.py`, results in `ab_results.json`).

**4. Live closed captions (TextSink CC).** The same grounding, segmented
into time beats — each style becomes a real timed CC track (`.srt` +
`.ass` + burned video) with one consistent voice and running gags.

**5. The Hecklers — two models argue about the video.**

![The Hecklers](assets/hecklers.gif)

Every line is generated live, turn by turn: **Gemma 4** plays the lead,
**gpt-oss-120b** plays the rival, each reading the argument so far.
Three flavors matching the contest styles: STAN & GUS (sarcastic old men),
LINT vs VIBE (code reviewer vs vibe-coder), DORIS & PEARL (neighbors over
the fence). Spice dial goes to eleven; grounding rules still apply.

## Quickstart

```bash
cp .env.example .env          # add your FIREWORKS_API_KEY

# Prebuilt image (linux/amd64) - no build needed:
docker pull ghcr.io/banksythequantlab/textsink:latest

# Or build it yourself (harness mode - what gets graded)
docker buildx build --platform linux/amd64 -t textsink .
docker run --rm -e FIREWORKS_API_KEY=fw_... \
  -v "$(pwd)/test_input:/input:ro" -v "$(pwd)/out:/output" textsink

# Local, no Docker (needs Python 3.11 + ffmpeg on PATH)
pip install -r requirements.txt
INPUT_PATH=test_input/tasks.json OUTPUT_PATH=results.json python main.py

# Offline wiring test - no API key needed
python run.py --input clip.mp4 --mock
```

### The fun stuff

```bash
# Styled closed captions: .srt + .ass + burned video, all four voices
python tools/textsink_cc.py --clip clip.mp4 --out cc_out --burn

# Two AIs arguing about your video, spice up to eleven
python tools/hecklers.py --clip clip.mp4 --burn --spice eleven --flavor sarcastic
python tools/hecklers.py --clip clip.mp4 --burn --flavor humorous_tech
python tools/hecklers.py --clip clip.mp4 --burn --flavor humorous_non_tech

# Single-caption kinetic-type renders + the 2x2 four-voices grid
python tools/render_captions.py --results results.json --clips clips/ --grid
```

## Architecture

```
clip -> ffmpeg frame sampling (timestamped, whole clip)
     -> Gemma 4 vision: scene facts JSON  (retry + refuse-to-caption-blind)
     -> 4 tone contracts + few-shot        -> 4 captions      -> results.json
     -> time-segmented beats               -> 4 CC tracks     -> .srt/.ass/.mp4
     -> beats + two live model personas    -> The Hecklers    -> .mp4
```

Reliability at judging time: the primary path is the Gemma 4 dedicated
deployment (`REASONING_EFFORT=none` — it emits a thought preamble
otherwise). If the deployment is cold or unreachable under the grader's
key, `main.py` cuts over per-task to serverless models
(`qwen3p7-plus` vision + `gpt-oss-120b` captions) so no task scores zero.
Clips run 4-at-a-time; 3 official clips complete in ~30s warm — far
inside the 10-minute harness budget.

## Repo map

| Path | What it is |
|---|---|
| `main.py` | graded entry: `/input/tasks.json` → `/output/results.json` |
| `run.py` | CLI: folder/clip → captions.json (`--mock` for offline) |
| `captioner/` | pipeline: frames, vision grounding, styles, judge, client |
| `tools/textsink_cc.py` | styled closed-caption tracks (the product) |
| `tools/hecklers.py` | two models argue about the video |
| `tools/render_captions.py` | kinetic-type caption burner + 2x2 grid |
| `tools/build_dataset.py` | Gemma-teaches-Gemma SFT dataset generator |
| `eval/run_eval.py` | self-eval: accuracy + tone via LLM judge |

MIT licensed. Built with Gemma 4 on Fireworks AI for the AMD Developer
Hackathon: ACT II.
