# Buku Nyanyian HKBP Digital (BN) — versi Dev

Sumber dan pembangun situs untuk Buku Nyanyian HKBP (874 lagu: BN 1–865 dan varian), dibaca dari PDF
"Buku Nyanyian HKBP" susunan Advendes Pasaribu. Tayang di **bukuende.com/bn/** bersama Buku Ende; `deploy/deploy.sh` membangun keduanya.

| Berkas | Isi |
|---|---|
| `build/extract_pdf.py` | Tahap 1: PDF → `work/pages.json` (lapisan teks + garis vektor; tidak disertakan, buat ulang dari PDF) |
| `build/assemble.py` | Tahap 2: `pages.json` + `work/fix/*.json` → `work/bn/NNN.json` |
| `build/build_site.py` | `work/bn` → `site/data/` (index + 44 batch), validasi ketukan dan suku kata |
| `build/cmp_be.py` | Banding melodi BN dengan BE yang Buku Logu-nya sama → `work/cmp_be.json` |


| `build/make_prod.py` | `site/index.html` (Dev) → `site-prod/index.html` (tanpa panel Dev, scan, koreksi) |
| `build/make_static.py` | `site-prod` + `site/data` → `<out>/bn/`: satu halaman per lagu, beranda, entri BN di `sitemap.xml` |
| `site/index.html` | Halaman Dev (beranda, pengalih buku, pemutar, panel scan) |

Scan halaman (73 MB) tidak disertakan: `BN_PDF=/path/BN-HKBP.pdf python3 build/build_site.py`.

Data mentah hasil ekstraksi (`build/work/`: bn, fix, review, cmp_be) **tidak disimpan di repo**; yang ada hanya data jadi di `site/data/`.
