# Buku Ende Digital (HKBP)

Buku Ende HKBP dalam bentuk digital: lirik semua ayat, not angka, dan not balok
yang bisa diputar. Ditranskrip dari scan buku (948 halaman), 870 ende (BE 1–864
dan 6 lagu varian).

## Struktur

| Folder | Isi |
|---|---|
| `build/work/be/NNN.txt` | **Sumber utama**: satu file per ende (kepala `@be @bl @title @key @meter …`, bagian `#A #B` berisi not angka + baris lirik `>`, lalu `#V` semua ayat) |
| `build/build_site.py` | Membaca sumber → `site/data/index.json` + `site/data/bNN.json` (20 ende per batch), sekaligus memeriksa ketukan per birama dan jumlah suku kata |
| `build/verse_align.py` | Memecah lirik ayat 2 dst per suku kata dan memasangnya ke not (dipanggil oleh `build_site.py`) |
| `site/index.html` | Versi **Dev** (catatan verifikasi, panel koreksi, scan) |
| `build/make_prod.py` | Membuat `site-prod/index.html` (versi **Prod**) dari versi Dev |
| `build/make_static.py` | Membuat `dist/`: satu halaman HTML per lagu + sitemap untuk Google |
| `icon/` | Ikon salib (`salib.ico`) |
| `docs/` | Hasil `make_static.py` untuk **GitHub Pages**: 870 halaman lagu siap dibaca Google |

Scan PDF Buku Ende dan gambar halaman **tidak** disertakan di repo.

## Membangun

```bash
python3 build/build_site.py          # sumber -> site/data
python3 build/make_prod.py           # site/index.html -> site-prod/index.html
python3 build/make_static.py --base https://domainanda.id   # -> dist/
```

Untuk membuat ulang scan halaman (panel Dev), set lokasi PDF:
`BE_PDF=/path/buku-ende.pdf python3 build/build_site.py` (perlu `pdftoppm`).

## Menjalankan di server

Situs resmi: **https://bukuende.com**. Langkah lengkap ada di [`deploy/README.md`](deploy/README.md)
(skrip `deploy/deploy.sh` dan konfigurasi `deploy/nginx-bukuende.conf`).


Isi `dist/` adalah situs statis biasa, tidak butuh Node.js atau database.
Contoh Nginx:

```nginx
server {
  server_name domainanda.id;
  root /var/www/bukuende;
  index index.html;
  location / { try_files $uri $uri/ =404; }
  error_page 404 /404.html;
  location /assets/ { expires 7d; }
  location /data/   { expires 1d; }
  gzip on; gzip_types text/css application/javascript application/json;
}
```

Lalu HTTPS dengan `certbot --nginx -d domainanda.id`, dan kirim
`https://domainanda.id/sitemap.xml` di Google Search Console.

## Supaya terbaca Google

Setiap lagu punya halaman sendiri (`/be/550/`) dengan judul, deskripsi, lirik
semua ayat langsung di HTML (tetap terbaca tanpa JavaScript), alamat kanonik,
tag Open Graph, dan data terstruktur `MusicComposition` (bahasa Batak Toba,
`bbc`). Beranda memuat tautan ke semua lagu; `sitemap.xml` berisi 871 alamat.

**Pakai GitHub Pages (gratis, tanpa server):**

1. Repo → Settings → Pages → *Deploy from a branch* → `main`, folder `/docs`.
2. Situs tampil di <https://frangkypratama.github.io/project-be/>.
3. Google Search Console → tambahkan properti *URL prefix*
   `https://frangkypratama.github.io/project-be/` → verifikasi (file HTML
   dari Search Console taruh di `docs/`) → kirim sitemap
   `https://frangkypratama.github.io/project-be/sitemap.xml`.

Di GitHub Pages proyek, `robots.txt` tidak dibaca karena tidak berada di akar
domain; itu tidak masalah karena sitemap dikirim langsung lewat Search Console.

Setiap kali data berubah, bangun ulang `docs/`:

```bash
python3 build/build_site.py && python3 build/make_prod.py
python3 build/make_static.py --base https://frangkypratama.github.io/project-be --out docs
touch docs/.nojekyll
```

**Pakai domain sendiri:** bangun ke `dist/` dengan `--base https://domainanda.id`
lalu unggah ke server (lihat Nginx di bawah). Kalau domain sendiri dipasang di
GitHub Pages (Settings → Pages → Custom domain), bangun `docs/` dengan
`--base https://domainanda.id` agar alamatnya tanpa `/project-be`.

## Cetak partitur (PDF F4)

Di situs statis (bukuende.com) setiap halaman lagu punya tombol **Cetak PDF**.
Tata letak cetak memakai kertas F4 (215 × 330 mm): kepala lagu, not angka,
not balok (sesuai pilihan tampilan dan ayat yang dipilih), semua ayat, dan
kaki halaman berisi alamat lagu. Selalu dicetak hitam di atas putih, juga
dalam mode gelap. Di jendela cetak pilih **Simpan sebagai PDF** dan ukuran
kertas **Default**. Tombol ini tidak ada di artifact Dev/Prod karena artifact
tidak mengizinkan jendela cetak.

## Uji

`build/t_*.js` memakai Playwright (`npm install` di `build/` untuk abcjs).
Contoh: `node build/t_allverses.js` membuka setiap ayat dari semua lagu.

## Status data

- Not angka dan lirik ayat 1 ditranskrip dari scan; masih berstatus draf
  verifikasi (catatan per lagu ada di baris `@check`).
- Lirik ayat 2 dst dipasang otomatis ke not: 2.578 dari 2.827 ayat;
  249 ayat belum dipasang (tidak diberi tombol ayat). Belum dicek manual.
