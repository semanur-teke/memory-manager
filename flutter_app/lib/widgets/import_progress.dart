import 'package:flutter/material.dart';
import '../services/import_service.dart';
import '../theme/colors.dart';
import '../theme/app_theme.dart';

/// Import ilerleme widget'i.
/// Progress bar + istatistikler (aktarilan, atlanan, hata) + son dosya.
class ImportProgressWidget extends StatelessWidget {
  final ImportProgress? progress;
  final ImportResult? result;
  final bool isRunning;

  const ImportProgressWidget({
    super.key,
    this.progress,
    this.result,
    this.isRunning = false,
  });

  @override
  Widget build(BuildContext context) {
    // Import tamamlandi — sonuclari goster
    if (result != null) {
      return _buildResult(context);
    }

    // Import devam ediyor
    if (progress != null && isRunning) {
      return _buildProgress(context);
    }

    // Henuz baslamadi
    return const SizedBox.shrink();
  }

  Widget _buildProgress(BuildContext context) {
    final p = progress!;
    return Card(
      child: Padding(
        padding: AppSpacing.cardPadding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Import ediliyor...',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Text(
                  '${p.current} / ${p.total}',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            LinearProgressIndicator(
              value: p.percent,
              backgroundColor: AppColors.border,
              valueColor: const AlwaysStoppedAnimation(AppColors.primary),
              minHeight: 8,
              borderRadius: BorderRadius.circular(4),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              p.file,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.textSecondary,
                  ),
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: AppSpacing.xs),
            Text(
              'Son durum: ${_statusText(p.status)}',
              style: TextStyle(
                fontSize: 12,
                color: _statusColor(p.status),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResult(BuildContext context) {
    final r = result!;
    return Card(
      child: Padding(
        padding: AppSpacing.cardPadding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                const Icon(Icons.check_circle, color: AppColors.success, size: 24),
                const SizedBox(width: AppSpacing.sm),
                Text(
                  'Import tamamlandi!',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: AppColors.success,
                      ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            _statRow(context, 'Bulunan', r.totalFound, AppColors.textPrimary),
            _statRow(context, 'Aktarilan', r.imported, AppColors.success),
            _statRow(context, 'Kopya (atlandi)', r.skippedDuplicates, AppColors.warning),
            _statRow(context, 'Hata', r.errors, AppColors.danger),
          ],
        ),
      ),
    );
  }

  Widget _statRow(BuildContext context, String label, int value, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodyMedium),
          Text(
            '$value',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  String _statusText(String status) {
    switch (status) {
      case 'imported':
        return 'Aktarildi';
      case 'duplicate':
        return 'Kopya (atlandi)';
      case 'no_consent':
        return 'Riza yok';
      case 'error':
        return 'Hata';
      default:
        return status;
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'imported':
        return AppColors.success;
      case 'duplicate':
        return AppColors.warning;
      case 'error':
        return AppColors.danger;
      default:
        return AppColors.textSecondary;
    }
  }
}
