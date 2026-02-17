# Proje Yapisi ve Detayli Modul Dokumantasyonu

Son guncelleme: Asama 7 tamamlandi, Asama 8'e gecilecek.

## Klasor Yapisi

```
memory-manager/
├── data/
│   ├── raw/                     # Ham fotograflar, sesler
│   ├── processed/               # Islenmis metadata
│   └── encrypted/               # Sifreli yedekler
├── models/
│   ├── clip/                    # CLIP model dosyalari
│   ├── sbert/                   # SBERT model dosyalari
│   └── whisper/                 # Whisper model dosyalari
├── database/
│   ├── __init__.py
│   └── schema.py                # SQLAlchemy ORM modelleri
├── security/
│   ├── encryption_manager.py    # Fernet sifreleme/cozme
│   └── security_manager.py      # Riza yonetimi ve denetim logu
├── src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── exif_extractor.py    # EXIF metadata cikarma
│   │   ├── photo_importer.py    # Toplu fotograf ice aktarma
│   │   ├── image_processer.py   # Yon duzeltme ve boyutlandirma
│   │   └── audio_processor.py   # Whisper ile transkript
│   ├── embedding/
│   │   ├── __init__.py
│   │   ├── clip_embedder.py     # CLIP gorsel embedding (512D)
│   │   ├── sbert_embedder.py    # SBERT metin embedding (384D)
│   │   ├── multimodal_fuser.py  # Gorsel+metin birlestirme (896D)
│   │   └── faiss_manager.py     # FAISS vektor arama indeksi
│   ├── search/
│   │   ├── __init__.py
│   │   ├── text_search.py       # Semantik metin aramasi
│   │   ├── time_search.py       # Tarih bazli arama
│   │   ├── location_search.py   # Konum bazli arama (Geopy)
│   │   └── search_engine.py     # Birlesik arama koordinatoru
│   ├── clustering/
│   │   ├── __init__.py
│   │   ├── dbscan_clusterer.py         # DBSCAN kumeleme (iskelet)
│   │   ├── refinement_clusterer.py     # Embedding ince ayar (iskelet)
│   │   ├── cover_photo_selector.py     # Kapak fotografi (iskelet)
│   │   └── event_clusterer.py          # Kumeleme koordinatoru (iskelet)
│   ├── flashcards/              # Egitim kartlari (bos)
│   └── ui/                      # Kullanici arayuzu (bos)
├── tests/
│   ├── __init__.py
│   ├── test_clustering.py       # (bos)
│   ├── test_embedding.py        # (bos)
│   └── test_photo_importer.py   # (bos)
├── requirements.txt
├── PROJECT_STRUCTURE.md
├── README.md
└── .gitignore
```

## Asama Bazinda Detayli Modul Dokumantasyonu

---

### Asama 1: Proje Kurulumu ✅

- `README.md` - Proje aciklamasi
- `requirements.txt` - Tum bagimliliklar (numpy, pandas, PIL, whisper, torch, transformers, sentence-transformers, faiss-cpu, scikit-learn, sqlalchemy, geopy, pytest)
- `.gitignore` - Guvenlik odakli (*.key, *.db, data/*, models/**/*.bin, *.log)
- Klasor yapisi olusturuldu

---

### Asama 2: Gizlilik & Sifreleme (Temel Katman) ✅

**`security/encryption_manager.py`** - Tam implementasyon
- `EncryptionManager` sinifi
- `_load_or_generate_key()`: Fernet anahtari yukle/olustur, `chmod 600` ile koru
- `encrypt_string(plain_text)`: Metin sifrele (transkript, ozet)
- `decrypt_string(encrypted_text)`: Metin coz
- `encrypt_file(file_path)`: Dosyayi diskte yerinde sifrele
- `decrypt_file(file_path)`: Sifreli dosya verisini belle coz (bytes doner)

**`security/security_manager.py`** - Tam implementasyon
- `PrivacyManager` sinifi
- `check_consent(item_id)`: Veri islenmeden once riza kontrolu
- `set_consent(item_id, status)`: Riza durumunu guncelle
- `secure_delete(file_path)`: Uzerine rastgele veri yaz + sil
- `_log_action(action, details)`: `privacy_audit.log`'a kayit

---

### Asama 3: Veritabani & Sema ✅

**`database/schema.py`** - Tam implementasyon
- `Item`: Ana veri tablosu (file_path, file_hash, type, has_consent, is_rotated, creation_datetime, latitude, longitude, transcription, faiss_index_id, event_id)
- `Event`: Olay tablosu (title, start_date, end_date, main_location, summary, cover_item_id)
- `Flashcard`: Egitim kartlari (question, answer, event_id, related_item_ids)
- `ReviewLog`: Tekrar loglari (review_date, user_rating, next_review_date)
- `DatabaseSchema`: Engine + `sessionmaker` fabrika

---

### Asama 4: Fotograf Ice Aktarma & EXIF ✅

**`src/ingestion/exif_extractor.py`** - Tam implementasyon
- `EXIFExtractor` sinifi
- `calculate_file_hash(path)`: SHA256 hash (duplicate tespiti icin)
- `extract_datetime(path)`: EXIF DateTimeOriginal
- `extract_gps_coordinates(path)`: GPS -> ondalik derece
- `extract_camera_info(path)`: Kamera marka/model
- `extract_metadata(path)`: Komple metadata paketi

**`src/ingestion/image_processer.py`** - Tam implementasyon
- `ImageProcessor` sinifi
- `fix_orientation(image)`: EXIF yon duzeltme (ImageOps.exif_transpose)
- `resize_if_needed(image, max_size=2000)`: En-boy oranini koruyarak kucult
- `process_image(path)`: Tam isleme pipeline'i

**`src/ingestion/photo_importer.py`** - Tam implementasyon
- `PhotoImporter` sinifi (PrivacyManager + EncryptionManager entegreli)
- `find_image_files(folder, recursive)`: .jpg, .jpeg, .png, .heic tara
- `is_duplicate(file_hash)`: DB'de hash kontrolu
- `add_photo_to_database(...)`: Item kaydi olustur
- `import_single_photo(path, consent)`: Tam pipeline, string sonuc doner ('imported'/'duplicate'/'no_consent'/'error')
- `import_folder(folder, consent)`: Toplu import + istatistik

---

### Asama 5: Ses Isleme ✅

**`src/ingestion/audio_processor.py`** - Tam implementasyon
- `AudioProcessor` sinifi (EncryptionManager + PrivacyManager entegreli)
- `load_model()`: Whisper lazy loading (small/base/medium/large)
- `is_supported_format(path)`: .mp3, .wav, .m4a, .flac, .ogg, .mp4, .aac, .wma
- `transcribe_audio(path, item_id)`: Consent kontrolu + transkript + `encrypt_string`
- `transcribe_batch(audio_data)`: Toplu transkript
- `get_audio_metadata(path)`: Sure, sample rate, kanal (WAV)

---

### Asama 6: Embedding & Multimodal Fusion ✅

**`src/embedding/clip_embedder.py`** - Tam implementasyon
- `CLIPEmbedder` sinifi (EncryptionManager entegreli)
- `load_model()`: clip-ViT-B-32 lazy loading (GPU/CPU)
- `_open_image(path)`: Normal ac, basarisizsa decrypt edip BytesIO ile ac
- `encode_image(path)`: Tek fotograf -> 512D normalize vektor
- `encode_images_batch(paths)`: Toplu embedding (batch_size=32)
- `encode_text(text)`: Metin -> 512D vektor (arama icin)
- `get_embedding_dimension()`: 512

**`src/embedding/sbert_embedder.py`** - Tam implementasyon
- `SBERTEmbedder` sinifi
- `_load_model()`: all-MiniLM-L6-v2 lazy loading (GPU/CPU)
- `encode_text(text)`: Metin -> 384D normalize vektor
- `encode_batch(texts)`: Toplu metin embedding
- `get_dimension()`: 384

**`src/embedding/multimodal_fuser.py`** - Tam implementasyon
- `MultimodalFuser` sinifi
- `fuse(image_vec, text_vec, weights)`: Agirlikli concat + L2 normalize -> 896D

**`src/embedding/faiss_manager.py`** - Tam implementasyon
- `FaissManager` sinifi
- `create_index(dim, index_type)`: FlatL2 veya HNSW
- `load_index(path)` / `save_index(path)`: Kalici depolama
- `add_embeddings(vectors, item_ids)`: L2 normalize + ekle
- `search(query_vec, k)`: k en yakin komsu
- `get_index_size()`: Toplam vektor sayisi

---

### Asama 7: Arama Motoru ✅

**`src/search/text_search.py`** - Tam implementasyon
- `TextSearch` sinifi (EncryptionManager entegreli)
- `search_images(query, k)`: Metin -> CLIP embedding -> FAISS -> `has_consent` filtre
- `search_texts(query, k)`: Metin -> SBERT embedding -> FAISS -> `has_consent` filtre -> `decrypt_string`
- `_decrypt_transcript(encrypted_text)`: Sifreli transkript cozme
- `search_all(query, k)`: Hem fotograf hem metin aramasi

**`src/search/time_search.py`** - Tam implementasyon
- `TimeSearch` sinifi
- `search_by_date_range(start, end)`: Tarih araligi + `has_consent` filtre
- `search_by_year(year)`: Yil bazli + `has_consent` filtre
- `search_by_month(year, month)`: Ay bazli + `has_consent` filtre
- `search_by_day(date)`: Gun bazli + `has_consent` filtre
- `get_timeline_stats()`: Istatistikler (sadece rizali veriler)

**`src/search/location_search.py`** - Tam implementasyon
- `LocationSearch` sinifi
- `calculate_distance(lat1, lon1, lat2, lon2)`: Geopy jeodezik mesafe (km)
- `search_by_location(lat, lon, radius)`: Yaricap aramasi + `has_consent` filtre
- `search_by_city(city, radius)`: Sehir adi -> koordinat -> arama

**`src/search/search_engine.py`** - Tam implementasyon
- `SearchEngine` sinifi
- `search(query, start_date, end_date, location, radius, k)`: Kombine arama
- `_intersect_results(results, filters)`: Birden fazla filtrede ortak sonuclar
- `advanced_search(filters)`: Yil/ay/sehir destekli gelismis arama

---

### Asama 8: Olay Kumeleme (SIRADA - iskelet mevcut)

**`src/clustering/dbscan_clusterer.py`** - Iskelet (metotlar `pass`)
- `cluster_by_time_and_location()`, `prepare_features()`, `normalize_features()`, `calculate_distance_matrix()`, `filter_small_clusters()`

**`src/clustering/refinement_clusterer.py`** - Iskelet (metotlar `pass`)
- `refine_large_clusters()`, `split_cluster_by_embeddings()`, `calculate_cluster_embeddings()`, `determine_optimal_clusters()`

**`src/clustering/cover_photo_selector.py`** - Iskelet (metotlar `pass`)
- `select_cover_photo()`, `calculate_photo_quality_score()`, `detect_faces()`, `calculate_center_distance()`, `calculate_composite_score()`

**`src/clustering/event_clusterer.py`** - Iskelet (metotlar `pass`)
- `cluster_all_items()`, `create_events_from_clusters()`, `generate_event_summary()`, `generate_event_name()`

---

### Asama 9-15: Henuz baslanmadi

- **Asama 9**: Ozetleme (`summarizer.py`)
- **Asama 10**: Flashcard & SM-2 (`flashcard_generator.py`, `sm2_scheduler.py`)
- **Asama 11**: Zaman Cizelgesi (`timeline_page.py`)
- **Asama 12**: Kullanici Arayuzu - Streamlit (`app.py`, `consent_modal.py`, `import_page.py`, vb.)
- **Asama 13**: Test Suite (`test_privacy.py`, `test_encryption.py`, `test_search.py`, vb.)
- **Asama 14**: Yedekleme & Disa Aktarma (`export_manager.py`)
- **Asama 15**: Performans Optimizasyonu (batch embedding, FAISS index tipi, cache)

---

## Guvenlik Entegrasyon Haritasi

| Modul | check_consent | encrypt | decrypt | has_consent filtre |
|-------|:---:|:---:|:---:|:---:|
| photo_importer | ✅ | ✅ (dosya) | - | - |
| audio_processor | ✅ | ✅ (transkript) | - | - |
| clip_embedder | - | - | ✅ (dosya) | - |
| text_search | - | - | ✅ (transkript) | ✅ |
| time_search | - | - | - | ✅ |
| location_search | - | - | - | ✅ |
| event_clusterer | yapilacak | - | yapilacak | yapilacak |
