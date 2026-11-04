# Buku Nyanyian HKBP Digital (BN) — versi Dev

Sumber dan pembangun situs untuk Buku Nyanyian HKBP (874 lagu: BN 1–865 dan varian), dibaca dari PDF
"Buku Nyanyian HKBP" susunan Advendes Pasaribu. **Belum ditayangkan** di bukuende.com; `deploy.sh` hanya
membangun BE dari folder ini sampai ada keputusan dan izin penayangan.

| Berkas | Isi |
|---|---|
| `build/extract_pdf.py` | Tahap 1: PDF → `work/pages.json` (lapisan teks + garis vektor; tidak disertakan, buat ulang dari PDF) |
| `build/assemble.py` | Tahap 2: `pages.json` + `work/fix/*.json` → `work/bn/NNN.json` |
| `build/build_site.py` | `work/bn` → `site/data/` (index + 44 batch), validasi ketukan dan suku kata |
| `build/cmp_be.py` | Banding melodi BN dengan BE yang Buku Logu-nya sama → `work/cmp_be.json` |
| `build/work/fix/` | Koreksi per lagu hasil pemeriksaan terhadap gambar halaman |
| `build/work/review/` | Laporan 20 agen peninjau (ok/fixed/issue) |
| `site/index.html` | Halaman Dev (beranda, pengalih buku, pemutar, panel scan) |

Scan halaman (73 MB) tidak disertakan: `BN_PDF=/path/BN-HKBP.pdf python3 build/build_site.py`.
