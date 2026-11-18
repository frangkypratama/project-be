import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

/// Not balok (abcjs) di dalam WebView (port StaffView/StaffState di Score.kt).
///
/// Halaman `assets/web/score.html` menyediakan `render(abc, ink, hl)` dan `mark(i)`,
/// lalu melaporkan tinggi isinya (px CSS) lewat kanal JavaScript `Tinggi`.
/// WebView tidak menerima sentuhan: gulir dan geser ditangani aplikasi.
class StaffView extends StatefulWidget {
  final String abc;
  final int curSi;

  const StaffView({super.key, required this.abc, required this.curSi});

  @override
  State<StaffView> createState() => _StaffViewState();
}

class _StaffViewState extends State<StaffView> {
  late final WebViewController _c;

  bool _ready = false;
  String _ink = '#000000';
  String _hl = '#000000';
  String _shown = '';
  int _marked = -2;
  double? _height;

  @override
  void initState() {
    super.initState();
    _c = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(Colors.transparent)
      ..addJavaScriptChannel(
        'Tinggi',
        onMessageReceived: (JavaScriptMessage m) {
          final double? h = double.tryParse(m.message.trim());
          if (h == null || h <= 0 || !mounted) return;
          if (h == _height) return;
          setState(() => _height = h);
        },
      )
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageFinished: (String _) {
            if (!mounted) return;
            _ready = true;
            // Halaman (baru) dimuat: gambar ulang dan tandai ulang.
            _shown = '';
            _marked = -2;
            _push();
            _mark();
          },
          onNavigationRequest: (NavigationRequest r) {
            final String url = r.url.toLowerCase();
            if (url.startsWith('http://') || url.startsWith('https://')) {
              return NavigationDecision.prevent;
            }
            return NavigationDecision.navigate;
          },
        ),
      )
      ..loadFlutterAsset('assets/web/score.html');
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final ColorScheme cs = Theme.of(context).colorScheme;
    _ink = _hex(cs.onSurface);
    _hl = _hex(cs.primary);
    _push();
    _mark();
  }

  @override
  void didUpdateWidget(covariant StaffView oldWidget) {
    super.didUpdateWidget(oldWidget);
    _push();
    _mark();
  }

  static String _hex(Color c) {
    final int rgb = c.toARGB32() & 0xFFFFFF;
    return '#${rgb.toRadixString(16).padLeft(6, '0').toUpperCase()}';
  }

  Future<void> _js(String code) async {
    try {
      await _c.runJavaScript(code);
    } catch (_) {
      // Halaman belum siap / WebView sudah dibuang: abaikan.
    }
  }

  void _push() {
    if (!_ready) return;
    final String k = '${widget.abc}|$_ink|$_hl';
    if (k == _shown) return;
    _shown = k;
    _marked = -2;
    _js('render(${jsonEncode(widget.abc)},${jsonEncode(_ink)},${jsonEncode(_hl)})');
  }

  void _mark() {
    if (!_ready) return;
    final int si = widget.curSi;
    if (si == _marked) return;
    _marked = si;
    _js('mark($si)');
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: _height ?? 180,
      child: IgnorePointer(
        child: WebViewWidget(controller: _c),
      ),
    );
  }
}
