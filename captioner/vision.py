"""Frames -> grounded scene description (structured facts)."""
from __future__ import annotations

import json

from .fireworks_client import image_content, text_content

SCENE_SYSTEM = (
    "You are a meticulous video analyst. Given ordered frames sampled from a "
    "short clip (and optionally a transcript), extract ONLY what is actually "
    "visible or audible. Do not speculate. Respond with strict JSON."
)
SCENE_INSTRUCTION = (
    "Analyze these ordered frames from one short video clip. Return JSON with "
    "keys: setting (string), subjects (array), actions (array of short strings "
    "in time order), on_screen_text (array), notable_audio (array), mood "
    "(string). Concise values; empty string/array when unknown. JSON only."
)


def describe_scene(client, model, frames, transcript, temperature=0.2,
                   max_tokens=1200, reasoning_effort=None) -> dict:
    content = [text_content(SCENE_INSTRUCTION)]
    for fb in frames:
        content.append(image_content(fb))
    if (transcript or "").strip():
        content.append(text_content(
            f"Transcript (for grounding): {transcript.strip()[:1500]}"))
    messages = [
        {"role": "system", "content": SCENE_SYSTEM},
        {"role": "user", "content": content},
    ]
    raw = client.chat(model=model, messages=messages, temperature=temperature,
                      max_tokens=max_tokens, reasoning_effort=reasoning_effort,
                      response_format={"type": "json_object"})
    return _coerce_json(raw)


def scene_to_text(scene: dict) -> str:
    parts = []
    if scene.get("setting"):
        parts.append(f"Setting: {scene['setting']}.")
    if scene.get("subjects"):
        parts.append("Subjects: " + ", ".join(map(str, scene["subjects"])) + ".")
    if scene.get("actions"):
        parts.append("Actions: " + "; ".join(map(str, scene["actions"])) + ".")
    if scene.get("on_screen_text"):
        parts.append("On-screen text: " + " | ".join(map(str, scene["on_screen_text"])) + ".")
    if scene.get("notable_audio"):
        parts.append("Audio: " + "; ".join(map(str, scene["notable_audio"])) + ".")
    if scene.get("mood"):
        parts.append(f"Mood: {scene['mood']}.")
    return " ".join(parts).strip() or "No salient details detected."


def _coerce_json(raw: str) -> dict:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        nl = raw.find("\n")
        if nl != -1 and raw[:nl].strip().lower() in ("json", ""):
            raw = raw[nl + 1:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(raw[s:e + 1])
            except json.JSONDecodeError:
                pass
    # Unparseable response: return an EMPTY scene so the validity gate
    # catches it and retries - never smuggle raw debris into the facts.
    return {"setting": "", "subjects": [], "actions": [],
            "on_screen_text": [], "notable_audio": [], "mood": ""}
