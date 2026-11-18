package com.bukuende.hkbp.music

import com.bukuende.hkbp.data.Hymn
import kotlin.math.abs
import kotlin.math.roundToInt

/*
 * Pembaca not angka (port dari situs bukuende.com).
 * - spasi memisah ketukan; | garis birama; :| ulang; |] akhir; baris baru = ganti baris
 * - 1-7 nada, 0 diam, . tahan satu ketukan (atau setengah dalam kelompok +)
 * - ' sesudah angka = oktaf atas, , = oktaf bawah, # / b di depan = naik/turun setengah
 * - a+b = dua not dalam satu ketukan; ( ) = legato; v = tanda napas
 */

class Syl(val t: String, val cont: Boolean, val mel: Boolean = false)

class El(val raw: Char, var dur: Double, val slurStart: Boolean, val slurEnd: Boolean) {
    var hold = false
    var owner: El? = null
    var deg = 0
    var rest = false
    var oct = 0
    var acc = 0
    var inSlurCont = false
    var slurEndHere = false
    var breath = false
    var syl: Array<Syl?> = emptyArray()
    /** indeks not (tanpa tahanan) di seluruh lagu = urutan not di not balok */
    var si = -1
}

class Beat { val els = mutableListOf<El>(); var breath = false }
class Bar { val beats = mutableListOf<Beat>(); var end: String? = null }
class Line { val items = mutableListOf<Bar>() }

class Sec(val lines: List<Line>, val rows: List<String>, val src: String, val meter: String?, val key: String?)

class KeyInfo(val li: Int, val tonic: Int, val alt: IntArray, val shift: Int)

object Notation {
    private const val LETTERS = "CDEFGAB"
    private val NAT = intArrayOf(0, 2, 4, 5, 7, 9, 11)
    private val MAJ = NAT
    private val KEYS = mapOf(
        "C" to (0 to 0), "G" to (4 to 0), "D" to (1 to 0), "A" to (5 to 0), "E" to (2 to 0),
        "B" to (6 to 0), "F" to (3 to 0), "Bb" to (6 to -1), "Eb" to (2 to -1), "Ab" to (5 to -1),
        "Db" to (1 to -1), "Gb" to (4 to -1), "F#" to (3 to 1),
    )
    val DO_NAME = mapOf(
        "C" to "C", "G" to "G", "D" to "D", "A" to "A", "E" to "E", "B" to "B", "F" to "F",
        "Bb" to "Bes", "Eb" to "Es", "Ab" to "As", "Db" to "Des", "Gb" to "Ges", "F#" to "Fis",
    )
    private val TOK = Regex("""^(\()?([#b])?([0-7.])([',]*)(\))?$""")
    private val WS = Regex("\\s+")

    fun keyInfo(key: String?, shift: Int): KeyInfo {
        val k = KEYS[key] ?: KEYS.getValue("C")
        val li = k.first
        val tonic = 60 + NAT[li] + k.second + 12 * shift
        val alt = IntArray(7)
        for (d in 0..6) {
            val l = (li + d) % 7
            val oc = (li + d) / 7
            alt[l] = tonic + MAJ[d] - (60 + 12 * (oc + shift) + NAT[l])
        }
        return KeyInfo(li, tonic, alt, shift)
    }

    fun midiOf(e: El, ki: KeyInfo): Int = ki.tonic + MAJ[e.deg - 1] + 12 * e.oct + e.acc

    private fun abcOf(e: El, ki: KeyInfo): String {
        val d = e.deg - 1
        val l = (ki.li + d) % 7
        val carry = (ki.li + d) / 7
        val midi = midiOf(e, ki)
        val octave = 4 + carry + e.oct + ki.shift
        val natural = 12 * (octave + 1) + NAT[l]
        val a = midi - natural
        val sym = if (a == ki.alt[l]) "" else when (a) { 0 -> "="; 1 -> "^"; -1 -> "_"; 2 -> "^^"; else -> "__" }
        var name = LETTERS[l].toString()
        if (octave >= 5) name = name.lowercase() + "'".repeat(octave - 5)
        else if (octave < 4) name += ",".repeat(4 - octave)
        return sym + name
    }

    fun parseNotes(src: String): List<Line> {
        val lines = mutableListOf<Line>()
        var slurOpen = false
        var last: El? = null
        for (lineSrc in src.split("\n")) {
            val line = Line()
            lines.add(line)
            var bar = Bar()
            line.items.add(bar)
            for (tok in lineSrc.trim().split(WS)) {
                if (tok.isEmpty()) continue
                if (tok == "|" || tok == ":|" || tok == "|]") {
                    bar.end = tok
                    bar = Bar()
                    line.items.add(bar)
                    continue
                }
                if (tok == "v") {
                    bar.beats.lastOrNull()?.breath = true
                    last?.breath = true
                    continue
                }
                val parts = tok.split("+")
                val beat = Beat()
                val unit = 1.0 / parts.size
                for (p in parts) {
                    val g = TOK.find(p)?.groupValues ?: throw IllegalArgumentException("Tidak dikenali: $p")
                    val el = El(g[3][0], unit, g[1].isNotEmpty(), g[5].isNotEmpty())
                    if (g[3] == ".") {
                        el.hold = true
                        last?.let { it.dur += unit }
                        el.owner = last
                    } else {
                        el.deg = g[3].toInt()
                        el.rest = el.deg == 0
                        el.oct = g[4].count { it == '\'' } - g[4].count { it == ',' }
                        el.acc = when (g[2]) { "#" -> 1; "b" -> -1; else -> 0 }
                        if (el.slurStart) slurOpen = true
                        el.inSlurCont = slurOpen && !el.slurStart && !el.rest
                        last = el
                    }
                    if (el.slurEnd) {
                        slurOpen = false
                        if (el.hold) el.owner?.slurEndHere = true
                    }
                    beat.els.add(el)
                }
                bar.beats.add(beat)
            }
            line.items.removeAll { it.beats.isEmpty() && it.end == null }
        }
        return lines
    }

    fun noteEls(lines: List<Line>): List<El> =
        lines.flatMap { l -> l.items.flatMap { b -> b.beats.flatMap { bt -> bt.els.filter { !it.hold } } } }

    private fun syllables(row: String): List<Syl> {
        val out = mutableListOf<Syl>()
        for (w in row.trim().split(WS)) {
            if (w.isEmpty()) continue
            if (w == "_") { out.add(Syl("", false, true)); continue }
            val s = w.split("-")
            s.forEachIndexed { i, x -> out.add(Syl(x, i < s.size - 1)) }
        }
        return out
    }

    private fun assignLyrics(lines: List<Line>, rows: List<String>) {
        val all = noteEls(lines)
        all.forEach { it.syl = arrayOfNulls<Syl>(rows.size) }
        val targets = all.filter { !it.rest && !it.inSlurCont }
        rows.forEachIndexed { ri, r ->
            val syl = syllables(r)
            targets.forEachIndexed { i, e -> e.syl[ri] = syl.getOrNull(i) }
        }
    }

    /** Bagian-bagian lagu dengan lirik ayat ke-[verse] terpasang pada not. */
    fun build(h: Hymn, verse: Int): List<Sec> {
        var gi = 0
        return h.sections.mapIndexed { si, s ->
            val lines = try { parseNotes(s.notes) } catch (e: Exception) { emptyList() }
            val rows = h.rowsFor(verse, si)
            assignLyrics(lines, rows)
            noteEls(lines).forEach { it.si = gi++ }
            Sec(lines, rows, s.notes, s.meter, s.key)
        }
    }

    fun unitOf(meter: String?): Double {
        val d = meter?.split("/")?.getOrNull(1)?.trim()?.toIntOrNull() ?: 4
        return 4.0 / d
    }

    private fun durStr(beats: Double): String {
        val e = (beats * 4).roundToInt()
        return if (e == 1) "" else e.toString()
    }

    fun toAbc(h: Hymn, secs: List<Sec>): String {
        var ki = keyInfo(h.key, h.oct)
        var curM = secs.firstOrNull()?.meter ?: h.meter
        var curK = h.key
        val out = mutableListOf("X:1", "M:$curM", "L:1/16", "K:${h.key}")
        for (sec in secs) {
            val sm = sec.meter ?: h.meter
            val u = unitOf(sm)
            var pre = ""
            if (sm != curM) { pre = "[M:$sm] "; curM = sm }
            val sk = sec.key ?: h.key
            if (sk != curK) { pre += "[K:$sk] "; curK = sk; ki = keyInfo(sk, h.oct) }
            val mus = mutableListOf<String>()
            val lyr = sec.rows.map { mutableListOf<String>() }
            for (line in sec.lines) for (bar in line.items) {
                for (beat in bar.beats) {
                    val tri = beat.els.size == 3 && beat.els.all { abs(it.dur * 3 - 1) < 1e-6 }
                    val chunk = StringBuilder(if (tri) "(3" else "")
                    for (e in beat.els) {
                        if (e.hold) continue
                        if (e.breath) chunk.append("!breath!")
                        if (e.slurStart) chunk.append("(")
                        chunk.append(if (e.rest) "z" else abcOf(e, ki))
                        chunk.append(durStr(e.dur * u * (if (tri) 1.5 else 1.0)))
                        if (e.slurEnd || e.slurEndHere) chunk.append(")")
                        if (!e.rest) {
                            lyr.forEachIndexed { ri, l ->
                                if (e.inSlurCont) { l.add("_"); return@forEachIndexed }
                                val sy = e.syl.getOrNull(ri)
                                l.add(
                                    when {
                                        sy == null -> "*"
                                        sy.mel -> "_"
                                        else -> sy.t.replace("-", "") + (if (sy.cont) "-" else "")
                                    }
                                )
                            }
                        }
                    }
                    if (chunk.isNotEmpty()) mus.add(chunk.toString())
                }
                bar.end?.let { mus.add(it) }
            }
            out.add(pre + mus.joinToString(" "))
            lyr.forEach { l ->
                out.add("w: " + l.joinToString("") { if (it.endsWith("-")) it else "$it " }.trimEnd())
            }
        }
        return out.joinToString("\n")
    }

    /** Satu bunyi (atau diam) dalam urutan pemutaran. */
    class Tone(val midi: Int, val beats: Double, val si: Int, val breath: Boolean, val verse: Int)

    /**
     * Urutan pemutaran: satu putaran per ayat, dimulai dari [fromVerse];
     * bila [all] maka lanjut ke ayat berikut yang liriknya sudah terpasang.
     */
    fun sequence(h: Hymn, fromVerse: Int, all: Boolean): List<Tone> {
        val one = mutableListOf<Pair<El, Pair<Double, KeyInfo>>>()
        var gi = 0
        for (s in h.sections) {
            val lines = try { parseNotes(s.notes) } catch (e: Exception) { emptyList() }
            val notes = noteEls(lines)
            notes.forEachIndexed { i, e -> e.si = gi + i }
            gi += notes.size
            val reps = if (s.notes.contains(":|")) 2 else 1
            val uu = unitOf(s.meter ?: h.meter)
            val kk = keyInfo(s.key ?: h.key, h.oct)
            repeat(reps) { notes.forEach { one.add(it to (uu to kk)) } }
        }
        val verses = if (all) h.readyVerses.filter { it >= fromVerse }.ifEmpty { listOf(fromVerse) } else listOf(fromVerse)
        val list = if (verses.first() != fromVerse) listOf(fromVerse) + verses else verses
        val seq = mutableListOf<Tone>()
        for (v in list) for ((e, uk) in one) {
            seq.add(Tone(if (e.rest) -1 else midiOf(e, uk.second), e.dur * uk.first, e.si, e.breath, v))
        }
        return seq
    }
}
