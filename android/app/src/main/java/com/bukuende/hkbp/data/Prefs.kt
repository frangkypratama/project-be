package com.bukuende.hkbp.data

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/** Pengaturan dan daftar pribadi, disimpan di perangkat (SharedPreferences). */
class Prefs(ctx: Context) {
    private val sp = ctx.getSharedPreferences("bukuende", Context.MODE_PRIVATE)

    /** 0 = ikuti sistem, 1 = terang, 2 = gelap */
    var theme by mutableIntStateOf(sp.getInt("theme", 0))
        private set
    var dynamicColor by mutableStateOf(sp.getBoolean("dynamic", false))
        private set
    var textScale by mutableFloatStateOf(sp.getFloat("textScale", 1f))
        private set
    /** 0 = lirik, 1 = not angka, 2 = not balok */
    var defaultView by mutableIntStateOf(sp.getInt("view", 1))
        private set
    var keepScreenOn by mutableStateOf(sp.getBoolean("screenOn", true))
        private set
    var playAllVerses by mutableStateOf(sp.getBoolean("allVerses", true))
        private set

    val favorites = mutableStateListOf<String>().apply {
        addAll(sp.getString("fav", "")!!.split('|').filter { it.isNotEmpty() })
    }
    val history = mutableStateListOf<String>().apply {
        addAll(sp.getString("hist", "")!!.split('|').filter { it.isNotEmpty() })
    }

    fun setTheme(v: Int) { theme = v; sp.edit().putInt("theme", v).apply() }
    fun setDynamic(v: Boolean) { dynamicColor = v; sp.edit().putBoolean("dynamic", v).apply() }
    fun setTextScale(v: Float) { textScale = v; sp.edit().putFloat("textScale", v).apply() }
    fun setDefaultView(v: Int) { defaultView = v; sp.edit().putInt("view", v).apply() }
    fun setKeepScreenOn(v: Boolean) { keepScreenOn = v; sp.edit().putBoolean("screenOn", v).apply() }
    fun setPlayAll(v: Boolean) { playAllVerses = v; sp.edit().putBoolean("allVerses", v).apply() }

    fun isFavorite(key: String) = key in favorites

    fun toggleFavorite(key: String) {
        if (!favorites.remove(key)) favorites.add(0, key)
        sp.edit().putString("fav", favorites.joinToString("|")).apply()
    }

    fun visit(key: String) {
        history.remove(key)
        history.add(0, key)
        while (history.size > 40) history.removeAt(history.size - 1)
        sp.edit().putString("hist", history.joinToString("|")).apply()
    }

    fun clearHistory() {
        history.clear()
        sp.edit().remove("hist").apply()
    }
}
