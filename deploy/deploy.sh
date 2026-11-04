#!/bin/sh
# Bangun ulang dan tayangkan bukuende.com (Buku Ende di / dan Buku Nyanyian di /bn/) dari repo ini.
# Pakai di VPS:  /opt/project-be/deploy/deploy.sh
set -e
REPO=/opt/project-be
WEB=/var/www/bukuende
BASE=https://bukuende.com

cd "$REPO"
git pull --ff-only
rm -rf "$WEB.new"
python3 build/make_static.py --base "$BASE" --out "$WEB.new" --books
python3 bn/build/make_prod.py
python3 bn/build/make_static.py --base "$BASE" --out "$WEB.new"
rm -f "$WEB.new/DEPLOY.txt"
# daftar pengalihan 301 (/be/1/ -> /be/1-judul/) dibaca Nginx, bukan disajikan ke publik
if [ -f "$WEB.new/redirects.map" ]; then
  [ -d /etc/nginx ] && cp "$WEB.new/redirects.map" /etc/nginx/bukuende-redirects.map
  rm -f "$WEB.new/redirects.map"
fi
rm -rf "$WEB.old"
[ -d "$WEB" ] && mv "$WEB" "$WEB.old"
mv "$WEB.new" "$WEB"
if command -v nginx >/dev/null 2>&1 && grep -qs bukuende-redirects /etc/nginx/sites-enabled/* 2>/dev/null; then
  nginx -t && systemctl reload nginx || echo "PERINGATAN: Nginx tidak dimuat ulang, periksa konfigurasi"
fi
echo "selesai: $(git log -1 --format='%h %s')"
