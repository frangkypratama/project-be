import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'package:hkbp/music/notation.dart';

/* ---------------- Not angka, digambar native (port Score.kt) ---------------- */

/// Garis atas per ketukan, sama dengan situs: 2+ not = 1 garis;
/// lebih dari 2 (BE) / 3 (BN) not = 2 garis.
int lineCount(Beat beat, bool bn) {
  final int n = beat.els.length;
  if (n <= 1) return 0;
  if (n > (bn ? 3 : 2)) return 2;
  return 1;
}

class AngkaView extends StatelessWidget {
  final List<Sec> secs;
  final int curSi;
  final double scale;
  final bool bn;

  /// null = akor tidak ditampilkan; selain itu Do (0..11) untuk menamai akor bagian tsb.
  final int Function(Sec)? chordTonic;

  const AngkaView({
    super.key,
    required this.secs,
    required this.curSi,
    required this.scale,
    required this.bn,
    this.chordTonic,
  });

  @override
  Widget build(BuildContext context) {
    final ColorScheme cs = Theme.of(context).colorScheme;
    final Color ink = cs.onSurface;
    final Color hl = cs.tertiaryContainer;
    final double digit = 21 * scale;
    final double syl = 13.5 * scale;
    // Setara digit.toDp() di Compose (sp ikut skala huruf sistem).
    final double digitPx = MediaQuery.textScalerOf(context).scale(digit);
    final double barH = digitPx * 1.25 + 22;
    final _Style st = _Style(
      ink: ink,
      hl: hl,
      digit: digit,
      syl: syl,
      barH: barH,
      bn: bn,
      curSi: curSi,
    );

    final List<Widget> children = <Widget>[];
    for (int i = 0; i < secs.length; i++) {
      final Sec sec = secs[i];
      if (i > 0) children.add(const SizedBox(height: 18));
      final List<Widget> bars = <Widget>[];
      for (final Line line in sec.lines) {
        for (final Bar bar in line.items) {
          bars.add(_BarView(
            bar: bar,
            rows: sec.rows.length,
            st: st,
            tonic: chordTonic?.call(sec),
            scale: scale,
            chColor: cs.primary,
          ));
        }
      }
      children.add(Wrap(runSpacing: 16, children: bars));
    }
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }
}

class _Style {
  final Color ink;
  final Color hl;
  final double digit;
  final double syl;
  final double barH;
  final bool bn;
  final int curSi;

  const _Style({
    required this.ink,
    required this.hl,
    required this.digit,
    required this.syl,
    required this.barH,
    required this.bn,
    required this.curSi,
  });
}

/// Garis atas (1.3 px) di y = 2, 6, ... dengan jarak tepi 3 px.
class _Overlines extends CustomPainter {
  final int n;
  final Color ink;

  const _Overlines(this.n, this.ink);

  @override
  void paint(Canvas canvas, Size size) {
    if (n <= 0) return;
    final Paint p = Paint()
      ..color = ink
      ..strokeWidth = 1.3
      ..style = PaintingStyle.stroke;
    for (int k = 0; k < n; k++) {
      final double y = 2.0 + 4.0 * k;
      canvas.drawLine(Offset(3, y), Offset(size.width - 3, y), p);
    }
  }

  @override
  bool shouldRepaint(_Overlines old) => old.n != n || old.ink != ink;
}

/// Garis miring kres (kiri-bawah ke kanan-atas) / mol (kiri-atas ke kanan-bawah).
class _AccLine extends CustomPainter {
  final int acc;
  final Color ink;

  const _AccLine(this.acc, this.ink);

  @override
  void paint(Canvas canvas, Size size) {
    if (acc == 0) return;
    final double w = size.width;
    final double h = size.height;
    final Offset a = acc > 0 ? Offset(w * .15, h * .85) : Offset(w * .15, h * .15);
    final Offset b = acc > 0 ? Offset(w * .85, h * .15) : Offset(w * .85, h * .85);
    final Paint p = Paint()
      ..color = ink
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;
    canvas.drawLine(a, b, p);
  }

  @override
  bool shouldRepaint(_AccLine old) => old.acc != acc || old.ink != ink;
}

Widget _withOverlines(int n, Color ink, Widget child) {
  final Widget padded = Padding(padding: const EdgeInsets.only(top: 12), child: child);
  if (n <= 0) return padded;
  return CustomPaint(painter: _Overlines(n, ink), child: padded);
}

class _BarView extends StatelessWidget {
  final Bar bar;
  final int rows;
  final _Style st;
  final int? tonic;
  final double scale;
  final Color chColor;

  const _BarView({
    required this.bar,
    required this.rows,
    required this.st,
    this.tonic,
    this.scale = 1.0,
    this.chColor = Colors.blue,
  });

  @override
  Widget build(BuildContext context) {
    final List<Widget> items = <Widget>[];
    final int? tn = tonic;
    final double chH = tn != null ? 18 * scale : 0;
    for (final Beat beat in bar.beats) {
      final int start = items.length;
      if (beat.exp) {
        // durasi eksplisit (BN): garis atas per not
        items.add(Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            for (final El e in beat.els)
              _withOverlines(
                math.min(e.lv, 2),
                st.ink,
                _ElView(e: e, rows: rows, lit: !e.hold && e.si == st.curSi, st: st),
              ),
          ],
        ));
      } else {
        items.add(_withOverlines(
          lineCount(beat, st.bn),
          st.ink,
          Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              for (final El e in beat.els)
                _ElView(e: e, rows: rows, lit: !e.hold && e.si == st.curSi, st: st),
            ],
          ),
        ));
      }
      if (tn != null) {
        // nama akor di atas ketukan; lebar 0 agar tidak melebarkan not
        final Chord? c = beat.chord;
        final Widget w = items.removeAt(start);
        items.insert(
          start,
          Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              SizedBox(
                height: chH,
                width: 0,
                child: c == null
                    ? null
                    : OverflowBox(
                        alignment: Alignment.topLeft,
                        maxWidth: double.infinity,
                        child: Padding(
                          padding: const EdgeInsets.only(left: 3),
                          child: Text(
                            Notation.chordName(c, tn),
                            maxLines: 1,
                            softWrap: false,
                            style: TextStyle(
                              color: chColor,
                              fontWeight: FontWeight.w700,
                              fontSize: 13.5 * scale,
                              height: 1.0,
                            ),
                          ),
                        ),
                      ),
              ),
              w,
            ],
          ),
        );
      }
      if (beat.breath) {
        items.add(Padding(
          padding: EdgeInsets.only(top: 10 + chH),
          child: Text(
            '’',
            style: TextStyle(
              fontSize: st.digit,
              height: math.max(1.0, 24 / st.digit),
              color: st.ink,
            ),
          ),
        ));
      }
    }
    final String? end = bar.end;
    if (end != null) {
      final double h = st.barH - 12;
      items.add(Padding(
        padding: EdgeInsets.only(left: 4, right: 6, top: 12 + chH),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: <Widget>[
            if (end == ':|')
              Text(
                ':',
                style: TextStyle(
                  fontSize: st.digit,
                  fontWeight: FontWeight.w700,
                  color: st.ink,
                ),
              ),
            Container(width: 1.2, height: h, color: st.ink),
            if (end != '|') ...<Widget>[
              const SizedBox(width: 2),
              Container(width: 3.5, height: h, color: st.ink),
            ],
          ],
        ),
      ));
    }
    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: items,
    );
  }
}

class _ElView extends StatelessWidget {
  final El e;
  final int rows;
  final bool lit;
  final _Style st;

  const _ElView({required this.e, required this.rows, required this.lit, required this.st});

  @override
  Widget build(BuildContext context) {
    final Color ink = st.ink;
    final TextStyle dotStyle = TextStyle(fontSize: 8, height: 1.0, color: ink);
    final double sylHeight = math.max(1.0, 24 / st.syl);
    final List<Widget> children = <Widget>[
      Text(e.oct > 0 ? '•' * e.oct : ' ', style: dotStyle),
      CustomPaint(
        foregroundPainter: (!e.hold && e.acc != 0) ? _AccLine(e.acc, ink) : null,
        child: Text(
          digitText(e),
          style: TextStyle(
            fontSize: st.digit,
            height: 1.0,
            fontWeight: e.hold ? FontWeight.w700 : FontWeight.w500,
            color: ink,
          ),
        ),
      ),
      Text(e.oct < 0 ? '•' * (-e.oct) : ' ', style: dotStyle),
    ];
    for (int r = 0; r < rows; r++) {
      final Syl? s = r < e.syl.length ? e.syl[r] : null;
      children.add(Text(
        s == null ? ' ' : s.t + (s.cont ? ' -' : ''),
        maxLines: 1,
        softWrap: false,
        style: TextStyle(
          fontSize: st.syl,
          height: sylHeight,
          color: r == 0 ? ink : ink.withValues(alpha: .75),
        ),
      ));
    }
    return Container(
      constraints: const BoxConstraints(minWidth: 18),
      padding: const EdgeInsets.symmetric(horizontal: 3),
      decoration: lit
          ? BoxDecoration(color: st.hl, borderRadius: BorderRadius.circular(6))
          : null,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: children,
      ),
    );
  }
}
