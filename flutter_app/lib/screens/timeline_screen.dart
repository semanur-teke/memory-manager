import 'package:flutter/material.dart';
import '../widgets/empty_state.dart';

/// Timeline ekrani — Phase 4'te doldurulacak.
class TimelineScreen extends StatelessWidget {
  const TimelineScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const EmptyState(
      icon: Icons.timeline_outlined,
      message: 'Timeline\nYakinda: kronolojik olay gorunumu',
    );
  }
}
