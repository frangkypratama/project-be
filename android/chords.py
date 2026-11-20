"""Penyusun akor iringan otomatis dari melodi not angka.

Hasil per bagian lagu: daftar token per ketukan (sejajar dengan ketukan not), None = akor
sebelumnya berlanjut. Token relatif terhadap Do bagian itu: "<semitone>" atau "<semitone>:<kualitas>",
mis. "0" = I, "7:7" = V7, "9:m" = vi. Aplikasi menamai akor sesuai nada dasar (dan transposisi).

Sumber akor: kolom "chords" tiap bagian lagu di data (baris akor sejajar dengan baris not,
satu nama akor atau "." per ketukan). Bila kolom itu kosong, akor disusun otomatis:

Aturan: akor diatonis (I ii iii IV V V7 vi) + akor sisipan bila ada nada kromatis
(#4 -> II, #5 -> III, #1 -> VI, b7 -> I7); maksimal 2 akor per birama; nada melodi pada
ketukan kuat diutamakan menjadi nada akor; kadens di akhir lagu; mode minor bila lagu berakhir di 6 (la).
"""
import re

MAJ = [0, 2, 4, 5, 7, 9, 11]
TOK = re.compile(r"^(\()?([#b])?([0-7.])([',]*)(/*)(\))?$")
QUAL = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "dim": (0, 3, 6)}


def tones(tok):
    r, _, q = tok.partition(":")
    r = int(r)
    return {(r + i) % 12 for i in QUAL[q]}


def parse(src):
    """Kembalikan (notes, bars): notes = [(start, dur, pc|None)], bars = [jumlah ketukan per birama]."""
    notes, bars, cur = [], [], 0
    last = None
    for line in src.split("\n"):
        for tok in line.split():
            if tok in ("|", ":|", "|]"):
                bars.append(cur)
                cur = 0
                continue
            if tok == "v":
                continue
            parts = tok.split("+")
            exp = "/" in tok
            unit = 1.0 / len(parts)
            for p in parts:
                m = TOK.match(p)
                if not m:
                    raise ValueError(p)
                sl = len(m.group(5))
                du = 0.5 ** sl if (exp and sl > 0) else unit
                if m.group(3) == ".":
                    if last is not None:
                        last[1] += unit
                    continue
                deg = int(m.group(3))
                if deg == 0:
                    last = [0, du, None]
                else:
                    acc = {"#": 1, "b": -1}.get(m.group(2) or "", 0)
                    last = [0, du, (MAJ[deg - 1] + acc) % 12]
                notes.append(last)
            cur += 1
    if cur:
        bars.append(cur)
    pos = 0.0
    for n in notes:
        n[0] = pos
        pos += n[1]
    return [tuple(n) for n in notes], bars


BASE = {"0": .35, "7": .25, "5": .25, "9:m": .12, "2:m": .08, "7:7": .05, "4:m": -.05}
SECONDARY = {6: ["2", "2:7"], 8: ["4", "4:7"], 1: ["9", "9:7"], 10: ["0:7"]}
GOOD = {("7", "0"): .5, ("7:7", "0"): .6, ("5", "7"): .15, ("5", "7:7"): .15, ("2:m", "7"): .3,
        ("2:m", "7:7"): .3, ("0", "5"): .05, ("0", "7"): .05, ("9:m", "2:m"): .2, ("9:m", "5"): .15,
        ("0", "9:m"): .1, ("2", "7"): .5, ("2", "7:7"): .5, ("2:7", "7"): .5, ("2:7", "7:7"): .5,
        ("4", "9:m"): .5, ("4:7", "9:m"): .6, ("9", "2:m"): .4, ("9:7", "2:m"): .4, ("0:7", "5"): .5,
        ("4:m", "9:m"): .1, ("7", "9:m"): .1, ("5", "0"): .15,
        ("7", "5"): -.2, ("7:7", "5"): -.3}


def harmonize(src, last_section=True):
    notes, bars = parse(src)
    if not bars:
        return []
    total = sum(bars)
    # slot: (mulai, akhir, setengah birama?)
    slots, b0 = [], 0
    for n in bars:
        if n <= 0:
            continue
        if n >= 4 and n % 2 == 0:
            slots += [(b0, b0 + n // 2, False), (b0 + n // 2, b0 + n, True)]
        elif n == 3:  # 3/4: akor kedua boleh di ketukan ketiga
            slots += [(b0, b0 + 2, False), (b0 + 2, b0 + 3, True)]
        else:
            slots.append((b0, b0 + n, False))
        b0 += n
    sounding = [x for x in notes if x[2] is not None]
    minor = bool(sounding) and sounding[-1][2] == 9
    pcs_all = {x[2] for x in sounding}

    def cands(present):
        c = list(BASE)
        for pc, extra in SECONDARY.items():
            if pc in present:
                c += extra
        if minor:
            c += ["4", "4:7"]
        return list(dict.fromkeys(c))

    prior = dict(BASE)
    if minor:
        prior.update({"9:m": .35, "4": .2, "4:7": .1, "2:m": .2, "5": .1, "0": .15})
    for k in ("2", "2:7", "4", "4:7", "9", "9:7", "0:7"):
        prior.setdefault(k, -.1)

    info = []
    for (s, e, mid) in slots:
        w = {}
        for (st, du, pc) in sounding:
            ov = min(e, st + du) - max(s, st)
            if ov <= 1e-9:
                continue
            ww = ov * (1.6 if abs(st - s) < 1e-9 else 1.0)
            w[pc] = w.get(pc, 0) + ww
        info.append((w, cands(set(w))))

    tonic = "9:m" if minor else "0"
    dom = ("4", "4:7") if minor else ("7", "7:7")
    n = len(slots)

    def score(i, c):
        w, _ = info[i]
        ts = tones(c)
        sc = sum(v * (1 if pc in ts else -.7) for pc, v in w.items()) + prior.get(c, -.1)
        if i == n - 1:  # kadens: bagian berakhir di tonika (lagu terakhir lebih kuat)
            sc += (2.0 if last_section else 1.0) if c == tonic else 0
        if i == n - 2 and c in dom:
            sc += .3
        if i == 0 and c == tonic:
            sc += .5
        return sc

    best = [{} for _ in range(n)]
    for c in info[0][1]:
        best[0][c] = (score(0, c), None)
    for i in range(1, n):
        mid = slots[i][2]
        for c in info[i][1]:
            sc = score(i, c)
            top = None
            for p, (ps, _) in best[i - 1].items():
                t = ps + GOOD.get((p, c), 0)
                if p == c:
                    t += .12 if mid else .06
                elif mid:
                    t -= .12
                if top is None or t > top[0]:
                    top = (t, p)
            best[i][c] = (top[0] + sc, top[1])
    c = max(best[-1], key=lambda k: best[-1][k][0])
    seq = [c]
    for i in range(n - 1, 0, -1):
        c = best[i][c][1]
        seq.append(c)
    seq.reverse()

    out = [None] * total
    prev = None
    for (s, e, mid), c in zip(slots, seq):
        if c != prev:
            out[s] = c
            prev = c
    return out


LETTER = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
KEY_PC = {"C": 0, "G": 7, "D": 2, "A": 9, "E": 4, "B": 11, "F": 5, "Bb": 10, "Eb": 3, "Ab": 8,
          "Db": 1, "Gb": 6, "F#": 6}
CH_RE = re.compile(r"^([A-G])(#|b)?(m7|m|7|dim)?$")


def from_letters(text, key):
    """Akor susunan tangan ("D . A . |") -> token relatif terhadap Do."""
    t = KEY_PC.get(key, 0)
    out = []
    for tok in re.sub(r"\|\]|:\||\|", " ", text).split():
        if tok == ".":
            out.append(None)
            continue
        m = CH_RE.match(tok)
        if not m:
            raise ValueError(tok)
        r = (LETTER[m.group(1)] + {"#": 1, "b": -1}.get(m.group(2) or "", 0) - t) % 12
        q = m.group(3) or ""
        out.append(f"{r}:{q}" if q else str(r))
    return out


FLAT_KEYS = {"F", "Bb", "Eb", "Ab", "Db", "Gb"}
SHARP_N = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_N = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]


def name(tok, key):
    """Token relatif ("7:7") -> nama akor menurut nada dasar ("A7" bila Do = D)."""
    r, _, q = tok.partition(":")
    names = FLAT_N if key in FLAT_KEYS else SHARP_N
    return names[(KEY_PC.get(key, 0) + int(r)) % 12] + q


def to_letters(src, ch, key):
    """Token per ketukan -> baris akor yang sejajar dengan baris not ("D . A . | Bm . G . |")."""
    out, i = [], 0
    for line in src.split("\n"):
        row = []
        for tok in line.split():
            if tok in ("|", ":|", "|]"):
                row.append(tok)
            elif tok != "v":
                c = ch[i] if i < len(ch) else None
                row.append(name(c, key) if c else ".")
                i += 1
        out.append(" ".join(row))
    if i != len(ch):
        raise ValueError(f"{len(ch)} akor untuk {i} ketukan")
    return "\n".join(out)


def chords_for(book, h):
    """Daftar token per bagian. Akor diambil dari kolom "chords" data lagu (sejajar dengan not);
    bagian yang belum punya akor disusun otomatis dari melodinya."""
    secs = h["sections"]
    out = []
    for i, s in enumerate(secs):
        key = s.get("key") or h.get("key") or "C"
        if s.get("chords"):
            out.append(from_letters(s["chords"], key))
        else:
            out.append(harmonize(s["notes"], last_section=(i == len(secs) - 1)))
    return out


def fit(src, ch):
    """Persentase not yang jatuh di awal slot akor dan termasuk nada akor (ukuran mutu)."""
    notes, bars = parse(src)
    cur, hit, tot = None, 0, 0
    by_beat = {}
    for b, c in enumerate(ch):
        if c:
            by_beat[b] = c
    for (st, du, pc) in notes:
        b = int(st + 1e-9)
        for k in sorted(by_beat):
            if k <= st + 1e-9:
                cur = by_beat[k]
        if pc is None or cur is None or abs(st - round(st)) > 1e-9:
            continue
        tot += 1
        hit += pc in tones(cur)
    return hit, tot
