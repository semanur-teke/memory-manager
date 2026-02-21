"""
Import endpoint'leri.
Fotograf ve ses dosyalarinin ice aktarilmasi.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/import", tags=["Import"])


async def import_folder():
    """POST /api/import/folder
    Klasorden toplu fotograf import (SSE stream ile ilerleme).
    Body: { path, consent, recursive }
    """
    pass


async def import_photo():
    """POST /api/import/photo
    Tekil fotograf import.
    Body: { path, consent }
    Response: { status: imported | duplicate | no_consent | error }
    """
    pass
