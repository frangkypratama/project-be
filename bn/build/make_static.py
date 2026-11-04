#!/usr/bin/env python3
"""Buat halaman statis Buku Nyanyian HKBP Digital di bawah /bn/ (dipasang di samping hasil BE).

  python3 bn/build/make_static.py --base https://bukuende.com --out /var/www/bukuende.new

Hasil di <out>/:
  bn/index.html               beranda (statis; diperkaya JavaScript)
  bn/<id>/index.html          satu halaman per lagu (judul, meta, lirik semua ayat di HTML)
  bn/assets/app.css, app.js   dipakai bersama
  bn/data/*.json              data lagu
  sitemap-bn.xml              ditambahkan ke robots.txt (sitemap.xml milik BE tidak diubah)
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


# --- app.js: tautan nyata /bn/<id>/ dan rute dari path, bukan hash ---
js = rep(js, 'a.href="#bn-"+(h.id||h.be);', 'a.href=BP+"/"+(h.id||h.be)+"/";')
js = rep(js, """href="#bn-'+xs[0].be+'\"""", """href="'+BP+'/'+xs[0].be+'/\"""")
js = rep(js, 'href="#bn-1"', """href="'+BP+'/1/\"""", 2)
js = rep(js, 'location.hash="#bn-"+(hit.id||hit.be);', 'location.href=BP+"/"+(hit.id||hit.be)+"/";')
js = rep(js, '.href=document.getElementById("todayBtn").href="#bn-"+id;', '.href=document.getElementById("todayBtn").href=BP+"/"+id+"/";')
js = rep(js, """href="#bn-'+(pv.id||pv.be)+'\"""", """href="'+BP+'/'+(pv.id||pv.be)+'/\"""")
js = rep(js, """href="#bn-'+(nx.id||nx.be)+'\"""", """href="'+BP+'/'+(nx.id||nx.be)+'/\"""")
js = rep(js, 'fetch("data/b"+pad2(n)+".json")', 'fetch(BP+"/data/b"+pad2(n)+".json")')
js = rep(js, 'fetch("data/index.json")', 'fetch(BP+"/data/index.json")')
js = js.replace('fetch("scans/b"', 'fetch(BP+"/scans/b"')
js = rep(js, 'if(a)location.hash=a.getAttribute("href");}});', 'if(a)location.href=a.getAttribute("href");}});')
js = rep(js, 'if(a){location.hash=a.getAttribute("href");}});', 'if(a){location.href=a.getAttribute("href");}});')
js = rep(js, """  var m=location.hash.match(/^#b[ne]-(\\d+[a-z]?)$/);
  if(!m){renderHome();return;}
  var n=m[1].replace(/^0+/,"");""",
         """  var m=location.hash.match(/^#b[ne]-(\\d+[a-z]?)$/);
  if(m){location.replace(BP+"/"+m[1].replace(/^0+/,"")+"/");return;} // alamat lama
  if(!window.BN_PAGE){renderHome();return;}
  var n=String(window.BN_PAGE);""")
js = mark(js).strip()
_bp = "var BP=" + json.dumps(BP) + "; // awalan path BN\n"
js = js.replace('"use strict";', '"use strict";\n' + _bp, 1) if js.startswith('"use strict";') else _bp + js

os.makedirs(os.path.join(BNOUT, "assets"), exist_ok=True)
shutil.rmtree(os.path.join(BNOUT, "data"), ignore_errors=True)
import hashlib
V = hashlib.sha1((css + js).encode("utf-8")).hexdigest()[:8]  # nomor versi berkas (lihat build/make_static.py)
open(os.path.join(BNOUT, "assets", "app.css"), "w", encoding="utf-8").write(css.strip() + "\n")
open(os.path.join(BNOUT, "assets", "app.js"), "w", encoding="utf-8").write(js + "\n")
shutil.copytree(DATA, os.path.join(BNOUT, "data"))

index = json.load(open(os.path.join(DATA, "index.json"), encoding="utf-8"))
hymns = {}
for f in sorted(glob.glob(os.path.join(DATA, "b*.json"))):
    for h in json.load(open(f, encoding="utf-8")):
        hymns[str(h.get("id") or h["be"])] = h
DO = {"C": "C", "D": "D", "E": "E", "F": "F", "G": "G", "A": "A", "B": "B", "Bb": "Bes", "Eb": "Es", "Ab": "As", "Db": "Des",
      "Gb": "Ges", "F#": "Fis"}


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
    tail = (f'<script>window.BE_STATIC=true;window.BN_PAGE={json.dumps(page_id)};</script>\n' if page_id else '<script>window.BE_STATIC=true;</script>\n') \
        + abcjs + f'\n<script src="{BP}/assets/app.js?v={V}"></script>\n</body>\n</html>\n'
    return head + b + tail


def first_line(h):
    v = h.get("verses") or [[]]
    t = " ".join(v[0])
    return (t[:150].rsplit(" ", 1)[0] + "…") if len(t) > 155 else t


ids = [str(x.get("id") or x["be"]) for x in index]
urls = []
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
            (f'<a class="prev" href="{BP}/{pv}/" rel="prev"><span class="lbl">← Sebelumnya</span><span class="ttl"><b>{pv}</b>{E(hymns[pv]["title"])}</span></a>' if pv else "") + \
            (f'<a class="next" href="{BP}/{nx}/" rel="next"><span class="lbl">Berikutnya →</span><span class="ttl"><b>{nx}</b>{E(hymns[nx]["title"])}</span></a>' if nx else "") + "</nav>"
    main = f"""<header class="hymn-head"><div class="hymn-no">{E(hid)}</div><h1>{E(h['title'])}</h1><div class="meta">{meta}</div></header>
<p class="loading">Memuat not angka dan not balok…</p>
<section class="block"><h2>Lirik</h2><div class="verses">{verses}</div><div class="credit">{credit}</div></section>
{pager}"""
    ld = {"@context": "https://schema.org", "@type": "MusicComposition", "name": h["title"],
          "alternateName": f"Buku Nyanyian {hid}", "url": f"{BASE}/bn/{hid}/", "inLanguage": "id",
          "isPartOf": {"@type": "Book", "name": "Buku Nyanyian HKBP"},
          "lyrics": {"@type": "CreativeWork", "inLanguage": "id", "text": "\n\n".join("\n".join(v) for v in (h.get("verses") or []))}}
    if h.get("credit"):
        ld["creditText"] = h["credit"]
    d = os.path.join(BNOUT, hid)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page(f"/bn/{hid}/", title, desc, main, page_id=hid, jsonld=ld))
    urls.append(f"/bn/{hid}/")

# --- beranda /bn/ ---
nav = "".join(f'<li><a href="{BP}/{hid}/"><span class="n">{E(hid)}</span><span class="t">{E(hymns[hid]["title"])}</span></a></li>' for hid in ids)
n_main = len({x["be"] for x in index})
home = f"""<div class="home"><section class="hero"><h1>Buku Nyanyian</h1>
<p class="lead">Nyanyikan, mainkan, dan dengarkan {n_main} nyanyian HKBP, lengkap dengan not angka, not balok, dan semua ayatnya.</p></section></div>"""
ld = {"@context": "https://schema.org", "@type": "WebSite", "name": BOOK, "url": BASE + "/bn/", "inLanguage": "id"}
open(os.path.join(BNOUT, "index.html"), "w", encoding="utf-8").write(
    page("/bn/", f"{BOOK} – lirik, not angka, not balok",
         f"Buku Nyanyian HKBP digital: {n_main} nyanyian dengan lirik semua ayat, not angka, dan not balok yang bisa diputar.",
         home, nav=nav, jsonld=ld))

# --- sitemap-bn.xml, robots.txt ---
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', f"  <url><loc>{BASE}/bn/</loc></url>"]
sm += [f"  <url><loc>{BASE}{u}</loc></url>" for u in urls]
sm.append("</urlset>")
open(os.path.join(OUT, "sitemap-bn.xml"), "w").write("\n".join(sm) + "\n")
rb = os.path.join(OUT, "robots.txt")
line = f"Sitemap: {BASE}/sitemap-bn.xml\n"
cur = open(rb).read() if os.path.exists(rb) else "User-agent: *\nAllow: /\n"
if line not in cur:
    open(rb, "w").write(cur.rstrip("\n") + "\n" + line)
print(f"ok: {len(urls)} halaman lagu + beranda, sitemap-bn {len(urls) + 1} URL, base {BASE}/bn/")
