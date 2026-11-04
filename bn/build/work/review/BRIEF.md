# Pemeriksaan data Buku Nyanyian HKBP (BN) terhadap gambar halaman PDF

Tujuan: data not angka + lirik tiap lagu diekstrak OTOMATIS dari PDF (lapisan teks + garis vektor).
Tugasmu: cocokkan data tiap lagu di jatahmu dengan gambar halaman PDF, perbaiki yang salah, dan laporkan.
Prinsip pemilik proyek: "Tunjukkan data bukan asumsi" — koreksi hanya bila gambar halaman menunjukkannya
dengan jelas. Bila ragu, JANGAN dikoreksi; laporkan sebagai "issue" dengan penjelasan apa yang terlihat.

## Lokasi
- PDF sumber: /mnt/user-data/attachments/cbd9054d-8209-50ff-8db3-998a463a8b89/8cb44d6e-578135457-BN-HKBP.pdf
  (halaman lanskap A4; satu lagu biasanya 1–2 halaman; nomor halaman ada di field `pages`)
- Data hasil ekstraksi (JANGAN diubah): /home/claude/project-bn/build/work/bn/<id>.json  (id = 3 digit + huruf varian, mis. 002, 597b)
- Petunjuk prioritas per lagu: /home/claude/project-bn/build/work/review/priority.json
  (`assemble` = peringatan ekstraksi, `validator` = ketukan/suku kata janggal, `be` = perbandingan melodi
  dengan Buku Ende yang Buku Logu-nya sama: `kemiripan` 1.0 = interval nada identik; `beda` = opcode difflib
  pada urutan interval. Buku Ende hanya pembanding; sumber kebenaran tetap halaman PDF BN.)
- Alat cek (hanya membaca): `python3 /home/claude/project-bn/build/check_one.py <id>` → menampilkan not, baris
  lirik, ayat, dan hasil validator, SUDAH termasuk koreksimu di work/fix.
- Gambar halaman: buat sendiri di folder kerjamu, mis.
  `pdftoppm -r 110 -f P -l P -png <PDF> /tmp/claude-0/-home-claude/cbd9054d-8209-50ff-8db3-998a463a8b89/scratchpad/review/agentKK/p`
  lalu buka dengan Read. Untuk detail (titik oktaf, garis atas, coretan kres) potong & perbesar:
  `pdftoppm -r 200 -f P -l P -x X -y Y -W W -H H -png ...`. Watermark miring merah di halaman abaikan.

## Format not (field `sections[i].notes`)
- Token dipisah spasi; satu token = satu ketuk (satu sel di buku). Baris baru = ganti baris (ikuti baris buku).
- `|` garis birama, `:|` akhir bagian yang diulang, `|]` garis akhir lagu.
- Elemen: `(` opsional, `#` (angka dicoret "/" di buku = naik ½) atau `b` (coret "\" = turun ½), angka `0`–`7`
  atau `.` (tahan), tanda oktaf `'` (titik di atas, satu per titik) atau `,` (titik di bawah), `/` durasi
  eksplisit opsional, `)` opsional.
- `a+b` = dua not ½ ketuk satu garis atas; `a+b+c+d` = empat not ¼ (dua garis atas); `a+b+c` = triol (hanya
  bila di buku ada angka kecil 3).
- Durasi eksplisit dipakai bila satu kelompok garis atas tidak terbagi rata: `/` = ½ ketuk, `//` = ¼ ketuk.
  Contoh: `3/+.//+2//` (3 bergaris satu, lalu . dan 2 bergaris dua = titik), not ½ ketuk sendirian `5/`
  (mis. ketuk angkat), `.+4` = tahan ½ lalu 4 ½.
- `( … )` legato: not sesudah not pertama di dalam legato TIDAK mendapat suku kata (melisma).
- Bagian (`sections`): daerah ulang `||: … :||` di buku = satu bagian berakhiran `:|`. Di luar ulang = bagian lain.
- Volta (kurung ulangan 1./2. bergaris putus-putus) BELUM dimodelkan — jangan diubah strukturnya, cukup laporkan.

## Format lirik
- `sections[i].rows`: satu baris per putaran (baris lirik ke-2 di bawah not = putaran ulang). Bagian tanpa
  ulang: satu baris (ayat 1).
- Suku kata berurutan, satu per not yang bukan istirahat (0) dan bukan lanjutan legato; suku kata satu kata
  disambung `-`, kata dipisah spasi (mis. `Hai bang-kit-lah ji-wa-ku`). `_` = not tanpa suku kata (jarang).
  Jumlah suku kata harus = jumlah not tersebut (validator memeriksa).
- Pemisahan kata (spasi vs `-`) ditebak otomatis dari kamus; perbaiki bila salah (mis. `'Ku-mau` → `'Ku mau`).
- `verses`: daftar ayat, tiap ayat = daftar baris teks; `vnum` = nomor ayatnya. Ayat 1 dibentuk dari baris lirik
  di bawah not; ayat lain dari teks bernomor di bawah not (bisa dua kolom). Pastikan semua ayat ada, urut, lengkap.

## Yang diperiksa per lagu
1. Judul, `key` (do = …; Es→Eb, Bes→Bb, As→Ab, Des→Db), `meter` (N ketuk), `bl` (Buku Logu).
2. Setiap birama: angka, titik oktaf, coretan, titik tahan, garis atas (durasi), istirahat, garis birama, tanda ulang.
3. Lirik ayat 1 (dan baris ulang): suku kata di bawah not yang benar, pemisahan kata.
4. Teks ayat lain: lengkap, urut, tidak tertukar kolom, tidak ada baris dari lagu lain.
Utamakan lagu yang punya peringatan di priority.json, tetapi lihat juga gambar halaman lagu lain di jatahmu.

## Cara memperbaiki
Tulis file /home/claude/project-bn/build/work/fix/<id>.json berisi HANYA field yang diganti (nilai lengkap field
itu), plus `note` = daftar kalimat singkat apa yang dikoreksi dan buktinya (halaman, birama/baris). Contoh:
```json
{"sections": [{"notes": "...", "rows": ["..."]}], "vl_direct": {},
 "note": ["hal. 4 birama 3: angka 4 dicoret di buku → #4"]}
```
- Bila mengganti `sections`, sertakan SEMUA bagian, dan tambahkan `"vl_direct": {}` kecuali kamu juga
  memperbaiki ayat bernot (lirik ayat lain diambil ulang dari teks otomatis).
- Bila mengganti `verses`, sertakan semua ayat dan `vnum` yang sesuai.
- Setelah menulis, jalankan check_one.py untuk lagu itu dan pastikan validator OK (atau jelaskan di note kenapa
  buku memang begitu).
- JANGAN mengubah file lain (work/bn, assemble.py, build_site.py, site/…), JANGAN menjalankan assemble.py atau
  build_site.py, JANGAN memakai tool Artifact. Hanya work/fix/<id>.json untuk id di jatahmu dan laporanmu.

## Laporan
Tulis /home/claude/project-bn/build/work/review/agentKK.json (KK = nomor agen 2 digit):
```json
[{"id": "002", "status": "ok|fixed|issue", "detail": "ringkas: apa yang dicek/dikoreksi/diragukan"}]
```
Satu entri per lagu di jatahmu. Pesan akhirmu: ringkasan angka (ok/fixed/issue) dan daftar issue penting.
