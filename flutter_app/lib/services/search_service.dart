import '../models/item.dart';
import 'api_client.dart';

/// Arama sonucu
class SearchResultItem {
  final Item item;
  final double score;
  final String source;

  SearchResultItem({
    required this.item,
    required this.score,
    required this.source,
  });

  factory SearchResultItem.fromJson(Map<String, dynamic> json) {
    return SearchResultItem(
      item: Item.fromJson(json['item']),
      score: (json['score'] ?? 0).toDouble(),
      source: json['source'] ?? 'db',
    );
  }
}

/// Arama response
class SearchResponse {
  final List<SearchResultItem> results;
  final int total;
  final Map<String, dynamic> filtersApplied;

  SearchResponse({
    required this.results,
    required this.total,
    required this.filtersApplied,
  });

  factory SearchResponse.fromJson(Map<String, dynamic> json) {
    final list = json['results'] as List;
    return SearchResponse(
      results: list.map((e) => SearchResultItem.fromJson(e)).toList(),
      total: json['total'] ?? 0,
      filtersApplied: json['filters_applied'] ?? {},
    );
  }
}

/// Arama servis katmani
class SearchService {
  final ApiClient _api;

  SearchService(this._api);

  /// Birlesik arama
  Future<SearchResponse> search({
    String? query,
    DateTime? startDate,
    DateTime? endDate,
    double? lat,
    double? lng,
    double? radiusKm,
    int k = 40,
  }) async {
    final body = <String, dynamic>{'k': k};
    if (query != null && query.isNotEmpty) body['query'] = query;
    if (startDate != null) body['start_date'] = startDate.toIso8601String().split('T')[0];
    if (endDate != null) body['end_date'] = endDate.toIso8601String().split('T')[0];
    if (lat != null) body['lat'] = lat;
    if (lng != null) body['lng'] = lng;
    if (radiusKm != null) body['radius_km'] = radiusKm;

    final response = await _api.post('/api/search', body: body);
    return SearchResponse.fromJson(response.data);
  }

  /// Gelismis arama
  Future<SearchResponse> advancedSearch({
    String? query,
    int? year,
    int? month,
    String? city,
    String? type,
    double? radiusKm,
    int k = 40,
  }) async {
    final body = <String, dynamic>{'k': k};
    if (query != null && query.isNotEmpty) body['query'] = query;
    if (year != null) body['year'] = year;
    if (month != null) body['month'] = month;
    if (city != null && city.isNotEmpty) body['city'] = city;
    if (type != null) body['type'] = type;
    if (radiusKm != null) body['radius_km'] = radiusKm;

    final response = await _api.post('/api/search/advanced', body: body);
    return SearchResponse.fromJson(response.data);
  }
}
