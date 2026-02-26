"""
Galeri endpoint'leri.
Fotograf listeleme, detay, thumbnail ve tam boyut gosterim.
Thumbnail'lar LRU cache ile bellekte tutulur.
"""

import io
import base64
import logging
from pathlib import Path
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from PIL import Image

from api.dependencies import get_db_session, get_encryption_manager, get_clip_embedder, get_faiss_manager
from api.models.item_models import ItemResponse, ItemListResponse, ThumbnailResponse
from api.models.common_models import SuccessResponse
from database.schema import Item
from security.encryption_manager import EncryptionManager
from config import Config

router = APIRouter(prefix="/api/items", tags=["Gallery"])
logger = logging.getLogger(__name__)

# Thumbnail LRU cache — max 500 item bellekte tutulur
_thumbnail_cache: dict[int, str] = {}
_CACHE_MAX = Config.THUMBNAIL_CACHE_MAX_SIZE


def _make_thumbnail(image_bytes: bytes) -> bytes:
    """Ham goruntu verisinden 200x200 JPEG thumbnail olusturur."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail(Config.THUMBNAIL_SIZE)
        if img.mode != "RGB":
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=Config.THUMBNAIL_QUALITY)
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Thumbnail olusturulamadi: {e}")
        return None


def _resize_fullsize(image_bytes: bytes) -> bytes:
    """Goruntu boyutunu max 2000px'e dusurur, JPEG olarak doner."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        max_size = Config.IMAGE_MAX_SIZE
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size))
        if img.mode != "RGB":
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Fullsize goruntu islenemedi: {e}")
        return None


@router.get("")
async def get_items(
    page: int = Query(1, ge=1),
    size: int = Query(40, ge=1, le=100),
    year: Optional[int] = None,
    month: Optional[int] = None,
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    type: Optional[str] = None,
    db: Session = Depends(get_db_session),
):
    """
    GET /api/items
    Sayfalanmis item listesi. Sadece has_consent=True doner.
    """
    query = db.query(Item).filter(Item.has_consent == True)

    if year:
        from sqlalchemy import extract
        query = query.filter(extract("year", Item.creation_datetime) == year)
    if month:
        from sqlalchemy import extract
        query = query.filter(extract("month", Item.creation_datetime) == month)
    if type:
        query = query.filter(Item.type == type)

    total = query.count()

    if sort == "desc":
        query = query.order_by(Item.creation_datetime.desc())
    else:
        query = query.order_by(Item.creation_datetime.asc())

    items = query.offset((page - 1) * size).limit(size).all()

    # Dosyasi diskten silinmis item'lari filtrele
    valid_items = [item for item in items if Path(item.file_path).exists()]
    orphan_count = len(items) - len(valid_items)
    if orphan_count > 0:
        logger.warning(f"{orphan_count} item'in dosyasi diskten silinmis — galeriden gizleniyor")

    return ItemListResponse(
        items=[ItemResponse.model_validate(item) for item in valid_items],
        total=total - orphan_count,
        page=page,
        size=size,
    )


@router.post("/repair")
async def repair_double_encrypted(
    db: Session = Depends(get_db_session),
    enc: EncryptionManager = Depends(get_encryption_manager),
):
    """
    POST /api/items/repair
    Cift sifrelenmis dosyalari tespit edip tek katmana dusurur.
    """
    from cryptography.fernet import InvalidToken

    all_items = db.query(Item).all()
    repaired = 0
    failed = 0

    for item in all_items:
        path = Path(item.file_path)
        if not path.exists():
            continue

        try:
            data = path.read_bytes()
            # Ilk decrypt — dis katman
            inner = enc.cipher.decrypt(data)
            # Ikinci decrypt — ic katman (eger basariliysa cift sifrelidir)
            try:
                original = enc.cipher.decrypt(inner)
                # Cift sifreli! Tek katman olarak yeniden yaz
                path.write_bytes(enc.cipher.encrypt(original))
                repaired += 1
                logger.info(f"Cift sifreleme duzeltildi: item {item.item_id} ({item.file_path})")
            except InvalidToken:
                pass  # Tek katman, sorun yok
        except InvalidToken:
            failed += 1
            logger.warning(f"Dosya decrypt edilemedi: item {item.item_id} ({item.file_path})")

    return SuccessResponse(message=f"{repaired} dosya onarildi, {failed} dosya okunamadi")


@router.delete("/cleanup")
async def cleanup_orphans(db: Session = Depends(get_db_session)):
    """
    DELETE /api/items/cleanup
    Dosyasi diskten silinmis DB kayitlarini temizler.
    """
    all_items = db.query(Item).all()
    deleted = 0
    for item in all_items:
        if not Path(item.file_path).exists():
            logger.info(f"Orphan temizlendi: item {item.item_id} ({item.file_path})")
            db.delete(item)
            deleted += 1

    db.commit()
    logger.info(f"Toplam {deleted} orphan kayit temizlendi")
    return SuccessResponse(message=f"{deleted} orphan kayit temizlendi")


@router.post("/reindex")
async def reindex_embeddings(db: Session = Depends(get_db_session)):
    """
    POST /api/items/reindex
    faiss_index_id'si NULL olan item'lari bulur, CLIP embedding uretir,
    FAISS'e ekler ve DB'yi gunceller.
    """
    clip = get_clip_embedder()
    faiss_mgr = get_faiss_manager()

    # faiss_index_id'si olmayan item'lari bul
    items = db.query(Item).filter(
        Item.faiss_index_id.is_(None),
        Item.has_consent == True,
    ).all()

    if not items:
        return {"reindexed": 0, "failed": 0, "message": "Reindex edilecek item yok"}

    reindexed = 0
    failed = 0

    for item in items:
        if not Path(item.file_path).exists():
            failed += 1
            continue

        try:
            embedding = clip.encode_image(Path(item.file_path))
            if embedding is None:
                failed += 1
                continue

            faiss_ids = faiss_mgr.add_embeddings(embedding, [item.item_id])
            if faiss_ids:
                item.faiss_index_id = faiss_ids[0]
                db.commit()
                reindexed += 1
                logger.info(f"Reindex basarili: item {item.item_id} -> faiss_id {faiss_ids[0]}")
            else:
                failed += 1
        except Exception as e:
            logger.warning(f"Reindex hatasi (item {item.item_id}): {e}")
            failed += 1

    logger.info(f"Reindex tamamlandi: {reindexed} basarili, {failed} basarisiz")
    return {
        "reindexed": reindexed,
        "failed": failed,
        "message": f"{reindexed} item reindex edildi",
    }


@router.get("/{item_id}")
async def get_item(
    item_id: int,
    db: Session = Depends(get_db_session),
):
    """GET /api/items/{id} — Tekil item detayi."""
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item bulunamadi")
    return ItemResponse.model_validate(item)


@router.get("/{item_id}/thumbnail")
async def get_thumbnail(
    item_id: int,
    db: Session = Depends(get_db_session),
    enc: EncryptionManager = Depends(get_encryption_manager),
):
    """
    GET /api/items/{id}/thumbnail
    200x200 JPEG base64 thumbnail. LRU cache (max 500 item).
    """
    # Cache kontrol
    if item_id in _thumbnail_cache:
        return ThumbnailResponse(item_id=item_id, thumbnail=_thumbnail_cache[item_id])

    item = db.query(Item).filter(Item.item_id == item_id, Item.has_consent == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item bulunamadi veya riza yok")

    # Sifreli dosyayi coz
    try:
        decrypted = enc.decrypt_file(item.file_path)
    except Exception as e:
        logger.error(f"Thumbnail decrypt hatasi (item {item_id}): {e}")
        raise HTTPException(status_code=422, detail="Dosya cozulemedi — sifreleme hatasi")
    if not decrypted:
        raise HTTPException(status_code=500, detail="Dosya cozulemedi")

    # Thumbnail olustur ve base64'e cevir
    thumb_bytes = _make_thumbnail(decrypted)
    if not thumb_bytes:
        raise HTTPException(status_code=422, detail="Goruntu isleme hatasi — dosya bozuk olabilir")
    b64 = base64.b64encode(thumb_bytes).decode()

    # Cache'e kaydet (max boyut kontrolu)
    if len(_thumbnail_cache) >= _CACHE_MAX:
        # En eski entry'yi sil (FIFO)
        oldest_key = next(iter(_thumbnail_cache))
        del _thumbnail_cache[oldest_key]
    _thumbnail_cache[item_id] = b64

    return ThumbnailResponse(item_id=item_id, thumbnail=b64)


@router.get("/{item_id}/debug")
async def debug_item(
    item_id: int,
    db: Session = Depends(get_db_session),
):
    """
    GET /api/items/{id}/debug
    Test endpoint'i: item'in DB'deki tum raw verisini doner.
    Metadata dogrulugunu kontrol etmek icin kullanilir.
    """
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item bulunamadi")
    return {
        "item_id": item.item_id,
        "file_path": item.file_path,
        "file_hash": item.file_hash,
        "type": item.type,
        "creation_datetime": item.creation_datetime.isoformat() if item.creation_datetime else None,
        "latitude": item.latitude,
        "longitude": item.longitude,
        "has_consent": item.has_consent,
        "is_rotated": item.is_rotated,
        "transcription": item.transcription,
        "event_id": item.event_id,
        "faiss_index_id": item.faiss_index_id,
        "file_exists": Path(item.file_path).exists(),
    }


@router.get("/{item_id}/fullsize")
async def get_fullsize(
    item_id: int,
    db: Session = Depends(get_db_session),
    enc: EncryptionManager = Depends(get_encryption_manager),
):
    """
    GET /api/items/{id}/fullsize
    Orijinal cozunurluk (max 2000px) binary JPEG stream.
    Base64 KULLANILMAZ — buyuk dosyalarda %33 overhead olur.
    """
    item = db.query(Item).filter(Item.item_id == item_id, Item.has_consent == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item bulunamadi veya riza yok")

    try:
        decrypted = enc.decrypt_file(item.file_path)
    except Exception as e:
        logger.error(f"Fullsize decrypt hatasi (item {item_id}): {e}")
        raise HTTPException(status_code=422, detail="Dosya cozulemedi — sifreleme hatasi")
    if not decrypted:
        raise HTTPException(status_code=500, detail="Dosya cozulemedi")

    jpeg_bytes = _resize_fullsize(decrypted)
    if not jpeg_bytes:
        raise HTTPException(status_code=422, detail="Goruntu isleme hatasi — dosya bozuk olabilir")

    return StreamingResponse(
        io.BytesIO(jpeg_bytes),
        media_type="image/jpeg",
        headers={"Content-Length": str(len(jpeg_bytes))},
    )


