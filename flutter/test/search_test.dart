// Pencarian daftar lagu (port Lists.kt) dan normalisasi teks.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:hkbp/data/models.dart';
import 'package:hkbp/ui/hymn_list.dart';

List<Hymn> _load(Book b) =>
    Library.parse(b, File('assets/data/${b.code}.json').readAsStringSync());

void main() {
  late List<Hymn> be;
  late List<Hymn> bn;

  setUpAll(() {
    be = _load(Book.be);
    bn = _load(Book.bn);
  });

  test('cari nomor: hasil pertama nomor itu sendiri', () {
    final r = searchHymns(be, '784', null);
    expect(r, isNotEmpty);
    expect(r.first.$2.id, '784');
    expect(identical(be[r.first.$1], r.first.$2), isTrue);
  });

  test('cari kata dalam lirik', () {
    expect(searchHymns(be, 'ringgas', null), isNotEmpty);
  });

  test('saring kategori BN', () {
    final cat = bn.firstWhere((h) => h.category != null).category!;
    final r = searchHymns(bn, '', cat);
    expect(r, isNotEmpty);
    for (final x in r) {
      expect(x.$2.category, cat);
    }
  });

  test('normal: huruf kecil, tanpa diakritik dan tanda baca', () {
    expect(Hymn.normal('Débata, Ho!').trim(), 'debata ho');
  });
}
