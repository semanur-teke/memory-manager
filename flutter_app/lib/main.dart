import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app.dart';

/// Uygulama giris noktasi.
/// ProviderScope ile Riverpod state management baslatilir.
void main() {
  runApp(const ProviderScope(child: MemoryManagerApp()));
}
