"""
Gizlilik yonetimi endpoint'leri.
Riza kontrolu, toplu islemler, guvenli silme, denetim logu.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db_session, get_privacy_manager, get_encryption_manager
from api.models.item_models import ItemResponse, ItemListResponse
from api.models.common_models import StatsResponse, SuccessResponse
from database.schema import Item
from security.security_manager import PrivacyManager

router = APIRouter(prefix="/api/privacy", tags=["Privacy"])
logger = logging.getLogger(__name__)


# --- Request/Response modelleri ---

class ConsentUpdateRequest(BaseModel):
    status: bool


class BulkConsentRequest(BaseModel):
    item_ids: List[int]
    status: bool


class BulkDeleteRequest(BaseModel):
    item_ids: List[int]


class AuditLogEntry(BaseModel):
    timestamp: str
    action: str
    details: str


# --- Endpoints ---

@router.get("/stats")
async def get_privacy_stats(db: Session = Depends(get_db_session)):
    """
    GET /api/privacy/stats
    Riza istatistikleri: consented, non_consented, total
    """
    total = db.query(Item).count()
    consented = db.query(Item).filter(Item.has_consent == True).count()
    non_consented = total - consented

    return StatsResponse(
        consented=consented,
        non_consented=non_consented,
        total=total,
    )


@router.get("/items")
async def get_privacy_items(
    consent: Optional[str] = Query("all", pattern="^(all|true|false)$"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_session),
):
    """
    GET /api/privacy/items
    Tum item'lar (consent durumu farketmeksizin).
    Thumbnail gosterilmez — sadece metadata.
    """
    query = db.query(Item)

    if consent == "true":
        query = query.filter(Item.has_consent == True)
    elif consent == "false":
        query = query.filter(Item.has_consent == False)
    # "all" ise filtre yok

    total = query.count()
    items = query.order_by(Item.creation_datetime.desc()).offset((page - 1) * size).limit(size).all()

    return ItemListResponse(
        items=[ItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
    )


@router.put("/{item_id}/consent")
async def set_consent(
    item_id: int,
    request: ConsentUpdateRequest,
    db: Session = Depends(get_db_session),
    privacy: PrivacyManager = Depends(get_privacy_manager),
):
    """
    PUT /api/privacy/{id}/consent
    Riza durumunu guncelle.
    """
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item bulunamadi")

    privacy.set_consent(item_id, request.status)
    logger.info(f"Riza guncellendi: item {item_id} -> {request.status}")
    return SuccessResponse(message=f"Riza {'verildi' if request.status else 'kaldirildi'}")


@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db_session),
    privacy: PrivacyManager = Depends(get_privacy_manager),
):
    """
    DELETE /api/privacy/{id}
    Guvenli silme (secure_delete + DB kayit silme).
    """
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item bulunamadi")

    # Dosyayi diskten guvenli sil
    privacy.secure_delete(item.file_path)

    # DB kaydini sil
    db.delete(item)
    db.commit()

    logger.info(f"Item guvenli silindi: {item_id}")
    return SuccessResponse(message="Item guvenli sekilde silindi")


@router.post("/bulk-consent")
async def bulk_consent(
    request: BulkConsentRequest,
    db: Session = Depends(get_db_session),
    privacy: PrivacyManager = Depends(get_privacy_manager),
):
    """
    POST /api/privacy/bulk-consent
    Toplu riza guncelleme.
    """
    updated = 0
    for item_id in request.item_ids:
        item = db.query(Item).filter(Item.item_id == item_id).first()
        if item:
            privacy.set_consent(item_id, request.status)
            updated += 1

    logger.info(f"Toplu riza guncellendi: {updated} item -> {request.status}")
    return SuccessResponse(message=f"{updated} item guncellendi")


@router.post("/bulk-delete")
async def bulk_delete(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db_session),
    privacy: PrivacyManager = Depends(get_privacy_manager),
):
    """
    POST /api/privacy/bulk-delete
    Toplu guvenli silme.
    """
    deleted = 0
    for item_id in request.item_ids:
        item = db.query(Item).filter(Item.item_id == item_id).first()
        if item:
            privacy.secure_delete(item.file_path)
            db.delete(item)
            deleted += 1
    db.commit()

    logger.info(f"Toplu guvenli silme: {deleted} item")
    return SuccessResponse(message=f"{deleted} item guvenli sekilde silindi")


@router.get("/audit-log")
async def get_audit_log(limit: int = Query(50, ge=1, le=200)):
    """
    GET /api/privacy/audit-log
    Denetim logu kayitlari.
    Simdilik log dosyasindan son satirlari okur.
    """
    import os
    from pathlib import Path

    log_entries = []
    log_path = Path("logs/app.log")

    if log_path.exists():
        try:
            lines = log_path.read_text(encoding="utf-8", errors="ignore").strip().split("\n")
            # Sadece privacy ile ilgili satirlari filtrele
            privacy_keywords = ["CONSENT", "SECURE_DELETE", "DELETE", "PRIVACY"]
            filtered = [
                line for line in lines
                if any(kw in line.upper() for kw in privacy_keywords)
            ]
            # Son 'limit' kaydi al
            for line in filtered[-limit:]:
                parts = line.split(" ", 2)
                log_entries.append(AuditLogEntry(
                    timestamp=parts[0] if len(parts) > 0 else "",
                    action=parts[1] if len(parts) > 1 else "",
                    details=parts[2] if len(parts) > 2 else line,
                ))
        except Exception as e:
            logger.error(f"Audit log okuma hatasi: {e}")

    return log_entries
