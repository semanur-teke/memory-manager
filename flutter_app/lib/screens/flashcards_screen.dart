import 'package:flutter/material.dart';
import '../widgets/empty_state.dart';

/// Flashcard ekrani — Phase 5'te doldurulacak.
class FlashcardsScreen extends StatelessWidget {
  const FlashcardsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const EmptyState(
      icon: Icons.quiz_outlined,
      message: 'Flashcard\nYakinda: tekrar kartlari ve SM-2 zamanlama',
    );
  }
}
