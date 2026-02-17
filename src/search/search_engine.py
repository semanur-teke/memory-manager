"""
Unified Arama Motoru (Aşama 5)

Tüm arama türlerini birleştirir.
"""

from typing import List, Dict, Optional
from datetime import date
from .text_search import TextSearch
from .time_search import TimeSearch
from .location_search import LocationSearch
from config import Config


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
               radius_km: float = Config.DEFAULT_SEARCH_RADIUS_KM,
               k: int = Config.DEFAULT_SEARCH_K) -> Dict:
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
        all_results = []
        filters_applied = {'text': False, 'time': False, 'location': False}

        # Metin araması
        if query:
            filters_applied['text'] = True
            text_results = self.text_search.search_all(query, k)
            for img in text_results.get('images', []):
                img['source'] = 'text_image'
                all_results.append(img)
            for txt in text_results.get('texts', []):
                txt['source'] = 'text_transcript'
                all_results.append(txt)

        # Zaman araması
        if start_date and end_date:
            filters_applied['time'] = True
            time_results = self.time_search.search_by_date_range(start_date, end_date)
            if time_results:
                for item in time_results:
                    item['source'] = 'time'
                    all_results.append(item)

        # Konum araması
        if location:
            filters_applied['location'] = True
            lat, lon = location
            loc_results = self.location_search.search_by_location(lat, lon, radius_km)
            if loc_results:
                for item in loc_results:
                    item['source'] = 'location'
                    all_results.append(item)

        # Birden fazla filtre varsa, kesişimi bul (item_id bazında)
        active_filters = [key for key, v in filters_applied.items() if v]
        if len(active_filters) > 1:
            all_results = self._intersect_results(all_results, active_filters)

        return {
            'items': all_results[:k],
            'filters_applied': filters_applied
        }

    def _intersect_results(self, results: List[Dict], active_filters: List[str]) -> List[Dict]:
        """Birden fazla filtre aktifse, tüm filtrelerde ortak olan item'ları döndürür."""
        # Her source'tan gelen item_id setlerini bul
        source_map = {}
        for r in results:
            source = r.get('source', '')
            # text_image ve text_transcript aynı filtre grubunda
            group = 'text' if source.startswith('text') else source
            if group not in source_map:
                source_map[group] = set()
            if 'item_id' in r:
                source_map[group].add(r['item_id'])

        # Tüm filtrelerde ortak olan item_id'ler
        if not source_map:
            return results
        common_ids = set.intersection(*source_map.values())

        # Score'a göre sırala (score yoksa 0)
        filtered = [r for r in results if r.get('item_id') in common_ids]
        filtered.sort(key=lambda x: x.get('score', 0), reverse=True)

        # Aynı item_id'den tekrar gelmesini engelle
        seen = set()
        unique = []
        for r in filtered:
            iid = r.get('item_id')
            if iid not in seen:
                seen.add(iid)
                unique.append(r)
        return unique

    def advanced_search(self, filters: Dict) -> List[Dict]:
        """
        Gelişmiş arama (daha fazla filtre seçeneği).

        Args:
            filters: Filtre dict'i
                - query: str (metin sorgusu)
                - start_date: date
                - end_date: date
                - year: int
                - month: int
                - location: (lat, lon)
                - city: str
                - radius_km: float
                - k: int

        Returns:
            Öğe listesi
        """
        query = filters.get('query')
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        year = filters.get('year')
        month = filters.get('month')
        location = filters.get('location')
        city = filters.get('city')
        radius_km = filters.get('radius_km', Config.DEFAULT_SEARCH_RADIUS_KM)
        k = filters.get('k', Config.DEFAULT_SEARCH_K)

        # Yıl/ay verilmişse tarih aralığına çevir
        if year and not (start_date and end_date):
            if month:
                # Ayın son gününü hesapla
                if month == 12:
                    end = date(year + 1, 1, 1)
                else:
                    end = date(year, month + 1, 1)
                start_date = date(year, month, 1)
                end_date = end
            else:
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)

        # Şehir adı verilmişse koordinata çevir
        if city and not location:
            city_results = self.location_search.search_by_city(city, radius_km)
            if city_results:
                return city_results[:k]
            return []

        result = self.search(
            query=query,
            start_date=start_date,
            end_date=end_date,
            location=location,
            radius_km=radius_km,
            k=k
        )
        return result['items']
