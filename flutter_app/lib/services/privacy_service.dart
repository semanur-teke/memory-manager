import 'api_client.dart';

/// Gizlilik istatistikleri
class PrivacyStats {
  final int consented;
  final int nonConsented;
  final int total;

  PrivacyStats({
    required this.consented,
    required this.nonConsented,
    required this.total,
  });

  factory PrivacyStats.fromJson(Map<String, dynamic> json) {
    return PrivacyStats(
      consented: json['consented'] ?? 0,
      nonConsented: json['non_consented'] ?? 0,
      total: json['total'] ?? 0,
    );
  }
}

/// Denetim logu kaydi
class AuditLogEntry {
  final String timestamp;
  final String action;
  final String details;

  AuditLogEntry({
    required this.timestamp,
    required this.action,
    required this.details,
  });

  factory AuditLogEntry.fromJson(Map<String, dynamic> json) {
    return AuditLogEntry(
      timestamp: json['timestamp'] ?? '',
      action: json['action'] ?? '',
      details: json['details'] ?? '',
    );
  }
}

/// Gizlilik servis katmani
class PrivacyService {
  final ApiClient _api;

  PrivacyService(this._api);

  /// Riza istatistikleri
  Future<PrivacyStats> getStats() async {
    final response = await _api.get('/api/privacy/stats');
    return PrivacyStats.fromJson(response.data);
  }

  /// Tum item'lar (consent filtreli)
  Future<Map<String, dynamic>> getItems({
    String consent = 'all',
    int page = 1,
    int size = 50,
  }) async {
    final response = await _api.get(
      '/api/privacy/items?consent=$consent&page=$page&size=$size',
    );
    return response.data as Map<String, dynamic>;
  }

  /// Tekil riza guncelle
  Future<void> setConsent(int itemId, bool status) async {
    await _api.put('/api/privacy/$itemId/consent', body: {'status': status});
  }

  /// Tekil guvenli silme
  Future<void> deleteItem(int itemId) async {
    await _api.delete('/api/privacy/$itemId');
  }

  /// Toplu riza guncelleme
  Future<void> bulkConsent(List<int> itemIds, bool status) async {
    await _api.post('/api/privacy/bulk-consent', body: {
      'item_ids': itemIds,
      'status': status,
    });
  }

  /// Toplu guvenli silme
  Future<void> bulkDelete(List<int> itemIds) async {
    await _api.post('/api/privacy/bulk-delete', body: {
      'item_ids': itemIds,
    });
  }

  /// Denetim logu
  Future<List<AuditLogEntry>> getAuditLog({int limit = 50}) async {
    final response = await _api.get('/api/privacy/audit-log?limit=$limit');
    final list = response.data as List;
    return list.map((e) => AuditLogEntry.fromJson(e)).toList();
  }
}
