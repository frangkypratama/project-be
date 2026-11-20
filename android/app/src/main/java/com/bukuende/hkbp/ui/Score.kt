package com.bukuende.hkbp.ui

import android.annotation.SuppressLint
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.print.PrintAttributes
import android.print.PrintManager
import android.view.MotionEvent
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.layout.layout
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import com.bukuende.hkbp.data.Book
import com.bukuende.hkbp.data.Hymn
import com.bukuende.hkbp.music.Bar
import com.bukuende.hkbp.music.Beat
import com.bukuende.hkbp.music.El
import com.bukuende.hkbp.music.Notation
import com.bukuende.hkbp.music.Sec
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.abs

/* ---------------- Not angka, digambar native ---------------- */

/** Garis atas per ketukan, sama dengan situs: 2+ not = 1 garis; lebih dari 2 (BE) / 3 (BN) not = 2 garis. */
private fun lineCount(beat: Beat, bn: Boolean): Int = when {
    beat.els.size <= 1 -> 0
    beat.els.size > (if (bn) 3 else 2) -> 2
    else -> 1
}

private fun digitText(e: El) = if (e.hold) "·" else e.deg.toString()

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AngkaView(
    secs: List<Sec>, curSi: Int, scale: Float, bn: Boolean, modifier: Modifier = Modifier,
    /** null = akor tidak ditampilkan; selain itu Do (0..11) untuk menamai akor bagian tsb. */
    chordTonic: ((Sec) -> Int)? = null,
) {
    val ink = MaterialTheme.colorScheme.onSurface
    val hl = MaterialTheme.colorScheme.tertiaryContainer
    val digit = (21 * scale).sp
    val sylSize = (13.5f * scale).sp
    val digitDp = with(LocalDensity.current) { digit.toDp() }
    val barH = digitDp * 1.25f + 22.dp
    Column(modifier, verticalArrangement = Arrangement.spacedBy(18.dp)) {
        secs.forEach { sec ->
            FlowRow(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                for (line in sec.lines) for (bar in line.items) {
                    BarView(bar, sec.rows.size, curSi, ink, hl, digit, sylSize, barH, bn, chordTonic?.invoke(sec), scale)
                }
            }
        }
    }
}

private fun Modifier.overlines(n: Int, ink: Color): Modifier = if (n <= 0) this else drawBehind {
    val sw = 1.3.dp.toPx()
    for (k in 0 until n) {
        val y = (2 + 4 * k).dp.toPx()
        drawLine(ink, Offset(3.dp.toPx(), y), Offset(size.width - 3.dp.toPx(), y), sw)
    }
}

@Composable
private fun BarView(
    bar: Bar, rows: Int, curSi: Int, ink: Color, hl: Color,
    digit: androidx.compose.ui.unit.TextUnit, syl: androidx.compose.ui.unit.TextUnit, barH: androidx.compose.ui.unit.Dp,
    bn: Boolean,
    tonic: Int? = null,
    scale: Float = 1f,
) {
    val chH = if (tonic != null) (18 * scale).dp else 0.dp
    val chColor = MaterialTheme.colorScheme.primary
    Row(verticalAlignment = Alignment.Top) {
        bar.beats.forEach { beat ->
          Column {
            if (tonic != null) {
                Box(Modifier.height(chH)) {
                    val c = beat.chord
                    if (c != null) {
                        Text(
                            Notation.chordName(c, tonic),
                            color = chColor,
                            fontWeight = FontWeight.Bold,
                            fontSize = (13.5f * scale).sp,
                            maxLines = 1,
                            softWrap = false,
                            // lebar 0: nama akor boleh melewati lebar ketukan tanpa melebarkan not
                            modifier = Modifier.padding(start = 3.dp).layout { m, cs ->
                                val p = m.measure(cs.copy(minWidth = 0, maxWidth = Constraints.Infinity))
                                layout(0, p.height) { p.placeRelative(0, 0) }
                            },
                        )
                    }
                }
            }
            if (beat.exp) {
                // durasi eksplisit (BN): garis atas per not
                Row {
                    beat.els.forEach { e ->
                        Box(Modifier.overlines(minOf(e.lv, 2), ink).padding(top = 12.dp)) {
                            ElView(e, rows, !e.hold && e.si == curSi, ink, hl, digit, syl)
                        }
                    }
                }
            } else {
                Row(Modifier.overlines(lineCount(beat, bn), ink).padding(top = 12.dp)) {
                    beat.els.forEach { e -> ElView(e, rows, !e.hold && e.si == curSi, ink, hl, digit, syl) }
                }
            }
          }
            if (beat.breath) Text("’", fontSize = digit, color = ink, modifier = Modifier.padding(top = 10.dp + chH))
        }
        val end = bar.end
        if (end != null) {
            Row(Modifier.padding(start = 4.dp, end = 6.dp, top = 12.dp + chH), verticalAlignment = Alignment.CenterVertically) {
                if (end == ":|") Text(":", fontSize = digit, color = ink, fontWeight = FontWeight.Bold)
                Box(Modifier.width(1.2.dp).height(barH - 12.dp).background(ink))
                if (end != "|") {
                    Spacer(Modifier.width(2.dp))
                    Box(Modifier.width(3.5.dp).height(barH - 12.dp).background(ink))
                }
            }
        }
    }
}

@Composable
private fun ElView(
    e: El, rows: Int, lit: Boolean, ink: Color, hl: Color,
    digit: androidx.compose.ui.unit.TextUnit, syl: androidx.compose.ui.unit.TextUnit,
) {
    val dot = 8.sp
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier
            .widthIn(min = 18.dp)
            .background(if (lit) hl else Color.Transparent, RoundedCornerShape(6.dp))
            .padding(horizontal = 3.dp),
    ) {
        Text(if (e.oct > 0) "•".repeat(e.oct) else " ", fontSize = dot, lineHeight = dot, color = ink)
        Text(
            digitText(e),
            fontSize = digit,
            lineHeight = digit,
            fontWeight = if (e.hold) FontWeight.Bold else FontWeight.Medium,
            color = ink,
            modifier = Modifier.drawWithContent {
                drawContent()
                if (!e.hold && e.acc != 0) {
                    val w = size.width
                    val h = size.height
                    val a = if (e.acc > 0) Offset(w * .15f, h * .85f) else Offset(w * .15f, h * .15f)
                    val b = if (e.acc > 0) Offset(w * .85f, h * .15f) else Offset(w * .85f, h * .85f)
                    drawLine(ink, a, b, 1.5.dp.toPx())
                }
            },
        )
        Text(if (e.oct < 0) "•".repeat(-e.oct) else " ", fontSize = dot, lineHeight = dot, color = ink)
        for (r in 0 until rows) {
            val s = e.syl.getOrNull(r)
            Text(
                if (s == null) " " else s.t + if (s.cont) " -" else "",
                fontSize = syl,
                color = if (r == 0) ink else ink.copy(alpha = .75f),
                maxLines = 1,
                softWrap = false,
            )
        }
    }
}

/* ---------------- Not balok (abcjs, luring) ---------------- */

private class StaffState {
    var ready = false
    var abc = ""
    var ink = ""
    var hl = ""
    var scale = 1f
    var shown = ""
    var marked = -2

    fun push(w: WebView) {
        if (!ready) return
        val k = "$abc|$ink|$hl|$scale"
        if (k == shown) return
        shown = k
        marked = -2
        w.evaluateJavascript("render(${JSONObject.quote(abc)},${JSONObject.quote(ink)},${JSONObject.quote(hl)},$scale)", null)
    }

    fun mark(w: WebView, si: Int) {
        if (!ready || si == marked) return
        marked = si
        w.evaluateJavascript("mark($si)", null)
    }
}

fun hex(c: Color): String = String.format("#%06X", 0xFFFFFF and c.toArgb())

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun StaffView(abc: String, curSi: Int, scale: Float, modifier: Modifier = Modifier) {
    val ink = hex(MaterialTheme.colorScheme.onSurface)
    val hl = hex(MaterialTheme.colorScheme.primary)
    val st = remember { StaffState() }
    var tinggi by remember { mutableIntStateOf(0) }
    AndroidView(
        modifier = modifier.height(if (tinggi > 0) tinggi.dp else 180.dp),
        factory = { ctx ->
            // WebView tidak menerima sentuhan: gulir dan geser ditangani aplikasi (tidak ada pilih teks)
            object : WebView(ctx) {
                override fun dispatchTouchEvent(event: MotionEvent?): Boolean = false
            }.apply {
                setBackgroundColor(android.graphics.Color.TRANSPARENT)
                settings.javaScriptEnabled = true
                settings.allowFileAccess = false
                isVerticalScrollBarEnabled = false
                isHorizontalScrollBarEnabled = false
                isLongClickable = false
                val wv = this
                addJavascriptInterface(object {
                    @JavascriptInterface
                    fun set(h: Int) { wv.post { tinggi = h } }
                }, "Tinggi")
                webViewClient = object : WebViewClient() {
                    override fun onPageFinished(view: WebView, url: String?) {
                        st.ready = true
                        st.push(view)
                        val m = st.marked
                        st.marked = -2
                        st.mark(view, m)
                    }

                    override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean = true
                }
                loadUrl("file:///android_asset/score.html")
            }
        },
        update = { w ->
            st.abc = abc
            st.scale = scale
            st.ink = ink
            st.hl = hl
            st.push(w)
            if (st.ready) st.mark(w, curSi) else st.marked = curSi
        },
    )
}

/* ---------------- Cetak / simpan PDF ---------------- */

object Printer {
    private var keep: WebView? = null

    private fun data(h: Hymn): JSONObject {
        val secs = Notation.build(h, 0)
        val bn = h.book == Book.BN
        val meta = JSONArray()
        fun m(k: String, v: String) { meta.put(JSONArray().put(k).put(v)) }
        m(h.book.short, h.id)
        m("do =", Notation.DO_NAME[h.key] ?: h.key)
        m("Birama", h.meter)
        h.tempo?.let { m("♩ =", it.toString()) }
        h.logu?.takeIf { it > 0 }?.let { m("Buku Logu", it.toString()) }
        h.category?.let { m(it, "") }
        val jsecs = JSONArray()
        for (sec in secs) {
            val bars = JSONArray()
            for (line in sec.lines) for (bar in line.items) {
                val beats = JSONArray()
                for (beat in bar.beats) {
                    val els = JSONArray()
                    for (e in beat.els) {
                        val syl = JSONArray()
                        for (r in sec.rows.indices) {
                            val s = e.syl.getOrNull(r)
                            syl.put(if (s == null) "" else s.t + if (s.cont) " -" else "")
                        }
                        els.put(
                            JSONObject()
                                .put("g", digitText(e))
                                .put("u", if (e.oct > 0) e.oct else 0)
                                .put("d", if (e.oct < 0) -e.oct else 0)
                                .put("acc", e.acc).put("hold", e.hold).put("rest", e.rest).put("lv", e.lv)
                                .put("ss", e.slurStart).put("se", e.slurEnd)
                                .put("syl", syl)
                        )
                    }
                    beats.put(JSONObject().put("exp", beat.exp).put("br", beat.breath).put("els", els))
                }
                val jb = JSONObject().put("beats", beats)
                bar.end?.let { jb.put("end", it) }
                bars.put(jb)
            }
            jsecs.put(JSONObject().put("bars", bars))
        }
        val verses = JSONArray()
        h.verses.forEachIndexed { k, v ->
            verses.put(JSONObject().put("n", h.verseLabel(k)).put("lines", JSONArray(v)))
        }
        return JSONObject()
            .put("no", h.id).put("title", h.title).put("bn", bn)
            .put("meta", meta).put("credits", JSONArray(h.credits))
            .put("foot", "${h.book.label} HKBP ${h.id} – ${h.title} · bukuende.com/${h.book.code}/${h.id}/")
            .put("verses", verses).put("secs", jsecs)
            .put("abc", Notation.toAbc(h, secs))
    }

    fun print(ctx: Context, h: Hymn) {
        val d = data(h).toString()
        val w = WebView(ctx)
        keep = w
        w.settings.javaScriptEnabled = true
        val name = "${h.book.short} ${h.id} ${h.title}"
        val main = Handler(Looper.getMainLooper())
        w.addJavascriptInterface(object {
            @JavascriptInterface
            fun siap() {
                main.post {
                    val pm = ctx.getSystemService(Context.PRINT_SERVICE) as PrintManager
                    val f4 = PrintAttributes.MediaSize("F4", "F4 (215 × 330 mm)", 8465, 12992)
                    pm.print(name, w.createPrintDocumentAdapter(name), PrintAttributes.Builder().setMediaSize(f4).build())
                }
            }
        }, "Cetak")
        w.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView, url: String?) {
                view.evaluateJavascript("printMode($d)", null)
            }
        }
        w.loadUrl("file:///android_asset/score.html")
    }
}
