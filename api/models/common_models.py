"""
Ortak Pydantic modelleri.
Sayfalama, istatistik ve genel response semalari.
"""

from pydantic import BaseModel


class PaginationParams(BaseModel):
    """Sayfalama parametreleri."""
    pass


class StatsResponse(BaseModel):
    """Genel istatistik response'u."""
    pass


class ErrorResponse(BaseModel):
    """Hata response'u."""
    pass


class SuccessResponse(BaseModel):
    """Basarili islem response'u."""
    pass
