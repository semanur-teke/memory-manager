import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../theme/app_theme.dart';

/// Bos durum gosterim widget'i.
/// Veri yokken ikon + mesaj gosterir, opsiyonel aksiyon butonu icerr.
///
/// Kullanim:
/// ```dart
/// EmptyState(
///   icon: Icons.photo_library_outlined,
///   message: 'Henuz fotograf yok',
///   actionLabel: 'Import Et',
///   onAction: () => context.go('/import'),
/// )
/// ```
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  const EmptyState({
    super.key,
    required this.icon,
    required this.message,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: AppSpacing.pagePadding,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 80,
              color: AppColors.border,
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              message,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: AppColors.textSecondary,
                  ),
              textAlign: TextAlign.center,
            ),
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: AppSpacing.lg),
              ElevatedButton(
                onPressed: onAction,
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
