"""
Zaman cizelgesi endpoint'leri.
Yillik/aylik istatistikler ve kronolojik listeleme.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/timeline", tags=["Timeline"])


async def get_timeline_stats():
    """GET /api/timeline/stats
    Genel zaman istatistikleri.
    Response: { earliest_date, latest_date, total_items, by_year, by_month }
    """
    pass


async def get_by_year(year: int):
    """GET /api/timeline/{year}
    Belirli yildaki item'lar.
    """
    pass


async def get_by_month(year: int, month: int):
    """GET /api/timeline/{year}/{month}
    Belirli ay'daki item'lar.
    """
    pass
