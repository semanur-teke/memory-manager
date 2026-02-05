# Kişisel Hafıza Yöneticisi (Memory Palace)

Kişisel fotoğraflarınızı, notlarınızı ve ses kayıtlarınızı AI destekli bir sistemle organize edin, arayın ve hatırlayın.

## Proje Yapısı

```
memory-manager/

├── data/                    # Kullanıcı verileri

│   ├── raw/                 # Ham fotoğraflar, sesler

│   ├── processed/           # İşlenmiş metadata

│   └── encrypted/           # Şifreli yedekler

├── models/                  # AI modelleri (CLIP, SBERT, Whisper)

├── database/                # Veritabanı

│   ├── schema.py            # SQLite tablo tanımları

│   └── __init__.py

├── security/                # GÜVENLİK KATMANI (Kök Dizinde)

│   ├── __init__.py

│   ├── encryption_manager.py # Veri şifreleme/çözme

│   └── security_manager.py   # İzin yönetimi ve gizlilik

├── src/                     # UYGULAMA MANTIĞI

│   ├── ingestion/           # Veri alma (Exif, Photo, Audio)

│   │   ├── __init__.py

│   │   ├── exif_extractor.py

│   │   ├── photo_importer.py

│   │   └── audio_processor.py

│   ├── embedding/           # Vektör üretme ve yönetim

│   │   ├── __init__.py

│   │   ├── clip_embedder.py

│   │   ├── sbert_embedder.py

│   │   ├── multimodal_fuser.py # Az önce yazdığımız fuser

│   │   └── faiss_manager.py

│   ├── search/              # Arama sistemleri

│   ├── clustering/          # Olay kümeleme

│   ├── flashcards/          # Eğitim kartları

│   └── ui/                  # Arayüz

├── tests/                   # Test dosyaları

│   ├── test_ai_engine.py    # 4/4 Geçen testimiz

│   └── ...

├── requirements.txt         # Bağımlılıklar

├── README.md

└── .gitignore
 
```

## Geliştirme Aşamaları

### Aşama 0: Proje Kurulumu ✅
- Proje klasör yapısı oluşturuldu
- Gerekli kütüphaneler belirlendi

### Aşama 1: Veritabanı Tasarımı 🔄
- SQLite veritabanı şeması tasarlandı
- Items, Events, Flashcards, ReviewLog tabloları

### Aşama 2: Fotoğraf İçe Aktarma 🔄
- EXIF metadata çıkarma
- Toplu içe aktarma

### Aşama 3: Ses Kayıtlarını İşleme 🔄
- Whisper ile transkript oluşturma

### Aşama 4: Embedding Üretme 🔄
- CLIP ile fotoğraf embedding'leri
- SBERT ile metin embedding'leri
- Faiss index entegrasyonu

### Aşama 5: Arama Sistemi 🔄
- Metin ile arama
- Zamana göre arama
- Konuma göre arama

### Aşama 6: Olay Kümeleme 🔄
- DBSCAN ile zaman/konum bazlı kümeleme
- Embedding bazlı ince ayar
- Temsilci fotoğraf seçimi

## Kurulum

```bash
pip install -r requirements.txt
```

## Kullanım

(İleride eklenecek)

## Lisans

MIT License

