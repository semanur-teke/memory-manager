"""
Bagimlilik enjeksiyonu (Dependency Injection).
DB session factory, servis singleton'lari ve ortak bagimliliklar.

FastAPI'nin Depends() mekanizmasi ile her request'e
gerekli servisler otomatik saglanir.
"""

import logging
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from database.schema import DatabaseSchema
from config import Config

logger = logging.getLogger(__name__)

# --- DB Session Factory (uygulama basinda bir kez olusturulur) ---
_db_schema = DatabaseSchema()


def get_db_session() -> Generator[Session, None, None]:
    """
    Veritabani oturumu olusturur ve request sonunda kapatir.

    Kullanim (router'da):
        @router.get("/items")
        async def get_items(db: Session = Depends(get_db_session)):
            ...
    """
    session = _db_schema.SessionLocal()
    try:
        yield session
    finally:
        session.close()


# --- Singleton Servisler ---
# EncryptionManager state'siz (sadece key tutar), tek instance yeterli.
_encryption_manager = None


def get_encryption_manager():
    """EncryptionManager singleton dondurur."""
    global _encryption_manager
    if _encryption_manager is None:
        from security.encryption_manager import EncryptionManager
        _encryption_manager = EncryptionManager()
        logger.info("EncryptionManager olusturuldu.")
    return _encryption_manager


def get_privacy_manager(db: Session = Depends(get_db_session)):
    """PrivacyManager instance dondurur (her request icin yeni — DB session gerektirir)."""
    from security.security_manager import PrivacyManager
    return PrivacyManager(db)


# --- CLIP & FAISS Singleton'lari ---
_clip_embedder = None
_faiss_manager = None


def get_clip_embedder():
    """CLIPEmbedder singleton dondurur (ilk cagride model yuklenir)."""
    global _clip_embedder
    if _clip_embedder is None:
        from src.embedding.clip_embedder import CLIPEmbedder
        _clip_embedder = CLIPEmbedder()
        logger.info("CLIPEmbedder olusturuldu.")
    return _clip_embedder


def get_faiss_manager():
    """FaissManager singleton dondurur."""
    global _faiss_manager
    if _faiss_manager is None:
        from src.embedding.faiss_manager import FaissManager
        _faiss_manager = FaissManager("database/clip_image_index.faiss", dimension=512, index_type="flat")
        logger.info("FaissManager olusturuldu.")
    return _faiss_manager


def get_photo_importer(db: Session = Depends(get_db_session)):
    """PhotoImporter instance dondurur."""
    from src.ingestion.photo_importer import PhotoImporter
    return PhotoImporter(db, clip_embedder=get_clip_embedder(), faiss_manager=get_faiss_manager())
