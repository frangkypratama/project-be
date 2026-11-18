import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Dua buku yang dimuat aplikasi.
enum Book { be, bn }

extension BookX on Book {
  String get code {
    switch (this) {
      case Book.be:
        return 'be';
      case Book.bn:
        return 'bn';
    }
  }

  String get label {
    switch (this) {
      case Book.be:
        return 'Buku Ende';
      case Book.bn:
        return 'Buku Nyanyian';
    }
  }

  String get short {
    switch (this) {
      case Book.be:
        return 'BE';
      case Book.bn:
        return 'BN';
    }
  }

  String get asset {
    switch (this) {
      case Book.be:
        return 'assets/data/be.json';
      case Book.bn:
        return 'assets/data/bn.json';
    }
  }

  String get site {
    switch (this) {
      case Book.be:
        return 'https://bukuende.com/be/';
      case Book.bn:
        return 'https://bukuende.com/bn/';
    }
  }
}

/// Satu bagian lagu: not angka mentah + baris lirik ayat 1 (+ birama/kunci bila berganti).
class Section {
  final String notes;
  final List<String> rows;
  final String? meter;
  final String? key;

  const Section(this.notes, this.rows, [this.meter, this.key]);
}

class Hymn {
  final Book book;
  final String id;
  final String title;
  final String key;
  final int oct;
  final String meter;
  final int? tempo;
  final int? logu;
  final String? category;
  final List<String> credits;
  final List<Section> sections;
  final List<List<String>> verses;
  final List<int> verseNumbers;

  /// Baris lirik per bagian untuk ayat ke-k (indeks 0 = ayat 1 memakai Section.rows);
  /// null = belum terpasang ke not.
  final List<List<List<String>>?> verseRows;

  /// Angka di depan id ("123a" -> 123), 0 bila tidak ada.
  final int number;

  /// Baris pertama ayat 1 tanpa tanda baca akhir.
  final String firstLine;

  /// Teks ternormalisasi (id, judul, semua lirik) untuk pencarian.
  final String search;

  /// Ayat yang liriknya sudah terpasang ke not (ayat 1 selalu).
  final List<int> readyVerses;

  Hymn({
    required this.book,
    required this.id,
    required this.title,
    required this.key,
    required this.oct,
    required this.meter,
    required this.tempo,
    required this.logu,
    required this.category,
    required this.credits,
    required this.sections,
    required this.verses,
    required this.verseNumbers,
    required this.verseRows,
  })  : number = _leadingNumber(id),
        firstLine = _firstLineOf(verses),
        search = _searchText(id, title, verses),
        readyVerses = _readyOf(verseRows);

  String get ref => '${book.short} $id';

  String get key2 => '${book.code}:$id';

  /// Nomor ayat sebagaimana tercetak (BN memakai vn).
  String verseLabel(int k) {
    if (k >= 0 && k < verseNumbers.length) return verseNumbers[k].toString();
    return (k + 1).toString();
  }

  List<String> rowsFor(int k, int si) {
    if (k == 0) return sections[si].rows;
    final List<List<String>>? r =
        (k >= 0 && k < verseRows.length) ? verseRows[k] : null;
    if (r == null) return _blankRows(si);
    if (si >= 0 && si < r.length) return r[si];
    return _blankRows(si);
  }

  List<String> _blankRows(int si) =>
      List<String>.filled(sections[si].rows.length, '');

  static int _leadingNumber(String id) {
    int end = 0;
    while (end < id.length) {
      final int c = id.codeUnitAt(end);
      if (c < 0x30 || c > 0x39) break;
      end++;
    }
    if (end == 0) return 0;
    return int.tryParse(id.substring(0, end)) ?? 0;
  }

  static String _firstLineOf(List<List<String>> verses) {
    if (verses.isEmpty || verses.first.isEmpty) return '';
    final String s = verses.first.first.trim();
    int end = s.length;
    while (end > 0) {
      final String ch = s[end - 1];
      if (ch == ',' || ch == '.' || ch == ';' || ch == ':') {
        end--;
      } else {
        break;
      }
    }
    return s.substring(0, end);
  }

  static String _searchText(
      String id, String title, List<List<String>> verses) {
    final StringBuffer sb = StringBuffer();
    sb.write(id);
    sb.write(' ');
    sb.write(title);
    sb.write(' ');
    for (final List<String> v in verses) {
      for (final String line in v) {
        sb.write(line);
        sb.write(' ');
      }
    }
    return normal(sb.toString());
  }

  static List<int> _readyOf(List<List<List<String>>?> verseRows) {
    final List<int> out = <int>[0];
    for (int i = 1; i < verseRows.length; i++) {
      if (verseRows[i] != null) out.add(i);
    }
    return out;
  }

  // Huruf Latin beraksen (Latin-1, Latin Extended-A/B, Latin Extended Additional) yang
  // menurut dekomposisi NFD tinggal satu huruf dasar a-z; _foldTo memuat huruf dasarnya.
  static const String _foldFrom =
      '\u00C0\u00C1\u00C2\u00C3\u00C4\u00C5\u00C7\u00C8\u00C9\u00CA\u00CB\u00CC'
      '\u00CD\u00CE\u00CF\u00D1\u00D2\u00D3\u00D4\u00D5\u00D6\u00D9\u00DA\u00DB'
      '\u00DC\u00DD\u00E0\u00E1\u00E2\u00E3\u00E4\u00E5\u00E7\u00E8\u00E9\u00EA'
      '\u00EB\u00EC\u00ED\u00EE\u00EF\u00F1\u00F2\u00F3\u00F4\u00F5\u00F6\u00F9'
      '\u00FA\u00FB\u00FC\u00FD\u00FF\u0100\u0101\u0102\u0103\u0104\u0105\u0106'
      '\u0107\u0108\u0109\u010A\u010B\u010C\u010D\u010E\u010F\u0112\u0113\u0114'
      '\u0115\u0116\u0117\u0118\u0119\u011A\u011B\u011C\u011D\u011E\u011F\u0120'
      '\u0121\u0122\u0123\u0124\u0125\u0128\u0129\u012A\u012B\u012C\u012D\u012E'
      '\u012F\u0130\u0134\u0135\u0136\u0137\u0139\u013A\u013B\u013C\u013D\u013E'
      '\u0143\u0144\u0145\u0146\u0147\u0148\u014C\u014D\u014E\u014F\u0150\u0151'
      '\u0154\u0155\u0156\u0157\u0158\u0159\u015A\u015B\u015C\u015D\u015E\u015F'
      '\u0160\u0161\u0162\u0163\u0164\u0165\u0168\u0169\u016A\u016B\u016C\u016D'
      '\u016E\u016F\u0170\u0171\u0172\u0173\u0174\u0175\u0176\u0177\u0178\u0179'
      '\u017A\u017B\u017C\u017D\u017E\u01A0\u01A1\u01AF\u01B0\u01CD\u01CE\u01CF'
      '\u01D0\u01D1\u01D2\u01D3\u01D4\u01D5\u01D6\u01D7\u01D8\u01D9\u01DA\u01DB'
      '\u01DC\u01DE\u01DF\u01E0\u01E1\u01E6\u01E7\u01E8\u01E9\u01EA\u01EB\u01EC'
      '\u01ED\u01F0\u01F4\u01F5\u01F8\u01F9\u01FA\u01FB\u0200\u0201\u0202\u0203'
      '\u0204\u0205\u0206\u0207\u0208\u0209\u020A\u020B\u020C\u020D\u020E\u020F'
      '\u0210\u0211\u0212\u0213\u0214\u0215\u0216\u0217\u0218\u0219\u021A\u021B'
      '\u021E\u021F\u0226\u0227\u0228\u0229\u022A\u022B\u022C\u022D\u022E\u022F'
      '\u0230\u0231\u0232\u0233\u1E00\u1E01\u1E02\u1E03\u1E04\u1E05\u1E06\u1E07'
      '\u1E08\u1E09\u1E0A\u1E0B\u1E0C\u1E0D\u1E0E\u1E0F\u1E10\u1E11\u1E12\u1E13'
      '\u1E14\u1E15\u1E16\u1E17\u1E18\u1E19\u1E1A\u1E1B\u1E1C\u1E1D\u1E1E\u1E1F'
      '\u1E20\u1E21\u1E22\u1E23\u1E24\u1E25\u1E26\u1E27\u1E28\u1E29\u1E2A\u1E2B'
      '\u1E2C\u1E2D\u1E2E\u1E2F\u1E30\u1E31\u1E32\u1E33\u1E34\u1E35\u1E36\u1E37'
      '\u1E38\u1E39\u1E3A\u1E3B\u1E3C\u1E3D\u1E3E\u1E3F\u1E40\u1E41\u1E42\u1E43'
      '\u1E44\u1E45\u1E46\u1E47\u1E48\u1E49\u1E4A\u1E4B\u1E4C\u1E4D\u1E4E\u1E4F'
      '\u1E50\u1E51\u1E52\u1E53\u1E54\u1E55\u1E56\u1E57\u1E58\u1E59\u1E5A\u1E5B'
      '\u1E5C\u1E5D\u1E5E\u1E5F\u1E60\u1E61\u1E62\u1E63\u1E64\u1E65\u1E66\u1E67'
      '\u1E68\u1E69\u1E6A\u1E6B\u1E6C\u1E6D\u1E6E\u1E6F\u1E70\u1E71\u1E72\u1E73'
      '\u1E74\u1E75\u1E76\u1E77\u1E78\u1E79\u1E7A\u1E7B\u1E7C\u1E7D\u1E7E\u1E7F'
      '\u1E80\u1E81\u1E82\u1E83\u1E84\u1E85\u1E86\u1E87\u1E88\u1E89\u1E8A\u1E8B'
      '\u1E8C\u1E8D\u1E8E\u1E8F\u1E90\u1E91\u1E92\u1E93\u1E94\u1E95\u1E96\u1E97'
      '\u1E98\u1E99\u1EA0\u1EA1\u1EA2\u1EA3\u1EA4\u1EA5\u1EA6\u1EA7\u1EA8\u1EA9'
      '\u1EAA\u1EAB\u1EAC\u1EAD\u1EAE\u1EAF\u1EB0\u1EB1\u1EB2\u1EB3\u1EB4\u1EB5'
      '\u1EB6\u1EB7\u1EB8\u1EB9\u1EBA\u1EBB\u1EBC\u1EBD\u1EBE\u1EBF\u1EC0\u1EC1'
      '\u1EC2\u1EC3\u1EC4\u1EC5\u1EC6\u1EC7\u1EC8\u1EC9\u1ECA\u1ECB\u1ECC\u1ECD'
      '\u1ECE\u1ECF\u1ED0\u1ED1\u1ED2\u1ED3\u1ED4\u1ED5\u1ED6\u1ED7\u1ED8\u1ED9'
      '\u1EDA\u1EDB\u1EDC\u1EDD\u1EDE\u1EDF\u1EE0\u1EE1\u1EE2\u1EE3\u1EE4\u1EE5'
      '\u1EE6\u1EE7\u1EE8\u1EE9\u1EEA\u1EEB\u1EEC\u1EED\u1EEE\u1EEF\u1EF0\u1EF1'
      '\u1EF2\u1EF3\u1EF4\u1EF5\u1EF6\u1EF7\u1EF8\u1EF9';
  static const String _foldTo =
      'aaaaaaceeeeiiiinooooouuuuyaaaaaaceeeeiiiinooooouuuuyyaaaaaac'
      'cccccccddeeeeeeeeeegggggggghhiiiiiiiiijjkkllllllnnnnnnoooooo'
      'rrrrrrssssssssttttuuuuuuuuuuuuwwyyyzzzzzzoouuaaiioouuuuuuuuu'
      'uaaaaggkkoooojggnnaaaaaaeeeeiiiioooorrrruuuusstthhaaeeoooooo'
      'ooyyaabbbbbbccddddddddddeeeeeeeeeeffgghhhhhhhhhhiiiikkkkkkll'
      'llllllmmmmmmnnnnnnnnoooooooopppprrrrrrrrssssssssssttttttttuu'
      'uuuuuuuuvvvvwwwwwwwwwwxxxxyyzzzzzzhtwyaaaaaaaaaaaaaaaaaaaaaa'
      'aaeeeeeeeeeeeeeeeeiiiioooooooooooooooooooooooouuuuuuuuuuuuuu'
      'yyyyyyyy';

  static final Map<int, int> _fold = _buildFold();

  static Map<int, int> _buildFold() {
    final Map<int, int> m = <int, int>{};
    final int n = _foldFrom.length;
    for (int i = 0; i < n; i++) {
      m[_foldFrom.codeUnitAt(i)] = _foldTo.codeUnitAt(i);
    }
    return m;
  }

  static bool _isMark(int c) =>
      (c >= 0x0300 && c <= 0x036F) ||
      (c >= 0x1AB0 && c <= 0x1AFF) ||
      (c >= 0x1DC0 && c <= 0x1DFF) ||
      (c >= 0x20D0 && c <= 0x20FF) ||
      (c >= 0xFE20 && c <= 0xFE2F);

  /// Huruf kecil, hapus diakritik (á -> a dst), selain [a-z0-9 ] jadi spasi, spasi beruntun jadi satu.
  /// Sama dengan Kotlin: tidak memangkas spasi di awal/akhir.
  static String normal(String s) {
    final String lower = s.toLowerCase();
    final StringBuffer sb = StringBuffer();
    bool lastSpace = false;
    for (final int r in lower.runes) {
      if (_isMark(r)) continue;
      final int c = _fold[r] ?? r;
      final bool ok = (c >= 0x61 && c <= 0x7A) || (c >= 0x30 && c <= 0x39);
      if (ok) {
        sb.writeCharCode(c);
        lastSpace = false;
      } else if (!lastSpace) {
        sb.write(' ');
        lastSpace = true;
      }
    }
    return sb.toString();
  }
}

class Library {
  static Map<Book, List<Hymn>>? _cache;

  /// Hasil muat terakhir (null bila belum dimuat).
  static Map<Book, List<Hymn>>? loaded() => _cache;

  /// Memuat kedua buku dari aset; penguraian JSON berjalan di isolate terpisah.
  static Future<Map<Book, List<Hymn>>> load() async {
    final Map<Book, List<Hymn>>? c = _cache;
    if (c != null) return c;
    final List<String> texts = <String>[];
    for (final Book b in Book.values) {
      texts.add(await rootBundle.loadString(b.asset));
    }
    final Map<Book, List<Hymn>> m =
        await compute<List<String>, Map<Book, List<Hymn>>>(_parseAll, texts);
    _cache = m;
    return m;
  }

  static Map<Book, List<Hymn>> _parseAll(List<String> texts) {
    final Map<Book, List<Hymn>> m = <Book, List<Hymn>>{};
    for (int i = 0; i < Book.values.length; i++) {
      final Book b = Book.values[i];
      m[b] = parse(b, texts[i]);
    }
    return m;
  }

  // ---- pembantu JSON (meniru perilaku org.json di versi Kotlin) ----

  static String _str(Object? v) {
    if (v == null) return '';
    if (v is String) return v;
    return v.toString();
  }

  static List<String> _strings(Object? a) {
    if (a is! List) return <String>[];
    return List<String>.generate(a.length, (int i) => _str(a[i]));
  }

  static String _optString(Map<String, dynamic> o, String name,
      [String fallback = '']) {
    final Object? v = o[name];
    if (v == null) return fallback;
    return _str(v);
  }

  static String? _optNonEmpty(Map<String, dynamic> o, String name) {
    final String s = _optString(o, name);
    return s.isEmpty ? null : s;
  }

  /// Seperti JSONObject.optInt: angka -> int, teks angka -> int, selain itu fallback.
  static int _toInt(Object? v, [int fallback = 0]) {
    if (v is int) return v;
    if (v is num) {
      final double d = v.toDouble();
      return d.isFinite ? d.toInt() : fallback;
    }
    if (v is String) {
      final double? d = double.tryParse(v.trim());
      if (d == null || !d.isFinite) return fallback;
      return d.toInt();
    }
    return fallback;
  }

  /// Murni: mengurai teks JSON aset menjadi daftar lagu.
  static List<Hymn> parse(Book b, String jsonText) {
    final Object? root = jsonDecode(jsonText);
    final Map<String, dynamic> top = root as Map<String, dynamic>;
    final List<dynamic> items = top['items'] as List<dynamic>;
    final List<Hymn> out = <Hymn>[];
    for (final dynamic item in items) {
      final Map<String, dynamic> o = item as Map<String, dynamic>;

      final List<dynamic> secs = o['s'] as List<dynamic>;
      final List<Section> sections = <Section>[];
      for (final dynamic sv in secs) {
        final Map<String, dynamic> s = sv as Map<String, dynamic>;
        sections.add(Section(
          _str(s['n']),
          _strings(s['r']),
          _optNonEmpty(s, 'm'),
          _optNonEmpty(s, 'k'),
        ));
      }

      final Object? va = o['v'];
      final List<List<String>> verses = <List<String>>[];
      if (va is List) {
        for (final dynamic x in va) {
          verses.add(_strings(x));
        }
      }

      final Object? vla = o['vl'];
      final List<List<List<String>>?> vl = <List<List<String>>?>[];
      if (vla is List) {
        for (final dynamic x in vla) {
          if (x is List) {
            vl.add(List<List<String>>.generate(
                x.length, (int si) => _strings(x[si])));
          } else {
            vl.add(null);
          }
        }
      }

      final Object? vn = o['vn'];
      final List<int> verseNumbers = <int>[];
      if (vn is List) {
        for (final dynamic x in vn) {
          verseNumbers.add(_toInt(x));
        }
      }

      out.add(Hymn(
        book: b,
        id: _str(o['id']),
        title: _str(o['t']),
        key: _optString(o, 'k', 'C'),
        oct: _toInt(o['o']),
        meter: _optString(o, 'm', '4/4'),
        tempo: o.containsKey('tp') ? _toInt(o['tp']) : null,
        logu: o.containsKey('bl') ? _toInt(o['bl']) : null,
        category: _optNonEmpty(o, 'c'),
        credits: _strings(o['cr']),
        sections: sections,
        verses: verses,
        verseNumbers: verseNumbers,
        verseRows: vl,
      ));
    }
    return out;
  }
}
