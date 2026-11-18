import 'package:flutter/material.dart';

// Biru gorga (warna situs bukuende.com) sebagai warna utama — port dari Theme.kt.

const ColorScheme _light = ColorScheme(
  brightness: Brightness.light,
  primary: Color(0xFF1F4F8F),
  onPrimary: Color(0xFFFFFFFF),
  primaryContainer: Color(0xFFD6E3FF),
  onPrimaryContainer: Color(0xFF001B3E),
  secondary: Color(0xFF555F71),
  onSecondary: Color(0xFFFFFFFF),
  secondaryContainer: Color(0xFFD9E3F8),
  onSecondaryContainer: Color(0xFF121C2B),
  tertiary: Color(0xFF7A5900),
  onTertiary: Color(0xFFFFFFFF),
  tertiaryContainer: Color(0xFFFFE7A0),
  onTertiaryContainer: Color(0xFF261A00),
  error: Color(0xFFBA1A1A),
  onError: Color(0xFFFFFFFF),
  errorContainer: Color(0xFFFFDAD6),
  onErrorContainer: Color(0xFF410002),
  surface: Color(0xFFF8F9FF),
  onSurface: Color(0xFF191C20),
  onSurfaceVariant: Color(0xFF44474E),
  surfaceDim: Color(0xFFD8DAE0),
  surfaceBright: Color(0xFFF8F9FF),
  surfaceContainerLowest: Color(0xFFFFFFFF),
  surfaceContainerLow: Color(0xFFF2F3FA),
  surfaceContainer: Color(0xFFECEEF4),
  surfaceContainerHigh: Color(0xFFE6E8EE),
  surfaceContainerHighest: Color(0xFFE1E2E8),
  outline: Color(0xFF74777F),
  outlineVariant: Color(0xFFC4C6D0),
  shadow: Color(0xFF000000),
  scrim: Color(0xFF000000),
  inverseSurface: Color(0xFF2E3036),
  onInverseSurface: Color(0xFFEFF0F7),
  inversePrimary: Color(0xFFA9C7FF),
  surfaceTint: Color(0xFF1F4F8F),
);

const ColorScheme _dark = ColorScheme(
  brightness: Brightness.dark,
  primary: Color(0xFFA9C7FF),
  onPrimary: Color(0xFF003063),
  primaryContainer: Color(0xFF184785),
  onPrimaryContainer: Color(0xFFD6E3FF),
  secondary: Color(0xFFBDC7DC),
  onSecondary: Color(0xFF273141),
  secondaryContainer: Color(0xFF3E4758),
  onSecondaryContainer: Color(0xFFD9E3F8),
  tertiary: Color(0xFFF0C048),
  onTertiary: Color(0xFF3F2E00),
  tertiaryContainer: Color(0xFF5B4300),
  onTertiaryContainer: Color(0xFFFFDF9C),
  error: Color(0xFFFFB4AB),
  onError: Color(0xFF690005),
  errorContainer: Color(0xFF93000A),
  onErrorContainer: Color(0xFFFFDAD6),
  surface: Color(0xFF111318),
  onSurface: Color(0xFFE2E2E9),
  onSurfaceVariant: Color(0xFFC4C6D0),
  surfaceDim: Color(0xFF111318),
  surfaceBright: Color(0xFF37393E),
  surfaceContainerLowest: Color(0xFF0C0E13),
  surfaceContainerLow: Color(0xFF191C20),
  surfaceContainer: Color(0xFF1D2024),
  surfaceContainerHigh: Color(0xFF282A2F),
  surfaceContainerHighest: Color(0xFF33353A),
  outline: Color(0xFF8E9099),
  outlineVariant: Color(0xFF44474E),
  shadow: Color(0xFF000000),
  scrim: Color(0xFF000000),
  inverseSurface: Color(0xFFE2E2E9),
  onInverseSurface: Color(0xFF2E3036),
  inversePrimary: Color(0xFF1F4F8F),
  surfaceTint: Color(0xFFA9C7FF),
);

/// Tema Material 3 aplikasi untuk kecerahan [b] (terang/gelap).
ThemeData buildTheme(Brightness b) {
  final ColorScheme scheme = b == Brightness.dark ? _dark : _light;
  return ThemeData(
    useMaterial3: true,
    brightness: b,
    colorScheme: scheme,
    scaffoldBackgroundColor: scheme.surface,
    navigationBarTheme: NavigationBarThemeData(
      labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
      // Seperti App.kt: label memakai gaya labelSmall.
      labelTextStyle: WidgetStateProperty.resolveWith<TextStyle?>((states) {
        final bool selected = states.contains(WidgetState.selected);
        return TextStyle(
          fontSize: 11,
          height: 16 / 11,
          letterSpacing: 0.5,
          fontWeight: FontWeight.w500,
          color: selected ? scheme.onSurface : scheme.onSurfaceVariant,
        );
      }),
    ),
  );
}
