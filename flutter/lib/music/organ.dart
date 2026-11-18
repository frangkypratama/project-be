import 'dart:isolate';
import 'dart:math' as math;
import 'dart:typed_data';

import 'notation.dart';

/// Hasil sintesis organ: berkas WAV utuh plus penanda waktu tiap nada.
class OrganRender {
  /// WAV RIFF, PCM16 mono 22050 Hz.
  final Uint8List wav;

  /// starts[i] = detik mulai Tone ke-i; entri terakhir = awal ekor gema.
  final List<double> starts;

  /// si per entri starts (entri terakhir -1).
  final List<int> si;

  /// verse per entri starts (entri terakhir -1).
  final List<int> verse;

  /// Panjang total dalam detik.
  final double seconds;

  const OrganRender({
    required this.wav,
    required this.starts,
    required this.si,
    required this.verse,
    required this.seconds,
  });
}

const int _sr = 22050;
const int _tableSize = 4096;

/// Organ pipa sintetis (port OrganPlayer.kt) yang dirender ke WAV di isolate terpisah.
Future<OrganRender> renderOrgan(List<Tone> seq,
    {required int bpm, required int transpose}) {
  final int count = seq.length;
  final List<int> midis = List<int>.filled(count, -1);
  final List<double> beats = List<double>.filled(count, 0.0);
  final List<bool> breaths = List<bool>.filled(count, false);
  final List<int> sis = List<int>.filled(count, -1);
  final List<int> verses = List<int>.filled(count, -1);
  for (int i = 0; i < count; i++) {
    final Tone t = seq[i];
    midis[i] = t.midi;
    beats[i] = t.beats;
    breaths[i] = t.breath;
    sis[i] = t.si;
    verses[i] = t.verse;
  }
  return _spawn(midis, beats, breaths, sis, verses, bpm, transpose);
}

// Fungsi terpisah agar closure untuk Isolate.run hanya menangkap data polos.
Future<OrganRender> _spawn(List<int> midis, List<double> beats,
    List<bool> breaths, List<int> sis, List<int> verses, int bpm,
    int transpose) {
  return Isolate.run<OrganRender>(
      () => _synth(midis, beats, breaths, sis, verses, bpm, transpose));
}

Float64List _buildTable() {
  const List<double> amp = <double>[
    1.0, .62, .34, .42, .1, .16, .04, .2, .03, .05, 0.0, .06
  ];
  final Float64List table = Float64List(_tableSize);
  double peak = 0.0;
  for (int i = 0; i < _tableSize; i++) {
    double v = 0.0;
    for (int h = 0; h < amp.length; h++) {
      v += amp[h] * math.sin(2 * math.pi * (h + 1) * i / _tableSize);
    }
    table[i] = v;
    final double a = v.abs();
    if (a > peak) peak = a;
  }
  if (peak > 0) {
    for (int i = 0; i < _tableSize; i++) {
      table[i] /= peak;
    }
  }
  return table;
}

/// Gema ruang gereja sederhana (Schroeder: 4 comb + 2 allpass).
class _Reverb {
  final List<Float64List> combs;
  final Int32List ci = Int32List(4);
  final Float64List cf = Float64List(4);
  final List<Float64List> aps;
  final Int32List ai = Int32List(2);

  _Reverb(int sr)
      : combs = <int>[1557, 1617, 1491, 1422]
            .map((int it) =>
                Float64List(math.max(1, (it * sr / 44100.0 * 1.6).toInt())))
            .toList(),
        aps = <int>[225, 556]
            .map((int it) => Float64List(math.max(1, (it * sr / 44100.0).toInt())))
            .toList();

  double process(double x) {
    double wet = 0.0;
    for (int k = 0; k < 4; k++) {
      final Float64List b = combs[k];
      final int idx = ci[k];
      final double y = b[idx];
      cf[k] = y * 0.6 + cf[k] * 0.4;
      b[idx] = x + cf[k] * 0.83;
      ci[k] = (idx + 1) % b.length;
      wet += y;
    }
    wet *= 0.25;
    for (int k = 0; k < 2; k++) {
      final Float64List b = aps[k];
      final int idx = ai[k];
      final double bv = b[idx];
      final double y = -wet + bv;
      b[idx] = wet + bv * 0.5;
      ai[k] = (idx + 1) % b.length;
      wet = y;
    }
    return x * 0.85 + wet * 0.45;
  }
}

double _tanh(double x) {
  if (x > 20) return 1.0;
  if (x < -20) return -1.0;
  final double e = math.exp(2 * x);
  return (e - 1) / (e + 1);
}

OrganRender _synth(List<int> midis, List<double> beats, List<bool> breaths,
    List<int> sis, List<int> verses, int bpmIn, int transpose) {
  const int sr = _sr;
  final int bpm = bpmIn <= 0 ? 84 : bpmIn;
  final int count = midis.length;
  final Float64List table = _buildTable();

  // Durasi tiap nada (detik) dan jumlah sampelnya.
  final Float64List durs = Float64List(count);
  final Int32List lens = Int32List(count);
  int total = 0;
  for (int i = 0; i < count; i++) {
    final double d = beats[i] * 60.0 / bpm;
    durs[i] = d;
    final int n = math.max(1, (d * sr).round());
    lens[i] = n;
    total += n;
  }
  final int tailLen = sr * 2;
  total += tailLen;

  final int dataLen = total * 2;
  final Uint8List wav = Uint8List(44 + dataLen);
  final ByteData bd = ByteData.view(wav.buffer);
  _writeHeader(bd, dataLen, sr);

  final List<double> starts = <double>[];
  final List<int> outSi = <int>[];
  final List<int> outVerse = <int>[];

  final _Reverb reverb = _Reverb(sr);
  int written = 0;

  void out(Float64List buf, int n) {
    int off = 44 + written * 2;
    for (int i = 0; i < n; i++) {
      final double y = reverb.process(buf[i]);
      int v = (_tanh(y) * 30000).round();
      if (v > 32767) v = 32767;
      if (v < -32768) v = -32768;
      bd.setInt16(off, v, Endian.little);
      off += 2;
    }
    written += n;
  }

  final int rel = (sr * 0.07).toInt();
  final int att = (sr * 0.035).toInt();
  Float64List carry = Float64List(0);
  double lp = 0.0;
  final double lpA = 1 - math.exp(-2 * math.pi * 4200 / sr);
  final double tableSizeD = _tableSize.toDouble();

  for (int idx = 0; idx < count; idx++) {
    final double d = durs[idx];
    final int n = lens[idx];
    starts.add(written / sr);
    outSi.add(sis[idx]);
    outVerse.add(verses[idx]);
    final Float64List buf = Float64List(n + rel + 1);
    final int m0 = midis[idx];
    if (m0 >= 0) {
      final int midi = m0 + transpose;
      final bool hasNext = idx + 1 < count;
      final int nxMidi = hasNext ? midis[idx + 1] : -1;
      double gap;
      if (breaths[idx]) {
        gap = math.min(.18, d * .25);
      } else if (!hasNext || nxMidi < 0 || nxMidi == m0) {
        gap = .06;
      } else {
        gap = .012;
      }
      final int gate = math.max(1, (math.max(.05, d - gap) * sr).round());
      final double f = 440.0 * math.pow(2.0, (midi - 69) / 12.0).toDouble();
      final double inc1 = f * _tableSize / sr;
      final double inc2 = f * 1.0016 * _tableSize / sr;
      double p1 = 0.0;
      double p2 = _tableSize * 0.25;
      final int lim = math.min(gate + rel, buf.length);
      for (int i = 0; i < lim; i++) {
        double env;
        if (i < att) {
          env = i / att;
        } else if (i < gate) {
          env = 1.0;
        } else {
          env = 1.0 - (i - gate) / rel;
        }
        final double s =
            table[p1.toInt() & 4095] * .7 + table[p2.toInt() & 4095] * .45;
        buf[i] = s * env * 0.28;
        p1 += inc1;
        if (p1 >= tableSizeD) p1 -= tableSizeD;
        p2 += inc2;
        if (p2 >= tableSizeD) p2 -= tableSizeD;
      }
    }
    final int cl = math.min(carry.length, buf.length);
    for (int i = 0; i < cl; i++) {
      buf[i] += carry[i];
    }
    for (int i = 0; i < n; i++) {
      lp += lpA * (buf[i] - lp);
      buf[i] = lp;
    }
    carry = Float64List.fromList(Float64List.sublistView(buf, n));
    out(buf, n);
  }

  // Ekor gema (sama seperti Kotlin: sisa release tanpa lowpass, lalu gema).
  final Float64List tail = Float64List(tailLen);
  final int tl = math.min(carry.length, tailLen);
  for (int i = 0; i < tl; i++) {
    tail[i] = carry[i];
  }
  starts.add(written / sr);
  outSi.add(-1);
  outVerse.add(-1);
  out(tail, tailLen);

  return OrganRender(
    wav: wav,
    starts: starts,
    si: outSi,
    verse: outVerse,
    seconds: written / sr,
  );
}

void _writeHeader(ByteData bd, int dataLen, int sr) {
  void ascii(int off, String s) {
    for (int i = 0; i < s.length; i++) {
      bd.setUint8(off + i, s.codeUnitAt(i));
    }
  }

  ascii(0, 'RIFF');
  bd.setUint32(4, 36 + dataLen, Endian.little);
  ascii(8, 'WAVE');
  ascii(12, 'fmt ');
  bd.setUint32(16, 16, Endian.little); // ukuran chunk fmt
  bd.setUint16(20, 1, Endian.little); // PCM
  bd.setUint16(22, 1, Endian.little); // mono
  bd.setUint32(24, sr, Endian.little);
  bd.setUint32(28, sr * 2, Endian.little); // byte rate
  bd.setUint16(32, 2, Endian.little); // block align
  bd.setUint16(34, 16, Endian.little); // bit per sampel
  ascii(36, 'data');
  bd.setUint32(40, dataLen, Endian.little);
}
