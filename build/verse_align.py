#!/usr/bin/env python3
"""Pecah lirik ayat 2 dst menjadi suku kata dan pasang ke not, memakai ayat 1 sebagai pola.

Ayat 1 sudah dipecah per suku kata di baris ">" (dicek manual terhadap not). Untuk ayat k:
  1. teks ayat dibersihkan: ":,: X :,:" diulang dua kali, "(2x)" mengulang baris, penanda
     refrein ("d.u.", "Ref.: ...", "Sai...") diganti sisa lirik ayat 1 mulai dari kata isyaratnya;
  2. tiap kata diberi beberapa kemungkinan pemecahan suku kata: dari kamus (semua kata ayat 1 di
     866 lagu) dan dari aturan suku kata Batak Toba (V, KV, KVK; "ng" satu konsonan);
  3. pemrograman dinamis memilih pemecahan yang jumlah suku katanya pas dengan slot not, dengan
     biaya: kata di luar kamus/varian gabung vokal, kata yang terpotong di batas baris, suku kata
     di slot tahan "_" ayat 1. Hanya hasil pas tepat yang dipakai; selain itu ayat ditandai
     "belum dicocokkan".
"""
import re, collections

VOW = set("aeiouéèêëäöüAEIOUÉÈÊËÄÖÜ")
ONSET2 = {"tr", "pr", "br", "kr", "gr", "dr", "pl", "bl", "kl", "gl", "fl", "fr", "sy", "kh"}


def norm(w):
    return re.sub(r"[^a-zà-ÿ]", "", w.lower())


def units(cons):
    """pecah gugus konsonan menjadi satuan; ng dan ny satu satuan"""
    out, i = [], 0
    while i < len(cons):
        if cons[i:i + 2] in ("ng", "ny"):
            out.append(cons[i:i + 2]); i += 2
        else:
            out.append(cons[i]); i += 1
    return out


def rule_split(letters):
    """pemecahan dasar: setiap vokal satu inti suku kata. Mengembalikan panjang tiap suku kata."""
    s = letters
    nuc = [i for i, ch in enumerate(s) if ch in VOW]
    if not nuc:
        return [len(s)] if s else []
    cuts = []
    for a, b in zip(nuc, nuc[1:]):
        cl = s[a + 1:b]
        if not cl:
            cuts.append(b); continue
        u = units(cl)
        if len(u) == 1:
            cuts.append(a + 1)
        elif len(u) >= 2 and (u[-2] + u[-1]) in ONSET2 and len(u[-2]) == 1:
            cuts.append(b - len(u[-1]) - len(u[-2]))
        else:
            cuts.append(b - len(u[-1]))
    bounds = [0] + cuts + [len(s)]
    return [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]


def merge_variants(letters, lens):
    """varian: dua vokal berdampingan (ai, au, ia, ua, ...) dinyanyikan satu suku kata."""
    out = {tuple(lens): 0}
    pos, joins = 0, []
    for i in range(len(lens) - 1):
        pos += lens[i]
        if letters[pos - 1] in VOW and letters[pos] in VOW and len(lens) > 1:
            joins.append(i)
    for mask in range(1, 1 << len(joins)):
        sel = [joins[j] for j in range(len(joins)) if mask >> j & 1]
        if any(b - a == 1 for a, b in zip(sel, sel[1:])):
            continue  # jangan gabung tiga vokal
        new, i = [], 0
        while i < len(lens):
            if i in sel:
                new.append(lens[i] + lens[i + 1]); i += 2
            else:
                new.append(lens[i]); i += 1
        out[tuple(new)] = len(sel)
    return out


def build_dict(hymns):
    d = collections.defaultdict(collections.Counter)
    for h in hymns:
        for s in h["sections"]:
            for r in s["rows"]:
                for w in r.split():
                    if w == "_":
                        continue
                    syl = [norm(x) for x in w.split("-")]
                    if not all(syl) or not all(any(ch in VOW for ch in x) for x in syl):
                        continue
                    groups = len(re.findall(r"[aeiouéèêëäöü]+", "".join(syl)))
                    if len(syl) < groups:
                        continue  # kata tak dipecah di sumber (mis. "Jesus" satu slot) -> bukan pola
                    d["".join(syl)][tuple(len(x) for x in syl)] += 1
    return d


def options(word, D):
    """semua kemungkinan pemecahan kata: [(daftar suku kata asli, biaya)]"""
    L = norm(word)
    if not L:
        return None  # tanda baca saja
    idx = [i for i, ch in enumerate(word) if norm(ch)]  # posisi huruf di kata asli
    opts = {}
    if L in D:
        tot = sum(D[L].values())
        best = D[L].most_common(1)[0][1]
        rs = tuple(rule_split(L))
        for lens, n in D[L].items():
            opts[lens] = 0 if n == best else 0.3
        for lens, c in merge_variants(L, list(rs)).items():
            opts.setdefault(lens, 0.25 if c == 0 else 1.0 + c)
    else:
        for lens, c in merge_variants(L, rule_split(L)).items():
            opts[lens] = 0.2 + 1.0 * c
    out = []
    for lens, c in opts.items():
        parts, start, li = [], 0, 0
        for k, n in enumerate(lens):
            li += n
            end = idx[li - 1] + 1 if k < len(lens) - 1 else len(word)
            parts.append(word[start:end]); start = end
        out.append((parts, c))
    return out


def template(h):
    """slot ayat 1: daftar (bagian, baris, isi) — isi '_' = slot tahan"""
    T, ends = [], []
    for si, s in enumerate(h["sections"]):
        for ri, r in enumerate(s["rows"]):
            for w in r.split():
                if w == "_":
                    T.append((si, ri, "_"))
                else:
                    for x in w.split("-"):
                        T.append((si, ri, x))
            ends.append(len(T))
    return T, ends


def v1_words(h):
    """kata ayat 1 berurutan dengan posisi slot awalnya (untuk isyarat refrein)"""
    out, pos = [], 0
    for s in h["sections"]:
        for r in s["rows"]:
            for w in r.split():
                n = 1 if w == "_" else len(w.split("-"))
                if w != "_":
                    out.append((norm(w.replace("-", "")), pos))
                pos += n
    return out


REF_RE = re.compile(r"\b(?:d\.\s?u\.?|D\.\s?U\.?)\s*$|(?:\.\s?\.\s?\.|…)\s*$")
LABEL_RE = re.compile(r"^\s*Ref+\.?\s*:?\s*", re.I)


def clean_verse(lines):
    """gabung baris ayat jadi daftar kata; kembalikan (kata, ada_penanda_refrein, catatan)"""
    notes, text = [], []
    for l in lines:
        l = l.strip()
        m = re.search(r"\((\d)\s*[xX]\)\s*$", l)
        if m:
            n = int(m.group(1)); l = l[:m.start()].strip()
            text.append(" ".join([l] * n)); notes.append(f"baris diulang {n}x")
            continue
        l = re.sub(r"\((?:Koor|koor|\d+[a-z]?)\)", " ", l)
        text.append(l)
    t = " ".join(text)
    # :,: X :,: -> X X
    def rep(m):
        notes.append("bagian :,: diulang")
        return m.group(1) + " " + m.group(1)
    t = re.sub(r":,:\s*(.*?)\s*:,:", rep, t)
    if t.count(":,:") == 1:
        # satu penanda di awal baris terakhir = baris itu dinyanyikan dua kali
        a, _, b = t.partition(":,:")
        t = a + " " + b + " " + b
        notes.append("baris bertanda :,: diulang")
    if ":,:" in t:
        notes.append("penanda :,: tidak berpasangan")
        t = t.replace(":,:", " ")
    refrain = False
    # Ref.: isyarat di baris terakhir
    m = re.search(r"\bRef+\.?\s*:?\s*", t, re.I)
    if m:
        refrain = True
        t = t[:m.start()] + " " + t[m.end():]
    m = REF_RE.search(t)
    if m:
        refrain = True
        t = t[:m.start()]
    if "[" in t or "…" in t:
        return None, refrain, notes + ["teks ayat tidak lengkap"]
    words = []
    for w in t.split():
        if not norm(w):
            if words: words[-1] = (words[-1][0] + w, words[-1][1])
            continue
        bits = [b for b in w.split("-") if b]
        bits = [b for b in bits if norm(b)] or bits
        for k, b in enumerate(bits):
            words.append((b, k < len(bits) - 1))
    return words, refrain, notes


def align(words, T, ends, D, tail=None):
    """DP: pasang suku kata kata-kata ke slot T. Kembalikan (biaya, daftar isi slot) atau None."""
    N, W = len(T), len(words)
    opts = [options(w, D) for w, _ in words]
    if any(o is None for o in opts):
        return None
    endset = set(ends)
    INF = float("inf")
    best = [[INF] * (N + 1) for _ in range(W + 1)]
    back = [[None] * (N + 1) for _ in range(W + 1)]
    best[0][0] = 0
    for w in range(W + 1):
        for j in range(N + 1):
            c0 = best[w][j]
            if c0 == INF:
                continue
            # slot tahan ayat 1 boleh tetap ditahan
            if j < N and T[j][2] == "_" and c0 < best[w][j + 1]:
                best[w][j + 1] = c0; back[w][j + 1] = ("hold",)
            if w == W:
                continue
            for oi, (parts, c) in enumerate(opts[w]):
                n = len(parts)
                if j + n > N:
                    continue
                cost = c0 + c
                # kata terpotong di batas baris lirik
                if any(j < e < j + n for e in endset):
                    cost += 2.0
                # suku kata jatuh di slot tahan ayat 1
                cost += 0.5 * sum(1 for k in range(j, j + n) if T[k][2] == "_")
                if cost < best[w + 1][j + n] - 1e-9:
                    best[w + 1][j + n] = cost; back[w + 1][j + n] = ("word", oi)
    if best[W][N] == INF:
        return None
    # telusur balik
    fill, w, j = [None] * N, W, N
    while w or j:
        b = back[w][j]
        if b[0] == "hold":
            fill[j - 1] = ("_", None); j -= 1
        else:
            parts = opts[w - 1][b[1]][0]
            n = len(parts)
            for k, p in enumerate(parts):
                fill[j - n + k] = (p, k < n - 1 or words[w - 1][1])
            w -= 1; j -= n
    return best[W][N], fill


def to_rows(h, T, fill):
    """isi slot -> format baris '>' per bagian"""
    out = [[[] for _ in s["rows"]] for s in h["sections"]]
    cur = None
    for (si, ri, _), f in zip(T, fill):
        toks = out[si][ri]
        t, cont = f
        if t == "_":
            toks.append("_"); cur = None; continue
        if cur is not None and cur[0] is toks:
            toks[-1] += "-" + t
        else:
            toks.append(t)
        cur = (toks,) if cont else None
    return [[" ".join(r) for r in sec] for sec in out]


def align_verse(h, lines, D):
    T, ends = template(h)
    words, refrain, notes = clean_verse(lines)
    if words is None:
        return None, notes
    tried = []
    if refrain:
        V1 = v1_words(h)
        nw = [norm(w) for w, _ in words]
        cand = []
        for m in range(min(6, len(nw)), 0, -1):
            cue = nw[-m:]
            for p in range(len(V1) - m + 1):
                if [x for x, _ in V1[p:p + m]] == cue:
                    cand.append((m, p))
            if cand:
                break
        for m, p in cand:
            start = V1[p + m][1] if p + m < len(V1) else len(T)
            pre = words
            r = align(pre, T[:start], [e for e in ends if e <= start] + [start], D)
            if r:
                tried.append((r[0], r[1] + [(T[k][2], None) for k in range(start, len(T))], "refrein dari ayat 1 mulai kata isyarat"))
        if not tried:
            # isyarat tidak ketemu: refrein = sisa lagu mulai batas baris
            for e in [0] + ends[:-1]:
                if e == 0:
                    continue
                r = align(words, T[:e], [x for x in ends if x <= e], D)
                if r:
                    tried.append((r[0] + 1.0, r[1] + [(T[k][2], None) for k in range(e, len(T))], "refrein dari ayat 1 mulai batas baris"))
    else:
        r = align(words, T, ends, D)
        if r:
            tried.append((r[0], r[1], None))
        else:
            # tanpa penanda tapi lebih pendek: bagian akhir (refrein) tidak dicetak ulang
            for e in ends[:-1]:
                r = align(words, T[:e], [x for x in ends if x <= e], D)
                if r:
                    tried.append((r[0] + 1.5, r[1] + [(T[k][2], None) for k in range(e, len(T))], "sisa lagu diisi lirik ayat 1 (refrein tanpa penanda)"))
    if not tried:
        return None, notes
    cost, fill, why = min(tried, key=lambda x: x[0])
    # isi dari ayat 1 memakai tanda sambung ayat 1
    fixed = []
    for (si, ri, t), f in zip(T, fill):
        fixed.append(f)
    # cont untuk slot salinan ayat 1: tentukan dari baris ayat 1
    v1cont = []
    for s in h["sections"]:
        for r in s["rows"]:
            for w in r.split():
                if w == "_":
                    v1cont.append(None)
                else:
                    xs = w.split("-")
                    v1cont += [k < len(xs) - 1 for k in range(len(xs))]
    fixed = [(f[0], v1cont[i] if f[1] is None and f[0] != "_" else f[1]) for i, f in enumerate(fixed)]
    if why:
        notes = notes + [why]
    return {"rows": to_rows(h, T, fixed), "cost": round(cost, 2), "notes": notes}, notes
