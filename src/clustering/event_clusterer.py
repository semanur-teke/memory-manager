"""
Ana Olay Kümeleme Sınıfı (Aşama 6)

Tüm kümeleme adımlarını koordine eder.
"""

from typing import List, Dict
from .dbscan_clusterer import DBSCANClusterer
from .refinement_clusterer import RefinementClusterer
from .cover_photo_selector import CoverPhotoSelector


class EventClusterer:
    """
    Tüm kümeleme işlemlerini yönetir.
    """
    
    def __init__(self, db_connection, clip_embedder=None):
        """
        Args:
            db_connection: Veritabanı bağlantısı
            clip_embedder: CLIP embedder (kapak fotoğrafı seçimi için)
        """
        self.db = db_connection
        self.clip_embedder = clip_embedder
        self.dbscan_clusterer = DBSCANClusterer()
        self.refinement_clusterer = RefinementClusterer()
        self.cover_selector = CoverPhotoSelector()
    
    def cluster_all_items(self) -> List[Dict]:
        """
        Tüm öğeleri olaylara kümele.
        
        Adımlar:
        1. DBSCAN ile zaman/konum bazlı kümeleme
        2. Büyük kümeleri embedding bazlı bölme
        3. Her küme için kapak fotoğrafı seçme
        4. Veritabanına Events tablosuna kaydetme
        
        Returns:
            Oluşturulan olayların listesi
        """
        pass
    
    def create_events_from_clusters(self, clusters: List[List[int]]) -> List[int]:
        """
        Kümeleri Events tablosuna kaydet.
        
        Args:
            clusters: Küme listesi (her küme item_id listesi)
            
        Returns:
            Oluşturulan event_id'lerin listesi
        """
        pass
    
    def generate_event_summary(self, cluster_items: List[int]) -> str:
        """
        Bir olay için otomatik özet oluştur.
        
        Args:
            cluster_items: Olay içindeki item_id'ler
            
        Returns:
            Özet metni
        """
        pass
    
    def generate_event_name(self, cluster_items: List[int]) -> str:
        """
        Bir olay için otomatik isim oluştur.
        
        Örnek: "15 Mart 2024 - İstanbul Taksim"
        
        Args:
            cluster_items: Olay içindeki item_id'ler
            
        Returns:
            Olay adı
        """
        pass

