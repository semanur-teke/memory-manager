# Kisisel Hafiza Yoneticisi (Memory Manager)

Kisisel fotograflarinizi, notlarinizi ve ses kayitlarinizi AI destekli bir sistemle organize edin, arayin ve hatirlatin.

## Proje Yapisi

```
memory-manager/
├── data/                        # Kullanici verileri
│   ├── raw/                     # Ham fotograflar, sesler
│   ├── processed/               # Islenmis metadata
│   └── encrypted/               # Sifreli yedekler
├── models/                      # AI modelleri
│   ├── clip/                    # CLIP model dosyalari
│   ├── sbert/                   # SBERT model dosyalari
│   └── whisper/                 # Whisper model dosyalari
├── database/                    # Veritabani
│   ├── __init__.py
│   └── schema.py                # SQLAlchemy ORM modelleri
├── security/                    # Guvenlik Katmani
│   ├── encryption_manager.py    # Fernet sifreleme/cozme
│   └── security_manager.py      # Riza yonetimi ve denetim logu
├── src/                         # Uygulama Mantigi
│   ├── ingestion/               # Veri alma
│   │   ├── __init__.py
│   │   ├── exif_extractor.py    # EXIF metadata cikarma
│   │   ├── photo_importer.py    # Toplu fotograf ice aktarma
│   │   ├── image_processer.py   # Yon duzeltme ve boyutlandirma
│   │   └── audio_processor.py   # Whisper ile transkript
│   ├── embedding/               # Vektor uretme
│   │   ├── __init__.py
│   │   ├── clip_embedder.py     # CLIP gorsel embedding (512D)
│   │   ├── sbert_embedder.py    # SBERT metin embedding (384D)
│   │   ├── multimodal_fuser.py  # Gorsel+metin birlestirme (896D)
│   │   └── faiss_manager.py     # FAISS vektor arama indeksi
│   ├── search/                  # Arama sistemleri
│   │   ├── __init__.py
│   │   ├── text_search.py       # Semantik metin aramasi
│   │   ├── time_search.py       # Tarih bazli arama
│   │   ├── location_search.py   # Konum bazli arama (Geopy)
│   │   └── search_engine.py     # Birlesik arama koordinatoru
│   ├── clustering/              # Olay kumeleme (iskelet)
│   │   ├── __init__.py
│   │   ├── dbscan_clusterer.py
│   │   ├── refinement_clusterer.py
│   │   ├── cover_photo_selector.py
│   │   └── event_clusterer.py
│   ├── flashcards/              # Egitim kartlari (bos)
│   └── ui/                      # Kullanici arayuzu (bos)
├── tests/                       # Test dosyalari
│   ├── __init__.py
│   ├── test_clustering.py
│   ├── test_embedding.py
│   └── test_photo_importer.py
├── requirements.txt
├── PROJECT_STRUCTURE.md
├── README.md
└── .gitignore
```

## Guvenlik Mimarisi

Bu proje "privacy-first" yaklasimi benimser. Guvenlik bir ozellik degil, projenin karakteridir.

- **Sifreleme**: Tum dosyalar Fernet (AES-128-CBC) ile diskte sifrelenir. Transkriptler DB'ye sifreli yazilir.
- **Riza Yonetimi**: Her Item icin `has_consent` bayragi. Rizasi olmayan veriler arama sonuclarinda goruntulenmez.
- **Guvenli Silme**: Dosyalar silinmeden once uzerine rastgele veri yazilir (`secure_delete`).
- **Denetim Logu**: Tum gizlilik islemleri `privacy_audit.log` dosyasina kaydedilir.
- **Anahtar Korumasi**: `secret.key` dosyasi OS seviyesinde sadece sahip tarafindan okunabilir (chmod 600).

## Gelistirme Asamalari

### Asama 1: Proje Kurulumu ✅
- Proje klasor yapisi, `.gitignore`, `requirements.txt`

### Asama 2: Gizlilik & Sifreleme (Temel Katman) ✅
- `encryption_manager.py`: Fernet sifreleme/cozme (string + dosya)
- `security_manager.py`: Riza kontrolu, guvenli silme, denetim logu

### Asama 3: Veritabani & Sema ✅
- `schema.py`: Item, Event, Flashcard, ReviewLog ORM modelleri
- `has_consent` ve `is_rotated` bayraklari
- `sessionmaker` ile dogru session yonetimi

### Asama 4: Fotograf Ice Aktarma & EXIF ✅
- `exif_extractor.py`: SHA256 hash, tarih, GPS, kamera bilgisi
- `image_processer.py`: EXIF yon duzeltme, boyut optimizasyonu
- `photo_importer.py`: Toplu import, duplicate kontrolu, sifreleme entegrasyonu

### Asama 5: Ses Isleme ✅
- `audio_processor.py`: Whisper transkript, sifreli kayit, batch isleme

### Asama 6: Embedding & Multimodal Fusion ✅
- `clip_embedder.py`: CLIP ViT-B-32 (512D), sifreli dosya destegi
- `sbert_embedder.py`: all-MiniLM-L6-v2 (384D)
- `multimodal_fuser.py`: Agirlikli birlestirme (896D)
- `faiss_manager.py`: FlatL2/HNSW indeks, ID mapping

### Asama 7: Arama Motoru ✅
- `text_search.py`: CLIP/SBERT ile semantik arama, consent filtresi, transkript decrypt
- `time_search.py`: Tarih araligi, yil, ay, gun bazli arama, consent filtresi
- `location_search.py`: Geopy jeodezik mesafe, sehir adi ile arama, consent filtresi
- `search_engine.py`: Tum filtreleri birlestiren kesisim mantigi

### Asama 8: Olay Kumeleme (sirada)
- DBSCAN ile zaman/konum kumeleme
- Embedding bazli ince ayar
- Kapak fotografi secimi
- Event olusturma ve DB kaydi

### Asama 9: Ozetleme
### Asama 10: Flashcard & SM-2
### Asama 11: Zaman Cizelgesi
### Asama 12: Kullanici Arayuzu (Streamlit)
### Asama 13: Test Suite
### Asama 14: Yedekleme & Disa Aktarma
### Asama 15: Performans Optimizasyonu

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Lisans

MIT License
