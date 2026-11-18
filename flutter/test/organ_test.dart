// Sintesis organ: header WAV valid, panjang data sesuai, penanda waktu naik monoton.
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:hkbp/data/models.dart';
import 'package:hkbp/music/notation.dart';
import 'package:hkbp/music/organ.dart';

String _ascii(Uint8List b, int from, int len) =>
    String.fromCharCodes(b.sublist(from, from + len));

int _u32(Uint8List b, int at) =>
    b[at] | (b[at + 1] << 8) | (b[at + 2] << 16) | (b[at + 3] << 24);

void main() {
  test('renderOrgan BE 3 menghasilkan WAV valid', () async {
    final hymns = Library.parse(
        Book.be, File('assets/data/be.json').readAsStringSync());
    final h = hymns.firstWhere((x) => x.id == '3');
    final List<Tone> seq = Notation.sequence(h, 0, true);
    expect(seq, isNotEmpty);

    final OrganRender r = await renderOrgan(seq, bpm: 84, transpose: 0);
    final Uint8List wav = r.wav;

    expect(wav.length, greaterThan(44));
    expect(_ascii(wav, 0, 4), 'RIFF');
    expect(_ascii(wav, 8, 4), 'WAVE');
    expect(_u32(wav, 4), wav.length - 8, reason: 'ukuran RIFF');
    expect(_u32(wav, 24), 22050, reason: 'sample rate');
    expect(_ascii(wav, 36, 4), 'data');
    expect(_u32(wav, 40), wav.length - 44, reason: 'panjang data');

    expect(r.starts.length, seq.length + 1);
    expect(r.si.length, r.starts.length);
    expect(r.verse.length, r.starts.length);
    for (var i = 1; i < r.starts.length; i++) {
      expect(r.starts[i], greaterThanOrEqualTo(r.starts[i - 1]),
          reason: 'starts[$i] menurun');
    }
    expect(r.si.last, -1);
    expect(r.verse.last, -1);
    expect(r.seconds, greaterThan(r.starts.last));
  });
}
