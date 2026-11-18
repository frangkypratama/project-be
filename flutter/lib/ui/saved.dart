import 'package:flutter/material.dart';

import 'package:hkbp/data/models.dart';
import 'package:hkbp/data/prefs.dart';
import 'package:hkbp/ui/detail.dart';
import 'package:hkbp/ui/hymn_list.dart';

/// Layar "Tersimpan": tab Favorit dan Terakhir dibuka (port SavedScreen di Lists.kt).
class SavedScreen extends StatefulWidget {
  final Map<Book, List<Hymn>> lib;
  final Prefs prefs;

  const SavedScreen({super.key, required this.lib, required this.prefs});

  @override
  State<SavedScreen> createState() => _SavedScreenState();
}

class _SavedScreenState extends State<SavedScreen> with SingleTickerProviderStateMixin {
  late final TabController _tab;
  Map<String, (Book, int)> _byKey = <String, (Book, int)>{};

  @override
  void initState() {
    super.initState();
    _tab = TabController(length: 2, vsync: this);
    _buildIndex();
  }

  @override
  void didUpdateWidget(SavedScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!identical(oldWidget.lib, widget.lib)) _buildIndex();
  }

  @override
  void dispose() {
    _tab.dispose();
    super.dispose();
  }

  void _buildIndex() {
    final Map<String, (Book, int)> m = <String, (Book, int)>{};
    widget.lib.forEach((Book book, List<Hymn> hymns) {
      for (int i = 0; i < hymns.length; i++) {
        m[hymns[i].key2] = (book, i);
      }
    });
    _byKey = m;
  }

  List<(Book, int, Hymn)> _rows(List<String> keys) {
    final List<(Book, int, Hymn)> out = <(Book, int, Hymn)>[];
    for (final String k in keys) {
      final (Book, int)? o = _byKey[k];
      if (o == null) continue;
      final List<Hymn>? hymns = widget.lib[o.$1];
      if (hymns == null || o.$2 < 0 || o.$2 >= hymns.length) continue;
      out.add((o.$1, o.$2, hymns[o.$2]));
    }
    return out;
  }

  Future<void> _confirmClear() async {
    final bool? ok = await showDialog<bool>(
      context: context,
      builder: (BuildContext ctx) => AlertDialog(
        title: const Text('Hapus riwayat?'),
        content: const Text('Daftar lagu yang terakhir dibuka akan dikosongkan. Favorit tidak terhapus.'),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Batal'),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Hapus'),
          ),
        ],
      ),
    );
    if (ok == true) widget.prefs.clearHistory();
  }

  Widget _empty(BuildContext context, bool history) {
    final ColorScheme cs = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(
              history ? Icons.history : Icons.star_outline,
              size: 56,
              color: cs.outline,
            ),
            const SizedBox(height: 12),
            Text(
              history
                  ? 'Belum ada lagu yang dibuka.'
                  : 'Belum ada favorit.\nTekan ikon bintang di halaman lagu untuk menyimpannya di sini.',
              textAlign: TextAlign.center,
              style: TextStyle(color: cs.onSurfaceVariant),
            ),
          ],
        ),
      ),
    );
  }

  Widget _list(BuildContext context, bool history) {
    final Prefs prefs = widget.prefs;
    final List<(Book, int, Hymn)> rows = _rows(history ? prefs.history : prefs.favorites);
    if (rows.isEmpty) return _empty(context, history);
    final Color divider = Theme.of(context).colorScheme.outlineVariant.withValues(alpha: 0.4);
    return ListView.builder(
      key: PageStorageKey<String>(history ? 'saved-history' : 'saved-favorites'),
      padding: const EdgeInsets.only(bottom: 24),
      itemCount: rows.length,
      itemBuilder: (BuildContext ctx, int i) {
        final (Book book, int index, Hymn h) = rows[i];
        return Column(
          key: ValueKey<String>(h.key2),
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            HymnTile(
              hymn: h,
              fav: history && prefs.isFavorite(h.key2),
              showBook: true,
              onTap: () => openHymn(context, widget.lib[book]!, index, widget.prefs),
            ),
            Divider(height: 1, thickness: 1, indent: 80, color: divider),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: Listenable.merge(<Listenable>[widget.prefs, _tab]),
      builder: (BuildContext context, Widget? _) {
        final bool onHistory = _tab.index == 1;
        final bool canClear = onHistory && _rows(widget.prefs.history).isNotEmpty;
        return Scaffold(
          appBar: AppBar(
            title: const Text('Tersimpan'),
            actions: <Widget>[
              if (canClear)
                IconButton(
                  icon: const Icon(Icons.delete_sweep),
                  tooltip: 'Hapus riwayat',
                  onPressed: _confirmClear,
                ),
            ],
            bottom: TabBar(
              controller: _tab,
              tabs: const <Widget>[
                Tab(icon: Icon(Icons.star), text: 'Favorit'),
                Tab(icon: Icon(Icons.history), text: 'Terakhir dibuka'),
              ],
            ),
          ),
          body: TabBarView(
            controller: _tab,
            children: <Widget>[
              _list(context, false),
              _list(context, true),
            ],
          ),
        );
      },
    );
  }
}
