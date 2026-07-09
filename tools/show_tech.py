import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")
d = json.load(open("test_input/results_all15_bestof3.json", encoding="utf-8"))
for t in d:
    print(f"{t['task_id']}: {t['captions']['humorous_tech']}")
