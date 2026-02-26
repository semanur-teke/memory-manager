import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shimmer/shimmer.dart';
import '../models/item.dart';
import '../providers/gallery_provider.dart';
import '../providers/app_provider.dart';
import '../services/gallery_service.dart';
import '../widgets/consent_toggle.dart';
import '../widgets/confirm_dialog.dart';
import '../theme/colors.dart';
import '../theme/app_theme.dart';

/// Item detay provider — item_id bazli
final itemDetailProvider = FutureProvider.family<Item, int>((ref, itemId) async {
  final service = ref.read(galleryServiceProvider);
  return service.getItem(itemId);
});

/// Fullsize goruntu provider — item_id bazli
final fullsizeProvider = FutureProvider.family<Uint8List, int>((ref, itemId) async {
  final service = ref.read(galleryServiceProvider);
  return service.getFullsize(itemId);
});

/// Fotograf detay ekrani.
/// Tam boyut foto, metadata, riza toggle, silme.
class PhotoDetailScreen extends ConsumerWidget {
  final String id;
  const PhotoDetailScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final itemId = int.parse(id);
    final itemAsync = ref.watch(itemDetailProvider(itemId));
    final fullsizeAsync = ref.watch(fullsizeProvider(itemId));

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/gallery'),
        ),
        title: itemAsync.whenOrNull(
          data: (item) => Text(item.fileName),
        ) ?? const Text('Fotograf Detay'),
        actions: [
          // Silme butonu
          IconButton(
            icon: const Icon(Icons.delete_outline, color: AppColors.danger),
            tooltip: 'Sil',
            onPressed: () => _showDeleteDialog(context, ref, itemId),
          ),
        ],
      ),
      body: Row(
        children: [
          // Sol: Fullsize goruntu
          Expanded(
            flex: 3,
            child: Container(
              color: Colors.black,
              child: fullsizeAsync.when(
                loading: () => Shimmer.fromColors(
                  baseColor: Colors.grey[800]!,
                  highlightColor: Colors.grey[700]!,
                  child: Container(color: Colors.grey[800]),
                ),
                data: (bytes) => InteractiveViewer(
                  minScale: 0.5,
                  maxScale: 4.0,
                  child: Center(
                    child: Image.memory(
                      bytes,
                      fit: BoxFit.contain,
                      errorBuilder: (_, __, ___) => const Icon(
                        Icons.broken_image,
                        size: 64,
                        color: Colors.white54,
                      ),
                    ),
                  ),
                ),
                error: (e, _) => Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error, size: 64, color: Colors.red),
                      const SizedBox(height: 16),
                      Text('$e', style: const TextStyle(color: Colors.white70)),
                    ],
                  ),
                ),
              ),
            ),
          ),
          // Sag: Metadata paneli
          SizedBox(
            width: 320,
            child: itemAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Hata: $e')),
              data: (item) => _MetadataPanel(item: item, ref: ref),
            ),
          ),
        ],
      ),
    );
  }

  void _showDeleteDialog(BuildContext context, WidgetRef ref, int itemId) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Fotografi Sil'),
        content: const Text(
          'Bu fotograf kalici olarak silinecek.\nSifreli dosya diskten guvenli sekilde silinir.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Vazgec'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                final api = ref.read(apiClientProvider);
                await api.delete('/api/privacy/$itemId');
                if (context.mounted) {
                  ref.read(galleryProvider.notifier).refresh();
                  context.go('/gallery');
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Silme hatasi: $e')),
                  );
                }
              }
            },
            child: const Text('Sil', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}

/// Sag panel — metadata + consent toggle
class _MetadataPanel extends StatelessWidget {
  final Item item;
  final WidgetRef ref;

  const _MetadataPanel({required this.item, required this.ref});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Theme.of(context).scaffoldBackgroundColor,
      child: SingleChildScrollView(
        padding: AppSpacing.cardPadding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Bilgiler', style: Theme.of(context).textTheme.titleLarge),
            const Divider(),
            const SizedBox(height: AppSpacing.sm),

            // Riza toggle
            ConsentToggle(
              hasConsent: item.hasConsent,
              onChanged: (value) async {
                try {
                  final api = ref.read(apiClientProvider);
                  await api.put('/api/privacy/${item.itemId}/consent', body: {
                    'status': value,
                  });
                  // Yenile
                  ref.invalidate(itemDetailProvider(item.itemId));
                  ref.read(galleryProvider.notifier).refresh();
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Riza guncelleme hatasi: $e')),
                    );
                  }
                }
              },
            ),

            const SizedBox(height: AppSpacing.lg),
            _infoRow(context, 'Dosya', item.fileName),
            _infoRow(context, 'Tur', item.type),
            _infoRow(context, 'Tarih', item.dateFormatted),
            if (item.latitude != null && item.longitude != null)
              _infoRow(
                context,
                'Konum',
                '${item.latitude!.toStringAsFixed(4)}, ${item.longitude!.toStringAsFixed(4)}',
              ),
            if (item.eventId != null)
              _infoRow(context, 'Olay ID', '#${item.eventId}'),
            if (item.transcription != null && item.transcription!.isNotEmpty) ...[
              const SizedBox(height: AppSpacing.md),
              Text('Transkript', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: AppSpacing.xs),
              Container(
                padding: AppSpacing.cardPadding,
                decoration: BoxDecoration(
                  color: AppColors.background,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  item.transcription!,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _infoRow(BuildContext context, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(value, style: Theme.of(context).textTheme.bodyMedium),
          ),
        ],
      ),
    );
  }
}
