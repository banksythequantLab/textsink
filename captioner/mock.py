"""Deterministic offline client for --mock runs and CI wiring tests."""
from __future__ import annotations

import json


class MockClient:
    base_url = "mock://local"
    api_key = "mock"
    timeout = 1

    def chat(self, model, messages, temperature=0.0, max_tokens=256,
             response_format=None, reasoning_effort=None):
        last = messages[-1]["content"]
        text = _as_text(last)
        if isinstance(last, list) or "Return JSON with keys" in text:
            return json.dumps({
                "setting": "an indoor room, daytime",
                "subjects": ["a person", "a laptop"],
                "actions": ["the person types", "the person smiles at the screen"],
                "on_screen_text": [], "notable_audio": ["upbeat background music"],
                "mood": "focused"})
        if "CAPTION TO SCORE" in text:
            return json.dumps({"accuracy": 4, "tone": 4, "reason": "mock"})
        if "STYLE = Sarcastic" in text:
            return "Oh sure, because typing furiously is the hallmark of real productivity."
        if "STYLE = Humorous (tech)" in text:
            return "POV: you finally get it to compile and immediately forget how."
        if "STYLE = Humorous (non-tech)" in text:
            return "The face of someone who found the one email that actually mattered today."
        return "A person works attentively at a laptop indoors as upbeat music plays."

    def list_models(self):
        return [{"id": "mock/qwen3p7-plus"}, {"id": "mock/gpt-oss-120b"}]


def _as_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(p.get("text", "") for p in content
                        if isinstance(p, dict) and p.get("type") == "text")
    return str(content)
