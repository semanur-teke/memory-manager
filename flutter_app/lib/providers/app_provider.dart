import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_client.dart';

/// API client provider — tum uygulamada tek instance kullanilir
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});

/// Backend baglanti durumu
final healthCheckProvider = FutureProvider<bool>((ref) async {
  final api = ref.read(apiClientProvider);
  return api.healthCheck();
});
