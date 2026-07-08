import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.textsink_cc import _parse_text_beats, _unwrap_tool_call, _norm_beat

t1 = """* **Beat 1 (0:00 - 0:01):** An orange kitten emerges from the shadows.
* **Beat 2 (0:01 - 0:02):** The kitten continues walking forward."""
t2 = "- 0:00-0:01: A ginger kitten walks forward through green leaves."
inner = "{'segments': [{'start_time': 0.0, 'end_time': 1.5, 'label': 'A ginger kitten walks forward.'}]}"
t3 = json.dumps({"action": "video_segmentation", "action_input": inner})

print("md:", _parse_text_beats(t1))
print("dash:", _parse_text_beats(t2))
print("tool:", [_norm_beat(b) for b in _unwrap_tool_call(t3)])
