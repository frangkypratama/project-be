package com.bukuende.hkbp.data

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.text.Normalizer

enum class Book(val code: String, val label: String, val short: String, val file: String, val site: String) {
    BE("be", "Buku Ende", "BE", "be.json", "https://bukuende.com/be/"),
    BN("bn", "Buku Nyanyian", "BN", "bn.json", "https://bukuende.com/bn/");
}

class Section(val notes: String, val rows: List<String>, val meter: String?, val key: String?)

class Hymn(
    val book: Book,
    val id: String,
    val title: String,
    val key: String,
    val oct: Int,
    val meter: String,
    val tempo: Int?,
    val logu: Int?,
    val category: String?,
    val credits: List<String>,
    val sections: List<Section>,
    val verses: List<List<String>>,
    val verseNumbers: List<Int>,
    /** baris lirik per bagian untuk ayat ke-k (indeks 0 = ayat 1 memakai Section.rows); null = belum terpasang ke not */
    val verseRows: List<List<List<String>>?>,
) {
    val number: Int = id.takeWhile { it.isDigit() }.toIntOrNull() ?: 0
    val ref: String get() = "${book.short} $id"
    val key2: String get() = "${book.code}:$id"
    val firstLine: String = verses.firstOrNull()?.firstOrNull()?.trim()?.trimEnd(',', '.', ';', ':') ?: ""
    val search: String = normal(buildString {
        append(id).append(' ').append(title).append(' ')
        verses.forEach { v -> v.forEach { append(it).append(' ') } }
    })

    /** Nomor ayat sebagaimana tercetak (BN memakai vnum). */
    fun verseLabel(k: Int): String = (verseNumbers.getOrNull(k) ?: (k + 1)).toString()

    /** Ayat yang liriknya sudah terpasang ke not (ayat 1 selalu). */
    val readyVerses: List<Int> = buildList {
        add(0)
        verseRows.forEachIndexed { i, r -> if (i > 0 && r != null) add(i) }
    }

    fun rowsFor(k: Int, si: Int): List<String> {
        if (k == 0) return sections[si].rows
        val r = verseRows.getOrNull(k) ?: return sections[si].rows.map { "" }
        return r.getOrNull(si) ?: sections[si].rows.map { "" }
    }

    companion object {
        fun normal(s: String): String =
            Normalizer.normalize(s.lowercase(), Normalizer.Form.NFD)
                .replace(Regex("\\p{M}+"), "")
                .replace(Regex("[^a-z0-9 ]"), " ")
                .replace(Regex("\\s+"), " ")
    }
}

object Library {
    @Volatile private var cache: Map<Book, List<Hymn>>? = null

    fun loaded(): Map<Book, List<Hymn>>? = cache

    fun load(ctx: Context): Map<Book, List<Hymn>> {
        cache?.let { return it }
        val m = Book.entries.associateWith { read(ctx, it) }
        cache = m
        return m
    }

    private fun strings(a: JSONArray?): List<String> =
        if (a == null) emptyList() else List(a.length()) { a.optString(it) }

    private fun read(ctx: Context, b: Book): List<Hymn> {
        val txt = ctx.assets.open(b.file).bufferedReader(Charsets.UTF_8).use { it.readText() }
        val items = JSONObject(txt).getJSONArray("items")
        return List(items.length()) { i ->
            val o = items.getJSONObject(i)
            val secs = o.getJSONArray("s")
            val sections = List(secs.length()) { j ->
                val s = secs.getJSONObject(j)
                Section(
                    s.getString("n"),
                    strings(s.optJSONArray("r")),
                    s.optString("m").ifEmpty { null },
                    s.optString("k").ifEmpty { null },
                )
            }
            val va = o.optJSONArray("v")
            val verses = if (va == null) emptyList() else List(va.length()) { strings(va.optJSONArray(it)) }
            val vla = o.optJSONArray("vl")
            val vl: List<List<List<String>>?> = if (vla == null) emptyList() else List(vla.length()) { k ->
                val x = vla.optJSONArray(k)
                if (x == null) null else List(x.length()) { si -> strings(x.optJSONArray(si)) }
            }
            val vn = o.optJSONArray("vn")
            Hymn(
                book = b,
                id = o.getString("id"),
                title = o.getString("t"),
                key = o.optString("k", "C"),
                oct = o.optInt("o", 0),
                meter = o.optString("m", "4/4"),
                tempo = if (o.has("tp")) o.optInt("tp") else null,
                logu = if (o.has("bl")) o.optInt("bl") else null,
                category = o.optString("c").ifEmpty { null },
                credits = strings(o.optJSONArray("cr")),
                sections = sections,
                verses = verses,
                verseNumbers = if (vn == null) emptyList() else List(vn.length()) { vn.optInt(it) },
                verseRows = vl,
            )
        }
    }
}
