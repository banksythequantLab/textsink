import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")
for f, needles in [
    ("heckle_out/12471596-uhd_2560_1440_30fps_hecklers_sarcastic.json",
     ["milkshake apocalypse", "dairy fantasy", "sky is bleeding",
      "Vitamin D"]),
    ("heckle_out/12471596-uhd_2560_1440_30fps_hecklers_humorous_tech.json",
     ["Touch grass", "segfaults", "rizz"]),
]:
    d = json.load(open(f, encoding="utf-8"))
    print("===", f.split("/")[-1])
    for l in d["dialogue"]:
        if any(n.lower() in l["text"].lower() for n in needles):
            print(f"  [{l['start']:.1f}-{l['end']:.1f}] {l['who']}: {l['text']}")
