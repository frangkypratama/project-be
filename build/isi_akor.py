#!/usr/bin/env python3
"""Isi akor iringan otomatis untuk bagian lagu yang belum punya akor.

Akor disimpan sejajar dengan not:
  - sumber BE  build/work/be/NNN.txt : baris "~ D . A . | Bm . G . |" tepat di atas baris not-nya
  - sumber BE  build/work/be/NNN.json dan data situs site/data, bn/site/data : kolom "chords"
    tiap bagian (baris dipisah "\n", sejajar dengan "notes")
Satu nama akor per ketukan, "." = akor sebelumnya berlanjut. Akor yang sudah ada tidak diubah,
jadi akor yang sudah dikoreksi manusia aman. Jalankan dari akar repo:  python3 build/isi_akor.py
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "android"))
sys.path.insert(0, os.path.join(ROOT, "build"))
import chords  # noqa: E402
from build_site import parse_txt  # noqa: E402

SEC = re.compile(r"^#[A-UW-Z]((?:\s+(?:\d+/\d+|key=[A-G][b#]?))*)\s*$")


def letters_for(h):
    """Baris akor (huruf) untuk tiap bagian; bagian yang sudah punya akor dikembalikan apa adanya."""
    secs, out = h["sections"], []
    for i, s in enumerate(secs):
        if s.get("chords"):
            out.append(s["chords"])
            continue
        key = s.get("key") or h.get("key") or "C"
        ch = chords.harmonize(s["notes"], last_section=(i == len(secs) - 1))
        out.append(chords.to_letters(s["notes"], ch, key))
    return out


def with_chords(sec, letters):
    """Sisipkan kolom "chords" tepat sesudah "notes" (urutan kolom tetap rapi)."""
    out = {}
    for k, v in sec.items():
        if k == "chords":
            continue
        out[k] = v
        if k == "notes":
            out["chords"] = letters
    return out


def fill_txt(path):
    h = parse_txt(path)
    if all(s.get("chords") for s in h["sections"]):
        return False
    lets = letters_for(h)
    lines = open(path, encoding="utf-8").read().split("\n")
    out, si, mode, li = [], -1, None, 0
    for line in lines:
        if SEC.match(line):
            si += 1; mode = "S"; li = 0
        elif re.match(r"^#V\s*$", line):
            mode = None
        elif mode == "S" and line.strip() and not line.startswith((">", "~", "@")):
            if not h["sections"][si].get("chords"):
                out.append("~ " + lets[si].split("\n")[li])
            li += 1
        out.append(line)
    open(path, "w", encoding="utf-8").write("\n".join(out))
    return True


def fill_json(path, indent=None, src=None):
    data = json.load(open(path, encoding="utf-8"))
    one = isinstance(data, dict)
    changed = False
    for h in ([data] if one else data):
        known = src.get(str(h.get("id"))) if src else None
        lets = known or letters_for(h)
        if len(lets) != len(h["sections"]):
            raise ValueError(f"{path} {h.get('id')}: jumlah bagian beda")
        new = [with_chords(s, l) for s, l in zip(h["sections"], lets)]
        if new != h["sections"]:
            h["sections"] = new; changed = True
    if changed:
        txt = json.dumps(data, ensure_ascii=False, indent=indent)
        open(path, "w", encoding="utf-8").write(txt)
    return changed


if __name__ == "__main__":
    n = sum(fill_txt(f) for f in sorted(glob.glob(os.path.join(ROOT, "build/work/be/*.txt"))))
    n += sum(fill_json(f, indent=1) for f in sorted(glob.glob(os.path.join(ROOT, "build/work/be/*.json"))))
    print("sumber BE diisi:", n)
    # data situs BE mengikuti sumbernya, supaya keduanya selalu sama
    src = {}
    for f in glob.glob(os.path.join(ROOT, "build/work/be/*")):
        h = json.load(open(f, encoding="utf-8")) if f.endswith(".json") else parse_txt(f)
        src[f"{h['be']}{h.get('variant', '')}"] = [s["chords"] for s in h["sections"]]
    n = sum(fill_json(f, src=src) for f in sorted(glob.glob(os.path.join(ROOT, "site/data/b*.json"))))
    n += sum(fill_json(f) for f in sorted(glob.glob(os.path.join(ROOT, "bn/site/data/b*.json"))))
    print("file data situs diisi:", n)
