# privacy_manager.py

import os
import logging
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from database.schema import Item  # Güncellediğimiz şemadan Item modelini alıyoruz

# Audit log (Denetim Kaydı) yapılandırması 
logging.basicConfig(
    filename='privacy_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PrivacyManager:
    """
    Kullanıcı rızası, güvenli silme ve denetim kayıtlarını yönetir. 
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session

    def check_consent(self, item_id: int) -> bool:
        """
        Bir veri işlenmeden önce rıza durumunu kontrol eder. [cite: 11, 112]
        Arama, gösterim ve dışa aktarma öncesi mutlaka çağrılmalıdır.
        """
        item = self.db.query(Item).filter(Item.item_id == item_id).first()
        if item and item.has_consent:
            self._log_action("CONSENT_CHECK", f"Item {item_id} erişim izni onaylandı.")
            return True
        
        self._log_action("CONSENT_DENIED", f"Item {item_id} için rıza bulunamadı!", level="warning")
        return False

    def set_consent(self, item_id: int, status: bool):
        """
        Kullanıcının rıza durumunu günceller. 
        """
        item = self.db.query(Item).filter(Item.item_id == item_id).first()
        if item:
            item.has_consent = status
            self.db.commit()
            action = "CONSENT_GRANTED" if status else "CONSENT_REVOKED"
            self._log_action(action, f"Item {item_id} rıza durumu {status} olarak güncellendi.")

    def secure_delete(self, file_path: str):
        """
        Dosyayı diskten güvenli bir şekilde siler. [cite: 11, 12]
        Dosyanın üzerine rastgele veri yazarak geri döndürülmesini zorlaştırır.
        """
        path = Path(file_path)
        if path.exists():
            try:
                # Dosya boyutunu al
                file_size = path.stat().st_size
                # Üzerine rastgele veri yaz (Güvenli Silme Mantığı) [cite: 10]
                with open(path, "ba+", buffering=0) as f:
                    f.write(os.urandom(file_size))
                
                # Dosyayı sil
                os.remove(path)
                self._log_action("SECURE_DELETE", f"Dosya başarıyla ve güvenli şekilde silindi: {file_path}")
                return True
            except Exception as e:
                self._log_action("DELETE_ERROR", f"Silme hatası: {str(e)}", level="error")
                return False
        return False

    def _log_action(self, action: str, details: str, level: str = "info"):
        """
        Gizlilikle ilgili tüm eylemleri denetim günlüğüne kaydeder. 
        """
        message = f"[{action}] {details}"
        if level == "warning":
            logging.warning(message)
        elif level == "error":
            logging.error(message)
        else:
            logging.info(message)