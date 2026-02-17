# tests/test_image_processor.py
"""
ImageProcessor testleri.
Yön düzeltme ve boyut küçültme testleri.
"""

import pytest
from pathlib import Path
from PIL import Image
from src.ingestion.image_processer import ImageProcessor
from config import Config


@pytest.fixture
def processor():
    return ImageProcessor()


class TestResizeIfNeeded:
    """resize_if_needed() testleri."""

    def test_large_image_resized(self, processor):
        """max_size'dan büyük görüntü küçültülür."""
        img = Image.new("RGB", (3000, 2000))

        result = processor.resize_if_needed(img)

        assert max(result.size) <= Config.IMAGE_MAX_SIZE

    def test_small_image_not_resized(self, processor):
        """max_size'dan küçük görüntü değiştirilmez."""
        img = Image.new("RGB", (500, 300))

        result = processor.resize_if_needed(img)

        assert result.size == (500, 300)

    def test_aspect_ratio_preserved(self, processor):
        """Küçültme sırasında en boy oranı korunur."""
        img = Image.new("RGB", (4000, 2000))

        result = processor.resize_if_needed(img)

        w, h = result.size
        original_ratio = 4000 / 2000
        new_ratio = w / h
        assert abs(original_ratio - new_ratio) < 0.1

    def test_exact_max_size_not_resized(self, processor):
        """Tam max_size boyutunda görüntü değiştirilmez."""
        img = Image.new("RGB", (Config.IMAGE_MAX_SIZE, Config.IMAGE_MAX_SIZE))

        result = processor.resize_if_needed(img)

        assert result.size == (Config.IMAGE_MAX_SIZE, Config.IMAGE_MAX_SIZE)


class TestFixOrientation:
    """fix_orientation() testleri."""

    def test_no_exif_no_crash(self, processor):
        """EXIF verisi olmayan görüntüde hata vermez."""
        img = Image.new("RGB", (100, 100))

        result = processor.fix_orientation(img)
        assert result.size == (100, 100)


class TestProcessImage:
    """process_image() testleri."""

    def test_process_success(self, processor, sample_image):
        """Normal bir fotoğraf başarıyla işlenir (True döner)."""
        result = processor.process_image(sample_image)
        assert result is True

    def test_process_large_image_shrinks(self, processor, large_image):
        """3000x3000 fotoğraf işlendikten sonra küçülmüş olur."""
        processor.process_image(large_image)

        with Image.open(large_image) as img:
            assert max(img.size) <= Config.IMAGE_MAX_SIZE

    def test_process_nonexistent_file(self, processor):
        """Olmayan dosyada False döner."""
        result = processor.process_image(Path("/nonexistent/photo.jpg"))
        assert result is False

    def test_process_preserves_format(self, processor, sample_image):
        """İşleme sonrası dosya formatı korunur (JPEG kalır)."""
        processor.process_image(sample_image)

        with Image.open(sample_image) as img:
            assert img.format == "JPEG"

    def test_custom_max_size(self, temp_dir):
        """Özel max_size parametresi kullanılabilir."""
        processor = ImageProcessor(max_size=500)

        img_path = temp_dir / "custom.jpg"
        img = Image.new("RGB", (1000, 1000), color="red")
        img.save(img_path, "JPEG")

        processor.process_image(img_path)

        with Image.open(img_path) as img:
            assert max(img.size) <= 500
