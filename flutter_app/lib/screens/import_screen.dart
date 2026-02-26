import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:go_router/go_router.dart';
import '../services/import_service.dart';
import '../providers/app_provider.dart';
import '../providers/gallery_provider.dart';
import '../widgets/import_progress.dart';
import '../theme/colors.dart';
import '../theme/app_theme.dart';

/// Import servis provider
final importServiceProvider = Provider((ref) {
  return ImportService(ref.read(apiClientProvider));
});

/// Import ekrani.
/// Klasor secimi, riza checkbox, SSE ile gercek zamanli ilerleme.
class ImportScreen extends ConsumerStatefulWidget {
  const ImportScreen({super.key});

  @override
  ConsumerState<ImportScreen> createState() => _ImportScreenState();
}

class _ImportScreenState extends ConsumerState<ImportScreen> {
  String? _selectedPath;
  bool _consent = false;
  bool _recursive = true;
  bool _isImporting = false;
  ImportProgress? _progress;
  ImportResult? _result;
  String? _error;

  Future<void> _pickFolder() async {
    final result = await FilePicker.platform.getDirectoryPath(
      dialogTitle: 'Import edilecek klasoru secin',
    );
    if (result != null) {
      setState(() {
        _selectedPath = result;
        _result = null;
        _error = null;
      });
    }
  }

  Future<void> _startImport() async {
    if (_selectedPath == null || !_consent) return;

    setState(() {
      _isImporting = true;
      _progress = null;
      _result = null;
      _error = null;
    });

    final service = ref.read(importServiceProvider);

    await service.importFolder(
      path: _selectedPath!,
      consent: _consent,
      recursive: _recursive,
      onProgress: (progress) {
        if (mounted) setState(() => _progress = progress);
      },
      onComplete: (result) {
        if (mounted) {
          setState(() {
            _result = result;
            _isImporting = false;
          });
          // Import bitti — galeri verisini yenile
          ref.read(galleryProvider.notifier).refresh();
        }
      },
      onError: (error) {
        if (mounted) {
          setState(() {
            _error = error;
            _isImporting = false;
          });
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: AppSpacing.pagePadding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Baslik
          Text('Fotograf Import', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: AppSpacing.lg),

          // Klasor secimi
          Card(
            child: Padding(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('1. Klasor Secin', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: AppSpacing.sm),
                  Row(
                    children: [
                      ElevatedButton.icon(
                        onPressed: _isImporting ? null : _pickFolder,
                        icon: const Icon(Icons.folder_open),
                        label: const Text('Klasor Sec'),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Text(
                          _selectedPath ?? 'Henuz klasor secilmedi',
                          style: TextStyle(
                            color: _selectedPath != null
                                ? AppColors.textPrimary
                                : AppColors.textSecondary,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  // Alt klasorleri dahil et
                  CheckboxListTile(
                    value: _recursive,
                    onChanged: _isImporting ? null : (v) => setState(() => _recursive = v!),
                    title: const Text('Alt klasorleri de tara'),
                    controlAffinity: ListTileControlAffinity.leading,
                    contentPadding: EdgeInsets.zero,
                    dense: true,
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: AppSpacing.md),

          // Riza onay
          Card(
            child: Padding(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('2. Riza Onayi', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: AppSpacing.sm),
                  CheckboxListTile(
                    value: _consent,
                    onChanged: _isImporting
                        ? null
                        : (v) => setState(() => _consent = v!),
                    title: const Text(
                      'Bu fotograflarin islenmesine ve sifrelenerek saklanmasina riza veriyorum.',
                    ),
                    subtitle: const Text(
                      'Riza vermeden import yapilamaz. Riza sonradan kaldirabilirsiniz.',
                      style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                    ),
                    controlAffinity: ListTileControlAffinity.leading,
                    contentPadding: EdgeInsets.zero,
                    activeColor: AppColors.success,
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: AppSpacing.md),

          // Import butonu
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              onPressed: (_selectedPath != null && _consent && !_isImporting)
                  ? _startImport
                  : null,
              icon: _isImporting
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.upload_file),
              label: Text(_isImporting ? 'Import ediliyor...' : 'Import Baslat'),
            ),
          ),

          const SizedBox(height: AppSpacing.md),

          // Ilerleme / Sonuc
          ImportProgressWidget(
            progress: _progress,
            result: _result,
            isRunning: _isImporting,
          ),

          // Hata mesaji
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.sm),
            Card(
              color: AppColors.danger.withOpacity(0.1),
              child: Padding(
                padding: AppSpacing.cardPadding,
                child: Row(
                  children: [
                    const Icon(Icons.error, color: AppColors.danger),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: Text(_error!, style: const TextStyle(color: AppColors.danger)),
                    ),
                  ],
                ),
              ),
            ),
          ],

          // Tamamlandi — Galeriye git butonu
          if (_result != null && _result!.imported > 0) ...[
            const SizedBox(height: AppSpacing.md),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () => context.go('/gallery'),
                icon: const Icon(Icons.photo_library),
                label: const Text('Galeriye Git'),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
