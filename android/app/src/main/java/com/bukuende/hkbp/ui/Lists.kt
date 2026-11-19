package com.bukuende.hkbp.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.DeleteSweep
import androidx.compose.material.icons.filled.Dialpad
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.StarOutline
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.bukuende.hkbp.data.Book
import com.bukuende.hkbp.data.Hymn
import com.bukuende.hkbp.data.Prefs

/** Hasil pencarian: nomor dicocokkan dulu, lalu judul, lalu isi lirik. */
fun searchHymns(hymns: List<Hymn>, query: String, cat: String?): List<Pair<Int, Hymn>> {
    val base = hymns.withIndex().filter { cat == null || it.value.category == cat }.map { it.index to it.value }
    val q = Hymn.normal(query).trim()
    if (q.isEmpty()) return base
    if (q.all { it.isDigit() || it == ' ' } || Regex("^\\d+[a-z]?$").matches(q)) {
        val qq = q.replace(" ", "")
        val exact = base.filter { it.second.id == qq }
        val starts = base.filter { it.second.id != qq && it.second.id.startsWith(qq) }
        return exact + starts
    }
    val words = q.split(' ').filter { it.isNotEmpty() }
    val hits = base.filter { p -> words.all { p.second.search.contains(it) } }
    val inTitle = hits.filter { p -> words.all { Hymn.normal(p.second.title).contains(it) } }
    return inTitle + hits.filter { it !in inTitle }
}

@Composable
fun NumberBadge(text: String, small: String? = null) {
    Box(
        Modifier.size(48.dp).clip(RoundedCornerShape(14.dp)).background(MaterialTheme.colorScheme.primaryContainer),
        contentAlignment = Alignment.Center,
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            if (small != null) {
                Text(small, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = .7f))
            }
            Text(
                text,
                style = if (text.length > 3) MaterialTheme.typography.titleSmall else MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
                maxLines = 1,
            )
        }
    }
}

@Composable
fun HymnRow(h: Hymn, fav: Boolean, showBook: Boolean = false, onClick: () -> Unit) {
    val sub = when {
        h.firstLine.isNotEmpty() && Hymn.normal(h.firstLine).trim() != Hymn.normal(h.title).trim() -> h.firstLine
        h.category != null -> h.category
        h.credits.isNotEmpty() -> h.credits.first()
        else -> null
    }
    ListItem(
        modifier = Modifier.clickable(onClick = onClick),
        leadingContent = { NumberBadge(h.id, if (showBook) h.book.short else null) },
        headlineContent = { Text(h.title, maxLines = 1, overflow = TextOverflow.Ellipsis, style = MaterialTheme.typography.titleMedium) },
        supportingContent = if (sub == null) null else {
            { Text(sub, maxLines = 1, overflow = TextOverflow.Ellipsis) }
        },
        trailingContent = if (!fav) null else {
            { Icon(Icons.Filled.Star, contentDescription = "Favorit", tint = MaterialTheme.colorScheme.primary) }
        },
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HymnListScreen(book: Book, hymns: List<Hymn>, prefs: Prefs, onOpen: (Int) -> Unit) {
    var query by rememberSaveable { mutableStateOf("") }
    var searching by rememberSaveable { mutableStateOf(false) }
    var cat by rememberSaveable { mutableStateOf<String?>(null) }
    var dial by remember { mutableStateOf(false) }
    val cats = remember(hymns) { hymns.mapNotNull { it.category }.distinct() }
    val shown = remember(query, cat, hymns) { searchHymns(hymns, query, cat) }
    val listState = rememberLazyListState()
    val focus = remember { FocusRequester() }
    val scroll = TopAppBarDefaults.pinnedScrollBehavior()

    LaunchedEffect(searching) { if (searching) focus.requestFocus() }
    // back saat mencari: tutup pencarian dulu, jangan pindah tab/keluar
    BackHandler(enabled = searching) { searching = false; query = "" }
    var lastFilter by rememberSaveable { mutableStateOf("$query|$cat") }
    LaunchedEffect(query, cat) {
        val f = "$query|$cat"
        if (f != lastFilter) { lastFilter = f; listState.scrollToItem(0) }
    }

    Scaffold(
        modifier = Modifier.nestedScroll(scroll.nestedScrollConnection),
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        topBar = {
            if (searching) {
                TopAppBar(
                    scrollBehavior = scroll,
                    navigationIcon = {
                        IconButton(onClick = { searching = false; query = "" }) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Tutup pencarian")
                        }
                    },
                    title = {
                        TextField(
                            value = query,
                            onValueChange = { query = it },
                            modifier = Modifier.fillMaxWidth().focusRequester(focus),
                            placeholder = { Text("Nomor, judul, atau lirik") },
                            singleLine = true,
                            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                            keyboardActions = KeyboardActions(onSearch = { shown.firstOrNull()?.let { onOpen(it.first) } }),
                            colors = TextFieldDefaults.colors(
                                focusedContainerColor = Color.Transparent,
                                unfocusedContainerColor = Color.Transparent,
                                focusedIndicatorColor = Color.Transparent,
                                unfocusedIndicatorColor = Color.Transparent,
                            ),
                        )
                    },
                    actions = {
                        if (query.isNotEmpty()) {
                            IconButton(onClick = { query = "" }) { Icon(Icons.Filled.Close, contentDescription = "Hapus") }
                        }
                    },
                )
            } else {
                TopAppBar(
                    scrollBehavior = scroll,
                    title = {
                        Column {
                            Text(book.label + " HKBP", style = MaterialTheme.typography.titleLarge)
                            Text(
                                "${hymns.size} lagu · lirik, not angka, not balok",
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    },
                    actions = {
                        IconButton(onClick = { searching = true }) { Icon(Icons.Filled.Search, contentDescription = "Cari") }
                    },
                )
            }
        },
        floatingActionButton = {
            if (!searching) {
                ExtendedFloatingActionButton(
                    onClick = { dial = true },
                    icon = { Icon(Icons.Filled.Dialpad, contentDescription = null) },
                    text = { Text("Nomor") },
                )
            }
        },
    ) { pad ->
        Column(Modifier.padding(pad).fillMaxSize()) {
            if (cats.isNotEmpty()) {
                LazyRow(
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    item { FilterChip(selected = cat == null, onClick = { cat = null }, label = { Text("Semua") }) }
                    items(cats) { c ->
                        FilterChip(selected = cat == c, onClick = { cat = if (cat == c) null else c }, label = { Text(c) })
                    }
                }
            }
            if (shown.isEmpty()) {
                Text(
                    "Tidak ada lagu yang cocok dengan “$query”.",
                    modifier = Modifier.fillMaxWidth().padding(32.dp),
                    textAlign = TextAlign.Center,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            LazyColumn(state = listState, contentPadding = PaddingValues(bottom = 96.dp)) {
                items(shown, key = { it.second.key2 }) { (i, h) ->
                    HymnRow(h, prefs.isFavorite(h.key2)) { onOpen(i) }
                }
            }
        }
    }

    if (dial) {
        NumberDialog(book, hymns, onDismiss = { dial = false }) { i -> dial = false; onOpen(i) }
    }
}

@Composable
fun NumberDialog(book: Book, hymns: List<Hymn>, onDismiss: () -> Unit, onGo: (Int) -> Unit) {
    var text by remember { mutableStateOf("") }
    var err by remember { mutableStateOf<String?>(null) }
    val focus = remember { FocusRequester() }
    LaunchedEffect(Unit) { focus.requestFocus() }
    fun go() {
        val t = text.trim().lowercase()
        val i = hymns.indexOfFirst { it.id == t }.takeIf { it >= 0 }
            ?: t.toIntOrNull()?.let { n -> hymns.indexOfFirst { it.number == n } }?.takeIf { it >= 0 }
        if (i == null) err = "${book.short} $t tidak ada (1–${hymns.maxOf { it.number }})" else onGo(i)
    }
    AlertDialog(
        onDismissRequest = onDismiss,
        icon = { Icon(Icons.Filled.Dialpad, contentDescription = null) },
        title = { Text("Buka ${book.label} nomor") },
        text = {
            OutlinedTextField(
                value = text,
                onValueChange = { v -> text = v.filter { it.isLetterOrDigit() }.take(4); err = null },
                modifier = Modifier.focusRequester(focus),
                singleLine = true,
                isError = err != null,
                supportingText = { Text(err ?: "Contoh: 784") },
                textStyle = MaterialTheme.typography.headlineMedium,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number, imeAction = ImeAction.Go),
                keyboardActions = KeyboardActions(onGo = { go() }),
            )
        },
        confirmButton = { TextButton(onClick = { go() }, enabled = text.isNotBlank()) { Text("Buka") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Batal") } },
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SavedScreen(lib: Map<Book, List<Hymn>>, byKey: Map<String, Opened>, prefs: Prefs, onOpen: (Opened) -> Unit) {
    var tab by rememberSaveable { mutableIntStateOf(0) }
    var confirm by remember { mutableStateOf(false) }
    val keys = if (tab == 0) prefs.favorites.toList() else prefs.history.toList()
    val rows = keys.mapNotNull { k -> byKey[k]?.let { o -> o to lib.getValue(o.book)[o.index] } }
    Scaffold(
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        topBar = {
            Column {
                TopAppBar(
                    title = { Text("Tersimpan") },
                    actions = {
                        if (tab == 1 && rows.isNotEmpty()) {
                            IconButton(onClick = { confirm = true }) { Icon(Icons.Filled.DeleteSweep, contentDescription = "Hapus riwayat") }
                        }
                    },
                )
                TabRow(selectedTabIndex = tab) {
                    Tab(selected = tab == 0, onClick = { tab = 0 }, text = { Text("Favorit") }, icon = { Icon(Icons.Filled.Star, null) })
                    Tab(selected = tab == 1, onClick = { tab = 1 }, text = { Text("Terakhir dibuka") }, icon = { Icon(Icons.Filled.History, null) })
                }
            }
        },
    ) { pad ->
        if (rows.isEmpty()) {
            Column(
                Modifier.padding(pad).fillMaxSize().padding(32.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Icon(
                    if (tab == 0) Icons.Outlined.StarOutline else Icons.Filled.History,
                    contentDescription = null,
                    modifier = Modifier.size(56.dp),
                    tint = MaterialTheme.colorScheme.outline,
                )
                Spacer(Modifier.height(12.dp))
                Text(
                    if (tab == 0) "Belum ada favorit.\nTekan ikon bintang di halaman lagu untuk menyimpannya di sini."
                    else "Belum ada lagu yang dibuka.",
                    textAlign = TextAlign.Center,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        } else {
            LazyColumn(Modifier.padding(pad), contentPadding = PaddingValues(bottom = 24.dp)) {
                items(rows, key = { it.second.key2 }) { (o, h) ->
                    HymnRow(h, tab == 1 && prefs.isFavorite(h.key2), showBook = true) { onOpen(o) }
                    HorizontalDivider(Modifier.padding(start = 80.dp), color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = .4f))
                }
            }
        }
    }
    if (confirm) {
        AlertDialog(
            onDismissRequest = { confirm = false },
            title = { Text("Hapus riwayat?") },
            text = { Text("Daftar lagu yang terakhir dibuka akan dikosongkan. Favorit tidak terhapus.") },
            confirmButton = { TextButton(onClick = { prefs.clearHistory(); confirm = false }) { Text("Hapus") } },
            dismissButton = { TextButton(onClick = { confirm = false }) { Text("Batal") } },
        )
    }
}
