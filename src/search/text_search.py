"""
Metin ile Arama (Aşama 5.1)

Kullanıcı metin sorgusu ile fotoğraf/metin arama yapar.
"""

from typing import List, Dict, Optional
import numpy as np
from ..embedding.clip_embedder import CLIPEmbedder
from ..embedding.sbert_embedder import SBERTEmbedder
from ..embedding.faiss_manager import FaissManager


class TextSearch:
    """
    Metin sorguları ile arama yapar.
    """
    
    def __init__(self, clip_embedder: CLIPEmbedder, sbert_embedder: SBERTEmbedder,
                 image_faiss: FaissManager, text_faiss: FaissManager):
        """
        Args:
            clip_embedder: CLIP embedder (fotoğraf araması için)
            sbert_embedder: SBERT embedder (metin araması için)
            image_faiss: Fotoğraf embedding'leri için Faiss index
            text_faiss: Metin embedding'leri için Faiss index
        """
        self.clip_embedder = clip_embedder
        self.sbert_embedder = sbert_embedder
        self.image_faiss = image_faiss
        self.text_faiss = text_faiss
    
    def search_images(self, query_text: str, k: int = 10) -> List[Dict]:
        """
        Metin sorgusu ile fotoğraf ara.
        
        Örnek: "plajda gün batımı" → ilgili fotoğraflar
        
        Args:
            query_text: Arama metni
            k: Kaç sonuç döndürülecek
            
        Returns:
            [{'item_id': int, 'score': float, 'file_path': str}, ...]
        """
        pass
    
    def search_texts(self, query_text: str, k: int = 10) -> List[Dict]:
        """
        Metin sorgusu ile metin/transkript ara.
        
        Args:
            query_text: Arama metni
            k: Kaç sonuç döndürülecek
            
        Returns:
            [{'item_id': int, 'score': float, 'transcript': str}, ...]
        """
        pass
    
    def search_all(self, query_text: str, k: int = 10) -> Dict[str, List[Dict]]:
        """
        Hem fotoğraf hem metin araması yap.
        
        Args:
            query_text: Arama metni
            k: Her kategori için kaç sonuç
            
        Returns:
            {
                'images': [...],
                'texts': [...]
            }
        """
        pass

