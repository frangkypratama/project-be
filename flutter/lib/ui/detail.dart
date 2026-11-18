import 'dart:async';

import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

import 'package:hkbp/data/models.dart';
import 'package:hkbp/data/prefs.dart';
import 'package:hkbp/music/notation.dart';
import 'package:hkbp/music/player.dart';
import 'package:hkbp/print/printer.dart';
import 'package:hkbp/ui/angka_view.dart';
import 'package:hkbp/ui/staff_view.dart';

const List<String> kViews = ['Lirik', 'Angka', 'Balok', 'Keduanya'];

void openHymn(BuildContext context, List<Hymn> hymns, int index, Prefs prefs) {
  Navigator.of(context).push(
    MaterialPageRoute<void>(
      builder: (BuildContext _) =>
          DetailScreen(hymns: hymns, start: index, prefs: prefs),
    ),
  );
}

int _clampBpm(int v) => v < 40 ? 40 : (v > 180 ? 180 : v);

String _doOf(Hymn h) => 'Do = ${Notation.doName[h.key] ?? h.key}';

String _signed(int t) => t > 0 ? '+$t' : '$t';

class DetailScreen extends StatefulWidget {
  final List<Hymn> hymns;
  final int start;
  final Prefs prefs;

  const DetailScreen({
    super.key,
    required this.hymns,
    required this.start,
    required this.prefs,
  });

  @override
  State<DetailScreen> createState() => _DetailScreenState();
}

class _DetailScreenState extends State<DetailScreen> {
  late final PageController _pager;
  late final OrganPlayer _player;
  late int _page;
  late int _view;
  int _verse = 0;
  int _bpm = 84;
  int _transpose = 0;
  bool _wake = false;

  final Map<String, List<Sec>> _secCache = <String, List<Sec>>{};
  final Map<String, String> _abcCache = <String, String>{};

  Prefs get prefs => widget.prefs;
  List<Hymn> get hymns => widget.hymns;
  Hymn get _cur => hymns[_page];

  @override
  void initState() {
    super.initState();
    _page = widget.start.clamp(0, hymns.length - 1).toInt();
    _pager = PageController(initialPage: _page);
    _player = OrganPlayer();
    _player.addListener(_onPlayer);
    _view = prefs.defaultView;
    _bpm = _clampBpm(_cur.tempo ?? 84);
    if (prefs.keepScreenOn) {
      _wake = true;
      _setWake(true);
    }
    final String startKey = _cur.key2;
    // ditunda agar notifyListeners() Prefs tidak terjadi di tengah build
    WidgetsBinding.instance.addPostFrameCallback((Duration _) {
      prefs.visit(startKey);
    });
  }

  @override
  void dispose() {
    _player.removeListener(_onPlayer);
    unawaited(_player.stop());
    _player.dispose();
    _pager.dispose();
    if (_wake) _setWake(false);
    super.dispose();
  }

  Future<void> _setWake(bool on) async {
    try {
      if (on) {
        await WakelockPlus.enable();
      } else {
        await WakelockPlus.disable();
      }
    } catch (_) {}
  }

  void _onPlayer() {
    if (!mounted) return;
    final int v = _player.curVerse;
    if (v >= 0 && v != _verse) {
      setState(() => _verse = v);
    }
  }

  void _onPageChanged(int i) {
    unawaited(_player.stop());
    final Hymn h = hymns[i];
    setState(() {
      _page = i;
      _verse = 0;
      _bpm = _clampBpm(h.tempo ?? 84);
      _transpose = 0;
    });
    prefs.visit(h.key2);
  }

  bool get _active => _player.playing || _player.preparing;

  void _stopPlay() {
    unawaited(_player.stop());
  }

  void _startPlay() {
    final List<Tone> seq =
        Notation.sequence(_cur, _verse, prefs.playAllVerses);
    unawaited(_player.play(seq, bpm: _bpm, transpose: _transpose));
  }

  void _togglePlay() {
    if (_active) {
      _stopPlay();
    } else {
      _startPlay();
    }
  }

  void _selectVerse(int k) {
    if (_active) _stopPlay();
    setState(() => _verse = k);
  }

  void _go(int target) {
    if (target < 0 || target >= hymns.length) return;
    _pager.animateToPage(
      target,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  List<Sec> _secsFor(Hymn h, int verse) {
    final String k = '${h.key2}:$verse';
    final List<Sec>? hit = _secCache[k];
    if (hit != null) return hit;
    if (_secCache.length > 16) {
      _secCache.clear();
      _abcCache.clear();
    }
    final List<Sec> secs = Notation.build(h, verse);
    _secCache[k] = secs;
    return secs;
  }

  String _abcFor(Hymn h, int verse, List<Sec> secs) {
    final String k = '${h.key2}:$verse';
    final String? hit = _abcCache[k];
    if (hit != null) return hit;
    final String abc = Notation.toAbc(h, secs);
    _abcCache[k] = abc;
    return abc;
  }

  // ---------- aksi AppBar ----------

  void _share(Hymn h) {
    final StringBuffer sb = StringBuffer();
    sb.write('${h.book.label} ${h.id} – ${h.title}\n\n');
    for (int k = 0; k < h.verses.length; k++) {
      sb.write(h.verseLabel(k));
      sb.write('. ');
      sb.write(h.verses[k].join('\n'));
      sb.write('\n\n');
    }
    sb.write(h.book.site);
    sb.write(h.id);
    sb.write('/');
    // ignore: deprecated_member_use
    Share.share(sb.toString(), subject: '${h.book.short} ${h.id} ${h.title}');
  }

  Future<void> _openSite(Hymn h) async {
    try {
      await launchUrl(
        Uri.parse('${h.book.site}${h.id}/'),
        mode: LaunchMode.externalApplication,
      );
    } catch (_) {}
  }

  void _print(Hymn h) {
    _stopPlay();
    unawaited(Printer.print(h));
  }

  void _showInfo(Hymn h) {
    showDialog<void>(
      context: context,
      builder: (BuildContext ctx) {
        final ThemeData t = Theme.of(ctx);
        final List<Widget> rows = <Widget>[
          Text(h.title, style: t.textTheme.titleMedium),
          _InfoLine('Nada dasar', _doOf(h)),
          _InfoLine('Birama', h.meter),
          if (h.logu != null && h.logu! > 0) _InfoLine('Logu', '${h.logu}'),
          if (h.category != null) _InfoLine('Kategori', h.category!),
          _InfoLine('Jumlah ayat', '${h.verses.length}'),
          for (final String c in h.credits)
            Text(c, style: t.textTheme.bodyMedium),
        ];
        return AlertDialog(
          title: Text('${h.book.label} ${h.id}'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                for (int i = 0; i < rows.length; i++) ...<Widget>[
                  if (i > 0) const SizedBox(height: 6),
                  rows[i],
                ],
              ],
            ),
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('Tutup'),
            ),
          ],
        );
      },
    );
  }

  // ---------- bottom sheet tempo & nada ----------

  void _openSheet() {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (BuildContext ctx) {
        return StatefulBuilder(
          builder: (BuildContext ctx, StateSetter setSheet) {
            return ListenableBuilder(
              listenable: Listenable.merge(<Listenable>[prefs, _player]),
              builder: (BuildContext ctx, Widget? _) {
                final ThemeData t = Theme.of(ctx);
                final Hymn h = _cur;
                void update(VoidCallback fn) {
                  setState(fn);
                  setSheet(() {});
                }

                return SafeArea(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(24, 0, 24, 32),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text('Pengaturan nada', style: t.textTheme.titleMedium),
                        const SizedBox(height: 16),
                        Text('Tempo: ♩ = $_bpm', style: t.textTheme.bodyLarge),
                        Slider(
                          value: _bpm.toDouble(),
                          min: 40,
                          max: 180,
                          divisions: 140,
                          label: '$_bpm',
                          onChanged: (double v) =>
                              update(() => _bpm = _clampBpm(v.round())),
                        ),
                        Row(
                          children: <Widget>[
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  Text('Nada dasar',
                                      style: t.textTheme.bodyLarge),
                                  Text(
                                    _doOf(h) +
                                        (_transpose == 0
                                            ? ''
                                            : ' (${_signed(_transpose)})'),
                                    style: t.textTheme.bodyMedium?.copyWith(
                                      color: t.colorScheme.onSurfaceVariant,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            IconButton.filledTonal(
                              tooltip: 'Turunkan nada',
                              onPressed: () => update(() {
                                _transpose =
                                    _transpose - 1 < -6 ? -6 : _transpose - 1;
                              }),
                              icon: const Icon(Icons.remove),
                            ),
                            SizedBox(
                              width: 40,
                              child: Text(
                                _signed(_transpose),
                                textAlign: TextAlign.center,
                                style: t.textTheme.titleMedium,
                              ),
                            ),
                            IconButton.filledTonal(
                              tooltip: 'Naikkan nada',
                              onPressed: () => update(() {
                                _transpose =
                                    _transpose + 1 > 6 ? 6 : _transpose + 1;
                              }),
                              icon: const Icon(Icons.add),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: <Widget>[
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  Text('Putar semua ayat',
                                      style: t.textTheme.bodyLarge),
                                  Text(
                                    'Lanjut ke ayat berikutnya setelah satu ayat selesai',
                                    style: t.textTheme.bodyMedium?.copyWith(
                                      color: t.colorScheme.onSurfaceVariant,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Switch(
                              value: prefs.playAllVerses,
                              onChanged: (bool v) => prefs.setPlayAllVerses(v),
                            ),
                          ],
                        ),
                        if (_active) ...<Widget>[
                          const SizedBox(height: 8),
                          Text(
                            'Berlaku saat diputar ulang',
                            style: t.textTheme.bodySmall?.copyWith(
                              color: t.colorScheme.onSurfaceVariant,
                            ),
                          ),
                        ],
                        const SizedBox(height: 8),
                        TextButton(
                          onPressed: () => update(() {
                            _bpm = _clampBpm(_cur.tempo ?? 84);
                            _transpose = 0;
                          }),
                          child: const Text('Kembalikan ke bawaan'),
                        ),
                      ],
                    ),
                  ),
                );
              },
            );
          },
        );
      },
    );
  }

  // ---------- build ----------

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: Listenable.merge(<Listenable>[_player, prefs]),
      builder: (BuildContext context, Widget? _) => _buildScaffold(context),
    );
  }

  Widget _buildScaffold(BuildContext context) {
    final ThemeData t = Theme.of(context);
    final ColorScheme cs = t.colorScheme;
    final Hymn h = _cur;
    final bool fav = prefs.isFavorite(h.key2);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          tooltip: 'Kembali',
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).maybePop(),
        ),
        titleSpacing: 0,
        title: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              h.ref,
              style: t.textTheme.titleLarge
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
            Text(
              h.title,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: t.textTheme.labelLarge
                  ?.copyWith(color: cs.onSurfaceVariant),
            ),
          ],
        ),
        actions: <Widget>[
          IconButton(
            tooltip: fav ? 'Hapus dari favorit' : 'Tambah ke favorit',
            icon: Icon(
              fav ? Icons.star : Icons.star_border,
              color: fav ? cs.primary : cs.onSurfaceVariant,
            ),
            onPressed: () => prefs.toggleFavorite(h.key2),
          ),
          IconButton(
            tooltip: 'Bagikan',
            icon: const Icon(Icons.share),
            onPressed: () => _share(h),
          ),
          PopupMenuButton<int>(
            tooltip: 'Lainnya',
            icon: const Icon(Icons.more_vert),
            onSelected: (int v) {
              final Hymn x = _cur;
              switch (v) {
                case 0:
                  _print(x);
                  break;
                case 1:
                  _showInfo(x);
                  break;
                case 2:
                  _openSite(x);
                  break;
              }
            },
            itemBuilder: (BuildContext _) => const <PopupMenuEntry<int>>[
              PopupMenuItem<int>(
                value: 0,
                child: _MenuRow(Icons.print, 'Cetak / simpan PDF'),
              ),
              PopupMenuItem<int>(
                value: 1,
                child: _MenuRow(Icons.info, 'Info lagu'),
              ),
              PopupMenuItem<int>(
                value: 2,
                child: _MenuRow(Icons.open_in_new, 'Buka di bukuende.com'),
              ),
            ],
          ),
        ],
      ),
      bottomNavigationBar: _playerBar(context),
      body: Column(
        children: <Widget>[
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: SizedBox(
              width: double.infinity,
              child: SegmentedButton<int>(
                showSelectedIcon: false,
                segments: <ButtonSegment<int>>[
                  for (int i = 0; i < kViews.length; i++)
                    ButtonSegment<int>(value: i, label: Text(kViews[i])),
                ],
                selected: <int>{_view},
                onSelectionChanged: (Set<int> s) {
                  if (s.isNotEmpty) setState(() => _view = s.first);
                },
              ),
            ),
          ),
          Expanded(
            // geser ke lagu lain hanya di tampilan Lirik; di not angka/balok pakai tombol ‹ ›
            child: PageView.builder(
              controller: _pager,
              physics: _view == 0
                  ? const PageScrollPhysics()
                  : const NeverScrollableScrollPhysics(),
              itemCount: hymns.length,
              onPageChanged: _onPageChanged,
              itemBuilder: (BuildContext context, int p) => _hymnPage(context, p),
            ),
          ),
        ],
      ),
    );
  }

  Widget _playerBar(BuildContext context) {
    final ThemeData t = Theme.of(context);
    final ColorScheme cs = t.colorScheme;
    final Hymn h = _cur;
    final bool playing = _player.playing;
    final bool preparing = _player.preparing;
    final int n = h.verses.length;
    final String line1 =
        n > 1 ? 'Ayat ${h.verseLabel(_verse)} dari $n' : 'Nada lagu';
    final String line2 = _doOf(h) +
        (_transpose != 0 ? ' (${_signed(_transpose)})' : '') +
        ' · ♩ = $_bpm';

    return Material(
      elevation: 6,
      color: cs.surfaceContainer,
      shadowColor: cs.shadow,
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          child: Row(
            children: <Widget>[
              IconButton(
                tooltip: 'Lagu sebelumnya',
                icon: const Icon(Icons.chevron_left),
                onPressed: _page > 0 ? () => _go(_page - 1) : null,
              ),
              Tooltip(
                message: (playing || preparing) ? 'Berhenti' : 'Putar nada',
                child: SizedBox(
                  width: 56,
                  height: 56,
                  child: FilledButton(
                    style: FilledButton.styleFrom(
                      shape: const CircleBorder(),
                      padding: EdgeInsets.zero,
                      minimumSize: const Size(56, 56),
                      fixedSize: const Size(56, 56),
                    ),
                    onPressed: _togglePlay,
                    child: preparing
                        ? SizedBox(
                            width: 24,
                            height: 24,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: cs.onPrimary,
                            ),
                          )
                        : Icon(
                            playing ? Icons.stop : Icons.play_arrow,
                            size: 30,
                          ),
                  ),
                ),
              ),
              Expanded(
                child: InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: _openSheet,
                  child: Padding(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          line1,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: t.textTheme.titleSmall,
                        ),
                        Text(
                          line2,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: t.textTheme.bodySmall
                              ?.copyWith(color: cs.onSurfaceVariant),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              IconButton(
                tooltip: 'Tempo dan nada',
                icon: const Icon(Icons.tune),
                onPressed: _openSheet,
              ),
              IconButton(
                tooltip: 'Lagu berikutnya',
                icon: const Icon(Icons.chevron_right),
                onPressed:
                    _page < hymns.length - 1 ? () => _go(_page + 1) : null,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _hymnPage(BuildContext context, int p) {
    final Hymn h = hymns[p];
    final bool isCur = p == _page;
    final int verse = isCur ? _verse : 0;
    final int curSi = isCur ? _player.curSi : -1;
    final double scale = prefs.textScale;

    if (_view == 0) {
      return _lyrics(context, h, verse, scale);
    }

    final List<Sec> secs = _secsFor(h, verse);
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          _HymnHeader(h),
          _verseChips(context, h, verse),
          const SizedBox(height: 4),
          if (_view == 1 || _view == 3)
            ScoreCard(
              key: const ValueKey<String>('angka'),
              'Not angka',
              AngkaView(
                secs: secs,
                curSi: curSi,
                scale: scale,
                bn: h.book == Book.bn,
              ),
            ),
          if (_view == 2 || _view == 3)
            ScoreCard(
              key: const ValueKey<String>('balok'),
              'Not balok',
              StaffView(abc: _abcFor(h, verse, secs), curSi: curSi),
            ),
          _Credits(h),
        ],
      ),
    );
  }

  Widget _lyrics(BuildContext context, Hymn h, int verse, double scale) {
    final ThemeData t = Theme.of(context);
    final ColorScheme cs = t.colorScheme;
    final double fs = 17 * scale;
    final double labelW = scale > 1 ? 34 * scale : 34;
    return ListView.builder(
      padding: const EdgeInsets.only(bottom: 24),
      itemCount: h.verses.length + 2,
      itemBuilder: (BuildContext context, int i) {
        if (i == 0) return _HymnHeader(h);
        if (i == h.verses.length + 1) return _Credits(h);
        final int k = i - 1;
        final List<String> lines = h.verses[k];
        final bool sel = k == verse && h.verses.length > 1;
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          child: Material(
            color: sel
                ? cs.secondaryContainer.withValues(alpha: 0.55)
                : Colors.transparent,
            borderRadius: BorderRadius.circular(16),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: () => _selectVerse(k),
              child: Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    SizedBox(
                      width: labelW,
                      child: Text(
                        h.verseLabel(k),
                        style: t.textTheme.titleMedium?.copyWith(
                          fontSize: fs,
                          height: 26 / 17,
                          color: cs.primary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          for (final String line in lines)
                            Text(
                              line,
                              style: t.textTheme.bodyLarge?.copyWith(
                                fontSize: fs,
                                height: 26 / 17,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _verseChips(BuildContext context, Hymn h, int verse) {
    if (h.verses.length <= 1) return const SizedBox.shrink();
    final ThemeData t = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: <Widget>[
              for (int k = 0; k < h.verses.length; k++)
                Padding(
                  padding: EdgeInsets.only(left: k == 0 ? 0 : 8),
                  child: ChoiceChip(
                    showCheckmark: false,
                    selected: k == verse,
                    label: Text('Ayat ${h.verseLabel(k)}'),
                    onSelected: (bool _) => _selectVerse(k),
                  ),
                ),
            ],
          ),
        ),
        if (verse > 0 && !h.readyVerses.contains(verse))
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Text(
              'Lirik ayat ${h.verseLabel(verse)} belum dipasang ke not. '
              'Teksnya ada di tab Lirik.',
              style: t.textTheme.bodySmall
                  ?.copyWith(color: t.colorScheme.onSurfaceVariant),
            ),
          ),
      ],
    );
  }
}

class _MenuRow extends StatelessWidget {
  final IconData icon;
  final String text;

  const _MenuRow(this.icon, this.text);

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Icon(icon, size: 22),
        const SizedBox(width: 12),
        Text(text),
      ],
    );
  }
}

class _InfoLine extends StatelessWidget {
  final String k;
  final String v;

  const _InfoLine(this.k, this.v);

  @override
  Widget build(BuildContext context) {
    final ColorScheme cs = Theme.of(context).colorScheme;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        SizedBox(
          width: 110,
          child: Text(k, style: TextStyle(color: cs.onSurfaceVariant)),
        ),
        Expanded(child: Text(v)),
      ],
    );
  }
}

/// Bingkai not: memisahkan partitur dari halaman, seperti lembar partitur.
class ScoreCard extends StatelessWidget {
  final String label;
  final Widget child;

  const ScoreCard(this.label, this.child, {super.key});

  @override
  Widget build(BuildContext context) {
    final ThemeData t = Theme.of(context);
    final ColorScheme cs = t.colorScheme;
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      padding: const EdgeInsets.fromLTRB(10, 10, 10, 12),
      decoration: BoxDecoration(
        color: cs.surfaceContainerLowest,
        border: Border.all(color: cs.outlineVariant, width: 1),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Padding(
            padding: const EdgeInsets.only(left: 4, bottom: 6),
            child: Text(
              label.toUpperCase(),
              style: t.textTheme.labelMedium?.copyWith(color: cs.primary),
            ),
          ),
          child,
        ],
      ),
    );
  }
}

class _HymnHeader extends StatelessWidget {
  final Hymn h;

  const _HymnHeader(this.h);

  @override
  Widget build(BuildContext context) {
    final ThemeData t = Theme.of(context);
    final List<String> meta = <String>[
      _doOf(h),
      h.meter,
      if (h.logu != null && h.logu! > 0) 'Logu ${h.logu}',
      if (h.category != null) h.category!,
    ];
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: SizedBox(
        width: double.infinity,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              h.title,
              style: t.textTheme.headlineSmall
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
            Text(
              meta.join(' · '),
              style: t.textTheme.labelLarge
                  ?.copyWith(color: t.colorScheme.primary),
            ),
          ],
        ),
      ),
    );
  }
}

class _Credits extends StatelessWidget {
  final Hymn h;

  const _Credits(this.h);

  @override
  Widget build(BuildContext context) {
    if (h.credits.isEmpty) return const SizedBox.shrink();
    final ThemeData t = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Divider(height: 1, color: t.colorScheme.outlineVariant),
          const SizedBox(height: 8),
          for (final String c in h.credits)
            Text(
              c,
              style: t.textTheme.bodySmall
                  ?.copyWith(color: t.colorScheme.onSurfaceVariant),
            ),
        ],
      ),
    );
  }
}
