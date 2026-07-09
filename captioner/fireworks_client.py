"""Minimal Fireworks REST client (OpenAI-compatible).

Uses plain `requests` to avoid SDK lock-in and to keep full control over the
multimodal `image_url` payload shape documented at
https://docs.fireworks.ai/guides/querying-vision-language-models
"""
from __future__ import annotations

import base64
import json
import re
import time
from typing import Any, Optional

import requests


class FireworksError(RuntimeError):
    pass


class FireworksClient:
    def __init__(self, api_key: str, base_url: str, timeout: int = 120):
        if not api_key:
            raise FireworksError(
                "FIREWORKS_API_KEY is not set. Export it, or use --mock for a "
                "no-network dry run."
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _post(self, path: str, payload: dict, retries: int = 10) -> dict:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        last_err = ""
        for attempt in range(retries):
            resp = requests.post(url, headers=headers, json=payload,
                                 timeout=self.timeout)
            if resp.status_code in (429, 503):
                # Cold start (scale-to-zero) or rate limit: back off and retry.
                last_err = resp.text[:300]
                wait = min(60, 10 * (attempt + 1))
                print(f"[fireworks] {resp.status_code} (attempt {attempt + 1}/"
                      f"{retries}) — deployment warming up, retrying in {wait}s")
                time.sleep(wait)
                continue
            if resp.status_code >= 400:
                raise FireworksError(f"{resp.status_code} {url}: {resp.text[:500]}")
            return resp.json()
        raise FireworksError(f"gave up after {retries} retries: {last_err}")

    def chat(self, model: str, messages: list, temperature: float = 0.4,
             max_tokens: int = 320, response_format: Optional[dict] = None,
             reasoning_effort: Optional[str] = None, retries: int = 10) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort
        data = self._post("/chat/completions", payload, retries=retries)
        try:
            msg = data["choices"][0]["message"]
            return _strip_reasoning(msg.get("content") or "")
        except (KeyError, IndexError) as e:
            raise FireworksError(
                f"Unexpected response: {json.dumps(data)[:500]}") from e

    def list_models(self) -> list:
        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        resp = requests.get(url, headers=headers, timeout=self.timeout)
        if resp.status_code >= 400:
            raise FireworksError(f"{resp.status_code} {url}: {resp.text[:500]}")
        return resp.json().get("data", [])


def image_content(jpeg_bytes: bytes) -> dict:
    """OpenAI-compatible image_url content part from raw JPEG bytes."""
    b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
    return {"type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}


def text_content(text: str) -> dict:
    return {"type": "text", "text": text}


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _strip_reasoning(text: str) -> str:
    """Remove <think>...</think> blocks that some reasoning models emit inline."""
    return _THINK_RE.sub("", text or "").strip()
