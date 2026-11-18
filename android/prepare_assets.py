#!/usr/bin/env python3
"""Menyiapkan isi situs (Buku Ende di / dan Buku Nyanyian di /bn/) sebagai aset APK luring.

Dipanggil dari akar repo:  python3 android/prepare_assets.py
Hasil: android/app/src/main/assets/www
"""
import os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "android", "app", "src", "main", "assets", "www")
BASE = "https://appassets.androidplatform.net"   # bukan bukuende.com => tanpa AdSense & Tag Manager

def run(*a):
    subprocess.run([sys.executable, *a], cwd=ROOT, check=True)

shutil.rmtree(OUT, ignore_errors=True)
run("build/make_static.py", "--base", BASE, "--out", OUT, "--books")
run("bn/build/make_prod.py")
run("bn/build/make_static.py", "--base", BASE, "--out", OUT)

# berkas yang hanya berguna untuk mesin pencari / server
for f in ("redirects.map", "sitemap.xml", "robots.txt", "DEPLOY.txt", "ads.txt"):
    p = os.path.join(OUT, f)
    if os.path.exists(p):
        os.remove(p)

# pustaka not balok: dari CDN -> berkas lokal
shutil.copy(os.path.join(ROOT, "android", "abcjs-basic-min.js"), os.path.join(OUT, "assets", "abcjs.js"))
RE_ABC = re.compile(r'<script src="https://cdn\.jsdelivr\.net/npm/abcjs[^"]*"></script>')
RE_FONT = re.compile(r'<link rel="(?:preconnect|stylesheet)" href="https://fonts\.(?:googleapis|gstatic)\.com[^"]*"[^>]*>\s*')

PRIVASI = (
    '<div style="line-height:1.7;max-width:70ch;padding:0 0 24px">'
    '<p><b>Data.</b> Aplikasi ini tidak memiliki akun, formulir, atau iklan, dan tidak mengumpulkan atau mengirim data apa pun. '
    'Seluruh isi buku ada di dalam aplikasi dan dibuka tanpa internet.</p>'
    '<p><b>Penyimpanan di perangkat.</b> Pengaturan tampilan (mode gelap dan pilihan tampilan not) disimpan di perangkat Anda saja.</p>'
    '<p><b>Tautan luar.</b> Tautan ke situs lain dibuka di peramban Anda dan tunduk pada kebijakan situs tersebut.</p>'
    '</div>'
)
RE_PRIV = re.compile(r'<div style="line-height:1\.7;max-width:70ch;padding:0 0 24px">.*?</div>', re.S)
RE_META = re.compile(r'(<div class="meta"><span>)Berlaku untuk bukuende\.com[^<]*(</span>)')

n = 0
for d, _, fs in os.walk(OUT):
    for f in fs:
        if not f.endswith(".html"):
            continue
        p = os.path.join(d, f)
        s = open(p, encoding="utf-8").read()
        t = RE_ABC.sub('<script src="/assets/abcjs.js"></script>', s)
        t = RE_FONT.sub("", t)
        if os.path.relpath(p, OUT) == os.path.join("privasi", "index.html"):
            t = RE_PRIV.sub(lambda m: PRIVASI, t, count=1)
            t = RE_META.sub(r"\1Berlaku untuk aplikasi Buku Ende dan Buku Nyanyian HKBP Digital (luring)\2", t)
        if t != s:
            open(p, "w", encoding="utf-8").write(t)
            n += 1

# pemeriksaan: tidak boleh ada sumber daya jaringan yang tersisa
bad = []
for d, _, fs in os.walk(OUT):
    for f in fs:
        if f.endswith((".html", ".js", ".css")):
            s = open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()
            for pat in ("cdn.jsdelivr.net", "fonts.googleapis.com", "fonts.gstatic.com",
                        "googletagmanager.com", "pagead2.googlesyndication.com", "adsbygoogle"):
                if pat in s:
                    bad.append((os.path.relpath(os.path.join(d, f), OUT), pat))
if bad:
    print("GAGAL: masih ada sumber daya jaringan:", bad[:10])
    sys.exit(1)

files = sum(len(fs) for _, _, fs in os.walk(OUT))
size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(OUT) for f in fs)
print(f"ok: {files} berkas, {size/1e6:.1f} MB, {n} halaman disesuaikan -> {OUT}")
