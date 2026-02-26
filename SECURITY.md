# Guvenlik Politikasi (Security Policy)

## Desteklenen Surumleri

| Surum | Destek Durumu |
|-------|---------------|
| Son surum (main branch) | Destekleniyor |

## Guvenlik Acigi Bildirimi

Bir guvenlik acigi kesfettiyseniz, lutfen **kamuya acik bir issue ACMAYIN**. Bunun yerine:

1. Detayli aciklamayi iceren bir e-posta gonderin
2. Acigi yeniden uretmek icin gereken adimlari belirtin
3. Varsa olasi etkiyi ve ciddiyetini belirtin

Bildiriminizi aldiktan sonra 48 saat icerisinde donus yapilacaktir.

## Guvenlik Mimarisi

Memory Manager asagidaki guvenlik onlemlerini uygular:

### Sifreleme
- **Fernet (AES-128-CBC + HMAC-SHA256)**: Tum dosyalar ve transkriptler diskte sifrelenir
- `secret.key` dosyasi ilk calistirmada otomatik uretilir
- Anahtar dosyasi OS seviyesinde `chmod 600` ile korunur

### Riza Yonetimi (Privacy)
- Her Item icin `has_consent` bayragi
- Rizasi olmayan veri arama sonuclarinda ve galerinde **gorunmez**
- Tum gizlilik islemleri `privacy_audit.log` dosyasina kaydedilir

### Guvenli Silme
- Dosyalar silinmeden once uzerine rastgele veri yazilir (`secure_delete`)
- DB kaydi ve FAISS indeksi de temizlenir

### Yerel Calisma (Local-Only)
- Hicbir veri buluta gitmez
- Tum AI modelleri yerel calisir
- API sadece `localhost` uzerinden erisime aciktir

## Bilinen Guvenlik Sinirlari

- Fernet sifreleme AES-128 kullanir (AES-256 degil). Cogu kullanim senaryosu icin yeterlidir.
- `secret.key` dosyasi kaybolursa tum sifreli veriler **kalici olarak erisilemez** hale gelir. Yedek alinmasi onemle onerilir.
- Thumbnail cache bellekte tutulur, diske yazilmaz. Uygulama kapaninca temizlenir.
