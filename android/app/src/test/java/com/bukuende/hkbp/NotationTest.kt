package com.bukuende.hkbp

import com.bukuende.hkbp.data.Book
import com.bukuende.hkbp.data.Library
import com.bukuende.hkbp.music.Notation
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.security.MessageDigest

/**
 * Pengolah not versi Kotlin harus menghasilkan not balok (ABC) yang sama persis
 * dengan kode situs bukuende.com, untuk semua lagu dan semua ayat yang terpasang ke not.
 * Acuan (sidik SHA-256) dibuat dari kode situs: src/test/resources/abc_expected.txt
 */
class NotationTest {
    private fun sha(s: String): String =
        MessageDigest.getInstance("SHA-256").digest(s.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }

    @Test
    fun abcSamaDenganSitus() {
        val expected = javaClass.classLoader!!.getResourceAsStream("abc_expected.txt")!!.bufferedReader().readLines()
            .filter { it.isNotBlank() }.associate { l -> l.substringBefore(' ') to l.substringAfter(' ') }
        val got = HashMap<String, String>()
        val sample = HashMap<String, String>()
        for (b in Book.entries) {
            val hymns = Library.parse(b, File("src/main/assets/${b.file}").readText())
            for (h in hymns) for (k in h.readyVerses) {
                val abc = try { Notation.toAbc(h, Notation.build(h, k)) } catch (e: Exception) { "ERR" }
                val key = "${b.code}:${h.id}:$k"
                got[key] = sha(abc)
                sample[key] = abc
            }
        }
        val bad = expected.keys.filter { got[it] != expected[it] }
        val extra = got.keys - expected.keys
        if (bad.isNotEmpty()) {
            println("BEDA ${bad.size} dari ${expected.size}: ${bad.take(30)}")
            bad.take(3).forEach { println("---- $it\n${sample[it]}") }
        }
        assertTrue("tidak ada data", expected.size > 7000)
        assertEquals("ABC berbeda dari situs: ${bad.take(20)} (dan ${(bad.size - 20).coerceAtLeast(0)} lainnya)", 0, bad.size)
        assertEquals("ayat tambahan: ${extra.take(20)}", 0, extra.size)
    }

    @Test
    fun urutanNada() {
        val h = Library.parse(Book.BE, File("src/main/assets/be.json").readText()).first { it.id == "784" }
        val seq = Notation.sequence(h, 0, false)
        assertTrue(seq.isNotEmpty())
        // Do = Bes, oktaf -1: nada pertama yang berbunyi adalah 3' (D5) = MIDI 74
        assertEquals(74, seq.first { it.midi >= 0 }.midi)
        val all = Notation.sequence(h, 0, true)
        assertEquals(seq.size * h.readyVerses.size, all.size)
    }

    @Test
    fun akorTerpasang() {
        var lagu = 0
        var bagianBerakor = 0
        for (b in Book.entries) {
            val hymns = Library.parse(b, File("src/main/assets/${b.file}").readText())
            for (h in hymns) {
                lagu++
                val secs = Notation.build(h, 0, chords = true)
                h.sections.forEachIndexed { si, s ->
                    if (s.chords != null) {
                        bagianBerakor++
                        // akor pertama setiap bagian harus ada dan terpasang
                        val first = secs[si].lines.flatMap { l -> l.items.flatMap { it.beats } }.firstOrNull()?.chord
                        assertTrue("${b.code}:${h.id} bagian $si tanpa akor awal", first != null)
                    }
                }
                Notation.toAbc(h, secs, chords = true)
                Notation.sequence(h, 0, true, chords = true)
            }
        }
        assertTrue("akor kurang: $bagianBerakor", bagianBerakor > lagu)
        // tanpa akor: keluaran tidak berubah (acuan situs diuji di abcSamaDenganSitus)
        val h = Library.parse(Book.BE, File("src/main/assets/be.json").readText()).first { it.id == "559" }
        val abc = Notation.toAbc(h, Notation.build(h, 0, chords = true), chords = true)
        assertTrue(abc.lines()[4], abc.lines()[4].startsWith("\"D\"D4 D4 F4 F4 | \"D\"A8 \"A\"A8 | \"Bm\"(B4"))
        val seq = Notation.sequence(h, 0, false, chords = true)
        assertEquals(29, seq.sumOf { it.chordAt.size })
    }
}
