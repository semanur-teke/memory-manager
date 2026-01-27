"""
Unified Arama Motoru (Aşama 5)

Tüm arama türlerini birleştirir.
"""

from typing import List, Dict, Optional
from datetime import date
from .text_search import TextSearch
from .time_search import TimeSearch
from .location_search import LocationSearch


class SearchEngine:
    """
    Tüm arama fonksiyonlarını birleştiren ana sınıf.
    """
    
    def __init__(self, text_search: TextSearch, time_search: TimeSearch,
                 location_search: LocationSearch):
        """
        Args:
            text_search: Metin arama motoru
            time_search: Zaman arama motoru
            location_search: Konum arama motoru
        """
        self.text_search = text_search
        self.time_search = time_search
        self.location_search = location_search
    
    def search(self, query: str = None, start_date: Optional[date] = None,
               end_date: Optional[date] = None, location: Optional[tuple] = None,
               radius_km: float = 5.0, k: int = 10) -> Dict:
        """
        Kombine arama yap.
        
        Args:
            query: Metin sorgusu (opsiyonel)
            start_date: Başlangıç tarihi (opsiyonel)
            end_date: Bitiş tarihi (opsiyonel)
            location: (latitude, longitude) tuple (opsiyonel)
            radius_km: Konum araması için yarıçap
            k: Sonuç sayısı
            
        Returns:
            {
                'items': [...],
                'filters_applied': {
                    'text': bool,
                    'time': bool,
                    'location': bool
                }
            }
        """
        pass
    
    def advanced_search(self, filters: Dict) -> List[Dict]:
        """
        Gelişmiş arama (daha fazla filtre seçeneği).
        
        Args:
            filters: Filtre dict'i
            
        Returns:
            Öğe listesi
        """
        pass

