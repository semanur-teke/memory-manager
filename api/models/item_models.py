"""
Item ile ilgili Pydantic request/response semalari.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ItemResponse(BaseModel):
    """Tekil item detay response'u."""
    item_id: int
    file_path: str
    type: str
    has_consent: bool
    is_rotated: bool
    creation_datetime: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    transcription: Optional[str] = None
    event_id: Optional[int] = None

    model_config = {"from_attributes": True}


class ItemListResponse(BaseModel):
    """Sayfalanmis item listesi response'u."""
    items: List[ItemResponse]
    total: int
    page: int
    size: int


class ThumbnailResponse(BaseModel):
    """Base64 thumbnail response'u."""
    item_id: int
    thumbnail: str  # base64 encoded JPEG


class ImportFolderRequest(BaseModel):
    """Klasor import istegi."""
    path: str
    consent: bool
    recursive: bool = True


class ImportPhotoRequest(BaseModel):
    """Tekil fotograf import istegi."""
    path: str
    consent: bool


class ImportPhotoResponse(BaseModel):
    """Tekil fotograf import sonucu."""
    status: str  # "imported" | "duplicate" | "no_consent" | "error"
