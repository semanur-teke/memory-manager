"""
Bagimlilik enjeksiyonu.
DB session factory, servis singleton'lari ve ortak bagimliliklar.
"""

from sqlalchemy.orm import Session


def get_db_session():
    """Veritabani oturumu olusturur ve request sonunda kapatir."""
    pass


def get_encryption_manager():
    """EncryptionManager singleton dondurur."""
    pass


def get_privacy_manager(session: Session = None):
    """PrivacyManager instance dondurur."""
    pass


def get_search_engine(session: Session = None):
    """SearchEngine instance dondurur."""
    pass


def get_photo_importer(session: Session = None):
    """PhotoImporter instance dondurur."""
    pass
