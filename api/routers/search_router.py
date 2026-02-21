"""
Arama endpoint'leri.
Semantik metin, zaman, konum ve birlesik arama.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/search", tags=["Search"])


async def search():
    """POST /api/search
    Birlesik arama (metin + zaman + konum).
    Body: { query, start_date, end_date, lat, lng, radius_km, k }
    """
    pass


async def advanced_search():
    """POST /api/search/advanced
    Gelismis arama (yil, ay, sehir destekli).
    Body: { query, year, month, city, radius_km, k }
    """
    pass
