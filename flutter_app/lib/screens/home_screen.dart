import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/app_provider.dart';
import '../providers/gallery_provider.dart';
import '../services/privacy_service.dart';
import '../screens/privacy_screen.dart';
import '../widgets/encrypted_image.dart';
import '../models/item.dart';
import '../theme/colors.dart';
import '../theme/app_theme.dart';

/// Son eklenen 12 fotograf provider
final recentPhotosProvider = FutureProvider((ref) async {
  final service = ref.read(galleryServiceProvider);
  final page = await service.getItems(page: 1, size: 12);
  return page;
});

/// Dashboard ekrani.
/// Stats kartlari, son fotograflar, hizli aksiyon butonlari.
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(privacyStatsProvider);
    final recentAsync = ref.watch(recentPhotosProvider);

    return SingleChildScrollView(
      padding: AppSpacing.pagePadding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Baslik
          Text('Ana Sayfa', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: AppSpacing.lg),

          // Stats kartlari
          statsAsync.when(
            loading: () => const LinearProgressIndicator(),
            error: (e, _) => Text('Istatistik yuklenemedi: $e'),
            data: (stats) => Row(
              children: [
                _DashboardCard(
                  icon: Icons.photo_library,
                  value: '${stats.total}',
                  label: 'Ani',
                  color: AppColors.primary,
                ),
                const SizedBox(width: AppSpacing.md),
                _DashboardCard(
                  icon: Icons.check_circle,
                  value: '${stats.consented}',
                  label: 'Rizali',
                  color: AppColors.success,
                ),
                const SizedBox(width: AppSpacing.md),
                _DashboardCard(
                  icon: Icons.remove_circle_outline,
                  value: '${stats.nonConsented}',
                  label: 'Rizasiz',
                  color: AppColors.textSecondary,
                ),
                const SizedBox(width: AppSpacing.md),
                _DashboardCard(
                  icon: Icons.shield,
                  value: stats.total > 0
                      ? '${(stats.consented / stats.total * 100).toInt()}%'
                      : '0%',
                  label: 'Riza Orani',
                  color: AppColors.info,
                ),
              ],
            ),
          ),

          const SizedBox(height: AppSpacing.xl),

          // Son eklenenler
          Row(
            children: [
              Text('Son Eklenenler', style: Theme.of(context).textTheme.titleLarge),
              const Spacer(),
              TextButton(
                onPressed: () => context.go('/gallery'),
                child: const Text('Tumunu Gor'),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),

          recentAsync.when(
            loading: () => const SizedBox(
              height: 200,
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (e, _) => SizedBox(
              height: 200,
              child: Center(child: Text('Yuklenemedi: $e')),
            ),
            data: (page) {
              if (page.items.isEmpty) {
                return SizedBox(
                  height: 200,
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.photo_library_outlined,
                            size: 48, color: AppColors.textSecondary),
                        const SizedBox(height: 8),
                        const Text('Henuz fotograf yok',
                            style: TextStyle(color: AppColors.textSecondary)),
                        const SizedBox(height: 8),
                        ElevatedButton.icon(
                          onPressed: () => context.go('/import'),
                          icon: const Icon(Icons.upload_file, size: 18),
                          label: const Text('Import Et'),
                        ),
                      ],
                    ),
                  ),
                );
              }
              return SizedBox(
                height: 320,
                child: GridView.builder(
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 4,
                    crossAxisSpacing: 8,
                    mainAxisSpacing: 8,
                  ),
                  itemCount: page.items.length > 12 ? 12 : page.items.length,
                  itemBuilder: (_, i) {
                    final item = page.items[i];
                    return InkWell(
                      onTap: () => context.go('/photo/${item.itemId}'),
                      borderRadius: BorderRadius.circular(8),
                      child: EncryptedImage(itemId: item.itemId),
                    );
                  },
                ),
              );
            },
          ),

          const SizedBox(height: AppSpacing.xl),

          // Hizli aksiyon butonlari
          Text('Hizli Erisim', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.sm),
          Row(
            children: [
              Expanded(
                child: _QuickActionButton(
                  icon: Icons.upload_file,
                  label: 'Import',
                  color: AppColors.primary,
                  onTap: () => context.go('/import'),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: _QuickActionButton(
                  icon: Icons.photo_library,
                  label: 'Galeri',
                  color: AppColors.success,
                  onTap: () => context.go('/gallery'),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: _QuickActionButton(
                  icon: Icons.search,
                  label: 'Arama',
                  color: AppColors.info,
                  onTap: () => context.go('/search'),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: _QuickActionButton(
                  icon: Icons.shield,
                  label: 'Gizlilik',
                  color: AppColors.warning,
                  onTap: () => context.go('/privacy'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Dashboard istatistik karti
class _DashboardCard extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  final Color color;

  const _DashboardCard({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: AppSpacing.lg, horizontal: AppSpacing.md),
          child: Column(
            children: [
              Icon(icon, color: color, size: 36),
              const SizedBox(height: AppSpacing.sm),
              Text(
                value,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              const SizedBox(height: 4),
              Text(label, style: const TextStyle(color: AppColors.textSecondary)),
            ],
          ),
        ),
      ),
    );
  }
}

/// Hizli erisim butonu
class _QuickActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _QuickActionButton({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: AppSpacing.lg, horizontal: AppSpacing.md),
          child: Column(
            children: [
              Icon(icon, color: color, size: 32),
              const SizedBox(height: AppSpacing.sm),
              Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
            ],
          ),
        ),
      ),
    );
  }
}
