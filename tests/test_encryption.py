# tests/test_encryption.py
"""
EncryptionManager testleri.
Şifreleme/çözme döngüsünün doğruluğunu test eder.
"""

import os
import pytest
from pathlib import Path
from security.encryption_manager import EncryptionManager


class TestEncryptionManager:
    """EncryptionManager sınıfı testleri."""

    # --- ANAHTAR YÖNETİMİ ---

    def test_key_generation(self, temp_dir):
        """Anahtar dosyası yoksa otomatik oluşturulur."""
        key_path = str(temp_dir / "new_key.key")

        assert not Path(key_path).exists()

        em = EncryptionManager(key_path=key_path)

        assert Path(key_path).exists()
        assert len(Path(key_path).read_bytes()) > 0

    def test_key_persistence(self, temp_dir):
        """Aynı anahtarla iki kez açıldığında aynı anahtar kullanılır."""
        key_path = str(temp_dir / "persist_key.key")

        em1 = EncryptionManager(key_path=key_path)
        key1 = em1.key

        em2 = EncryptionManager(key_path=key_path)
        key2 = em2.key

        assert key1 == key2

    # --- METİN ŞİFRELEME ---

    def test_encrypt_decrypt_string(self, encryption_manager):
        """Metin şifreleme → çözme döngüsü orijinal metni verir."""
        original = "Merhaba Dünya! Türkçe karakterler: ğüşöç"

        encrypted = encryption_manager.encrypt_string(original)
        decrypted = encryption_manager.decrypt_string(encrypted)

        assert decrypted == original
        assert encrypted != original

    def test_encrypt_empty_string(self, encryption_manager):
        """Boş string şifrelenmeden geri döner."""
        result = encryption_manager.encrypt_string("")
        assert result == ""

    def test_encrypt_none(self, encryption_manager):
        """None değer şifrelenmeden geri döner."""
        result = encryption_manager.encrypt_string(None)
        assert result is None

    def test_decrypt_empty_string(self, encryption_manager):
        """Boş string çözümlenmeden geri döner."""
        result = encryption_manager.decrypt_string("")
        assert result == ""

    def test_different_texts_different_ciphertexts(self, encryption_manager):
        """Farklı metinler farklı şifreli çıktılar üretir."""
        enc1 = encryption_manager.encrypt_string("metin bir")
        enc2 = encryption_manager.encrypt_string("metin iki")

        assert enc1 != enc2

    def test_same_text_different_ciphertexts(self, encryption_manager):
        """Aynı metin bile her seferinde farklı şifreli çıktı üretir (Fernet IV)."""
        enc1 = encryption_manager.encrypt_string("aynı metin")
        enc2 = encryption_manager.encrypt_string("aynı metin")

        assert enc1 != enc2
        assert encryption_manager.decrypt_string(enc1) == encryption_manager.decrypt_string(enc2)

    def test_wrong_key_fails(self, temp_dir):
        """Farklı anahtarla şifre çözme başarısız olur."""
        em1 = EncryptionManager(key_path=str(temp_dir / "key1.key"))
        em2 = EncryptionManager(key_path=str(temp_dir / "key2.key"))

        encrypted = em1.encrypt_string("gizli veri")

        with pytest.raises(Exception):
            em2.decrypt_string(encrypted)

    # --- DOSYA ŞİFRELEME ---

    def test_encrypt_decrypt_file(self, encryption_manager, temp_dir):
        """Dosya şifreleme → çözme döngüsü orijinal veriyi verir."""
        file_path = temp_dir / "secret_doc.txt"
        original_content = b"Bu gizli bir dosyadir!"
        file_path.write_bytes(original_content)

        encryption_manager.encrypt_file(str(file_path))

        encrypted_content = file_path.read_bytes()
        assert encrypted_content != original_content

        decrypted_content = encryption_manager.decrypt_file(str(file_path))
        assert decrypted_content == original_content

    def test_encrypt_file_nonexistent(self, encryption_manager):
        """Olmayan dosya şifrelenmeye çalışılınca hata vermez."""
        encryption_manager.encrypt_file("/nonexistent/path/file.txt")

    def test_decrypt_file_nonexistent(self, encryption_manager):
        """Olmayan dosya çözülmeye çalışılınca boş bytes döner."""
        result = encryption_manager.decrypt_file("/nonexistent/path/file.txt")
        assert result == b""

    def test_encrypt_file_binary(self, encryption_manager, temp_dir):
        """Binary dosya (fotoğraf simülasyonu) şifreleme/çözme."""
        file_path = temp_dir / "photo.bin"
        original = os.urandom(1024)
        file_path.write_bytes(original)

        encryption_manager.encrypt_file(str(file_path))
        decrypted = encryption_manager.decrypt_file(str(file_path))

        assert decrypted == original

    def test_long_text_encryption(self, encryption_manager):
        """Uzun metin (transkript simülasyonu) şifreleme/çözme."""
        long_text = "Bu bir test cümlesidir. " * 500

        encrypted = encryption_manager.encrypt_string(long_text)
        decrypted = encryption_manager.decrypt_string(encrypted)

        assert decrypted == long_text
