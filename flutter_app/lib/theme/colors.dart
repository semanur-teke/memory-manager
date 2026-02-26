import 'package:flutter/material.dart';

/// Uygulama renk paleti.
/// Privacy-first bir ani uygulamasi icin guven, sakinlik ve guvenlik hissi.
class AppColors {
  AppColors._(); // Instance olusturulamaz

  // --- ANA RENKLER ---
  static const primary = Color(0xFF1B4965);       // Koyu deniz mavisi — guven
  static const primaryLight = Color(0xFF5FA8D3);   // Acik mavi — vurgular
  static const primaryDark = Color(0xFF0D2137);    // Cok koyu mavi — basliklar

  // --- IKINCIL RENKLER ---
  static const secondary = Color(0xFF62B6CB);      // Turkuaz — aksiyon butonlari
  static const accent = Color(0xFFBEE9E8);         // Pastel turkuaz — hover

  // --- SEMANTIK RENKLER ---
  static const success = Color(0xFF2D6A4F);        // Koyu yesil — riza verildi
  static const warning = Color(0xFFE76F51);        // Turuncu — dikkat
  static const danger = Color(0xFFD62828);         // Kirmizi — silme, tehlike
  static const info = Color(0xFF457B9D);           // Gri-mavi — bilgi

  // --- RIZA DURUMLARI ---
  static const consentGranted = Color(0xFF2D6A4F); // Yesil
  static const consentDenied = Color(0xFFADB5BD);  // Gri (kirmizi DEGIL!)
  // Neden gri: Riza vermemek bir hata degil, kullanicinin hakkidir.

  // --- NOTR RENKLER ---
  static const background = Color(0xFFF8F9FA);    // Sayfa arka plani
  static const surface = Color(0xFFFFFFFF);        // Kart arka plani
  static const textPrimary = Color(0xFF212529);    // Ana metin
  static const textSecondary = Color(0xFF6C757D);  // Ikincil metin
  static const border = Color(0xFFDEE2E6);         // Cerceveler

  // --- KOYU TEMA ---
  static const darkBackground = Color(0xFF121212);
  static const darkSurface = Color(0xFF1E1E1E);
  static const darkTextPrimary = Color(0xFFE0E0E0);
  static const darkTextSecondary = Color(0xFF9E9E9E);
}
