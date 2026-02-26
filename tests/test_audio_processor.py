import pytest
import sys
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
    # 'base' modeli kullanıyoruz; daha hızlı sonuç için 'tiny' de seçilebilir.
    processor = AudioProcessor(db_session=db_session_dummy, model_size="small")
   
    # Test ses dosyasi
    test_ses_yolu = Path(r"C:\Users\sema\Desktop\test_images\Kayıt.m4a")
    if not test_ses_yolu.exists():
        # Alternatif konum
        test_ses_yolu = Path(r"C:\Users\sema\Desktop\memory-manager\test_data\Kayıt.m4a")
   
    # --- ASSERTIONS (Kontroller) ---
    # 1. Dosya sistemde mevcut mu?
    if not test_ses_yolu.exists():
        pytest.skip(f"Test ses dosyasi bulunamadi: {test_ses_yolu}")
   
    # 2. Transkripsiyon ve Şifreleme süreci (Encryption)
    sonuc_sifreli = processor.transcribe_audio(test_ses_yolu, item_id=1)
    assert sonuc_sifreli is not None, "HATA: Transkripsiyon sonucu None döndü!"
   
    # 3. Şifre Çözme süreci (Decryption)
    # EncryptionManager üzerinden şifreyi çözüyoruz
    orijinal_metin = processor.encryptor.decrypt_string(sonuc_sifreli)
   
    # Metin bütünlüğü kontrolleri
    assert isinstance(orijinal_metin, str), "HATA: Çözülen metin string tipinde değil!"
    assert len(orijinal_metin.strip()) > 0, "HATA: Çözülen metin boş çıktı!"
 
    # --- ÇIKTIYI GÖRÜNTÜLEME ---
    # Pytest normalde çıktıları yakalar; sys.stdout.flush() ile terminale zorluyoruz.
    print(f"\n\n" + "="*50)
    print(f"--- WHISPER TRANSKRİPT SONUCU ---")
    print(f"Metin: {orijinal_metin}")
    print("="*50 + "\n")
   
    sys.stdout.flush()