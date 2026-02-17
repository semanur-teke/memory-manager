# tests/conftest.py
"""
Paylaşımlı test fixture'ları.
Tüm test_*.py dosyaları bu fixture'ları otomatik olarak kullanabilir.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Proje kökünü path'e ekle
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database.schema import Base, Item, Event
from security.encryption_manager import EncryptionManager


# ================================================================
#                    VERİTABANI FİXTURE'LARI
# ================================================================

@pytest.fixture
def db_engine():
    """Her test için bellekte (in-memory) yeni SQLite veritabanı oluşturur."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Her test için yeni bir DB oturumu açar, test bitince rollback yapar."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_items(db_session):
    """Test veritabanına 5 örnek Item ekler ve döndürür."""
    items = [
        Item(
            file_path="/photos/istanbul_sunset.jpg",
            file_hash="hash_ist_001",
            type="Photo",
            has_consent=True,
            is_rotated=False,
            creation_datetime=datetime(2025, 6, 15, 14, 30),
            latitude=41.0082,
            longitude=28.9784,
        ),
        Item(
            file_path="/photos/ankara_castle.jpg",
            file_hash="hash_ank_002",
            type="Photo",
            has_consent=True,
            is_rotated=True,
            creation_datetime=datetime(2025, 3, 20, 10, 0),
            latitude=39.9334,
            longitude=32.8597,
        ),
        Item(
            file_path="/photos/no_consent.jpg",
            file_hash="hash_noc_003",
            type="Photo",
            has_consent=False,
            is_rotated=False,
            creation_datetime=datetime(2025, 1, 10, 8, 0),
            latitude=41.0,
            longitude=29.0,
        ),
        Item(
            file_path="/audio/meeting_notes.m4a",
            file_hash="hash_aud_004",
            type="Audio",
            has_consent=True,
            is_rotated=False,
            creation_datetime=datetime(2025, 7, 1, 9, 0),
            transcription="bu_alan_sifreli_metin_olacak",
        ),
        Item(
            file_path="/photos/no_gps.jpg",
            file_hash="hash_nog_005",
            type="Photo",
            has_consent=True,
            is_rotated=False,
            creation_datetime=datetime(2024, 12, 25, 18, 0),
            latitude=None,
            longitude=None,
        ),
    ]
    db_session.add_all(items)
    db_session.commit()
    return items


# ================================================================
#                    ŞİFRELEME FİXTURE'LARI
# ================================================================

@pytest.fixture
def temp_dir():
    """Geçici bir klasör oluşturur, test bitince siler."""
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def encryption_manager(temp_dir):
    """Geçici anahtarla EncryptionManager oluşturur."""
    key_path = str(temp_dir / "test_secret.key")
    return EncryptionManager(key_path=key_path)


# ================================================================
#                    GÖRÜNTÜ FİXTURE'LARI
# ================================================================

@pytest.fixture
def sample_image(temp_dir):
    """100x100 piksellik basit bir test JPEG dosyası oluşturur."""
    from PIL import Image
    img_path = temp_dir / "test_photo.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path, "JPEG")
    return img_path


@pytest.fixture
def large_image(temp_dir):
    """3000x3000 piksellik büyük bir test JPEG dosyası oluşturur."""
    from PIL import Image
    img_path = temp_dir / "big_photo.jpg"
    img = Image.new("RGB", (3000, 3000), color="blue")
    img.save(img_path, "JPEG")
    return img_path


@pytest.fixture
def small_image(temp_dir):
    """500x500 piksellik küçük bir test JPEG dosyası oluşturur."""
    from PIL import Image
    img_path = temp_dir / "small_photo.jpg"
    img = Image.new("RGB", (500, 500), color="green")
    img.save(img_path, "JPEG")
    return img_path
