#!/usr/bin/env python3
"""Buat bn/site-prod/index.html (Buku Nyanyian HKBP Digital, prod) dari bn/site/index.html (dev).
Jalankan ulang setiap kali bn/site/index.html berubah: python3 bn/build/make_prod.py
Penanda __ROOT__ (akar situs) dan __BN__ (akar /bn/) diganti oleh make_static.py."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = os.path.join(ROOT, 'site', 'index.html')
dst = os.path.join(ROOT, 'site-prod', 'index.html')
s = open(src, encoding='utf-8').read()


def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:90])
    s = s.replace(a, b)


def rx(pat, repl=''):
    global s
    n = len(re.findall(pat, s, flags=re.S))
    assert n == 1, (n, pat[:70])
    s = re.sub(pat, lambda m: repl, s, flags=re.S)


# ---- judul, pengalih buku ----
rep('<title>Buku Nyanyian HKBP Digital</title>', '<title>Buku Nyanyian HKBP Digital</title>')
rep('Buku Nyanyian HKBP Digital</a><small class="dev">Dev</small></div>', 'Buku Nyanyian HKBP Digital</a></div>')
rep('<div class="brand"><a href="#beranda">', '<div class="brand"><a href="__BN__/">')
rep('<a href="https://bukuende.com/" target="_blank" rel="noopener" title="Pada situs sebenarnya: bukuende.com/">Buku Ende</a><a href="#beranda" aria-current="true">Buku Nyanyian</a>',
    '<a href="__ROOT__/">Buku Ende</a><a href="__BN__/" aria-current="true">Buku Nyanyian</a>')

# ---- CSS ----
rep('.index{align-self:start;position:sticky;top:calc(env(safe-area-inset-top,0px) + 70px);min-width:0}',
    '.index{align-self:start;position:sticky;top:calc(env(safe-area-inset-top,0px) + var(--tb,64px) + 14px);min-width:0}')
rep('.index ol{max-height:calc(100vh - 220px);overflow-y:auto}',
    '.index ol{max-height:calc(100vh - var(--tb,64px) - 190px);overflow-y:auto;scrollbar-width:thin}')
rep('@media (max-width:820px){.index ol{max-height:260px}}', '@media (max-width:820px){.index ol{max-height:340px}}')
rep('.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:16px 0 6px}',
    '.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0;position:sticky;'
    'top:calc(env(safe-area-inset-top,0px) + var(--tb,64px));z-index:4;background:var(--paper);'
    'padding-block:12px;box-shadow:0 1px 0 var(--rule)}')
extra = r'''
/* ---- prod: catatan, navigasi lagu, daftar di HP ---- */
.hymn-head{margin-top:4px}
.chip{display:inline-flex;align-items:center;font-size:11.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:2px 8px;border-radius:999px;background:var(--warn-soft);color:var(--warn)}
details.notes{margin:14px 0 0;font-size:14px;color:var(--ink-2)}
details.notes summary{cursor:pointer;display:inline-flex;flex-wrap:wrap;gap:6px 10px;align-items:center;list-style:none;padding:4px 0}
details.notes summary::-webkit-details-marker{display:none}
details.notes summary::after{content:"Lihat";font-size:13px;color:var(--gorga);text-decoration:underline;text-underline-offset:3px}
details.notes[open] summary::after{content:"Tutup"}
details.notes summary:focus-visible{outline:2px solid var(--gorga);outline-offset:3px;border-radius:4px}
details.notes ul{margin:8px 0 0;padding:12px 16px 12px 32px;background:var(--warn-soft);border-radius:10px;color:var(--ink);display:flex;flex-direction:column;gap:6px;max-width:72ch}
.xref{margin:12px 0 0;font-size:14px;color:var(--ink-2)}
.xref a{color:var(--gorga)}
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
  .index:not(.open) ol,.index:not(.open) .count{display:none}
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
rep('<h2>Daftar lagu</h2><p class="count" id="count"></p>',
    '<h2>Daftar lagu</h2><button type="button" class="list-toggle" id="listToggle" aria-expanded="false" aria-controls="list">Daftar lagu</button><p class="count" id="count"></p>')
rx(r'<p class="pilot-note">.*?</p>\s*')
rx(r'<footer>.*?</footer>',
   '<footer>Sumber: "Buku Nyanyian HKBP" susunan <b>Advendes Pasaribu</b>. '
   'Not balok dibuat otomatis dari not angka. Nomor BN adalah nomor di buku.</footer>')

# ---- daftar: tanpa status, jumlah lagu ----
rep("""+(h.status?'<span class="st">'+h.status+'</span>':'');""", "+'';")
rep('INDEX.length+" lagu termasuk varian)";', 'INDEX.length+" lagu termasuk varian)";')
rep('" dari "+TOTAL_BE+" nomor lagu ("', '" nomor lagu ("')

# ---- halaman lagu: catatan hanya untuk lagu yang ditandai "Perlu dicek" ----
rx(r"""   '<div class="status"><div><b>'\+\(h\.fixed.*?'</ul></div></div>'\+\n""",
   """   (h.status?'<details class="notes"><summary><span class="chip">Perlu dicek</span>Ada catatan pemeriksaan \\u00b7 '+(h.checks.length+mismatch.length)+' catatan</summary><ul>'+h.checks.map(function(c){return '<li>'+c+'</li>';}).join("")+mismatch.map(function(m){return '<li>'+m+'</li>';}).join("")+vlInfo(h)+beInfo(h)+'</ul></details>':'')+
   (h.becmp?'<p class="xref">Buku Logu yang sama ada di <a href="__ROOT__/be/'+h.becmp.be+'/">Buku Ende no. '+h.becmp.be+'</a>.</p>':'')+
""")
rep("""href="https://bukuende.com/be/'+c.be+'/" target="_blank" rel="noopener">Buka BE '+c.be+' \\u2197</a>""",
    """href="__ROOT__/be/'+c.be+'/">Buka BE '+c.be+'</a>""")
rep('<label class="tempo" for="bpm">Tempo <input', '<label class="tempo" for="bpm"><span class="tl">Tempo</span> <input')
rx(r"""   \(h\.refs\?'<section class="block"><h2>Referensi pembanding</h2>.*?:''\)\+\n""")
rx(r"""   '<details class="panel" id="scanPanel">.*?</details>'\+\n""")
rx(r"""  var sp=document\.getElementById\("scanPanel"\);\n  sp\.addEventListener\(.*?\n""")
rep('<details class="panel edit">', '<details class="panel edit" hidden>')

rep('  setVerse(VSEL.k,true);\n  applyView();',
    """  setVerse(VSEL.k,true);
  var pos=INDEX.map(function(x){return String(x.id||x.be);}).indexOf(String(h.id||h.be)), pv=INDEX[pos-1], nx=INDEX[pos+1];
  var pg=document.createElement("nav");pg.className="pager";pg.setAttribute("aria-label","Nyanyian sebelum dan sesudahnya");
  pg.innerHTML=(pv?'<a class="prev" href="#bn-'+(pv.id||pv.be)+'" rel="prev"><span class="lbl">\\u2190 Sebelumnya</span><span class="ttl"><b>'+(pv.id||pv.be)+'</b>'+pv.title+'</span></a>':'')+
    (nx?'<a class="next" href="#bn-'+(nx.id||nx.be)+'" rel="next"><span class="lbl">Berikutnya \\u2192</span><span class="ttl"><b>'+(nx.id||nx.be)+'</b>'+nx.title+'</span></a>':'');
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

# ---- beranda prod: tanpa keterangan pratinjau Dev ----
rep(' <i>Pratinjau Dev: tab Buku Ende membuka bukuende.com di tab baru.</i>', '')

os.makedirs(os.path.dirname(dst), exist_ok=True)
open(dst, 'w', encoding='utf-8').write(s)
print('ok', dst, len(s))
