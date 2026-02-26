import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/gallery_provider.dart';
import '../widgets/photo_grid.dart';
import '../widgets/empty_state.dart';
import '../theme/colors.dart';
import '../theme/app_theme.dart';

/// Galeri ekrani.
/// Grid gorunumunde thumbnail'lar, filtreleme, infinite scroll.
class GalleryScreen extends ConsumerWidget {
  const GalleryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final gallery = ref.watch(galleryProvider);

    return Column(
      children: [
        // Ust bar — baslik + filtreler
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
          child: Row(
            children: [
              Text(
                'Galeri',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(width: 8),
              if (gallery.total > 0)
                Text(
                  '(${gallery.total} fotograf)',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              const Spacer(),
              // Siralama butonu
              IconButton(
                icon: Icon(
                  gallery.sortOrder == 'desc'
                      ? Icons.arrow_downward
                      : Icons.arrow_upward,
                ),
                tooltip: gallery.sortOrder == 'desc'
                    ? 'En yeniden eskiye'
                    : 'En eskiden yeniye',
                onPressed: () => ref.read(galleryProvider.notifier).toggleSort(),
              ),
              // Yenile butonu
              IconButton(
                icon: const Icon(Icons.refresh),
                tooltip: 'Yenile',
                onPressed: () => ref.read(galleryProvider.notifier).refresh(),
              ),
            ],
          ),
        ),

        // Icerik
        Expanded(
          child: gallery.items.isEmpty && !gallery.isLoading
              ? EmptyState(
                  icon: Icons.photo_library_outlined,
                  message: 'Henuz fotograf yok',
                  actionLabel: 'Import Et',
                  onAction: () => context.go('/import'),
                )
              : gallery.items.isEmpty && gallery.isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : PhotoGrid(
                      items: gallery.items,
                      isLoading: gallery.isLoading,
                      onTap: (item) {
                        context.go('/gallery/${item.itemId}');
                      },
                      onLoadMore: () {
                        ref.read(galleryProvider.notifier).loadNextPage();
                      },
                    ),
        ),
      ],
    );
  }
}
