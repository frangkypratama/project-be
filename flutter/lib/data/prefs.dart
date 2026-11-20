import 'dart:collection';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Pengaturan dan daftar pribadi, disimpan di perangkat (SharedPreferences).
/// Port dari Prefs.kt; setiap perubahan disimpan lalu memanggil notifyListeners().
class Prefs extends ChangeNotifier {
  Prefs._(this._sp)
      : _theme = _clampInt(_sp.getInt(_kTheme) ?? 0, 0, 2),
        _textScale = _clampScale(_sp.getDouble(_kTextScale) ?? 1.0),
        _defaultView = _clampInt(_sp.getInt(_kView) ?? 1, 0, 3),
        _keepScreenOn = _sp.getBool(_kScreenOn) ?? true,
        _playAllVerses = _sp.getBool(_kAllVerses) ?? true,
        _chordsOn = _sp.getBool(_kChords) ?? true,
        _favorites = _readList(_sp, _kFav),
        _history = _readList(_sp, _kHist) {
    if (_history.length > maxHistory) {
      _history.removeRange(maxHistory, _history.length);
    }
  }

  static const String _kTheme = 'theme';
  static const String _kTextScale = 'textScale';
  static const String _kView = 'view';
  static const String _kScreenOn = 'screenOn';
  static const String _kAllVerses = 'allVerses';
  static const String _kChords = 'chords';
  static const String _kFav = 'fav';
  static const String _kHist = 'hist';

  static const int maxHistory = 40;
  static const double minTextScale = 0.8;
  static const double maxTextScale = 1.8;

  final SharedPreferences _sp;

  int _theme;
  double _textScale;
  int _defaultView;
  bool _keepScreenOn;
  bool _playAllVerses;
  bool _chordsOn;

  /// Akor iringan: tampil di not angka/balok dan berbunyi saat diputar. Bawaan: mati.
  bool get chordsOn => _chordsOn;

  void setChordsOn(bool v) {
    _chordsOn = v;
    _sp.setBool(_kChords, v);
    notifyListeners();
  }
  final List<String> _favorites;
  final List<String> _history;

  static Future<Prefs> load() async {
    final sp = await SharedPreferences.getInstance();
    return Prefs._(sp);
  }

  /// 0 = ikuti sistem, 1 = terang, 2 = gelap
  int get theme => _theme;
  set theme(int v) => setTheme(v);

  /// 0.8..1.8, default 1.0
  double get textScale => _textScale;
  set textScale(double v) => setTextScale(v);

  /// 0 = Lirik, 1 = Angka, 2 = Balok, 3 = Keduanya
  int get defaultView => _defaultView;
  set defaultView(int v) => setDefaultView(v);

  bool get keepScreenOn => _keepScreenOn;
  set keepScreenOn(bool v) => setKeepScreenOn(v);

  bool get playAllVerses => _playAllVerses;
  set playAllVerses(bool v) => setPlayAllVerses(v);

  /// key2 ("be:784"), terbaru di depan.
  List<String> get favorites => UnmodifiableListView<String>(_favorites);

  /// key2, terbaru di depan, maksimal 40.
  List<String> get history => UnmodifiableListView<String>(_history);

  void setTheme(int v) {
    _theme = _clampInt(v, 0, 2);
    _sp.setInt(_kTheme, _theme);
    notifyListeners();
  }

  void setTextScale(double v) {
    _textScale = _clampScale(v);
    _sp.setDouble(_kTextScale, _textScale);
    notifyListeners();
  }

  void setDefaultView(int v) {
    _defaultView = _clampInt(v, 0, 3);
    _sp.setInt(_kView, _defaultView);
    notifyListeners();
  }

  void setKeepScreenOn(bool v) {
    _keepScreenOn = v;
    _sp.setBool(_kScreenOn, v);
    notifyListeners();
  }

  void setPlayAllVerses(bool v) {
    _playAllVerses = v;
    _sp.setBool(_kAllVerses, v);
    notifyListeners();
  }

  bool isFavorite(String key2) => _favorites.contains(key2);

  void toggleFavorite(String key2) {
    if (!_favorites.remove(key2)) _favorites.insert(0, key2);
    _sp.setStringList(_kFav, List<String>.of(_favorites));
    notifyListeners();
  }

  void visit(String key2) {
    _history.remove(key2);
    _history.insert(0, key2);
    if (_history.length > maxHistory) {
      _history.removeRange(maxHistory, _history.length);
    }
    _sp.setStringList(_kHist, List<String>.of(_history));
    notifyListeners();
  }

  void clearHistory() {
    _history.clear();
    _sp.remove(_kHist);
    notifyListeners();
  }

  static int _clampInt(int v, int lo, int hi) => v < lo ? lo : (v > hi ? hi : v);

  static double _clampScale(double v) {
    if (v.isNaN) return 1.0;
    return v < minTextScale ? minTextScale : (v > maxTextScale ? maxTextScale : v);
  }

  /// Baca daftar string; toleran terhadap format lama "a|b|c" (String).
  static List<String> _readList(SharedPreferences sp, String key) {
    final Object? raw = sp.get(key);
    final List<String> out = <String>[];
    if (raw is List) {
      for (final Object? e in raw) {
        if (e is String && e.isNotEmpty && !out.contains(e)) out.add(e);
      }
    } else if (raw is String) {
      for (final String e in raw.split('|')) {
        if (e.isNotEmpty && !out.contains(e)) out.add(e);
      }
    }
    return out;
  }
}
