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
curl -I https://bukuende.com/be/550/     # 200
curl -I https://www.bukuende.com/be/550/ # 301 ke https://bukuende.com/be/550/
curl -I https://bukuende.com/be/9999/    # 404
curl -I https://bukuende.com/bn/         # 200
curl -I https://bukuende.com/bn/62/      # 200
curl -s https://bukuende.com/sitemap-bn.xml | head -3
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
dan menulis `sitemap-bn.xml` di samping `sitemap.xml` (keduanya terdaftar di `robots.txt`).
Setelah deploy pertama yang memuat BN, kirim `https://bukuende.com/sitemap-bn.xml` di Google Search Console.

Situs dibangun di `/var/www/bukuende.new` lalu ditukar, jadi tidak pernah
tayang setengah jadi. Versi sebelumnya disimpan di `/var/www/bukuende.old`.
