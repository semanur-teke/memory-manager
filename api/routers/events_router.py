"""
Olay (Event) endpoint'leri.
Olay listeleme, detay, kumeleme, guncelleme, silme.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/events", tags=["Events"])


async def get_events():
    """GET /api/events
    Sayfalanmis olay listesi (kapak fotografi dahil).
    Query: page, size
    """
    pass


async def get_event(event_id: int):
    """GET /api/events/{id}
    Olay detayi (item'lar ve flashcard'lar dahil).
    """
    pass


async def trigger_clustering():
    """POST /api/events/cluster
    DBSCAN kumeleme baslatma (SSE stream ile ilerleme).
    Uzun islem — background task.
    """
    pass


async def update_event(event_id: int):
    """PUT /api/events/{id}
    Olay bilgilerini guncelle.
    Body: { title, main_location, summary }
    """
    pass


async def delete_event(event_id: int):
    """DELETE /api/events/{id}
    Olay silme.
    UYARI: Cascade delete — Event + tum Item'lar + Flashcard'lar + ReviewLog'lar.
    """
    pass
