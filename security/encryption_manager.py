# encryption_manager.py

import os
import stat
import logging
from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)

class EncryptionManager:
    """
    Dosya ve veritabanı verilerini şifreleme/şifre çözme işlemlerini yönetir.
    """

    def __init__(self, key_path: str = Config.SECRET_KEY_PATH):
        self.key_path = Path(key_path)
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def _load_or_generate_key(self) -> bytes:
        """Anahtarı yükler veya yoksa yeni bir tane oluşturur."""
        if self.key_path.exists():
            return self.key_path.read_bytes()

        key = Fernet.generate_key()
        self.key_path.write_bytes(key)
        # Dosya izinlerini sadece sahibine oku/yaz olarak ayarla (diğerleri erişemez)
        os.chmod(self.key_path, stat.S_IRUSR | stat.S_IWUSR)
        return key

    def encrypt_string(self, plain_text: str) -> str:
        """Metin verisini (özet, transkript vb.) şifreler."""
        if not plain_text:
            return plain_text
        return self.cipher.encrypt(plain_text.encode()).decode()

    def decrypt_string(self, encrypted_text: str) -> str:
        """Şifrelenmiş metnin şifresini çözer."""
        if not encrypted_text:
            return encrypted_text
        return self.cipher.decrypt(encrypted_text.encode()).decode()

    def encrypt_file(self, file_path: str):
        """Diskteki bir dosyayı (fotoğraf, ses vb.) yerinde şifreler."""
        path = Path(file_path)
        if path.exists():
            data = path.read_bytes()
            # Çift şifreleme koruması: zaten şifreli mi kontrol et
            try:
                self.cipher.decrypt(data)
                logger.warning(f"Dosya zaten şifreli, tekrar şifrelenmedi: {file_path}")
                return
            except InvalidToken:
                pass  # Şifreli değil, şifrelemeye devam
            encrypted_data = self.cipher.encrypt(data)
            path.write_bytes(encrypted_data)

    def decrypt_file(self, file_path: str) -> bytes:
        """Şifreli dosyanın verisini okur ve şifresini çözer."""
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Dosya bulunamadı: {file_path}")
            return b""
        try:
            encrypted_data = path.read_bytes()
            return self.cipher.decrypt(encrypted_data)
        except InvalidToken:
            logger.error(f"Şifre çözme başarısız (anahtar uyumsuz veya dosya bozuk): {file_path}")
            raise