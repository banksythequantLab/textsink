import glob
import json

out = open("all_dialogue.txt", "w", encoding="utf-8")
for f in sorted(glob.glob("heckle_out/*_hecklers_*.json")):
    d = json.load(open(f, encoding="utf-8"))
    name = f.split("\\")[-1].split("/")[-1].replace("_hecklers_", " | ")
    out.write(f"\n=== {name}\n")
    if d.get("beats"):
        out.write(f"    scene: {d['beats'][0]['what'][:80]}\n")
    for l in d.get("dialogue", []):
        out.write(f"  {l['who']}: {l['text']}\n")
out.close()
print("written all_dialogue.txt")
