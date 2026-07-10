#!/usr/bin/env python3
"""Build YouTube captions (.srt) for TextSink_demo_final.mp4 from the
known narration texts + measured segment/VO durations."""
import os
import re
import subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def dur(p):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", p],
        capture_output=True, text=True).stdout.strip()
    return float(out or 0)


TEXTS = {
    "open": ("TextSink. Four voices. One truth. Built on Gemma 4 and "
             "Fireworks AI, for the AMD Developer Hackathon."),
    1: ("One video. Four voices. A formal narrator, a deadpan cynic, a "
        "developer who's seen things, and your favorite neighbor. This is "
        "TextSink. And every word you're seeing was written live by Gemma "
        "4, about the actual competition clips."),
    2: ("Under the hood, it's the official Track 2 contract. Tasks in, "
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
        "models, Gemma 4 versus GPT-OSS, watch the clip and argue about "
        "it, turn by turn. Every line generated live. It's a strawberry "
        "milkshake apocalypse, Gus! Apocalypse? It's just sunset, not your "
        "dairy fantasy. And when the code reviewer meets the vibe coder: "
        "touch grass, Lint, before your soul segfaults. The models wrote "
        "every word."),
    6: ("Gemma grounds it. Writes it. Argues it. Judges it. And last "
        "night, it trained its own captioner on the drafts it judged best. "
        "TextSink. Four voices. One truth."),
    "end": ("TextSink. Thanks to AMD, Fireworks AI, Google DeepMind's "
            "Gemma, and lablab.ai. Find us on GitHub."),
}

# film layout: [seg0_card] [seg1..seg6] [seg7_card]
order = [("open", "seg0_card.mp4", "vo_open.wav", 0.5),
         (1, "seg1.mp4", "vo_1.wav", 0.3),
         (2, "seg2.mp4", "vo_2.wav", 0.3),
         (3, "seg3.mp4", "vo_3.wav", 0.3),
         (4, "seg4.mp4", "vo_4.wav", 0.3),
         (5, "seg5.mp4", "vo_5.wav", 0.3),
         (6, "seg6.mp4", "vo_6.wav", 0.3),
         ("end", "seg7_card.mp4", "vo_end.wav", 0.6)]


def chunks(text, max_words=9):
    words = text.split()
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= max_words or (len(cur) >= 5 and w[-1] in ".!?"):
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def ts(sec):
    h = int(sec // 3600); m = int(sec % 3600 // 60)
    s = int(sec % 60); ms = int((sec % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


srt, n, offset = [], 0, 0.0
for key, seg, vo, lead in order:
    seg_d, vo_d = dur(seg), dur(vo)
    text = TEXTS[key]
    parts = chunks(text)
    total_chars = sum(len(p) for p in parts)
    t = offset + lead
    for p in parts:
        d = vo_d * len(p) / total_chars
        n += 1
        srt.append(f"{n}\n{ts(t)} --> {ts(min(t + d, offset + seg_d))}\n{p}\n")
        t += d
    offset += seg_d

open("TextSink_demo_final.srt", "w", encoding="utf-8").write("\n".join(srt))
print(f"SRT written: {n} captions over {offset:.1f}s")
