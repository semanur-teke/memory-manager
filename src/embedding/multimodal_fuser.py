import numpy as np
from typing import Optional

class MultimodalFuser:
    """
    Görsel (512) ve Metinsel (384) vektörleri birleştirerek 
    896 boyutlu tek bir 'Hafıza Vektörü' oluşturur.
    """
    def __init__(self, clip_dim: int = 512, sbert_dim: int = 384):
        self.clip_dim = clip_dim
        self.sbert_dim = sbert_dim
        self.total_dim = clip_dim + sbert_dim

    def fuse(self, 
             image_vec: Optional[np.ndarray] = None, 
             text_vec: Optional[np.ndarray] = None,
             image_weight: float = 0.5,
             text_weight: float = 0.5) -> np.ndarray:
        
        # Vektörler yoksa sıfır vektörü oluştur
        if image_vec is None:
            image_vec = np.zeros(self.clip_dim, dtype='float32')
        if text_vec is None:
            text_vec = np.zeros(self.sbert_dim, dtype='float32')

        # Birleştir ve Normalize et
        fused_vector = np.concatenate([
            image_vec * image_weight, 
            text_vec * text_weight
        ])
        
        norm = np.linalg.norm(fused_vector)
        if norm > 0:
            fused_vector = fused_vector / norm
            
        return fused_vector.astype('float32')