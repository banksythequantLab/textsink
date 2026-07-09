import glob
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

pattern = sys.argv[1] if len(sys.argv) > 1 else "*"
for f in sorted(glob.glob(f"heckle_out/{pattern}_hecklers_*.json")):
    d = json.load(open(f, encoding="utf-8"))
    print("===", f.split("/")[-1].split("\\")[-1])
    if d.get("beats"):
        print("  scene:", d["beats"][0]["what"][:100])
    for l in d.get("dialogue", [])[:10]:
        print(f"  [{l['start']:>5.1f}s] {l['who']}: {l['text']}")
    print()
