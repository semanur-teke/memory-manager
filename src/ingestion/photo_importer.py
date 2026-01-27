import os
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session

# 1. Veritabanı ve Güvenlik Modülleri (Kök dizinden)
from database.schema import Item 
from security.encryption_manager import EncryptionManager
from security.security_manager import PrivacyManager

# 2. Ingestion Modülleri (Aynı klasörde oldukları için bağıl import)
from .exif_extractor import EXIFExtractor 
from .image_processer import ImageProcessor

class PhotoImporter:
    """
    Fotoğrafları toplu olarak içe aktarır, işler ve güvenli şekilde saklar[cite: 28].
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.exif_extractor = EXIFExtractor()
        self.processor = ImageProcessor()
        self.privacy = PrivacyManager(db_session)
        self.encryption = EncryptionManager()
        self.supported_formats = {".jpg", ".jpeg", ".png", ".heic"}

    def find_image_files(self, folder_path: Path, recursive: bool = True) -> List[Path]:
        """Klasördeki desteklenen görüntü dosyalarını bulur[cite: 24]."""
        pattern = "**/*" if recursive else "*"
        return [
            p for p in folder_path.glob(pattern) 
            if p.suffix.lower() in self.supported_formats
        ]

    def is_duplicate(self, file_hash: str) -> bool:
        """Dosya hash'i üzerinden kopya kontrolü yapar[cite: 24, 28]."""
        return self.db.query(Item).filter(Item.file_hash == file_hash).first() is not None

    def add_photo_to_database(self, image_path: Path, metadata: Dict, has_consent: bool, is_rotated: bool) -> Optional[int]:
        """Fotoğraf verilerini DB'ye kaydeder[cite: 16, 20]."""
        try:
            new_item = Item(
                file_path=str(image_path),
                file_hash=metadata["file_hash"],
                type="Photo",
                creation_datetime=metadata["created_at"] or datetime.now(),
                latitude=metadata.get("location_lat"),
                longitude=metadata.get("location_lng"),
                has_consent=has_consent, # Gizlilik bayrağı [cite: 16]
                is_rotated=is_rotated    # İşleme bayrağı [cite: 16]
            )
            self.db.add(new_item)
            self.db.commit()
            return new_item.item_id
        except Exception:
            self.db.rollback()
            return None

    def import_single_photo(self, image_path: Path, user_consent: bool) -> bool:
        """Tek bir fotoğrafı tüm güvenlik ve işleme adımlarından geçirir."""
        # 1. Privacy Check: Rıza yoksa işlem yapma [cite: 11, 112]
        if not user_consent:
            return False

        # 2. Duplicate Check: Hash hesapla ve kontrol et [cite: 24, 28]
        file_hash = self.exif_extractor.calculate_file_hash(image_path)
        if self.is_duplicate(file_hash):
            return False

        try:
            # 3. EXIF & Metadata çıkarma [cite: 26]
            metadata = self.exif_extractor.extract_metadata(image_path)
            metadata["file_hash"] = file_hash

            # 4. Image Processing: Yön düzeltme ve boyutlandırma [cite: 25, 27]
            rotation_success = self.processor.process_image(image_path)

            # 5. Encryption: Dosyayı diskte şifrele [cite: 13]
            self.encryption.encrypt_file(str(image_path))

            # 6. Database: Kaydı tamamla
            return self.add_photo_to_database(image_path, metadata, user_consent, rotation_success) is not None
        except Exception:
            return False

    def import_folder(self, folder_path: str, user_consent: bool, recursive: bool = True) -> Dict:
        """Klasördeki tüm fotoğrafları içe aktarır ve istatistik döner[cite: 28]."""
        folder = Path(folder_path)
        files = self.find_image_files(folder, recursive)
        
        stats = {
            'total_found': len(files),
            'imported': 0,
            'skipped_duplicates': 0,
            'errors': 0
        }

        for file_path in files:
            # Önce duplicate kontrolü (hız için DB sorgusu)
            temp_hash = self.exif_extractor.calculate_file_hash(file_path)
            if self.is_duplicate(temp_hash):
                stats['skipped_duplicates'] += 1
                continue

            if self.import_single_photo(file_path, user_consent):
                stats['imported'] += 1
            else:
                stats['errors'] += 1

        return stats