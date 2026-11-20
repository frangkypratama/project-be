package com.bukuende.hkbp.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.OpenInNew
import androidx.compose.material.icons.filled.ChevronLeft
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Print
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material.icons.outlined.StarOutline
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.FilledTonalIconButton
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.bukuende.hkbp.data.Book
import com.bukuende.hkbp.data.Hymn
import com.bukuende.hkbp.data.Prefs
import com.bukuende.hkbp.music.Notation
import com.bukuende.hkbp.music.OrganPlayer
import kotlinx.coroutines.launch
import kotlin.math.roundToInt

val VIEWS = listOf("Lirik", "Angka", "Balok", "Keduanya")

private fun clampBpm(v: Int) = v.coerceIn(40, 180)

@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
@Composable
fun DetailScreen(hymns: List<Hymn>, start: Int, prefs: Prefs, onBack: () -> Unit) {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    val pager = rememberPagerState(initialPage = start) { hymns.size }
    val settled = pager.settledPage
    val h = hymns[pager.currentPage]
    val cur = hymns[settled]

    val player = remember { OrganPlayer() }
    var playing by remember { mutableStateOf(false) }
    var curSi by remember { mutableIntStateOf(-1) }
    var verse by remember { mutableIntStateOf(0) }
    // tampilan lagu = pengaturan aplikasi: diingat dan tidak berubah saat pindah lagu
    val view = prefs.defaultView
    var bpm by remember { mutableIntStateOf(84) }
    var transpose by remember { mutableIntStateOf(0) }
    var menu by remember { mutableStateOf(false) }
    var info by remember { mutableStateOf(false) }
    var sheet by remember { mutableStateOf(false) }

    DisposableEffect(Unit) { onDispose { player.stop() } }

    val root = LocalView.current
    DisposableEffect(prefs.keepScreenOn) {
        root.keepScreenOn = prefs.keepScreenOn
        onDispose { root.keepScreenOn = false }
    }

    LaunchedEffect(settled) {
        player.stop()
        playing = false
        curSi = -1
        verse = 0
        bpm = clampBpm(cur.tempo ?: 84)
        transpose = 0
        prefs.visit(cur.key2)
    }

    fun stopPlay() {
        player.stop()
        playing = false
        curSi = -1
    }

    fun startPlay() {
        val seq = Notation.sequence(cur, verse, prefs.playAllVerses, prefs.chordsOn)
        player.bpm = bpm
        player.transpose = transpose
        player.play(seq, object : OrganPlayer.Listener {
            override fun onNote(si: Int, verse2: Int) {
                curSi = si
                if (verse2 >= 0 && verse2 != verse) verse = verse2
            }

            override fun onEnd() {
                playing = false
                curSi = -1
            }
        })
        playing = true
    }

    val selectVerse: (Int) -> Unit = { k ->
        if (playing) stopPlay()
        verse = k
    }

    Scaffold(
        topBar = {
            TopAppBar(
                navigationIcon = {
                    IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Kembali") }
                },
                title = {
                    Column {
                        Text(h.ref, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                        Text(
                            h.title, style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            maxLines = 1, overflow = TextOverflow.Ellipsis,
                        )
                    }
                },
                actions = {
                    val fav = prefs.isFavorite(h.key2)
                    IconButton(onClick = { prefs.toggleFavorite(h.key2) }) {
                        Icon(
                            if (fav) Icons.Filled.Star else Icons.Outlined.StarOutline,
                            contentDescription = if (fav) "Hapus dari favorit" else "Tambah ke favorit",
                            tint = if (fav) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    IconButton(onClick = { share(ctx, h) }) { Icon(Icons.Filled.Share, contentDescription = "Bagikan") }
                    IconButton(onClick = { menu = true }) { Icon(Icons.Filled.MoreVert, contentDescription = "Lainnya") }
                    DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
                        DropdownMenuItem(
                            text = { Text("Cetak / simpan PDF") },
                            leadingIcon = { Icon(Icons.Filled.Print, null) },
                            onClick = { menu = false; stopPlay(); Printer.print(ctx, h) },
                        )
                        DropdownMenuItem(
                            text = { Text("Info lagu") },
                            leadingIcon = { Icon(Icons.Filled.Info, null) },
                            onClick = { menu = false; info = true },
                        )
                        DropdownMenuItem(
                            text = { Text("Buka di bukuende.com") },
                            leadingIcon = { Icon(Icons.AutoMirrored.Filled.OpenInNew, null) },
                            onClick = {
                                menu = false
                                try {
                                    ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(h.book.site + h.id + "/")))
                                } catch (e: Exception) { }
                            },
                        )
                    }
                },
            )
        },
        bottomBar = {
            PlayerBar(
                hymn = cur, verse = verse, playing = playing, bpm = bpm, transpose = transpose,
                hasPrev = settled > 0, hasNext = settled < hymns.size - 1,
                onPlay = { if (playing) stopPlay() else startPlay() },
                onPrev = { scope.launch { pager.animateScrollToPage(settled - 1) } },
                onNext = { scope.launch { pager.animateScrollToPage(settled + 1) } },
                onTune = { sheet = true },
            )
        },
    ) { pad ->
        Column(Modifier.padding(pad).fillMaxSize()) {
            Segments(VIEWS, view, { prefs.useDefaultView(it) }, Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp))
            // geser ke lagu lain hanya di tampilan Lirik; di not angka/balok pakai tombol ‹ › agar tidak tergeser
            HorizontalPager(
                state = pager,
                modifier = Modifier.fillMaxSize(),
                userScrollEnabled = view == 0,
                key = { hymns[it].key2 },
            ) { p ->
                val isCur = p == settled
                HymnPage(
                    h = hymns[p],
                    view = view,
                    verse = if (isCur) verse else 0,
                    curSi = if (isCur) curSi else -1,
                    scale = prefs.textScale,
                    onVerse = selectVerse,
                    chords = prefs.chordsOn,
                    transpose = if (isCur) transpose else 0,
                )
            }
        }
    }

    if (sheet) {
        ModalBottomSheet(onDismissRequest = { sheet = false }) {
            Column(Modifier.verticalScroll(rememberScrollState()).padding(horizontal = 24.dp).padding(bottom = 32.dp)) {
                Text("Pengaturan lagu", style = MaterialTheme.typography.titleMedium)
                Text(
                    "Ukuran huruf, tema, dan tampilan berlaku untuk semua lagu. Tempo dan nada kembali ke bawaan tiap lagu.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(Modifier.height(16.dp))
                Text("TAMPILAN", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                Spacer(Modifier.height(8.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Ukuran huruf: ${(prefs.textScale * 100).roundToInt()}%", style = MaterialTheme.typography.bodyLarge, modifier = Modifier.weight(1f))
                    FilledTonalIconButton(onClick = { prefs.useTextScale(((prefs.textScale - 0.1f) * 20).roundToInt().coerceIn(16, 36) / 20f) }) {
                        Text("A−", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    }
                    Spacer(Modifier.width(8.dp))
                    FilledTonalIconButton(onClick = { prefs.useTextScale(((prefs.textScale + 0.1f) * 20).roundToInt().coerceIn(16, 36) / 20f) }) {
                        Text("A+", fontWeight = FontWeight.Bold, fontSize = 17.sp)
                    }
                }
                Slider(
                    value = prefs.textScale,
                    onValueChange = { prefs.useTextScale((it * 20).roundToInt() / 20f) },
                    valueRange = 0.8f..1.8f,
                    steps = 19,
                )
                Text("Tema", style = MaterialTheme.typography.bodyLarge)
                Spacer(Modifier.height(6.dp))
                Segments(listOf("Sistem", "Terang", "Gelap"), prefs.theme, { prefs.useTheme(it) }, Modifier.fillMaxWidth())
                Spacer(Modifier.height(20.dp))
                Text("NADA", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                Spacer(Modifier.height(8.dp))
                Text("Tempo: ♩ = $bpm", style = MaterialTheme.typography.bodyLarge)
                Slider(
                    value = bpm.toFloat(),
                    onValueChange = { bpm = clampBpm(it.toInt()); player.bpm = bpm },
                    valueRange = 40f..180f,
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Nada dasar", style = MaterialTheme.typography.bodyLarge)
                        Text(
                            "Do = ${Notation.DO_NAME[cur.key] ?: cur.key}" +
                                if (transpose == 0) "" else " (${if (transpose > 0) "+" else ""}$transpose)",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    FilledTonalIconButton(onClick = { transpose = (transpose - 1).coerceAtLeast(-6); player.transpose = transpose }) {
                        Icon(Icons.Filled.Remove, contentDescription = "Turunkan nada")
                    }
                    Text(
                        (if (transpose > 0) "+" else "") + transpose,
                        modifier = Modifier.width(40.dp),
                        style = MaterialTheme.typography.titleMedium,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                    )
                    FilledTonalIconButton(onClick = { transpose = (transpose + 1).coerceAtMost(6); player.transpose = transpose }) {
                        Icon(Icons.Filled.Add, contentDescription = "Naikkan nada")
                    }
                }
                Spacer(Modifier.height(12.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Putar semua ayat", style = MaterialTheme.typography.bodyLarge)
                        Text(
                            "Lanjut ke ayat berikutnya setelah satu ayat selesai",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    Switch(checked = prefs.playAllVerses, onCheckedChange = { prefs.setPlayAll(it) })
                }
                Spacer(Modifier.height(12.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Akor iringan", style = MaterialTheme.typography.bodyLarge)
                        Text(
                            "Nama akor di not angka dan not balok, iringan ikut berbunyi",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    Switch(checked = prefs.chordsOn, onCheckedChange = { if (playing) stopPlay(); prefs.useChords(it) })
                }
                Spacer(Modifier.height(8.dp))
                TextButton(onClick = { bpm = clampBpm(cur.tempo ?: 84); transpose = 0; player.bpm = bpm; player.transpose = 0 }) {
                    Text("Kembalikan ke bawaan")
                }
            }
        }
    }

    if (info) {
        AlertDialog(
            onDismissRequest = { info = false },
            title = { Text("${h.book.label} ${h.id}") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(h.title, style = MaterialTheme.typography.titleMedium)
                    InfoLine("Nada dasar", "Do = ${Notation.DO_NAME[h.key] ?: h.key}")
                    InfoLine("Birama", h.meter)
                    h.logu?.takeIf { it > 0 }?.let { InfoLine("Logu", it.toString()) }
                    h.category?.let { InfoLine("Kategori", it) }
                    InfoLine("Jumlah ayat", h.verses.size.toString())
                    h.credits.forEach { Text(it, style = MaterialTheme.typography.bodyMedium) }
                }
            },
            confirmButton = { TextButton(onClick = { info = false }) { Text("Tutup") } },
        )
    }
}

@Composable
private fun InfoLine(k: String, v: String) {
    Row {
        Text(k, modifier = Modifier.width(110.dp), color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(v)
    }
}

private fun share(ctx: android.content.Context, h: Hymn) {
    val text = buildString {
        append("${h.book.label} ${h.id} – ${h.title}\n\n")
        h.verses.forEachIndexed { k, v ->
            append(h.verseLabel(k)).append(". ").append(v.joinToString("\n")).append("\n\n")
        }
        append(h.book.site).append(h.id).append("/")
    }
    val i = Intent(Intent.ACTION_SEND).setType("text/plain")
        .putExtra(Intent.EXTRA_SUBJECT, "${h.book.short} ${h.id} ${h.title}")
        .putExtra(Intent.EXTRA_TEXT, text)
    ctx.startActivity(Intent.createChooser(i, "Bagikan lirik"))
}

@Composable
private fun PlayerBar(
    hymn: Hymn, verse: Int, playing: Boolean, bpm: Int, transpose: Int,
    hasPrev: Boolean, hasNext: Boolean,
    onPlay: () -> Unit, onPrev: () -> Unit, onNext: () -> Unit, onTune: () -> Unit,
) {
    Surface(tonalElevation = 3.dp, shadowElevation = 6.dp) {
        Row(
            Modifier.fillMaxWidth().navigationBarsPadding().padding(horizontal = 8.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onPrev, enabled = hasPrev) { Icon(Icons.Filled.ChevronLeft, contentDescription = "Lagu sebelumnya") }
            FilledIconButton(
                onClick = onPlay,
                modifier = Modifier.size(56.dp),
                colors = IconButtonDefaults.filledIconButtonColors(),
            ) {
                Icon(
                    if (playing) Icons.Filled.Stop else Icons.Filled.PlayArrow,
                    contentDescription = if (playing) "Berhenti" else "Putar nada",
                    modifier = Modifier.size(30.dp),
                )
            }
            Column(Modifier.weight(1f).padding(horizontal = 12.dp).clickable(onClick = onTune)) {
                val n = hymn.verses.size
                Text(
                    if (n > 1) "Ayat ${hymn.verseLabel(verse)} dari $n" else "Nada lagu",
                    style = MaterialTheme.typography.titleSmall,
                )
                Text(
                    "Do = ${Notation.DO_NAME[hymn.key] ?: hymn.key}" +
                        (if (transpose != 0) " (${if (transpose > 0) "+" else ""}$transpose)" else "") +
                        " · ♩ = $bpm",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            IconButton(onClick = onTune) { Icon(Icons.Filled.Tune, contentDescription = "Tempo dan nada") }
            IconButton(onClick = onNext, enabled = hasNext) { Icon(Icons.Filled.ChevronRight, contentDescription = "Lagu berikutnya") }
        }
    }
}

/** Bingkai not: memisahkan partitur dari halaman, seperti lembar partitur. */
@Composable
private fun ScoreCard(label: String, content: @Composable () -> Unit) {
    Surface(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp),
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.surfaceContainerLowest,
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
    ) {
        Column(Modifier.padding(start = 10.dp, end = 10.dp, top = 10.dp, bottom = 12.dp)) {
            Text(
                label.uppercase(),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(start = 4.dp, bottom = 6.dp),
            )
            content()
        }
    }
}

@Composable
private fun HymnHeader(h: Hymn) {
    Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp)) {
        Text(h.title, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
        val meta = listOfNotNull(
            "Do = ${Notation.DO_NAME[h.key] ?: h.key}", h.meter,
            h.logu?.takeIf { it > 0 }?.let { "Logu $it" }, h.category,
        ).joinToString(" · ")
        Text(meta, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
    }
}

@Composable
private fun Credits(h: Hymn) {
    if (h.credits.isEmpty()) return
    Column(Modifier.padding(16.dp)) {
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        Spacer(Modifier.height(8.dp))
        h.credits.forEach {
            Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun VerseChips(h: Hymn, verse: Int, onVerse: (Int) -> Unit) {
    if (h.verses.size <= 1) return
    LazyRow(
        contentPadding = PaddingValues(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        itemsIndexed(h.verses) { k, _ ->
            FilterChip(selected = k == verse, onClick = { onVerse(k) }, label = { Text("Ayat ${h.verseLabel(k)}") })
        }
    }
    if (verse > 0 && verse !in h.readyVerses) {
        Text(
            "Lirik ayat ${h.verseLabel(verse)} belum dipasang ke not. Teksnya ada di tab Lirik.",
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun HymnPage(
    h: Hymn, view: Int, verse: Int, curSi: Int, scale: Float, onVerse: (Int) -> Unit,
    chords: Boolean = false, transpose: Int = 0,
) {
    val secs = remember(h, verse, chords) { Notation.build(h, verse, chords) }
    when (view) {
        0 -> LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 24.dp)) {
            item { HymnHeader(h) }
            itemsIndexed(h.verses) { k, lines ->
                val sel = k == verse && h.verses.size > 1
                Row(
                    Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 8.dp, vertical = 2.dp)
                        .clip(RoundedCornerShape(16.dp))
                        .background(if (sel) MaterialTheme.colorScheme.secondaryContainer.copy(alpha = .55f) else Color.Transparent)
                        .clickable { onVerse(k) }
                        .padding(horizontal = 8.dp, vertical = 10.dp),
                ) {
                    Text(
                        h.verseLabel(k),
                        modifier = Modifier.width(34.dp),
                        style = MaterialTheme.typography.titleMedium,
                        fontSize = (17 * scale).sp,
                        color = MaterialTheme.colorScheme.primary,
                        fontWeight = FontWeight.Bold,
                    )
                    Column {
                        lines.forEach {
                            Text(it, fontSize = (17 * scale).sp, lineHeight = (26 * scale).sp)
                        }
                    }
                }
            }
            item { Credits(h) }
        }

        else -> Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
            HymnHeader(h)
            VerseChips(h, verse, onVerse)
            Spacer(Modifier.height(4.dp))
            if (view == 1 || view == 3) {
                ScoreCard("Not angka") {
                    AngkaView(
                        secs, curSi, scale, h.book == Book.BN,
                        // akor ikut nada dasar (transposisi) supaya cocok dengan yang terdengar
                        chordTonic = if (chords) { sec -> Notation.tonicPc(sec.key ?: h.key) + transpose } else null,
                    )
                }
            }
            if (view == 2 || view == 3) {
                val abc = remember(secs, chords) { Notation.toAbc(h, secs, chords) }
                ScoreCard("Not balok") {
                    StaffView(abc, curSi, scale, Modifier.fillMaxWidth())
                }
            }
            Credits(h)
        }
    }
}
