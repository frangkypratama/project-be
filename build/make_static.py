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
ap.add_argument("--books", action="store_true", help="tampilkan pengalih Buku Ende | Buku Nyanyian (situs gabungan dengan /bn/)")
a = ap.parse_args()
BASE = a.base.rstrip("/")
from urllib.parse import urlparse
P = urlparse(BASE).path.rstrip("/")  # awalan path, mis. "/project-be" untuk GitHub Pages; "" untuk domain sendiri
OUT = a.out
E = lambda s: html.escape(str(s), quote=True)

src = open(PROD, encoding="utf-8").read()
css = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
js = re.search(r"<script>(.*)</script>\s*$", src, re.S).group(1)
fonts = "\n".join(re.findall(r'<link rel="(?:preconnect|stylesheet)"[^>]*>', src))
abcjs = re.search(r'<script src="https://cdn\.jsdelivr\.net/npm/abcjs[^"]*"></script>', src).group(0)
body = src[src.index("</style>") + len("</style>"):src.index(abcjs)]


HOME_CSS = """
/* ---- beranda ---- */
.home{display:flex;flex-direction:column;gap:24px}
.home h2{margin:0 0 10px;font-size:14px;font-weight:600}
.hero{position:relative;background:var(--sheet);border:1px solid var(--rule);border-radius:12px;padding:30px 28px;overflow:hidden}
.hero h1{margin:0;font-family:var(--f-display);font-weight:700;font-size:clamp(36px,6vw,52px);line-height:1.04;letter-spacing:-.01em}
.hero .lead{margin:10px 0 22px;max-width:54ch;font-size:17px;color:var(--ink-2)}
.go{display:flex;flex-wrap:wrap;align-items:center;gap:10px}
.go label{font-family:var(--f-display);font-size:19px;margin-right:2px}
.board{display:inline-flex}
.board input{width:4.2ch;box-sizing:content-box;font-family:var(--f-num);font-size:26px;font-weight:600;font-variant-numeric:tabular-nums;letter-spacing:.04em;text-align:center;padding:3px 12px;border:1px solid var(--rule);border-radius:8px;background:var(--paper);color:var(--ink)}
.board input::placeholder{color:var(--ink-2);opacity:.6}
.board input:focus{outline:2px solid var(--gorga);outline-offset:1px;border-color:var(--gorga)}
.go .btn{font-size:15px;padding:9px 18px}
.go-msg{flex-basis:100%;margin:0;font-size:14px;color:var(--warn)}
.go-msg:empty{display:none}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));margin:0;background:var(--sheet);border:1px solid var(--rule);border-radius:12px}
.stats div{display:flex;flex-direction:column;gap:2px;padding:14px 18px;min-width:0}
.stats dd{order:-1}
.stats div+div{border-left:1px solid var(--rule)}
.stats dd{margin:0;font-family:var(--f-num);font-size:26px;font-weight:700;line-height:1.1;font-variant-numeric:tabular-nums}
.stats dt{font-size:13px;color:var(--ink-2);line-height:1.3}
.today{background:var(--gorga-soft);border-radius:12px;padding:22px 24px 24px}
.today h2{color:var(--gorga)}
.today-head{display:grid;grid-template-columns:auto minmax(0,1fr);gap:0 16px;align-items:baseline;color:var(--ink);text-decoration:none}
.today-head .no{font-family:var(--f-body);font-weight:600;font-size:34px;line-height:1;color:var(--gorga);font-variant-numeric:tabular-nums;min-width:2.2ch}
.today-head .tt{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 14px;min-width:0}
.today-head .t{font-family:var(--f-display);font-weight:600;font-size:clamp(22px,3.2vw,28px);line-height:1.2}
.today-head .lg{font-size:14px;color:var(--ink-2)}
.today-head:hover .t{text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:5px}
.today-head:focus-visible{outline:2px solid var(--gorga);outline-offset:4px}
.today-v{margin:12px 0 18px;font-family:var(--f-display);font-size:18px;line-height:1.6;max-width:60ch}
.today-v span{display:block}
.home a.btn{text-decoration:none}
.dl{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:2px 24px}
.dl a{display:flex;gap:10px;align-items:baseline;padding:7px 4px;color:var(--ink);text-decoration:none;border-bottom:1px solid var(--rule);min-width:0}
.dl a:hover{color:var(--gorga)}
.dl a:focus-visible{outline:2px solid var(--gorga);outline-offset:2px}
.dl .dn{font-family:var(--f-num);font-weight:700;font-variant-numeric:tabular-nums;min-width:3.2ch;color:var(--ink-2)}
.dl .dt{font-family:var(--f-display);min-width:0;overflow-wrap:anywhere}
.more{margin:14px 0 0}
.more a{color:var(--gorga)}
.ranges{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px}
.rng{display:flex;flex-direction:column;gap:2px;padding:12px 14px;background:var(--sheet);border:1px solid var(--rule);border-radius:10px;color:var(--ink);text-decoration:none;min-width:0}
.rng:hover{border-color:var(--gorga)}
.rng:focus-visible{outline:2px solid var(--gorga);outline-offset:2px}
.rng .rn{font-family:var(--f-num);font-weight:700;font-size:19px;font-variant-numeric:tabular-nums}
.rng .rt{font-family:var(--f-display);font-size:15px;color:var(--ink-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fchips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.fchips button{display:inline-flex;align-items:center;gap:8px;font:inherit;font-size:14px;font-weight:600;padding:8px 14px 8px 12px;border:1px solid var(--rule);border-radius:999px;background:var(--sheet);color:var(--ink);cursor:pointer}
.fchips button:hover{border-color:var(--gorga)}
.fchips button:focus-visible{outline:2px solid var(--gorga);outline-offset:2px}
.fchips button svg{width:18px;height:18px;flex:none;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.fchips button[aria-selected="true"]{background:var(--gorga);color:var(--on-accent);border-color:var(--gorga)}
.demo{background:var(--sheet);border:1px solid var(--rule);border-radius:12px;padding:16px 18px;min-height:170px;display:flex;flex-direction:column;gap:10px;min-width:0}
.demo .dtitle{margin:0;font-size:13px;color:var(--ink-2)}
.demo .dcap{margin:0;font-size:14px;color:var(--ink-2)}
.demo .verse{margin:0;font-size:18px}
.demo .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.feats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.feats div{background:var(--sheet);border:1px solid var(--rule);border-radius:10px;padding:14px 16px}
.feats h3{margin:0 0 4px;font-family:var(--f-display);font-size:18px;font-weight:600}
.feats p{margin:0;font-size:14px;color:var(--ink-2)}
@media (max-width:640px){.hero{padding:24px 18px}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.stats div:nth-child(3){border-left:0}.stats div:nth-child(n+3){border-top:1px solid var(--rule)}.feats{grid-template-columns:minmax(0,1fr)}.today{padding:18px}.today-head .no{font-size:28px}}
"""


def rep(s, old, new, cnt=1):
    assert s.count(old) == cnt, (s.count(old), old[:80])
    return s.replace(old, new)


# --- app.js: tautan nyata /be/<id>/ dan rute dari path, bukan hash ---
js = rep(js, 'a.href="#be-"+(h.id||h.be);', 'a.href=BP+"/be/"+(h.id||h.be)+"/";')
js = rep(js, """'<a class="prev" href="#be-'+(pv.id||pv.be)+'" rel="prev">""", """'<a class="prev" href="'+BP+'/be/'+(pv.id||pv.be)+'/" rel="prev">""")
js = rep(js, """'<a class="next" href="#be-'+(nx.id||nx.be)+'" rel="next">""", """'<a class="next" href="'+BP+'/be/'+(nx.id||nx.be)+'/" rel="next">""")
js = rep(js, 'fetch("data/b"+pad2(n)+".json")', 'fetch(BP+"/data/b"+pad2(n)+".json")')
js = rep(js, 'fetch("data/index.json")', 'fetch(BP+"/data/index.json")')
js = rep(js, 'if(a)location.hash=a.getAttribute("href");}});', 'if(a)location.href=a.getAttribute("href");}});')
js = rep(js, 'if(a){location.hash=a.getAttribute("href");}});', 'if(a){location.href=a.getAttribute("href");}});')
js = rep(js, """  var m=location.hash.match(/^#be-(\\d+[a-z]?)$/), n=m?m[1].replace(/^0+/,""):String(INDEX[0].id||INDEX[0].be);""",
         """  var m=location.hash.match(/^#be-(\\d+[a-z]?)$/);
  if(m){location.replace(BP+"/be/"+m[1].replace(/^0+/,"")+"/");return;} // alamat lama
  if(!window.BE_PAGE) return; // beranda: isi dari HTML statis
  var n=String(window.BE_PAGE);""")
js = js.replace('fetch("scans/b"', 'fetch(BP+"/scans/b"')
js = js.strip()
_bp = "var BP=" + json.dumps(P) + "; // awalan path situs\n"
js = (js.replace('"use strict";', '"use strict";\n' + _bp, 1) if js.startswith('"use strict";') else _bp + js)

os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
for d in ("be", "data"):
    shutil.rmtree(os.path.join(OUT, d), ignore_errors=True)
import hashlib
V = hashlib.sha1((css + HOME_CSS + js).encode("utf-8")).hexdigest()[:8]  # nomor versi: ganti isi berkas = ganti alamat, jadi cache 7 hari tidak menahan versi lama
open(os.path.join(OUT, "assets", "app.css"), "w", encoding="utf-8").write(css.strip() + "\n" + HOME_CSS)
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


def sm_label(s):
    s = re.sub(r"-{2,}", "-", str(s)).strip().rstrip("-").strip()
    return s.replace("<", "").replace(">", "")


def daftar_main(pref, label, ids_, hy):
    groups = {}
    for i in ids_:
        groups.setdefault((hy[i]["be"] - 1) // 100, []).append(i)
    out = f'<header class="hymn-head"><div class="hymn-no">No.</div><h1>Daftar {label}</h1><div class="meta"><span>{len({hy[i]["be"] for i in ids_})} nomor, urut nomor</span></div></header>'
    for g in sorted(groups):
        out += f'<section class="block"><h2>{g * 100 + 1}–{g * 100 + 100}</h2><ul class="dl">' + "".join(
            f'<li><a href="{pref}/{i}/"><span class="dn">{E(i)}</span><span class="dt">{E(hy[i]["title"])}</span></a></li>' for i in groups[g]) + "</ul></section>"
    return out


def page(path, title, desc, main, nav="", page_id=None, jsonld=None, extra_head="", extra_tail=""):
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
<meta property="og:site_name" content="Buku Ende HKBP Digital">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(url)}">
<meta property="og:locale" content="id_ID">
<link rel="icon" href="{P}/favicon.ico" sizes="any">
{fonts}
<link rel="stylesheet" href="{P}/assets/app.css?v={V}">
{extra_head}{('<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/") + '</script>') if jsonld else ''}
</head>
<body>"""
    b = body
    if a.books:
        b = b.replace("__ROOT__", P).replace("__BN__", P + "/bn")
    else:
        b = re.sub(r'<nav class="books".*?</nav>\s*', '', b, count=1, flags=re.S)
    b = rep(b, '<main id="main"></main>', '<main id="main">' + main + '</main>')
    if nav:
        b = rep(b, '<ol id="list"></ol>', '<ol id="list">' + nav + '</ol>')
    b = b.replace('Buku Ende HKBP Digital</div>', f'<a href="{P}/" style="color:inherit;text-decoration:none">Buku Ende HKBP Digital</a></div>', 1)
    tail = (f'<script>window.BE_STATIC=true;window.BE_PAGE={json.dumps(page_id)};</script>\n' if page_id else '') + abcjs + f'\n<script src="{P}/assets/app.js?v={V}"></script>\n' + extra_tail + f'</body>\n</html>\n'
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
    title = f"Buku Ende {hid} – {h['title']} | Buku Ende HKBP Digital"
    desc = f"Buku Ende HKBP No. {hid}: {h['title']}. " + (f"Logu No. {h['bl']}. " if h.get("bl") else "") + \
           f"Lirik {nv} ayat, not angka dan not balok (do = {DO.get(h['key'], h['key'])}, {h['meter']}). " + first_line(h)
    meta = f"<span>BE <b>{E(str(h['be']).zfill(3) + (h.get('variant') or ''))}</b></span>" + \
           (f"<span>Logu <b>No. {E(h['bl'])}</b></span>" if h.get("bl") else "<span>Logu <b>tidak dicantumkan</b></span>") + \
           f"<span><b>do = {E(DO.get(h['key'], h['key']))}</b></span><span>Birama <b>{E(h['meter'])}</b></span><span>Lagu: <b>{E(h.get('credit', ''))}</b></span>"
    verses = "".join(f'<p class="verse"><span class="vn">{k + 1}.</span><span>' + "".join(f'<span class="l">{E(l)}</span>' for l in v) + "</span></p>"
                     for k, v in enumerate(h.get("verses") or []))
    pv, nx = (ids[i - 1] if i else None), (ids[i + 1] if i + 1 < len(ids) else None)
    pager = '<nav class="pager" aria-label="Ende sebelum dan sesudahnya">' + \
            (f'<a class="prev" href="{P}/be/{pv}/" rel="prev"><span class="lbl">← Sebelumnya</span><span class="ttl"><b>{pv}</b>{E(hymns[pv]["title"])}</span></a>' if pv else "") + \
            (f'<a class="next" href="{P}/be/{nx}/" rel="next"><span class="lbl">Berikutnya →</span><span class="ttl"><b>{nx}</b>{E(hymns[nx]["title"])}</span></a>' if nx else "") + "</nav>"
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
nav = "".join(f'<li><a href="{P}/be/{hid}/"><span class="n">{E(hid)}</span><span class="t">{E(hymns[hid]["title"])}</span>'
              f'<span class="st">{"lagu kedua" if hymns[hid].get("variant") else ""}</span></a></li>' for hid in ids)
n_main = len([x for x in index if not x.get("variant")])
all_h = [hymns[i] for i in ids]
n_ayat = sum(len(h.get("verses") or []) for h in all_h)
n_logu = sum(1 for h in all_h if h.get("bl"))
n_vl = sum(1 for h in all_h for v in (h.get("vl") or [])[1:] if v and v.get("r")) + sum(1 for h in all_h if h.get("verses"))
fmt = lambda n: f"{n:,}".replace(",", ".")
first = hymns[ids[0]]
ranges = []
for r0 in range(1, 865, 100):
    xs = [hymns[i] for i in ids if r0 <= hymns[i]["be"] < r0 + 100 and not hymns[i].get("variant")]
    if xs:
        ranges.append((r0, xs[-1]["be"], xs[0]))
tiles = "".join(f'<a class="rng" href="{P}/be/{h["be"]}/"><span class="rn">{a}–{b}</span><span class="rt">{h["be"]}. {E(h["title"])}</span></a>' for a, b, h in ranges)
v1 = "".join(f"<span>{E(l)}</span>" for l in (first.get("verses") or [[]])[0])
logu1 = f"Logu No. {first['bl']}" if first.get("bl") else ""
home = f"""<div class="home">
<section class="hero">
  <h1>Buku Ende</h1>
  <p class="lead">Nyanyikan, mainkan, dan dengarkan {fmt(n_main)} ende HKBP, lengkap dengan not angka, not balok, dan semua ayatnya.</p>
  <form class="go" id="goForm" autocomplete="off">
    <label for="goNo">Ende nomor</label>
    <span class="board"><input id="goNo" inputmode="numeric" placeholder="550" maxlength="5" aria-describedby="goMsg"></span>
    <button type="submit" class="btn primary">Buka</button>
    <p class="go-msg" id="goMsg" role="status"></p>
  </form>
</section>
<dl class="stats">
  <div><dt>Ende</dt><dd>{fmt(n_main)}</dd></div>
  <div><dt>Ayat</dt><dd>{fmt(n_ayat)}</dd></div>
  <div><dt>Ayat dengan lirik di bawah not</dt><dd>{fmt(n_vl)}</dd></div>
  <div><dt>Dengan nomor Logu</dt><dd>{fmt(n_logu)}</dd></div>
</dl>
<section class="today" aria-labelledby="todayH">
  <h2 id="todayH">Ende hari ini</h2>
  <a class="today-head" id="todayLink" href="{P}/be/{first['be']}/"><span class="no" id="todayNo">{first['be']}</span><span class="tt"><span class="t" id="todayTitle">{E(first['title'])}</span><span class="lg" id="todayLogu">{logu1}</span></span></a>
  <p class="today-v" id="todayVerse">{v1}</p>
  <a class="btn" id="todayBtn" href="{P}/be/{first['be']}/">Buka ende ini</a>
</section>
<section class="block"><h2>Per seratus nomor</h2><div class="ranges">{tiles}</div><p class="more"><a href="{P}/daftar/">Lihat daftar lengkap {fmt(n_main)} ende beserta judulnya →</a></p></section>
<section class="block"><h2>Fitur</h2><div class="fchips" role="tablist" aria-label="Fitur di setiap ende">
<button type="button" role="tab" data-f="angka"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5h8M12 9v10M9.5 11.5 12 9"/></svg>Not angka</button>
<button type="button" role="tab" data-f="balok"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 8h18M3 11h18M3 14h18M3 17h18"/><circle cx="9" cy="14" r="2"/><path d="M11 14V6"/></svg>Not balok</button>
<button type="button" role="tab" data-f="putar"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z"/></svg>Putar</button>
<button type="button" role="tab" data-f="ayat"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M5 12h14M5 17h9"/></svg>Ayat</button></div>
<div class="demo" id="demo" role="tabpanel"><p class="dtitle">Memuat contoh…</p></div></section>
</div>"""
home_js = r"""<script>
(function(){
  var BP=__BP__, IDX=null, f=document.getElementById("goForm"), inp=document.getElementById("goNo"), msg=document.getElementById("goMsg");
  function load(){return IDX?Promise.resolve(IDX):fetch(BP+"/data/index.json").then(function(r){return r.json();}).then(function(j){IDX=j;return j;});}
  function go(id){location.href=BP+"/be/"+id+"/";}
  f.addEventListener("submit",function(e){e.preventDefault();var v=inp.value.trim().toLowerCase().replace(/^be\s*-?\s*/,"").replace(/^0+/,"");
    if(!v){inp.focus();return;}
    load().then(function(ix){var hit=ix.filter(function(x){return String(x.id||x.be)===v;})[0];
      if(hit)go(hit.id||hit.be);else{msg.textContent="Tidak ada ende nomor "+v+".";inp.select();}});});
  inp.addEventListener("input",function(){msg.textContent="";});
  // ende hari ini + contoh fitur: dipilih acak setiap kali beranda dibuka; utamakan ende yang punya lebih dari satu ayat berlirik
  var DEMO=null;
  function demoFeat(f){
    var d=document.getElementById("demo"); if(!d||!DEMO) return; stopAudio();
    document.querySelectorAll(".fchips button").forEach(function(b){var on=b.dataset.f===f;b.setAttribute("aria-selected",String(on));b.tabIndex=on?0:-1;});
    var h=DEMO.h, s0=DEMO.secs[0], ln={}; for(var kk in s0.lines[0]) ln[kk]=s0.lines[0][kk]; ln.items=s0.lines[0].items.slice(0,6);
    var one={lines:[ln],rows:s0.rows.slice(0,1),src:"",meter:s0.meter,key:s0.key};
    var head='<p class="dtitle">BE '+(h.id||h.be)+' \u00b7 '+h.title+'</p>';
    if(f==="angka"){
      d.innerHTML=head+'<div class="angka" id="dAngka"></div>'; renderAngka(one,document.getElementById("dAngka"),1);
    }else if(f==="balok"||f==="putar"){
      d.innerHTML=head+(f==="putar"?'<div class="row"><button type="button" class="btn primary" id="playBtn">'+PLAY_LABEL+'</button></div>':'')+'<div class="staff" id="staff"></div>';
      drawStaff(h,[one]);
      var pb=document.getElementById("playBtn");
      if(pb) pb.addEventListener("click",function(){if(audio.playing){stopAudio();return;}VALL=false;VSEL={id:h.id||h.be,k:0};playHymn(h,[one]);});
    }else{
      var rd=vReady(h);
      d.innerHTML=head+'<div class="vbar"><span class="vl" id="dvl">Ayat</span><div class="vchips" role="group" aria-labelledby="dvl">'+rd.map(function(k){return '<button type="button" data-k="'+k+'" aria-pressed="'+(k===0)+'">'+(k+1)+'</button>';}).join("")+'</div></div><p class="verse" id="dVerse"></p>';
      var show1=function(k){document.getElementById("dVerse").innerHTML='<span class="vn">'+(k+1)+'.</span><span>'+(h.verses[k]||[]).map(function(l){return '<span class="l">'+l+'</span>';}).join("")+'</span>';d.querySelectorAll(".vchips button").forEach(function(b){b.setAttribute("aria-pressed",String(+b.dataset.k===k));});};
      d.querySelectorAll(".vchips button").forEach(function(b){b.addEventListener("click",function(){show1(+b.dataset.k);});});
      show1(0);
    }
  }
  document.querySelectorAll(".fchips button").forEach(function(b){b.addEventListener("click",function(){demoFeat(b.dataset.f);});});
  function pick(ix,n){
    var e=ix[Math.floor(Math.random()*ix.length)], id=e.id||e.be;
    return fetch(BP+"/data/b"+("0"+e.batch).slice(-2)+".json").then(function(r){return r.json();}).then(function(arr){
      var h=arr.filter(function(x){return String(x.id||x.be)===String(id);})[0];
      if(h&&(vReady(h).length>1||n>=5)) return h;
      return pick(ix,n+1);
    });
  }
  load().then(function(ix){return pick(ix,0);}).then(function(h){
    if(!h) return; var id=h.id||h.be;
    document.getElementById("todayLink").href=BP+"/be/"+id+"/"; document.getElementById("todayBtn").href=BP+"/be/"+id+"/";
    document.getElementById("todayNo").textContent=id; document.getElementById("todayTitle").textContent=h.title;
    document.getElementById("todayLogu").textContent=h.bl?"Logu No. "+h.bl:"";
    var v=document.getElementById("todayVerse"); v.textContent=""; (h.verses[0]||[]).forEach(function(l){var s=document.createElement("span");s.textContent=l;v.appendChild(s);});
    try{DEMO={h:h,secs:buildSecs(h)};demoFeat("angka");}catch(err){var dm=document.getElementById("demo");if(dm)dm.innerHTML='<p class="dcap">Contoh tidak bisa dimuat.</p>';}
  }).catch(function(){});
})();
</script>
""".replace("__BP__", json.dumps(P))
ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Buku Ende HKBP Digital", "url": BASE + "/", "inLanguage": "id"}
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
    page("/", "Buku Ende HKBP Digital – lirik, not angka, not balok", f"Buku Ende HKBP digital: {n_main} ende dengan lirik semua ayat, not angka, dan not balok yang bisa diputar.", home, nav=nav, jsonld=ld, extra_tail=home_js))
nf = f"""<header class="hymn-head"><div class="hymn-no">404</div><h1>Halaman tidak ditemukan</h1><div class="meta"><span>Pilih ende di daftar atau kembali ke <a href="{P}/">beranda</a>.</span></div></header>"""
open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(page("/404.html", "Halaman tidak ditemukan | Buku Ende HKBP Digital", "Halaman tidak ditemukan.", nf, extra_head='<meta name="robots" content="noindex">\n'))

# --- daftar lengkap (nomor + judul) ---
os.makedirs(os.path.join(OUT, "daftar"), exist_ok=True)
open(os.path.join(OUT, "daftar", "index.html"), "w", encoding="utf-8").write(page(
    "/daftar/", "Daftar Ende HKBP – nomor dan judul | Buku Ende HKBP Digital",
    f"Daftar lengkap {n_main} ende HKBP berdasarkan nomor Buku Ende, dengan judul masing-masing.",
    daftar_main(f"{P}/be", "Ende", ids, hymns), nav=nav))

# --- sitemap & robots ---
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', f"  <url><loc>{BASE}/</loc></url> <!-- Beranda Buku Ende -->"]
sm.append(f"  <url><loc>{BASE}/daftar/</loc></url> <!-- Daftar lengkap nomor dan judul -->")
sm += [f"  <url><loc>{BASE}{u}</loc></url> <!-- {sm_label(u.split('/')[2] + '. ' + hymns[u.split('/')[2]]['title'])} -->" for u in urls]
sm.append("</urlset>")
open(os.path.join(OUT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
print(f"ok: {len(urls)} halaman lagu + beranda + 404, sitemap {len(urls) + 2} URL, base {BASE}")
