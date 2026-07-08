"""Frame sampling and audio extraction via ffmpeg/ffprobe.

Pure local processing, no network. Exercised end-to-end by
scripts/make_test_clip.sh + the sandbox tests.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass


class FfmpegError(RuntimeError):
    pass


def _require(bin_name: str) -> str:
    path = shutil.which(bin_name)
    if not path:
        raise FfmpegError(f"'{bin_name}' not found on PATH. Install ffmpeg.")
    return path


def probe_duration(video_path: str) -> float:
    ffprobe = _require("ffprobe")
    cmd = [ffprobe, "-v", "error", "-show_entries", "format=duration",
           "-of", "json", video_path]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise FfmpegError(out.stderr.strip())
    try:
        return float(json.loads(out.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return 0.0


def _n_frames(duration: float, fps_sample: float, lo: int, hi: int) -> int:
    n = int(round(duration * fps_sample)) if duration > 0 else lo
    return max(lo, min(hi, n))


@dataclass
class SampledClip:
    frames: list          # list[bytes] of JPEG-encoded frames
    duration: float
    frame_count: int


def sample_frames(video_path: str, fps_sample: float = 0.2, min_frames: int = 8,
                  max_frames: int = 16, width: int = 512) -> SampledClip:
    """Sample up to `max_frames` JPEG frames evenly across the clip."""
    ffmpeg = _require("ffmpeg")
    if not os.path.exists(video_path):
        raise FfmpegError(f"missing video: {video_path}")
    duration = probe_duration(video_path)
    n = _n_frames(duration, fps_sample, min_frames, max_frames)

    with tempfile.TemporaryDirectory() as td:
        # Even sampling: N frames across the whole clip. Derive an fps that
        # yields ~N frames when the duration is known; else use fps_sample.
        rate = (n / duration) if duration > 0 else fps_sample
        vf = f"fps={rate:.6f},scale={width}:-2"
        pattern = os.path.join(td, "f_%04d.jpg")
        cmd = [ffmpeg, "-y", "-i", video_path, "-vf", vf,
               "-frames:v", str(n), "-q:v", "3", pattern]
        out = subprocess.run(cmd, capture_output=True, text=True)
        if out.returncode != 0:
            raise FfmpegError(out.stderr.strip()[:500])
        frames = []
        for fn in sorted(os.listdir(td)):
            if fn.endswith(".jpg"):
                with open(os.path.join(td, fn), "rb") as fh:
                    frames.append(fh.read())
    return SampledClip(frames=frames, duration=duration, frame_count=len(frames))


def extract_audio(video_path: str, out_path: str, seconds: int = 120):
    """Extract mono 16 kHz opus/ogg audio. Returns path, or None if no audio.

    ffmpeg recipe per https://docs.fireworks.ai/guides/video-audio-inputs
    """
    ffmpeg = _require("ffmpeg")
    cmd = [ffmpeg, "-y", "-i", video_path, "-t", str(seconds), "-vn",
           "-c:a", "libopus", "-b:a", "24k", "-ar", "16000", "-ac", "1", out_path]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if (out.returncode != 0 or not os.path.exists(out_path)
            or os.path.getsize(out_path) == 0):
        return None
    return out_path
