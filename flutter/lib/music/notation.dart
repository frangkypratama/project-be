// Pembaca not angka (port persis dari Notation.kt, yang merupakan port dari situs bukuende.com).
// - spasi memisah ketukan; | garis birama; :| ulang; |] akhir; baris baru = ganti baris
// - 1-7 nada, 0 diam, . tahan satu ketukan (atau setengah dalam kelompok +)
// - ' sesudah angka = oktaf atas, , = oktaf bawah, # / b di depan = naik/turun setengah
// - a+b = dua not dalam satu ketukan; ( ) = legato; v = tanda napas

import '../data/models.dart';

class Syl {
  final String t;
  final bool cont;
  final bool mel;
  const Syl(this.t, this.cont, [this.mel = false]);
}

class El {
  final String raw;
  double dur;
  final bool slurStart;
  final bool slurEnd;

  /// jumlah garis atas pada penulisan durasi eksplisit (BN: 1/ = 1 garis, 1// = 2 garis)
  int lv = 0;
  bool hold = false;
  El? owner;
  int deg = 0;
  bool rest = false;
  int oct = 0;
  int acc = 0;
  bool inSlurCont = false;
  bool slurEndHere = false;
  bool breath = false;
  List<Syl?> syl = const [];

  /// indeks not (tanpa tahanan) di seluruh lagu = urutan not di not balok
  int si = -1;

  El(this.raw, this.dur, this.slurStart, this.slurEnd);
}

class Beat {
  final List<El> els = [];
  bool breath = false;
  bool exp = false;
}

class Bar {
  final List<Beat> beats = [];
  String? end;
}

class Line {
  final List<Bar> items = [];
}

class Sec {
  final List<Line> lines;
  final List<String> rows;
  final String src;
  final String? meter;
  final String? key;
  const Sec(this.lines, this.rows, this.src, this.meter, this.key);
}

class KeyInfo {
  final int li;
  final int tonic;
  final List<int> alt;
  final int shift;
  const KeyInfo(this.li, this.tonic, this.alt, this.shift);
}

/// Satu bunyi (atau diam, midi -1) dalam urutan pemutaran.
class Tone {
  final int midi;
  final double beats;
  final int si;
  final bool breath;
  final int verse;
  const Tone(this.midi, this.beats, this.si, this.breath, this.verse);
}

String digitText(El e) => e.hold ? '·' : '${e.deg}';

class _Item {
  final El e;
  final double u;
  final KeyInfo k;
  const _Item(this.e, this.u, this.k);
}

class Notation {
  Notation._();

  static const String _letters = 'CDEFGAB';
  static const List<int> _nat = [0, 2, 4, 5, 7, 9, 11];
  static const List<int> _maj = _nat;

  // kunci -> [indeks huruf, alterasi]
  static const Map<String, List<int>> _keys = {
    'C': [0, 0],
    'G': [4, 0],
    'D': [1, 0],
    'A': [5, 0],
    'E': [2, 0],
    'B': [6, 0],
    'F': [3, 0],
    'Bb': [6, -1],
    'Eb': [2, -1],
    'Ab': [5, -1],
    'Db': [1, -1],
    'Gb': [4, -1],
    'F#': [3, 1],
  };

  static const Map<String, String> doName = {
    'C': 'C',
    'G': 'G',
    'D': 'D',
    'A': 'A',
    'E': 'E',
    'B': 'B',
    'F': 'F',
    'Bb': 'Bes',
    'Eb': 'Es',
    'Ab': 'As',
    'Db': 'Des',
    'Gb': 'Ges',
    'F#': 'Fis',
  };

  static final RegExp _tok = RegExp(r"^(\()?([#b])?([0-7.])([',]*)(/*)(\))?$");
  static final RegExp _ws = RegExp(r'\s+');

  static KeyInfo keyInfo(String? key, int shift) {
    final k = _keys[key] ?? _keys['C']!;
    final li = k[0];
    final tonic = 60 + _nat[li] + k[1] + 12 * shift;
    final alt = List<int>.filled(7, 0);
    for (var d = 0; d <= 6; d++) {
      final l = (li + d) % 7;
      final oc = (li + d) ~/ 7;
      alt[l] = tonic + _maj[d] - (60 + 12 * (oc + shift) + _nat[l]);
    }
    return KeyInfo(li, tonic, alt, shift);
  }

  static int midiOf(El e, KeyInfo ki) => ki.tonic + _maj[e.deg - 1] + 12 * e.oct + e.acc;

  static String _abcOf(El e, KeyInfo ki) {
    final d = e.deg - 1;
    final l = (ki.li + d) % 7;
    final carry = (ki.li + d) ~/ 7;
    final midi = midiOf(e, ki);
    final octave = 4 + carry + e.oct + ki.shift;
    final natural = 12 * (octave + 1) + _nat[l];
    final a = midi - natural;
    String sym;
    if (a == ki.alt[l]) {
      sym = '';
    } else {
      switch (a) {
        case 0:
          sym = '=';
          break;
        case 1:
          sym = '^';
          break;
        case -1:
          sym = '_';
          break;
        case 2:
          sym = '^^';
          break;
        default:
          sym = '__';
      }
    }
    var name = _letters[l];
    if (octave >= 5) {
      name = name.toLowerCase() + ("'" * (octave - 5));
    } else if (octave < 4) {
      name += ',' * (4 - octave);
    }
    return sym + name;
  }

  static int _count(String s, String ch) {
    var n = 0;
    for (var i = 0; i < s.length; i++) {
      if (s[i] == ch) n++;
    }
    return n;
  }

  static List<Line> parseNotes(String src) {
    final lines = <Line>[];
    var slurOpen = false;
    El? last;
    for (final lineSrc in src.split('\n')) {
      final line = Line();
      lines.add(line);
      var bar = Bar();
      line.items.add(bar);
      for (final tok in lineSrc.trim().split(_ws)) {
        if (tok.isEmpty) continue;
        if (tok == '|' || tok == ':|' || tok == '|]') {
          bar.end = tok;
          bar = Bar();
          line.items.add(bar);
          continue;
        }
        if (tok == 'v') {
          if (bar.beats.isNotEmpty) bar.beats.last.breath = true;
          if (last != null) last.breath = true;
          continue;
        }
        final parts = tok.split('+');
        final beat = Beat();
        final exp = tok.contains('/');
        beat.exp = exp;
        final unit = 1.0 / parts.length;
        for (final p in parts) {
          final m = _tok.firstMatch(p);
          if (m == null) throw FormatException('Tidak dikenali: $p');
          final g1 = m.group(1) ?? '';
          final g2 = m.group(2) ?? '';
          final g3 = m.group(3) ?? '';
          final g4 = m.group(4) ?? '';
          final g5 = m.group(5) ?? '';
          final g6 = m.group(6) ?? '';
          final sl = g5.length;
          final du = (exp && sl > 0) ? _pow05(sl) : unit;
          final el = El(g3[0], du, g1.isNotEmpty, g6.isNotEmpty);
          el.lv = exp ? sl : 0;
          if (g3 == '.') {
            el.hold = true;
            if (last != null) last.dur += unit;
            el.owner = last;
          } else {
            el.deg = int.parse(g3);
            el.rest = el.deg == 0;
            el.oct = _count(g4, "'") - _count(g4, ',');
            el.acc = g2 == '#' ? 1 : (g2 == 'b' ? -1 : 0);
            if (el.slurStart) slurOpen = true;
            el.inSlurCont = slurOpen && !el.slurStart && !el.rest;
            last = el;
          }
          if (el.slurEnd) {
            slurOpen = false;
            if (el.hold) el.owner?.slurEndHere = true;
          }
          beat.els.add(el);
        }
        bar.beats.add(beat);
      }
      line.items.removeWhere((it) => it.beats.isEmpty && it.end == null);
    }
    return lines;
  }

  // Math.pow(0.5, n) untuk n bulat positif (hasil eksak: pangkat dua)
  static double _pow05(int n) {
    var r = 1.0;
    for (var i = 0; i < n; i++) {
      r *= 0.5;
    }
    return r;
  }

  static List<El> noteEls(List<Line> lines) {
    final out = <El>[];
    for (final l in lines) {
      for (final b in l.items) {
        for (final bt in b.beats) {
          for (final e in bt.els) {
            if (!e.hold) out.add(e);
          }
        }
      }
    }
    return out;
  }

  static List<Syl> _syllables(String row) {
    final out = <Syl>[];
    for (final w in row.trim().split(_ws)) {
      if (w == '_') {
        out.add(const Syl('', false, true));
        continue;
      }
      final s = w.split('-');
      for (var i = 0; i < s.length; i++) {
        out.add(Syl(s[i], i < s.length - 1));
      }
    }
    return out;
  }

  static void _assignLyrics(List<Line> lines, List<String> rows) {
    final all = noteEls(lines);
    for (final e in all) {
      e.syl = List<Syl?>.filled(rows.length, null);
    }
    final targets = all.where((e) => !e.rest && !e.inSlurCont).toList();
    for (var ri = 0; ri < rows.length; ri++) {
      final syl = _syllables(rows[ri]);
      for (var i = 0; i < targets.length; i++) {
        targets[i].syl[ri] = i < syl.length ? syl[i] : null;
      }
    }
  }

  /// Bagian-bagian lagu dengan lirik ayat ke-[verse] terpasang pada not.
  static List<Sec> build(Hymn h, int verse) {
    var gi = 0;
    final out = <Sec>[];
    for (var si = 0; si < h.sections.length; si++) {
      final s = h.sections[si];
      List<Line> lines;
      try {
        lines = parseNotes(s.notes);
      } catch (_) {
        lines = <Line>[];
      }
      final rows = h.rowsFor(verse, si);
      _assignLyrics(lines, rows);
      for (final e in noteEls(lines)) {
        e.si = gi++;
      }
      out.add(Sec(lines, rows, s.notes, s.meter, s.key));
    }
    return out;
  }

  static double unitOf(String? meter) {
    int d = 4;
    if (meter != null) {
      final parts = meter.split('/');
      if (parts.length > 1) {
        d = int.tryParse(parts[1].trim(), radix: 10) ?? 4;
      }
    }
    return 4.0 / d;
  }

  static String _durStr(double beats) {
    final e = (beats * 4).round();
    return e == 1 ? '' : e.toString();
  }

  static String toAbc(Hymn h, List<Sec> secs) {
    var ki = keyInfo(h.key, h.oct);
    var curM = (secs.isNotEmpty ? secs.first.meter : null) ?? h.meter;
    var curK = h.key;
    final out = <String>['X:1', 'M:$curM', 'L:1/16', 'K:${h.key}'];
    for (final sec in secs) {
      final sm = sec.meter ?? h.meter;
      final u = unitOf(sm);
      var pre = '';
      if (sm != curM) {
        pre = '[M:$sm] ';
        curM = sm;
      }
      final sk = sec.key ?? h.key;
      if (sk != curK) {
        pre += '[K:$sk] ';
        curK = sk;
        ki = keyInfo(sk, h.oct);
      }
      final mus = <String>[];
      final lyr = sec.rows.map((_) => <String>[]).toList();
      for (final line in sec.lines) {
        for (final bar in line.items) {
          for (final beat in bar.beats) {
            final tri = beat.els.length == 3 && beat.els.every((it) => (it.dur * 3 - 1).abs() < 1e-6);
            final chunk = StringBuffer(tri ? '(3' : '');
            for (final e in beat.els) {
              if (e.hold) continue;
              if (e.breath) chunk.write('!breath!');
              if (e.slurStart) chunk.write('(');
              chunk.write(e.rest ? 'z' : _abcOf(e, ki));
              chunk.write(_durStr(e.dur * u * (tri ? 1.5 : 1.0)));
              if (e.slurEnd || e.slurEndHere) chunk.write(')');
              if (!e.rest) {
                for (var ri = 0; ri < lyr.length; ri++) {
                  final l = lyr[ri];
                  if (e.inSlurCont) {
                    l.add('_');
                    continue;
                  }
                  final Syl? sy = ri < e.syl.length ? e.syl[ri] : null;
                  if (sy == null) {
                    l.add('*');
                  } else if (sy.mel) {
                    l.add('_');
                  } else {
                    l.add(sy.t.replaceAll('-', '') + (sy.cont ? '-' : ''));
                  }
                }
              }
            }
            if (chunk.isNotEmpty) mus.add(chunk.toString());
          }
          final end = bar.end;
          if (end != null) mus.add(end);
        }
      }
      out.add(pre + mus.join(' '));
      for (final l in lyr) {
        out.add('w: ' + l.map((it) => it.endsWith('-') ? it : '$it ').join('').trimRight());
      }
    }
    return out.join('\n');
  }

  /// Urutan pemutaran: satu putaran per ayat, dimulai dari [fromVerse];
  /// bila [all] maka lanjut ke ayat berikut yang liriknya sudah terpasang.
  static List<Tone> sequence(Hymn h, int fromVerse, bool all) {
    final one = <_Item>[];
    var gi = 0;
    for (final s in h.sections) {
      List<Line> lines;
      try {
        lines = parseNotes(s.notes);
      } catch (_) {
        lines = <Line>[];
      }
      final notes = noteEls(lines);
      for (var i = 0; i < notes.length; i++) {
        notes[i].si = gi + i;
      }
      gi += notes.length;
      final reps = s.notes.contains(':|') ? 2 : 1;
      final uu = unitOf(s.meter ?? h.meter);
      final kk = keyInfo(s.key ?? h.key, h.oct);
      for (var r = 0; r < reps; r++) {
        for (final e in notes) {
          one.add(_Item(e, uu, kk));
        }
      }
    }
    List<int> verses;
    if (all) {
      verses = h.readyVerses.where((it) => it >= fromVerse).toList();
      if (verses.isEmpty) verses = [fromVerse];
    } else {
      verses = [fromVerse];
    }
    final list = verses.first != fromVerse ? <int>[fromVerse, ...verses] : verses;
    final seq = <Tone>[];
    for (final v in list) {
      for (final it in one) {
        final e = it.e;
        seq.add(Tone(e.rest ? -1 : midiOf(e, it.k), e.dur * it.u, e.si, e.breath, v));
      }
    }
    return seq;
  }
}
