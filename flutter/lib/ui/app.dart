import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:hkbp/data/models.dart';
import 'package:hkbp/data/prefs.dart';
import 'package:hkbp/ui/hymn_list.dart';
import 'package:hkbp/ui/saved.dart';
import 'package:hkbp/ui/settings.dart';
import 'package:hkbp/ui/theme.dart';

/// Akar aplikasi: tema mengikuti pengaturan (0 sistem, 1 terang, 2 gelap).
class BukuEndeApp extends StatelessWidget {
  const BukuEndeApp({super.key, required this.prefs});

  final Prefs prefs;

  static ThemeMode _modeOf(int theme) {
    switch (theme) {
      case 1:
        return ThemeMode.light;
      case 2:
        return ThemeMode.dark;
      default:
        return ThemeMode.system;
    }
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData light = buildTheme(Brightness.light);
    final ThemeData dark = buildTheme(Brightness.dark);
    return ListenableBuilder(
      listenable: prefs,
      builder: (BuildContext context, Widget? child) {
        return MaterialApp(
          title: 'Buku Ende HKBP',
          debugShowCheckedModeBanner: false,
          theme: light,
          darkTheme: dark,
          themeMode: _modeOf(prefs.theme),
          // Setara SideEffect di Theme.kt: ikon bilah status & navigasi mengikuti tema.
          builder: (BuildContext context, Widget? app) {
            final bool dark = Theme.of(context).brightness == Brightness.dark;
            final Brightness icons = dark ? Brightness.light : Brightness.dark;
            return AnnotatedRegion<SystemUiOverlayStyle>(
              value: SystemUiOverlayStyle(
                statusBarColor: Colors.transparent,
                statusBarIconBrightness: icons,
                statusBarBrightness: dark ? Brightness.dark : Brightness.light,
                systemNavigationBarColor: Colors.transparent,
                systemNavigationBarDividerColor: Colors.transparent,
                systemNavigationBarIconBrightness: icons,
                systemNavigationBarContrastEnforced: false,
              ),
              child: app ?? const SizedBox.shrink(),
            );
          },
          home: child,
        );
      },
      // Dibuat sekali agar Shell (dan Library.load) tidak dibuat ulang saat prefs berubah.
      child: Shell(prefs: prefs),
    );
  }
}

class _Dest {
  const _Dest(this.label, this.on, this.off);

  final String label;
  final IconData on;
  final IconData off;
}

const List<_Dest> _dests = <_Dest>[
  _Dest('Buku Ende', Icons.menu_book, Icons.menu_book_outlined),
  _Dest('Buku Nyanyian', Icons.library_music, Icons.library_music_outlined),
  _Dest('Tersimpan', Icons.bookmarks, Icons.bookmarks_outlined),
  _Dest('Pengaturan', Icons.settings, Icons.settings_outlined),
];

/// Kerangka utama: memuat pustaka lagu, lalu navigasi bawah 4 tab.
class Shell extends StatefulWidget {
  const Shell({super.key, required this.prefs});

  final Prefs prefs;

  @override
  State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  late final Future<Map<Book, List<Hymn>>> _lib;
  int _tab = 0;

  /// Tab yang dibuka sebelumnya (terakhir di ujung); back kembali ke tab-tab ini.
  final List<int> _history = <int>[];
  final List<BackHook> _hooks = List<BackHook>.generate(4, (_) => BackHook());
  DateTime? _lastBack;

  void _select(int i) {
    if (i == _tab) return;
    setState(() {
      _history.remove(i);
      _history.remove(_tab);
      _history.add(_tab);
      _tab = i;
    });
  }

  /// Urutan: tutup pencarian di tab aktif -> tab sebelumnya -> tekan dua kali untuk keluar.
  void _onBack() {
    if (_hooks[_tab].handle?.call() ?? false) return;
    if (_history.isNotEmpty) {
      setState(() => _tab = _history.removeLast());
      return;
    }
    if (_tab != 0) {
      setState(() => _tab = 0);
      return;
    }
    final DateTime now = DateTime.now();
    final DateTime? last = _lastBack;
    if (last != null && now.difference(last) < const Duration(seconds: 2)) {
      SystemNavigator.pop();
      return;
    }
    _lastBack = now;
    final ScaffoldMessengerState m = ScaffoldMessenger.of(context);
    m.hideCurrentSnackBar();
    m.showSnackBar(const SnackBar(
      content: Text('Tekan kembali sekali lagi untuk keluar'),
      duration: Duration(seconds: 2),
    ));
  }

  @override
  void initState() {
    super.initState();
    _lib = Library.load();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<Book, List<Hymn>>>(
      future: _lib,
      builder: (BuildContext context, AsyncSnapshot<Map<Book, List<Hymn>>> snap) {
        if (snap.hasError) {
          return Scaffold(
            body: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  'Gagal memuat data lagu.\n${snap.error}',
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          );
        }
        final Map<Book, List<Hymn>>? lib = snap.data;
        if (snap.connectionState != ConnectionState.done || lib == null) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        return _main(lib);
      },
    );
  }

  Widget _main(Map<Book, List<Hymn>> lib) {
    final Prefs prefs = widget.prefs;
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (bool didPop, Object? _) {
        if (!didPop) _onBack();
      },
      child: Scaffold(
      body: IndexedStack(
        index: _tab,
        children: <Widget>[
          HymnListScreen(
            book: Book.be,
            hymns: lib[Book.be] ?? const <Hymn>[],
            prefs: prefs,
            back: _hooks[0],
          ),
          HymnListScreen(
            book: Book.bn,
            hymns: lib[Book.bn] ?? const <Hymn>[],
            prefs: prefs,
            back: _hooks[1],
          ),
          SavedScreen(lib: lib, prefs: prefs),
          SettingsScreen(lib: lib, prefs: prefs),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        onDestinationSelected: _select,
        destinations: <Widget>[
          for (final _Dest d in _dests)
            NavigationDestination(
              icon: Icon(d.off),
              selectedIcon: Icon(d.on),
              label: d.label,
            ),
        ],
      ),
      ),
    );
  }
}
