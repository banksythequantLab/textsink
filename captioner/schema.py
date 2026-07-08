"""Output data structures + light JSON validation (no external deps)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

STYLES = ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]


@dataclass
class ClipResult:
    clip: str
    duration_sec: float
    frames: int
    transcript: str
    scene: dict
    captions: dict
    meta: dict = field(default_factory=dict)

    def validate(self) -> "ClipResult":
        missing = [s for s in STYLES
                   if s not in self.captions or not str(self.captions[s]).strip()]
        if missing:
            raise ValueError(f"{self.clip}: missing captions for {missing}")
        return self

    def to_dict(self) -> dict:
        return asdict(self)


def dumps(results: list) -> str:
    return json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False)
