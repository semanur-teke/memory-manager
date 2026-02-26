import 'package:flutter/material.dart';
import '../widgets/empty_state.dart';

/// Olaylar ekrani — Phase 4'te doldurulacak.
class EventsScreen extends StatelessWidget {
  const EventsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const EmptyState(
      icon: Icons.event_outlined,
      message: 'Olaylar\nYakinda: olay listesi ve detaylari',
    );
  }
}
