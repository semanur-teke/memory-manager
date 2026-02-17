# tests/test_exif.py
"""
EXIFExtractor testleri.
Dosya hash, tarih, GPS ve metadata çıkarma testleri.
"""

import pytest
from pathlib import Path
from datetime import datetime
from src.ingestion.exif_extractor import EXIFExtractor


@pytest.fixture
def extractor():
    return EXIFExtractor()


class TestFileHash:
    """calculate_file_hash() testleri."""

    def test_hash_is_sha256(self, extractor, sample_image):
        """Hash 64 karakter (256-bit hex) uzunluğunda olmalı."""
        hash_val = extractor.calculate_file_hash(sample_image)

        assert len(hash_val) == 64
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_same_file_same_hash(self, extractor, sample_image):
        """Aynı dosya her seferinde aynı hash'i üretir."""
        hash1 = extractor.calculate_file_hash(sample_image)
        hash2 = extractor.calculate_file_hash(sample_image)

        assert hash1 == hash2

    def test_different_files_different_hash(self, extractor, sample_image, large_image):
        """Farklı dosyalar farklı hash'ler üretir."""
        hash1 = extractor.calculate_file_hash(sample_image)
        hash2 = extractor.calculate_file_hash(large_image)

        assert hash1 != hash2

    def test_nonexistent_file_returns_empty(self, extractor):
        """Olmayan dosya için boş string döner."""
        result = extractor.calculate_file_hash(Path("/nonexistent/file.jpg"))
        assert result == ""


class TestExtractDatetime:
    """extract_datetime() testleri."""

    def test_no_exif_returns_none(self, extractor, sample_image):
        """EXIF verisi olmayan fotoğrafta None döner."""
        result = extractor.extract_datetime(sample_image)
        assert result is None

    def test_nonexistent_file_returns_none(self, extractor):
        """Olmayan dosyada None döner."""
        result = extractor.extract_datetime(Path("/nonexistent/photo.jpg"))
        assert result is None


class TestExtractGPS:
    """extract_gps_coordinates() testleri."""

    def test_no_gps_returns_none(self, extractor, sample_image):
        """GPS verisi olmayan fotoğrafta None döner."""
        result = extractor.extract_gps_coordinates(sample_image)
        assert result is None

    def test_convert_to_degrees(self, extractor):
        """Derece/dakika/saniye -> ondalık derece dönüşümü doğru."""
        result = extractor._convert_to_degrees((41, 0, 30))
        assert abs(result - 41.00833) < 0.001


class TestExtractMetadata:
    """extract_metadata() testleri."""

    def test_metadata_dict_keys(self, extractor, sample_image):
        """Metadata dict'i gerekli anahtarları içerir."""
        meta = extractor.extract_metadata(sample_image)

        expected_keys = {
            'created_at', 'location_lat', 'location_lng',
            'camera_make', 'camera_model', 'file_hash', 'file_size'
        }
        assert expected_keys.issubset(meta.keys())

    def test_metadata_file_size(self, extractor, sample_image):
        """file_size pozitif bir sayı."""
        meta = extractor.extract_metadata(sample_image)
        assert meta['file_size'] > 0

    def test_metadata_has_hash(self, extractor, sample_image):
        """file_hash boş değil."""
        meta = extractor.extract_metadata(sample_image)
        assert len(meta['file_hash']) == 64

    def test_metadata_nonexistent_file(self, extractor):
        """Olmayan dosya için error dict'i döner."""
        meta = extractor.extract_metadata(Path("/nonexistent/photo.jpg"))
        assert "error" in meta

    def test_camera_info_format(self, extractor, sample_image):
        """Kamera bilgisi dict formatında döner."""
        info = extractor.extract_camera_info(sample_image)
        assert 'make' in info
        assert 'model' in info
