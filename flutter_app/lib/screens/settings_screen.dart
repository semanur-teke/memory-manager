import 'package:flutter/material.dart';
import '../widgets/empty_state.dart';

/// Ayarlar ekrani — Phase 5'te doldurulacak.
class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const EmptyState(
      icon: Icons.settings_outlined,
      message: 'Ayarlar\nYakinda: tema, secret.key yedekleme, cache temizleme',
    );
  }
}
