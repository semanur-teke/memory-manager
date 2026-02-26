import 'package:flutter/material.dart';

/// Flashcard tekrar ekrani — Phase 5'te doldurulacak.
class ReviewScreen extends StatelessWidget {
  const ReviewScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Kart Tekrari')),
      body: const Center(child: Text('Tekrar ekrani — yakinda')),
    );
  }
}
