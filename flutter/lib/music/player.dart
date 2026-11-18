import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:just_audio/just_audio.dart';
import 'package:path_provider/path_provider.dart';

import 'notation.dart';
import 'organ.dart';

/// Pemutar organ: menyintesis urutan nada menjadi WAV (renderOrgan), menulisnya
/// ke berkas sementara, lalu memutarnya dengan just_audio. Posisi pemutaran
/// dipetakan ke indeks suku kata (curSi) dan ayat (curVerse) untuk penyorotan.
class OrganPlayer extends ChangeNotifier {
  OrganPlayer() {
    _posSub = _player.positionStream.listen(_onPosition, onError: (Object _) {});
    _stateSub = _player.playerStateStream.listen(_onState, onError: (Object _) {
      _finish();
    });
  }

  final AudioPlayer _player = AudioPlayer();
  StreamSubscription<Duration>? _posSub;
  StreamSubscription<PlayerState>? _stateSub;

  bool _playing = false;
  bool _preparing = false;
  int _curSi = -1;
  int _curVerse = -1;
  bool _disposed = false;

  /// Bertambah setiap play()/stop(); dipakai untuk membatalkan hasil sintesis usang.
  int _gen = 0;
  OrganRender? _render;
  File? _file;

  bool get playing => _playing;
  bool get preparing => _preparing;
  int get curSi => _curSi;
  int get curVerse => _curVerse;

  void _notify() {
    if (!_disposed) notifyListeners();
  }

  Future<void> play(List<Tone> seq, {required int bpm, required int transpose}) async {
    if (_disposed) return;
    await stop();
    // Sama dengan OrganPlayer.kt: urutan kosong tidak diputar.
    if (_disposed || seq.isEmpty) return;
    final int g = ++_gen;
    _preparing = true;
    _notify();
    try {
      final OrganRender r = await renderOrgan(seq, bpm: bpm, transpose: transpose);
      if (g != _gen || _disposed) return;

      final Directory dir = await getTemporaryDirectory();
      final File f = File('${dir.path}/organ_$g.wav');
      await f.writeAsBytes(r.wav, flush: true);
      if (g != _gen || _disposed) {
        _deleteQuietly(f);
        return;
      }
      final File? old = _file;
      _file = f;
      if (old != null && old.path != f.path) _deleteQuietly(old);

      await _player.setFilePath(f.path);
      if (g != _gen || _disposed) return;

      _render = r;
      _curSi = -1;
      _curVerse = -1;
      _playing = true;
      _preparing = false;
      _notify();
      // play() baru selesai saat pemutaran berhenti; jangan ditunggu.
      unawaited(_player.play().catchError((Object _) {
        if (g == _gen) _finish();
      }));
    } catch (_) {
      if (g == _gen) _finish();
    }
  }

  Future<void> stop() async {
    _gen++;
    final bool changed =
        _playing || _preparing || _curSi != -1 || _curVerse != -1;
    _playing = false;
    _preparing = false;
    _curSi = -1;
    _curVerse = -1;
    _render = null;
    if (changed) _notify();
    if (_disposed) return;
    try {
      await _player.stop();
    } catch (_) {}
  }

  void _finish() {
    final bool changed =
        _playing || _preparing || _curSi != -1 || _curVerse != -1;
    _playing = false;
    _preparing = false;
    _curSi = -1;
    _curVerse = -1;
    _render = null;
    if (changed) _notify();
  }

  void _onPosition(Duration pos) {
    final OrganRender? r = _render;
    if (!_playing || r == null) return;
    final List<double> starts = r.starts;
    if (starts.isEmpty) return;
    final double t = pos.inMicroseconds / 1000000.0;
    // Indeks terakhir dengan starts[i] <= t.
    int lo = 0, hi = starts.length - 1, idx = -1;
    while (lo <= hi) {
      final int mid = (lo + hi) >> 1;
      if (starts[mid] <= t) {
        idx = mid;
        lo = mid + 1;
      } else {
        hi = mid - 1;
      }
    }
    int si = -1, verse = -1;
    if (idx >= 0) {
      if (idx < r.si.length) si = r.si[idx];
      if (idx < r.verse.length) verse = r.verse[idx];
    }
    if (si != _curSi || verse != _curVerse) {
      _curSi = si;
      _curVerse = verse;
      _notify();
    }
  }

  void _onState(PlayerState s) {
    if (s.processingState == ProcessingState.completed && _playing) {
      _finish();
    }
  }

  void _deleteQuietly(File f) {
    f.delete().then((_) {}, onError: (Object _) {});
  }

  @override
  void dispose() {
    _disposed = true;
    _gen++;
    _playing = false;
    _preparing = false;
    _render = null;
    _posSub?.cancel();
    _stateSub?.cancel();
    _posSub = null;
    _stateSub = null;
    _player.dispose();
    final File? f = _file;
    _file = null;
    if (f != null) _deleteQuietly(f);
    super.dispose();
  }
}
