"""
Gizlilik yonetimi endpoint'leri.
Riza kontrolu, toplu islemler, guvenli silme, denetim logu.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/privacy", tags=["Privacy"])


async def get_privacy_stats():
    """GET /api/privacy/stats
    Riza istatistikleri: { consented, non_consented, total }
    """
    pass


async def get_privacy_items():
    """GET /api/privacy/items
    Tum item'lar (consent durumu farketmeksizin).
    Query: consent=all, page, size
    NOT: Thumbnail gosterilmez.
    """
    pass


async def set_consent(item_id: int):
    """PUT /api/privacy/{id}/consent
    Riza durumunu guncelle.
    Body: { status: true | false }
    """
    pass


async def delete_item(item_id: int):
    """DELETE /api/privacy/{id}
    Guvenli silme (secure_delete + DB kayit silme).
    """
    pass


async def bulk_consent():
    """POST /api/privacy/bulk-consent
    Toplu riza guncelleme.
    Body: { item_ids: [...], status: true | false }
    """
    pass


async def bulk_delete():
    """POST /api/privacy/bulk-delete
    Toplu guvenli silme.
    Body: { item_ids: [...] }
    """
    pass


async def get_audit_log():
    """GET /api/privacy/audit-log
    Denetim logu kayitlari.
    Query: limit=50
    """
    pass
