"""
Event ile ilgili Pydantic request/response semalari.
"""

from pydantic import BaseModel


class EventResponse(BaseModel):
    """Tekil event ozet response'u."""
    pass


class EventDetailResponse(BaseModel):
    """Event detay response'u (item'lar ve flashcard'lar dahil)."""
    pass


class EventUpdateRequest(BaseModel):
    """Event guncelleme request'i."""
    pass


class ClusterResponse(BaseModel):
    """Kumeleme sonuc response'u."""
    pass
