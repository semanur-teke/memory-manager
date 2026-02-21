"""
Arama ile ilgili Pydantic request/response semalari.
"""

from pydantic import BaseModel


class SearchRequest(BaseModel):
    """Birlesik arama request'i."""
    pass


class SearchResponse(BaseModel):
    """Arama sonuclari response'u."""
    pass


class AdvancedSearchRequest(BaseModel):
    """Gelismis arama request'i (yil, ay, sehir destekli)."""
    pass
