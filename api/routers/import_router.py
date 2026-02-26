"""
Import endpoint'leri.
Fotograf ve ses dosyalarinin ice aktarilmasi.
SSE (Server-Sent Events) ile gercek zamanli ilerleme bildirimi.
"""

import json
import asyncio
import logging
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session

from api.dependencies import get_db_session, get_clip_embedder, get_faiss_manager
from api.models.item_models import ImportFolderRequest, ImportPhotoRequest, ImportPhotoResponse

router = APIRouter(prefix="/api/import", tags=["Import"])
logger = logging.getLogger(__name__)


async def _import_folder_stream(
    folder_path: str, consent: bool, recursive: bool, db: Session
) -> AsyncGenerator[dict, None]:
    """
    Klasor import islemini SSE stream olarak yayinlar.
    Her dosya islendikten sonra progress event'i gonderir.
    """
    from src.ingestion.photo_importer import PhotoImporter

    importer = PhotoImporter(db, clip_embedder=get_clip_embedder(), faiss_manager=get_faiss_manager())
    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        yield {"event": "error", "data": json.dumps({"detail": "Klasor bulunamadi"})}
        return

    files = importer.find_image_files(folder, recursive)
    total = len(files)

    if total == 0:
        yield {"event": "complete", "data": json.dumps({
            "imported": 0, "skipped_duplicates": 0, "errors": 0, "total_found": 0
        })}
        return

    stats = {"imported": 0, "skipped_duplicates": 0, "errors": 0}

    for i, file_path in enumerate(files, 1):
        try:
            result = importer.import_single_photo(file_path, consent)
        except Exception as e:
            logger.error(f"Import hatasi ({file_path.name}): {e}")
            result = "error"

        if result == "imported":
            stats["imported"] += 1
        elif result == "duplicate":
            stats["skipped_duplicates"] += 1
        else:
            stats["errors"] += 1

        # Progress event gonder
        yield {
            "event": "progress",
            "data": json.dumps({
                "current": i,
                "total": total,
                "status": result,
                "file": file_path.name,
            }),
        }

        # Event loop'un nefes almasina izin ver (UI donmasin)
        await asyncio.sleep(0)

    # Tamamlandi event'i
    yield {
        "event": "complete",
        "data": json.dumps({
            "imported": stats["imported"],
            "skipped_duplicates": stats["skipped_duplicates"],
            "errors": stats["errors"],
            "total_found": total,
        }),
    }


@router.post("/folder")
async def import_folder(request: ImportFolderRequest, db: Session = Depends(get_db_session)):
    """
    POST /api/import/folder
    Klasorden toplu fotograf import (SSE stream ile ilerleme).
    """
    logger.info(f"Import basladi: {request.path} (consent={request.consent}, recursive={request.recursive})")

    return EventSourceResponse(
        _import_folder_stream(request.path, request.consent, request.recursive, db)
    )


@router.post("/photo")
async def import_photo(request: ImportPhotoRequest, db: Session = Depends(get_db_session)):
    """
    POST /api/import/photo
    Tekil fotograf import.
    """
    from src.ingestion.photo_importer import PhotoImporter

    importer = PhotoImporter(db, clip_embedder=get_clip_embedder(), faiss_manager=get_faiss_manager())
    file_path = Path(request.path)

    if not file_path.exists():
        return JSONResponse(status_code=404, content={"detail": "Dosya bulunamadi"})

    result = importer.import_single_photo(file_path, request.consent)
    logger.info(f"Tekil import: {file_path.name} -> {result}")

    return ImportPhotoResponse(status=result)
