import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/app_provider.dart';
import '../providers/gallery_provider.dart';
import '../services/search_service.dart';
import '../widgets/encrypted_image.dart';
import '../theme/colors.dart';
import '../theme/app_theme.dart';

/// Search servis provider
final searchServiceProvider = Provider((ref) {
  return SearchService(ref.read(apiClientProvider));
});

/// Arama ekrani.
/// Metin arama, tarih filtresi, sonuc grid'i.
class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final _queryController = TextEditingController();
  bool _showFilters = false;
  DateTime? _startDate;
  DateTime? _endDate;
  String? _typeFilter;
  bool _isSearching = false;
  SearchResponse? _searchResult;
  String? _error;

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  Future<void> _doSearch() async {
    final query = _queryController.text.trim();
    if (query.isEmpty && _startDate == null && _endDate == null) return;

    setState(() {
      _isSearching = true;
      _error = null;
    });

    try {
      final service = ref.read(searchServiceProvider);
      final result = await service.search(
        query: query.isEmpty ? null : query,
        startDate: _startDate,
        endDate: _endDate,
      );
      setState(() {
        _searchResult = result;
        _isSearching = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isSearching = false;
      });
    }
  }

  Future<void> _pickDate(bool isStart) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime.now(),
    );
    if (picked != null) {
      setState(() {
        if (isStart) {
          _startDate = picked;
        } else {
          _endDate = picked;
        }
      });
    }
  }

  void _clearFilters() {
    setState(() {
      _startDate = null;
      _endDate = null;
      _typeFilter = null;
      _queryController.clear();
      _searchResult = null;
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: AppSpacing.pagePadding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Baslik
          Text('Arama', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: AppSpacing.md),

          // Arama cubugu
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _queryController,
                  decoration: InputDecoration(
                    hintText: 'Dosya adi veya transkript icinde ara...',
                    prefixIcon: const Icon(Icons.search),
                    border: const OutlineInputBorder(),
                    suffixIcon: _queryController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear),
                            onPressed: () {
                              _queryController.clear();
                              setState(() {});
                            },
                          )
                        : null,
                  ),
                  onSubmitted: (_) => _doSearch(),
                  onChanged: (_) => setState(() {}),
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              ElevatedButton.icon(
                onPressed: _isSearching ? null : _doSearch,
                icon: _isSearching
                    ? const SizedBox(
                        width: 18, height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.search),
                label: const Text('Ara'),
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(80, 48),
                ),
              ),
            ],
          ),

          const SizedBox(height: AppSpacing.sm),

          // Filtre toggle
          InkWell(
            onTap: () => setState(() => _showFilters = !_showFilters),
            child: Row(
              children: [
                Icon(_showFilters ? Icons.expand_less : Icons.expand_more, size: 20),
                const SizedBox(width: 4),
                Text(
                  'Filtreler',
                  style: TextStyle(
                    color: AppColors.primary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                if (_startDate != null || _endDate != null) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Text('Aktif', style: TextStyle(fontSize: 11, color: AppColors.primary)),
                  ),
                ],
              ],
            ),
          ),

          // Filtre paneli
          if (_showFilters) ...[
            const SizedBox(height: AppSpacing.sm),
            Card(
              child: Padding(
                padding: AppSpacing.cardPadding,
                child: Column(
                  children: [
                    Row(
                      children: [
                        // Baslangic tarihi
                        Expanded(
                          child: InkWell(
                            onTap: () => _pickDate(true),
                            child: InputDecorator(
                              decoration: const InputDecoration(
                                labelText: 'Baslangic',
                                prefixIcon: Icon(Icons.calendar_today, size: 18),
                                border: OutlineInputBorder(),
                                contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                              ),
                              child: Text(
                                _startDate != null
                                    ? '${_startDate!.day.toString().padLeft(2, '0')}.${_startDate!.month.toString().padLeft(2, '0')}.${_startDate!.year}'
                                    : 'Sec...',
                                style: TextStyle(
                                  color: _startDate != null ? null : AppColors.textSecondary,
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: AppSpacing.md),
                        // Bitis tarihi
                        Expanded(
                          child: InkWell(
                            onTap: () => _pickDate(false),
                            child: InputDecorator(
                              decoration: const InputDecoration(
                                labelText: 'Bitis',
                                prefixIcon: Icon(Icons.calendar_today, size: 18),
                                border: OutlineInputBorder(),
                                contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                              ),
                              child: Text(
                                _endDate != null
                                    ? '${_endDate!.day.toString().padLeft(2, '0')}.${_endDate!.month.toString().padLeft(2, '0')}.${_endDate!.year}'
                                    : 'Sec...',
                                style: TextStyle(
                                  color: _endDate != null ? null : AppColors.textSecondary,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    Row(
                      children: [
                        TextButton.icon(
                          onPressed: _clearFilters,
                          icon: const Icon(Icons.clear_all, size: 18),
                          label: const Text('Filtreleri Temizle'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],

          const SizedBox(height: AppSpacing.md),

          // Sonuclar
          if (_error != null)
            Card(
              color: AppColors.danger.withOpacity(0.1),
              child: Padding(
                padding: AppSpacing.cardPadding,
                child: Row(
                  children: [
                    const Icon(Icons.error, color: AppColors.danger),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(child: Text(_error!, style: const TextStyle(color: AppColors.danger))),
                  ],
                ),
              ),
            ),

          if (_searchResult != null) ...[
            Text(
              '${_searchResult!.total} sonuc bulundu',
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
          ],

          // Sonuc grid'i
          if (_searchResult != null)
            Expanded(
              child: _searchResult!.results.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.search_off, size: 64, color: AppColors.textSecondary),
                          SizedBox(height: 16),
                          Text('Sonuc bulunamadi', style: TextStyle(color: AppColors.textSecondary)),
                        ],
                      ),
                    )
                  : GridView.builder(
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 4,
                        crossAxisSpacing: 8,
                        mainAxisSpacing: 8,
                      ),
                      itemCount: _searchResult!.results.length,
                      itemBuilder: (_, i) {
                        final result = _searchResult!.results[i];
                        final item = result.item;
                        return InkWell(
                          onTap: () => context.go('/photo/${item.itemId}'),
                          borderRadius: BorderRadius.circular(8),
                          child: Stack(
                            fit: StackFit.expand,
                            children: [
                              EncryptedImage(itemId: item.itemId),
                              // Tarih overlay
                              Positioned(
                                bottom: 0,
                                left: 0,
                                right: 0,
                                child: Container(
                                  decoration: BoxDecoration(
                                    borderRadius: const BorderRadius.vertical(bottom: Radius.circular(8)),
                                    gradient: LinearGradient(
                                      begin: Alignment.topCenter,
                                      end: Alignment.bottomCenter,
                                      colors: [Colors.transparent, Colors.black.withOpacity(0.7)],
                                    ),
                                  ),
                                  padding: const EdgeInsets.all(6),
                                  child: Text(
                                    item.dateFormatted,
                                    style: const TextStyle(color: Colors.white, fontSize: 11),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
            ),

          // Bos durum — henuz aranmadi
          if (_searchResult == null && _error == null && !_isSearching)
            const Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.search, size: 64, color: AppColors.textSecondary),
                    SizedBox(height: 16),
                    Text(
                      'Aramak icin yukariya yazin',
                      style: TextStyle(color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
