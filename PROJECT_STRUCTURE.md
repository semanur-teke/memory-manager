# Proje Yapısı ve Aşamalar

Bu dosya, projenin ilk 7 aşaması için oluşturulan dosya şablonlarını açıklar.

## Klasör Yapısı

```
memory-manager/
├── data/                    # Kullanıcı verileri
│   ├── raw/                # Ham fotoğraflar, sesler
│   ├── processed/          # İşlenmiş metadata
│   └── encrypted/          # Şifreli yedekler
├── models/                 # AI modelleri
│   ├── clip/              # CLIP model dosyaları
│   ├── sbert/             # SBERT model dosyaları
│   └── whisper/           # Whisper model dosyaları
├── database/               # Veritabanı
│   ├── schema.py          # Veritabanı şema tanımları (Aşama 1)
│   └── __init__.py
├── src/
│   ├── ingestion/         # Veri alma (Aşama 2-3)
│   │   ├── __init__.py
│   │   ├── exif_extractor.py      # EXIF metadata çıkarma (2.1)
│   │   ├── photo_importer.py      # Toplu fotoğraf içe aktarma (2.2)
│   │   └── audio_processor.py     # Ses transkript (3)
│   ├── embedding/         # Embedding üretme (Aşama 4)
│   │   ├── __init__.py
│   │   ├── clip_embedder.py       # CLIP embedding (4.1)
│   │   ├── sbert_embedder.py      # SBERT embedding (4.2)
│   │   └── faiss_manager.py       # Faiss index yönetimi (4.3)
│   ├── search/            # Arama sistemi (Aşama 5)
│   │   ├── __init__.py
│   │   ├── text_search.py         # Metin ile arama (5.1)
│   │   ├── time_search.py          # Zamana göre arama (5.2)
│   │   ├── location_search.py     # Konuma göre arama (5.3)
│   │   └── search_engine.py       # Unified arama motoru
│   ├── clustering/        # Olay kümeleme (Aşama 6)
│   │   ├── __init__.py
│   │   ├── dbscan_clusterer.py    # DBSCAN kümeleme (6.1)
│   │   ├── refinement_clusterer.py # Embedding bazlı ince ayar (6.2)
│   │   ├── cover_photo_selector.py # Kapak fotoğrafı seçimi (6.3)
│   │   └── event_clusterer.py     # Ana kümeleme koordinatörü
│   ├── flashcards/        # Flashcard (Aşama 7-8) - placeholder
│   └── ui/                # Kullanıcı arayüzü (Aşama 8-9) - placeholder
├── tests/                 # Test dosyaları
│   ├── test_exif_extractor.py
│   ├── test_photo_importer.py
│   ├── test_audio_processor.py
│   ├── test_embedding.py
│   ├── test_search.py
│   └── test_clustering.py
├── requirements.txt       # Python bağımlılıkları
├── README.md             # Proje açıklaması
└── .gitignore           # Git ignore kuralları
```

## Aşama Bazında Dosyalar

### Aşama 0: Proje Kurulumu
- ✅ `README.md` - Proje açıklaması
- ✅ `requirements.txt` - Bağımlılıklar
- ✅ `.gitignore` - Git ignore kuralları
- ✅ Klasör yapısı oluşturuldu

### Aşama 1: Veritabanı Tasarımı
- ✅ `database/schema.py` - Veritabanı şema tanımları
  - `DatabaseSchema` sınıfı
  - `create_items_table()` - Items tablosu
  - `create_events_table()` - Events tablosu
  - `create_flashcards_table()` - Flashcards tablosu
  - `create_review_log_table()` - ReviewLog tablosu

### Aşama 2: Fotoğraf İçe Aktarma
- ✅ `src/ingestion/exif_extractor.py` - EXIF metadata çıkarma
  - `EXIFExtractor` sınıfı
  - `extract_metadata()` - Tüm metadata'yı çıkar
  - `extract_datetime()` - Tarih/saat çıkar
  - `extract_gps_coordinates()` - GPS koordinatları
  - `calculate_file_hash()` - Dosya hash'i
- ✅ `src/ingestion/photo_importer.py` - Toplu içe aktarma
  - `PhotoImporter` sınıfı
  - `import_folder()` - Klasör içe aktarma
  - `find_image_files()` - Görüntü dosyalarını bul
  - `is_duplicate()` - Duplicate kontrolü

### Aşama 3: Ses Kayıtlarını İşleme
- ✅ `src/ingestion/audio_processor.py` - Ses transkript
  - `AudioProcessor` sınıfı
  - `transcribe_audio()` - Tek ses dosyası transkript
  - `transcribe_batch()` - Toplu transkript
  - `get_audio_metadata()` - Ses metadata'sı

### Aşama 4: Embedding Üretme
- ✅ `src/embedding/clip_embedder.py` - CLIP embedding
  - `CLIPEmbedder` sınıfı
  - `encode_image()` - Tek fotoğraf embedding
  - `encode_images_batch()` - Toplu embedding
  - `encode_text()` - Metin embedding (arama için)
- ✅ `src/embedding/sbert_embedder.py` - SBERT embedding
  - `SBERTEmbedder` sınıfı
  - `encode_text()` - Metin embedding
  - `encode_texts_batch()` - Toplu metin embedding
- ✅ `src/embedding/faiss_manager.py` - Faiss index yönetimi
  - `FaissManager` sınıfı
  - `add_embeddings()` - Embedding ekleme
  - `search()` - Arama yapma
  - `search_batch()` - Toplu arama

### Aşama 5: Arama Sistemi
- ✅ `src/search/text_search.py` - Metin ile arama
  - `TextSearch` sınıfı
  - `search_images()` - Fotoğraf arama
  - `search_texts()` - Metin arama
- ✅ `src/search/time_search.py` - Zamana göre arama
  - `TimeSearch` sınıfı
  - `search_by_date_range()` - Tarih aralığı arama
  - `search_by_year()` - Yıl bazlı arama
- ✅ `src/search/location_search.py` - Konuma göre arama
  - `LocationSearch` sınıfı
  - `search_by_location()` - Koordinat bazlı arama
  - `calculate_distance()` - Mesafe hesaplama
- ✅ `src/search/search_engine.py` - Unified arama motoru
  - `SearchEngine` sınıfı
  - `search()` - Kombine arama

### Aşama 6: Olay Kümeleme
- ✅ `src/clustering/dbscan_clusterer.py` - DBSCAN kümeleme
  - `DBSCANClusterer` sınıfı
  - `cluster_by_time_and_location()` - Zaman/konum kümeleme
  - `prepare_features()` - Feature hazırlama
- ✅ `src/clustering/refinement_clusterer.py` - Embedding bazlı ince ayar
  - `RefinementClusterer` sınıfı
  - `refine_large_clusters()` - Büyük kümeleri böl
  - `split_cluster_by_embeddings()` - Embedding bazlı bölme
- ✅ `src/clustering/cover_photo_selector.py` - Kapak fotoğrafı seçimi
  - `CoverPhotoSelector` sınıfı
  - `select_cover_photo()` - Kapak fotoğrafı seç
  - `calculate_photo_quality_score()` - Kalite skoru
- ✅ `src/clustering/event_clusterer.py` - Ana kümeleme koordinatörü
  - `EventClusterer` sınıfı
  - `cluster_all_items()` - Tüm öğeleri kümele
  - `create_events_from_clusters()` - Olayları oluştur

## Notlar

- Tüm dosyalar şablon olarak oluşturuldu, kodlar henüz yazılmadı
- Her sınıf ve fonksiyon için docstring'ler eklendi
- Fonksiyonlar şimdilik `pass` ile boş bırakıldı
- Test dosyaları placeholder olarak oluşturuldu
- Aşama 7-8 (Flashcards) ve 8-9 (UI) için placeholder klasörler eklendi

## Sonraki Adımlar

1. Her modül için kod implementasyonu
2. Veritabanı bağlantılarının kurulması
3. Model yükleme fonksiyonlarının implementasyonu
4. Testlerin yazılması
5. Entegrasyon testleri

