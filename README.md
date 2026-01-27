# Kişisel Hafıza Yöneticisi (Memory Palace)

Kişisel fotoğraflarınızı, notlarınızı ve ses kayıtlarınızı AI destekli bir sistemle organize edin, arayın ve hatırlayın.

## Proje Yapısı

```
memory-manager/
├── data/                    # Kullanıcı verileri
│   ├── raw/                # Ham fotoğraflar, sesler
│   ├── processed/          # İşlenmiş metadata
│   └── encrypted/          # Şifreli yedekler
├── models/                 # AI modelleri
│   ├── clip/
│   ├── sbert/
│   └── whisper/
├── database/               # Veritabanı
│   ├── metadata.db        # SQLite
│   └── embeddings.faiss   # Faiss index
├── src/
│   ├── ingestion/         # Veri alma
│   ├── embedding/         # Embedding üretme
│   ├── clustering/        # Olay kümeleme
│   ├── flashcards/        # Flashcard üretme
│   └── ui/                # Kullanıcı arayüzü
└── tests/
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

