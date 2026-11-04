#!/usr/bin/env python3
"""Buat site-prod/index.html (Buku Ende Digital, prod) dari site/index.html (dev).
Jalankan ulang setiap kali site/index.html berubah: python3 build/make_prod.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = os.path.join(ROOT, 'site', 'index.html')
dst = os.path.join(ROOT, 'site-prod', 'index.html')
s = open(src, encoding='utf-8').read()


def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:90])
    s = s.replace(a, b)


# ---- judul (dev memakai "Buku Ende Digital Dev") ----
rep('<title>Buku Ende Digital Dev</title>', '<title>Buku Ende Digital</title>')
rep('Buku Ende Digital<small class="dev">Dev</small></div>', 'Buku Ende Digital HKBP</div>')

# ---- CSS ----
rep('.index{align-self:start;position:sticky;top:calc(env(safe-area-inset-top,0px) + 70px);min-width:0}',
    '.index{align-self:start;position:sticky;top:calc(env(safe-area-inset-top,0px) + var(--tb,64px) + 14px);min-width:0}')
rep('.index ol{max-height:calc(100vh - 220px);overflow-y:auto}',
    '.index ol{max-height:calc(100vh - var(--tb,64px) - 190px);overflow-y:auto;scrollbar-width:thin}')
rep('@media (max-width:820px){.index ol{max-height:260px}}', '@media (max-width:820px){.index ol{max-height:340px}}')
rep('.index .st{grid-column:2;font-size:12px;color:var(--warn)}',
    '.index .st{grid-column:2;font-size:12.5px;color:var(--ink-2);font-variant-numeric:tabular-nums}')
rep('.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:16px 0 6px}',
    '.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0;position:sticky;'
    'top:calc(env(safe-area-inset-top,0px) + var(--tb,64px));z-index:4;background:var(--paper);'
    'padding-block:12px;box-shadow:0 1px 0 var(--rule)}')
extra = r'''
/* ---- prod: pita gorga, catatan, navigasi lagu, daftar di HP ---- */
.brand small{font-family:var(--f-body);font-weight:400;font-size:13px;color:var(--ink-2);margin-left:2px}
.hymn-head{margin-top:4px}
.chip{display:inline-flex;align-items:center;font-size:11.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:2px 8px;border-radius:999px;background:var(--warn-soft);color:var(--warn)}
details.notes{margin:14px 0 0;font-size:14px;color:var(--ink-2)}
details.notes summary{cursor:pointer;display:inline-flex;flex-wrap:wrap;gap:6px 10px;align-items:center;list-style:none;padding:4px 0}
details.notes summary::-webkit-details-marker{display:none}
details.notes summary::after{content:"Lihat";font-size:13px;color:var(--gorga);text-decoration:underline;text-underline-offset:3px}
details.notes[open] summary::after{content:"Tutup"}
details.notes summary:focus-visible{outline:2px solid var(--gorga);outline-offset:3px;border-radius:4px}
details.notes ul{margin:8px 0 0;padding:12px 16px 12px 32px;background:var(--warn-soft);border-radius:10px;color:var(--ink);display:flex;flex-direction:column;gap:6px;max-width:72ch}
.verse{font-size:19px;line-height:1.55}
.verses{gap:24px 40px}
.pager{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:12px;margin-top:28px}
.pager a{display:flex;flex-direction:column;gap:2px;padding:12px 16px;border:1px solid var(--rule);border-radius:8px;background:var(--sheet);color:var(--ink);text-decoration:none;min-width:0}
.pager a:hover{border-color:var(--gorga)}
.pager a:focus-visible{outline:2px solid var(--gorga);outline-offset:2px}
.pager a.next{text-align:right;grid-column:2}
.pager .lbl{font-size:13px;color:var(--ink-2)}
.pager .ttl{font-family:var(--f-display);font-weight:600;font-size:16px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pager .ttl b{color:var(--ink-2);font-family:var(--f-body);font-weight:500;font-size:14px;margin-right:8px}
.list-toggle{display:none}
@media (max-width:820px){
  .index{background:var(--sheet);border:1px solid var(--rule);border-radius:8px;padding:6px 12px}
  .index h2{display:none}
  .list-toggle{display:flex;width:100%;justify-content:space-between;align-items:center;font:inherit;font-weight:500;font-size:15px;background:none;border:0;color:var(--ink);padding:8px 0;cursor:pointer}
  .list-toggle::after{content:"+";font-size:20px;line-height:1;color:var(--ink-2)}
  .index.open .list-toggle::after{content:"\2013"}
  .list-toggle:focus-visible{outline:2px solid var(--gorga);outline-offset:2px;border-radius:4px}
  .index:not(.open) ol,.index:not(.open) .pilot-note,.index:not(.open) .count{display:none}
  .index .count{margin:0 0 8px}
}
@media (max-width:520px){
  .search{flex-basis:100%}
  .tempo .tl{display:none}
  .tempo input{width:90px}
  .hymn-head{align-items:center;column-gap:14px}
  .hymn-no{grid-row:auto;font-size:30px}
  .hymn-head h1{font-size:25px}
  .hymn-head .meta{grid-column:1/-1;margin-top:6px}
  .verse{font-size:18px}
  .pager .ttl{font-size:15px}
}
'''
rep('[hidden]{display:none!important}', extra + '[hidden]{display:none!important}')

# ---- markup ----
rep('<h2>Daftar ende</h2><p class="count" id="count"></p>',
    '<h2>Daftar ende</h2><button type="button" class="list-toggle" id="listToggle" aria-expanded="false" aria-controls="list">Daftar ende</button><p class="count" id="count"></p>')
rep('<p class="pilot-note">Ditranskrip bertahap per 20 ende dari PDF scan Buku Ende HKBP. Nomor kiri = nomor BE; "Logu" = nomor di Buku Logu.</p>',
    '<p class="pilot-note">Angka kiri adalah nomor Buku Ende (BE). "Logu" adalah nomor lagu di Buku Logu.</p>')
i = s.index('<footer>'); j = s.index('</footer>') + len('</footer>')
s = s[:i] + ('<footer>Ditranskrip dari scan Buku Ende HKBP. Not balok dibuat otomatis dari not angka. '
             'Transkripsi masih berstatus draf: setiap lagu memuat catatan pemeriksaan dan scan halaman aslinya untuk dibandingkan.</footer>') + s[j:]

# ---- daftar: tanpa nomor Logu (seperti daftar BN), bukan status pengecekan ----
rep('<span class="st">\'+(h.status||"Draf \\u00b7 perlu dicek")+\'</span>\'',
    '<span class="st">\'+(h.variant?\'lagu kedua\':\'\')+\'</span>\'')
rep('INDEX.filter(function(x){return !x.variant;}).length+" dari "+TOTAL_BE+" ende sudah ditranskrip"',
    'INDEX.filter(function(x){return !x.variant;}).length+" ende"')
rep('Belum ada ende yang cocok di antara yang sudah ditranskrip.',
    'Tidak ada ende yang cocok. Coba nomor BE, nomor Logu, atau sebagian judul.')

# ---- halaman lagu ----
rep("""'<div class="status"><div><b>Draf transkripsi — belum diverifikasi.</b> Dibaca dari scan resolusi tinggi; catatan pemeriksaan:'+""",
    """'<details class="notes"><summary><span class="chip">Draf</span>Transkripsi belum diverifikasi \\u00b7 '+(h.checks.length+mismatch.length)+' catatan pemeriksaan</summary>'+""")
rep("""'</ul></div></div>'+""", """'</ul></details>'+""")
rep('<label class="tempo" for="bpm">Tempo <input', '<label class="tempo" for="bpm"><span class="tl">Tempo</span> <input')
rep('<h2>Referensi pembanding</h2>', '<h2>Lirik pembanding</h2>')
rep('<summary>Bandingkan dengan scan asli (hlm. ', '<summary>Lihat halaman buku asli (hlm. ')
rep('<details class="panel edit">', '<details class="panel edit" hidden>')

rep('  setVerse(VSEL.k,true);\n  applyView();',
    """  setVerse(VSEL.k,true);
  var pos=INDEX.map(function(x){return String(x.id||x.be);}).indexOf(String(h.id||h.be)), pv=INDEX[pos-1], nx=INDEX[pos+1];
  var pg=document.createElement("nav");pg.className="pager";pg.setAttribute("aria-label","Ende sebelum dan sesudahnya");
  pg.innerHTML=(pv?'<a class="prev" href="#be-'+(pv.id||pv.be)+'" rel="prev"><span class="lbl">\\u2190 Sebelumnya</span><span class="ttl"><b>'+(pv.id||pv.be)+'</b>'+pv.title+'</span></a>':'')+
    (nx?'<a class="next" href="#be-'+(nx.id||nx.be)+'" rel="next"><span class="lbl">Berikutnya \\u2192</span><span class="ttl"><b>'+(nx.id||nx.be)+'</b>'+nx.title+'</span></a>':'');
  main.appendChild(pg);
  applyView();""")

rep('window.addEventListener("hashchange",function(){show();window.scrollTo(0,0);});',
    """window.addEventListener("hashchange",function(){var ix=document.querySelector(".index");ix.classList.remove("open");document.getElementById("listToggle").setAttribute("aria-expanded","false");show();window.scrollTo(0,0);});
document.getElementById("listToggle").addEventListener("click",function(){var ix=document.querySelector(".index"),o=ix.classList.toggle("open");this.setAttribute("aria-expanded",String(o));});
document.getElementById("q").addEventListener("input",function(e){var ix=document.querySelector(".index");if(e.target.value.trim()){ix.classList.add("open");document.getElementById("listToggle").setAttribute("aria-expanded","true");}});
function setTB(){var t=document.querySelector(".topbar");if(t)document.documentElement.style.setProperty("--tb",t.offsetHeight+"px");}
setTB();window.addEventListener("resize",setTB);try{document.fonts.ready.then(setTB);}catch(e){}
document.addEventListener("keydown",function(e){var tg=e.target&&e.target.tagName;if(tg==="INPUT"||tg==="TEXTAREA"||tg==="SELECT"||e.altKey||e.ctrlKey||e.metaKey)return;
  var sel=e.key==="ArrowLeft"?".pager a.prev":e.key==="ArrowRight"?".pager a.next":null;var a=sel&&document.querySelector(sel);if(a){location.hash=a.getAttribute("href");}});""")


# ---- prod tanpa catatan draf, lirik pembanding, dan scan asli ----
import re
def rx(pat, repl=''):
    global s
    n = len(re.findall(pat, s, flags=re.S))
    assert n == 1, (n, pat[:60])
    s = re.sub(pat, repl, s, flags=re.S)
rx(r"'<details class=\"notes\">.*?'</ul></details>'\+\n\s*")
rx(r"\(h\.refs\?'<section class=\"block\"><h2>Lirik pembanding</h2>.*?:''\)\+\n\s*")
rx(r"'<details class=\"panel\" id=\"scanPanel\">.*?</details>'\+\n\s*")
rx(r"  var sp=document\.getElementById\(\"scanPanel\"\);\n  sp\.addEventListener\(.*?\n")
i = s.index('<footer>'); j = s.index('</footer>') + len('</footer>')
s = s[:i] + '<footer>Ditranskrip dari Buku Ende HKBP. Not balok dibuat otomatis dari not angka.</footer>' + s[j:]

# ---- prod tanpa keterangan angka kiri dan teks kaki halaman ----
_a = s.count('<p class="pilot-note">'); assert _a == 1, _a
s = re.sub(r'<p class="pilot-note">.*?</p>\s*', '', s, flags=re.S)
_b = s.count('<footer>'); assert _b == 1, _b
s = re.sub(r'\s*<footer>.*?</footer>', '', s, flags=re.S)

os.makedirs(os.path.dirname(dst), exist_ok=True)
open(dst, 'w', encoding='utf-8').write(s)
print('ok', dst, len(s))
