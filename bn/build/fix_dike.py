#!/usr/bin/env python3
"""Pisahkan kata depan "di"/"ke" yang tersambung ke kata berikut di baris lirik (mis. di-da-lam → di da-lam),
hanya bila teks ayat di seluruh buku lebih sering menulis "di dalam" daripada "didalam"."""
import json, glob, re, collections, sys
regs = json.load(open("work/pages.json"))
W = collections.Counter(); B = collections.Counter()
for r in regs:
    for t in r["text"]:
        if t["size"] < 11: continue
        ws = [w.strip("'’").lower() for w in re.findall(r"[A-Za-z'’]+", t["t"].replace("’", "'"))]
        for a, b in zip(ws, ws[1:]):
            B[(a, b)] += 1
        W.update(ws)
def fix_row(row, log):
    out = []
    for w in row.split():
        parts = w.split("-")
        if len(parts) > 1 and parts[0].lower() in ("di", "ke"):
            rest = "".join(p.strip(",.;:!?") for p in parts[1:]).lower().strip("'")
            joined = parts[0].lower() + rest
            if B[(parts[0].lower(), rest)] > W[joined] and B[(parts[0].lower(), rest)] >= 1:
                out.append(parts[0]); out.append("-".join(parts[1:])); log.append(w); continue
        out.append(w)
    return " ".join(out)
tot = collections.Counter()
for f in sorted(glob.glob("work/fix/*.json")):
    fx = json.load(open(f)); log = []
    for s in fx.get("sections", []):
        s["rows"] = [fix_row(r, log) for r in s["rows"]]
    for k, v in (fx.get("vl_direct") or {}).items():
        if v and v.get("r"):
            v["r"] = [[fix_row(r, log) for r in rs] for rs in v["r"]]
    if log:
        fx.setdefault("note", [])
        if isinstance(fx["note"], str): fx["note"] = [fx["note"]]
        fx["note"].append("kata depan dipisah: " + ", ".join(log))
        json.dump(fx, open(f, "w"), ensure_ascii=False, indent=1)
        tot[f] = len(log)
        print(f.split("/")[-1], log)
print("file:", len(tot), "kata:", sum(tot.values()))
