# Deploy ke bukuende.com (VPS sendiri, Ubuntu/Debian)

## 1. DNS (di panel registrar bukuende.com)

| Tipe | Host  | Nilai    |
|------|-------|----------|
| A    | `@`   | IP VPS   |
| A    | `www` | IP VPS   |

Hapus record A/AAAA lama untuk `@` dan `www`. Tunggu sampai
`nslookup bukuende.com` menunjukkan IP VPS.

## 2. Sekali di VPS

```bash
apt update && apt install -y nginx git python3 certbot python3-certbot-nginx
ufw allow OpenSSH && ufw allow 'Nginx Full' && ufw enable

git clone https://github.com/frangkypratama/project-be /opt/project-be
/opt/project-be/deploy/deploy.sh

cp /opt/project-be/deploy/nginx-bukuende.conf /etc/nginx/sites-available/bukuende
ln -s /etc/nginx/sites-available/bukuende /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

certbot --nginx -d bukuende.com -d www.bukuende.com --redirect
certbot renew --dry-run
```

## 3. Cek

```bash
curl -I https://bukuende.com/            # 200
curl -I https://bukuende.com/be/550-tanganku-na-metmet/   # 200
curl -I https://bukuende.com/be/550/     # 301 ke /be/550-tanganku-na-metmet/
curl -I https://www.bukuende.com/be/550-tanganku-na-metmet/ # 301 ke https://bukuende.com/be/550-tanganku-na-metmet/
curl -I https://bukuende.com/be/9999/    # 404
curl -I https://bukuende.com/bn/         # 200
curl -I https://bukuende.com/bn/62-sukacita-yang-ceria/  # 200
curl -I https://bukuende.com/bn/62/      # 301 ke /bn/62-sukacita-yang-ceria/
curl -s https://bukuende.com/sitemap.xml | grep -c "/bn/"   # harus 876
curl -s https://bukuende.com/sitemap.xml | head -3
```

## 4. Google Search Console

Tambah properti **Domain** `bukuende.com`, pasang record TXT yang diberikan
di DNS registrar, verifikasi, lalu kirim sitemap
`https://bukuende.com/sitemap.xml`.

## Status

- 2026-11-03: tayang di https://bukuende.com (VPS 202.10.35.60, Ubuntu 24.04,
  Nginx 1.24). Sertifikat Let's Encrypt untuk bukuende.com + www, berlaku
  sampai 2027-02-01, diperpanjang otomatis oleh `certbot.timer`.

**Jangan salin ulang `nginx-bukuende.conf` ke `/etc/nginx/sites-available/bukuende`
setelah certbot berjalan**: certbot sudah menambahkan bagian HTTPS ke file di
server, dan menyalin ulang akan menghapusnya. `deploy.sh` tidak menyentuh
konfigurasi Nginx.

## Memperbarui

Setelah perubahan di-push ke GitHub, di VPS:

```bash
/opt/project-be/deploy/deploy.sh
```

`deploy.sh` membangun **Buku Ende** (di `/`) dan **Buku Nyanyian** (di `/bn/`) sekaligus,
dan menambahkan entri BN ke `sitemap.xml` yang sama (satu sitemap untuk BE dan BN).
Cukup satu sitemap di Google Search Console: `https://bukuende.com/sitemap.xml`. Hapus entri `sitemap-bn.xml` lama bila ada.

Situs dibangun di `/var/www/bukuende.new` lalu ditukar, jadi tidak pernah
tayang setengah jadi. Versi sebelumnya disimpan di `/var/www/bukuende.old`.

## 4. Alamat dengan judul (/be/1-judul/) dan pengalihan 301

Alamat lagu memuat nomor dan judul, mis. `/be/550-tanganku-na-metmet/` dan `/bn/62-sukacita-yang-ceria/`.
Alamat lama (`/be/550/`, `/bn/62/`) dialihkan 301 oleh Nginx memakai daftar yang dibuat `deploy.sh`
di `/etc/nginx/bukuende-redirects.map`. Pasang sekali di VPS:

```bash
/opt/project-be/deploy/deploy.sh                  # membuat /etc/nginx/bukuende-redirects.map
/opt/project-be/deploy/setup-redirects.sh         # memasang map + baris "if" di Nginx, nginx -t, reload
```

Skrip kedua aman dijalankan berulang dan menyimpan cadangan konfigurasi (`*.bak-<waktu>`).

Sebelum itu dipasang, alamat lama tetap bekerja lewat halaman pengalih (meta refresh) yang ikut dibangun.
