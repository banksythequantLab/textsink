#!/usr/bin/env python3
"""Assemble the rough-cut demo: numbered assets + cloned-voice narration."""
import os
import subprocess

KIT = os.path.dirname(os.path.abspath(__file__))
os.chdir(KIT)


def dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def run(args):
    r = subprocess.run(["ffmpeg", "-y", "-v", "error"] + args,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-500:])


VF = ("scale=1920:1080:force_original_aspect_ratio=decrease,"
      "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p")


def seg_video(src, vo, out, lead=0.3):
    d = dur(vo) + lead + 0.4
    run(["-i", src, "-i", vo,
         "-filter_complex",
         f"[0:v]{VF},tpad=stop_mode=clone:stop_duration=120[v];"
         f"[1:a]adelay={int(lead*1000)}|{int(lead*1000)},"
         f"aresample=48000,apad[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-ar", "48000", out])


def seg_still(img, vo, out, lead=0.3):
    d = dur(vo) + lead + 0.4
    run(["-loop", "1", "-i", img, "-i", vo,
         "-filter_complex",
         f"[0:v]{VF}[v];[1:a]adelay={int(lead*1000)}|{int(lead*1000)},"
         f"aresample=48000,apad[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-ar", "48000", out])


TERM_LINES = [
    r"PS B:\amd-track2-captioner> python -u main.py",
    "[main] 3 task(s); budget 540s; workers 4",
    "[main] probe: Gemma deployment reachable - all-Gemma run",
    "[captioner] grounding clip v1 ... scene facts OK",
    "[captioner] drafting 3 candidates x 4 styles ... judging ...",
    "[main] 1/3 done (34s elapsed)",
    "[main] 2/3 done (61s elapsed)",
    "[main] v3: empty grounding -> refusing to caption blind, retrying",
    "[main] 3/3 done (100s elapsed)",
    "[main] wrote 3 result(s) -> /output/results.json",
]

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: T,Consolas,34,&H0050FF96,&H0050FF96,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,80,80,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ts(sec):
    m = int(sec // 60); s = sec % 60
    return f"0:{m:02d}:{s:05.2f}"


def seg_terminal(vo, out, lead=0.3):
    d = dur(vo) + lead + 0.4
    step = (d - 1.5) / len(TERM_LINES)
    ass = ASS_HEAD
    shown = []
    for i, line in enumerate(TERM_LINES):
        shown.append(line.replace("{", "(").replace("}", ")"))
        start = 0.4 + i * step
        end = 0.4 + (i + 1) * step if i < len(TERM_LINES) - 1 else d
        text = "\\N".join(shown)
        ass += f"Dialogue: 0,{_ts(start)},{_ts(end)},T,,0,0,0,,{text}\n"
    open("term.ass", "w", encoding="utf-8-sig").write(ass)
    ass_ff = os.path.join(KIT, "term.ass").replace("\\", "/").replace(":", "\\:")
    run(["-f", "lavfi", "-i", f"color=c=0x0D1119:s=1920x1080:r=30:d={d:.2f}",
         "-i", vo,
         "-filter_complex",
         f"[0:v]ass='{ass_ff}',format=yuv420p[v];"
         f"[1:a]adelay={int(lead*1000)}|{int(lead*1000)},"
         f"aresample=48000,apad[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-ar", "48000", out])


def seg_two_videos(src1, t1, src2, vo, out, lead=0.3):
    """Segment 5: ocean clip for t1 seconds, then doris/pearl for the rest."""
    d = dur(vo) + lead + 0.4
    run(["-i", src1, "-i", src2, "-i", vo,
         "-filter_complex",
         f"[0:v]trim=0:{t1},setpts=PTS-STARTPTS,{VF}[v0];"
         f"[1:v]{VF},tpad=stop_mode=clone:stop_duration=120[v1];"
         f"[v0][v1]concat=n=2:v=1:a=0[v];"
         f"[2:a]adelay={int(lead*1000)}|{int(lead*1000)},"
         f"aresample=48000,apad[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-ar", "48000", out])


print("[cut] building segments ...", flush=True)
seg_video("01_fourvoices_grid.mp4", "vo_1.wav", "seg1.mp4")
print("[cut] seg1 ok", flush=True)
seg_terminal("vo_2.wav", "seg2.mp4")
print("[cut] seg2 ok", flush=True)
seg_still("02_captions_slide.jpg", "vo_3.wav", "seg3.mp4")
print("[cut] seg3 ok", flush=True)
seg_video("03_cc_sarcastic_kitten.mp4", "vo_4.wav", "seg4.mp4")
print("[cut] seg4 ok", flush=True)
seg_two_videos("04_hecklers_ocean_stan_gus.mp4", 20,
               "05_hecklers_kitten_doris_pearl.mp4", "vo_5.wav", "seg5.mp4")
print("[cut] seg5 ok", flush=True)
seg_still("07_close_slide.jpg", "vo_6.wav", "seg6.mp4")
print("[cut] seg6 ok", flush=True)

with open("concat.txt", "w") as fh:
    for i in range(1, 7):
        fh.write(f"file 'seg{i}.mp4'\n")
run(["-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy",
     "TextSink_demo_roughcut.mp4"])
total = dur("TextSink_demo_roughcut.mp4")
print(f"[cut] DONE: TextSink_demo_roughcut.mp4 ({total:.0f}s)", flush=True)
