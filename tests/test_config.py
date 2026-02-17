# tests/test_config.py
"""
Config ve setup_logging() testleri.
Merkezi yapılandırmanın doğruluğunu kontrol eder.
"""

import pytest
import logging
from config import Config, setup_logging


class TestConfigValues:
    """Config sabitleri testleri."""

    def test_model_names_not_empty(self):
        """Model adları boş değil."""
        assert len(Config.SBERT_MODEL_NAME) > 0
        assert len(Config.CLIP_MODEL_NAME) > 0
        assert len(Config.WHISPER_MODEL_SIZE) > 0

    def test_database_url_is_sqlite(self):
        """Veritabanı URL'i SQLite formatında."""
        assert Config.DATABASE_URL.startswith("sqlite")

    def test_supported_image_formats(self):
        """Temel fotoğraf formatları destekleniyor."""
        assert ".jpg" in Config.SUPPORTED_IMAGE_FORMATS
        assert ".jpeg" in Config.SUPPORTED_IMAGE_FORMATS
        assert ".png" in Config.SUPPORTED_IMAGE_FORMATS

    def test_supported_audio_formats(self):
        """Temel ses formatları destekleniyor."""
        assert ".mp3" in Config.SUPPORTED_AUDIO_FORMATS
        assert ".wav" in Config.SUPPORTED_AUDIO_FORMATS
        assert ".m4a" in Config.SUPPORTED_AUDIO_FORMATS

    def test_numeric_values_positive(self):
        """Sayısal parametreler pozitif."""
        assert Config.IMAGE_MAX_SIZE > 0
        assert Config.SBERT_BATCH_SIZE > 0
        assert Config.CLIP_BATCH_SIZE > 0
        assert Config.HNSW_NEIGHBORS > 0
        assert Config.DEFAULT_SEARCH_RADIUS_KM > 0
        assert Config.DEFAULT_SEARCH_K > 0


class TestSetupLogging:
    """setup_logging() testleri."""

    def test_setup_creates_handlers(self):
        """setup_logging() root logger'a handler ekler."""
        setup_logging()

        root = logging.getLogger()
        assert len(root.handlers) > 0

    def test_security_logger_has_file_handler(self):
        """security logger'a file handler eklenir."""
        setup_logging()

        sec_logger = logging.getLogger("security")
        has_file_handler = any(
            isinstance(h, logging.FileHandler)
            for h in sec_logger.handlers
        )
        assert has_file_handler

    def test_setup_idempotent(self):
        """Birden fazla çağrılsa handler duplikasyonu olmaz."""
        setup_logging()
        count1 = len(logging.getLogger().handlers)

        setup_logging()
        count2 = len(logging.getLogger().handlers)

        assert count1 == count2
