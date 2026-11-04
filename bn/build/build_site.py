#!/usr/bin/env python3
"""Bangun data situs Buku Nyanyian HKBP dari sumber per lagu (work/bn/NNN.json).

Keluaran: ../site/data/index.json, ../site/data/bNN.json, ../site/scans/bNN.json
Juga memeriksa: ketukan per birama vs birama lagu, jumlah not vs suku kata per baris lirik.
Format not sama dengan Buku Ende, ditambah durasi eksplisit: "5/" = ½ ketuk, "5//" = ¼ ketuk
(dipakai bila satu ketuk tidak terbagi rata, mis. "3/+.//+2//" = titik ¾ + ¼).
"""
import base64, glob, io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work", "bn")
SITE = os.path.join(HERE, "..", "site")
CACHE = os.path.join(HERE, "work", "scan-cache")
PDF = os.environ.get("BN_PDF", "/mnt/user-data/attachments/cbd9054d-8209-50ff-8db3-998a463a8b89/8cb44d6e-578135457-BN-HKBP.pdf")
EL = re.compile(r"^(\()?([#b])?([0-7.])([',]*)(/*)(\))?$")


def tok_dur(tok):
    parts = tok.split("+")
    ms = [EL.match(p) for p in parts]
    if any(m is None for m in ms):
        return None, ms
    if any(m.group(5) for m in ms):
        return sum(0.5 ** len(m.group(5)) if m.group(5) else 1.0 / len(parts) for m in ms), ms
    return 1.0, ms


def dedupe(lines):
    """buang blok baris berurutan yang persis sama (blok 1–3 baris)."""
    norm = lambda x: re.sub(r"[^a-z]", "", x.lower())
    out = list(lines)
    changed = True
    while changed:
        changed = False
        for n in (3, 2, 1):
            for i in range(len(out) - 2 * n + 1):
                if [norm(x) for x in out[i:i + n]] == [norm(x) for x in out[i + n:i + 2 * n]]:
                    out = out[:i + n] + out[i + 2 * n:]; changed = True; break
            if changed:
                break
    return out


def validate(h):
    msgs = []
    tag = f"BN {h['be']}{h.get('variant', '')}"
    bars = []
    for si, s in enumerate(h["sections"]):
        num = int(s.get("meter", h["meter"]).split("/")[0])
        alt = h.get("meter2") or num
        cur, slur, need = 0.0, False, 0
        for tok in s["notes"].split():
            if tok in ("|", ":|", "|]"):
                bars.append((si, cur, tok, (num, alt))); cur = 0.0; continue
            if tok == "v":
                continue
            d, ms = tok_dur(tok)
            if d is None:
                msgs.append(f"{tag}: token tidak dikenal {tok!r}"); continue
            cur += d
            for m in ms:
                if m.group(3) == ".":
                    if m.group(6): slur = False
                    continue
                rest = m.group(3) == "0"
                if m.group(1): slur = True
                cont = slur and not m.group(1) and not rest
                if not rest and not cont:
                    need += 1
                if m.group(6): slur = False
        if cur:
            bars.append((si, cur, "(tanpa garis)", (num, alt)))
        for ri, row in enumerate(s["rows"]):
            n = sum(len(w.split("-")) for w in row.split())
            if n != need:
                msgs.append(f"{tag} bagian {si+1} baris {ri+1}: {need} not vs {n} suku kata")
    paired = set()  # birama pendek + birama pendek berikut = satu birama penuh (ketuk angkat di tengah lagu)
    for i in range(len(bars) - 1):
        (si, n, end, (num, alt)), (si2, n2, _, _) = bars[i], bars[i + 1]
        if si == si2 and n < num and n2 < num and any(abs(n + n2 - m) < 1e-6 for m in (num, alt)):
            paired.update((i, i + 1))
    for i, (si, n, end, (num, alt)) in enumerate(bars):
        if i in paired:
            continue
        start = i == 0 or bars[i-1][0] != si or bars[i-1][2] in (":|", "|]")
        last = end in (":|", "|]", "(tanpa garis)") or i == len(bars)-1 or bars[i+1][0] != si
        ok = any(abs(n - m) < 1e-6 for m in (num, alt))
        big = max(num, alt)
        if not ok and (n > big + 1e-6 or not (start or last)):
            msgs.append(f"{tag}: birama #{i+1} (bagian {si+1}) = {n:g} ketuk, seharusnya {num}")
    return msgs


KEYS = {"C": 0, "G": 7, "D": 2, "A": 9, "E": 4, "B": 11, "F": 5, "Bb": 10, "Eb": 3, "Ab": 8, "Db": 1, "Gb": 6, "F#": 6}
MAJ = [0, 2, 4, 5, 7, 9, 11]


def play_oct(h):
    """geser oktaf pemutaran agar nada tengah melodi berada di sekitar C4–C5 (buku kadang menulis satu oktaf tinggi)."""
    ps = []
    for s in h["sections"]:
        for tok in s["notes"].split():
            for p in tok.split("+"):
                m = EL.match(p)
                if m and m.group(3) not in ".0":
                    o = m.group(4).count("'") - m.group(4).count(",")
                    ps.append(60 + KEYS.get(h["key"], 0) + MAJ[int(m.group(3)) - 1] + 12 * o)
    if not ps:
        return 0
    ps.sort(); med = ps[len(ps) // 2]
    return round((67 - med) / 12)


def scan_jpg(page):
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f"p{page:04d}.jpg")
    if not os.path.exists(out):
        import pymupdf
        doc = scan_jpg.doc = getattr(scan_jpg, "doc", None) or pymupdf.open(PDF)
        pix = doc[page - 1].get_pixmap(dpi=78, colorspace=pymupdf.csGRAY)
        pix.save(out, jpg_quality=55)
    return out


def main():
    hymns = {}
    for f in sorted(glob.glob(os.path.join(WORK, "*.json"))):
        h = json.load(open(f))
        h["batch"] = (h["be"] - 1) // 20 + 1
        h["variant"] = h.get("variant", "")
        h["id"] = f"{h['be']}{h['variant']}"
        hymns[(h["be"], h["variant"])] = h
    warn = []
    for k in sorted(hymns):
        warn += validate(hymns[k])
    import verse_align as VA
    D = VA.build_dict(hymns.values())
    vstat = {"not": 0, "cocok": 0, "belum": 0}
    for key in sorted(hymns):
        h = hymns[key]
        direct = h.pop("vl_direct", {}) or {}
        if len(h.get("verses", [])) < 2:
            continue
        bad = any("suku kata" in m for m in validate(h))
        vl = [None]
        for i, v in enumerate(h["verses"][1:], start=1):
            if str(i) in direct and not bad:
                vl.append(direct[str(i)]); vstat["not"] += 1; continue
            r = None if bad else VA.align_verse(h, v, D)[0]
            if not r and not bad:
                dv = dedupe(v)  # baris ulangan yang ditulis dua kali di teks ayat (bagian :| hanya satu baris lirik)
                if dv != v:
                    r = VA.align_verse(h, dv, D)[0]
                    if r:
                        r["notes"] = r["notes"] + ["baris yang ditulis dua kali di teks dinyanyikan pada bagian ulang"]
            if r:
                vl.append({"r": r["rows"], "c": r["cost"], "n": r["notes"]}); vstat["cocok"] += 1
            else:
                vl.append({"x": "ayat 1 belum pas dengan not" if bad else "jumlah suku kata tidak bisa dipasangkan ke not"}); vstat["belum"] += 1
        h["vl"] = vl
    # pembanding Buku Ende, status, oktaf putar
    cmpf = os.path.join(HERE, "work", "cmp_be.json")
    cmp = {c["bn"]: c for c in json.load(open(cmpf))} if os.path.exists(cmpf) else {}
    bad_ids = {w.split(":")[0].split(" bagian")[0][3:] for w in warn}
    rev = {}
    for f in glob.glob(os.path.join(HERE, "work", "review", "agent*.json")):
        for x in json.load(open(f)):
            rev[x["id"]] = x
    for k in sorted(hymns):
        h = hymns[k]
        x = rev.get(f"{h['be']:03d}{h['variant']}")
        if x:
            h["review"] = x["status"]
            if x["status"] == "issue":
                h["checks"].append("Pemeriksaan terhadap gambar halaman — belum diputuskan: " + x["detail"])
                bad_ids.add(h["id"])
    for k in sorted(hymns):
        h = hymns[k]
        c = cmp.get(h["id"])
        if c:
            h["becmp"] = {"be": c["be"], "r": c["r"]}
        flag = h["id"] in bad_ids or (c and c["r"] < 0.95)
        h["status"] = "Perlu dicek" if flag else ""
        h["oct"] = play_oct(h)
        if not h["oct"]:
            del h["oct"]
    os.makedirs(os.path.join(SITE, "data"), exist_ok=True)
    os.makedirs(os.path.join(SITE, "scans"), exist_ok=True)
    have_scans = os.path.exists(PDF) and "--noscan" not in sys.argv
    index, batches = [], {}
    for k in sorted(hymns):
        h = hymns[k]
        h.pop("warn", None)
        index.append({"be": h["be"], "id": h["id"], "variant": h["variant"], "bl": h.get("bl"), "title": h["title"],
                      "batch": h["batch"], "status": h.get("status", ""), "cat": h.get("cat") or "",
                      "nv": len(h.get("verses", [])), "nvl": (1 if h.get("verses") else 0) + sum(1 for v in (h.get("vl") or [])[1:] if v and v.get("r")), "be2": (h.get("becmp") or {}).get("be")})
        batches.setdefault(h["batch"], []).append(h)
    json.dump(index, open(os.path.join(SITE, "data", "index.json"), "w"), ensure_ascii=False)
    for b, arr in batches.items():
        json.dump(arr, open(os.path.join(SITE, "data", f"b{b:02d}.json"), "w"), ensure_ascii=False)
        if not have_scans:
            continue
        scans = {}
        for h in arr:
            for p in h.get("pages", []):
                scans[p] = "data:image/jpeg;base64," + base64.b64encode(open(scan_jpg(p), "rb").read()).decode()
        json.dump(scans, open(os.path.join(SITE, "scans", f"b{b:02d}.json"), "w"))
    print(f"{len(hymns)} lagu ({len({k[0] for k in hymns})} nomor), batch: {len(batches)}")
    print(f"lirik ayat 2+: {vstat['not']} dari not di buku, {vstat['cocok']} dipasang otomatis, {vstat['belum']} belum")
    print(f"peringatan: {len(warn)} di {len({w.split(':')[0].split(' bagian')[0] for w in warn})} lagu")
    json.dump(warn, open(os.path.join(HERE, "work", "validate_warn.json"), "w"), ensure_ascii=False, indent=0)
    if "-v" in sys.argv:
        for w in warn:
            print("  " + w)


if __name__ == "__main__":
    main()
