import logging
import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Optional, Tuple
from config import Config

logger = logging.getLogger(__name__)

class FaissManager:
    """
    Vektör arama motoru. Embedding'leri saklar ve anlamsal benzerlik
    araması yaparak en yakın sonuçları (Item ID bazlı) döndürür.
    """
    
    def __init__(self, index_path: str, dimension: int, index_type: str = "flat",
                 hnsw_neighbors: int = Config.HNSW_NEIGHBORS):
        # Index dosyasının yolu (Örn: database/vector_index.faiss)
        self.index_path = Path(index_path)
        self.dimension = dimension
        self.index_type = index_type.lower()
        self.hnsw_neighbors = hnsw_neighbors
        self.index = None
        # Faiss ID -> Database Item ID eşleşmesi
        self.id_to_item_id = {} 

        # Klasör yoksa oluştur
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        if self.index_path.exists():
            self.load_index()
        else:
            self.create_index()

    def create_index(self):
        """Yeni bir boş Faiss index oluşturur."""
        if self.index_type == "hnsw":
            # HNSW: Büyük veri setlerinde çok hızlı arama sağlar.
            self.index = faiss.IndexHNSWFlat(self.dimension, self.hnsw_neighbors)
            logger.info(f"HNSW Faiss index oluşturuldu (Boyut: {self.dimension})")
        else:
            # FlatL2: En hassas, kaba kuvvet arama (Küçük veri setleri için ideal).
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"FlatL2 Faiss index oluşturuldu (Boyut: {self.dimension})")

    def load_index(self):
        """Index'i ve ID haritasını yükler."""
        try:
            self.index = faiss.read_index(str(self.index_path))
            map_path = self.index_path.with_suffix('.pkl')
            if map_path.exists():
                with open(map_path, 'rb') as f:
                    self.id_to_item_id = pickle.load(f)
            logger.info("Mevcut Faiss index başarıyla yüklendi.")
        except Exception as e:
            logger.warning(f"Yükleme hatası: {e}. Yeni index açılıyor.")
            self.create_index()

    def save_index(self):
        """Verileri diske kalıcı olarak yazar."""
        faiss.write_index(self.index, str(self.index_path))
        map_path = self.index_path.with_suffix('.pkl')
        with open(map_path, 'wb') as f:
            pickle.dump(self.id_to_item_id, f)

    def add_embeddings(self, embeddings: np.ndarray, item_ids: List[int]):
        """Yeni vektörleri ekler ve normalizasyon yapar."""
        # Veri tipini Faiss için float32'ye zorla
        embeddings = embeddings.astype('float32')
        
        # 2D array kontrolü
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        # PDF GEREKSİNİMİ: L2 Normalizasyonu (Cosine Similarity için şart)
        faiss.normalize_L2(embeddings)

        start_id = self.index.ntotal
        self.index.add(embeddings)

        # ID Eşleşmelerini Güncelle
        for i, item_id in enumerate(item_ids):
            self.id_to_item_id[start_id + i] = item_id
        
        self.save_index()
        return list(range(start_id, self.index.ntotal))

    def search(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[int, float]]:
        """Sorgu vektörüne en benzer sonuçları bulur."""
        # Sorgu vektörünü hazırla ve normalize et
        query_embedding = query_embedding.astype('float32')
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        faiss.normalize_L2(query_embedding)

        # Arama yap
        distances, indices = self.index.search(query_embedding, k)

        results = []
        for dist, f_id in zip(distances[0], indices[0]):
            if f_id != -1: # -1: Sonuç bulunamadı bayrağı
                item_id = self.id_to_item_id.get(f_id)
                # Küçük dist (mesafe) = Yüksek benzerlik
                results.append((item_id, float(dist)))
        
        return results

    def get_index_size(self) -> int:
        return self.index.ntotal if self.index else 0