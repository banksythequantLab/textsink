"""End-to-end orchestration: one video clip -> four styled captions."""
from __future__ import annotations

import os
import tempfile

from . import frames as F
from . import styles as S
from . import vision as V
from .config import Config
from .schema import STYLES, ClipResult
from .transcribe import transcribe


def process_clip(path: str, client, cfg: Config) -> ClipResult:
    sampled = F.sample_frames(path, cfg.fps_sample, cfg.min_frames,
                              cfg.max_frames, cfg.frame_width)
    with tempfile.TemporaryDirectory() as td:
        audio = F.extract_audio(path, os.path.join(td, "a.ogg"), cfg.audio_seconds)
        transcript = transcribe(audio, cfg.transcribe_backend, cfg.whisper_model,
                                client=client)
    scene = _grounded_scene(client, cfg, sampled.frames, transcript)
    scene_text = V.scene_to_text(scene)
    captions = {}
    for style in STYLES:
        msgs = S.build_messages(style, scene_text, transcript)
        cap = client.chat(model=cfg.caption_model, messages=msgs,
                          temperature=cfg.temperature, max_tokens=cfg.max_tokens,
                          reasoning_effort=cfg.reasoning_effort)
        captions[style] = _clean(cap)
    return ClipResult(
        clip=os.path.basename(path),
        duration_sec=round(sampled.duration, 2),
        frames=sampled.frame_count,
        transcript=transcript,
        scene=scene,
        captions=captions,
        meta={"vision_model": cfg.vision_model, "caption_model": cfg.caption_model,
              "transcribe_backend": cfg.transcribe_backend},
    ).validate()


def _grounded_scene(client, cfg: Config, frames, transcript) -> dict:
    """Vision grounding with a validity gate: an empty scene never reaches the
    caption stage. Retries with varied temperature; hard-fails after 3 tries so
    we never publish captions about a clip the model didn't actually see."""
    last: dict = {}
    for attempt, temp in enumerate((0.2, 0.5, 0.8), start=1):
        scene = V.describe_scene(client, cfg.vision_model, frames, transcript,
                                 temperature=temp,
                                 max_tokens=cfg.scene_max_tokens,
                                 reasoning_effort=cfg.reasoning_effort)
        if scene.get("subjects") or scene.get("actions"):
            return scene
        last = scene
        print(f"[captioner] scene empty (attempt {attempt}/3), retrying ...")
    raise RuntimeError(
        "vision grounding returned an empty scene 3x - refusing to caption blind")


def _clean(text: str) -> str:
    t = (text or "").strip()
    for pre in ("CAPTION:", "Caption:", "caption:"):
        if t.startswith(pre):
            t = t[len(pre):].strip()
    if len(t) >= 2 and t[0] in "\"'" and t[-1] in "\"'":
        t = t[1:-1].strip()
    return t
