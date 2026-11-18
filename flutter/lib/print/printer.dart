import 'dart:convert';

import 'package:flutter/services.dart';

import 'package:hkbp/data/models.dart';
import 'package:hkbp/music/notation.dart';

/// Cetak / simpan PDF — port `object Printer` di Score.kt.
/// Data JSON dikirim ke sisi Android (MethodChannel `bukuende/print`), yang
/// memuat score.html, memanggil `printMode(data)` lalu membuka PrintManager.
class Printer {
  Printer._();

  static const MethodChannel _channel = MethodChannel('bukuende/print');

  /// Persis `Printer.data(h)` di Score.kt.
  static Map<String, dynamic> data(Hymn h) {
    final List<Sec> secs = Notation.build(h, 0);
    final bool bn = h.book == Book.bn;

    final List<List<String>> meta = <List<String>>[];
    void m(String k, String v) => meta.add(<String>[k, v]);
    m(h.book.short, h.id);
    m('do =', Notation.doName[h.key] ?? h.key);
    m('Birama', h.meter);
    final int? tempo = h.tempo;
    if (tempo != null) m('♩ =', '$tempo');
    final int? logu = h.logu;
    if (logu != null && logu > 0) m('Buku Logu', '$logu');
    final String? cat = h.category;
    if (cat != null) m(cat, '');

    final List<Map<String, dynamic>> jsecs = <Map<String, dynamic>>[];
    for (final Sec sec in secs) {
      final List<Map<String, dynamic>> bars = <Map<String, dynamic>>[];
      for (final Line line in sec.lines) {
        for (final Bar bar in line.items) {
          final List<Map<String, dynamic>> beats = <Map<String, dynamic>>[];
          for (final Beat beat in bar.beats) {
            final List<Map<String, dynamic>> els = <Map<String, dynamic>>[];
            for (final El e in beat.els) {
              final List<String> syl = <String>[];
              for (int r = 0; r < sec.rows.length; r++) {
                final Syl? s = r < e.syl.length ? e.syl[r] : null;
                syl.add(s == null ? '' : s.t + (s.cont ? ' -' : ''));
              }
              els.add(<String, dynamic>{
                'g': digitText(e),
                'u': e.oct > 0 ? e.oct : 0,
                'd': e.oct < 0 ? -e.oct : 0,
                'acc': e.acc,
                'hold': e.hold,
                'rest': e.rest,
                'lv': e.lv,
                'ss': e.slurStart,
                'se': e.slurEnd,
                'syl': syl,
              });
            }
            beats.add(<String, dynamic>{
              'exp': beat.exp,
              'br': beat.breath,
              'els': els,
            });
          }
          final Map<String, dynamic> jb = <String, dynamic>{'beats': beats};
          final String? end = bar.end;
          if (end != null) jb['end'] = end;
          bars.add(jb);
        }
      }
      jsecs.add(<String, dynamic>{'bars': bars});
    }

    final List<Map<String, dynamic>> verses = <Map<String, dynamic>>[];
    for (int k = 0; k < h.verses.length; k++) {
      verses.add(<String, dynamic>{
        'n': h.verseLabel(k),
        'lines': List<String>.from(h.verses[k]),
      });
    }

    return <String, dynamic>{
      'no': h.id,
      'title': h.title,
      'bn': bn,
      'meta': meta,
      'credits': List<String>.from(h.credits),
      'foot': '${h.book.label} HKBP ${h.id} – ${h.title} · '
          'bukuende.com/${h.book.code}/${h.id}/',
      'verses': verses,
      'secs': jsecs,
      'abc': Notation.toAbc(h, secs),
    };
  }

  static Future<void> print(Hymn h) async {
    try {
      final String json = jsonEncode(data(h));
      await _channel.invokeMethod<void>('print', <String, dynamic>{
        'data': json,
        'name': '${h.book.short} ${h.id} ${h.title}',
      });
    } on PlatformException {
      // diabaikan, sama seperti versi Kotlin yang tidak menampilkan galat
    } on MissingPluginException {
      // platform tanpa penangan cetak
    }
  }
}
