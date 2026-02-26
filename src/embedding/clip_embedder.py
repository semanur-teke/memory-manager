import io
import logging
from pathlib import Path
from typing import List, Optional, Union
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer
import torch
from security.encryption_manager import EncryptionManager
from config import Config

logger = logging.getLogger(__name__)

class CLIPEmbedder:
    """
    CLIP modeli ile fotoğraf ve metin embedding'leri üretir.
    Görsel encode: clip-ViT-B-32 (orijinal CLIP)
    Metin encode: clip-ViT-B-32-multilingual-v1 (68 dil destekli)
    Her iki model de aynı 512 boyutlu uzaya iz düşürür.
    """

    def __init__(self, image_model: str = Config.CLIP_IMAGE_MODEL,
                 text_model: str = Config.CLIP_TEXT_MODEL,
                 encryption_manager: EncryptionManager = None,
                 batch_size: int = Config.CLIP_BATCH_SIZE):
        self.image_model_name = image_model
        self.text_model_name = text_model
        self.image_model = None
        self.text_model = None
        self.batch_size = batch_size
        self.encryptor = encryption_manager or EncryptionManager()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def _load_image_model(self):
        """Görsel CLIP modelini ihtiyaç duyulduğunda yükler."""
        if self.image_model is None:
            logger.info(f"CLIP gorsel modeli yukleniyor: {self.image_model_name} ({self.device})...")
            self.image_model = SentenceTransformer(self.image_model_name, device=self.device)

    def _load_text_model(self):
        """Multilingual metin modelini ihtiyaç duyulduğunda yükler."""
        if self.text_model is None:
            logger.info(f"CLIP metin modeli yukleniyor: {self.text_model_name} ({self.device})...")
            self.text_model = SentenceTransformer(self.text_model_name, device=self.device)
    
    def _open_image(self, image_path: Path) -> Optional[Image.Image]:
        """Fotoğrafı açar. Şifreliyse önce çözer, değilse direkt açar."""
        try:
            return Image.open(image_path)
        except Exception:
            # Dosya şifreli olabilir, decrypt edip tekrar dene
            try:
                decrypted_bytes = self.encryptor.decrypt_file(str(image_path))
                if decrypted_bytes:
                    return Image.open(io.BytesIO(decrypted_bytes))
            except Exception:
                pass
        return None

    def encode_image(self, image_path: Path) -> Optional[np.ndarray]:
        """
        Tek bir fotoğraf için normalize edilmiş 512 boyutlu embedding üretir.
        Şifreli dosyaları otomatik olarak bellekte çözer.
        """
        if not image_path.exists():
            return None

        self._load_image_model()

        try:
            img = self._open_image(image_path)
            if img is None:
                return None
            embedding = self.image_model.encode(
                img,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding.astype('float32')
        except Exception as e:
            logger.error(f"Fotoğraf vektöre çevrilemedi ({image_path.name}) -> {e}")
            return None

    def encode_images_batch(self, image_paths: List[Path]) -> np.ndarray:
        """
        Birden fazla fotoğraf için toplu (batch) embedding üretir.
        """
        if not image_paths:
            return np.array([], dtype='float32')

        self._load_image_model()

        try:
            images = [img for p in image_paths if p.exists() for img in [self._open_image(p)] if img is not None]
            embeddings = self.image_model.encode(
                images,
                batch_size=self.batch_size,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings.astype('float32')
        except Exception as e:
            logger.error(f"Toplu fotoğraf işleme başarısız -> {e}")
            return np.array([], dtype='float32')

    def encode_text(self, text: str) -> Optional[np.ndarray]:
        """
        Arama metni için embedding üretir (multilingual — 68 dil destekli).
        Türkçe, İngilizce ve diğer dillerde arama yapılabilir.
        """
        if not text:
            return None

        self._load_text_model()

        try:
            embedding = self.text_model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding.astype('float32')
        except Exception as e:
            logger.error(f"Metin vektöre çevrilemedi -> {e}")
            return None

    def get_embedding_dimension(self) -> int:
        """Kullanılan modelin boyutunu döndürür (Standart: 512)."""
        self._load_image_model()
        return self.image_model.get_sentence_embedding_dimension()