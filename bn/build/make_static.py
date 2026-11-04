#!/usr/bin/env python3
"""Buat halaman statis Buku Nyanyian HKBP Digital di bawah /bn/ (dipasang di samping hasil BE).

  python3 bn/build/make_static.py --base https://bukuende.com --out /var/www/bukuende.new

Hasil di <out>/:
  bn/index.html               beranda (statis; diperkaya JavaScript)
  bn/<id>/index.html          satu halaman per lagu (judul, meta, lirik semua ayat di HTML)
  bn/assets/app.css, app.js   dipakai bersama
  bn/data/*.json              data lagu
  sitemap.xml                 entri BN ditambahkan ke sitemap BE (satu sitemap untuk dua buku)
Jalankan SETELAH build/make_static.py milik BE (yang membuat <out>/ dan robots.txt).
"""
import argparse, glob, html, json, os, re, shutil
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PROD = os.path.join(ROOT, "site-prod", "index.html")
DATA = os.path.join(ROOT, "site", "data")

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="https://bukuende.example", help="alamat situs, tanpa garis miring di akhir")
ap.add_argument("--out", required=True, help="folder situs (akar), mis. /var/www/bukuende.new")
a = ap.parse_args()
BASE = a.base.rstrip("/")
RP = urlparse(BASE).path.rstrip("/")  # awalan path situs ("" untuk domain sendiri)
BP = RP + "/bn"                       # awalan path BN
OUT = a.out
BNOUT = os.path.join(OUT, "bn")
E = lambda s: html.escape(str(s), quote=True)
BOOK = "Buku Nyanyian HKBP Digital"

src = open(PROD, encoding="utf-8").read()
css = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
js = re.search(r"<script>(.*)</script>\s*$", src, re.S).group(1)
fonts = "\n".join(re.findall(r'<link rel="(?:preconnect|stylesheet)"[^>]*>', src))
abcjs = re.search(r'<script src="https://cdn\.jsdelivr\.net/npm/abcjs[^"]*"></script>', src).group(0)
body = src[src.index("</style>") + len("</style>"):src.index(abcjs)]


def rep(s, old, new, cnt=1):
    assert s.count(old) == cnt, (s.count(old), old[:80])
    return s.replace(old, new)


def mark(s):
    return s.replace("__BN__", BP).replace("__ROOT__", RP)


import unicodedata


def slugify(t):
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().lower().replace("'", "")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if len(t) > 60:
        t = t[:60].rsplit("-", 1)[0]
    return t


_ix0 = json.load(open(os.path.join(DATA, "index.json"), encoding="utf-8"))
SLUG = {str(x.get("id") or x["be"]): slugify(x["title"]) for x in _ix0}   # nomor -> slug judul
SEGS = {k: (k + "-" + v if v else k) for k, v in SLUG.items()}              # nomor -> segmen alamat, mis. "1-ringgas-ma-ho-tondingku"
_seg_js = "var SEG_MAP=" + json.dumps({k: v for k, v in SLUG.items() if v}, separators=(",", ":")) + ";\nfunction SEG(id){id=String(id);return SEG_MAP[id]?id+\"-\"+SEG_MAP[id]:id;}\n"
REDIR = []   # pasangan (alamat lama, alamat baru) untuk 301


def stub(newpath, base):
    return ('<!doctype html>\n<html lang="id"><head><meta charset="utf-8"><title>Halaman dipindahkan</title>'
            f'<link rel="canonical" href="{base}{newpath}"><meta http-equiv="refresh" content="0;url={newpath}"></head>'
            f'<body><p>Halaman ini pindah ke <a href="{newpath}">{newpath}</a>.</p></body></html>\n')


# --- app.js: tautan nyata /bn/<id>-<judul>/ dan rute dari path, bukan hash ---
js = rep(js, 'a.href="#bn-"+(h.id||h.be);', 'a.href=BP+"/"+SEG(h.id||h.be)+"/";')
js = rep(js, """href="#bn-'+xs[0].be+'\"""", """href="'+BP+'/'+SEG(xs[0].be)+'/\"""")
js = rep(js, 'href="#bn-1"', """href="'+BP+'/'+SEG(1)+'/\"""", 2)
js = rep(js, 'location.hash="#bn-"+(hit.id||hit.be);', 'location.href=BP+"/"+SEG(hit.id||hit.be)+"/";')
js = rep(js, '.href=document.getElementById("todayBtn").href="#bn-"+id;', '.href=document.getElementById("todayBtn").href=BP+"/"+SEG(id)+"/";')
js = rep(js, """href="#bn-'+(pv.id||pv.be)+'\"""", """href="'+BP+'/'+SEG(pv.id||pv.be)+'/\"""")
js = rep(js, """href="#bn-'+(nx.id||nx.be)+'\"""", """href="'+BP+'/'+SEG(nx.id||nx.be)+'/\"""")
js = rep(js, 'fetch("data/b"+pad2(n)+".json")', 'fetch(BP+"/data/b"+pad2(n)+".json")')
js = rep(js, 'fetch("data/index.json")', 'fetch(BP+"/data/index.json")')
js = js.replace('fetch("scans/b"', 'fetch(BP+"/scans/b"')
js = rep(js, 'if(a)location.hash=a.getAttribute("href");}});', 'if(a)location.href=a.getAttribute("href");}});')
js = rep(js, 'if(a){location.hash=a.getAttribute("href");}});', 'if(a){location.href=a.getAttribute("href");}});')
js = rep(js, """  var m=location.hash.match(/^#b[ne]-(\\d+[a-z]?)$/);
  if(!m){renderHome();return;}
  var n=m[1].replace(/^0+/,"");""",
         """  var m=location.hash.match(/^#b[ne]-(\\d+[a-z]?)$/);
  if(m){location.replace(BP+"/"+SEG(m[1].replace(/^0+/,""))+"/");return;} // alamat lama
  if(!window.BN_PAGE){if(window.BN_DAFTAR)return;renderHome();return;}
  var n=String(window.BN_PAGE);""")
js = mark(js).strip()
_bp = "var BP=" + json.dumps(BP) + "; // awalan path BN\n" + _seg_js
js = js.replace('"use strict";', '"use strict";\n' + _bp, 1) if js.startswith('"use strict";') else _bp + js

DL_CSS = """.dl{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:2px 24px}
.dl a{display:flex;gap:10px;align-items:baseline;padding:7px 4px;color:var(--ink);text-decoration:none;border-bottom:1px solid var(--rule);min-width:0}
.dl a:hover{color:var(--gorga)}
.dl a:focus-visible{outline:2px solid var(--gorga);outline-offset:2px}
.dl .dn{font-family:var(--f-num);font-weight:700;font-variant-numeric:tabular-nums;min-width:3.2ch;color:var(--ink-2)}
.dl .dt{font-family:var(--f-display);min-width:0;overflow-wrap:anywhere}
.more{margin:14px 0 0}
.more a{color:var(--gorga)}
"""
os.makedirs(os.path.join(BNOUT, "assets"), exist_ok=True)
shutil.rmtree(os.path.join(BNOUT, "data"), ignore_errors=True)
import hashlib
V = hashlib.sha1((css + js).encode("utf-8")).hexdigest()[:8]  # nomor versi berkas (lihat build/make_static.py)
open(os.path.join(BNOUT, "assets", "app.css"), "w", encoding="utf-8").write(css.strip() + "\n" + DL_CSS)
open(os.path.join(BNOUT, "assets", "app.js"), "w", encoding="utf-8").write(js + "\n")
shutil.copytree(DATA, os.path.join(BNOUT, "data"))

index = json.load(open(os.path.join(DATA, "index.json"), encoding="utf-8"))
hymns = {}
for f in sorted(glob.glob(os.path.join(DATA, "b*.json"))):
    for h in json.load(open(f, encoding="utf-8")):
        hymns[str(h.get("id") or h["be"])] = h
DO = {"C": "C", "D": "D", "E": "E", "F": "F", "G": "G", "A": "A", "B": "B", "Bb": "Bes", "Eb": "Es", "Ab": "As", "Db": "Des",
      "Gb": "Ges", "F#": "Fis"}


def sm_label(s):
    s = re.sub(r"-{2,}", "-", str(s)).strip().rstrip("-").strip()
    return s.replace("<", "").replace(">", "")


def daftar_main(pref, label, ids_, hy, segs):
    groups = {}
    for i in ids_:
        groups.setdefault((hy[i]["be"] - 1) // 100, []).append(i)
    out = f'<header class="hymn-head"><div class="hymn-no">No.</div><h1>Daftar {label}</h1><div class="meta"><span>{len({hy[i]["be"] for i in ids_})} nomor, urut nomor</span></div></header>'
    for g in sorted(groups):
        out += f'<section class="block"><h2>{g * 100 + 1}–{g * 100 + 100}</h2><ul class="dl">' + "".join(
            f'<li><a href="{pref}/{segs[i]}/"><span class="dn">{E(i)}</span><span class="dt">{E(hy[i]["title"])}</span></a></li>' for i in groups[g]) + "</ul></section>"
    return out


def page(path, title, desc, main, nav="", page_id=None, jsonld=None, extra_head=""):
    url = BASE + path
    head = f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(url)}">
<meta property="og:type" content="{'music.song' if page_id else 'website'}">
<meta property="og:site_name" content="{BOOK}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(url)}">
<meta property="og:locale" content="id_ID">
<link rel="icon" href="{RP}/favicon.ico" sizes="any">
{fonts}
<link rel="stylesheet" href="{BP}/assets/app.css?v={V}">
{extra_head}{('<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/") + '</script>') if jsonld else ''}
</head>
<body>"""
    b = mark(body)
    b = rep(b, '<main id="main"></main>', '<main id="main">' + main + '</main>')
    if nav:
        b = rep(b, '<ol id="list"></ol>', '<ol id="list">' + nav + '</ol>')
    tail = (f'<script>window.BE_STATIC=true;window.BN_PAGE={json.dumps(page_id)};</script>\n' if page_id else '<script>window.BE_STATIC=true;' + ('window.BN_DAFTAR=true;' if path.endswith('/daftar/') else '') + '</script>\n') \
        + abcjs + f'\n<script src="{BP}/assets/app.js?v={V}"></script>\n</body>\n</html>\n'
    return head + b + tail


def first_line(h):
    v = h.get("verses") or [[]]
    t = " ".join(v[0])
    return (t[:150].rsplit(" ", 1)[0] + "…") if len(t) > 155 else t


ids = [str(x.get("id") or x["be"]) for x in index]
urls = []
uhid = {}
for i, hid in enumerate(ids):
    h = hymns[hid]
    nv = len(h.get("verses") or [])
    title = f"Buku Nyanyian {hid} – {h['title']} | {BOOK}"
    desc = f"Buku Nyanyian HKBP No. {hid}: {h['title']}. " + (f"Buku Logu No. {h['bl']}. " if h.get("bl") else "") + \
           f"Lirik {nv} ayat, not angka dan not balok (do = {DO.get(h['key'], h['key'])}, {h['meter']}). " + first_line(h)
    meta = f"<span>BN <b>{E(str(h['be']).zfill(3) + (h.get('variant') or ''))}</b></span>" + \
           (f"<span>Buku Logu <b>{E(h['bl'])}</b></span>" if h.get("bl") else "") + \
           f"<span><b>do = {E(DO.get(h['key'], h['key']))}</b></span><span>Birama <b>{E(h['meter'])}</b></span>" + \
           (f"<span>♩ = <b>{E(h['tempo'])}</b></span>" if h.get("tempo") else "") + \
           (f"<span>{E(h['cat'])}</span>" if h.get("cat") else "")
    vn = h.get("vnum") or []
    verses = "".join(f'<p class="verse"><span class="vn">{E(vn[k] if k < len(vn) else k + 1)}.</span><span>' + "".join(f'<span class="l">{E(l)}</span>' for l in v) + "</span></p>"
                     for k, v in enumerate(h.get("verses") or []))
    credit = "<br>".join(E(c) for c in h["credits"]) if h.get("credits") else (f"Lagu: {E(h['credit'])}" if h.get("credit") else "")
    pv, nx = (ids[i - 1] if i else None), (ids[i + 1] if i + 1 < len(ids) else None)
    pager = '<nav class="pager" aria-label="Nyanyian sebelum dan sesudahnya">' + \
            (f'<a class="prev" href="{BP}/{SEGS[pv]}/" rel="prev"><span class="lbl">← Sebelumnya</span><span class="ttl"><b>{pv}</b>{E(hymns[pv]["title"])}</span></a>' if pv else "") + \
            (f'<a class="next" href="{BP}/{SEGS[nx]}/" rel="next"><span class="lbl">Berikutnya →</span><span class="ttl"><b>{nx}</b>{E(hymns[nx]["title"])}</span></a>' if nx else "") + "</nav>"
    main = f"""<header class="hymn-head"><div class="hymn-no">{E(hid)}</div><h1>{E(h['title'])}</h1><div class="meta">{meta}</div></header>
<p class="loading">Memuat not angka dan not balok…</p>
<section class="block"><h2>Lirik</h2><div class="verses">{verses}</div><div class="credit">{credit}</div></section>
{pager}"""
    ld = {"@context": "https://schema.org", "@type": "MusicComposition", "name": h["title"],
          "alternateName": f"Buku Nyanyian {hid}", "url": f"{BASE}/bn/{SEGS[hid]}/", "inLanguage": "id",
          "isPartOf": {"@type": "Book", "name": "Buku Nyanyian HKBP"},
          "lyrics": {"@type": "CreativeWork", "inLanguage": "id", "text": "\n\n".join("\n".join(v) for v in (h.get("verses") or []))}}
    if h.get("credit"):
        ld["creditText"] = h["credit"]
    d = os.path.join(BNOUT, SEGS[hid])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page(f"/bn/{SEGS[hid]}/", title, desc, main, page_id=hid, jsonld=ld))
    urls.append(f"/bn/{SEGS[hid]}/")
    uhid[f"/bn/{SEGS[hid]}/"] = hid
    if SEGS[hid] != hid:   # alamat lama /bn/<nomor>/: halaman pengalih (cadangan; Nginx mengalihkan 301 lewat redirects.map)
        od = os.path.join(BNOUT, hid)
        os.makedirs(od, exist_ok=True)
        open(os.path.join(od, "index.html"), "w", encoding="utf-8").write(stub(f"{BP}/{SEGS[hid]}/", BASE))
        REDIR.append((f"/bn/{hid}/", f"/bn/{SEGS[hid]}/"))

# --- beranda /bn/ ---
nav = "".join(f'<li><a href="{BP}/{SEGS[hid]}/"><span class="n">{E(hid)}</span><span class="t">{E(hymns[hid]["title"])}</span></a></li>' for hid in ids)
n_main = len({x["be"] for x in index})
home = f"""<div class="home"><section class="hero"><h1>Buku Nyanyian</h1>
<p class="lead">Nyanyikan, mainkan, dan dengarkan {n_main} nyanyian HKBP, lengkap dengan not angka, not balok, dan semua ayatnya.</p></section></div>"""
ld = {"@context": "https://schema.org", "@type": "WebSite", "name": BOOK, "url": BASE + "/bn/", "inLanguage": "id"}
open(os.path.join(BNOUT, "index.html"), "w", encoding="utf-8").write(
    page("/bn/", f"{BOOK} – lirik, not angka, not balok",
         f"Buku Nyanyian HKBP digital: {n_main} nyanyian dengan lirik semua ayat, not angka, dan not balok yang bisa diputar.",
         home, nav=nav, jsonld=ld))

# --- daftar lengkap (nomor + judul) ---
os.makedirs(os.path.join(BNOUT, "daftar"), exist_ok=True)
open(os.path.join(BNOUT, "daftar", "index.html"), "w", encoding="utf-8").write(page(
    "/bn/daftar/", f"Daftar Nyanyian HKBP – nomor dan judul | {BOOK}",
    f"Daftar lengkap {n_main} nyanyian HKBP berdasarkan nomor Buku Nyanyian, dengan judul masing-masing.",
    daftar_main(BP, "Nyanyian", ids, hymns, SEGS), nav=nav))

# --- sitemap.xml (satu untuk BE dan BN), robots.txt ---
ent = [f"  <url><loc>{BASE}/bn/</loc></url> <!-- Beranda Buku Nyanyian -->",
       f"  <url><loc>{BASE}/bn/daftar/</loc></url> <!-- Daftar lengkap nomor dan judul -->"]
ent += [f"  <url><loc>{BASE}{u}</loc></url> <!-- {sm_label(uhid[u] + '. ' + hymns[uhid[u]]['title'])} -->" for u in urls]
smp = os.path.join(OUT, "sitemap.xml")
if os.path.exists(smp):  # sitemap BE sudah ada (dibuat build/make_static.py): tambahkan entri BN ke dalamnya
    cur_sm = open(smp, encoding="utf-8").read()
    assert "</urlset>" in cur_sm
    if f"<loc>{BASE}/bn/</loc>" not in cur_sm:
        cur_sm = cur_sm.replace("</urlset>", "\n".join(ent) + "\n</urlset>")
    open(smp, "w", encoding="utf-8").write(cur_sm)
else:
    open(smp, "w", encoding="utf-8").write("\n".join(['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'] + ent + ["</urlset>"]) + "\n")
rb = os.path.join(OUT, "robots.txt")
line = f"Sitemap: {BASE}/sitemap.xml\n"
cur = open(rb).read() if os.path.exists(rb) else "User-agent: *\nAllow: /\n"
if line not in cur:
    open(rb, "w").write(cur.rstrip("\n") + "\n" + line)
_rm = os.path.join(OUT, "redirects.map")
_old = open(_rm, encoding="utf-8").read() if os.path.exists(_rm) else ""
_new = "".join(f"{a} {b};\n" for a, b in REDIR if f"{a} {b};\n" not in _old)
open(_rm, "w", encoding="utf-8").write(_old + _new)
print(f"ok: {len(urls)} halaman lagu + beranda, masuk sitemap.xml {len(urls) + 2} URL, base {BASE}/bn/")
