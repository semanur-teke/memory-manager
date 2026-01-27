import pytest
from pathlib import Path
from src.ingestion.audio_processor import AudioProcessor
from database.schema import Item
 
# Pytest'te testler 'test_' ile başlayan fonksiyonlar olmalıdır.
def test_audio_transcription_and_decryption():
    """
    Ses dosyasının transkripsiyonunu, şifrelenmesini ve
    şifresinin doğru çözüldüğünü test eder.
    """
    # --- SETUP (Hazırlık) ---
    db_session_dummy = None
    # Hızlı test için 'tiny' model önerilir, senin tercihin 'base'
    processor = AudioProcessor(db_session=db_session_dummy, model_size="base")
   
    test_ses_yolu = Path(r"C:\Users\tuana\OneDrive\Desktop\WhatsApp Audio 2026-01-27 at 22.48.40.mp4")
   
    # --- ASSERTIONS (Kontroller) ---
    # 1. Dosya gerçekten var mı?
    assert test_ses_yolu.exists(), f"HATA: Test dosyası bulunamadı: {test_ses_yolu}"
   
    # 2. Transkripsiyon ve Şifreleme süreci
    sonuc_sifreli = processor.transcribe_audio(test_ses_yolu, item_id=1)
    assert sonuc_sifreli is not None, "HATA: Transkripsiyon sonucu None döndü!"
   
    # 3. Şifre Çözme süreci
    orijinal_metin = processor.encryptor.decrypt_string(sonuc_sifreli)
   
    # Metin boş olmamalı ve string tipinde olmalı
    assert isinstance(orijinal_metin, str), "HATA: Çözülen metin string değil!"
    assert len(orijinal_metin.strip()) > 0, "HATA: Çözülen metin boş çıktı!"
 
    # Test başarılı olursa çıktıları görebilmek için (pytest -s ile)
    print(f"\n[Test Başarılı] Metin: {orijinal_metin}")