#!/bin/sh
# Pasang pengalihan 301 (/be/1/ -> /be/1-judul/) di Nginx. Aman dijalankan berulang.
# Pakai di VPS:  /opt/project-be/deploy/setup-redirects.sh   (setelah deploy.sh dijalankan sekali)
set -e
CONF=${CONF:-/etc/nginx/sites-available/bukuende}
MAPCONF=${MAPCONF:-/etc/nginx/conf.d/bukuende-redirects.conf}
MAPFILE=${MAPFILE:-/etc/nginx/bukuende-redirects.map}

[ -f "$MAPFILE" ] || { echo "Belum ada $MAPFILE: jalankan deploy.sh dulu."; exit 1; }
[ -f "$CONF" ] || { echo "Tidak ada $CONF"; exit 1; }

# 1) blok map (konteks http) di berkas terpisah
cat > "$MAPCONF" <<EOT
map_hash_bucket_size 128;
map \$uri \$bk_baru {
    default "";
    include $MAPFILE;
}
EOT

# 2) baris "if" di blok server yang menyajikan situs (sebelum "location / { try_files")
if ! grep -q 'bk_baru' "$CONF"; then
  cp "$CONF" "$CONF.bak-$(date +%Y%m%d%H%M%S)"
  sed -i 's#^\([[:space:]]*\)location / { try_files#\1if ($bk_baru) { return 301 $bk_baru; }\n\n\1location / { try_files#' "$CONF"
  grep -q 'bk_baru' "$CONF" || { echo "Gagal menyisipkan baris if ke $CONF"; exit 1; }
fi

nginx -t && systemctl reload nginx
echo "pengalihan 301 aktif"
