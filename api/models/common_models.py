"""
Ortak Pydantic modelleri.
Sayfalama, istatistik ve genel response semalari.
"""

from pydantic import BaseModel
from typing import Optional


class PaginationParams(BaseModel):
    """Sayfalama parametreleri."""
    page: int = 1
    size: int = 40


class StatsResponse(BaseModel):
    """Genel istatistik response'u."""
    consented: int
    non_consented: int
    total: int


class ErrorResponse(BaseModel):
    """Hata response'u."""
    detail: str


class SuccessResponse(BaseModel):
    """Basarili islem response'u."""
    message: str
