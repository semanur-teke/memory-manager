from typing import List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

class SBERTEmbedder:
    """
    Metinleri (transkript, not vb.) anlamsal vektörlere dönüştüren motor.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        # Önce cihazı belirle (Hata almamak için)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None  # Lazy loading: Sadece ihtiyaç duyulduğunda yüklenir.

    def _load_model(self):
        """Modeli belleğe yükler. Sadece bir kez çalışır."""
        if self.model is None:
            print(f"SBERT modeli yükleniyor: {self.model_name} ({self.device})...")
            self.model = SentenceTransformer(self.model_name, device=self.device)

    def encode_text(self, text: str) -> Optional[np.ndarray]:
        """
        Tek bir metni normalize edilmiş float32 vektöre çevirir.
        """
        if not text or not isinstance(text, str):
            return None
            
        self._load_model()
        
        try:
            # normalize_embeddings=True: PDF'de belirtilen L2 normalizasyonunu yapar.
            # convert_to_numpy=True: Doğrudan FAISS uyumlu NumPy dizisi döner.
            embedding = self.model.encode(
                text, 
                convert_to_numpy=True, 
                normalize_embeddings=True
            )
            return embedding.astype('float32')
        except Exception as e:
            print(f"Hata: Metin vektöre çevrilemedi -> {e}")
            return None

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Çok sayıda metni (batch) hızlıca işler.
        """
        if not texts:
            return np.array([], dtype='float32')

        self._load_model()
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings.astype('float32')
        except Exception as e:
            print(f"Hata: Toplu işlem başarısız -> {e}")
            return np.array([], dtype='float32')

    def get_dimension(self) -> int:
        """Kullanılan modelin vektör boyutunu döndürür (Örn: 384)."""
        self._load_model()
        return self.model.get_sentence_embedding_dimension()