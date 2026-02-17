# tests/test_audio.py
"""
AudioProcessor testleri.
Whisper modeli mock'lanır (ağır model indirmek gerekmez).
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from config import Config


@pytest.fixture
def audio_processor():
    """Whisper mock'lu AudioProcessor."""
    with patch('src.ingestion.audio_processor.whisper') as mock_whisper:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": " Bugün hava çok güzeldi. "}
        mock_whisper.load_model.return_value = mock_model

        from src.ingestion.audio_processor import AudioProcessor
        processor = AudioProcessor(db_session=None, model_size="tiny")
        processor.model = mock_model

        yield processor


class TestSupportedFormat:
    """is_supported_format() testleri."""

    def test_mp3_supported(self, audio_processor):
        assert audio_processor.is_supported_format(Path("song.mp3")) is True

    def test_wav_supported(self, audio_processor):
        assert audio_processor.is_supported_format(Path("recording.wav")) is True

    def test_m4a_supported(self, audio_processor):
        assert audio_processor.is_supported_format(Path("voice.m4a")) is True

    def test_flac_supported(self, audio_processor):
        assert audio_processor.is_supported_format(Path("music.flac")) is True

    def test_txt_not_supported(self, audio_processor):
        assert audio_processor.is_supported_format(Path("document.txt")) is False

    def test_jpg_not_supported(self, audio_processor):
        assert audio_processor.is_supported_format(Path("photo.jpg")) is False

    def test_case_insensitive(self, audio_processor):
        """Büyük/küçük harf fark etmez."""
        assert audio_processor.is_supported_format(Path("file.MP3")) is True
        assert audio_processor.is_supported_format(Path("file.WAV")) is True


class TestTranscribeAudio:
    """transcribe_audio() testleri."""

    def test_unsupported_format_returns_none(self, audio_processor):
        """Desteklenmeyen format None döner."""
        result = audio_processor.transcribe_audio(Path("video.avi"), item_id=1)
        assert result is None

    def test_transcription_returns_encrypted_text(self, audio_processor, temp_dir):
        """Başarılı transkripsiyon şifreli metin döner."""
        audio_file = temp_dir / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        result = audio_processor.transcribe_audio(audio_file, item_id=1)

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0


class TestTranscribeBatch:
    """transcribe_batch() testleri."""

    def test_batch_empty_dict(self, audio_processor):
        """Boş dict verilince boş dict döner."""
        result = audio_processor.transcribe_batch({})
        assert result == {}

    def test_batch_processes_multiple(self, audio_processor, temp_dir):
        """Birden fazla dosya sırayla işlenir."""
        f1 = temp_dir / "audio1.wav"
        f2 = temp_dir / "audio2.wav"
        f1.write_bytes(b"fake1")
        f2.write_bytes(b"fake2")

        data = {1: f1, 2: f2}
        result = audio_processor.transcribe_batch(data)

        assert isinstance(result, dict)


class TestAudioMetadata:
    """get_audio_metadata() testleri."""

    def test_metadata_keys(self, audio_processor, temp_dir):
        """Metadata dict'i gerekli anahtarları içerir."""
        audio_file = temp_dir / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        meta = audio_processor.get_audio_metadata(audio_file)

        assert 'duration' in meta
        assert 'sample_rate' in meta
        assert 'channels' in meta
        assert 'file_size' in meta
        assert 'format' in meta

    def test_metadata_file_size(self, audio_processor, temp_dir):
        """file_size pozitif bir sayı."""
        audio_file = temp_dir / "test.wav"
        audio_file.write_bytes(b"x" * 100)

        meta = audio_processor.get_audio_metadata(audio_file)
        assert meta['file_size'] == 100

    def test_metadata_format(self, audio_processor, temp_dir):
        """format doğru uzantıyı içerir."""
        audio_file = temp_dir / "test.mp3"
        audio_file.write_bytes(b"fake")

        meta = audio_processor.get_audio_metadata(audio_file)
        assert meta['format'] == ".mp3"
