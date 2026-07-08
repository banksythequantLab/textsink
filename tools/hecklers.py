#!/usr/bin/env python3
"""The Hecklers - two competing models argue about the video like old men.

STAN (Gemma 4, the one who actually watched it): grumpy, seen-it-all,
complains, starts every topic, suspicious of modern everything.
GUS (gpt-oss-120b, the know-it-all): corrects Stan, condescending,
one-ups with suspiciously precise facts, escalates the bickering.

Turn-by-turn generation: each model writes its own lines, sees the
running argument, and responds - a real two-model dialogue, not a script.

Usage:
  python tools/hecklers.py --clip <video> [--out heckle_out] [--burn]
                           [--spice eleven]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from captioner.config import Config                     # noqa: E402
from captioner.fireworks_client import FireworksClient  # noqa: E402
from tools.textsink_cc import get_beats                 # noqa: E402

GUS_MODEL = "accounts/fireworks/models/gpt-oss-120b"

SPICE = {
    "mild": "Keep it gently amusing.",
    "hot": "Be sharp and funny. Swing at every beat.",
    "eleven": ("Turn it up to 11. Mock-epic stakes, wild exaggeration, "
               "absurd metaphors, petty personal grudges, callbacks to "
               "earlier gripes. NEVER invent things on screen - but your "
               "emotional reaction to them may be catastrophically "
               "disproportionate."),
}

RULES_A = (
    "\n{spice}\nYou will receive: what's happening on screen (a beat) and "
    "the argument so far. Reply with ONE quick quip, max 10 words, no name "
    "prefix, no quotes. React to the beat and/or take a shot at your rival."
)
RULES_B = (
    "\n{spice}\nYou will receive: what's happening on screen (a beat) and "
    "the argument so far, ending with your rival's latest remark. Reply "
    "with ONE quick quip, max 10 words, no name prefix, no quotes. Correct "
    "or one-up them, staying true to what's actually on screen."
)

PERSONAS = {
    # flavor: (name_a, persona_a, name_b, persona_b)
    "sarcastic": (
        "STAN",
        "You are STAN, a grumpy old man heckling a video from the balcony. "
        "You've seen everything, hate most of it, and start every topic. "
        "Suspicious of modern nonsense. You bicker with your friend GUS, "
        "who thinks he knows everything." + RULES_A,
        "GUS",
        "You are GUS, a know-it-all old man heckling a video from the "
        "balcony with your friend STAN. You correct people, cite "
        "suspiciously precise facts, and always one-up. You find STAN's "
        "takes exhausting and say so." + RULES_B,
    ),
    "humorous_tech": (
        "LINT",
        "You are LINT, a pedantic senior engineer code-reviewing a VIDEO "
        "as if it were a pull request. Everything on screen is a code "
        "smell, an anti-pattern, or a missing test. Your rival VIBE ships "
        "garbage and you know it." + RULES_A,
        "VIBE",
        "You are VIBE, a chaotic vibe-coder watching a video with LINT, "
        "your uptight reviewer. Everything on screen is actually a "
        "brilliant feature, a growth hack, or 'basically agile'. LINT "
        "needs to touch grass and you tell them so." + RULES_B,
    ),
    "humorous_non_tech": (
        "DORIS",
        "You are DORIS, a warm but nosy neighbor watching a video over "
        "the fence with PEARL. Everything reminds you of someone you "
        "know, and you narrate like it's neighborhood gossip. PEARL "
        "always gets the details wrong, bless her." + RULES_A,
        "PEARL",
        "You are PEARL, DORIS's neighbor, watching the same video. You "
        "one-up every story, correct DORIS with your own version, and "
        "relate everything to your prize-winning casserole, garden, or "
        "grandkids." + RULES_B,
    ),
}


def _line(client, model, system, beat, convo, reasoning):
    hist = "\n".join(f"{who}: {txt}" for who, txt in convo[-8:]) or "(start)"
    user = (f"ON SCREEN NOW: {beat['what']}\n\nTHE ARGUMENT SO FAR:\n{hist}\n\n"
            f"Your line:")
    txt = client.chat(model=model, messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], temperature=1.0, max_tokens=400, reasoning_effort=reasoning)
    txt = (txt or "").strip().strip('"').strip()
    # keep it one line
    return txt.splitlines()[0][:120] if txt else "..."


def argue(client, cfg, beats, spice, flavor="sarcastic"):
    name_a, sys_a, name_b, sys_b = PERSONAS[flavor]
    stan_sys = sys_a.format(spice=SPICE[spice])
    gus_sys = sys_b.format(spice=SPICE[spice])
    convo, timed = [], []
    cursor, turn, bi = 0.0, 0, 0
    total_end = float(beats[-1]["end"])
    MIN_LINE = 1.8   # quick TV-comedy pacing
    MAX_LINE = 3.2
    while cursor < total_end - 0.8:
        while (bi < len(beats) - 1
               and float(beats[bi]["end"]) <= cursor):
            bi += 1
        beat = beats[bi]
        if turn % 2 == 0:
            who, model, sysmsg, reff = (name_a, cfg.caption_model, stan_sys,
                                        cfg.reasoning_effort)
        else:
            who, model, sysmsg, reff = name_b, GUS_MODEL, gus_sys, "low"
        txt = _line(client, model, sysmsg, beat, convo, reff)
        convo.append((who, txt))
        dur = min(max(MIN_LINE, len(txt) * 0.055), MAX_LINE)
        e = min(cursor + dur, total_end)
        timed.append({"start": round(cursor, 2), "end": round(e, 2),
                      "who": who, "text": txt})
        cursor, turn = e, turn + 1
    return timed


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: VoiceA,Trebuchet MS,44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,4,3,0,1,60,60,44,1
Style: VoiceB,Trebuchet MS,44,&H0007C1FF,&H0007C1FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,4,3,0,3,60,60,44,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ts(sec: float) -> str:
    h = int(sec // 3600); m = int(sec % 3600 // 60); s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def write_ass(timed, out_path):
    ass = ASS_HEAD
    first = timed[0]["who"] if timed else ""
    for ln in timed:
        who = ln["who"]
        style = "VoiceA" if who == first else "VoiceB"
        tag = f"{{\\b1}}{who}:{{\\b0}} "
        ass += (f"Dialogue: 0,{_ts(ln['start'])},{_ts(ln['end'])},{style},,"
                f"0,0,0,,{{\\fad(100,100)}}{tag}{ln['text']}\n")
    with open(out_path, "w", encoding="utf-8-sig") as fh:
        fh.write(ass)


def burn(clip, ass_path, out_path):
    ass_ff = ass_path.replace("\\", "/").replace(":", "\\:")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", clip,
         "-vf", f"scale=-2:720,ass='{ass_ff}'",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-movflags", "+faststart", out_path], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="The Hecklers")
    ap.add_argument("--clip", required=True)
    ap.add_argument("--out", default="heckle_out")
    ap.add_argument("--burn", action="store_true")
    ap.add_argument("--spice", default="eleven",
                    choices=list(SPICE.keys()))
    ap.add_argument("--flavor", default="sarcastic",
                    choices=list(PERSONAS.keys()))
    args = ap.parse_args()

    cfg = Config.from_env()
    client = FireworksClient(cfg.api_key, cfg.base_url, cfg.request_timeout)
    os.makedirs(args.out, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.clip))[0]

    print(f"[hecklers] segmenting {base} ...", file=sys.stderr)
    beats, dur = get_beats(client, cfg, args.clip)
    print(f"[hecklers] {len(beats)} beats; the argument begins "
          f"(flavor={args.flavor}, spice={args.spice}) ...", file=sys.stderr)
    timed = argue(client, cfg, beats, args.spice, args.flavor)
    for ln in timed:
        print(f"  [{ln['start']:.1f}s] {ln['who']}: {ln['text']}",
              file=sys.stderr)

    name_a, _, name_b, _ = PERSONAS[args.flavor]
    suffix = f"hecklers_{args.flavor}"
    with open(os.path.join(args.out, f"{base}_{suffix}.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"clip": os.path.basename(args.clip), "beats": beats,
                   "dialogue": timed, "spice": args.spice,
                   "flavor": args.flavor,
                   "models": {name_a: cfg.caption_model, name_b: GUS_MODEL}},
                  fh, indent=2, ensure_ascii=False)
    ass_p = os.path.join(args.out, f"{base}_{suffix}.ass")
    write_ass(timed, ass_p)
    if args.burn:
        print("[hecklers] burning ...", file=sys.stderr)
        burn(args.clip, ass_p,
             os.path.join(args.out, f"{base}_{suffix}.mp4"))
    print(f"[hecklers] done -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
