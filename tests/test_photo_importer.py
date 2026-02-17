# tests/test_photo_importer.py
"""
PhotoImporter testleri.
Fotoğraf import iş akışı end-to-end testleri.

ÖNEMLİ: Bu testler gerçek DB kullanır ama EXIF/şifreleme kısımlarını mock'lar.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.ingestion.photo_importer import PhotoImporter
from database.schema import Item
from config import Config


@pytest.fixture
def importer(db_session):
    """Mock bağımlılıklarla PhotoImporter oluşturur."""
    with patch('src.ingestion.photo_importer.EXIFExtractor') as MockExif, \
         patch('src.ingestion.photo_importer.ImageProcessor') as MockProc, \
         patch('src.ingestion.photo_importer.PrivacyManager') as MockPrivacy, \
         patch('src.ingestion.photo_importer.EncryptionManager') as MockEnc:

        mock_exif = MockExif.return_value
        mock_exif.calculate_file_hash.return_value = "unique_hash_12345"
        mock_exif.extract_metadata.return_value = {
            "created_at": datetime(2025, 6, 15, 14, 30),
            "location_lat": 41.0,
            "location_lng": 29.0,
            "camera_make": "TestCam",
            "camera_model": "Model X",
            "file_hash": "unique_hash_12345",
            "file_size": 1024
        }

        MockProc.return_value.process_image.return_value = True
        MockEnc.return_value.encrypt_file.return_value = None

        imp = PhotoImporter(db_session)
        yield imp


class TestFindImageFiles:
    """find_image_files() testleri."""

    def test_find_supported_formats(self, importer, temp_dir):
        """Desteklenen formatlardaki dosyaları bulur."""
        (temp_dir / "photo.jpg").write_bytes(b"fake jpg")
        (temp_dir / "photo.png").write_bytes(b"fake png")
        (temp_dir / "document.pdf").write_bytes(b"fake pdf")
        (temp_dir / "readme.txt").write_bytes(b"not an image")

        files = importer.find_image_files(temp_dir)
        extensions = {f.suffix.lower() for f in files}

        assert ".jpg" in extensions or ".png" in extensions
        assert ".pdf" not in extensions
        assert ".txt" not in extensions

    def test_find_recursive(self, importer, temp_dir):
        """Alt klasörlerdeki dosyaları da bulur."""
        subdir = temp_dir / "vacation" / "summer"
        subdir.mkdir(parents=True)
        (subdir / "beach.jpg").write_bytes(b"fake jpg")

        files = importer.find_image_files(temp_dir, recursive=True)
        assert len(files) >= 1

    def test_find_non_recursive(self, importer, temp_dir):
        """recursive=False ise alt klasörlere bakmaz."""
        subdir = temp_dir / "subfolder"
        subdir.mkdir()
        (temp_dir / "root.jpg").write_bytes(b"fake jpg in root")
        (subdir / "sub.jpg").write_bytes(b"fake jpg in sub")

        files = importer.find_image_files(temp_dir, recursive=False)
        file_names = [f.name for f in files]

        assert "root.jpg" in file_names
        assert "sub.jpg" not in file_names

    def test_empty_folder(self, importer, temp_dir):
        """Boş klasörde boş liste döner."""
        empty = temp_dir / "empty"
        empty.mkdir()

        files = importer.find_image_files(empty)
        assert files == []


class TestIsDuplicate:
    """is_duplicate() testleri."""

    def test_not_duplicate(self, importer):
        """DB'de olmayan hash duplicate değildir."""
        assert importer.is_duplicate("brand_new_hash") is False

    def test_is_duplicate(self, importer, db_session):
        """DB'de olan hash duplicate'tır."""
        item = Item(
            file_path="/existing.jpg",
            file_hash="existing_hash",
            type="Photo",
            is_rotated=False,
            creation_datetime=datetime.now()
        )
        db_session.add(item)
        db_session.commit()

        assert importer.is_duplicate("existing_hash") is True


class TestImportSinglePhoto:
    """import_single_photo() testleri."""

    def test_no_consent_returns_no_consent(self, importer, sample_image):
        """user_consent=False ise 'no_consent' döner."""
        result = importer.import_single_photo(sample_image, user_consent=False)
        assert result == 'no_consent'

    def test_duplicate_returns_duplicate(self, importer, sample_image, db_session):
        """Zaten var olan dosya 'duplicate' döner."""
        item = Item(
            file_path="/old.jpg",
            file_hash="unique_hash_12345",
            type="Photo",
            is_rotated=False,
            creation_datetime=datetime.now()
        )
        db_session.add(item)
        db_session.commit()

        result = importer.import_single_photo(sample_image, user_consent=True)
        assert result == 'duplicate'

    def test_successful_import(self, importer, sample_image, db_session):
        """Başarılı import 'imported' döner ve DB'ye kayıt eklenir."""
        result = importer.import_single_photo(sample_image, user_consent=True)

        assert result == 'imported'

        count = db_session.query(Item).count()
        assert count == 1
