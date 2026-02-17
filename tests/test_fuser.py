# tests/test_fuser.py
"""
MultimodalFuser testleri.
Görsel + metin vektörlerinin birleştirilmesi testleri.
"""

import pytest
import numpy as np
from src.embedding.multimodal_fuser import MultimodalFuser


@pytest.fixture
def fuser():
    return MultimodalFuser(clip_dim=512, sbert_dim=384)


class TestFusion:
    """fuse() testleri."""

    def test_output_dimension(self, fuser):
        """Çıktı boyutu 512 + 384 = 896."""
        img_vec = np.random.randn(512).astype('float32')
        txt_vec = np.random.randn(384).astype('float32')

        result = fuser.fuse(img_vec, txt_vec)

        assert result.shape == (896,)

    def test_output_dtype_float32(self, fuser):
        """Çıktı tipi float32."""
        img_vec = np.random.randn(512).astype('float32')
        txt_vec = np.random.randn(384).astype('float32')

        result = fuser.fuse(img_vec, txt_vec)

        assert result.dtype == np.float32

    def test_only_image_vector(self, fuser):
        """Sadece görüntü vektörü verilince de çalışır."""
        img_vec = np.random.randn(512).astype('float32')

        result = fuser.fuse(image_vec=img_vec, text_vec=None)

        assert result.shape == (896,)

    def test_only_text_vector(self, fuser):
        """Sadece metin vektörü verilince de çalışır."""
        txt_vec = np.random.randn(384).astype('float32')

        result = fuser.fuse(image_vec=None, text_vec=txt_vec)

        assert result.shape == (896,)

    def test_both_none_returns_zero_vector(self, fuser):
        """Her iki vektör None ise sıfır vektörü döner."""
        result = fuser.fuse(image_vec=None, text_vec=None)

        assert result.shape == (896,)
        assert np.allclose(result, 0)

    def test_normalized_output(self, fuser):
        """Çıktı L2 normalize edilmiş olur (norm ~ 1)."""
        img_vec = np.random.randn(512).astype('float32')
        txt_vec = np.random.randn(384).astype('float32')

        result = fuser.fuse(img_vec, txt_vec)

        norm = np.linalg.norm(result)
        assert abs(norm - 1.0) < 0.01

    def test_custom_weights(self, fuser):
        """Özel ağırlıklar kullanılabilir."""
        img_vec = np.ones(512, dtype='float32')
        txt_vec = np.ones(384, dtype='float32')

        result1 = fuser.fuse(img_vec, txt_vec, image_weight=0.8, text_weight=0.2)
        result2 = fuser.fuse(img_vec, txt_vec, image_weight=0.2, text_weight=0.8)

        assert not np.allclose(result1, result2)

    def test_custom_dimensions(self):
        """Farklı boyutlarla da çalışır."""
        custom_fuser = MultimodalFuser(clip_dim=256, sbert_dim=128)

        img_vec = np.random.randn(256).astype('float32')
        txt_vec = np.random.randn(128).astype('float32')

        result = custom_fuser.fuse(img_vec, txt_vec)

        assert result.shape == (384,)
