import 'package:flutter/material.dart';

/// Olay detay ekrani — Phase 4'te doldurulacak.
class EventDetailScreen extends StatelessWidget {
  final String id;
  const EventDetailScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Olay #$id')),
      body: Center(child: Text('Olay detay sayfasi — event $id')),
    );
  }
}
