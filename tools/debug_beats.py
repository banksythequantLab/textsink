import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from captioner import frames as F
from captioner.config import Config
from captioner.fireworks_client import FireworksClient, image_content, text_content
from tools.textsink_cc import BEATS_SYSTEM

cfg = Config.from_env()
client = FireworksClient(cfg.api_key, cfg.base_url, cfg.request_timeout)
clip = sys.argv[1]
sampled = F.sample_frames(clip, 0.5, 10, 20, cfg.frame_width)
dur = sampled.duration
n = len(sampled.frames)
content = [text_content(f"Clip duration: {dur:.1f}s. {n} frames follow.")]
for i, fb in enumerate(sampled.frames):
    t = (i + 0.5) * dur / n
    content.append(text_content(f"frame at t={t:.1f}s:"))
    content.append(image_content(fb))
msgs = [{"role": "system", "content": BEATS_SYSTEM},
        {"role": "user", "content": content}]
raw = client.chat(model=cfg.vision_model, messages=msgs, temperature=0.2,
                  max_tokens=cfg.scene_max_tokens,
                  reasoning_effort=cfg.reasoning_effort,
                  response_format={"type": "json_object"})
print("RAW RESPONSE >>>")
print(raw[:2000])
