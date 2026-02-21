"""
Flashcard ile ilgili Pydantic request/response semalari.
"""

from pydantic import BaseModel


class FlashcardResponse(BaseModel):
    """Tekil flashcard response'u."""
    pass


class FlashcardListResponse(BaseModel):
    """Flashcard listesi response'u."""
    pass


class ReviewRequest(BaseModel):
    """SM-2 tekrar degerlendirme request'i."""
    pass


class ReviewResponse(BaseModel):
    """Tekrar sonuc response'u (sonraki tekrar tarihi)."""
    pass
