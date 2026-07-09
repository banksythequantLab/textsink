import json

d = json.load(open("ab_results.json", encoding="utf-8"))
rows = d["rows"]

def valid(r):
    # drop rows where either judge response was unparseable (0/0)
    return not ((r["tuned"]["accuracy"] == 0 and r["tuned"]["tone"] == 0) or
                (r["prompted"]["accuracy"] == 0 and r["prompted"]["tone"] == 0))

clean = [r for r in rows if valid(r)]
print(f"rows: {len(rows)} total, {len(clean)} clean (judge parsed both sides)")

for side in ("tuned", "prompted"):
    a = sum(r[side]["accuracy"] for r in clean) / len(clean)
    t = sum(r[side]["tone"] for r in clean) / len(clean)
    print(f"{side:9} accuracy {a:.2f}   tone {t:.2f}")

wins = {"tuned": 0, "prompted": 0, "tie": 0}
for r in clean:
    ts = r["tuned"]["accuracy"] + r["tuned"]["tone"]
    ps = r["prompted"]["accuracy"] + r["prompted"]["tone"]
    wins["tuned" if ts > ps else "prompted" if ps > ts else "tie"] += 1
print("head-to-head:", wins)

print("\nper style (clean rows):")
from collections import defaultdict
by = defaultdict(list)
for r in clean:
    by[r["style"]].append(r)
for style, rs in by.items():
    ta = sum(r["tuned"]["accuracy"] + r["tuned"]["tone"] for r in rs) / len(rs)
    pa = sum(r["prompted"]["accuracy"] + r["prompted"]["tone"] for r in rs) / len(rs)
    print(f"  {style:18} tuned {ta:.1f}  vs  prompted {pa:.1f}  (n={len(rs)})")
