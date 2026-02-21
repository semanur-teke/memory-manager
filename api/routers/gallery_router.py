"""
Galeri endpoint'leri.
Fotograf listeleme, detay, thumbnail ve tam boyut gosterim.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/items", tags=["Gallery"])


async def get_items():
    """GET /api/items
    Sayfalanmis item listesi.
    Query: page, size, year, month, sort, type
    Sadece has_consent=True doner.
    """
    pass


async def get_item(item_id: int):
    """GET /api/items/{id}
    Tekil item detayi (metadata dahil).
    """
    pass


async def get_thumbnail(item_id: int):
    """GET /api/items/{id}/thumbnail
    200x200 JPEG base64 thumbnail.
    LRU cache (max 500 item).
    """
    pass


async def get_fullsize(item_id: int):
    """GET /api/items/{id}/fullsize
    Orijinal cozunurluk (max 2000px) base64 fotograf.
    """
    pass
