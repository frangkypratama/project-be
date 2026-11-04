#!/usr/bin/env python3
"""Tahap 1: baca PDF Buku Nyanyian HKBP (lapisan teks + vektor) per halaman.

Keluaran: work/pages.json — untuk tiap halaman: judul, kunci/ketuk/tempo, Buku Logu,
komponis, label ayat, sistem not (token per sel + suku kata per baris lirik),
garis atas (½ ketuk), legato, coretan (kres/mol), teks ayat, kredit.
"""
import json, os, re, sys, collections
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.environ.get("BN_PDF", "/mnt/user-data/attachments/cbd9054d-8209-50ff-8db3-998a463a8b89/8cb44d6e-578135457-BN-HKBP.pdf")
OUT = os.path.join(HERE, "work", "pages.json")

DOT_BELOW = "̣"
DOT_ABOVE = "˙"
NOTE_CH = set("01234567.|:") | {DOT_BELOW, DOT_ABOVE}


def is_bold(f):
    return "Bold" in f


def spans_of(page):
    out = []
    d = page.get_text("rawdict")
    for b in d["blocks"]:
        for l in b.get("lines", []):
            if abs(l["dir"][1]) > 1e-3:  # watermark miring
                continue
            for s in l["spans"]:
                if "Myriad" in s["font"]:
                    continue
                chars = [(c["c"], c["bbox"][0], c["bbox"][2]) for c in s["chars"]]
                txt = "".join(c[0] for c in chars)
                if not txt.strip():
                    continue
                out.append({"y": round(s["origin"][1], 1), "top": s["bbox"][1], "x0": s["bbox"][0], "x1": s["bbox"][2],
                            "font": s["font"], "size": round(s["size"], 1), "color": s["color"],
                            "text": txt, "chars": chars})
    return out


def note_tokens(chars):
    """chars: [(c,x0,x1)] terurut x → token not/garis birama."""
    toks = []
    for c, x0, x1 in chars:
        if c.isspace():
            continue
        if c in (DOT_BELOW, DOT_ABOVE):
            if toks and toks[-1]["k"] == "n":
                toks[-1]["oct"] += -1 if c == DOT_BELOW else 1
            else:
                toks.append({"k": "?", "t": c, "x0": x0, "x1": x1})
            continue
        if c in "|:":
            if toks and toks[-1]["k"] == "bar" and x0 - toks[-1]["x1"] < 3.5:
                toks[-1]["t"] += c; toks[-1]["x1"] = x1; continue
            toks.append({"k": "bar", "t": c, "x0": x0, "x1": x1}); continue
        if c == ".":
            toks.append({"k": "dot", "t": c, "x0": x0, "x1": x1}); continue
        if c in "01234567":
            toks.append({"k": "n", "t": c, "deg": int(c), "oct": 0, "acc": 0, "x0": x0, "x1": x1}); continue
        toks.append({"k": "?", "t": c, "x0": x0, "x1": x1})
    return toks


def words_of(chars):
    """kelompokkan karakter jadi kata (dipisah spasi atau celah lebar)."""
    ws, cur = [], None
    for c, x0, x1 in chars:
        if c.isspace():
            cur = None; continue
        if cur and x0 - cur["x1"] > 4.5:
            cur = None
        if cur is None:
            cur = {"t": "", "x0": x0, "x1": x1, "xa": None}; ws.append(cur)
        cur["t"] += c; cur["x1"] = x1
        if cur["xa"] is None and c.isalnum():
            cur["xa"] = x0
    for w in ws:
        if w["xa"] is None: w["xa"] = w["x0"]
    return ws


TITLE_RE = re.compile(r"^\s*(\d+)\s*([a-z])?\s*(?:\.|\s)\s*(.*)$")


def drawings_of(page):
    hl, sl, cv, rules = [], [], [], []
    for g in page.get_drawings():
        col = g.get("color")
        black = col is not None and max(col) < 0.15
        r = g["rect"]
        if r.width > 300 and r.height < 3 and r.y0 > 75:
            rules.append(r.y0)
        for it in g["items"]:
            if it[0] == "l" and black:
                a, b = it[1], it[2]
                if abs(a.y - b.y) < 0.6:
                    if abs(b.x - a.x) > 300:
                        rules.append(a.y)
                    else:
                        hl.append((min(a.x, b.x), max(a.x, b.x), a.y))
                else:
                    sl.append((a.x, a.y, b.x, b.y))
            elif it[0] == "c" and black:
                pts = [it[1], it[2], it[3], it[4]]
                cv.append((min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts)))
    return hl, sl, cv, sorted(rules)


def page_struct(page, pn):
    sp = spans_of(page)
    H = page.rect.height
    body = [s for s in sp if 70 < s["y"] < H - 25 and not (s["y"] < 66)]
    # judul: tebal, berwarna (biru), diawali nomor; gabung span sebaris
    tsp = [s for s in body if is_bold(s["font"]) and s["size"] >= 11.5 and s["color"] not in (0, 0xffffff)]
    titles = []
    for s in sorted(tsp, key=lambda s: (s["y"], s["x0"])):
        if titles and abs(titles[-1]["y"] - s["y"]) < 2:
            titles[-1]["t"] += s["text"]; continue
        if TITLE_RE.match(s["text"]):
            titles.append({"y": s["y"], "t": s["text"]})
    cats = [s for s in body if "Comic" in s["font"]]
    hl, sl, cv, rules = drawings_of(page)
    regions = []
    y0 = 70
    if titles:
        if any(s["y"] < titles[0]["y"] - 3 and s["y"] > 70 and is_bold(s["font"]) and s["color"] == 0 and s["size"] >= 12
               and set(s["text"]) - set(" ") <= NOTE_CH for s in body):
            regions.append((70, titles[0]["y"] - 25, None))
        for i, t in enumerate(titles):
            nxt = titles[i + 1]["y"] - 25 if i + 1 < len(titles) else H
            regions.append((t["y"] - 2, nxt, t))
    else:
        regions.append((70, H, None))
    out = []
    for ra, rb, t in regions:
        r = region_struct([s for s in body if ra <= s["y"] < rb], t, hl, sl, cv, rules, pn)
        cs = [c for c in cats if (t and t["y"] - 60 < c["y"] < t["y"]) or (not t and c["y"] < 140)]
        if cs and t:
            r["cat"] = cs[-1]["text"].strip()
        out.append(r)
    return out


def region_struct(body, title, hl, sl, cv, rules, pn):
    res = {"p": pn, "title": title["t"].strip() if title else None, "cat": None, "keyline": None, "logu": None, "composer": None,
           "ayat": [], "systems": [], "text": [], "credit": [], "warn": []}
    if title:
        ty = title["y"]
        head = [s for s in body if ty + 3 < s["y"] < ty + 24]
        hs = sorted(head, key=lambda s: (round(s["y"] / 4), s["x0"]))
        KF = ("Calibri", "Euphemia", "Gadugi")
        res["keyline"] = re.sub(r"\s+", " ", "".join(s["text"] for s in hs if any(k in s["font"] for k in KF))).strip()
        alltxt = " ".join(s["text"] for s in hs)
        m = re.search(r"Logu\s*:?\s*([0-9]+[a-z]?)", alltxt)
        res["logu"] = m.group(1) if m else None
        if not res["logu"]:
            lg = [s for s in hs if "Logu" in s["text"]]
            if lg:
                L = lg[0]
                cand = [s for s in hs if s is not L and re.fullmatch(r"\s*\d+[a-z]?\s*", s["text"]) and 0 <= s["x0"] - L["x1"] < 90 and abs(s["y"] - L["y"]) < 5]
                if cand:
                    res["logu"] = min(cand, key=lambda s: s["x0"])["text"].strip()
        def orange(c):
            r_, g_, b_ = c >> 16, (c >> 8) & 255, c & 255
            return r_ > 180 and 70 < g_ < 160 and b_ < 80
        res["composer"] = re.sub(r"\s+", " ", " ".join(s["text"] for s in hs if orange(s["color"]))).strip() or None
        other = " ".join(s["text"] for s in hs if not orange(s["color"]) and not any(k in s["font"] for k in KF))
        other = re.sub(r"Buku\s*Logu\s*:?\s*[0-9]+[a-z]?", "", other).strip()
        res["ref"] = re.sub(r"\s+", " ", other) or None
        # keterangan kecil di samping judul (mis. ayat Alkitab)
        res["note"] = " ".join(s["text"].strip() for s in body if abs(s["y"] - ty) < 6 and not is_bold(s["font"])) or None
        if res["note"] and re.search(r"\[\s*\]?\s*$", res["title"]):
            res["title"] = re.sub(r"\[\s*\]?\s*$", "[" + res["note"] + "]", res["title"]); res["note"] = None
        elif res["note"] and re.fullmatch(r"\d+", res["note"]):
            res["title"] += " [" + res["note"] + "]"; res["note"] = None
        rest = [s for s in body if s["y"] >= ty + 6 and s not in head and abs(s["y"] - ty) >= 6]
    else:
        ty = 60
        rest = list(body)
    for s in rest:
        m = re.match(r"^\s*Ayat\s+(\d+)\s*([A-Z])?\s*$", s["text"])
        if m and s["size"] <= 11.5 and s["x0"] < 95:
            res["ayat"].append({"n": int(m.group(1)), "y": s["y"], "suf": m.group(2) or ""})
    rest = [s for s in rest if not (re.match(r"^\s*Ayat\s+\d", s["text"]) and s["size"] <= 11.5 and s["x0"] < 95) and "Comic" not in s["font"]]
    note_sp = [s for s in rest if is_bold(s["font"]) and s["color"] == 0 and s["size"] >= 11.5
               and set(s["text"]) - set(" ") <= NOTE_CH | {"\u00a0"}]
    rows = collections.defaultdict(list)
    for s in note_sp:
        key = next((k for k in rows if abs(k - s["y"]) < 2), s["y"])
        rows[key].append(s)
    # garis birama/angka yang ditulis tidak tebal, sebaris dengan baris not
    for s in rest:
        if s in note_sp or s["color"] != 0 or s["size"] < 11.5:
            continue
        if set(s["text"]) - set(" ") <= NOTE_CH | {"\u00a0"}:
            key = next((k for k in rows if abs(k - s["y"]) < 2), None)
            if key is not None:
                rows[key].append(s); note_sp.append(s)
    ys = sorted(rows)
    used = set()
    other_sp = [s for s in rest if s not in note_sp]
    for i, y in enumerate(ys):
        chars = sorted([c for s in rows[y] for c in s["chars"]], key=lambda c: c[1])
        toks = note_tokens(chars)
        top = min(s["top"] for s in rows[y])
        fs = max(s["size"] for s in rows[y])
        ny = ys[i + 1] if i + 1 < len(ys) else 1e9
        # garis atas: di atas angka (antara top-9 dan top+3)
        ovs = sorted({(round(a, 1), round(b, 1), round(yy, 1)) for a, b, yy in hl if y - 1.2 * fs < yy < y - 0.6 * fs and b - a < 200})
        ded = []
        for o in ovs:  # buang garis kembar
            if not any(abs(o[0] - d[0]) < 1 and abs(o[1] - d[1]) < 1 and abs(o[2] - d[2]) < 1 for d in ded):
                ded.append(o)
        ovs = ded
        for t in toks:
            if t["k"] in ("n", "dot"):
                t["ov"] = [i for i, (a, b, yy) in enumerate(ovs) if t["x1"] >= a - 6 and t["x0"] <= b - 1]
        # coretan: garis miring yang memotong angka
        for (x1_, y1_, x2_, y2_) in sl:
            ylo, yhi = min(y1_, y2_), max(y1_, y2_)
            if not (y - 1.3 * fs < ylo and yhi < y + 4):
                continue
            mx = (x1_ + x2_) / 2
            for t in toks:
                if t["k"] == "n" and t["x0"] - 3 <= mx <= t["x1"] + 3:
                    # "/" naik ke kanan = kres; "\" turun ke kanan = mol
                    (xl, yl), (xr, yr) = sorted([(x1_, y1_), (x2_, y2_)])
                    t["acc"] = 1 if yr < yl else -1
        # legato: kurva di sekitar baris not (bawah angka sampai sebelum lirik)
        segs = sorted({(round(a, 1), round(b, 1), round(y0)) for a, b, y0, y1 in cv if y - 0.55 * fs < y0 and y1 < y + 9 and b - a > 2})
        slurs = []
        for a, b, y0 in segs:  # gabung potongan kurva yang bersambung
            if slurs and abs(slurs[-1][1] - a) < 1.5 and abs(slurs[-1][2] - y0) < 4:
                slurs[-1][1] = max(slurs[-1][1], b)
            elif slurs and a >= slurs[-1][0] - 0.5 and b <= slurs[-1][1] + 0.5:
                continue
            else:
                slurs.append([a, b, y0])
        slurs = [(a, b) for a, b, _ in slurs if b - a > 6]
        # tanda triol: angka kecil "3" di atas baris not
        tri = [round((s["x0"] + s["x1"]) / 2, 1) for s in other_sp if s["text"].strip() == "3" and s["size"] < 10
               and y - 2.6 * fs < s["y"] < y - 0.5 * fs]
        # volta (ulangan 1/2): teks garis putus "/---- 1 ----\\" di atas baris not
        volta = []
        for s in other_sp:
            if "---" in s["text"] and y - 2.8 * fs < s["y"] < y - 0.6 * fs:
                cs = [c for c in s["chars"] if not c[0].isspace()]
                cur = None
                for c, x0, x1 in cs:
                    if c == "/" or cur is None:
                        cur = {"x0": x0, "x1": x1, "n": None, "open": c == "/", "close": False}
                        volta.append(cur)
                        if c == "/":
                            continue
                    cur["x1"] = x1
                    if c.isdigit():
                        cur["n"] = int(c)
                    if c == "\\":
                        cur["close"] = True; cur = None
        slurs = [(a, b) for a, b in slurs if not any(a - 4 <= t <= b + 4 for t in tri)]
        for s in other_sp:
            if (s["text"].strip() == "3" and s["size"] < 10) or ("---" in s["text"] and y - 2.8 * fs < s["y"] < y - 0.6 * fs):
                used.add(id(s))
        # lirik: span biasa di bawah baris not sampai baris not berikutnya
        rl = [ry for ry in rules if ry > y + 3]
        lim = min(ny - 8, y + 70, (rl[0] + 2) if rl else 1e9)
        lyr = [s for s in other_sp if y + 3 < s["y"] < lim and not is_bold(s["font"]) and s["size"] >= 12
               and s["x1"] >= 70]
        lrows = collections.defaultdict(list)
        for s in lyr:
            key = next((k for k in lrows if abs(k - s["y"]) < 2.5), s["y"])
            lrows[key].append(s)
        lys = sorted(lrows)
        # hentikan pada celah besar (teks ayat di bawah sistem terakhir)
        keep = []
        prev = y
        for ly in lys:
            if ly - prev > 24:
                break
            keep.append(ly); prev = ly
        lines = []
        for ly in keep:
            chars2 = sorted([c for s in lrows[ly] for c in s["chars"]], key=lambda c: c[1])
            lines.append({"y": ly, "w": words_of(chars2)})
            for s in lrows[ly]:
                used.add(id(s))
        res["systems"].append({"y": y, "top": round(top, 1), "toks": toks, "ovs": ovs, "slurs": [(round(a, 1), round(b, 1)) for a, b in slurs], "lyr": lines, "tri": tri, "volta": volta})
    # sisanya: teks ayat & kredit
    last_y = max([sy["lyr"][-1]["y"] if sy["lyr"] else sy["y"] for sy in res["systems"]], default=0)
    for s in sorted(other_sp, key=lambda s: (s["y"], s["x0"])):
        if id(s) in used or s["y"] <= last_y + 2:
            continue
        it = "Italic" in s["font"]
        res["credit" if it else "text"].append({"y": s["y"], "x": round(s["x0"], 1), "size": s["size"], "t": s["text"]})
    return res


def main():
    doc = pymupdf.open(PDF)
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    b = int(sys.argv[2]) if len(sys.argv) > 2 else len(doc)
    pages = []
    for pn in range(a, b + 1):
        pages.extend(page_struct(doc[pn - 1], pn))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(pages, open(OUT if len(sys.argv) < 4 else sys.argv[3], "w"), ensure_ascii=False)
    print(f"{len(pages)} halaman → {OUT}")


if __name__ == "__main__":
    main()
