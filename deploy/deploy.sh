#!/bin/sh
# Bangun ulang dan tayangkan bukuende.com dari repo ini.
# Pakai di VPS:  /opt/project-be/deploy/deploy.sh
set -e
REPO=/opt/project-be
WEB=/var/www/bukuende
BASE=https://bukuende.com

cd "$REPO"
git pull --ff-only
python3 build/make_static.py --base "$BASE" --out "$WEB.new"
rm -f "$WEB.new/DEPLOY.txt"
rm -rf "$WEB.old"
[ -d "$WEB" ] && mv "$WEB" "$WEB.old"
mv "$WEB.new" "$WEB"
echo "selesai: $(git log -1 --format='%h %s')"
