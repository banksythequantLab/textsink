"""End-to-end orchestration: one video clip -> four styled captions."""
from __future__ import annotations

import os
import tempfile
import time

from . import frames as F
from . import styles as S
from . import vision as V
from .config import Config
from .schema import STYLES, ClipResult
from .transcribe import transcribe


def _best_caption(client, cfg: Config, style: str, scene_text: str,
                  transcript: str, n: int) -> str:
    """Best-of-N: draft N candidates at high temp, self-judge on
    accuracy + tone (same model - stays all-Gemma), ship the winner."""
    from .judge import judge_caption
    spec = S.STYLE_SPECS[style]
    drafts: list[str] = []
    for k in range(max(n, 1)):
        temp = cfg.temperature if k == 0 else (0.6 if style == "formal"
                                               else 0.95)
        msgs = S.build_messages(style, scene_text, transcript)
        cap = _clean(client.chat(model=cfg.caption_model, messages=msgs,
                                 temperature=temp, max_tokens=cfg.max_tokens,
                                 reasoning_effort=cfg.reasoning_effort))
        if cap and not _is_refusal(cap) and cap not in drafts:
            drafts.append(cap)
    if not drafts:
        # all drafts were refusals/empty -> hard-fail this clip so the
        # task-level ladder regenerates it with fresh grounding
        raise RuntimeError(f"no usable draft for style {style}")
    if len(drafts) == 1:
        return drafts[0]
    best, best_key = drafts[0], (-1, -1)
    for d in drafts:
        s = judge_caption(client, cfg.caption_model, spec["label"],
                          spec["contract"], scene_text, transcript, d,
                          reasoning_effort=cfg.reasoning_effort)
        key = (int(s.get("accuracy", 0)), int(s.get("tone", 0)))
        if key > best_key:
            best, best_key = d, key
    return best


def process_clip(path: str, client, cfg: Config,
                 deadline: float | None = None) -> ClipResult:
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
        # degrade to single-shot when the harness clock is running low
        n = cfg.best_of
        if deadline is not None and time.time() > deadline - 150:
            n = 1
        captions[style] = _best_caption(client, cfg, style, scene_text,
                                        transcript, n)
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
        text = V.scene_to_text(scene)
        looks_sane = (len(text) >= 30 and "{" not in text
                      and (scene.get("subjects") or scene.get("actions")))
        if looks_sane:
            return scene
        last = scene
        print(f"[captioner] scene empty (attempt {attempt}/3), retrying ...")
    raise RuntimeError(
        "vision grounding returned an empty scene 3x - refusing to caption blind")


_REFUSAL_MARKERS = ("i cannot fulfill", "cannot fulfill this",
                    "i can't fulfill", "i am unable", "i'm unable",
                    "as an ai", "no scene facts", "please provide")


def _is_refusal(text: str) -> bool:
    t = (text or "").lower()
    return any(m in t for m in _REFUSAL_MARKERS)


def _clean(text: str) -> str:
    t = (text or "").strip()
    for pre in ("CAPTION:", "Caption:", "caption:"):
        if t.startswith(pre):
            t = t[len(pre):].strip()
    if len(t) >= 2 and t[0] in "\"'" and t[-1] in "\"'":
        t = t[1:-1].strip()
    return t
