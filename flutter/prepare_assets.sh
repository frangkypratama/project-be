#!/bin/sh
# Salin data lagu dan penggambar not dari proyek Android ke aset Flutter. Jalankan dari akar repo.
set -e
python3 android/prepare_assets.py
mkdir -p flutter/assets/data flutter/assets/web
cp android/app/src/main/assets/be.json android/app/src/main/assets/bn.json flutter/assets/data/
cp android/app/src/main/assets/score.html android/app/src/main/assets/abcjs.js flutter/assets/web/
