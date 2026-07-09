#!/usr/bin/env python3
"""Generate demo narration in Derek's cloned voice via FreeClone/VoxCPM2."""
import sys

import requests

BASE = "http://johnson:8300"
REF = r"B:\freeclone-backend\derek-voice.wav"
OUT = r"B:\amd-track2-captioner\demo_kit"

SEGMENTS = {
    1: ("One video. Four voices. A formal narrator, a deadpan cynic, a "
        "developer who's seen things, and your favorite neighbor. This is "
        "TextSink. And every word you're seeing was written live by Gemma "
        "four, about the actual competition clips."),
    2: ("Under the hood, it's the official Track two contract. Tasks in, "
        "captions out, fully containerized. The container probes its model "
        "access, grounds every clip in scene facts, drafts three captions "
        "per style, judges its own drafts, and ships the winner. And if "
        "grounding ever comes back empty, it refuses to caption blind. An "
        "empty caption is structurally impossible."),
    3: ("Four styles isn't one prompt with four adjectives. Broadcast "
        "precision. Deadpan, scale mismatch irony. A developer culture "
        "metaphor built from what's actually on screen. And warm, everyday "
        "relatability. An AI judge can blind sort these. That's the tone "
        "score."),
    4: ("Then we kept going. The same grounding becomes real closed "
        "captions. A timed subtitle track you can toggle, with one "
        "consistent voice across the whole clip. A tiny orange predator "
        "prepares for total world domination. The menace is closing in. "
        "Send help."),
    5: ("And because one voice is a monologue: The Hecklers. Two different "
        "models, Gemma four versus GPT oh ess ess, watch the clip and argue "
        "about it, turn by turn. Every line generated live. The deep blue "
        "menace is swallowing the very earth! Only you think foam is world "
        "ending, Stan. Three duos: grumpy old men, a code reviewer versus a "
        "vibe coder, and two neighbors who think your kitten looks like a "
        "lying ex husband."),
    6: ("Gemma grounds it. Writes it. Argues it. Judges it. And last night, "
        "it trained its own captioner on the drafts it judged best. "
        "TextSink. Four voices. One truth."),
}

for i, text in SEGMENTS.items():
    print(f"[vo] segment {i} ({len(text)} chars) ...", flush=True)
    with open(REF, "rb") as f:
        r = requests.post(f"{BASE}/api/clone",
                          files={"prompt_audio": ("ref.wav", f, "audio/wav")},
                          data={"text": text, "lang": "en"}, timeout=900)
    if r.status_code != 200 or len(r.content) < 2000:
        print(f"[vo] FAILED seg {i}: {r.status_code} {r.text[:200]}",
              flush=True)
        sys.exit(1)
    out = rf"{OUT}\vo_{i}.wav"
    open(out, "wb").write(r.content)
    print(f"[vo] wrote vo_{i}.wav ({len(r.content)//1024} KB)", flush=True)
print("[vo] ALL DONE", flush=True)
