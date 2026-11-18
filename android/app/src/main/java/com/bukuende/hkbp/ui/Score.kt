package com.bukuende.hkbp.ui

import android.annotation.SuppressLint
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.print.PrintAttributes
import android.print.PrintManager
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
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import com.bukuende.hkbp.data.Hymn
import com.bukuende.hkbp.music.Bar
import com.bukuende.hkbp.music.Beat
import com.bukuende.hkbp.music.El
import com.bukuende.hkbp.music.Notation
import com.bukuende.hkbp.music.Sec
import org.json.JSONObject
import kotlin.math.abs

/* ---------------- Not angka, digambar native ---------------- */

private fun lineCount(beat: Beat): Int = when {
    beat.els.size <= 1 -> 0
    beat.els.size == 2 -> 1
    beat.els.size == 3 && beat.els.all { abs(it.dur * 3 - 1) < 1e-6 } -> 1
    else -> 2
}

private fun digitText(e: El) = if (e.hold) "·" else e.deg.toString()

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AngkaView(secs: List<Sec>, curSi: Int, scale: Float, modifier: Modifier = Modifier) {
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
                    BarView(bar, sec.rows.size, curSi, ink, hl, digit, sylSize, barH)
                }
            }
        }
    }
}

@Composable
private fun BarView(
    bar: Bar, rows: Int, curSi: Int, ink: Color, hl: Color,
    digit: androidx.compose.ui.unit.TextUnit, syl: androidx.compose.ui.unit.TextUnit, barH: androidx.compose.ui.unit.Dp,
) {
    Row(verticalAlignment = Alignment.Top) {
        bar.beats.forEach { beat ->
            val n = lineCount(beat)
            Row(
                Modifier
                    .drawBehind {
                        val sw = 1.3.dp.toPx()
                        for (k in 0 until n) {
                            val y = (2 + 4 * k).dp.toPx()
                            drawLine(ink, Offset(3.dp.toPx(), y), Offset(size.width - 3.dp.toPx(), y), sw)
                        }
                    }
                    .padding(top = 12.dp)
            ) {
                beat.els.forEach { e -> ElView(e, rows, !e.hold && e.si == curSi, ink, hl, digit, syl) }
            }
            if (beat.breath) Text("’", fontSize = digit, color = ink, modifier = Modifier.padding(top = 10.dp))
        }
        val end = bar.end
        if (end != null) {
            Row(Modifier.padding(start = 4.dp, end = 6.dp, top = 12.dp), verticalAlignment = Alignment.CenterVertically) {
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
    var shown = ""
    var marked = -2

    fun push(w: WebView) {
        if (!ready) return
        val k = "$abc|$ink|$hl"
        if (k == shown) return
        shown = k
        marked = -2
        w.evaluateJavascript("render(${JSONObject.quote(abc)},${JSONObject.quote(ink)},${JSONObject.quote(hl)})", null)
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
fun StaffView(abc: String, curSi: Int, modifier: Modifier = Modifier) {
    val ink = hex(MaterialTheme.colorScheme.onSurface)
    val hl = hex(MaterialTheme.colorScheme.primary)
    val st = remember { StaffState() }
    AndroidView(
        modifier = modifier,
        factory = { ctx ->
            WebView(ctx).apply {
                setBackgroundColor(android.graphics.Color.TRANSPARENT)
                settings.javaScriptEnabled = true
                settings.builtInZoomControls = true
                settings.displayZoomControls = false
                settings.allowFileAccess = false
                isHorizontalScrollBarEnabled = false
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

    private fun esc(s: String) = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    private fun angkaHtml(secs: List<Sec>): String = buildString {
        for (sec in secs) {
            append("<div class=flow>")
            for (line in sec.lines) for (bar in line.items) {
                append("<div class=bar>")
                for (beat in bar.beats) {
                    val n = lineCount(beat)
                    append("<div class=\"beat").append(if (n == 1) " l1" else if (n >= 2) " l2" else "").append("\">")
                    for (e in beat.els) {
                        append("<div class=\"el").append(if (e.acc != 0 && !e.hold) " sh" else "").append("\">")
                        append("<span class=u>").append(if (e.oct > 0) "•".repeat(e.oct) else "&nbsp;").append("</span>")
                        append("<span class=g>").append(digitText(e)).append("</span>")
                        append("<span class=d>").append(if (e.oct < 0) "•".repeat(-e.oct) else "&nbsp;").append("</span>")
                        for (r in sec.rows.indices) {
                            val s = e.syl.getOrNull(r)
                            append("<span class=s>").append(if (s == null) "&nbsp;" else esc(s.t + if (s.cont) " -" else "")).append("</span>")
                        }
                        append("</div>")
                    }
                    append("</div>")
                    if (beat.breath) append("<span>’</span>")
                }
                bar.end?.let { append(if (it == "|") "<span class=bl></span>" else "<span class=bl></span><span class=\"bl f\"></span>") }
                append("</div>")
            }
            append("</div>")
        }
    }

    private fun versesHtml(h: Hymn): String = buildString {
        append("<div class=vs>")
        h.verses.forEachIndexed { k, v ->
            append("<p><b>").append(h.verseLabel(k)).append(".</b> ")
            append(v.joinToString("<br>") { esc(it) })
            append("</p>")
        }
        append("</div>")
    }

    fun print(ctx: Context, h: Hymn) {
        val secs = Notation.build(h, 0)
        val abc = Notation.toAbc(h, secs)
        val meta = esc(
            listOfNotNull(
                "Do = ${Notation.DO_NAME[h.key] ?: h.key}", h.meter,
                h.logu?.takeIf { it > 0 }?.let { "Logu $it" },
            ).joinToString(" · ") + if (h.credits.isEmpty()) "" else " · " + h.credits.joinToString(" · ")
        )
        val head = "<h1>${esc(h.book.label)} ${esc(h.id)} – ${esc(h.title)}</h1><p class=sub>$meta</p>"
        val body = "<section class=part>$head<div class=lbl>Not angka</div>${angkaHtml(secs)}" +
            "<div class=lbl>Lirik</div>${versesHtml(h)}</section>" +
            "<section class=part>$head<div class=lbl>Not balok</div><div id=staffp></div>" +
            "<div class=lbl>Lirik</div>${versesHtml(h)}</section>" +
            "<p class=sub style=\"margin-top:16px\">Buku Ende HKBP Digital · bukuende.com</p>"

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
                view.evaluateJavascript("document.getElementById('s').outerHTML=${JSONObject.quote(body)};printMode(${JSONObject.quote(abc)})", null)
            }
        }
        w.loadUrl("file:///android_asset/score.html")
    }
}
