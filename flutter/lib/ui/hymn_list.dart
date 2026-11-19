import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:hkbp/data/models.dart';
import 'package:hkbp/data/prefs.dart';
import 'package:hkbp/ui/detail.dart';

final RegExp _digitsOrSpaces = RegExp(r'^[0-9 ]+$');
final RegExp _numberWithSuffix = RegExp(r'^\d+[a-z]?$');

/// Hasil pencarian: nomor dicocokkan dulu, lalu judul, lalu isi lirik.
/// Setiap hasil = (indeks di [hymns], lagu).
List<(int, Hymn)> searchHymns(List<Hymn> hymns, String query, String? cat) {
  final List<(int, Hymn)> base = <(int, Hymn)>[];
  for (var i = 0; i < hymns.length; i++) {
    final h = hymns[i];
    if (cat == null || h.category == cat) base.add((i, h));
  }
  final q = Hymn.normal(query).trim();
  if (q.isEmpty) return base;
  if (_digitsOrSpaces.hasMatch(q) || _numberWithSuffix.hasMatch(q)) {
    final qq = q.replaceAll(' ', '');
    final exact = base.where((r) => r.$2.id == qq);
    final starts = base.where((r) => r.$2.id != qq && r.$2.id.startsWith(qq));
    return <(int, Hymn)>[...exact, ...starts];
  }
  final words = q.split(' ').where((w) => w.isNotEmpty).toList();
  final hits = base.where((r) => words.every((w) => r.$2.search.contains(w))).toList();
  final inTitle = <(int, Hymn)>[];
  final inTitleIdx = <int>{};
  for (final r in hits) {
    final t = Hymn.normal(r.$2.title);
    if (words.every((w) => t.contains(w))) {
      inTitle.add(r);
      inTitleIdx.add(r.$1);
    }
  }
  return <(int, Hymn)>[
    ...inTitle,
    ...hits.where((r) => !inTitleIdx.contains(r.$1)),
  ];
}

/// Lencana nomor lagu 48x48, sudut 14, warna primaryContainer.
class NumberBadge extends StatelessWidget {
  const NumberBadge(this.text, {super.key, this.small});

  final String text;
  final String? small;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;
    final mainStyle = (text.length > 3 ? tt.titleSmall : tt.titleMedium) ?? const TextStyle();
    return Container(
      width: 48,
      height: 48,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: scheme.primaryContainer,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: <Widget>[
          if (small != null)
            Text(
              small!,
              style: (tt.labelSmall ?? const TextStyle()).copyWith(
                color: scheme.onPrimaryContainer.withValues(alpha: 0.7),
              ),
            ),
          Text(
            text,
            maxLines: 1,
            softWrap: false,
            overflow: TextOverflow.clip,
            style: mainStyle.copyWith(
              fontWeight: FontWeight.w600,
              color: scheme.onPrimaryContainer,
            ),
          ),
        ],
      ),
    );
  }
}

/// Satu baris lagu dalam daftar (setara HymnRow di Kotlin).
class HymnTile extends StatelessWidget {
  const HymnTile({
    super.key,
    required this.hymn,
    required this.fav,
    this.showBook = false,
    required this.onTap,
  });

  final Hymn hymn;
  final bool fav;
  final bool showBook;
  final VoidCallback onTap;

  String? _subtitle() {
    final h = hymn;
    if (h.firstLine.isNotEmpty && Hymn.normal(h.firstLine).trim() != Hymn.normal(h.title).trim()) {
      return h.firstLine;
    }
    if (h.category != null) return h.category;
    if (h.credits.isNotEmpty) return h.credits.first;
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final sub = _subtitle();
    return ListTile(
      onTap: onTap,
      leading: NumberBadge(hymn.id, small: showBook ? hymn.book.short : null),
      title: Text(
        hymn.title,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: Theme.of(context).textTheme.titleMedium,
      ),
      subtitle: sub == null ? null : Text(sub, maxLines: 1, overflow: TextOverflow.ellipsis),
      trailing: fav ? Icon(Icons.star, color: scheme.primary, semanticLabel: 'Favorit') : null,
    );
  }
}

class HymnListScreen extends StatefulWidget {
  const HymnListScreen({
    super.key,
    required this.book,
    required this.hymns,
    required this.prefs,
    this.back,
  });

  final Book book;
  final List<Hymn> hymns;
  final Prefs prefs;

  /// Kait tombol back dari Shell: mengembalikan true bila back sudah ditangani di sini.
  final BackHook? back;

  @override
  State<HymnListScreen> createState() => _HymnListScreenState();
}

/// Penghubung tombol back antara Shell dan layar di dalam tab.
class BackHook {
  bool Function()? handle;
}

class _HymnListScreenState extends State<HymnListScreen> with AutomaticKeepAliveClientMixin<HymnListScreen> {
  final TextEditingController _queryCtl = TextEditingController();
  final ScrollController _scroll = ScrollController();

  String _query = '';
  bool _searching = false;
  String? _cat;
  List<String> _cats = const <String>[];
  List<(int, Hymn)> _shown = const <(int, Hymn)>[];

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    widget.back?.handle = () {
      if (!_searching) return false;
      _closeSearch();
      return true;
    };
    _cats = _categoriesOf(widget.hymns);
    _shown = searchHymns(widget.hymns, _query, _cat);
  }

  @override
  void didUpdateWidget(covariant HymnListScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!identical(oldWidget.hymns, widget.hymns)) {
      _cats = _categoriesOf(widget.hymns);
      if (_cat != null && !_cats.contains(_cat)) _cat = null;
      _shown = searchHymns(widget.hymns, _query, _cat);
    }
  }

  @override
  void dispose() {
    _queryCtl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  static List<String> _categoriesOf(List<Hymn> hymns) {
    // Set literal mempertahankan urutan kemunculan (LinkedHashSet).
    return <String>{...hymns.map((h) => h.category).whereType<String>()}.toList();
  }

  /// Ubah kueri/kategori, hitung ulang hasil, lalu gulir ke atas bila berubah.
  void _setFilter({String? query, String? cat, bool setCat = false}) {
    final newQuery = query ?? _query;
    final newCat = setCat ? cat : _cat;
    if (newQuery == _query && newCat == _cat) return;
    setState(() {
      _query = newQuery;
      _cat = newCat;
      _shown = searchHymns(widget.hymns, _query, _cat);
    });
    if (_scroll.hasClients) _scroll.jumpTo(0);
  }

  void _open(int index) {
    openHymn(context, widget.hymns, index, widget.prefs);
  }

  void _startSearch() {
    setState(() => _searching = true);
  }

  void _closeSearch() {
    _queryCtl.clear();
    FocusScope.of(context).unfocus();
    setState(() => _searching = false);
    _setFilter(query: '');
  }

  Future<void> _showNumberDialog() async {
    final index = await showDialog<int>(
      context: context,
      builder: (_) => _NumberDialog(book: widget.book, hymns: widget.hymns),
    );
    if (!mounted || index == null) return;
    _open(index);
  }

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;
    if (_searching) {
      return AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          tooltip: 'Tutup pencarian',
          onPressed: _closeSearch,
        ),
        titleSpacing: 0,
        title: TextField(
          controller: _queryCtl,
          autofocus: true,
          textInputAction: TextInputAction.search,
          style: tt.titleMedium,
          decoration: const InputDecoration(
            hintText: 'Nomor, judul, atau lirik',
            border: InputBorder.none,
            enabledBorder: InputBorder.none,
            focusedBorder: InputBorder.none,
            filled: false,
          ),
          onChanged: (v) => _setFilter(query: v),
          onSubmitted: (_) {
            if (_shown.isNotEmpty) _open(_shown.first.$1);
          },
        ),
        actions: <Widget>[
          if (_query.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.close),
              tooltip: 'Hapus',
              onPressed: () {
                _queryCtl.clear();
                _setFilter(query: '');
              },
            ),
        ],
      );
    }
    return AppBar(
      title: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text('${widget.book.label} HKBP', style: tt.titleLarge),
          Text(
            '${widget.hymns.length} lagu · lirik, not angka, not balok',
            style: (tt.labelMedium ?? const TextStyle()).copyWith(color: scheme.onSurfaceVariant),
          ),
        ],
      ),
      actions: <Widget>[
        IconButton(
          icon: const Icon(Icons.search),
          tooltip: 'Cari',
          onPressed: _startSearch,
        ),
      ],
    );
  }

  Widget _buildChips() {
    return SizedBox(
      height: 48,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        children: <Widget>[
          FilterChip(
            label: const Text('Semua'),
            selected: _cat == null,
            onSelected: (_) => _setFilter(cat: null, setCat: true),
          ),
          for (final c in _cats) ...<Widget>[
            const SizedBox(width: 8),
            FilterChip(
              label: Text(c),
              selected: _cat == c,
              onSelected: (_) => _setFilter(cat: _cat == c ? null : c, setCat: true),
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final scheme = Theme.of(context).colorScheme;
    final shown = _shown;
    // Sengaja tanpa PopScope: Lists.kt tidak punya BackHandler untuk mode cari, dan di dalam
    // IndexedStack PopScope dari tab yang tersembunyi tetap terdaftar sehingga menahan tombol kembali.
    return Scaffold(
      appBar: _buildAppBar(context),
      floatingActionButton: _searching
          ? null
          : FloatingActionButton.extended(
              onPressed: _showNumberDialog,
              icon: const Icon(Icons.dialpad),
              label: const Text('Nomor'),
            ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          if (_cats.isNotEmpty) _buildChips(),
          if (shown.isEmpty)
            Padding(
              padding: const EdgeInsets.all(32),
              child: Text(
                'Tidak ada lagu yang cocok dengan “$_query”.',
                textAlign: TextAlign.center,
                style: TextStyle(color: scheme.onSurfaceVariant),
              ),
            ),
          Expanded(
            child: ListenableBuilder(
              listenable: widget.prefs,
              builder: (BuildContext context, Widget? _) {
                return ListView.builder(
                  controller: _scroll,
                  padding: const EdgeInsets.only(bottom: 96),
                  itemCount: shown.length,
                  itemBuilder: (BuildContext context, int n) {
                    final (i, h) = shown[n];
                    return HymnTile(
                      key: ValueKey<String>(h.key2),
                      hymn: h,
                      fav: widget.prefs.isFavorite(h.key2),
                      onTap: () => _open(i),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

/// Dialog "Buka <label> nomor". Mengembalikan indeks lagu lewat Navigator.pop.
class _NumberDialog extends StatefulWidget {
  const _NumberDialog({required this.book, required this.hymns});

  final Book book;
  final List<Hymn> hymns;

  @override
  State<_NumberDialog> createState() => _NumberDialogState();
}

class _NumberDialogState extends State<_NumberDialog> {
  final TextEditingController _ctl = TextEditingController();
  String? _err;

  @override
  void initState() {
    super.initState();
    _ctl.addListener(_onText);
  }

  @override
  void dispose() {
    _ctl.removeListener(_onText);
    _ctl.dispose();
    super.dispose();
  }

  void _onText() {
    // Perbarui tombol Buka dan hapus pesan galat saat teks berubah.
    setState(() => _err = null);
  }

  void _go() {
    final t = _ctl.text.trim().toLowerCase();
    if (t.isEmpty) return;
    final hymns = widget.hymns;
    var i = hymns.indexWhere((h) => h.id == t);
    if (i < 0) {
      final n = int.tryParse(t);
      if (n != null) i = hymns.indexWhere((h) => h.number == n);
    }
    if (i < 0) {
      var max = 0;
      for (final h in hymns) {
        if (h.number > max) max = h.number;
      }
      setState(() => _err = '${widget.book.short} $t tidak ada (1–$max)');
    } else {
      Navigator.of(context).pop(i);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tt = Theme.of(context).textTheme;
    final hasText = _ctl.text.trim().isNotEmpty;
    return AlertDialog(
      icon: const Icon(Icons.dialpad),
      title: Text('Buka ${widget.book.label} nomor'),
      content: TextField(
        controller: _ctl,
        autofocus: true,
        keyboardType: TextInputType.number,
        textInputAction: TextInputAction.go,
        style: tt.headlineMedium,
        inputFormatters: <TextInputFormatter>[
          FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9]')),
          LengthLimitingTextInputFormatter(4),
        ],
        decoration: InputDecoration(
          border: const OutlineInputBorder(),
          helperText: _err == null ? 'Contoh: 784' : null,
          errorText: _err,
        ),
        onSubmitted: (_) => _go(),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Batal'),
        ),
        TextButton(
          onPressed: hasText ? _go : null,
          child: const Text('Buka'),
        ),
      ],
    );
  }
}
