# Panduan agen batch Buku Ende

Folder kerja: /tmp/claude-0/-home-claude/cbd9054d-8209-50ff-8db3-998a463a8b89/scratchpad/build
Tulis HANYA file `work/be/NNN.txt` untuk nomor BE di batch-mu. Jangan ubah site/, template, skrip, atau file batch lain. Jangan publish.

## Alat
- `python3 headers.py A B` → lembar kontak header hlm A..B (angka kanan atas = nomor ende yang MULAI di halaman itu). Perkiraan: halaman PDF ≈ 0,9 × nomor BE (BE 20→hlm 18, BE 171→hlm 155, BE 189→hlm 175).
- `python3 pg.py HAL` → work/pg/pHAL_0.png & _1.png (setengah atas/bawah, 420 dpi). Baca keduanya.
- `python3 zoom.py HAL y0 y1 [x0 x1]` → potongan 600 dpi (pecahan tinggi/lebar halaman) untuk not/kata yang ragu.
- `python3 build_site.py --check A-B` → validasi file batch-mu (ketukan per birama, jumlah not = suku kata, field wajib). Harus "OK" sebelum selesai.

## Format NNN.txt (lihat contoh work/be/004.txt, 008.txt, 010.txt, 013.txt)
```
@be 4
@bl 148                      # angka "Logu No."
@title Sai puji Debata
@key F                       # C G D A E B F Bb Eb Ab Db Gb F#  (tonika mayor = do)
@oct -1                      # opsional: bila do buku ada di oktaf bawah (mis. Bes: 1 = Bes3, 1' = Bes4)
@meter 4/4
@credit Choral Buch 156, Johann Crüger, 1647   # sesuai buku; tidak ada → (tidak dicantumkan di buku)
@pages 4 5                   # semua halaman PDF yang memuat lagu ini
@status Lirik dicek · 9/10 baris sama dgn pembanding
@check catatan keraguan/perbedaan (boleh beberapa baris @check)
@ref judul | url | catatan
#A                           # bagian; bagian yang diulang (:|) boleh punya 2 baris lirik ">"
5 | 5 5 6 6 | 5 . . v 3 | 4 3 2 3 | 2 . 1 . :|
> Sai pu-ji De-ba-ta di-baen a-si ro-ha-Na.
> Hu-hut tong-tong ba-sa di na-sa ti-nom-pa-Na.
#B
2 | 2 2 3 3 | ... | 1 . . |]
> Ri-a ma ...
#V
baris ayat 1 (teks utuh)
-
ayat 2 ...
```
Not: spasi = 1 ketukan; `.` = tahan 1 ketukan; `a+b` = dua not ½ ketukan (garis atas di buku), `.+b` = titik + ½; `1'` oktaf atas, `5,` oktaf bawah; `#4`/`b7` kres/mol (angka dicoret = kres); `0` diam; `( )` legato; `v` tanda napas; `|` `:|` `|]`. Baris baru = ganti baris (ikuti buku).
Lirik: suku kata dipisah `-`, satu suku kata per not (not lanjutan legato dilewati otomatis); `_` = suku kata sebelumnya ditahan ke not berikut tanpa legato.

## Pelajaran dari batch 1
- Tentukan nada dasar dari tanda mula + letak not 1 di paranada; lagu minor tetap pakai tonika mayor relatif (la = 6, kres = `#5`/`#4`).
- Titik di antara angka kadang hanya pemisah (mis. "6 . 5" padahal dua not 1/4): putuskan dengan not balok buku + validator ketukan. Catat di @check.
- Ketukan gantung + birama akhir/sebelum `:|` boleh pendek. Birama penuh harus genap.
- Pemenggalan ikut buku: bila buku menulis "go-ar-Mu", pakai 3 suku kata.
- Salah cetak buku DITULIS APA ADANYA, beri @check.
- Nama komponis ditulis seperti buku (boleh catat ejaan lazim di @check).

## Cek referensi (wajib setelah lirik & notasi selesai)
1. Lirik: cari URL lagu di indeks huruf bukuende.wordpress.com (`https://bukuende.wordpress.com/<huruf>/`, huruf awal judul: a b d e g h i j l m n o p r s t u). WebFetch post-nya dengan prompt:
   "Proofreading task (no quoting needed). For each of my numbered lines, reply only "Ln: MATCH" or "Ln: DIFFERS word k (spelling/different/missing/extra)", ignoring punctuation, capitalization and line-break placement." + daftar baris L1.. semua ayat.
   Jika ditolak, ulangi sekali. Untuk baris DIFFERS, cek ulang kata itu di scan (zoom.py); buku tetap acuan.
   Tulis: `@status Lirik dicek · X/Y baris sama dgn pembanding`, satu `@check Pembanding lirik: ...` (ringkas: baris mana beda, hasil cek ulang), dan `@ref Lirik pembanding: bukuende.wordpress.com (BE n) | URL | ...`.
   Bila tidak ditemukan: `@status Lirik belum ada pembanding` + @check.
2. Melodi (opsional, maks 4 pencarian per batch): bila komponis menunjuk koral terkenal, cari tune di Hymnary.org (WebSearch → hymnary.org/hymn/CCEH/.. atau /tune/..), bandingkan incipit (15 derajat nada pertama) dengan not angka. Jika sama: tambah " · melodi cocok Hymnary" di @status + @check + @ref.

## Laporan akhir (≤ 200 kata)
Daftar BE, judul, halaman, hasil validator, jumlah baris lirik cocok, dan hal yang perlu dicek manusia.

## Tambahan
- Not 1/16 kini didukung: satu ketukan bisa dibagi 4 (`3+.+.+4` = 1/8 bertitik + 1/16; `1+2+3+4` = empat 1/16). Garis atas ganda di buku = 1/16.
- Judul: bila kepala lagu mencetak judul Logu yang berbeda, @title tetap judul yang tercetak di kepala lagu itu; catat di @check bila baris pertama lirik berbeda.
- Simpan tiap lagu begitu selesai (batas pemakaian bisa memutus kerja kapan saja).
- Indeks huruf I bukuende.wordpress.com juga ada di /i-2/ (dan mungkin huruf lain: /x-2/).
- Ganti birama di tengah lagu: tulis birama bagian di header bagian, mis. `#B 3/4` (@meter = birama bagian pertama).
- Acuan halaman: BE 400 → hlm 384, BE 500 → hlm 473, BE 801 → hlm 879 (bagian akhir lebih rapat halaman). Selalu verifikasi dengan headers.py.
- Buku tidak mencetak nomor Logu → `@bl 0` + @check. JANGAN isi @bl dari situs pembanding (boleh dicatat di @check).
- BE 744 → hlm 797–798
- Triol (3 not dalam 1 ketukan): tulis `a+b+c` dalam satu ketukan (mis. `(2+1)+6,`) — situs kini menampilkannya sebagai triol di not balok.
- BE 748 → hlm 804–806
- BE 771 → hlm 839
- Ganti nada dasar di tengah lagu: tulis di header bagian, mis. `#B key=F` atau `#C 3/4 key=G`.
- Satu nomor dengan dua lagu (mis. 641a/641b): NNN.txt = versi a; versi b di NNNb.txt dengan `@be NNN` + `@variant b`. Situs menampilkannya sebagai "641b".
