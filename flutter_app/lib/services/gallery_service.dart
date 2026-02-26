import 'dart:typed_data';
import '../models/item.dart';
import 'api_client.dart';

/// Galeri servis katmani.
/// Item listeleme, detay, thumbnail ve fullsize API cagrilari.
class GalleryService {
  final ApiClient _api;

  GalleryService(this._api);

  /// Sayfalanmis item listesi
  Future<GalleryPage> getItems({
    int page = 1,
    int size = 40,
    int? year,
    int? month,
    String sort = 'desc',
    String? type,
  }) async {
    final params = <String, dynamic>{
      'page': page,
      'size': size,
      'sort': sort,
    };
    if (year != null) params['year'] = year;
    if (month != null) params['month'] = month;
    if (type != null) params['type'] = type;

    final response = await _api.get('/api/items', queryParams: params);
    final data = response.data as Map<String, dynamic>;

    return GalleryPage(
      items: (data['items'] as List).map((j) => Item.fromJson(j)).toList(),
      total: data['total'],
      page: data['page'],
      size: data['size'],
    );
  }

  /// Tekil item detayi
  Future<Item> getItem(int itemId) async {
    final response = await _api.get('/api/items/$itemId');
    return Item.fromJson(response.data);
  }

  /// Base64 thumbnail string
  Future<String> getThumbnail(int itemId) async {
    final response = await _api.get('/api/items/$itemId/thumbnail');
    return response.data['thumbnail'] as String;
  }

  /// Fullsize binary (JPEG bytes)
  Future<Uint8List> getFullsize(int itemId) async {
    final response = await _api.getBytes('/api/items/$itemId/fullsize');
    return Uint8List.fromList(response.data!);
  }
}

/// Sayfalanmis galeri sonucu
class GalleryPage {
  final List<Item> items;
  final int total;
  final int page;
  final int size;

  GalleryPage({
    required this.items,
    required this.total,
    required this.page,
    required this.size,
  });

  bool get hasMore => page * size < total;
}
