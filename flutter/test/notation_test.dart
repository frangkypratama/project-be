// Pengolah not versi Dart harus menghasilkan not balok (ABC) yang sama persis
// dengan kode situs bukuende.com, untuk semua lagu dan semua ayat yang terpasang ke not.
// Acuan (sidik SHA-256) dibuat dari kode situs:
// ../android/app/src/test/resources/abc_expected.txt
import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hkbp/data/models.dart';
import 'package:hkbp/music/notation.dart';

String _sha(String s) => sha256.convert(utf8.encode(s)).toString();

List<Hymn> _load(Book b) =>
    Library.parse(b, File('assets/data/${b.code}.json').readAsStringSync());

void main() {
  test('ABC sama dengan situs', () {
    final expected = <String, String>{};
    for (final l in File('../android/app/src/test/resources/abc_expected.txt')
        .readAsLinesSync()) {
      if (l.trim().isEmpty) continue;
      final i = l.indexOf(' ');
      if (i < 0) continue;
      expected[l.substring(0, i)] = l.substring(i + 1).trim();
    }

    final got = <String, String>{};
    final sample = <String, String>{};
    for (final b in Book.values) {
      for (final h in _load(b)) {
        for (final k in h.readyVerses) {
          String abc;
          try {
            abc = Notation.toAbc(h, Notation.build(h, k));
          } catch (_) {
            abc = 'ERR';
          }
          final key = '${b.code}:${h.id}:$k';
          got[key] = _sha(abc);
          sample[key] = abc;
        }
      }
    }

    final bad = expected.keys.where((k) => got[k] != expected[k]).toList();
    final extra = got.keys.where((k) => !expected.containsKey(k)).toList();
    if (bad.isNotEmpty) {
      // ignore: avoid_print
      print('BEDA ${bad.length} dari ${expected.length}: ${bad.take(30).toList()}');
      for (final k in bad.take(2)) {
        // ignore: avoid_print
        print('---- $k\n${sample[k]}');
      }
    }
    if (extra.isNotEmpty) {
      // ignore: avoid_print
      print('TAMBAHAN ${extra.length}: ${extra.take(30).toList()}');
    }

    expect(expected.length, greaterThan(7000), reason: 'tidak ada data');
    expect(bad, isEmpty, reason: 'ABC berbeda dari situs');
    expect(extra, isEmpty, reason: 'ayat tambahan');
  });

  test('urutan nada', () {
    final h = _load(Book.be).firstWhere((h) => h.id == '784');
    final seq = Notation.sequence(h, 0, false);
    expect(seq, isNotEmpty);
    // Do = Bes, oktaf -1: nada pertama yang berbunyi adalah 3' (D5) = MIDI 74
    expect(seq.firstWhere((t) => t.midi >= 0).midi, 74);
    final all = Notation.sequence(h, 0, true);
    expect(all.length, seq.length * h.readyVerses.length);
  });

  test('akor terpasang', () {
    var lagu = 0;
    var berakor = 0;
    for (final b in Book.values) {
      for (final h in _load(b)) {
        lagu++;
        final secs = Notation.build(h, 0, chords: true);
        for (var si = 0; si < h.sections.length; si++) {
          if (h.sections[si].chords == null) continue;
          berakor++;
          final first = <Beat>[for (final l in secs[si].lines) for (final bar in l.items) ...bar.beats];
          expect(first.isEmpty || first.first.chord != null, isTrue, reason: '${b.code}:${h.id} bagian $si tanpa akor awal');
        }
        Notation.toAbc(h, secs, chords: true);
        Notation.sequence(h, 0, true, chords: true);
      }
    }
    expect(berakor, greaterThan(lagu));
    final h = _load(Book.be).firstWhere((h) => h.id == '559');
    final abc = Notation.toAbc(h, Notation.build(h, 0, chords: true), chords: true);
    expect(abc.split('\n')[4].startsWith('"D"D4 D4 F4 F4 | "D"A8 "A"A8 | "Bm"(B4'), isTrue, reason: abc.split('\n')[4]);
    final seq = Notation.sequence(h, 0, false, chords: true);
    expect(seq.fold<int>(0, (n, t) => n + t.chordAt.length), 29);
  });
}
