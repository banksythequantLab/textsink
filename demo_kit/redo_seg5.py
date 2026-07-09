#!/usr/bin/env python3
"""Recast demo segment 5: sunset STAN & GUS + LINT vs VIBE. DORIS is out."""
import os
import subprocess

import requests

KIT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(KIT)
os.chdir(KIT)

VO5 = ("And because one voice is a monologue: The Hecklers. Two different "
       "models, Gemma four versus GPT oh ess ess, watch the clip and argue "
       "about it, turn by turn. Every line generated live. It's a "
       "strawberry milkshake apocalypse, Gus! Apocalypse? It's just sunset, "
       "not your dairy fantasy. And when the code reviewer meets the vibe "
       "coder: touch grass, Lint, before your soul segfaults. The models "
       "wrote every word.")

print("[seg5] generating VO ...", flush=True)
with open(r"B:\freeclone-backend\derek-voice.wav", "rb") as f:
    r = requests.post("http://johnson:8300/api/clone",
                      files={"prompt_audio": ("ref.wav", f, "audio/wav")},
                      data={"text": VO5, "lang": "en"}, timeout=900)
assert r.status_code == 200 and len(r.content) > 2000, r.text[:300]
open("vo_5.wav", "wb").write(r.content)
print(f"[seg5] vo_5.wav ({len(r.content)//1024} KB)", flush=True)


def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration", "-of",
                          "default=noprint_wrappers=1:nokey=1", p],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


d = dur("vo_5.wav") + 0.7
sarc = os.path.join(ROOT, "heckle_out",
                    "12471596-uhd_2560_1440_30fps_hecklers_sarcastic.mp4")
tech = os.path.join(ROOT, "heckle_out",
                    "12471596-uhd_2560_1440_30fps_hecklers_humorous_tech.mp4")
VF = ("scale=1920:1080:force_original_aspect_ratio=decrease,"
      "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p")

print(f"[seg5] building ({d:.1f}s) ...", flush=True)
r = subprocess.run(
    ["ffmpeg", "-y", "-v", "error",
     "-ss", "39.8", "-t", "10.9", "-i", sarc,
     "-ss", "27.3", "-t", "6.8", "-i", tech,
     "-i", "vo_5.wav",
     "-filter_complex",
     f"[0:v]{VF}[v0];[1:v]{VF},tpad=stop_mode=clone:stop_duration=120[v1];"
     f"[v0][v1]concat=n=2:v=1:a=0[v];"
     f"[2:a]adelay=300|300,aresample=48000,apad[a]",
     "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
     "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
     "-c:a", "aac", "-ar", "48000", "seg5.mp4"], capture_output=True,
    text=True)
if r.returncode != 0:
    raise SystemExit(r.stderr[-400:])
print("[seg5] rebuilt", flush=True)

subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                "-i", "concat.txt", "-c", "copy",
                "TextSink_demo_roughcut_v2.mp4"], check=True)
print(f"[seg5] rough cut v2: {dur('TextSink_demo_roughcut_v2.mp4'):.0f}s",
      flush=True)
