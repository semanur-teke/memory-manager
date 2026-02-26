# Katkida Bulunma Rehberi

Memory Manager'a katkida bulunmak istediginiz icin tesekkurler! Bu rehber, projeye nasil katkida bulunabileceginizi aciklar.

## Genel Kurallar

1. **Her ozellik icin ayri branch** acilmalidir
2. **Commit mesajlari** anlamli ve Turkce olmalidir
3. **Code review** olmadan `main` branch'e merge yapilmaz
4. Tum PR'lar proje yoneticisi tarafindan onaylanmalidir

## Fork ve Kurulum (Ilk Kez)

```bash
# 1. GitHub'da sag ustteki "Fork" butonuna tiklayin

# 2. Fork'unuzu klonlayin
git clone https://github.com/KULLANICI_ADINIZ/memory-manager.git
cd memory-manager

# 3. Ana repo'yu upstream olarak ekleyin
git remote add upstream https://github.com/semanur-teke/memory-manager.git

# 4. Sanal ortami olusturun ve bagimliliklari yukleyin
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Yeni Ozellik Gelistirme

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
# fix/faiss-search-bug
# test/privacy-tests
```

## Commit Mesaj Formati

```bash
git commit -m "feat: DBSCAN kumeleme algoritmasi tamamlandi"

# Commit mesaj tipleri:
# feat: yeni ozellik eklendi
# fix: hata duzeltildi
# refactor: kod iyilestirmesi yapildi
# docs: dokuman guncellendi
# test: test eklendi
# style: kod formati duzenlendi
```

## Pull Request Gonderme

```bash
# Branch'inizi fork'unuza push'layin
git push origin feature/gorev-adi
```

Ardindan GitHub'da **"Compare & pull request"** butonuna tiklayin ve PR sablonunu doldurun.

## PR Kabul Kriterleri

1. Yeni eklenen her fonksiyon icin en az 1 test yazilmis olmali
2. Item verisi donduren fonksiyonlarda `has_consent == True` filtresi olmali
3. Hardcoded degerler yerine `Config` sabitleri kullanilmali
4. `logger` kullanilmali, `print()` kullanilmamali
5. Docstring yazilmis olmali

## Code Review Sureci

1. PR acildiginda proje yoneticisi review eder
2. Gerekirse degisiklik talep edilir (Request Changes)
3. Duzeltmeler yapilir ve tekrar review istenir
4. Onay alindiktan sonra **Squash and Merge** yapilir

### Review Kriterleri

- Kod okunabilir ve anlasilir mi?
- `has_consent` filtresi gerekli yerlerde var mi?
- Config sabitleri kullanilmis mi?
- Gereksiz kod tekrari var mi?
- Test yazilmis mi?
- Edge case'ler dusunulmus mu?

## Fork'u Guncel Tutma

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

## Kodlama Standartlari

| Oge | Kural | Ornek |
|-----|-------|-------|
| Dosya adlari | snake_case | `audio_processor.py` |
| Sinif adlari | PascalCase | `AudioProcessor` |
| Metod adlari | snake_case | `encode_text()` |
| Sabitler | UPPER_SNAKE_CASE | `Config.SBERT_MODEL_NAME` |
| Test dosyalari | `test_` + modul adi | `test_audio.py` |

## Sorulariniz mi Var?

GitHub Issues uzerinden soru sorabilir veya oneri paylasiabilirsiniz.
