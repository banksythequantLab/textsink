# TextSink — Demo / Video Presentation Script (2:45)

**Format:** screen recording + voiceover. Target 2m30s–2m50s. Record at 1080p.
**Tone:** confident, fast, technical-but-clear. No filler.

> Tip: record the terminal run first (Section 4) so the on-screen captions are
> real. Everything else can be recorded around it.

---

### 0:00–0:15 · Hook  *(talking head or title card)*

**VO:** "Give ten AI captioners the same clip and you get ten captions that are
either accurate but boring, or funny but wrong. Track 2 asks for four *different*
styles on the same clip — formal, sarcastic, tech-humor, and everyday-humor —
and it scores you on both accuracy *and* tone. That's the hard part. Meet
TextSink."

**On screen:** cover slide — "TextSink: four voices, one truth."

---

### 0:15–0:35 · What it is

**VO:** "TextSink is a containerized agent for AMD's ACT II hackathon. Drop in a
clip, get back four captions — each faithful to what actually happens, each in a
distinct voice. It runs on Gemma, served on AMD hardware through Fireworks AI."

**On screen:** one clip thumbnail → four caption cards fanning out, each labeled
with its style.

---

### 0:35–1:15 · How it works  *(architecture animation)*

**VO:** "The trick is separating the two things the judge scores. First,
accuracy. We sample frames with ffmpeg, pull the audio into a transcript, and
ask Gemma to extract only the *facts* — setting, subjects, actions, on-screen
text — as structured JSON. Nothing invented. Then, tone. Each style has its own
tone contract and few-shot examples, and every caption is locked to those facts.
So the humor never drifts from the truth."

**On screen:** the pipeline diagram animating left→right:
`clip → frames + audio → Gemma scene JSON → 4 tone-contract prompts → captions`.
Highlight "grounding = accuracy" and "tone contracts = tone" as two lanes.

---

### 1:15–2:00 · Live demo  *(terminal + output)*

**VO:** "Here it is on a real clip. One command. The agent samples frames,
grounds the scene, and writes all four styles."

**On screen — type and run:**
```
python run.py --input demo/clip01.mp4 --output captions.json
```
Then open `captions.json` and read the four captions aloud, briefly:

**VO:** "Formal — states what happens. Sarcastic — dry, not mean. Tech-humor —
a joke a developer gets. Everyday-humor — no jargon, lands for anyone. Same
facts, four voices."

**On screen:** highlight that all four reference the *same* grounded action.

---

### 2:00–2:30 · Why Gemma + AMD  *(and the eval loop)*

**VO:** "Gemma does both jobs — the visual grounding and the styled captions —
running on AMD Instinct through Fireworks. And because tone is subjective, we
ship a self-judge: it scores every caption on accuracy and tone so we tune the
prompts with data, not vibes. The whole thing is one Docker container — clone,
build, run."

**On screen:** `docker run ...` line, then the eval harness printing
`accuracy / tone` averages per style.

---

### 2:30–2:45 · Close

**VO:** "TextSink: accurate where it counts, funny where it's allowed, and
Gemma-powered end to end. Four voices, one truth. Thanks for watching."

**On screen:** cover slide + repo URL + "AMD Developer Hackathon: ACT II · Track 2".

---

## Shot list / b-roll checklist

- [ ] Cover title card (from `cover.png`)
- [ ] Clip-to-four-captions animation (can be a slide build)
- [ ] Architecture diagram (slide 4 of the deck works)
- [ ] Terminal run of `run.py` producing real `captions.json`
- [ ] Scroll of `captions.json` with the four styles
- [ ] `docker run` line + eval harness averages
- [ ] Repo URL end card

## Recording notes

- Keep the terminal font large (18pt+) and the theme high-contrast.
- Pre-stage `demo/clip01.mp4` and a valid `FIREWORKS_API_KEY` before recording.
- If a live API call is slow on camera, pre-generate `captions.json` and just
  show the file — never fake the command, show the real output.
