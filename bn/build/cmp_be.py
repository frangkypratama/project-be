#!/usr/bin/env python3
"""Bandingkan melodi BN dengan Buku Ende (Buku Logu sama) memakai urutan interval nada."""
import json, glob, re, difflib, sys, collections
EL = re.compile(r"^(\()?([#b])?([0-7.])([',]*)(/*)(\))?$")
MAJ = [0, 2, 4, 5, 7, 9, 11]
def pitches(h):
    out = []
    for s in h["sections"]:
        for t in s["notes"].split():
            if t in ("|", ":|", "|]", "v"): continue
            for p in t.split("+"):
                m = EL.match(p)
                if not m or m.group(3) in ".0": continue
                o = m.group(4).count("'") - m.group(4).count(",")
                acc = 1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0
                out.append(MAJ[int(m.group(3)) - 1] + 12 * o + acc)
    return out
be = collections.defaultdict(list)
for f in glob.glob("/home/claude/project-be/site/data/b*.json"):
    for h in json.load(open(f)):
        if h.get("bl"): be[int(h["bl"])].append(h)
res = []
for f in sorted(glob.glob("work/bn/*.json")):
    h = json.load(open(f))
    if not h.get("bl") or not str(h["bl"]).isdigit() or int(h["bl"]) not in be: continue
    a = pitches(h); ia = [y - x for x, y in zip(a, a[1:])]
    best = None
    for b in be[int(h["bl"])]:
        c = pitches(b); ic = [y - x for x, y in zip(c, c[1:])]
        sm = difflib.SequenceMatcher(None, ia, ic, autojunk=False)
        r = sm.ratio()
        if best is None or r > best[0]:
            best = (r, b, sm.get_opcodes(), len(a), len(c))
    res.append({"bn": f"{h['be']}{h['variant']}", "be": f"{best[1]['be']}{best[1].get('variant','')}", "r": round(best[0], 4),
                "na": best[3], "nb": best[4], "diff": [op for op in best[2] if op[0] != "equal"][:8]})
json.dump(res, open("work/cmp_be.json", "w"))
rs = [x["r"] for x in res]
print("pasangan:", len(res))
for th in (1.0, 0.98, 0.95, 0.9, 0.8):
    print(f"  kemiripan >= {th}: {sum(1 for r in rs if r >= th - 1e-9)}")
