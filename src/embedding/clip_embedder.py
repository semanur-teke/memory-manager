from pathlib import Path
from typing import List, Optional, Union
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer
import torch

class CLIPEmbedder:
    """
    CLIP modeli ile fotoğraf ve metin embedding'leri üretir.
    Fotoğrafları anlamsal sayılara (512 boyutlu vektörler) dönüştürür.
    """
    
    def __init__(self, model_name: str = "clip-ViT-B-32"):
        """
        Args:
            model_name: CLIP model adı (512 boyut için ViT-B-32 idealdir)
        """
        self.model_name = model_name
        self.model = None
        # Cihazı belirle: GPU varsa CUDA, yoksa CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def load_model(self):
        """CLIP modelini ihtiyaç duyulduğunda belleğe yükler."""
        if self.model is None:
            print(f"CLIP modeli yükleniyor: {self.model_name} ({self.device})...")
            # SentenceTransformer, görsel ve metinsel CLIP işlemlerini tek çatı altında toplar.
            self.model = SentenceTransformer(self.model_name, device=self.device)
    
    def encode_image(self, image_path: Path) -> Optional[np.ndarray]:
        """
        Tek bir fotoğraf için normalize edilmiş 512 boyutlu embedding üretir.
        """
        if not image_path.exists():
            return None
            
        self.load_model()
        
        try:
            # Fotoğrafı aç
            img = Image.open(image_path)
            # normalize_embeddings=True: FAISS araması için vektör boyunu 1'e eşitler.
            embedding = self.model.encode(
                img, 
                convert_to_numpy=True, 
                normalize_embeddings=True
            )
            return embedding.astype('float32')
        except Exception as e:
            print(f"Hata: Fotoğraf vektöre çevrilemedi ({image_path.name}) -> {e}")
            return None
    
    def encode_images_batch(self, image_paths: List[Path]) -> np.ndarray:
        """
        Birden fazla fotoğraf için toplu (batch) embedding üretir.
        """
        if not image_paths:
            return np.array([], dtype='float32')

        self.load_model()
        
        try:
            images = [Image.open(p) for p in image_paths if p.exists()]
            embeddings = self.model.encode(
                images,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings.astype('float32')
        except Exception as e:
            print(f"Hata: Toplu fotoğraf işleme başarısız -> {e}")
            return np.array([], dtype='float32')
    
    def encode_text(self, text: str) -> Optional[np.ndarray]:
        """
        Arama metni için embedding üretir. Bu sayede "mavi araba" yazarak 
        ilgili fotoğrafları bulabilirsin.
        """
        if not text:
            return None
            
        self.load_model()
        
        try:
            # CLIP'in metin kodlayıcısını kullanarak metni görsel uzaya iz düşürür.
            embedding = self.model.encode(
                text, 
                convert_to_numpy=True, 
                normalize_embeddings=True
            )
            return embedding.astype('float32')
        except Exception as e:
            print(f"Hata: Metin vektöre çevrilemedi -> {e}")
            return None
    
    def get_embedding_dimension(self) -> int:
        """Kullanılan modelin boyutunu döndürür (Standart: 512)."""
        self.load_model()
        return self.model.get_sentence_embedding_dimension()