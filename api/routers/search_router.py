"""
Arama endpoint'leri.
Simdilik DB-based arama (dosya adi, tarih, tur).
FAISS/CLIP hazir olunca semantik arama eklenecek.
"""

import logging
from typing import Optional, List
from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import extract, func

from api.dependencies import get_db_session, get_clip_embedder, get_faiss_manager
from api.models.item_models import ItemResponse
from database.schema import Item

router = APIRouter(prefix="/api/search", tags=["Search"])
logger = logging.getLogger(__name__)


# --- Request/Response modelleri ---

class SearchRequest(BaseModel):
    query: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: Optional[float] = 5.0
    k: int = 40


class AdvancedSearchRequest(BaseModel):
    query: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    city: Optional[str] = None
    type: Optional[str] = None
    radius_km: Optional[float] = 5.0
    k: int = 40


class SearchResultItem(BaseModel):
    item: ItemResponse
    score: float = 0.0
    source: str = "db"


class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    total: int
    filters_applied: dict


# --- Endpoints ---

def _db_fallback_search(request: SearchRequest, db: Session) -> SearchResponse:
    """FAISS kullanilamadiginda dosya adi / transcription LIKE aramasina duser."""
    query = db.query(Item).filter(Item.has_consent == True)
    filters_applied = {"text": False, "time": False, "location": False}

    if request.query:
        filters_applied["text"] = True
        search_term = f"%{request.query}%"
        query = query.filter(
            Item.file_path.ilike(search_term) |
            Item.transcription.ilike(search_term)
        )

    if request.start_date and request.end_date:
        filters_applied["time"] = True
        start_dt = datetime.combine(request.start_date, datetime.min.time())
        end_dt = datetime.combine(request.end_date, datetime.max.time())
        query = query.filter(
            Item.creation_datetime >= start_dt,
            Item.creation_datetime <= end_dt,
        )

    if request.lat is not None and request.lng is not None:
        filters_applied["location"] = True
        delta = request.radius_km / 111.0
        query = query.filter(
            Item.latitude.isnot(None),
            Item.longitude.isnot(None),
            Item.latitude >= request.lat - delta,
            Item.latitude <= request.lat + delta,
            Item.longitude >= request.lng - delta,
            Item.longitude <= request.lng + delta,
        )

    total = query.count()
    items = query.order_by(Item.creation_datetime.desc()).limit(request.k).all()

    results = [
        SearchResultItem(
            item=ItemResponse.model_validate(item),
            score=1.0,
            source="db",
        )
        for item in items
    ]

    return SearchResponse(results=results, total=total, filters_applied=filters_applied)


@router.post("")
async def search(request: SearchRequest, db: Session = Depends(get_db_session)):
    """
    POST /api/search
    Birlesik arama (metin + zaman + konum).
    Query varsa ve FAISS index doluysa semantik arama yapar,
    aksi halde DB-based LIKE aramasina duser.
    """
    # Semantik arama: query + dolu FAISS index gerekli
    if request.query:
        try:
            clip = get_clip_embedder()
            faiss_mgr = get_faiss_manager()

            if faiss_mgr.get_index_size() > 0:
                # Metin -> CLIP vektoru
                text_embedding = clip.encode_text(request.query)
                if text_embedding is not None:
                    # FAISS'te ara (en yakin 200 sonuc al, threshold ile filtrele)
                    faiss_results = faiss_mgr.search(text_embedding, k=min(200, faiss_mgr.get_index_size()))

                    if faiss_results:
                        item_ids = [item_id for item_id, _ in faiss_results if item_id is not None]
                        score_map = {item_id: dist for item_id, dist in faiss_results if item_id is not None}

                        # DB'den item bilgilerini cek (consent + varlik kontrolu)
                        db_query = db.query(Item).filter(
                            Item.has_consent == True,
                            Item.item_id.in_(item_ids),
                        )

                        # Ek tarih filtresi
                        if request.start_date and request.end_date:
                            start_dt = datetime.combine(request.start_date, datetime.min.time())
                            end_dt = datetime.combine(request.end_date, datetime.max.time())
                            db_query = db_query.filter(
                                Item.creation_datetime >= start_dt,
                                Item.creation_datetime <= end_dt,
                            )

                        # Ek konum filtresi
                        if request.lat is not None and request.lng is not None:
                            delta = request.radius_km / 111.0
                            db_query = db_query.filter(
                                Item.latitude.isnot(None),
                                Item.longitude.isnot(None),
                                Item.latitude >= request.lat - delta,
                                Item.latitude <= request.lat + delta,
                                Item.longitude >= request.lng - delta,
                                Item.longitude <= request.lng + delta,
                            )

                        items = db_query.all()

                        # Skor hesapla ve sirala (dusuk distance = yuksek benzerlik)
                        # min_score esigi: dusuk benzerlikli sonuclari filtrele
                        MIN_SCORE = 0.24
                        results = []
                        for item in items:
                            dist = score_map.get(item.item_id, 2.0)
                            score = max(0.0, 1.0 - dist / 2.0)
                            if score >= MIN_SCORE:
                                results.append(SearchResultItem(
                                    item=ItemResponse.model_validate(item),
                                    score=round(score, 4),
                                    source="semantic",
                                ))

                        results.sort(key=lambda r: r.score, reverse=True)

                        filters_applied = {
                            "text": True,
                            "time": bool(request.start_date and request.end_date),
                            "location": request.lat is not None and request.lng is not None,
                        }

                        logger.info(f"Semantik arama: query='{request.query}', {len(results)} sonuc")
                        return SearchResponse(
                            results=results,
                            total=len(results),
                            filters_applied=filters_applied,
                        )
        except Exception as e:
            logger.warning(f"Semantik arama basarisiz, DB fallback: {e}")

    # Fallback: DB-based LIKE aramasi
    return _db_fallback_search(request, db)


@router.post("/advanced")
async def advanced_search(request: AdvancedSearchRequest, db: Session = Depends(get_db_session)):
    """
    POST /api/search/advanced
    Gelismis arama (yil, ay, sehir, tur destekli).
    """
    query = db.query(Item).filter(Item.has_consent == True)
    filters_applied = {"text": False, "time": False, "location": False, "type": False}

    # Metin
    if request.query:
        filters_applied["text"] = True
        search_term = f"%{request.query}%"
        query = query.filter(
            Item.file_path.ilike(search_term) |
            Item.transcription.ilike(search_term)
        )

    # Yil / Ay
    if request.year:
        filters_applied["time"] = True
        query = query.filter(extract("year", Item.creation_datetime) == request.year)
    if request.month:
        filters_applied["time"] = True
        query = query.filter(extract("month", Item.creation_datetime) == request.month)

    # Tur
    if request.type:
        filters_applied["type"] = True
        query = query.filter(Item.type == request.type)

    total = query.count()
    items = query.order_by(Item.creation_datetime.desc()).limit(request.k).all()

    results = [
        SearchResultItem(
            item=ItemResponse.model_validate(item),
            score=1.0,
            source="db",
        )
        for item in items
    ]

    return SearchResponse(
        results=results,
        total=total,
        filters_applied=filters_applied,
    )
