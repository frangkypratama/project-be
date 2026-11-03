#!/usr/bin/env python3
"""Buat situs statis siap-Google dari halaman Prod.

  python3 build/make_static.py --base https://domainanda.id

Hasil di dist/:
  index.html              beranda: pengantar + daftar tautan semua lagu
  be/<id>/index.html      satu halaman per lagu: judul, meta, lirik semua ayat di HTML
  assets/app.css, app.js  dipakai bersama (di-cache browser)
  data/*.json             data lagu (sama dengan Prod)
  sitemap.xml, robots.txt, 404.html, favicon.ico
Alamat lama "#be-550" otomatis dialihkan ke /be/550/.
"""
import argparse, html, json, os, re, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PROD = os.path.join(ROOT, "site-prod", "index.html")
DATA = os.path.join(ROOT, "site", "data")
ICON = os.path.join(ROOT, "icon", "salib.ico")

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="https://bukuende.example", help="alamat situs, tanpa garis miring di akhir")
ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
a = ap.parse_args()
BASE = a.base.rstrip("/")
OUT = a.out
E = lambda s: html.escape(str(s), quote=True)

src = open(PROD, encoding="utf-8").read()
css = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
js = re.search(r"<script>(.*)</script>\s*$", src, re.S).group(1)
fonts = "\n".join(re.findall(r'<link rel="(?:preconnect|stylesheet)"[^>]*>', src))
abcjs = re.search(r'<script src="https://cdn\.jsdelivr\.net/npm/abcjs[^"]*"></script>', src).group(0)
body = src[src.index("</style>") + len("</style>"):src.index(abcjs)]


def rep(s, old, new, cnt=1):
    assert s.count(old) == cnt, (s.count(old), old[:80])
    return s.replace(old, new)


# --- app.js: tautan nyata /be/<id>/ dan rute dari path, bukan hash ---
js = rep(js, 'a.href="#be-"+(h.id||h.be);', 'a.href="/be/"+(h.id||h.be)+"/";')
js = rep(js, """'<a class="prev" href="#be-'+(pv.id||pv.be)+'" rel="prev">""", """'<a class="prev" href="/be/'+(pv.id||pv.be)+'/" rel="prev">""")
js = rep(js, """'<a class="next" href="#be-'+(nx.id||nx.be)+'" rel="next">""", """'<a class="next" href="/be/'+(nx.id||nx.be)+'/" rel="next">""")
js = rep(js, 'fetch("data/b"+pad2(n)+".json")', 'fetch("/data/b"+pad2(n)+".json")')
js = rep(js, 'fetch("data/index.json")', 'fetch("/data/index.json")')
js = rep(js, 'if(a)location.hash=a.getAttribute("href");}});', 'if(a)location.href=a.getAttribute("href");}});')
js = rep(js, 'if(a){location.hash=a.getAttribute("href");}});', 'if(a){location.href=a.getAttribute("href");}});')
js = rep(js, """  var m=location.hash.match(/^#be-(\\d+[a-z]?)$/), n=m?m[1].replace(/^0+/,""):String(INDEX[0].id||INDEX[0].be);""",
         """  var m=location.hash.match(/^#be-(\\d+[a-z]?)$/);
  if(m){location.replace("/be/"+m[1].replace(/^0+/,"")+"/");return;} // alamat lama
  if(!window.BE_PAGE) return; // beranda: isi dari HTML statis
  var n=String(window.BE_PAGE);""")
js = js.replace('fetch("scans/b"', 'fetch("/scans/b"')

os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
for d in ("be", "data"):
    shutil.rmtree(os.path.join(OUT, d), ignore_errors=True)
open(os.path.join(OUT, "assets", "app.css"), "w", encoding="utf-8").write(css.strip() + "\n")
open(os.path.join(OUT, "assets", "app.js"), "w", encoding="utf-8").write(js.strip() + "\n")
shutil.copytree(DATA, os.path.join(OUT, "data"))
if os.path.exists(ICON):
    shutil.copy(ICON, os.path.join(OUT, "favicon.ico"))

index = json.load(open(os.path.join(DATA, "index.json"), encoding="utf-8"))
hymns = {}
for f in sorted(glob.glob(os.path.join(DATA, "b*.json"))):
    for h in json.load(open(f, encoding="utf-8")):
        hymns[str(h.get("id") or h["be"])] = h
DO = {"C": "C", "D": "D", "E": "E", "F": "F", "G": "G", "A": "A", "B": "B", "Bb": "Bes", "Eb": "Es", "Ab": "As", "Db": "Des",
      "Gb": "Ges", "F#": "Fis", "C#": "Cis", "G#": "Gis", "D#": "Dis", "A#": "Ais"}


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
<meta property="og:site_name" content="Buku Ende Digital">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(url)}">
<meta property="og:locale" content="id_ID">
<link rel="icon" href="/favicon.ico" sizes="any">
{fonts}
<link rel="stylesheet" href="/assets/app.css">
{extra_head}{('<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/") + '</script>') if jsonld else ''}
</head>
<body>"""
    b = body
    b = rep(b, '<main id="main"></main>', '<main id="main">' + main + '</main>')
    if nav:
        b = rep(b, '<ol id="list"></ol>', '<ol id="list">' + nav + '</ol>')
    b = b.replace('Buku Ende Digital<small>HKBP</small></div>', '<a href="/" style="color:inherit;text-decoration:none">Buku Ende Digital</a><small>HKBP</small></div>', 1)
    tail = (f'<script>window.BE_PAGE={json.dumps(page_id)};</script>\n' if page_id else '') + abcjs + '\n<script src="/assets/app.js"></script>\n</body>\n</html>\n'
    return head + b + tail


def first_line(h):
    v = h.get("verses") or [[]]
    t = " ".join(v[0])
    return (t[:150].rsplit(" ", 1)[0] + "…") if len(t) > 155 else t


# --- halaman per lagu ---
ids = [str(x.get("id") or x["be"]) for x in index]
urls = []
for i, hid in enumerate(ids):
    h = hymns[hid]
    nv = len(h.get("verses") or [])
    title = f"Buku Ende {hid} – {h['title']} | Buku Ende Digital HKBP"
    desc = f"Buku Ende HKBP No. {hid}: {h['title']}. " + (f"Logu No. {h['bl']}. " if h.get("bl") else "") + \
           f"Lirik {nv} ayat, not angka dan not balok (do = {DO.get(h['key'], h['key'])}, {h['meter']}). " + first_line(h)
    meta = f"<span>BE <b>{E(str(h['be']).zfill(3) + (h.get('variant') or ''))}</b></span>" + \
           (f"<span>Logu <b>No. {E(h['bl'])}</b></span>" if h.get("bl") else "<span>Logu <b>tidak dicantumkan</b></span>") + \
           f"<span><b>do = {E(DO.get(h['key'], h['key']))}</b></span><span>Birama <b>{E(h['meter'])}</b></span><span>Lagu: <b>{E(h.get('credit', ''))}</b></span>"
    verses = "".join(f'<p class="verse"><span class="vn">{k + 1}.</span><span>' + "".join(f'<span class="l">{E(l)}</span>' for l in v) + "</span></p>"
                     for k, v in enumerate(h.get("verses") or []))
    pv, nx = (ids[i - 1] if i else None), (ids[i + 1] if i + 1 < len(ids) else None)
    pager = '<nav class="pager" aria-label="Ende sebelum dan sesudahnya">' + \
            (f'<a class="prev" href="/be/{pv}/" rel="prev"><span class="lbl">← Sebelumnya</span><span class="ttl"><b>{pv}</b>{E(hymns[pv]["title"])}</span></a>' if pv else "") + \
            (f'<a class="next" href="/be/{nx}/" rel="next"><span class="lbl">Berikutnya →</span><span class="ttl"><b>{nx}</b>{E(hymns[nx]["title"])}</span></a>' if nx else "") + "</nav>"
    main = f"""<header class="hymn-head"><div class="hymn-no">{E(hid)}</div><h1>{E(h['title'])}</h1><div class="meta">{meta}</div></header>
<p class="loading">Memuat not angka dan not balok…</p>
<section class="block"><h2>Ende</h2><div class="verses">{verses}</div><div class="credit">Lagu: {E(h.get('credit', ''))}</div></section>
{pager}"""
    ld = {"@context": "https://schema.org", "@type": "MusicComposition", "name": h["title"],
          "alternateName": f"Buku Ende {hid}", "url": f"{BASE}/be/{hid}/", "inLanguage": "bbc",
          "isPartOf": {"@type": "Book", "name": "Buku Ende HKBP"},
          "lyrics": {"@type": "CreativeWork", "inLanguage": "bbc", "text": "\n\n".join("\n".join(v) for v in (h.get("verses") or []))}}
    if h.get("credit"):
        ld["creditText"] = h["credit"]
    if h.get("bl"):
        ld["musicalKey"] = DO.get(h["key"], h["key"]) + " mayor"
    d = os.path.join(OUT, "be", hid)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page(f"/be/{hid}/", title, desc, main, page_id=hid, jsonld=ld))
    urls.append(f"/be/{hid}/")

# --- beranda ---
nav = "".join(f'<li><a href="/be/{hid}/"><span class="n">{E(hid)}</span><span class="t">{E(hymns[hid]["title"])}</span>'
              f'<span class="st">{("Logu " + str(hymns[hid]["bl"])) if hymns[hid].get("bl") else ""}</span></a></li>' for hid in ids)
n_main = len([x for x in index if not x.get("variant")])
home = f"""<header class="hymn-head"><div class="hymn-no">BE</div><h1>Buku Ende HKBP</h1><div class="meta"><span><b>{n_main}</b> ende</span><span>lirik · not angka · not balok</span></div></header>
<section class="block"><h2>Tentang</h2><p>Buku Ende HKBP dalam bentuk digital: lirik semua ayat, not angka, dan not balok yang bisa diputar. Pilih nomor ende di daftar, atau cari nomor BE, nomor Logu, atau judul.</p>
<p><a href="/be/1/">Mulai dari Buku Ende 1 – {E(hymns[ids[0]]['title'])}</a></p></section>"""
ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Buku Ende Digital", "url": BASE + "/", "inLanguage": "id"}
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
    page("/", "Buku Ende Digital HKBP – lirik, not angka, not balok", f"Buku Ende HKBP digital: {n_main} ende dengan lirik semua ayat, not angka, dan not balok yang bisa diputar.", home, nav=nav, jsonld=ld))
nf = """<header class="hymn-head"><div class="hymn-no">404</div><h1>Halaman tidak ditemukan</h1><div class="meta"><span>Pilih ende di daftar atau kembali ke <a href="/">beranda</a>.</span></div></header>"""
open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(page("/404.html", "Halaman tidak ditemukan | Buku Ende Digital", "Halaman tidak ditemukan.", nf, extra_head='<meta name="robots" content="noindex">\n'))

# --- sitemap & robots ---
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', f"  <url><loc>{BASE}/</loc></url>"]
sm += [f"  <url><loc>{BASE}{u}</loc></url>" for u in urls]
sm.append("</urlset>")
open(os.path.join(OUT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
print(f"ok: {len(urls)} halaman lagu + beranda + 404, sitemap {len(urls) + 1} URL, base {BASE}")
