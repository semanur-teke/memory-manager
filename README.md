# Memory Manager — Kisisel Hafiza Yoneticisi

<p align="center">
  <strong>Anilarin Sana Ait, Guvende ve Akilli.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PyTorch-2.10-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch">
  <img src="https://img.shields.io/badge/FAISS-Vector%20Search-4285F4?style=for-the-badge&logo=meta&logoColor=white" alt="FAISS">
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Flutter-UI-02569B?style=for-the-badge&logo=flutter&logoColor=white" alt="Flutter">
</p>

<p align="center">
  <a href="#ozellikler">Ozellikler</a> •
  <a href="#mimari">Mimari</a> •
  <a href="#kurulum">Kurulum</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#yol-haritasi">Yol Haritasi</a> •
  <a href="#test">Test</a> •
  <a href="#guvenlik">Guvenlik</a>
</p>

---

## Proje Hakkinda

Memory Manager, kisisel fotograflarinizi, ses kayitlarinizi ve notlarinizi **yapay zeka ile indeksleyen**, **dogal dil ile aratan** ve **tum veriyi yerel bilgisayarinizda sifreleyerek saklayan** bir kisisel hafiza yoneticisidir.

### Cozulen Problem

Kisisel anilar binlerce dosya arasinda kaybolur. "Gecen yaz plajda cekilmis o fotografi" bulmak icin klasorleri tek tek acmak zorundasinizdir. Memory Manager, **"plajda gun batimi"** yazip ilgili fotograflari bulmanizi saglar — dosya adina degil, **icerigi anlayarak**.

### Temel Felsefe

| Ilke | Aciklama |
|------|----------|
| **Privacy-First** | Her veri islemi `has_consent` kontrolunden gecer. Riza yoksa veri **var ama gorunmez**. |
| **Local-Only** | Hicbir veri buluta gitmez. Tum AI modelleri ve veriler yerel calisir. |
| **Encryption-Default** | Dosyalar ve transkriptler Fernet (AES-128-CBC) ile sifrelenir. |
| **Semantic Search** | Dosya adina degil, icerigi anlayarak arama yapar. |

---

## Ozellikler

### AI Destekli Semantik Arama

| Arama Turu | Aciklama | Teknoloji |
|------------|----------|-----------|
| **Metin Aramasi** | "Plajda gun batimi" yaz, ilgili fotograflari bul | CLIP (multilingual) + FAISS |
| **Zaman Aramasi** | Tarih araligi, yil, ay veya gun bazli filtrele | SQLAlchemy query |
| **Konum Aramasi** | GPS koordinati veya sehir adi ile ara | Geopy jeodezik mesafe |
| **Birlesik Arama** | Tum filtreleri kesistirerek birlikte kullan | SearchEngine koordinatoru |

### Akilli Veri Isleme

```
Fotograf → EXIF cikar → Yon duzelt → CLIP vektor uret → Sifrele → DB kaydet → FAISS'e ekle
Ses      → Whisper transkript → Sifrele → DB kaydet → SBERT vektoru → FAISS indeksi
Arama    → CLIP multilingual text encode → FAISS ara → MIN_SCORE filtrele → Consent filtrele → Sonuc
```

### Multimodal Embedding Sistemi (Dual-Model CLIP)

```
┌─────────────────────────────────────────────────────┐
│         CLIP IMAGE MODEL (clip-ViT-B-32)             │
│         Fotograf → 512 boyutlu vektor                │
│         Import sirasinda otomatik uretilir           │
└───────────────────────┬─────────────────────────────┘
                        │
                        ├──→ FAISS FlatL2 Index (512D)
                        │         Semantik arama
                        │
┌───────────────────────┴─────────────────────────────┐
│  CLIP TEXT MODEL (clip-ViT-B-32-multilingual-v1)     │
│         Metin → 512 boyutlu vektor (68 dil)          │
│         Turkce, Ingilizce, Almanca, ... destekli     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│            SBERT (all-MiniLM-L6-v2)                  │
│           Metin → 384 boyutlu vektor                 │
└─────────────────────────────────────────────────────┘
```

**Neden iki ayri CLIP modeli?**
- `clip-ViT-B-32`: Orijinal CLIP — gorsel encoding icin optimum, ama sadece Ingilizce metin destekler
- `clip-ViT-B-32-multilingual-v1`: 68 dilde metin encoding, ama gorsel encoding desteklemez
- Cozum: Fotograflar icin orijinal, arama metni icin multilingual model kullanilir

### Guvenlik Katmani

- **Fernet Sifreleme**: Tum dosyalar ve transkriptler AES-128-CBC ile diskte sifrelenir
- **Riza Yonetimi**: Her Item icin `has_consent` bayragi — rizasi olmayan veri arama sonuclarinda gorunmez
- **Guvenli Silme**: Dosyalar silinmeden once uzerine rastgele veri yazilir (`secure_delete`)
- **Denetim Logu**: Tum gizlilik islemleri `privacy_audit.log` dosyasina kaydedilir
- **Anahtar Korumasi**: `secret.key` dosyasi OS seviyesinde `chmod 600` ile korunur

---

## Mimari

### Katmanli Yapi

```
┌─────────────────────────────────────────────────────────┐
│                      KULLANICI                           │
│               (Flutter UI + FastAPI Backend)              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐              │
│  │  SEARCH  │  │CLUSTERING│  │FLASHCARDS │              │
│  │  ENGINE  │  │(Asama 8) │  │(Asama 10) │              │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘              │
│       │              │              │                     │
├───────┼──────────────┼──────────────┼─────────────────────┤
│       ▼              ▼              ▼                     │
│  ┌──────────────────────────────────────────────┐        │
│  │             EMBEDDING KATMANI                 │        │
│  │  CLIP (512D)  │  SBERT (384D)  │  FAISS      │        │
│  │  Fotograf→Vec │  Metin→Vec     │  Vec→Arama  │        │
│  └──────────────────────────────────────────────┘        │
│       ▲              ▲              ▲                     │
├───────┼──────────────┼──────────────┼─────────────────────┤
│       │              │              │                     │
│  ┌──────────────────────────────────────────────┐        │
│  │            INGESTION KATMANI                  │        │
│  │  PhotoImporter │ AudioProcessor │ EXIFExtract │        │
│  └──────────────────────────────────────────────┘        │
│       ▲              ▲              ▲                     │
├───────┼──────────────┼──────────────┼─────────────────────┤
│       │              │              │                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │ ENCRYPTION │  │  PRIVACY   │  │  DATABASE  │         │
│  │ (Fernet)   │  │ (Consent)  │  │  (SQLite)  │         │
│  └────────────┘  └────────────┘  └────────────┘         │
│                                                          │
│  ┌──────────────────────────────────────────────┐        │
│  │             config.py (Config)                │        │
│  │      Tum sabitler, logging ayarlari           │        │
│  └──────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### Veritabani Semasi

```
┌────────────┐       ┌────────────┐       ┌────────────┐
│   Item     │ N───1 │   Event    │ 1───N │ Flashcard  │
│────────────│       │────────────│       │────────────│
│ item_id PK │       │ event_id PK│       │flashcard_id│
│ file_path  │       │ title      │       │ question   │
│ file_hash  │       │ start_date │       │ answer     │
│ type       │       │ end_date   │       │ event_id FK│
│ has_consent│       │ main_loc   │       └─────┬──────┘
│ is_rotated │       │ summary    │             │
│ created_at │       │cover_id FK │             │ 1───N
│ lat, lng   │       └────────────┘       ┌─────┴──────┐
│ transcript │                            │ ReviewLog  │
│ faiss_id   │                            │────────────│
│ event_id FK│                            │ log_id PK  │
└────────────┘                            │ review_date│
                                          │ user_rating│
                                          │next_review │
                                          └────────────┘
```

---

## Tech Stack

| Katman | Teknoloji | Rol |
|--------|-----------|-----|
| **Veritabani** | SQLAlchemy + SQLite | ORM, 4 tablo, iliskisel veri |
| **Sifreleme** | cryptography (Fernet) | AES-128-CBC simetrik sifreleme |
| **Goruntu AI** | CLIP (ViT-B-32) | Fotograf → 512 boyutlu vektor |
| **Metin AI (Arama)** | CLIP (ViT-B-32-multilingual-v1) | Metin → 512D vektor (68 dil, Turkce dahil) |
| **Metin AI (Embedding)** | SBERT (all-MiniLM-L6-v2) | Metin → 384 boyutlu vektor |
| **Ses AI** | OpenAI Whisper | Ses → metin transkripsiyonu |
| **Vektor Arama** | FAISS (Meta) | Milyonlarca vektorde milisaniye arama |
| **Konum** | Geopy + Nominatim | GPS koordinat ↔ sehir adi donusumu |
| **Goruntu Isleme** | Pillow (PIL) | EXIF okuma, yon duzeltme, boyut kucultme |
| **Kumeleme** | scikit-learn (DBSCAN) | Zaman/konum bazli olay kumeleme |
| **Yapilandirma** | config.py (Config sinifi) | Tum sabitler tek merkezde |
| **Backend API** | FastAPI + Uvicorn | REST API, CORS, Swagger UI |
| **UI** | Flutter (Dart) | Cross-platform masaustu uygulamasi |

---

## Proje Yapisi

```
memory-manager/
├── config.py                        # Merkezi yapilandirma (tum sabitler)
├── database/
│   ├── __init__.py
│   └── schema.py                    # Item, Event, Flashcard, ReviewLog ORM
├── security/
│   ├── encryption_manager.py        # Fernet sifreleme/cozme (metin + dosya)
│   └── security_manager.py          # Riza yonetimi, guvenli silme, audit log
├── src/
│   ├── ingestion/                   # Veri alma pipeline'i
│   │   ├── exif_extractor.py        # SHA256 hash, EXIF tarih/GPS/kamera
│   │   ├── image_processer.py       # Yon duzeltme, boyut optimizasyonu
│   │   ├── photo_importer.py        # Toplu import orkestrasyonu
│   │   └── audio_processor.py       # Whisper transkript + sifreleme
│   ├── embedding/                   # Vektor uretme ve arama
│   │   ├── clip_embedder.py         # CLIP gorsel embedding (512D)
│   │   ├── sbert_embedder.py        # SBERT metin embedding (384D)
│   │   ├── multimodal_fuser.py      # Gorsel+metin birlestirme (896D)
│   │   └── faiss_manager.py         # FAISS indeks yonetimi (FlatL2/HNSW)
│   ├── search/                      # Arama motorlari
│   │   ├── text_search.py           # Semantik metin/gorsel arama
│   │   ├── time_search.py           # Tarih bazli arama
│   │   ├── location_search.py       # Konum bazli arama (Geopy)
│   │   └── search_engine.py         # Birlesik arama koordinatoru
│   ├── clustering/                  # Olay kumeleme (iskelet hazir)
│   │   ├── dbscan_clusterer.py      # DBSCAN zaman/konum kumeleme
│   │   ├── refinement_clusterer.py  # Embedding bazli ince ayar
│   │   ├── cover_photo_selector.py  # Kapak fotografi secimi
│   │   ├── event_clusterer.py       # Kumeleme koordinatoru
│   │   └── summarizer.py            # Olay ozetleme (template/LLM)
│   ├── flashcards/                  # Flashcard & SM-2 (iskelet hazir)
│   │   ├── flashcard_generator.py   # Event'ten soru-cevap uretimi
│   │   └── sm2_scheduler.py         # SM-2 aralikli tekrar algoritmasi
│   └── ui/                          # Kullanici arayuzu (iskelet hazir)
│       └── timeline_page.py         # Zaman cizelgesi goruntuleme
├── api/                             # FastAPI REST API katmani
│   ├── main.py                      # FastAPI app, CORS, router kaydi
│   ├── dependencies.py              # DB session, CLIPEmbedder, FaissManager singleton'lari
│   ├── models/                      # Pydantic request/response semalari
│   │   ├── item_models.py           # Item DTO'lari
│   │   ├── event_models.py          # Event DTO'lari
│   │   ├── search_models.py         # Arama DTO'lari
│   │   ├── flashcard_models.py      # Flashcard DTO'lari
│   │   └── common_models.py         # Ortak response modelleri
│   └── routers/                     # REST endpoint'leri
│       ├── import_router.py         # /api/import
│       ├── gallery_router.py        # /api/gallery
│       ├── search_router.py         # /api/search
│       ├── privacy_router.py        # /api/privacy
│       ├── events_router.py         # /api/events
│       ├── flashcard_router.py      # /api/flashcards
│       ├── timeline_router.py       # /api/timeline
│       └── settings_router.py       # /api/settings
├── flutter_app/                     # Flutter masaustu UI (iskelet hazir)
│   ├── pubspec.yaml                 # Flutter bagimliliklari
│   └── lib/
│       ├── main.dart                # Uygulama giris noktasi
│       ├── app.dart                 # MaterialApp + GoRouter
│       ├── theme/                   # Tema dosyalari
│       │   ├── colors.dart          # Renk paleti
│       │   ├── typography.dart      # Yazi tipleri
│       │   └── app_theme.dart       # ThemeData birlestirme
│       ├── models/                  # Dart veri modelleri
│       ├── services/                # API istemci servisleri
│       ├── providers/               # Riverpod state yonetimi
│       ├── screens/                 # 12 ekran (Home, Gallery, Search, ...)
│       └── widgets/                 # Tekrar kullanilabilir widget'lar
├── models/                          # AI model dosyalari
│   ├── clip/                        # CLIP model agirliklari
│   ├── sbert/                       # SBERT model agirliklari
│   └── whisper/                     # Whisper model agirliklari
├── data/
│   ├── raw/                         # Ham fotograflar ve sesler
│   ├── processed/                   # Islenmis metadata
│   └── encrypted/                   # Sifreli yedekler
├── tests/                           # Test suite
├── requirements.txt
├── pyproject.toml                   # pytest yapilandirmasi
└── .gitignore
```

---

## Kurulum

### Gereksinimler

- Python `>=3.10`
- pip
- (Opsiyonel) CUDA destekli GPU — AI modelleri icin hiz artisi saglar

### Adimlar

```bash
# 1. Repoyu klonlayin
git clone https://github.com/KULLANICI_ADINIZ/memory-manager.git
cd memory-manager

# 2. Sanal ortami olusturun ve aktif edin
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Mac/Linux:
source .venv/bin/activate

# 3. Bagimliliklari yukleyin
pip install -r requirements.txt

# 4. (Ilk calistirmada) AI modelleri otomatik indirilir
# CLIP: ~400MB, SBERT: ~90MB, Whisper: ~500MB (model boyutuna gore)
```

### Ortam Degiskenleri

Projeye ozel `.env` dosyasina gerek yoktur. Tum yapilandirma `config.py` icerisindeki `Config` sinifinda merkezilestirmistir.

> **Onemli**: `secret.key` dosyasi ilk calistirmada otomatik uretilir. Bu dosya kaybolursa **tum sifreli veriler kalici olarak erisilemez** hale gelir. Yedek almaniz onemle onerilir.

---

## Veri Akis Diyagramlari

### Fotograf Import Pipeline

```
[Kullanici: "Bu klasoru import et" + user_consent=True]
        │
        ▼
┌─ find_image_files() ──────────────────────────────┐
│  Klasoru tara, .jpg/.jpeg/.png/.heic filtrele      │
└───────────────────────┬───────────────────────────┘
                        │ Her dosya icin:
                        ▼
┌─ Riza kontrolu ──────────────────────────────────┐
│  user_consent=False → return 'no_consent'          │
└───────────────────────┬───────────────────────────┘
                        ▼
┌─ calculate_file_hash() ──────────────────────────┐
│  SHA256 hash → DB'de ayni hash var mi?             │
│  Varsa → return 'duplicate'                        │
└───────────────────────┬───────────────────────────┘
                        ▼
┌─ extract_metadata() ─────────────────────────────┐
│  EXIF: tarih, GPS koordinatlari, kamera bilgisi    │
└───────────────────────┬───────────────────────────┘
                        ▼
┌─ process_image() ────────────────────────────────┐
│  1. fix_orientation() → EXIF yon duzeltme          │
│  2. resize_if_needed() → max 2000px                │
└───────────────────────┬───────────────────────────┘
                        ▼
┌─ CLIP embedding uret ───────────────────────────┐
│  clip-ViT-B-32 → 512D vektor (raw image'den)      │
│  Sifreleme ONCESI yapilir (decrypt gerektirmez)    │
└───────────────────────┬───────────────────────────┘
                        ▼
┌─ encrypt_file() ─────────────────────────────────┐
│  Fernet ile dosyayi yerinde sifrele                │
└───────────────────────┬───────────────────────────┘
                        ▼
┌─ add_photo_to_database() ────────────────────────┐
│  Item olustur + DB'ye commit → item_id al          │
└───────────────────────┬───────────────────────────┘
                        ▼
┌─ FAISS'e ekle ───────────────────────────────────┐
│  faiss_manager.add_embeddings(vec, [item_id])      │
│  Item.faiss_index_id guncelle                      │
└───────────────────────┬───────────────────────────┘
                        ▼
                  return 'imported'
```

### Arama Pipeline (Semantik Arama — TAMAMLANDI)

```
[Kullanici: "plajda gun batimi"]
        │
        ▼
┌─ Sorgu vektoru olustur ─────────────────────────┐
│  CLIP multilingual encode_text() → 512D vektor    │
│  (clip-ViT-B-32-multilingual-v1 — 68 dil)        │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─ FAISS vektor arama ────────────────────────────┐
│  faiss_manager.search(clip_vec, k=min(200, N))    │
│  En yakin komsulari bul (L2 distance)             │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─ Skor hesaplama ────────────────────────────────┐
│  score = max(0, 1 - distance / 2)                 │
│  MIN_SCORE = 0.24 altindakileri filtrele          │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─ DB filtreleri ─────────────────────────────────┐
│  has_consent == True (KRITIK)                     │
│  + opsiyonel tarih araligi filtresi               │
│  + opsiyonel konum/yaricap filtresi               │
└───────────────────────┬─────────────────────────┘
                        ▼
              return results (skora gore sirali)

[Query yoksa veya FAISS bossa → DB LIKE fallback]
```

---

## Guvenlik

### Sifreleme Altyapisi

```
Fernet = AES-128-CBC + HMAC-SHA256 + Timestamp

Sifreleme:  plaintext → AES-CBC encrypt → HMAC sign → base64 encode → ciphertext
Cozumleme:  ciphertext → base64 decode → HMAC verify → AES-CBC decrypt → plaintext
```

### Guvenlik Entegrasyon Haritasi

| Modul | check_consent | encrypt | decrypt | has_consent filtre |
|-------|:---:|:---:|:---:|:---:|
| photo_importer | **Var** | **Var** (dosya) | - | - |
| audio_processor | **Var** | **Var** (transkript) | - | - |
| clip_embedder | - | - | **Var** (dosya) | - |
| text_search | - | - | **Var** (transkript) | **Var** |
| time_search | - | - | - | **Var** |
| location_search | - | - | - | **Var** |
| event_clusterer | Yapilacak | - | Yapilacak | Yapilacak |

### Kritik Kurallar

1. **`has_consent` filtresi**: Item verisi donduren **her** fonksiyon `has_consent == True` filtresi icermelidir
2. **`secret.key` korumasi**: Bu dosya kaybolursa tum sifreli veriler **geri donusumsuz** erislemez olur
3. **Import sirasi**: EXIF cikar → Goruntu isle → CLIP vektor → Sifrele → DB kaydet → FAISS ekle (sira degistirilemez)
4. **FAISS normalizasyon**: `faiss.normalize_L2()` atlanirsa arama sonuclari anlamsiz olur
5. **ID mapping sync**: FAISS indeksi ve `.pkl` mapping dosyasi her zaman birlikte guncellenir

---

## Yol Haritasi

### Tamamlanan Asamalar

| Asama | Aciklama | Durum |
|-------|----------|-------|
| **1** | Proje Kurulumu — klasor yapisi, bagimliliklar, .gitignore | **Tamamlandi** |
| **2** | Gizlilik & Sifreleme — Fernet sifreleme, riza yonetimi, guvenli silme | **Tamamlandi** |
| **3** | Veritabani & Sema — Item, Event, Flashcard, ReviewLog ORM modelleri | **Tamamlandi** |
| **4** | Fotograf Ice Aktarma & EXIF — hash, tarih, GPS, toplu import | **Tamamlandi** |
| **5** | Ses Isleme — Whisper transkript, sifreli kayit, batch isleme | **Tamamlandi** |
| **6** | Embedding & Multimodal Fusion — CLIP 512D, SBERT 384D, Fuser 896D, FAISS | **Tamamlandi** |
| **7** | Arama Motoru — semantik, zaman, konum, birlesik arama | **Tamamlandi** |

### Tamamlanan Ek Asamalar

| Asama | Aciklama | Durum |
|-------|----------|-------|
| **UI Faz 0-3** | Flutter UI + FastAPI backend — import, galeri, arama, gizlilik, dashboard ekranlari | **Tamamlandi** |
| **UI Faz 3.5** | CLIP/FAISS semantik arama entegrasyonu — dual-model CLIP, import pipeline, reindex | **Tamamlandi** |
| **13** | Test Suite — 163 test passed, 0 failed | **Tamamlandi** |

### Devam Eden ve Planlanan Asamalar

| Asama | Aciklama | Durum |
|-------|----------|-------|
| **BUG** | Ses/transkripsiyon arama birlestirme — semantik arama erken return edip DB fallback'i atliyor | **Oncelikli** |
| **8** | Olay Kumeleme — DBSCAN ile zaman/konum kumeleme, kapak fotografi secimi | **Sirada** (iskelet hazir) |
| **9** | Ozetleme — Olay bazli metin ozetleme | **Sirada** (iskelet hazir) |
| **10** | Flashcard & SM-2 — Araliklarla tekrar sistemi | **Sirada** (iskelet hazir) |
| **11** | Zaman Cizelgesi — Kronolojik goruntuleyici | **Sirada** (iskelet hazir) |
| **14** | Yedekleme & Disa Aktarma — Sifreli export | Planlandi |
| **15** | Performans Optimizasyonu — batch embedding, cache, FAISS index tipi | Planlandi |
| **—** | CLIP ViT-B-16 model yukseltmesi (daha kaliteli vektor, ayni boyut) | Planlandi |
| **—** | Kullaniciya "Arama Kalitesi" ayari (Hizli/Dengeli/En Iyi) | Planlandi |

### UI Mimarisi: Flutter + FastAPI (AKTIF)

```
┌─────────────────────────────────────────────────────┐
│               FLUTTER UI (Dart)                      │
│   12 Ekran: Dashboard, Galeri, Arama, Timeline,     │
│   Olaylar, Flashcard, Import, Gizlilik, Ayarlar     │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (localhost:8000)
┌──────────────────────┴──────────────────────────────┐
│               FASTAPI KATMANI (Python)               │
│   REST endpoints + CLIPEmbedder + FaissManager       │
│   Semantik arama, reindex, import pipeline           │
└──────────────────────┬──────────────────────────────┘
                       │ Direct Python calls
┌──────────────────────┴──────────────────────────────┐
│            MEVCUT BACKEND (Python)                    │
│   PhotoImporter | EncryptionManager | PrivacyManager │
└─────────────────────────────────────────────────────┘
```

---

## Test

### Testleri Calistirma

```bash
# Tum testleri calistir
pytest

# Coverage raporu ile
pytest --cov=src --cov=database --cov=security --cov-report=term-missing

# Tek bir modulu calistir
pytest tests/test_encryption.py -v

# Sadece privacy testleri
pytest -k "consent" -v
```

### Mock Kurallari

| Modul | Gercek mi? | Neden? |
|-------|------------|--------|
| SQLite DB | Gercek (in-memory) | Hizli, izole, guvenilir |
| FAISS | Gercek | CPU'da calisir, hafif |
| Fernet | Gercek | CPU'da calisir, hizli |
| PIL/Pillow | Gercek | CPU'da calisir |
| Whisper | **Mock** | 500MB+ model, GPU gerektirir |
| CLIP | **Mock** | 500MB+ model, GPU onerilir |
| SBERT | **Mock** | 250MB+ model |
| Geopy | **Mock** | Internet baglantisi gerektirir |

---

## Kodlama Standartlari

### Isimlendirme Kurallari

| Oge | Kural | Ornek |
|-----|-------|-------|
| Dosya adlari | snake_case | `audio_processor.py` |
| Sinif adlari | PascalCase | `AudioProcessor` |
| Metod adlari | snake_case | `encode_text()` |
| Sabitler | UPPER_SNAKE_CASE | `Config.SBERT_MODEL_NAME` |
| Test dosyalari | `test_` + modul adi | `test_audio.py` |

### Config Entegrasyonu

Tum sabit degerler `config.py` icerisindeki `Config` sinifinda merkezilestirmistir. Modullerde hardcoded deger **kullanilmaz**:

```python
# DOGRU:
def __init__(self, image_model: str = Config.CLIP_IMAGE_MODEL,
             text_model: str = Config.CLIP_TEXT_MODEL):
    self.image_model = image_model
    self.text_model = text_model

# YANLIS:
def __init__(self, model_name: str = "clip-ViT-B-32"):
    self.model_name = model_name
```

### PR Kabul Kriterleri

1. Yeni eklenen her fonksiyon icin en az 1 test yazilmis olmali
2. Item verisi donduren fonksiyonlarda `has_consent == True` filtresi olmali
3. Hardcoded degerler yerine Config sabitleri kullanilmali
4. `logger` kullanilmali, `print()` kullanilmamali
5. Docstring yazilmis olmali

---

## Ilgili Dokumanlar

| Dokuman | Aciklama |
|---------|----------|
| [TECHNICAL_ORIENTATION.md](TECHNICAL_ORIENTATION.md) | Sistemin DNA'si — mimari analiz, kritik mekanizmalar, kirmizi cizgiler |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Asama bazinda detayli modul dokumantasyonu |
| [PLAN.md](PLAN.md) | Test altyapisi ve profesyonellesme plani |
| [UI_GUIDELINE.md](UI_GUIDELINE.md) | Flutter + FastAPI UI tasarim ve uygulama rehberi |
| [TEAM_B_TEST_GUIDE.md](TEAM_B_TEST_GUIDE.md) | Test yazim rehberi — 106 test plani |

---

## Katkida Bulunma

Projeye katkida bulunmak icin asagidaki adimlari takip edin.

### Genel Kurallar

1. **Her ozellik icin ayri branch** acilmalidir
2. **Commit mesajlari** anlamli ve Turkce olmalidir
3. **Code review** olmadan `main` branch'e merge yapilmaz
4. Tum PR'lar proje yoneticisi tarafindan onaylanmalidir

### Fork ve Kurulum (Ilk Kez)

```bash
# 1. GitHub'da sag ustteki "Fork" butonuna tiklayin

# 2. Fork'unuzu klonlayin
git clone https://github.com/KULLANICI_ADINIZ/memory-manager.git
cd memory-manager

# 3. Ana repo'yu upstream olarak ekleyin
git remote add upstream https://github.com/semanur-teke/memory-manager.git

# 4. Remote'lari kontrol edin
git remote -v
# origin    https://github.com/KULLANICI_ADINIZ/memory-manager.git (fetch)
# origin    https://github.com/KULLANICI_ADINIZ/memory-manager.git (push)
# upstream  https://github.com/semanur-teke/memory-manager.git (fetch)
# upstream  https://github.com/semanur-teke/memory-manager.git (push)

# 5. Sanal ortami olusturun ve bagimliliklari yukleyin
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### Yeni Ozellik Gelistirme

```bash
# 1. Main branch'i guncelleyin
git checkout main
git fetch upstream
git merge upstream/main
git push origin main

# 2. Gorevinize uygun branch olusturun
git checkout -b feature/gorev-adi

# Ornek branch isimleri:
# feature/event-clustering
# feature/flashcard-sm2
# feature/flutter-gallery-screen
# fix/faiss-search-bug
# refactor/search-engine
# test/privacy-tests
```

### Gelistirme ve Commit

```bash
# Degisikliklerinizi yapin...

# Degisiklikleri stage'leyin
git add .

# Anlamli commit mesaji yazin (Turkce)
git commit -m "feat: DBSCAN kumeleme algoritmasi tamamlandi"

# Commit mesaj formatlari:
# feat: yeni ozellik eklendi
# fix: hata duzeltildi
# refactor: kod iyilestirmesi yapildi
# docs: dokuman guncellendi
# test: test eklendi
# style: kod formati duzenlendi
```

### Push ve Pull Request

```bash
# Branch'inizi kendi fork'unuza push'layin
git push origin feature/gorev-adi
```

Ardindan GitHub'da:

1. Fork'unuza gidin
2. **"Compare & pull request"** butonuna tiklayin
3. PR aciklamasini doldurun (asagidaki sablonu kullanin)
4. **"Create pull request"** butonuna tiklayin

### Pull Request Sablonu

```markdown
## Aciklama
Bu PR ile ne yapildigini kisaca aciklayin.

## Ilgili Asama
- [ ] Asama 8: Olay Kumeleme
- [ ] Asama 9: Ozetleme
- [ ] Asama 10: Flashcard & SM-2
- [ ] Asama 12: UI (Flutter/FastAPI)
- [ ] Asama 13: Test Suite
- [ ] Diger: ____

## Degisiklik Turu
- [ ] Yeni ozellik (feat)
- [ ] Hata duzeltme (fix)
- [ ] Refactoring
- [ ] Test

## Checklist
- [ ] Kod calisiyor ve hata vermiyor
- [ ] Yeni fonksiyonlar icin test yazildi
- [ ] Item verisi donduren fonksiyonlarda has_consent filtresi var
- [ ] Hardcoded deger yok, Config sabitleri kullanildi
- [ ] logger kullanildi, print() kullanilmadi
- [ ] Docstring yazildi
```

### Fork'u Guncel Tutma

Ana repo guncellendiginde fork'unuzu senkronize edin:

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

### Bug Raporu

Hata bildirmek icin GitHub **Issues** sekmesinden yeni issue acin:

```markdown
## Hata Raporu

### Aciklama
Hatayi kisaca aciklayin.

### Tekrarlama Adimlari
1. Suraya git...
2. Sunu calistir...
3. Hata olusuyor

### Beklenen Davranis
Ne olmasi gerekiyordu?

### Gerceklesen Davranis
Ne oldu?

### Ortam
- Python version:
- OS:
- GPU var mi:
```

### Yeni Ozellik Talebi

```markdown
## Ozellik Onerisi

### Aciklama
Ozelligi detaylica aciklayin.

### Motivasyon
Bu ozellik neden gerekli? Hangi sorunu cozuyor?

### Onerilen Cozum
Nasil implement edilebilecegine dair fikirleriniz.
```

### Code Review Sureci

1. PR acildiginda proje yoneticisi review eder
2. Gerekirse degisiklik talep edilir (Request Changes)
3. Duzeltmeler yapilir ve tekrar review istenir
4. Onay alindiktan sonra **Squash and Merge** yapilir

#### Review Kriterleri

- [ ] Kod okunabilir ve anlasilir mi?
- [ ] `has_consent` filtresi gerekli yerlerde var mi?
- [ ] Config sabitleri kullanilmis mi?
- [ ] Gereksiz kod tekrari var mi?
- [ ] Test yazilmis mi?
- [ ] Edge case'ler dusunulmus mu?

---

## Lisans

MIT License

---

<p align="center">
  <strong>Anilarin sana ait. Guvende ve akilli.</strong>
</p>
