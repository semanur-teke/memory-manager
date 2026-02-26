import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart';
import 'api_client.dart';

/// Import islemi sirasinda gelen SSE progress verisi
class ImportProgress {
  final int current;
  final int total;
  final String status;
  final String file;

  ImportProgress({
    required this.current,
    required this.total,
    required this.status,
    required this.file,
  });

  double get percent => total > 0 ? current / total : 0;

  factory ImportProgress.fromJson(Map<String, dynamic> json) {
    return ImportProgress(
      current: json['current'] ?? 0,
      total: json['total'] ?? 0,
      status: json['status'] ?? '',
      file: json['file'] ?? '',
    );
  }
}

/// Import tamamlandigindaki ozet
class ImportResult {
  final int imported;
  final int skippedDuplicates;
  final int errors;
  final int totalFound;

  ImportResult({
    required this.imported,
    required this.skippedDuplicates,
    required this.errors,
    required this.totalFound,
  });

  factory ImportResult.fromJson(Map<String, dynamic> json) {
    return ImportResult(
      imported: json['imported'] ?? 0,
      skippedDuplicates: json['skipped_duplicates'] ?? 0,
      errors: json['errors'] ?? 0,
      totalFound: json['total_found'] ?? 0,
    );
  }
}

/// Import servis katmani — SSE stream ile klasor import.
class ImportService {
  final ApiClient _api;

  ImportService(this._api);

  /// Klasor import — SSE stream doner.
  /// onProgress: her dosya icin cagirilir
  /// onComplete: islem bittiginde cagirilir
  /// onError: hata durumunda cagirilir
  Future<void> importFolder({
    required String path,
    required bool consent,
    bool recursive = true,
    required void Function(ImportProgress) onProgress,
    required void Function(ImportResult) onComplete,
    required void Function(String) onError,
  }) async {
    try {
      final response = await _api.dio.post(
        '/api/import/folder',
        data: {
          'path': path,
          'consent': consent,
          'recursive': recursive,
        },
        options: Options(
          responseType: ResponseType.stream,
          headers: {'Accept': 'text/event-stream'},
        ),
      );

      final stream = response.data.stream as Stream<List<int>>;
      String buffer = '';

      await for (final chunk in stream) {
        buffer += utf8.decode(chunk);
        _processBuffer(buffer, onProgress, onComplete, onError, (remaining) {
          buffer = remaining;
        });
      }

      // Stream kapandiktan sonra buffer'da kalan veriyi isle
      // (son event \n\n ile bitmemis olabilir)
      if (buffer.trim().isNotEmpty) {
        _parseSingleEvent(buffer.trim(), onProgress, onComplete, onError);
      }
    } on DioException catch (e) {
      onError('Baglanti hatasi: ${e.message}');
    } catch (e) {
      onError('Beklenmeyen hata: $e');
    }
  }

  /// SSE buffer'ini parse et — \n\n ile ayrilan event bloklarini isler
  void _processBuffer(
    String buffer,
    void Function(ImportProgress) onProgress,
    void Function(ImportResult) onComplete,
    void Function(String) onError,
    void Function(String remaining) updateBuffer,
  ) {
    while (buffer.contains('\n\n')) {
      final eventEnd = buffer.indexOf('\n\n');
      final eventBlock = buffer.substring(0, eventEnd);
      buffer = buffer.substring(eventEnd + 2);
      _parseSingleEvent(eventBlock, onProgress, onComplete, onError);
    }
    updateBuffer(buffer);
  }

  /// Tek bir SSE event blogunu parse et
  void _parseSingleEvent(
    String eventBlock,
    void Function(ImportProgress) onProgress,
    void Function(ImportResult) onComplete,
    void Function(String) onError,
  ) {
    String? eventType;
    String? eventData;

    for (final line in eventBlock.split('\n')) {
      if (line.startsWith('event: ')) {
        eventType = line.substring(7).trim();
      } else if (line.startsWith('data: ')) {
        eventData = line.substring(6).trim();
      }
    }

    if (eventData == null) return;
    try {
      final json = jsonDecode(eventData) as Map<String, dynamic>;

      if (eventType == 'progress') {
        onProgress(ImportProgress.fromJson(json));
      } else if (eventType == 'complete') {
        onComplete(ImportResult.fromJson(json));
      } else if (eventType == 'error') {
        onError(json['detail'] ?? 'Bilinmeyen hata');
      }
    } catch (e) {
      // JSON parse hatasi — ignore
    }
  }

  /// Tekil fotograf import
  Future<String> importPhoto(String path, bool consent) async {
    final response = await _api.post('/api/import/photo', body: {
      'path': path,
      'consent': consent,
    });
    return response.data['status'] as String;
  }
}
