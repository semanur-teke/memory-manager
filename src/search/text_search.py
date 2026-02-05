"""
Metin ile Arama (Aşama 5.1)

Kullanıcı metin sorgusu ile fotoğraf/metin arama yapar.
"""

from typing import List, Dict, Optional
import numpy as np
from sqlalchemy.orm import Session
from ..embedding.clip_embedder import CLIPEmbedder
from ..embedding.sbert_embedder import SBERTEmbedder
from ..embedding.faiss_manager import FaissManager
from database.schema import Item


class TextSearch:
    """
    Metin sorguları ile arama yapar.
    """

    def __init__(self, clip_embedder: CLIPEmbedder, sbert_embedder: SBERTEmbedder,
                 image_faiss: FaissManager, text_faiss: FaissManager,
                 db_session: Session):
        """
        Args:
            clip_embedder: CLIP embedder (fotoğraf araması için)
            sbert_embedder: SBERT embedder (metin araması için)
            image_faiss: Fotoğraf embedding'leri için Faiss index
            text_faiss: Metin embedding'leri için Faiss index
            db_session: SQLAlchemy session (has_consent filtrelemesi için)
        """
        self.clip_embedder = clip_embedder
        self.sbert_embedder = sbert_embedder
        self.image_faiss = image_faiss
        self.text_faiss = text_faiss
        self.db_session = db_session

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
        # 1. Metin → CLIP embedding
        query_vec = self.clip_embedder.encode_text(query_text)
        if query_vec is None:
            return []

        # 2. FAISS'ten k*2 sonuç al (consent filtresi sonrası yeterli sonuç kalsın)
        faiss_results = self.image_faiss.search(query_vec, k * 2)
        if not faiss_results:
            return []

        # 3. DB'den Item bilgilerini çek, has_consent filtrele
        item_ids = [item_id for item_id, _ in faiss_results]
        items = self.db_session.query(Item).filter(
            Item.item_id.in_(item_ids),
            Item.has_consent == True
        ).all()
        consent_map = {item.item_id: item for item in items}

        # 4. Sonuçları oluştur (distance → score dönüşümü)
        results = []
        for item_id, distance in faiss_results:
            if item_id in consent_map:
                score = 1 - distance / 2
                results.append({
                    'item_id': item_id,
                    'score': round(score, 4),
                    'file_path': consent_map[item_id].file_path
                })
            if len(results) >= k:
                break

        return results

    def search_texts(self, query_text: str, k: int = 10) -> List[Dict]:
        """
        Metin sorgusu ile metin/transkript ara.

        Args:
            query_text: Arama metni
            k: Kaç sonuç döndürülecek

        Returns:
            [{'item_id': int, 'score': float, 'transcript': str}, ...]
        """
        # 1. Metin → SBERT embedding
        query_vec = self.sbert_embedder.encode_text(query_text)
        if query_vec is None:
            return []

        # 2. FAISS'ten k*2 sonuç al
        faiss_results = self.text_faiss.search(query_vec, k * 2)
        if not faiss_results:
            return []

        # 3. DB'den Item bilgilerini çek, has_consent filtrele
        item_ids = [item_id for item_id, _ in faiss_results]
        items = self.db_session.query(Item).filter(
            Item.item_id.in_(item_ids),
            Item.has_consent == True
        ).all()
        consent_map = {item.item_id: item for item in items}

        # 4. Sonuçları oluştur
        results = []
        for item_id, distance in faiss_results:
            if item_id in consent_map:
                score = 1 - distance / 2
                results.append({
                    'item_id': item_id,
                    'score': round(score, 4),
                    'transcript': consent_map[item_id].transcription or ''
                })
            if len(results) >= k:
                break

        return results

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
        return {
            'images': self.search_images(query_text, k),
            'texts': self.search_texts(query_text, k)
        }
