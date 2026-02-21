"""
Flashcard endpoint'leri.
Kart listeleme, bugunun kartlari, SM-2 tekrar degerlendirme.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/flashcards", tags=["Flashcards"])


async def get_flashcards():
    """GET /api/flashcards
    Tum flashcard listesi.
    """
    pass


async def get_due_today():
    """GET /api/flashcards/due-today
    Bugun tekrar edilecek kartlar (next_review_date <= today).
    """
    pass


async def submit_review(flashcard_id: int):
    """POST /api/flashcards/{id}/review
    SM-2 tekrar degerlendirme.
    Body: { rating: 1-5 }
    Response: { next_review_date, interval_days }
    """
    pass


async def delete_flashcard(flashcard_id: int):
    """DELETE /api/flashcards/{id}
    Flashcard silme.
    """
    pass
