package com.bukuende.hkbp

import android.annotation.SuppressLint
import android.content.Context
import android.print.PrintAttributes
import android.print.PrintManager
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.webkit.WebViewClient
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    /** Disimpan agar WebView tidak di-GC sebelum dokumen cetak selesai. */
    private var keep: WebView? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "bukuende/print")
            .setMethodCallHandler { call, result ->
                if (call.method == "print") {
                    val data = call.argument<String>("data")
                    if (data == null) {
                        result.error("ARG", "data kosong", null)
                    } else {
                        val name = call.argument<String>("name") ?: "Buku Ende"
                        cetak(data, name)
                        result.success(null)
                    }
                } else {
                    result.notImplemented()
                }
            }
    }

    @SuppressLint("SetJavaScriptEnabled", "AddJavascriptInterface")
    private fun cetak(data: String, name: String) {
        val w = WebView(this)
        keep = w
        w.settings.javaScriptEnabled = true
        w.addJavascriptInterface(object {
            @JavascriptInterface
            fun siap() {
                runOnUiThread {
                    val pm = getSystemService(Context.PRINT_SERVICE) as PrintManager
                    val f4 = PrintAttributes.MediaSize("F4", "F4 (215 × 330 mm)", 8465, 12992)
                    pm.print(
                        name,
                        w.createPrintDocumentAdapter(name),
                        PrintAttributes.Builder().setMediaSize(f4).build()
                    )
                }
            }
        }, "Cetak")
        w.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView, url: String?) {
                view.evaluateJavascript("printMode($data)", null)
            }
        }
        w.loadUrl("file:///android_asset/flutter_assets/assets/web/score.html")
    }
}
