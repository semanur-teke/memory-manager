import os
import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from PIL import Image

logger = logging.getLogger(__name__)

# 1. Veritabanı ve Güvenlik Modülleri (Kök dizinden)
from database.schema import Item
from security.encryption_manager import EncryptionManager
from security.security_manager import PrivacyManager
from config import Config

# 2. Ingestion Modülleri (Aynı klasörde oldukları için bağıl import)
from .exif_extractor import EXIFExtractor 
from .image_processer import ImageProcessor

class PhotoImporter:
    """
    Fotoğrafları toplu olarak içe aktarır, işler ve güvenli şekilde saklar[cite: 28].
    """

    def __init__(self, db_session: Session, clip_embedder=None, faiss_manager=None):
        self.db = db_session
        self.exif_extractor = EXIFExtractor()
        self.processor = ImageProcessor()
        self.privacy = PrivacyManager(db_session)
        self.encryption = EncryptionManager()
        self.clip_embedder = clip_embedder
        self.faiss_manager = faiss_manager
        self.supported_formats = Config.SUPPORTED_IMAGE_FORMATS

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
                creation_datetime=metadata["created_at"] or datetime.fromtimestamp(os.path.getmtime(str(image_path))),
                latitude=metadata.get("location_lat"),
                longitude=metadata.get("location_lng"),
                has_consent=has_consent, # Gizlilik bayrağı [cite: 16]
                is_rotated=is_rotated    # İşleme bayrağı [cite: 16]
            )
            self.db.add(new_item)
            self.db.commit()
            return new_item.item_id
        except Exception as e:
            logger.error(f"Veritabanına kayıt hatası ({image_path}): {e}")
            self.db.rollback()
            return None

    def import_single_photo(self, image_path: Path, user_consent: bool) -> str:
        """
        Tek bir fotoğrafı tüm güvenlik ve işleme adımlarından geçirir.

        Returns:
            'imported': Başarıyla içe aktarıldı
            'no_consent': Rıza yok
            'duplicate': Zaten mevcut
            'error': İşlem hatası
        """
        # 1. Privacy Check: Rıza yoksa işlem yapma
        if not user_consent:
            return 'no_consent'

        # 2. Duplicate Check: Hash hesapla ve kontrol et
        file_hash = self.exif_extractor.calculate_file_hash(image_path)
        if self.is_duplicate(file_hash):
            return 'duplicate'

        # 2b. file_path bazlı duplicate kontrolü (aynı dosya şifrelendiyse hash değişir)
        existing = self.db.query(Item).filter(Item.file_path == str(image_path)).first()
        if existing:
            logger.info(f"Dosya zaten DB'de kayıtlı (path): {image_path}")
            return 'duplicate'

        # 2c. Dosyanın gerçek bir görüntü olduğunu doğrula (şifreli dosyaları atla)
        try:
            with Image.open(image_path) as img:
                img.verify()
        except Exception:
            logger.warning(f"Geçerli görüntü dosyası değil, atlanıyor: {image_path}")
            return 'duplicate'

        try:
            # 3. EXIF & Metadata çıkarma
            metadata = self.exif_extractor.extract_metadata(image_path)
            metadata["file_hash"] = file_hash

            # 4. Image Processing: Yön düzeltme ve boyutlandırma
            rotation_success = self.processor.process_image(image_path)

            # 5. CLIP Embedding: Raw image'den vektör üret (şifrelemeden ÖNCE)
            embedding = None
            if self.clip_embedder is not None:
                try:
                    embedding = self.clip_embedder.encode_image(image_path)
                    if embedding is not None:
                        logger.info(f"CLIP embedding uretildi: {image_path.name}")
                    else:
                        logger.warning(f"CLIP embedding uretilemedi: {image_path.name}")
                except Exception as e:
                    logger.warning(f"CLIP embedding hatasi ({image_path.name}): {e}")

            # 6. Encryption: Dosyayı diskte şifrele
            self.encryption.encrypt_file(str(image_path))

            # 7. Database: Kaydı tamamla
            item_id = self.add_photo_to_database(image_path, metadata, user_consent, rotation_success)
            if item_id is None:
                return 'error'

            # 8. FAISS'e embedding ekle ve faiss_index_id güncelle
            if embedding is not None and self.faiss_manager is not None:
                try:
                    faiss_ids = self.faiss_manager.add_embeddings(embedding, [item_id])
                    if faiss_ids:
                        item = self.db.query(Item).filter(Item.item_id == item_id).first()
                        if item:
                            item.faiss_index_id = faiss_ids[0]
                            self.db.commit()
                            logger.info(f"FAISS index guncellendi: item {item_id} -> faiss_id {faiss_ids[0]}")
                except Exception as e:
                    logger.warning(f"FAISS ekleme hatasi (item {item_id}): {e}")

            return 'imported'
        except Exception as e:
            logger.error(f"Fotoğraf import hatası ({image_path}): {e}")
            return 'error'

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
            result = self.import_single_photo(file_path, user_consent)
            if result == 'imported':
                stats['imported'] += 1
            elif result == 'duplicate':
                stats['skipped_duplicates'] += 1
            else:
                stats['errors'] += 1

        return stats