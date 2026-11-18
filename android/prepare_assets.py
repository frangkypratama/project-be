#!/usr/bin/env python3
"""Menyiapkan data aplikasi Android luring dari sumber situs.

Dipanggil dari akar repo:  python3 android/prepare_assets.py
Hasil di android/app/src/main/assets/:
  be.json, bn.json  data lagu ringkas (judul, not, lirik semua ayat, pemasangan suku kata)
  score.html        penggambar not balok (abcjs) untuk tampilan dan cetak
  abcjs.js          pustaka not balok (luring)
"""
import glob, json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "android", "app", "src", "main", "assets")
os.makedirs(OUT, exist_ok=True)

def credits(h):
    c = h.get("credits")
    if c:
        return [x for x in c if x]
    c = (h.get("credit") or "").strip()
    return [x.strip() for x in c.split("·") if x.strip()] if c else []

def pack(h):
    o = {"id": str(h["id"]), "t": h["title"], "k": h.get("key") or "C", "m": h.get("meter") or "4/4"}
    if h.get("oct"): o["o"] = h["oct"]
    if h.get("tempo"): o["tp"] = h["tempo"]
    if h.get("bl"): o["bl"] = h["bl"]
    if h.get("cat"): o["c"] = h["cat"]
    cr = credits(h)
    if cr: o["cr"] = cr
    secs = []
    for s in h["sections"]:
        x = {"n": s["notes"], "r": s["rows"]}
        if s.get("meter"): x["m"] = s["meter"]
        if s.get("key"): x["k"] = s["key"]
        secs.append(x)
    o["s"] = secs
    o["v"] = h.get("verses") or []
    if h.get("vnum"): o["vn"] = h["vnum"]
    vl = h.get("vl")
    if vl:
        o["vl"] = [(v["r"] if (i and v and v.get("r")) else None) for i, v in enumerate(vl)]
    return o

def book(pattern):
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, pattern))):
        out.extend(pack(h) for h in json.load(open(f, encoding="utf-8")))
    return out

be = book("site/data/b*.json")
bn = book("bn/site/data/b*.json")
for name, items in (("be", be), ("bn", bn)):
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, ensure_ascii=False, separators=(",", ":"))

shutil.copy(os.path.join(ROOT, "android", "abcjs-basic-min.js"), os.path.join(OUT, "abcjs.js"))
shutil.copy(os.path.join(ROOT, "android", "score.html"), os.path.join(OUT, "score.html"))

sz = {f: os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)}
print(f"ok: BE {len(be)} lagu, BN {len(bn)} lagu ->", ", ".join(f"{k} {v/1e6:.2f} MB" for k, v in sorted(sz.items())))
if len(be) < 860 or len(bn) < 860:
    sys.exit("GAGAL: jumlah lagu kurang")
