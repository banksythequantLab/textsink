"""Audio transcription with pluggable backends.

- none:      skip audio (captions rely on frames only). DEFAULT.
- local:     faster-whisper (offline). Requires `pip install faster-whisper`
             and a one-time model download at first run.
- fireworks: Fireworks audio transcription endpoint (OpenAI-compatible,
             multipart). VERIFY the endpoint + model id are enabled on your
             account before relying on it (see README).

Adding audio is the single biggest accuracy win for clips with speech, but it
is opt-in so the container runs anywhere with just frames. Any backend failure
degrades gracefully to an empty transcript (never crashes the pipeline).
"""
from __future__ import annotations

import os
import sys


def transcribe(audio_path, backend: str = "none", whisper_model: str = "base",
               client=None, fireworks_model: str = "whisper-v3") -> str:
    if not audio_path or backend == "none":
        return ""
    if backend == "local":
        return _local(audio_path, whisper_model)
    if backend == "fireworks":
        return _fireworks(audio_path, client, fireworks_model)
    _warn(f"unknown TRANSCRIBE_BACKEND={backend}; skipping audio")
    return ""


def _warn(msg: str) -> None:
    print(f"[transcribe] WARNING: {msg}", file=sys.stderr)


def _local(audio_path: str, whisper_model: str) -> str:
    try:
        from faster_whisper import WhisperModel
    except Exception:
        _warn("faster-whisper not installed; `pip install faster-whisper` to "
              "enable local audio. Continuing with empty transcript.")
        return ""
    try:
        model = WhisperModel(whisper_model, device="auto", compute_type="int8")
        segments, _info = model.transcribe(audio_path, vad_filter=True)
        return " ".join(seg.text.strip() for seg in segments).strip()
    except Exception as e:  # model download / runtime failure
        _warn(f"local transcription failed: {e}")
        return ""


def _fireworks(audio_path: str, client, fireworks_model: str) -> str:
    import requests
    if client is None:
        _warn("no client for fireworks transcription; skipping")
        return ""
    url = f"{client.base_url}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {client.api_key}"}
    try:
        with open(audio_path, "rb") as fh:
            files = {"file": (os.path.basename(audio_path), fh, "audio/ogg")}
            data = {"model": fireworks_model}
            resp = requests.post(url, headers=headers, files=files, data=data,
                                 timeout=client.timeout)
    except Exception as e:
        _warn(f"fireworks transcription request failed: {e}")
        return ""
    if resp.status_code >= 400:
        _warn(f"fireworks transcription {resp.status_code}: {resp.text[:200]}")
        return ""
    try:
        return resp.json().get("text", "").strip()
    except Exception:
        return resp.text.strip()
