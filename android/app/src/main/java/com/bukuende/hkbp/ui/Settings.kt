package com.bukuende.hkbp.ui

import android.content.Intent
import android.net.Uri
import android.os.Build
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.OpenInNew
import androidx.compose.material.icons.filled.DarkMode
import androidx.compose.material.icons.filled.FormatSize
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.LightMode
import androidx.compose.material.icons.filled.Palette
import androidx.compose.material.icons.automirrored.filled.PlaylistPlay
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.bukuende.hkbp.data.Book
import com.bukuende.hkbp.data.Hymn
import com.bukuende.hkbp.data.Prefs
import kotlin.math.roundToInt

@Composable
private fun Header(t: String) {
    Text(
        t,
        style = MaterialTheme.typography.labelLarge,
        color = MaterialTheme.colorScheme.primary,
        modifier = Modifier.padding(start = 16.dp, end = 16.dp, top = 20.dp, bottom = 4.dp),
    )
}

@Composable
fun Segments(options: List<String>, selected: Int, onSelect: (Int) -> Unit, modifier: Modifier = Modifier) {
    SingleChoiceSegmentedButtonRow(modifier) {
        options.forEachIndexed { i, label ->
            SegmentedButton(
                selected = selected == i,
                onClick = { onSelect(i) },
                shape = SegmentedButtonDefaults.itemShape(index = i, count = options.size),
            ) { Text(label, maxLines = 1) }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(lib: Map<Book, List<Hymn>>, prefs: Prefs) {
    val ctx = LocalContext.current
    val version = try {
        ctx.packageManager.getPackageInfo(ctx.packageName, 0).versionName ?: ""
    } catch (e: Exception) { "" }
    Scaffold(
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        topBar = { TopAppBar(title = { Text("Pengaturan") }) },
    ) { pad ->
        Column(Modifier.padding(pad).fillMaxSize().verticalScroll(rememberScrollState())) {
            Header("Tampilan")
            ListItem(
                leadingContent = { Icon(if (isDark(prefs)) Icons.Filled.DarkMode else Icons.Filled.LightMode, null) },
                headlineContent = { Text("Tema") },
                supportingContent = {
                    Segments(
                        listOf("Sistem", "Terang", "Gelap"), prefs.theme, { prefs.useTheme(it) },
                        Modifier.fillMaxWidth().padding(top = 8.dp),
                    )
                },
            )
            if (Build.VERSION.SDK_INT >= 31) {
                ListItem(
                    modifier = Modifier.clickable { prefs.setDynamic(!prefs.dynamicColor) },
                    leadingContent = { Icon(Icons.Filled.Palette, null) },
                    headlineContent = { Text("Warna dari wallpaper") },
                    supportingContent = { Text("Pakai warna Material You perangkat, bukan biru bawaan") },
                    trailingContent = { Switch(checked = prefs.dynamicColor, onCheckedChange = { prefs.setDynamic(it) }) },
                )
            }
            ListItem(
                leadingContent = { Icon(Icons.Filled.FormatSize, null) },
                headlineContent = { Text("Ukuran huruf lagu: ${(prefs.textScale * 100).roundToInt()}%") },
                supportingContent = {
                    Column {
                        Slider(
                            value = prefs.textScale,
                            onValueChange = { prefs.useTextScale((it * 20).roundToInt() / 20f) },
                            valueRange = 0.8f..1.8f,
                            steps = 19,
                        )
                        Text("Ringgas ma ho, tondingku", fontSize = (17 * prefs.textScale).sp)
                    }
                },
            )
            ListItem(
                leadingContent = { Icon(Icons.Filled.Visibility, null) },
                headlineContent = { Text("Tampilan awal lagu") },
                supportingContent = {
                    Segments(
                        VIEWS, prefs.defaultView, { prefs.useDefaultView(it) },
                        Modifier.fillMaxWidth().padding(top = 8.dp),
                    )
                },
            )

            Header("Pemutaran")
            ListItem(
                modifier = Modifier.clickable { prefs.setPlayAll(!prefs.playAllVerses) },
                leadingContent = { Icon(Icons.AutoMirrored.Filled.PlaylistPlay, null) },
                headlineContent = { Text("Putar semua ayat") },
                supportingContent = { Text("Setelah satu ayat selesai, lanjut ke ayat berikutnya") },
                trailingContent = { Switch(checked = prefs.playAllVerses, onCheckedChange = { prefs.setPlayAll(it) }) },
            )
            ListItem(
                modifier = Modifier.clickable { prefs.useKeepScreenOn(!prefs.keepScreenOn) },
                leadingContent = { Icon(Icons.Filled.LightMode, null) },
                headlineContent = { Text("Layar tetap menyala") },
                supportingContent = { Text("Selama halaman lagu terbuka, misalnya saat ibadah") },
                trailingContent = { Switch(checked = prefs.keepScreenOn, onCheckedChange = { prefs.useKeepScreenOn(it) }) },
            )

            Header("Data")
            ListItem(
                modifier = Modifier.clickable { prefs.clearHistory() },
                leadingContent = { Icon(Icons.Filled.History, null) },
                headlineContent = { Text("Hapus riwayat") },
                supportingContent = { Text("${prefs.history.size} lagu di daftar Terakhir dibuka") },
            )

            Header("Tentang")
            ListItem(
                leadingContent = { Icon(Icons.Filled.Info, null) },
                headlineContent = { Text("Buku Ende HKBP Digital $version") },
                supportingContent = {
                    Text(
                        "${lib[Book.BE]?.size ?: 0} lagu Buku Ende dan ${lib[Book.BN]?.size ?: 0} lagu Buku Nyanyian, " +
                            "lengkap dengan lirik semua ayat, not angka, not balok, dan nada. Semua tersimpan di dalam aplikasi, " +
                            "jadi bisa dibuka tanpa internet."
                    )
                },
            )
            ListItem(
                leadingContent = { Icon(Icons.Filled.Shield, null) },
                headlineContent = { Text("Privasi") },
                supportingContent = {
                    Text(
                        "Aplikasi ini tidak memiliki izin internet, tidak menampilkan iklan, dan tidak mengumpulkan data. " +
                            "Favorit, riwayat, dan pengaturan hanya disimpan di perangkat Anda."
                    )
                },
            )
            ListItem(
                modifier = Modifier.clickable {
                    try { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://bukuende.com/"))) } catch (e: Exception) { }
                },
                leadingContent = { Icon(Icons.AutoMirrored.Filled.OpenInNew, null) },
                headlineContent = { Text("bukuende.com") },
                supportingContent = { Text("Versi situs, bisa dibuka di peramban") },
            )
            HorizontalDivider(Modifier.padding(vertical = 8.dp))
        }
    }
}
