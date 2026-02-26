/// Item veri modeli.
/// API'den gelen item verisini Dart nesnesine donusturur.
class Item {
  final int itemId;
  final String filePath;
  final String type;
  final bool hasConsent;
  final bool isRotated;
  final DateTime creationDatetime;
  final double? latitude;
  final double? longitude;
  final String? transcription;
  final int? eventId;

  Item({
    required this.itemId,
    required this.filePath,
    required this.type,
    required this.hasConsent,
    required this.isRotated,
    required this.creationDatetime,
    this.latitude,
    this.longitude,
    this.transcription,
    this.eventId,
  });

  factory Item.fromJson(Map<String, dynamic> json) {
    return Item(
      itemId: json['item_id'],
      filePath: json['file_path'],
      type: json['type'],
      hasConsent: json['has_consent'],
      isRotated: json['is_rotated'],
      creationDatetime: DateTime.parse(json['creation_datetime']),
      latitude: json['latitude']?.toDouble(),
      longitude: json['longitude']?.toDouble(),
      transcription: json['transcription'],
      eventId: json['event_id'],
    );
  }

  /// Dosya adini path'ten cikar
  String get fileName => filePath.split(RegExp(r'[/\\]')).last;

  /// Tarih formatli string
  String get dateFormatted {
    return '${creationDatetime.day.toString().padLeft(2, '0')}.'
        '${creationDatetime.month.toString().padLeft(2, '0')}.'
        '${creationDatetime.year}';
  }
}
