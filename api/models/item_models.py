"""
Item ile ilgili Pydantic request/response semalari.
"""

from pydantic import BaseModel


class ItemResponse(BaseModel):
    """Tekil item detay response'u."""
    pass


class ItemListResponse(BaseModel):
    """Sayfalanmis item listesi response'u."""
    pass


class ThumbnailResponse(BaseModel):
    """Base64 thumbnail response'u."""
    pass


class FullsizeResponse(BaseModel):
    """Base64 tam boyut fotograf response'u."""
    pass
