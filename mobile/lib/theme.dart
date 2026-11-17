import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Palette commune au site web, à l'application mobile et à l'application desktop.
class AppColors {
  static const primary = Color(0xFF0F5D4A);
  static const primarySoft = Color(0xFFE6F0ED);
  static const primaryMuted = Color(0xFFB9D3CB);
  static const bg = Color(0xFFF7F8F7);
  static const surface = Color(0xFFFFFFFF);
  static const border = Color(0xFFE4E7E5);
  static const borderStrong = Color(0xFFCFD5D1);
  static const text = Color(0xFF16201C);
  static const muted = Color(0xFF5B6661);
  static const warning = Color(0xFFB7791F);
  static const warningSoft = Color(0xFFFBF3E2);
  static const warningText = Color(0xFF8A5A12);
  static const danger = Color(0xFFB42318);
  static const dangerSoft = Color(0xFFFDECEA);
  static const success = Color(0xFF1E7B4F);
  static const successSoft = Color(0xFFE7F4EC);
}

const double kRadius = 8;

/// Convertit une couleur "#RRGGBB" renvoyée par l'API.
Color colorFromHex(String hex) {
  final value = int.tryParse(hex.replaceFirst('#', ''), radix: 16);
  if (value == null) return AppColors.muted;
  return Color(0xFF000000 | value);
}

ThemeData buildTheme() {
  final scheme = ColorScheme.fromSeed(seedColor: AppColors.primary).copyWith(
    primary: AppColors.primary,
    onPrimary: Colors.white,
    surface: AppColors.surface,
    onSurface: AppColors.text,
    error: AppColors.danger,
  );
  final base = ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: AppColors.bg,
  );
  return base.copyWith(
    textTheme: GoogleFonts.interTextTheme(base.textTheme).apply(
      bodyColor: AppColors.text,
      displayColor: AppColors.text,
    ),
  );
}

class AppText {
  static const title = TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.4, height: 1.2);
  static const section = TextStyle(fontSize: 16, fontWeight: FontWeight.w600);
  static const body = TextStyle(fontSize: 14, height: 1.45);
  static const strong = TextStyle(fontSize: 14, fontWeight: FontWeight.w500);
  static const small = TextStyle(fontSize: 12, color: AppColors.muted, height: 1.4);
  static const label = TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: AppColors.muted);
  static const stat = TextStyle(
    fontSize: 28,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.5,
    height: 1.2,
    fontFeatures: [FontFeature.tabularFigures()],
  );
  static const amount = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w500,
    fontFeatures: [FontFeature.tabularFigures()],
  );
}

OutlineInputBorder _border(Color color, [double width = 1]) {
  return OutlineInputBorder(
    borderRadius: BorderRadius.circular(kRadius),
    borderSide: BorderSide(color: color, width: width),
  );
}

InputDecoration fieldDecoration(String label, {String? hint, String? suffix, String? helper, Widget? prefixIcon}) {
  return InputDecoration(
    labelText: label,
    hintText: hint,
    suffixText: suffix,
    helperText: helper,
    prefixIcon: prefixIcon,
    filled: true,
    fillColor: AppColors.surface,
    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
    border: _border(AppColors.borderStrong),
    enabledBorder: _border(AppColors.borderStrong),
    focusedBorder: _border(AppColors.primary, 1.5),
    errorBorder: _border(AppColors.danger),
    focusedErrorBorder: _border(AppColors.danger, 1.5),
  );
}

final _buttonShape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(kRadius));

ButtonStyle primaryButtonStyle({Color color = AppColors.primary}) {
  return FilledButton.styleFrom(
    backgroundColor: color,
    foregroundColor: Colors.white,
    minimumSize: const Size(0, 48),
    padding: const EdgeInsets.symmetric(horizontal: 16),
    shape: _buttonShape,
    textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
  );
}

ButtonStyle secondaryButtonStyle() {
  return OutlinedButton.styleFrom(
    foregroundColor: AppColors.text,
    backgroundColor: AppColors.surface,
    minimumSize: const Size(0, 48),
    padding: const EdgeInsets.symmetric(horizontal: 16),
    side: const BorderSide(color: AppColors.borderStrong),
    shape: _buttonShape,
    textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
  );
}
