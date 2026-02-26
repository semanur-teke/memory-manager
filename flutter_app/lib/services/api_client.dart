import 'package:dio/dio.dart';

/// Base HTTP client — tum servisler bunu kullanir.
///
/// Kullanim:
/// ```dart
/// final api = ApiClient();
/// final response = await api.get('/api/items', queryParams: {'page': 1});
/// ```
class ApiClient {
  static const String defaultBaseUrl = 'http://localhost:8000';
  static const Duration defaultTimeout = Duration(seconds: 30);

  final Dio _dio;

  ApiClient({String baseUrl = defaultBaseUrl})
      : _dio = Dio(BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: defaultTimeout,
          receiveTimeout: defaultTimeout,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
        )) {
    // Gelistirme ortaminda request/response loglama
    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: false, // Body cok buyuk olabilir (base64 foto)
      logPrint: (obj) => print('[API] $obj'),
    ));
  }

  /// Dio instance'ina dogrudan erisim (SSE stream gibi ozel durumlar icin)
  Dio get dio => _dio;

  /// GET istegi
  Future<Response> get(
    String path, {
    Map<String, dynamic>? queryParams,
  }) async {
    return _dio.get(path, queryParameters: queryParams);
  }

  /// POST istegi
  Future<Response> post(
    String path, {
    dynamic body,
  }) async {
    return _dio.post(path, data: body);
  }

  /// PUT istegi
  Future<Response> put(
    String path, {
    dynamic body,
  }) async {
    return _dio.put(path, data: body);
  }

  /// DELETE istegi
  Future<Response> delete(String path) async {
    return _dio.delete(path);
  }

  /// GET — binary response (fullsize foto icin)
  Future<Response<List<int>>> getBytes(String path) async {
    return _dio.get<List<int>>(
      path,
      options: Options(responseType: ResponseType.bytes),
    );
  }

  /// Baglanti testi — /api/health endpoint'ini cagirip status kontrol eder
  Future<bool> healthCheck() async {
    try {
      final response = await get('/api/health');
      return response.statusCode == 200 &&
          response.data['status'] == 'ok';
    } catch (e) {
      return false;
    }
  }
}
