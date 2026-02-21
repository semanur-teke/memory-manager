"""
Ayarlar endpoint'leri.
Sistem bilgisi, anahtar yedekleme, cache yonetimi.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/settings", tags=["Settings"])


async def get_system_info():
    """GET /api/settings/info
    Sistem bilgisi.
    Response: { db_size_mb, faiss_vectors, key_exists, cache_items }
    """
    pass


async def backup_key():
    """POST /api/settings/backup-key
    secret.key dosyasini yedekle.
    Body: { destination: "C:/Backup/secret.key" }
    """
    pass


async def clear_cache():
    """POST /api/settings/clear-cache
    Thumbnail cache temizle.
    """
    pass
