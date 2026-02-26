import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/item.dart';
import '../services/gallery_service.dart';
import 'app_provider.dart';

/// Gallery service provider (singleton)
final galleryServiceProvider = Provider((ref) {
  return GalleryService(ref.read(apiClientProvider));
});

/// Thumbnail bellekte cache — API tekrar cagirilmaz
final thumbnailCacheProvider = Provider((ref) => <int, Uint8List>{});

/// Thumbnail provider — item_id bazli, otomatik cache
final thumbnailProvider = FutureProvider.family<Uint8List, int>((ref, itemId) async {
  // Once bellekteki cache'e bak
  final cache = ref.read(thumbnailCacheProvider);
  if (cache.containsKey(itemId)) return cache[itemId]!;

  // Cache'de yoksa API'den cek
  final service = ref.read(galleryServiceProvider);
  final base64Str = await service.getThumbnail(itemId);
  final bytes = base64Decode(base64Str);

  // Cache'e kaydet (sonraki rebuild'lerde API cagirilmaz)
  cache[itemId] = bytes;
  return bytes;
});

/// Galeri state
class GalleryState {
  final List<Item> items;
  final bool isLoading;
  final bool hasMore;
  final int currentPage;
  final int? selectedYear;
  final int? selectedMonth;
  final String sortOrder;
  final int total;

  const GalleryState({
    this.items = const [],
    this.isLoading = false,
    this.hasMore = true,
    this.currentPage = 0,
    this.selectedYear,
    this.selectedMonth,
    this.sortOrder = 'desc',
    this.total = 0,
  });

  GalleryState copyWith({
    List<Item>? items,
    bool? isLoading,
    bool? hasMore,
    int? currentPage,
    int? selectedYear,
    int? selectedMonth,
    String? sortOrder,
    int? total,
  }) {
    return GalleryState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      hasMore: hasMore ?? this.hasMore,
      currentPage: currentPage ?? this.currentPage,
      selectedYear: selectedYear,
      selectedMonth: selectedMonth,
      sortOrder: sortOrder ?? this.sortOrder,
      total: total ?? this.total,
    );
  }
}

/// Galeri state yoneticisi (Riverpod 2.0+ Notifier)
class GalleryNotifier extends Notifier<GalleryState> {
  @override
  GalleryState build() {
    // Ilk acilista otomatik yukle
    Future.microtask(() => loadNextPage());
    return const GalleryState();
  }

  Future<void> loadNextPage() async {
    if (state.isLoading || !state.hasMore) return;

    state = state.copyWith(isLoading: true);

    try {
      final service = ref.read(galleryServiceProvider);
      final nextPage = state.currentPage + 1;

      final page = await service.getItems(
        page: nextPage,
        year: state.selectedYear,
        month: state.selectedMonth,
        sort: state.sortOrder,
      );

      state = state.copyWith(
        items: [...state.items, ...page.items],
        currentPage: nextPage,
        hasMore: page.hasMore,
        total: page.total,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false);
    }
  }

  void setYearFilter(int? year) {
    state = GalleryState(
      selectedYear: year,
      selectedMonth: state.selectedMonth,
      sortOrder: state.sortOrder,
    );
    loadNextPage();
  }

  void setMonthFilter(int? month) {
    state = GalleryState(
      selectedYear: state.selectedYear,
      selectedMonth: month,
      sortOrder: state.sortOrder,
    );
    loadNextPage();
  }

  void toggleSort() {
    final newSort = state.sortOrder == 'desc' ? 'asc' : 'desc';
    state = GalleryState(
      selectedYear: state.selectedYear,
      selectedMonth: state.selectedMonth,
      sortOrder: newSort,
    );
    loadNextPage();
  }

  Future<void> refresh() async {
    state = GalleryState(
      selectedYear: state.selectedYear,
      selectedMonth: state.selectedMonth,
      sortOrder: state.sortOrder,
    );
    await loadNextPage();
  }
}

/// Ana galeri provider
final galleryProvider = NotifierProvider<GalleryNotifier, GalleryState>(
  GalleryNotifier.new,
);
