"""
DBSCAN Kümeleme (Aşama 6.1)

Zaman ve konum bazlı ön-kümeleme yapar.
"""

from typing import List, Dict, Tuple
from datetime import datetime
import numpy as np
from sklearn.cluster import DBSCAN


class DBSCANClusterer:
    """
    DBSCAN algoritması ile zaman ve konum bazlı kümeleme yapar.
    """
    
    def __init__(self, time_threshold_hours: float = 3.0, 
                 location_threshold_km: float = 1.0):
        """
        Args:
            time_threshold_hours: Aynı olay için maksimum zaman farkı (saat)
            location_threshold_km: Aynı olay için maksimum konum farkı (km)
        """
        self.time_threshold_hours = time_threshold_hours
        self.location_threshold_km = location_threshold_km
    
    def cluster_by_time_and_location(self, items: List[Dict]) -> List[List[int]]:
        """
        Öğeleri zaman ve konuma göre kümele.
        
        Args:
            items: [{'item_id': int, 'created_at': datetime, 
                    'location_lat': float, 'location_lng': float}, ...]
            
        Returns:
            Her küme için item_id listesi: [[id1, id2, ...], [id3, id4, ...], ...]
        """
        pass
    
    def prepare_features(self, items: List[Dict]) -> np.ndarray:
        """
        Öğeleri DBSCAN için feature vektörlerine çevir.
        
        Feature'lar:
        - Zaman (timestamp olarak)
        - Konum (lat, lng)
        
        Args:
            items: Öğe listesi
            
        Returns:
            (N, 3) shape'inde numpy array: [timestamp, lat, lng]
        """
        pass
    
    def normalize_features(self, features: np.ndarray) -> np.ndarray:
        """
        Feature'ları normalize et (DBSCAN için önemli).
        
        Args:
            features: Ham feature array
            
        Returns:
            Normalize edilmiş feature array
        """
        pass
    
    def calculate_distance_matrix(self, features: np.ndarray) -> np.ndarray:
        """
        Öğeler arası mesafe matrisini hesapla.
        
        Args:
            features: Feature array
            
        Returns:
            (N, N) mesafe matrisi
        """
        pass
    
    def filter_small_clusters(self, clusters: List[List[int]], 
                             min_size: int = 2) -> List[List[int]]:
        """
        Çok küçük kümeleri filtrele (gürültü olarak işaretle).
        
        Args:
            clusters: Küme listesi
            min_size: Minimum küme boyutu
            
        Returns:
            Filtrelenmiş küme listesi
        """
        pass

