package com.bukuende.hkbp

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.print.PrintAttributes
import android.print.PrintManager
import android.webkit.JavascriptInterface
import android.webkit.MimeTypeMap
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import java.io.ByteArrayInputStream
import java.io.IOException
import java.io.InputStream

/**
 * Buku Ende & Buku Nyanyian HKBP Digital, versi luring.
 * Seluruh situs statis ada di assets/www dan disajikan lewat WebView
 * pada alamat maya https://appassets.androidplatform.net/ (tanpa jaringan).
 */
class MainActivity : Activity() {

    private lateinit var web: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        web = WebView(this)
        setContentView(web)

        val s = web.settings
        s.javaScriptEnabled = true
        s.domStorageEnabled = true
        s.mediaPlaybackRequiresUserGesture = false
        s.allowFileAccess = false
        s.allowContentAccess = false
        s.setSupportZoom(true)
        s.builtInZoomControls = true
        s.displayZoomControls = false

        web.addJavascriptInterface(Bridge(), "BukuEndeApp")
        web.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView?, request: WebResourceRequest?): WebResourceResponse? {
                val u = request?.url ?: return null
                return if (u.host == HOST) layani(u) else blokir()
            }

            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val u = request?.url ?: return true
                if (u.host == HOST) return false
                try {
                    startActivity(Intent(Intent.ACTION_VIEW, u))
                } catch (e: Exception) {
                    // tidak ada aplikasi untuk membuka tautan luar
                }
                return true
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                view?.evaluateJavascript(JS_CETAK, null)
            }
        }

        web.loadUrl("https://$HOST/")
    }

    private inner class Bridge {
        @JavascriptInterface
        fun print() {
            runOnUiThread { cetak() }
        }
    }

    private fun cetak() {
        val pm = getSystemService(Context.PRINT_SERVICE) as PrintManager
        val judul = web.title ?: "Buku Ende HKBP"
        val kertas = PrintAttributes.MediaSize("F4", "F4 (215 x 330 mm)", 8465, 12992)
        val atribut = PrintAttributes.Builder().setMediaSize(kertas).build()
        pm.print(judul, web.createPrintDocumentAdapter(judul), atribut)
    }

    private fun layani(u: Uri): WebResourceResponse {
        var p = (u.path ?: "/").trimStart('/')
        if (p.isEmpty() || p.endsWith("/")) p += "index.html"
        var stream = bukaAset(p)
        if (stream == null && !p.substringAfterLast('/').contains('.')) {
            p += "/index.html"
            stream = bukaAset(p)
        }
        if (stream != null) {
            return WebResourceResponse(jenis(p), "utf-8", stream)
        }
        val nf = bukaAset("404.html") ?: ByteArrayInputStream("Halaman tidak ditemukan".toByteArray())
        return WebResourceResponse("text/html", "utf-8", 404, "Not Found", HashMap<String, String>(), nf)
    }

    private fun blokir(): WebResourceResponse =
        WebResourceResponse("text/plain", "utf-8", 403, "Blocked", HashMap<String, String>(), ByteArrayInputStream(ByteArray(0)))

    private fun bukaAset(p: String): InputStream? =
        try {
            assets.open("www/$p")
        } catch (e: IOException) {
            null
        }

    private fun jenis(p: String): String {
        val ext = p.substringAfterLast('.', "").lowercase()
        return when (ext) {
            "html" -> "text/html"
            "js" -> "application/javascript"
            "css" -> "text/css"
            "json" -> "application/json"
            "txt" -> "text/plain"
            "xml" -> "application/xml"
            "svg" -> "image/svg+xml"
            "ico" -> "image/x-icon"
            else -> MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext) ?: "application/octet-stream"
        }
    }

    override fun onPause() {
        web.onPause()
        super.onPause()
    }

    override fun onResume() {
        super.onResume()
        web.onResume()
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }

    override fun onDestroy() {
        web.destroy()
        super.onDestroy()
    }

    companion object {
        const val HOST = "appassets.androidplatform.net"
        const val JS_CETAK = "window.print=function(){try{BukuEndeApp.print();}catch(e){}};"
    }
}
