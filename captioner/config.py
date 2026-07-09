"""Central configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _load_dotenv(path: str = ".env") -> None:
    """Load KEY=VALUE lines from a .env file into os.environ (no override)."""
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))



@dataclass
class Config:
    api_key: str = ""
    base_url: str = "https://api.fireworks.ai/inference/v1"
    # Gemma 4 (26B MoE) does BOTH vision grounding and the 4 captions =
    # maximal "Best Use of Gemma 4". Needs an on-demand deployment (see README);
    # then set the model to accounts/fireworks/models/gemma-4-26b-a4b-it#<deployment>.
    vision_model: str = "accounts/fireworks/models/gemma-4-26b-a4b-it"
    # Serverless fallback (no deployment): VISION=qwen3p7-plus,
    # CAPTION=gpt-oss-120b, REASONING_EFFORT=low.
    caption_model: str = "accounts/fireworks/models/gemma-4-26b-a4b-it"
    judge_model: str = "accounts/fireworks/models/gpt-oss-120b"

    fps_sample: float = 0.2
    min_frames: int = 8
    max_frames: int = 16
    frame_width: int = 512

    transcribe_backend: str = "none"   # none | local | fireworks
    whisper_model: str = "base"
    audio_seconds: int = 120

    temperature: float = 0.4
    max_tokens: int = 320
    scene_max_tokens: int = 3000
    reasoning_effort: str = "none"
    request_timeout: int = 120
    best_of: int = 3

    @classmethod
    def from_env(cls) -> "Config":
        _load_dotenv()
        c = cls()
        c.api_key = _get("FIREWORKS_API_KEY", c.api_key)
        c.base_url = _get("FIREWORKS_BASE_URL", c.base_url)
        c.vision_model = _get("VISION_MODEL", c.vision_model)
        c.caption_model = _get("CAPTION_MODEL", c.caption_model)
        c.judge_model = _get("JUDGE_MODEL", c.judge_model)
        c.transcribe_backend = _get("TRANSCRIBE_BACKEND", c.transcribe_backend)
        c.whisper_model = _get("WHISPER_MODEL", c.whisper_model)
        c.fps_sample = float(_get("FPS_SAMPLE", str(c.fps_sample)))
        c.min_frames = int(_get("MIN_FRAMES", str(c.min_frames)))
        c.max_frames = int(_get("MAX_FRAMES", str(c.max_frames)))
        c.frame_width = int(_get("FRAME_WIDTH", str(c.frame_width)))
        c.temperature = float(_get("TEMPERATURE", str(c.temperature)))
        c.max_tokens = int(_get("MAX_TOKENS", str(c.max_tokens)))
        c.scene_max_tokens = int(_get("SCENE_MAX_TOKENS", str(c.scene_max_tokens)))
        c.reasoning_effort = _get("REASONING_EFFORT", c.reasoning_effort)
        c.best_of = int(_get("BEST_OF", str(c.best_of)))
        return c
