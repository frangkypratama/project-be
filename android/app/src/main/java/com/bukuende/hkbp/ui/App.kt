package com.bukuende.hkbp.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.MenuBook
import androidx.compose.material.icons.automirrored.filled.MenuBook
import androidx.compose.material.icons.filled.Bookmarks
import androidx.compose.material.icons.filled.LibraryMusic
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.outlined.Bookmarks
import androidx.compose.material.icons.outlined.LibraryMusic
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.saveable.rememberSaveableStateHolder
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import com.bukuende.hkbp.data.Book
import com.bukuende.hkbp.data.Hymn
import com.bukuende.hkbp.data.Library
import com.bukuende.hkbp.data.Prefs
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

private class Dest(val label: String, val on: ImageVector, val off: ImageVector)

private val DESTS = listOf(
    Dest("Buku Ende", Icons.AutoMirrored.Filled.MenuBook, Icons.AutoMirrored.Outlined.MenuBook),
    Dest("Buku Nyanyian", Icons.Filled.LibraryMusic, Icons.Outlined.LibraryMusic),
    Dest("Tersimpan", Icons.Filled.Bookmarks, Icons.Outlined.Bookmarks),
    Dest("Pengaturan", Icons.Filled.Settings, Icons.Outlined.Settings),
)

class Opened(val book: Book, val index: Int)

@Composable
fun App(prefs: Prefs) {
    val ctx = LocalContext.current
    var lib by remember { mutableStateOf(Library.loaded()) }
    LaunchedEffect(Unit) {
        if (lib == null) lib = withContext(Dispatchers.IO) { Library.load(ctx.applicationContext) }
    }
    BukuEndeTheme(prefs) {
        val l = lib
        if (l == null) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        } else {
            Main(l, prefs)
        }
    }
}

@Composable
private fun Main(lib: Map<Book, List<Hymn>>, prefs: Prefs) {
    var tab by rememberSaveable { mutableIntStateOf(0) }
    var opened by remember { mutableStateOf<Opened?>(null) }
    val holder = rememberSaveableStateHolder()
    val byKey = remember(lib) {
        val m = HashMap<String, Opened>()
        lib.forEach { (b, list) -> list.forEachIndexed { i, h -> m[h.key2] = Opened(b, i) } }
        m
    }
    val open: (Book, Int) -> Unit = { b, i -> opened = Opened(b, i) }

    val o = opened
    if (o != null) {
        BackHandler { opened = null }
        DetailScreen(lib.getValue(o.book), o.index, prefs, onBack = { opened = null })
        return
    }

    Scaffold(
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        bottomBar = {
            NavigationBar {
                DESTS.forEachIndexed { i, d ->
                    NavigationBarItem(
                        selected = tab == i,
                        onClick = { tab = i },
                        icon = { Icon(if (tab == i) d.on else d.off, contentDescription = null) },
                        label = { Text(d.label, style = MaterialTheme.typography.labelSmall) },
                    )
                }
            }
        },
    ) { pad ->
        Box(Modifier.padding(pad)) {
            holder.SaveableStateProvider("tab$tab") {
                when (tab) {
                    0 -> HymnListScreen(Book.BE, lib.getValue(Book.BE), prefs) { open(Book.BE, it) }
                    1 -> HymnListScreen(Book.BN, lib.getValue(Book.BN), prefs) { open(Book.BN, it) }
                    2 -> SavedScreen(lib, byKey, prefs) { o2 -> open(o2.book, o2.index) }
                    else -> SettingsScreen(lib, prefs)
                }
            }
        }
    }
}
