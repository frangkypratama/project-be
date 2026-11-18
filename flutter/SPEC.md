# Buku Ende HKBP — versi Flutter: kontrak antarmuka

Port dari aplikasi Kotlin/Compose yang sudah jadi dan teruji di `../android/`
(baca sumbernya di `../android/app/src/main/java/com/bukuende/hkbp/`).
Fitur dan perilaku HARUS sama dengan versi Kotlin. Semua teks UI dalam Bahasa Indonesia.

Tidak ada Flutter/Dart SDK di mesin ini (pub.dev diblokir): kode tidak bisa dikompilasi lokal.
Build dan uji berjalan di GitHub Actions (Flutter stable terbaru, Dart 3.x, null safety, Material 3).
Karena itu: tulis Dart yang konservatif, tanpa paket di luar daftar, import lengkap, tanpa API eksperimental.

## Paket (pubspec.yaml, nama paket Dart: `hkbp`, import `package:hkbp/...`)
- shared_preferences, just_audio, path_provider, webview_flutter, wakelock_plus, share_plus, url_launcher
- dev: flutter_test, crypto, flutter_lints
Pakai API yang stabil lama (mis. `Share.share(text, subject: ...)` dari share_plus, `launchUrl(Uri, mode: LaunchMode.externalApplication)`).

## Aset (disalin oleh CI dari `../android/prepare_assets.py`)
- `assets/data/be.json`, `assets/data/bn.json` — format: `{"items":[{...}]}`, field per lagu:
  `id` (string), `t` judul, `k` kunci (default "C"), `m` birama (default "4/4"), `o` oktaf (int, opsional),
  `tp` tempo (opsional), `bl` nomor Logu (opsional), `c` kategori (opsional), `cr` daftar kredit (opsional),
  `s` bagian: `[{"n": not, "r": [baris lirik], "m"?: birama, "k"?: kunci}]`, `v` ayat `[[baris]]`,
  `vn` nomor ayat (opsional), `vl` (opsional) per ayat: `null` atau `[[baris per bagian]]` (indeks 0 selalu null).
- `assets/web/score.html`, `assets/web/abcjs.js` — penggambar not balok & halaman cetak.

## File dan API publik

### lib/data/models.dart
```dart
enum Book { be, bn }
extension BookX on Book {
  String get code;   // 'be' | 'bn'
  String get label;  // 'Buku Ende' | 'Buku Nyanyian'
  String get short;  // 'BE' | 'BN'
  String get asset;  // 'assets/data/be.json' | 'assets/data/bn.json'
  String get site;   // 'https://bukuende.com/be/' | 'https://bukuende.com/bn/'
}
class Section { final String notes; final List<String> rows; final String? meter; final String? key; const Section(...); }
class Hymn {
  final Book book; final String id; final String title; final String key; final int oct; final String meter;
  final int? tempo; final int? logu; final String? category; final List<String> credits;
  final List<Section> sections; final List<List<String>> verses; final List<int> verseNumbers;
  final List<List<List<String>>?> verseRows;   // per ayat; null = belum dipasang ke not
  int get number;          // angka di depan id ("123a" -> 123)
  String get ref;          // "BE 784"
  String get key2;         // "be:784"
  String get firstLine;    // baris pertama ayat 1 tanpa tanda baca akhir
  String get search;       // teks ternormalisasi (id, judul, semua lirik) untuk pencarian
  String verseLabel(int k);           // nomor ayat tercetak (verseNumbers[k] ?? k+1) sebagai string
  List<int> get readyVerses;          // [0] + indeks k>0 dengan verseRows[k] != null
  List<String> rowsFor(int k, int si); // persis Data.kt
  static String normal(String s);     // huruf kecil, hapus diakritik (á->a dst), non [a-z0-9 ] -> spasi, rapikan spasi
}
class Library {
  static List<Hymn> parse(Book b, String jsonText); // murni, dipakai uji
  static Future<Map<Book, List<Hymn>>> load();      // rootBundle.loadString + compute/Isolate.run untuk parse
}
```

### lib/data/prefs.dart
```dart
class Prefs extends ChangeNotifier {
  static Future<Prefs> load();          // SharedPreferences
  int theme;            // 0 sistem, 1 terang, 2 gelap   (kunci 'theme')
  double textScale;     // 0.8..1.8, default 1.0          ('textScale')
  int defaultView;      // 0 Lirik, 1 Angka, 2 Balok, 3 Keduanya, default 1 ('view')
  bool keepScreenOn;    // default true ('screenOn')
  bool playAllVerses;   // default true ('allVerses')
  List<String> get favorites;  List<String> get history;   // key2, terbaru di depan; riwayat maks 40
  void setTheme(int v); void setTextScale(double v); void setDefaultView(int v);
  void setKeepScreenOn(bool v); void setPlayAllVerses(bool v);
  bool isFavorite(String key2); void toggleFavorite(String key2); void visit(String key2); void clearHistory();
}   // setiap setter: simpan + notifyListeners()
```

### lib/music/notation.dart  (port PERSIS dari Notation.kt — diuji sidik ABC terhadap situs untuk 7.080 ayat)
```dart
class Syl { final String t; final bool cont; final bool mel; }
class El { final String raw; double dur; final bool slurStart; final bool slurEnd; int lv=0; bool hold=false; El? owner;
  int deg=0; bool rest=false; int oct=0; int acc=0; bool inSlurCont=false; bool slurEndHere=false; bool breath=false;
  List<Syl?> syl = const []; int si=-1; }
class Beat { final List<El> els = []; bool breath=false; bool exp=false; }
class Bar { final List<Beat> beats = []; String? end; }
class Line { final List<Bar> items = []; }
class Sec { final List<Line> lines; final List<String> rows; final String src; final String? meter; final String? key; }
class KeyInfo { final int li; final int tonic; final List<int> alt; final int shift; }
class Tone { final int midi; final double beats; final int si; final bool breath; final int verse; } // midi -1 = diam
class Notation {
  static const Map<String,String> doName; // "Bb"->"Bes", "Eb"->"Es", ... (lihat Kotlin DO_NAME)
  static KeyInfo keyInfo(String? key, int shift);
  static int midiOf(El e, KeyInfo ki);
  static List<Line> parseNotes(String src);
  static List<El> noteEls(List<Line> lines);
  static List<Sec> build(Hymn h, int verse);
  static double unitOf(String? meter);
  static String toAbc(Hymn h, List<Sec> secs);
  static List<Tone> sequence(Hymn h, int fromVerse, bool all);
}
String digitText(El e) => e.hold ? '·' : '${e.deg}';
```

### lib/music/organ.dart
```dart
class OrganRender { final Uint8List wav; final List<double> starts; final List<int> si; final List<int> verse; final double seconds; }
// starts[i] = detik mulai Tone ke-i; si/verse dari Tone; entri terakhir tambahan si=-1 verse=-1 di awal ekor gema.
Future<OrganRender> renderOrgan(List<Tone> seq, {required int bpm, required int transpose}); // jalan di Isolate.run
```
Sintesis = port OrganPlayer.kt (tabel gelombang harmonik, 2 osilator detune 1.0016, attack 35 ms, release 70 ms,
celah legato/napas, lowpass 4200 Hz, gema Schroeder, tanh), 22050 Hz mono PCM16, WAV RIFF, ekor 2 detik.

### lib/music/player.dart
```dart
class OrganPlayer extends ChangeNotifier {
  bool get playing; int get curSi; int get curVerse;   // -1 bila tidak bermain
  bool get preparing;                                   // sedang menyintesis
  Future<void> play(List<Tone> seq, {required int bpm, required int transpose});
  Future<void> stop();
  @override void dispose();
}
```
Tulis WAV ke `getTemporaryDirectory()/organ.wav` lalu `AudioPlayer.setFilePath` (jangan StreamAudioSource: itu butuh izin internet).
`positionStream` -> cari indeks terakhir dengan starts[i] <= posisi -> curSi/curVerse (notifyListeners hanya bila berubah).
Selesai (ProcessingState.completed) -> playing=false, curSi=-1. play() saat bermain = stop dulu.

### lib/ui/theme.dart
`ThemeData buildTheme(Brightness b)` — Material 3, `ColorScheme` eksplisit biru dari Theme.kt (Light & Dark, semua warna termasuk surfaceContainer*).

### lib/main.dart + lib/ui/app.dart
`main()`: ensureInitialized, `Prefs.load()`, `runApp(BukuEndeApp(prefs: prefs))`.
`BukuEndeApp` (AnimatedBuilder pada prefs): MaterialApp(title 'Buku Ende HKBP', theme/darkTheme/themeMode dari prefs.theme,
debugShowCheckedModeBanner false, home: `Shell`). `Shell` memuat `Library.load()` (FutureBuilder + indikator),
lalu Scaffold dengan `NavigationBar` 4 tujuan + `IndexedStack`:
Buku Ende (`HymnListScreen(book: Book.be, hymns:, prefs:)`), Buku Nyanyian (Book.bn), Tersimpan (`SavedScreen(lib:, prefs:)`),
Pengaturan (`SettingsScreen(lib:, prefs:)`). Ikon: menu_book, library_music, bookmarks, settings (outlined saat tidak terpilih).

### lib/ui/detail.dart
```dart
const List<String> kViews = ['Lirik', 'Angka', 'Balok', 'Keduanya'];
void openHymn(BuildContext context, List<Hymn> hymns, int index, Prefs prefs); // Navigator.push(MaterialPageRoute(DetailScreen))
class DetailScreen extends StatefulWidget { final List<Hymn> hymns; final int start; final Prefs prefs; }
```
Perilaku = Detail.kt: AppBar (ref + judul), favorit, bagikan (share_plus), menu (Cetak/simpan PDF -> `Printer.print`,
Info lagu, Buka di bukuende.com), SegmentedButton tampilan, PageView antarlagu (physics: geser hanya di tab Lirik,
selain itu NeverScrollableScrollPhysics), chip ayat, ScoreCard berbingkai untuk not angka/balok, bilah pemutar bawah
(‹, putar/berhenti, "Ayat x dari n · Do = .. · ♩ = ..", setel, ›), bottom sheet tempo (40..180) / nada (-6..+6) / putar semua ayat,
riwayat (`prefs.visit`) saat lagu tampil, wakelock_plus bila prefs.keepScreenOn.
Halaman lagu: tab Lirik = ListView ayat (ayat terpilih disorot, ketuk untuk memilih); tab not = SingleChildScrollView berisi
header, chip ayat, `ScoreCard('Not angka', AngkaView(...))` dan/atau `ScoreCard('Not balok', StaffView(...))`, kredit.

### lib/ui/hymn_list.dart
`HymnListScreen({required Book book, required List<Hymn> hymns, required Prefs prefs})`,
`List<(int, Hymn)> searchHymns(List<Hymn> hymns, String query, String? cat)` (persis Lists.kt),
`class NumberBadge`, `class HymnTile(hymn, fav, showBook, onTap)`. Fitur: AppBar judul "<label> HKBP" + subjudul jumlah lagu,
mode cari (TextField di AppBar), chip kategori (BN), FAB "Nomor" -> dialog nomor, daftar lagu -> `openHymn`.

### lib/ui/saved.dart
`SavedScreen({required Map<Book, List<Hymn>> lib, required Prefs prefs})` — TabBar Favorit / Terakhir dibuka, keadaan kosong, hapus riwayat (dialog).

### lib/ui/settings.dart
`SettingsScreen({required Map<Book, List<Hymn>> lib, required Prefs prefs})` — Tema (SegmentedButton Sistem/Terang/Gelap),
Ukuran huruf (Slider + contoh), Tampilan awal (kViews), Putar semua ayat, Layar tetap menyala, Hapus riwayat, Tentang, Privasi, bukuende.com.

### lib/ui/angka_view.dart
`AngkaView({required List<Sec> secs, required int curSi, required double scale, required bool bn})` — not angka native,
persis Score.kt (Wrap birama, garis atas per ketukan: `lineCount` seperti situs; ketukan `exp` garis per not min(lv,2);
titik oktaf, garis miring kres/mol, tahan '·', napas ’, garis birama | :| |], suku kata per baris, sorot not `si == curSi`).

### lib/ui/staff_view.dart
`StaffView({required String abc, required int curSi})` — webview_flutter, `loadFlutterAsset('assets/web/score.html')`,
latar transparan, JavaScriptChannel `Tinggi` (pesan = tinggi px CSS) -> SizedBox(height), dibungkus IgnorePointer.
Setelah halaman siap: `render(abcJson, inkHex, hlHex)` lalu `mark(curSi)` saat berubah (lihat score.html).

### lib/print/printer.dart
`class Printer { static Future<void> print(Hymn h); }` — susun JSON data cetak PERSIS seperti `Printer.data()` di Score.kt,
lalu `MethodChannel('bukuende/print').invokeMethod('print', {'data': jsonString, 'name': '<BE 3 Judul>'})`.

### android/app/src/main/kotlin/com/bukuende/hkbp/MainActivity.kt
FlutterActivity + MethodChannel `bukuende/print`: WebView memuat `file:///android_asset/flutter_assets/assets/web/score.html`,
`evaluateJavascript("printMode(" + data + ")")`, JS interface `Cetak.siap()` -> PrintManager (kertas F4) — port Printer.print.

### test/
- `test/notation_test.dart`: baca `assets/data/{be,bn}.json` (File), untuk tiap lagu & `readyVerses` hitung SHA-256 dari
  `Notation.toAbc(h, Notation.build(h, k))`, bandingkan dengan `../android/app/src/test/resources/abc_expected.txt`
  (baris `be:784:0 <hex>`). Harus 0 beda dan 0 tambahan. Plus uji urutan nada BE 784 (nada pertama MIDI 74).
- `test/organ_test.dart`: renderOrgan menghasilkan header WAV valid, panjang sesuai, starts naik monoton.
