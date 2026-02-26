import 'package:flutter/material.dart';
import 'colors.dart';

/// Uygulama tipografi sistemi.
/// Font boyutlari, agirliklari ve stilleri.
class AppTypography {
  AppTypography._();

  static const displayLarge = TextStyle(
    fontSize: 36,
    fontWeight: FontWeight.bold,
  ); // Istatistik sayilari

  static const headlineMedium = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.bold,
  ); // Sayfa basligi

  static const titleLarge = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.w600,
  ); // Bolum basligi

  static const titleMedium = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w500,
  ); // Kart basligi

  static const bodyMedium = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.normal,
  ); // Ana metin

  static const bodySmall = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.normal,
  ); // Kucuk metin

  static const labelSmall = TextStyle(
    fontSize: 11,
    color: AppColors.textSecondary,
  ); // Caption
}
