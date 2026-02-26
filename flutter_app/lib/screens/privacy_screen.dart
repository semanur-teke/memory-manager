import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/app_provider.dart';
import '../providers/gallery_provider.dart';
import '../services/privacy_service.dart';
import '../models/item.dart';
import '../widgets/confirm_dialog.dart';
import '../theme/colors.dart';
import '../theme/app_theme.dart';

/// Privacy servis provider
final privacyServiceProvider = Provider((ref) {
  return PrivacyService(ref.read(apiClientProvider));
});

/// Privacy stats provider — home_screen ile paylasiliyor
final privacyStatsProvider = FutureProvider((ref) async {
  final service = ref.read(privacyServiceProvider);
  return service.getStats();
});

/// Gizlilik yonetimi ekrani.
/// Stats, item listesi, toplu islemler, denetim logu.
class PrivacyScreen extends ConsumerStatefulWidget {
  const PrivacyScreen({super.key});

  @override
  ConsumerState<PrivacyScreen> createState() => _PrivacyScreenState();
}

class _PrivacyScreenState extends ConsumerState<PrivacyScreen> {
  String _consentFilter = 'all';
  final Set<int> _selectedIds = {};
  bool _showAuditLog = false;

  // Local state — provider yerine manuel yonetim (daha guvenilir refresh)
  PrivacyStats? _stats;
  List<Item> _items = [];
  List<AuditLogEntry> _auditLog = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final service = ref.read(privacyServiceProvider);
      final stats = await service.getStats();
      final itemsData = await service.getItems(consent: _consentFilter, size: 200);
      final items = (itemsData['items'] as List)
          .map((e) => Item.fromJson(e as Map<String, dynamic>))
          .toList();

      if (mounted) {
        setState(() {
          _stats = stats;
          _items = items;
          _isLoading = false;
        });
      }
      // Diger ekranlari da guncelle
      ref.invalidate(privacyStatsProvider);
      ref.read(galleryProvider.notifier).refresh();
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _loadAuditLog() async {
    try {
      final service = ref.read(privacyServiceProvider);
      final log = await service.getAuditLog();
      if (mounted) setState(() => _auditLog = log);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: AppSpacing.pagePadding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Baslik
          Row(
            children: [
              Text('Gizlilik Yonetimi', style: Theme.of(context).textTheme.headlineMedium),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: _loadAll,
                tooltip: 'Yenile',
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),

          // Stats kartlari
          if (_stats != null)
            Row(
              children: [
                _StatsCard(
                  label: 'Rizali',
                  count: _stats!.consented,
                  color: AppColors.success,
                  icon: Icons.check_circle,
                ),
                const SizedBox(width: AppSpacing.md),
                _StatsCard(
                  label: 'Rizasiz',
                  count: _stats!.nonConsented,
                  color: AppColors.textSecondary,
                  icon: Icons.remove_circle_outline,
                ),
                const SizedBox(width: AppSpacing.md),
                _StatsCard(
                  label: 'Toplam',
                  count: _stats!.total,
                  color: AppColors.primary,
                  icon: Icons.photo_library,
                ),
              ],
            ),

          const SizedBox(height: AppSpacing.md),

          // Aksiyon butonlari
          Wrap(
            spacing: AppSpacing.sm,
            children: [
              // Filtre dropdown
              DropdownButton<String>(
                value: _consentFilter,
                items: const [
                  DropdownMenuItem(value: 'all', child: Text('Tumu')),
                  DropdownMenuItem(value: 'true', child: Text('Rizali')),
                  DropdownMenuItem(value: 'false', child: Text('Rizasiz')),
                ],
                onChanged: (v) {
                  _consentFilter = v!;
                  _selectedIds.clear();
                  _loadAll();
                },
              ),
              const SizedBox(width: AppSpacing.sm),
              // Secilenlere riza ver
              ElevatedButton.icon(
                onPressed: _selectedIds.isEmpty ? null : () => _bulkConsent(true),
                icon: const Icon(Icons.check, size: 18),
                label: const Text('Riza Ver'),
                style: ElevatedButton.styleFrom(backgroundColor: AppColors.success),
              ),
              // Secilenlerin rizasini kaldir
              OutlinedButton.icon(
                onPressed: _selectedIds.isEmpty ? null : () => _bulkConsent(false),
                icon: const Icon(Icons.remove_circle_outline, size: 18),
                label: const Text('Riza Kaldir'),
              ),
              // Secilenleri sil
              ElevatedButton.icon(
                onPressed: _selectedIds.isEmpty ? null : _bulkDelete,
                icon: const Icon(Icons.delete, size: 18),
                label: const Text('Sil'),
                style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
              ),
              const SizedBox(width: AppSpacing.md),
              // Orphan temizleme
              OutlinedButton.icon(
                onPressed: _cleanupOrphans,
                icon: const Icon(Icons.cleaning_services, size: 18),
                label: const Text('Orphan Temizle'),
              ),
            ],
          ),

          const SizedBox(height: AppSpacing.md),

          // Hata mesaji
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: Text('Hata: $_error', style: const TextStyle(color: AppColors.danger)),
            ),

          // Item listesi
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _items.isEmpty
                    ? const Center(child: Text('Hic item bulunamadi'))
                    : _buildItemTable(),
          ),

          // Denetim logu toggle
          const Divider(),
          InkWell(
            onTap: () {
              setState(() => _showAuditLog = !_showAuditLog);
              if (_showAuditLog && _auditLog.isEmpty) _loadAuditLog();
            },
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
              child: Row(
                children: [
                  Icon(_showAuditLog ? Icons.expand_less : Icons.expand_more),
                  const SizedBox(width: AppSpacing.xs),
                  Text('Denetim Logu', style: Theme.of(context).textTheme.titleMedium),
                ],
              ),
            ),
          ),
          if (_showAuditLog) _buildAuditLog(),
        ],
      ),
    );
  }

  Widget _buildItemTable() {
    return SingleChildScrollView(
      child: DataTable(
        showCheckboxColumn: true,
        columns: const [
          DataColumn(label: Text('Dosya')),
          DataColumn(label: Text('Tur')),
          DataColumn(label: Text('Tarih')),
          DataColumn(label: Text('Riza')),
          DataColumn(label: Text('')),
        ],
        rows: _items.map((item) {
          final selected = _selectedIds.contains(item.itemId);
          return DataRow(
            selected: selected,
            onSelectChanged: (v) {
              setState(() {
                if (v == true) {
                  _selectedIds.add(item.itemId);
                } else {
                  _selectedIds.remove(item.itemId);
                }
              });
            },
            cells: [
              DataCell(
                SizedBox(
                  width: 200,
                  child: Text(item.fileName, overflow: TextOverflow.ellipsis),
                ),
              ),
              DataCell(Text(item.type)),
              DataCell(Text(item.dateFormatted)),
              DataCell(
                Switch(
                  value: item.hasConsent,
                  activeColor: AppColors.success,
                  onChanged: (v) => _toggleConsent(item.itemId, v),
                ),
              ),
              DataCell(
                IconButton(
                  icon: const Icon(Icons.delete_outline, color: AppColors.danger, size: 20),
                  onPressed: () => _deleteItem(item.itemId, item.fileName),
                  tooltip: 'Sil',
                ),
              ),
            ],
          );
        }).toList(),
      ),
    );
  }

  Widget _buildAuditLog() {
    if (_auditLog.isEmpty) {
      return const SizedBox(
        height: 100,
        child: Center(child: Text('Henuz kayit yok')),
      );
    }
    return SizedBox(
      height: 200,
      child: ListView.builder(
        itemCount: _auditLog.length,
        itemBuilder: (_, i) {
          final e = _auditLog[i];
          return ListTile(
            dense: true,
            leading: Icon(
              e.action.contains('DELETE') ? Icons.delete : Icons.shield,
              size: 16,
              color: e.action.contains('DELETE') ? AppColors.danger : AppColors.success,
            ),
            title: Text(e.details, style: const TextStyle(fontSize: 12)),
            subtitle: Text('${e.timestamp} ${e.action}',
                style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
          );
        },
      ),
    );
  }

  Future<void> _cleanupOrphans() async {
    try {
      final api = ref.read(apiClientProvider);
      final response = await api.delete('/api/items/cleanup');
      final msg = response.data['message'] ?? 'Temizlendi';
      await _loadAll();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(msg)),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Temizleme hatasi: $e')),
        );
      }
    }
  }

  Future<void> _toggleConsent(int itemId, bool status) async {
    try {
      final service = ref.read(privacyServiceProvider);
      await service.setConsent(itemId, status);
      // Tum veriyi yeniden yukle (stats + items)
      await _loadAll();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Hata: $e')),
        );
      }
    }
  }

  Future<void> _deleteItem(int itemId, String fileName) async {
    final confirmed = await ConfirmDialog.show(
      context,
      title: 'Guvenli Silme',
      message: '$fileName guvenli sekilde silinecek.\nBu islem geri alinamaz.',
      confirmText: 'Sil',
    );
    if (confirmed != true) return;

    try {
      await ref.read(privacyServiceProvider).deleteItem(itemId);
      _selectedIds.remove(itemId);
      await _loadAll();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Silme hatasi: $e')),
        );
      }
    }
  }

  Future<void> _bulkConsent(bool status) async {
    try {
      await ref.read(privacyServiceProvider).bulkConsent(
        _selectedIds.toList(),
        status,
      );
      _selectedIds.clear();
      await _loadAll();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${status ? "Riza verildi" : "Riza kaldirildi"}')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Hata: $e')),
        );
      }
    }
  }

  Future<void> _bulkDelete() async {
    final count = _selectedIds.length;
    final confirmed = await ConfirmDialog.show(
      context,
      title: 'Toplu Guvenli Silme',
      message: '$count item guvenli sekilde silinecek.\nBu islem geri alinamaz!',
      confirmText: 'Sil',
      requireTextInput: true,
      requiredInput: 'SIL',
    );
    if (confirmed != true) return;

    try {
      await ref.read(privacyServiceProvider).bulkDelete(_selectedIds.toList());
      _selectedIds.clear();
      await _loadAll();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$count item silindi')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Silme hatasi: $e')),
        );
      }
    }
  }
}

/// Stats karti
class _StatsCard extends StatelessWidget {
  final String label;
  final int count;
  final Color color;
  final IconData icon;

  const _StatsCard({
    required this.label,
    required this.count,
    required this.color,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: AppSpacing.cardPadding,
          child: Column(
            children: [
              Icon(icon, color: color, size: 32),
              const SizedBox(height: AppSpacing.xs),
              Text(
                '$count',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              Text(label, style: const TextStyle(color: AppColors.textSecondary)),
            ],
          ),
        ),
      ),
    );
  }
}
