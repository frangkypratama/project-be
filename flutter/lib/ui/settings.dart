import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:hkbp/data/models.dart';
import 'package:hkbp/data/prefs.dart';
import 'package:hkbp/ui/detail.dart';

/// Layar Pengaturan — port Settings.kt.
class SettingsScreen extends StatelessWidget {
  final Map<Book, List<Hymn>> lib;
  final Prefs prefs;

  const SettingsScreen({super.key, required this.lib, required this.prefs});

  Future<void> _openSite() async {
    try {
      await launchUrl(
        Uri.parse('https://bukuende.com/'),
        mode: LaunchMode.externalApplication,
      );
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Pengaturan')),
      body: ListenableBuilder(
        listenable: prefs,
        builder: (BuildContext context, Widget? _) {
          final bool dark = Theme.of(context).brightness == Brightness.dark;
          final int pct = (prefs.textScale * 100).round();
          final int beCount = lib[Book.be]?.length ?? 0;
          final int bnCount = lib[Book.bn]?.length ?? 0;
          return ListView(
            children: <Widget>[
              const _Header('Tampilan'),
              ListTile(
                leading: Icon(dark ? Icons.dark_mode : Icons.light_mode),
                title: const Text('Tema'),
                subtitle: Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: _Segments(
                    options: const <String>['Sistem', 'Terang', 'Gelap'],
                    selected: prefs.theme,
                    onSelect: prefs.setTheme,
                  ),
                ),
              ),
              ListTile(
                leading: const Icon(Icons.format_size),
                title: Text('Ukuran huruf lagu: $pct%'),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Slider(
                      value: prefs.textScale.clamp(0.8, 1.8).toDouble(),
                      min: 0.8,
                      max: 1.8,
                      divisions: 20,
                      label: '$pct%',
                      onChanged: (double v) =>
                          prefs.setTextScale((v * 20).round() / 20.0),
                    ),
                    Text(
                      'Ringgas ma ho, tondingku',
                      style: TextStyle(fontSize: 17 * prefs.textScale),
                    ),
                  ],
                ),
              ),
              ListTile(
                leading: const Icon(Icons.visibility),
                title: const Text('Tampilan awal lagu'),
                subtitle: Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: _Segments(
                    options: kViews,
                    selected: prefs.defaultView,
                    onSelect: prefs.setDefaultView,
                  ),
                ),
              ),
              const _Header('Pemutaran'),
              SwitchListTile(
                secondary: const Icon(Icons.playlist_play),
                title: const Text('Putar semua ayat'),
                subtitle: const Text(
                    'Setelah satu ayat selesai, lanjut ke ayat berikutnya'),
                value: prefs.playAllVerses,
                onChanged: prefs.setPlayAllVerses,
              ),
              SwitchListTile(
                secondary: const Icon(Icons.light_mode),
                title: const Text('Layar tetap menyala'),
                subtitle: const Text(
                    'Selama halaman lagu terbuka, misalnya saat ibadah'),
                value: prefs.keepScreenOn,
                onChanged: prefs.setKeepScreenOn,
              ),
              const _Header('Data'),
              ListTile(
                leading: const Icon(Icons.history),
                title: const Text('Hapus riwayat'),
                subtitle: Text(
                    '${prefs.history.length} lagu di daftar Terakhir dibuka'),
                onTap: prefs.clearHistory,
              ),
              const _Header('Tentang'),
              ListTile(
                leading: const Icon(Icons.info),
                title: const Text('Buku Ende HKBP Digital (Flutter)'),
                subtitle: Text(
                  '$beCount lagu Buku Ende dan $bnCount lagu Buku Nyanyian, '
                  'lengkap dengan lirik semua ayat, not angka, not balok, dan nada. '
                  'Semua tersimpan di dalam aplikasi, jadi bisa dibuka tanpa internet.',
                ),
              ),
              const ListTile(
                leading: Icon(Icons.shield),
                title: Text('Privasi'),
                subtitle: Text(
                  'Aplikasi ini tidak memiliki izin internet, tidak menampilkan iklan, '
                  'dan tidak mengumpulkan data. Favorit, riwayat, dan pengaturan '
                  'hanya disimpan di perangkat Anda.',
                ),
              ),
              ListTile(
                leading: const Icon(Icons.open_in_new),
                title: const Text('bukuende.com'),
                subtitle: const Text('Versi situs, bisa dibuka di peramban'),
                onTap: _openSite,
              ),
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 8),
                child: Divider(height: 1),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _Header extends StatelessWidget {
  final String text;

  const _Header(this.text);

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 4),
      child: Text(
        text,
        style: theme.textTheme.labelLarge
            ?.copyWith(color: theme.colorScheme.primary),
      ),
    );
  }
}

class _Segments extends StatelessWidget {
  final List<String> options;
  final int selected;
  final ValueChanged<int> onSelect;

  const _Segments({
    required this.options,
    required this.selected,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    return SegmentedButton<int>(
      showSelectedIcon: false,
      expandedInsets: EdgeInsets.zero,
      segments: <ButtonSegment<int>>[
        for (int i = 0; i < options.length; i++)
          ButtonSegment<int>(
            value: i,
            label: Text(
              options[i],
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              softWrap: false,
            ),
          ),
      ],
      selected: <int>{selected},
      onSelectionChanged: (Set<int> s) {
        if (s.isNotEmpty) onSelect(s.first);
      },
    );
  }
}
