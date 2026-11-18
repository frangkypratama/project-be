import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:hkbp/data/prefs.dart';
import 'package:hkbp/ui/app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Setara enableEdgeToEdge() di MainActivity.kt.
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
  final Prefs prefs = await Prefs.load();
  runApp(BukuEndeApp(prefs: prefs));
}
