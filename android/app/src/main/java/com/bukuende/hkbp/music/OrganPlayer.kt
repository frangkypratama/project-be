package com.bukuende.hkbp.music

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.os.Handler
import android.os.Looper
import kotlin.math.PI
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.roundToInt
import kotlin.math.sin
import kotlin.math.tanh

/**
 * Organ pipa sintetis (Principal 8' + Octave 4' + Quint + Superoctave) dengan gema gereja,
 * dibuat langsung di perangkat lewat AudioTrack. Tempo dan transposisi dibaca setiap not,
 * jadi perubahan langsung terdengar tanpa menghentikan pemutaran.
 */
class OrganPlayer {
    interface Listener {
        fun onNote(si: Int, verse: Int)
        fun onEnd()
    }

    @Volatile var bpm: Int = 84
    @Volatile var transpose: Int = 0

    private val sr = 32000
    private val table = FloatArray(4096)
    private val gen = java.util.concurrent.atomic.AtomicInteger(0)
    @Volatile private var active = -1
    private val main = Handler(Looper.getMainLooper())

    init {
        val amp = floatArrayOf(1f, .62f, .34f, .42f, .1f, .16f, .04f, .2f, .03f, .05f, 0f, .06f)
        var peak = 0f
        for (i in table.indices) {
            var v = 0.0
            for (h in amp.indices) v += amp[h] * sin(2 * PI * (h + 1) * i / table.size)
            table[i] = v.toFloat()
            peak = max(peak, kotlin.math.abs(table[i]))
        }
        for (i in table.indices) table[i] /= peak
    }

    val isPlaying: Boolean get() = active == gen.get()

    fun stop() {
        gen.incrementAndGet()
    }

    fun play(seq: List<Notation.Tone>, listener: Listener) {
        val my = gen.incrementAndGet()
        if (seq.isEmpty()) return
        active = my
        Thread({ run(my, seq, listener) }, "organ").start()
    }

    private class Mark(val frame: Long, val si: Int, val verse: Int)

    private fun run(my: Int, seq: List<Notation.Tone>, listener: Listener) {
        fun running() = gen.get() == my
        val minBuf = AudioTrack.getMinBufferSize(sr, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT)
        val track = try {
            AudioTrack.Builder()
                .setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                        .build()
                )
                .setAudioFormat(
                    AudioFormat.Builder()
                        .setSampleRate(sr)
                        .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                        .build()
                )
                .setBufferSizeInBytes(max(minBuf, sr / 5 * 2))
                .setTransferMode(AudioTrack.MODE_STREAM)
                .build()
        } catch (e: Exception) {
            main.post { if (running()) { gen.incrementAndGet(); active = -1; listener.onEnd() } }
            return
        }

        val marks = ArrayList<Mark>()
        val reverb = Reverb(sr)
        var written = 0L
        var lastShown = -2
        track.play()

        // pemantau posisi: menyorot not yang sedang berbunyi
        val poll = object : Runnable {
            override fun run() {
                if (!running()) return
                val head = try { track.playbackHeadPosition.toLong() and 0xffffffffL } catch (e: Exception) { 0L }
                var m: Mark? = null
                synchronized(marks) {
                    for (x in marks) { if (x.frame <= head) m = x else break }
                }
                val cur = m
                if (cur != null && cur.si != lastShown) {
                    lastShown = cur.si
                    listener.onNote(cur.si, cur.verse)
                }
                main.postDelayed(this, 30)
            }
        }
        main.post(poll)

        fun out(buf: FloatArray, n: Int): Boolean {
            val pcm = ShortArray(n)
            for (i in 0 until n) {
                val y = reverb.process(buf[i])
                pcm[i] = (tanh(y.toDouble()) * 30000).roundToInt().toShort()
            }
            var off = 0
            while (off < n) {
                if (!running()) return false
                val w = track.write(pcm, off, n - off, AudioTrack.WRITE_NON_BLOCKING)
                if (w < 0) return false
                if (w == 0) Thread.sleep(8) else off += w
            }
            written += n
            return true
        }

        val rel = (sr * 0.07).toInt()
        val att = (sr * 0.035).toInt()
        var carry = FloatArray(0)
        var ok = true
        var lp = 0f
        val lpA = (1 - kotlin.math.exp(-2 * PI * 4200 / sr)).toFloat()

        for (idx in seq.indices) {
            if (!running()) { ok = false; break }
            val e = seq[idx]
            val d = e.beats * 60.0 / bpm
            val n = max(1, (d * sr).roundToInt())
            synchronized(marks) { marks.add(Mark(written, e.si, e.verse)) }
            val buf = FloatArray(n + rel + 1)
            if (e.midi >= 0) {
                val midi = e.midi + transpose
                val nx = seq.getOrNull(idx + 1)
                val gap = when {
                    e.breath -> min(.18, d * .25)
                    nx == null || nx.midi < 0 || nx.midi == e.midi -> .06
                    else -> .012
                }
                val gate = max(1, ((max(.05, d - gap)) * sr).roundToInt())
                val f = 440.0 * 2.0.pow((midi - 69) / 12.0)
                val inc1 = f * table.size / sr
                val inc2 = f * 1.0016 * table.size / sr
                var p1 = 0.0
                var p2 = table.size * 0.25
                val total = gate + rel
                for (i in 0 until min(total, buf.size)) {
                    val env = when {
                        i < att -> i.toFloat() / att
                        i < gate -> 1f
                        else -> 1f - (i - gate).toFloat() / rel
                    }
                    val s = table[p1.toInt() and 4095] * .7f + table[p2.toInt() and 4095] * .45f
                    buf[i] = s * env * 0.28f
                    p1 += inc1; if (p1 >= 4096) p1 -= 4096
                    p2 += inc2; if (p2 >= 4096) p2 -= 4096
                }
            }
            for (i in carry.indices) if (i < buf.size) buf[i] += carry[i]
            for (i in 0 until n) { lp += lpA * (buf[i] - lp); buf[i] = lp }
            carry = buf.copyOfRange(n, buf.size)
            if (!out(buf, n)) { ok = false; break }
        }

        if (ok && running()) {
            // ekor gema
            val tail = FloatArray(sr * 2)
            for (i in carry.indices) if (i < tail.size) tail[i] = carry[i]
            synchronized(marks) { marks.add(Mark(written, -1, -1)) }
            out(tail, tail.size)
            val end = written
            while (running()) {
                val head = try { track.playbackHeadPosition.toLong() and 0xffffffffL } catch (e: Exception) { end }
                if (head >= end - sr / 10) break
                Thread.sleep(30)
            }
        }
        try { track.pause(); track.flush(); track.release() } catch (e: Exception) { }
        main.post {
            if (running()) {
                gen.incrementAndGet()
                active = -1
                listener.onNote(-1, -1)
                listener.onEnd()
            }
        }
    }

    /** Gema ruang gereja sederhana (Schroeder: 4 comb + 2 allpass). */
    private class Reverb(sr: Int) {
        private val combs = intArrayOf(1557, 1617, 1491, 1422).map { (it * sr / 44100.0 * 1.6).toInt() }.map { FloatArray(it) }
        private val ci = IntArray(4)
        private val cf = FloatArray(4)
        private val aps = intArrayOf(225, 556).map { (it * sr / 44100.0).toInt() }.map { FloatArray(it) }
        private val ai = IntArray(2)

        fun process(x: Float): Float {
            var wet = 0f
            for (k in 0 until 4) {
                val b = combs[k]
                val y = b[ci[k]]
                cf[k] = y * 0.6f + cf[k] * 0.4f
                b[ci[k]] = x + cf[k] * 0.83f
                ci[k] = (ci[k] + 1) % b.size
                wet += y
            }
            wet *= 0.25f
            for (k in 0 until 2) {
                val b = aps[k]
                val bv = b[ai[k]]
                val y = -wet + bv
                b[ai[k]] = wet + bv * 0.5f
                ai[k] = (ai[k] + 1) % b.size
                wet = y
            }
            return x * 0.85f + wet * 0.45f
        }
    }
}
