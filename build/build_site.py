#!/usr/bin/env python3
"""Build the Buku Ende site data from per-hymn source files.

Source: work/be/NNN.txt (or NNN.json for hand-converted ones).
Output: ../site/data/index.json, ../site/data/bNN.json, ../site/scans/bNN.json
Also validates: beats per bar vs meter, notes vs syllables per lyric row.
"""
import base64, glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work", "be")
SITE = os.path.join(HERE, "..", "site")
CACHE = os.path.join(HERE, "work", "scan-cache")
PDF = os.environ.get("BE_PDF", "/mnt/user-data/attachments/cbd9054d-8209-50ff-8db3-998a463a8b89/a89ce26f-buku-ende-hkbp.pdf")  # scan PDF Buku Ende (tidak ikut di repo)
EL = re.compile(r"^(\()?([#b])?([0-7.])([',]*)(\))?$")


def parse_txt(path):
    h = {"checks": [], "refs": [], "sections": [], "verses": []}
    mode, sec, verse = None, None, []
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("@"):
            k, _, v = line[1:].partition(" ")
            v = v.strip()
            if k in ("be", "bl", "oct"):
                h[k] = int(v)
            elif k == "pages":
                h["pages"] = [int(x) for x in v.replace(",", " ").split()]
            elif k == "check":
                h["checks"].append(v)
            elif k == "ref":
                t, u, n = [x.strip() for x in v.split("|")]
                h["refs"].append({"t": t, "u": u, "n": n})
            else:
                h[k] = v
            continue
        if re.match(r"^#V\s*$", line):
            mode = "V"; verse = []; h["verses"].append(verse); continue
        m_sec = re.match(r"^#[A-UW-Z]((?:\s+(?:\d+/\d+|key=[A-G][b#]?))*)\s*$", line)
        if m_sec:
            mode = "S"; sec = {"notes": [], "rows": []}
            for tok in m_sec.group(1).split():
                if tok.startswith("key="): sec["key"] = tok[4:]
                else: sec["meter"] = tok
            h["sections"].append(sec); continue
        if mode == "S":
            if line.startswith(">"):
                sec["rows"].append(line[1:].strip())
            else:
                sec["notes"].append(line.strip())
        elif mode == "V":
            if line.strip() == "-":
                verse = []; h["verses"].append(verse)
            else:
                verse.append(line.strip())
    for s in h["sections"]:
        s["notes"] = "\n".join(s["notes"])
    if not h["refs"]:
        del h["refs"]
    return h


def validate(h):
    msgs = []
    num = int(h["meter"].split("/")[0])
    bars = []
    for si, s in enumerate(h["sections"]):
        cur, slur, need = 0, False, 0
        for tok in s["notes"].split():
            if tok in ("|", ":|", "|]"):
                bars.append((si, cur, tok, int(s.get("meter", h["meter"]).split("/")[0]))); cur = 0; continue
            if tok == "v":
                continue
            cur += 1
            for p in tok.split("+"):
                m = EL.match(p)
                if not m:
                    msgs.append(f"BE {h['be']}: token tidak dikenal {p!r}"); continue
                if m.group(3) == ".":
                    if m.group(5): slur = False
                    continue
                rest = m.group(3) == "0"
                if m.group(1): slur = True
                cont = slur and not m.group(1) and not rest
                if not rest and not cont:
                    need += 1
                if m.group(5): slur = False
        if cur:
            bars.append((si, cur, "(tanpa garis)", int(s.get("meter", h["meter"]).split("/")[0])))
        for ri, row in enumerate(s["rows"]):
            n = sum(len(w.split("-")) for w in row.split())
            if n != need:
                msgs.append(f"BE {h['be']} bagian {si+1} baris {ri+1}: {need} not vs {n} suku kata")
    # bar lengths: short bars are fine at a section start (pickup) or right before :| / |] / section end
    for i, (si, n, end, num) in enumerate(bars):
        start = i == 0 or bars[i-1][0] != si or bars[i-1][2] in (":|", "|]")
        last = end in (":|", "|]", "(tanpa garis)") or i == len(bars)-1 or bars[i+1][0] != si
        if n > num or (n < num and not start and not last):
            msgs.append(f"BE {h['be']}: birama #{i+1} (bagian {si+1}) = {n} ketuk, seharusnya {num}")
    return msgs


def scan_png(page):
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f"p{page:03d}.png")
    if not os.path.exists(out):
        base = os.path.join(CACHE, f"tmp{page}")
        subprocess.run(["pdftoppm", "-r", "170", "-f", str(page), "-l", str(page), "-mono", "-png", "-singlefile", PDF, base], check=True)
        os.replace(base + ".png", out)
    return out


def main():
    hymns = {}
    for f in sorted(glob.glob(os.path.join(WORK, "*.txt")) + glob.glob(os.path.join(WORK, "*.json"))):
        h = json.load(open(f)) if f.endswith(".json") else parse_txt(f)
        h["batch"] = (h["be"] - 1) // 20 + 1
        h["variant"] = h.get("variant", "")
        h["id"] = f"{h['be']}{h['variant']}"
        hymns[(h["be"], h["variant"])] = h
    warn = []
    for be in sorted(hymns):
        warn += validate(hymns[be])
    if len(sys.argv) > 2 and sys.argv[1] == "--check":
        a, _, b = sys.argv[2].partition("-"); a = int(a); b = int(b or a)
        sel = [k for k in sorted(hymns) if a <= k[0] <= b]
        missing = [n for n in range(a, b + 1) if (n, "") not in hymns]
        for key in sel:
            h = hymns[key]; be = h["be"]
            for k in ("bl", "title", "key", "meter", "credit", "pages"):
                if k not in h: warn.append(f"BE {be}: field @{k} kosong")
            if not h["verses"]: warn.append(f"BE {be}: tidak ada ayat (#V)")
        ws = [w for w in warn if any(w.startswith(f"BE {be}:") or w.startswith(f"BE {be} ") for be in {k[0] for k in sel})]
        print(f"CEK BE {a}-{b}: {len(sel)} file, belum ada: {missing or '-'}")
        print("OK, tidak ada peringatan" if not ws else "PERINGATAN:\n  " + "\n  ".join(ws))
        return
    # lirik ayat 2 dst dipasang ke not (lihat verse_align.py)
    import verse_align as VA
    D = VA.build_dict(hymns.values())
    vstat = {"cocok": 0, "belum": 0}
    for key in sorted(hymns):
        h = hymns[key]
        if len(h.get("verses", [])) < 2:
            continue
        bad = any("suku kata" in m for m in validate(h))
        vl = [None]
        for v in h["verses"][1:]:
            r = None if bad else VA.align_verse(h, v, D)[0]
            if r:
                vl.append({"r": r["rows"], "c": r["cost"], "n": r["notes"]}); vstat["cocok"] += 1
            else:
                vl.append({"x": "ayat 1 belum pas dengan not" if bad else "jumlah suku kata tidak bisa dipasangkan ke not"}); vstat["belum"] += 1
        h["vl"] = vl
    os.makedirs(os.path.join(SITE, "data"), exist_ok=True)
    os.makedirs(os.path.join(SITE, "scans"), exist_ok=True)
    # scan halaman hanya untuk panel Dev; dilewati bila PDF tidak ada (mis. hasil clone dari GitHub)
    have_scans = os.path.exists(PDF) or os.path.isdir(CACHE)
    if not have_scans:
        print("Catatan: PDF scan tidak ditemukan (set BE_PDF=...); site/scans tidak dibuat ulang.")
    index, batches = [], {}
    for be in sorted(hymns):
        h = hymns[be]
        index.append({"be": h["be"], "id": h["id"], "variant": h["variant"], "bl": h.get("bl"), "title": h["title"], "batch": h["batch"], "status": h.get("status", "")})
        batches.setdefault(h["batch"], []).append(h)
    json.dump(index, open(os.path.join(SITE, "data", "index.json"), "w"), ensure_ascii=False)
    for b, arr in batches.items():
        json.dump(arr, open(os.path.join(SITE, "data", f"b{b:02d}.json"), "w"), ensure_ascii=False)
        if not have_scans:
            continue
        scans = {}
        for h in arr:
            for p in h.get("pages", []):
                scans[p] = "data:image/png;base64," + base64.b64encode(open(scan_png(p), "rb").read()).decode()
        json.dump(scans, open(os.path.join(SITE, "scans", f"b{b:02d}.json"), "w"))
    print(f"{len(hymns)} ende ({len({k[0] for k in hymns})} nomor), batch: {sorted(batches)}")
    print(f"lirik ayat 2+: {vstat['cocok']} dipasang ke not, {vstat['belum']} belum")
    if warn:
        print("PERINGATAN:")
        for w in warn:
            print("  " + w)


if __name__ == "__main__":
    main()
