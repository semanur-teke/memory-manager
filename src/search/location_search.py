"""
Konuma Göre Arama (Aşama 5.3) - Geopy Entegrasyonu
"""

from typing import List, Dict, Optional
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from sqlalchemy.orm import Session
from database.schema import Item

class LocationSearch:
    def __init__(self, db_connection: Session):
        self.db = db_connection
        # User-agent kısmına kendi proje adını yazman önemli (OpenStreetMap kuralı)
        self.geocoder = Nominatim(user_agent="MemoryManager_App_v1")

    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Geopy'nin 'geodesic' (jeodezik) yöntemini kullanarak mesafe hesaplar.
        Dünya'nın tam küre olmadığını (elipsoid olduğunu) hesaba katar, daha hassastır.
        """
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers

    def search_by_location(self, latitude: float, longitude: float, 
                          radius_km: float = 5.0) -> List[Dict]:
        """Koordinat çevresindeki öğeleri getirir."""
        items = self.db.query(Item).filter(
            Item.latitude.isnot(None),
            Item.has_consent == True
        ).all()
        results = []

        for item in items:
            dist = self.calculate_distance(latitude, longitude, item.latitude, item.longitude)
            if dist <= radius_km:
                results.append({
                    'item_id': item.item_id,
                    'distance_km': round(dist, 2),
                    'location': (item.latitude, item.longitude)
                })
        return sorted(results, key=lambda x: x['distance_km'])

    def search_by_city(self, city_name: str, radius_km: float = 20.0) -> List[Dict]:
        """
        Geopy kullanarak şehir adını koordinata çevirir ve arama yapar.
        """
        try:
            # Şehri buluyoruz
            location = self.geocoder.geocode(city_name)
            if location:
                print(f"Arama merkezi: ({location.latitude}, {location.longitude})")
                return self.search_by_location(location.latitude, location.longitude, radius_km)
            else:
                print(f"HATA: '{city_name}' konumu bulunamadi.")
                return []
        except Exception as e:
            print(f"Geocoding hatasi: {e}")
            return []
