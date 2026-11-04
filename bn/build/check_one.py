#!/usr/bin/env python3
"""Cek satu lagu (data hasil ekstraksi + koreksi di work/fix) tanpa menulis apa pun.
Pakai: python3 build/check_one.py 2      atau   python3 build/check_one.py 597b
Menampilkan not, baris lirik, ayat, dan peringatan validator (ketukan per birama, not vs suku kata)."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_site import validate
for arg in sys.argv[1:]:
    m = re.fullmatch(r"(\d+)([a-z]?)", arg)
    sid = f"{int(m.group(1)):03d}{m.group(2)}"
    h = json.load(open(os.path.join(HERE, "work", "bn", sid + ".json")))
    fx = os.path.join(HERE, "work", "fix", sid + ".json")
    if os.path.exists(fx):
        for k, v in json.load(open(fx)).items():
            if k != "note": h[k] = v
        print("(koreksi work/fix diterapkan)")
    print(f"BN {h['be']}{h['variant']} — {h['title']} | do={h['key']} birama={h['meter']} | Logu {h.get('bl')} | hal. {h['pages']}")
    for i, s in enumerate(h["sections"]):
        print(f"--- bagian {i+1}" + (f" (meter {s['meter']})" if s.get("meter") else ""))
        print(s["notes"])
        for r in s["rows"]:
            print("  > " + r)
    for i, v in enumerate(h["verses"]):
        print(f"ayat {h.get('vnum', list(range(1, 99)))[i]}: " + " / ".join(v))
    w = validate(h)
    print("VALIDATOR: " + ("OK" if not w else "\n  " + "\n  ".join(w)))
