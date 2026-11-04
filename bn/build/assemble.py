#!/usr/bin/env python3
"""Tahap 2: work/pages.json → work/bn/NNN.json (format sumber sama dengan Buku Ende).

- lagu = wilayah berjudul + wilayah lanjutan tanpa judul
- blok not per "Ayat N"; ayat lain dari teks bernomor
- ketukan: sel = 1 ketuk; garis atas = ½ (dua garis = ¼); "." = tahan
- bagian dipisah pada tanda ulang (||: … :||), baris lirik ke-2 = putaran ulang
- not tanpa suku kata = melisma → disambung legato ke not sebelumnya
- suku kata digabung jadi kata memakai kamus dari teks ayat seluruh buku
"""
import collections, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(HERE, "work", "pages.json")
OUTD = os.path.join(HERE, "work", "bn")
TITLE_RE = re.compile(r"^\s*(\d+)\s*([a-z])?\s*(?:\.|\s)\s*(.*)$")
KEYMAP = {"C": "C", "D": "D", "E": "E", "F": "F", "G": "G", "A": "A", "B": "B", "Bes": "Bb", "Es": "Eb", "As": "Ab",
          "Des": "Db", "Ges": "Gb", "Fis": "F#", "Bb": "Bb", "Eb": "Eb", "Ab": "Ab"}
CLITIC = ("nya", "mu", "ku", "lah", "kah", "pun")
PUNCT = ",.;:!?"


def norm(s):
    return s.replace("’", "'").replace("‘", "'").replace("`", "'")


# ---------------- kamus kata ----------------
def build_dict(regions):
    D = collections.Counter()
    for r in regions:
        for t in r["text"]:
            if t["size"] < 11:
                continue
            for w in re.findall(r"[A-Za-z']+", norm(t["t"])):
                w = w.strip("'").lower()
                if len(w) >= 2:
                    D[w] += 1
        if r["title"]:
            for w in re.findall(r"[A-Za-z']+", norm(r["title"])):
                D[w.strip("'").lower()] += 1
    return D


def join_syllables(syls, D):
    """syls: daftar suku kata (bisa '_'); kembalikan string baris: kata-kata, suku kata dipisah '-'."""
    out, seg = [], []
    def flush():
        if seg:
            out.extend(segment(seg, D))
        seg.clear()
    for s in syls:
        if s == "_":
            flush(); out.append("_")
        else:
            seg.append(s)
    flush()
    return " ".join(out)


def clean(s):
    return norm(s).strip(PUNCT + "\"“”()").lower().strip("'")


PREF = ("se", "ber", "be", "me", "mem", "men", "meng", "meny", "ter", "pe", "per", "pen", "peng")  # "di"/"ke" tidak: sering kata depan
SUF = ("", "nya", "mu", "ku", "lah", "kah", "kan", "an", "i", "kannya", "kanlah", "annya", "nyalah")


def known_affixed(w, D):
    for p in PREF:
        if w.startswith(p):
            r = w[len(p):]
            for sf in SUF:
                if sf and not r.endswith(sf):
                    continue
                base = r[:len(r) - len(sf)] if sf else r
                if len(base) >= 3 and D.get(base, 0) >= 2:
                    return True
    for sf in SUF[1:]:
        if w.endswith(sf) and D.get(w[:-len(sf)], 0) >= 2 and len(w) - len(sf) >= 3:
            return True
    return False


def segment(syl, D):
    n = len(syl)
    best = [(-1e9, None)] * (n + 1)
    best[0] = (0, None)
    for i in range(n):
        if best[i][0] <= -1e8:
            continue
        for j in range(i + 1, min(n, i + 7) + 1):
            part = syl[i:j]
            # tanda baca di tengah kata → tidak boleh
            if any(p and p[-1] in PUNCT for p in part[:-1]):
                break
            if j - i > 1 and (part[0].startswith("'") or any(p.startswith("'") for p in part[1:])):
                break
            if j - i > 1 and any(p[:1].isupper() and clean(p) not in CLITIC for p in part[1:]):
                break
            w = "".join(clean(p) for p in part)
            k = j - i
            if w in D:
                sc = k * k + 0.1 * math.log(D[w])
            elif k > 1 and any(w.endswith(c) and w[:-len(c)] in D for c in CLITIC):
                sc = k * k - 0.5
            elif k > 2 and any(w.endswith(c1 + c2) and w[:-len(c1 + c2)] in D for c1 in ("kan", "an", "i") for c2 in ("lah", "nya", "mu", "ku")):
                sc = k * k - 1
            elif k > 1 and known_affixed(w, D):
                sc = k * k - 1
            elif k == 1:
                sc = -2
            else:
                continue
            if best[i][0] + sc > best[j][0]:
                best[j] = (best[i][0] + sc, i)
    words, j = [], n
    while j > 0:
        i = best[j][1]
        words.append("-".join(syl[i:j]))
        j = i
    return words[::-1]


# ---------------- kepala lagu ----------------
def parse_keyline(kl):
    kl = kl or ""
    m = re.match(r"\s*([A-G](?:es|is|s|b)?)\s*=", kl)
    key = KEYMAP.get(m.group(1)) if m else None
    m = re.search(r"(\d+)(?:\s*&\s*(\d+))?\s*[Kk]etuk", kl)
    beats = int(m.group(1)) if m else None
    alt = int(m.group(2)) if m and m.group(2) else None
    m = re.search(r"=\s*(\d+)\s*$", kl) or re.search(r"[ᖱ♩♪]\s*=\s*(\d+)", kl)
    tempo = int(m.group(1)) if m else None
    return key, beats, alt, tempo


def meter_of(n):
    if n is None:
        return "4/4"
    return f"{n}/8" if n in (6, 9, 12) else f"{n}/4"


# ---------------- konversi blok not ----------------
def assign_lyrics(sysm, warn):
    """pasang kata lirik ke not (tiap baris lirik = satu jalur)."""
    notes = [t for t in sysm["toks"] if t["k"] == "n" and t["deg"] != 0]
    for li, line in enumerate(sysm["lyr"]):
        occ = {}
        for w in line["w"]:
            if not notes:
                warn.append(f"lirik tanpa not: {w['t']}"); continue
            order = sorted(range(len(notes)), key=lambda i: abs(w["xa"] - notes[i]["x0"]))
            i = order[0]
            if i in occ:
                # geser ke not bebas terdekat di sisi yang sesuai
                cand = [k for k in order[1:4] if k not in occ and abs(w["xa"] - notes[k]["x0"]) < 40]
                if cand:
                    i = cand[0]
                else:
                    warn.append(f"dua suku kata di satu not: {occ[i]['t']} + {w['t']}")
                    notes[i].setdefault("syl", {})[str(li)] += " " + w["t"]; continue
            occ[i] = w
            notes[i].setdefault("syl", {})[str(li)] = w["t"]


def beats_of(toks, warn):
    """kelompokkan token not/titik jadi ketuk memakai garis atas yang sama."""
    out, i = [], 0
    while i < len(toks):
        t = toks[i]
        if t["k"] not in ("n", "dot") or not t.get("ov"):
            out.append([t]); i += 1; continue
        grp, segs = [t], set(t["ov"])
        j = i + 1
        while j < len(toks) and toks[j]["k"] in ("n", "dot") and toks[j].get("ov") and segs & set(toks[j]["ov"]):
            grp.append(toks[j]); segs |= set(toks[j]["ov"]); j += 1
        out.append(grp); i = j
    return out


def encode_beat(grp, warn, tri=()):
    """kembalikan (bagian, eksplisit). eksplisit: durasi tiap elemen ditulis dgn '/' (½) atau '//' (¼)."""
    lv = [len(e.get("ov") or []) for e in grp]
    if len(grp) == 1 and lv[0] == 0:
        return [[e] for e in grp], False
    if len(set(lv)) == 1 and ((len(grp) == 2 and lv[0] == 1) or (len(grp) == 4 and lv[0] == 2)):
        return [[e] for e in grp], False
    tot = sum(2.0 ** -l for l in lv)
    if len(grp) == 3 and set(lv) == {1}:
        if any(grp[0]["x0"] - 10 <= t <= grp[-1]["x1"] + 10 for t in tri):
            return [[e] for e in grp], False  # triol: tiga not dalam satu ketuk
        warn.append("tiga not ½ ketuk di bawah satu garis atas (tanpa tanda 3)")
    elif abs(tot - round(tot)) > 1e-6 and len(grp) > 1:
        warn.append(f"kelompok garis atas berdurasi {tot} ketuk")
    for e, l in zip(grp, lv):
        e["_lv"] = l
    return [[e] for e in grp], True


def elem_code(e, slur_open, slur_close, explicit=False):
    if e["k"] == "dot":
        c = "."
    else:
        acc = "#" if e.get("acc", 0) > 0 else "b" if e.get("acc", 0) < 0 else ""
        o = e.get("oct", 0)
        c = acc + str(e["deg"]) + ("'" * o if o > 0 else "," * (-o))
    if explicit:
        c += "/" * e.get("_lv", 0)
    return ("(" if slur_open else "") + c + (")" if slur_close else "")


def block_events(block, warn):
    """blok (daftar sistem) → daftar event: ('beat', [[elem..],..], mode, sys) / ('bar', tok, sys)"""
    ev = []
    for si, sysm in enumerate(block["systems"]):
        assign_lyrics(sysm, warn)
        toks = [t for t in sysm["toks"] if t["k"] in ("n", "dot", "bar")]
        for t in sysm["toks"]:
            if t["k"] == "?":
                warn.append(f"karakter tak dikenal {t['t']!r}")
        # legato tergambar
        notes = [t for t in toks if t["k"] == "n"]
        for a, b in sysm.get("slurs", []):
            st = [t for t in notes if t["x0"] <= a + 3]
            en = [t for t in notes if t["x0"] <= b + 2]
            if st and en and st[-1] is not en[-1]:
                st[-1].setdefault("sl_start", 0); st[-1]["sl_start"] += 1
                en[-1].setdefault("sl_end", 0); en[-1]["sl_end"] += 1
        seq = []
        for t in toks:
            if t["k"] == "bar":
                ev.append(("bar", t["t"], si))
            else:
                seq.append(t)
                continue
        # bangun ulang dengan ketukan (bar memotong grup)
    ev = []
    for si, sysm in enumerate(block["systems"]):
        toks = [t for t in sysm["toks"] if t["k"] in ("n", "dot", "bar")]
        for t in toks:
            cx = (t["x0"] + t["x1"]) / 2
            for v in sysm.get("volta", []):
                if v.get("n") and v["x0"] - 4 <= cx <= v["x1"] + 4:
                    t["vol"] = v["n"]
        run = []
        def flush():
            for grp in beats_of(run, warn):
                parts, mode = encode_beat(grp, warn, sysm.get("tri", []))
                ev.append(("beat", parts, mode, si))
            run.clear()
        for t in toks:
            if t["k"] == "bar":
                flush(); ev.append(("bar", t["t"], si))
            else:
                run.append(t)
        flush()
    return ev


def ev_vol(e):
    if e[0] == "bar":
        return None
    vs = [x.get("vol") for part in e[1] for x in part]
    return vs[0] if vs and all(v == vs[0] for v in vs) else None


def remap(x, p):
    """salinan elemen untuk putaran p (0/1): jalur lirik ke-p jadi jalur 0."""
    y = dict(x)
    def pick(d, pre):
        out = {}
        if not d:
            return out
        own = d.get(pre + str(p)) or d.get(pre + "0")
        if own is not None:
            out[pre + "0"] = own
        return out
    syl = x.get("syl") or {}
    ns = pick(syl, "")
    for k in {k.split("_")[0] for k in syl if k.startswith("x")}:
        ns.update(pick(syl, k + "_"))
    y["syl"] = ns
    y["_own"] = pick(x.get("_own") or {}, "")
    if x.get("xsyl"):
        xs = {}
        for vn in {k[0] for k in x["xsyl"]}:
            v = x["xsyl"].get((vn, p), x["xsyl"].get((vn, 0)))
            if v is not None:
                xs[(vn, 0)] = v
        y["xsyl"] = xs
    return y


def copy_ev(e, p):
    if e[0] == "bar":
        return e
    return ("beat", [[remap(x, p) for x in part] for part in e[1]], e[2], e[3])


def apply_volta(ev, warn):
    """||: A [1. B1 :||] [2. B2] → bagian A+B1 (putaran 1) lalu A+B2 (putaran 2)."""
    n = 0
    while True:
        v1 = next((k for k, e in enumerate(ev) if ev_vol(e) == 1 and not (e[0] == "beat" and e[1][0][0].get("_vdone"))), None)
        if v1 is None:
            return ev, n
        re_ = next((k for k in range(v1, len(ev)) if ev[k][0] == "bar" and ev[k][1] in (":||", ":|||", ":||:")), None)
        v2s = next((k for k in range(re_ + 1, len(ev)) if ev_vol(ev[k]) == 2), None) if re_ is not None else None
        if re_ is None or v2s is None or v2s - re_ > 2:
            warn.append("volta tidak lengkap (ulangan 1/2) — ditulis apa adanya")
            for e in ev:
                if e[0] == "beat":
                    for part in e[1]:
                        for x in part:
                            x["_vdone"] = True
            return ev, n
        rs = 0
        for k in range(v1 - 1, -1, -1):
            if ev[k][0] == "bar" and ev[k][1] in ("||:", ":||:", "SEC"):
                rs = k + 1; break
        v2e = v2s
        while v2e + 1 < len(ev) and (ev_vol(ev[v2e + 1]) == 2 or (ev[v2e + 1][0] == "bar" and v2e + 2 < len(ev) and ev_vol(ev[v2e + 2]) == 2)):
            v2e += 1
        if v2e + 1 < len(ev) and ev[v2e + 1][0] == "bar":
            v2e += 1
        pre = ev[rs:v1]
        b1 = [e for e in ev[v1:re_]]
        si = ev[re_][2]
        s1 = [copy_ev(e, 0) for e in pre + b1] + [("bar", "|", si), ("bar", "SEC", si)]
        s2 = [copy_ev(e, 1) for e in pre] + ev[v2s:v2e + 1]
        for e in s1 + s2:
            if e[0] == "beat":
                for part in e[1]:
                    for x in part:
                        x["_vdone"] = True
        ev = ev[:rs] + s1 + s2 + ev[v2e + 1:]
        n += 1


def split_sections(ev):
    secs, cur = [], []
    def close():
        if any(e[0] == "beat" for e in cur):
            secs.append(list(cur))
        cur.clear()
    for e in ev:
        if e[0] == "bar":
            t = e[1]
            if t in ("||:", "SEC"):
                close(); continue
            if t in (":||", ":|||", ":||:", "://"):
                cur.append(("bar", ":|", e[2])); close(); continue
            if t == "|||" or t == "||||":
                cur.append(("bar", "|]", e[2])); continue
            if t in ("|", "||"):
                cur.append(("bar", "|", e[2])); continue
            cur.append(("bar", "|", e[2]))
            continue
        cur.append(e)
    close()
    return secs


def sec_elems(sec):
    return [x for e in sec if e[0] == "beat" for part in e[1] for x in part]


def finish_section(sec, tracks_all, D, warn):
    """tentukan legato + baris lirik; kembalikan (notes_str, rows, n_targets)."""
    els = sec_elems(sec)
    notes = [x for x in els if x["k"] == "n"]
    tracks = sorted({k for x in notes for k in (x.get("syl") or {})})
    # interval legato dari gambar
    iv = []
    stack = []
    for i, x in enumerate(notes):
        for _ in range(x.get("sl_start", 0)):
            stack.append(i)
        for _ in range(x.get("sl_end", 0)):
            if stack:
                iv.append([stack.pop(), i])
    good = []
    for a, b in iv:
        if any(notes[k].get("syl") for k in range(a + 1, b + 1)):
            continue  # ada suku kata di dalam legato → abaikan legato
        good.append([a, b])
    # melisma: not tanpa suku kata (semua jalur) → sambung ke not sebelumnya
    cont = set()
    for a, b in good:
        cont.update(range(a + 1, b + 1))
    for i, x in enumerate(notes):
        if x["deg"] == 0 or i in cont or x.get("syl"):
            continue
        if not tracks:
            continue
        # cari not bukan-istirahat sebelumnya
        p = i - 1
        while p >= 0 and notes[p]["deg"] == 0:
            p -= 1
        if p < 0 or any(notes[k]["deg"] == 0 for k in range(p, i)):
            continue
        hit = next((g for g in good if g[1] == i - 1 or (g[0] <= p <= g[1] and g[1] >= p)), None)
        hit = next((g for g in good if g[1] == p), None)
        if hit:
            hit[1] = i
        else:
            good.append([p, i])
        cont.add(i)
    good.sort()
    opens = collections.Counter(a for a, b in good)
    closes = collections.Counter(b for a, b in good)
    idx = {id(x): i for i, x in enumerate(notes)}
    # rangkai teks not
    lines, cur_si, line = [], None, []
    open_now = False
    for e in sec:
        si = e[-1]
        if cur_si is None:
            cur_si = si
        if si != cur_si:
            lines.append(" ".join(line)); line = []; cur_si = si
        if e[0] == "bar":
            line.append(e[1]); continue
        parts, mode = e[1], e[2]
        codes = []
        for part in parts:
            pc = []
            for x in part:
                i = idx.get(id(x))
                o = i is not None and opens[i] > 0 and not open_now
                c = False
                if i is not None and closes[i] > 0 and (open_now or o):
                    c = True
                if o:
                    open_now = True
                # titik yang menutup legato: lewati (tutup di not)
                pc.append(elem_code(x, o, c, mode))
                if c:
                    open_now = False
            codes.append("".join(pc))
        line.append("+".join(codes))
    if line:
        lines.append(" ".join(line))
    for i, x in enumerate(notes):
        x["_cont"] = i in cont
    return "\n".join(lines)


def struct_sig(block):
    sig = []
    for s in block["systems"]:
        for t in s["toks"]:
            if t["k"] == "n":
                sig.append((t["deg"], t.get("oct", 0)))
            elif t["k"] == "dot":
                sig.append(".")
    return sig


# ---------------- teks ayat ----------------
def text_verses(regs, warn):
    """kumpulkan teks ayat bernomor (bisa dua kolom)."""
    verses = collections.OrderedDict()
    last = None
    for r in regs:
        marks = [t for t in r["text"] if t["size"] < 10 and re.fullmatch(r"\s*\d+\s*\.?\s*", t["t"])]
        lines = [t for t in r["text"] if t["size"] >= 11]
        misc = [t for t in r["text"] if t["size"] < 10 and t not in marks]
        for ln in sorted(lines, key=lambda t: (t["y"], t["x"])):
            cand = [m for m in marks if m["x"] - 2 < ln["x"] <= m["x"] + 45 and m["y"] - 6 <= ln["y"]]
            if cand:
                m = max(cand, key=lambda m: m["y"])
                n = int(re.sub(r"\D", "", m["t"]))
                key = n
            else:
                key = last
                if key is None:
                    warn.append(f"teks tanpa nomor ayat: {ln['t'][:40]}")
                    key = "?"
            verses.setdefault(key, []).append((r["p"], ln["y"], ln["x"], ln["t"].strip()))
            if cand:
                last = key
        for t in misc:
            if t["t"].strip():
                warn.append(f"teks kecil: {t['t'].strip()[:60]}")
    out = {}
    for k, v in verses.items():
        out[k] = [re.sub(r"\s+", " ", norm(x[3])) for x in v]
    return out


# ---------------- utama ----------------
def main():
    regs = json.load(open(PAGES))
    D = build_dict(regs)
    songs = collections.OrderedDict()
    cur = None
    for r in regs:
        if r["title"]:
            m = TITLE_RE.match(r["title"])
            n, v, t = int(m.group(1)), m.group(2) or "", m.group(3).strip()
            k = (n, v)
            if k not in songs:
                songs[k] = {"n": n, "v": v, "title": t, "regs": [], "head": r}
            cur = songs[k]
        elif cur is None:
            continue
        cur["regs"].append(r)
    os.makedirs(OUTD, exist_ok=True)
    stats = collections.Counter()
    allwarn = {}
    for (n, v), s in songs.items():
        warn = []
        hd = s["head"]
        key, beats, alt, tempo = parse_keyline(hd["keyline"])
        if not key:
            warn.append(f"kunci tidak terbaca: {hd['keyline']!r}")
        meter = meter_of(beats)
        # blok not per ayat
        blocks = []
        for r in s["regs"]:
            labels = sorted(r["ayat"], key=lambda a: a["y"])
            for sysm in r["systems"]:
                lab = [a for a in labels if a["y"] < sysm["y"] and not a.get("_used")]
                if lab:
                    for a in lab:
                        a["_used"] = True
                    blocks.append({"n": lab[-1]["n"], "systems": [sysm], "pages": [r["p"]]})
                elif not blocks:
                    blocks.append({"n": 1, "systems": [sysm], "pages": [r["p"]], "nolabel": True})
                else:
                    b = blocks[-1]
                    if r["title"] and r["p"] not in b["pages"] and any(t["t"] in ("|||", ":|||") for t in b["systems"][-1]["toks"]):
                        # halaman baru berjudul tanpa label, blok sebelumnya sudah selesai → ayat berikut
                        blocks.append({"n": b["n"] + 1, "systems": [sysm], "pages": [r["p"]], "guess": True})
                        warn.append(f"blok not hal. {r['p']} tanpa label ayat, dianggap ayat {b['n'] + 1}")
                    else:
                        b["systems"].append(sysm)
                        if r["p"] not in b["pages"]:
                            b["pages"].append(r["p"])
        tv = text_verses(s["regs"], warn)
        credits = [re.sub(r"\s+", " ", c["t"]).strip() for r in s["regs"] for c in r["credit"] if c["t"].strip()]
        if not blocks:
            warn.append("tidak ada not"); stats["tanpa not"] += 1
            allwarn[f"{n}{v}"] = warn
            continue
        base = blocks[0]
        h_volta = 0
        sig0 = struct_sig(base)
        ev = block_events(base, warn)
        # ayat lain yang ditulis di not: gabung suku katanya bila struktur sama
        extra = []
        for b in blocks[1:]:
            if struct_sig(b) == sig0:
                block_events(b, warn)  # pasang lirik
                extra.append(b)
            else:
                warn.append(f"not ayat {b['n']} (hal. {b['pages']}) beda dengan ayat {base['n']}; liriknya dipasang dari teks")
                stats["blok beda"] += 1
        # salin suku kata ayat lain ke elemen blok dasar dengan jalur bernomor ayat*10+jalur
        if extra:
            bel = [t for sy in base["systems"] for t in sy["toks"] if t["k"] == "n"]
            for b in extra:
                xel = [t for sy in b["systems"] for t in sy["toks"] if t["k"] == "n"]
                for a_, x_ in zip(bel, xel):
                    for tr, sy in (x_.get("syl") or {}).items():
                        a_.setdefault("xsyl", {})[(b["n"], int(tr))] = sy
        # jalur gabungan untuk menentukan melisma: semua ayat bernot
        for x in [t for sy in base["systems"] for t in sy["toks"] if t["k"] == "n"]:
            x["_own"] = dict(x.get("syl") or {})
            if x.get("xsyl"):
                x.setdefault("syl", {})
                for (vn, tr), sy in x["xsyl"].items():
                    x["syl"][f"x{vn}_{tr}"] = sy
        ev, nvol = apply_volta(ev, warn)
        if nvol:
            h_volta = nvol
        secs = split_sections(ev)
        sections, vnot = [], {}
        for sec in secs:
            # rows hanya dari jalur ayat dasar; ayat lain diambil terpisah
            els = [x for x in sec_elems(sec) if x["k"] == "n"]
            notes_str = finish_section(sec, None, D, warn)
            # pisahkan rows per ayat
            own_tr = sorted({int(k) for x in els for k in x.get("_own", {})})
            xs = collections.defaultdict(set)
            for x in els:
                for (vn, tr) in (x.get("xsyl") or {}):
                    xs[vn].add(tr)
            tr_order = [str(t) for t in own_tr] + [f"x{vn}_{tr}" for vn in sorted(xs) for tr in sorted(xs[vn])]
            # finish_section menyusun rows urut jalur numerik; susun ulang manual
            rows = section_rows(sec, D, tr_order)
            own = [rows[t] for t in tr_order if not t.startswith("x") and rows.get(t)]
            sections.append({"notes": notes_str, "rows": own})
            for vn in xs:
                vnot.setdefault(vn, []).append([rows[f"x{vn}_{tr}"] for tr in sorted(xs[vn]) if rows.get(f"x{vn}_{tr}")])
        # ayat
        def vtext(rowsets):
            return [re.sub(r"\s+", " ", re.sub(r"(?:^|\s)_(?=\s|$)", " ", r).replace("-", "")).strip() for rs in rowsets for r in rs]
        verses = {base["n"]: vtext([sec["rows"] for sec in sections])}
        vl_direct = {}
        for b in extra:
            vn = b["n"]
            rs = vnot.get(vn, [])
            if len(rs) == len(sections) and all(len(r) == len(sec["rows"]) for r, sec in zip(rs, sections)):
                verses[vn] = vtext(rs)
                vl_direct[vn] = {"r": rs, "c": 0, "n": [f"lirik ayat {vn} tertulis di not (hal. {', '.join(map(str, b['pages']))})"]}
            else:
                verses[vn] = vtext(rs)
                warn.append(f"ayat {vn} di not: jumlah baris lirik beda dengan ayat {base['n']}")
        for k, lines in tv.items():
            if k == "?":
                continue
            if k in verses:
                warn.append(f"ayat {k} ada di not dan di teks")
                continue
            verses[k] = lines
        if "?" in tv:
            verses.setdefault(max(verses) + 1 if verses else 2, tv["?"])
        order = sorted(verses)
        if order != list(range(1, len(order) + 1)):
            warn.append(f"nomor ayat: {order}")
        pages = sorted({r["p"] for r in s["regs"]})
        h = {"be": n, "variant": v, "bl": (int(hd["logu"]) if str(hd["logu"]).isdigit() else hd["logu"]) if hd.get("logu") else None,
             "title": norm(s["title"]), "key": key or "C", "meter": meter, "credit": hd.get("composer") or "",
             "pages": pages, "cat": hd.get("cat"), "tempo": tempo, "credits": credits,
             "sections": sections, "verses": [verses[k] for k in order], "vnum": order,
             "checks": [], "status": ""}
        if alt:
            h["checks"].append(f"Birama berganti: {beats} & {alt} ketuk (lihat buku).")
        if hd.get("ref"):
            h["ref"] = hd["ref"]
        h["vl_direct"] = {str(order.index(k)): v_ for k, v_ in vl_direct.items()}
        if alt:
            h["meter2"] = alt
        if h_volta:
            h["checks"].append("Ulangan dengan kurung 1./2. (volta) di buku ditulis sebagai dua bagian: putaran 1 lalu putaran 2.")
        fix_bars(h)
        apply_fix(h)
        h["warn"] = warn
        stats["lagu"] += 1
        json.dump(h, open(os.path.join(OUTD, f"{n:03d}{v}.json"), "w"), ensure_ascii=False, indent=1)
        if warn:
            allwarn[f"{n}{v}"] = warn
    json.dump(allwarn, open(os.path.join(HERE, "work", "assemble_warn.json"), "w"), ensure_ascii=False, indent=1)
    print(dict(stats), "lagu dgn peringatan:", len(allwarn))


def apply_fix(h):
    """koreksi manual (hasil periksa terhadap gambar halaman): work/fix/<id>.json menimpa field yang ada."""
    f = os.path.join(HERE, "work", "fix", f"{h['be']:03d}{h['variant']}.json")
    if not os.path.exists(f):
        return
    fx = json.load(open(f))
    for k, v in fx.items():
        if k == "note":
            for n in (v if isinstance(v, list) else [v]):
                h["checks"].append("Koreksi dari gambar halaman: " + n)
        elif k == "vl_direct":
            h["vl_direct"] = v
        else:
            h[k] = v
    h["fixed"] = True


def tok_dur(tok):
    EL = re.compile(r"^(\()?([#b])?([0-7.])([',]*)(/*)(\))?$")
    parts = tok.split("+")
    ms = [EL.match(p) for p in parts]
    if any(m is None for m in ms):
        return 1.0
    if any(m.group(5) for m in ms):
        return sum(0.5 ** len(m.group(5)) if m.group(5) else 1.0 / len(parts) for m in ms)
    return 1.0


def bar_lens(h):
    out = []
    for s in h["sections"]:
        cur, bl = 0, []
        for t in s["notes"].split():
            if t in ("|", ":|", "|]"):
                bl.append(cur); cur = 0; continue
            cur += tok_dur(t)
        if cur:
            bl.append(cur)
        out.append(bl)
    return out


def fix_bars(h):
    """birama dari data bila kepala lagu tidak cocok; garis birama yang tidak tertulis ditambahkan."""
    num = int(h["meter"].split("/")[0])
    allowed = {num, h.get("meter2") or num}
    inner = [x for bl in bar_lens(h) for x in bl[1:-1]]
    if inner:
        c = collections.Counter(inner)
        mode, cnt = c.most_common(1)[0]
        if mode not in allowed and cnt >= 0.6 * len(inner) and float(mode).is_integer():
            old = h["meter"]
            den = h["meter"].split("/")[1]
            h["meter"] = f"{int(mode)}/{den}"
            h["checks"].append(f"Kepala lagu di buku menulis {old.split('/')[0]} ketuk, tetapi {cnt} dari {len(inner)} birama berisi {int(mode)} ketuk → birama ditulis {h['meter']}.")
            num = int(mode); allowed = {num, h.get("meter2") or num}
    added = 0
    for s in h["sections"]:
        lines = s["notes"].split("\n")
        new = []
        for ln in lines:
            toks = ln.split()
            out, cur, buf = [], 0, []
            for t in toks:
                if t in ("|", ":|", "|]"):
                    out.extend(split_bar(buf, num, allowed) if buf else [])
                    if split_bar.added:
                        added += split_bar.added
                    out.append(t); buf = []; continue
                buf.append(t)
            if buf:
                out.extend(split_bar(buf, num, allowed))
                added += split_bar.added
            new.append(" ".join(out))
        s["notes"] = "\n".join(new)
    if added:
        h["checks"].append(f"{added} garis birama tidak tertulis di buku (birama berisi {num * 2} ketuk) — ditambahkan agar birama {h['meter']} terbaca benar.")


def split_bar(buf, num, allowed):
    split_bar.added = 0
    tot = sum(tok_dur(t) for t in buf)
    if abs(tot - 2 * num) > 1e-6 or (2 * num) in allowed:
        return buf
    acc = 0
    for i, t in enumerate(buf):
        acc += tok_dur(t)
        if abs(acc - num) < 1e-6 and i + 1 < len(buf):
            split_bar.added = 1
            return buf[:i + 1] + ["|"] + buf[i + 1:]
    return buf


def section_rows(sec, D, tr_order):
    """baris lirik per jalur untuk satu bagian (setelah finish_section menentukan legato)."""
    els = sec_elems(sec)
    notes = [x for x in els if x["k"] == "n"]
    # target = not yang dirangkai tanpa ")"-lanjutan: hitung ulang dari kode legato
    targets = [x for x in notes if x["deg"] != 0 and not x.get("_cont")]
    out = {}
    for tr in tr_order:
        syls = [(x.get("syl") or {}).get(tr) or "_" for x in targets]
        if all(s == "_" for s in syls):
            continue
        out[tr] = join_syllables(syls, D)
    return out


if __name__ == "__main__":
    main()
