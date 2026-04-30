"""
SM-2 Aralikli Tekrar Zamanlayicisi (Asama 10)

SuperMemo SM-2 algoritmasini kullanarak flashcard tekrar
zamanlamasini hesaplar. ReviewLog tablosunu kullanir.
Kullanici puanina (1-5) gore next_review_date gunceller.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from database.schema import Flashcard, ReviewLog, Event, Item
from security.encryption_manager import EncryptionManager
from config import Config

logger = logging.getLogger(__name__)


class SM2Scheduler:
    """
    SM-2 (SuperMemo 2) aralikli tekrar algoritmasi.

    Algoritma ozeti:
    - Kullanici her flashcard'a 1-5 arasi puan verir
    - Puan >= 3: basarili tekrar, aralik artar
    - Puan < 3: basarisiz, aralik sifirlanir
    - EF (easiness factor) her tekrarda guncellenir
    - next_review_date hesaplanarak ReviewLog'a yazilir
    """

    def __init__(self, db_connection):
        """
        Args:
            db_connection: Veritabani baglantisi (ReviewLog tablosu icin)
        """
        self.db = db_connection
        self.encryption_manager = EncryptionManager()

    def _validate_rating(self, user_rating: int) -> None:
        """Kullanici puanini dogrula."""
        if not isinstance(user_rating, int) or not (1 <= user_rating <= 5):
            raise ValueError("user_rating 1 ile 5 arasinda bir tamsayi olmali.")

    def _safe_decrypt(self, encrypted_text: Optional[str]) -> Optional[str]:
        """
        Metni guvenli sekilde decrypt et.
        Cozulemezse ham metni dondur.
        """
        if not encrypted_text:
            return encrypted_text

        try:
            return self.encryption_manager.decrypt_string(encrypted_text)
        except Exception as exc:
            logger.warning("Metin decrypt edilemedi, ham veri donduruluyor: %s", exc)
            return encrypted_text

    def _get_flashcard(self, flashcard_id: int) -> Flashcard:
        """Flashcard'i getir, yoksa hata ver."""
        flashcard = (
            self.db.query(Flashcard)
            .filter(Flashcard.flashcard_id == flashcard_id)
            .first()
        )
        if flashcard is None:
            raise ValueError(f"Flashcard bulunamadi: {flashcard_id}")
        return flashcard

    def _get_review_logs(self, flashcard_id: int) -> List[ReviewLog]:
        """Flashcard'in tum review gecmisini tarih sirasina gore getir."""
        return (
            self.db.query(ReviewLog)
            .filter(ReviewLog.flashcard_id == flashcard_id)
            .order_by(ReviewLog.review_date.asc(), ReviewLog.log_id.asc())
            .all()
        )

    def _reconstruct_state(self, flashcard_id: int) -> Dict:
        """
        ReviewLog gecmisinden mevcut SM-2 durumunu yeniden hesapla.

        Returns:
            {
                'repetition_number': int,
                'easiness_factor': float,
                'interval_days': int,
                'next_review_date': Optional[datetime],
                'total_reviews': int
            }
        """
        logs = self._get_review_logs(flashcard_id)

        repetition_number = 0
        easiness_factor = Config.SM2_INITIAL_EF
        interval_days = 0
        next_review_date = None

        for log in logs:
            rating = log.user_rating
            easiness_factor = self.calculate_easiness_factor(easiness_factor, rating)

            if rating >= 3:
                interval_days = self.calculate_interval(
                    repetition_number=repetition_number,
                    easiness_factor=easiness_factor,
                    previous_interval=interval_days,
                )
                repetition_number += 1
            else:
                repetition_number = 0
                interval_days = 1

            next_review_date = log.next_review_date

        return {
            "repetition_number": repetition_number,
            "easiness_factor": easiness_factor,
            "interval_days": interval_days,
            "next_review_date": next_review_date,
            "total_reviews": len(logs),
        }

    def calculate_next_review(self, flashcard_id: int, user_rating: int) -> datetime:
        """
        Kullanici puanina gore bir sonraki tekrar tarihini hesapla.

        SM-2 Algoritmasi:
        - n=0: interval = 1 gun
        - n=1: interval = 6 gun
        - n>=2: interval = onceki_interval * EF
        - EF = EF + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
        - EF minimum 1.3

        Args:
            flashcard_id: Tekrarlanan flashcard'in ID'si
            user_rating: Kullanici puani (1-5)

        Returns:
            Bir sonraki tekrar tarihi
        """
        self._validate_rating(user_rating)
        self._get_flashcard(flashcard_id)

        state = self._reconstruct_state(flashcard_id)
        current_repetition = state["repetition_number"]
        current_ef = state["easiness_factor"]
        previous_interval = state["interval_days"]

        new_ef = self.calculate_easiness_factor(current_ef, user_rating)

        if user_rating >= 3:
            interval_days = self.calculate_interval(
                repetition_number=current_repetition,
                easiness_factor=new_ef,
                previous_interval=previous_interval,
            )
        else:
            interval_days = 1

        next_review_date = datetime.utcnow() + timedelta(days=interval_days)

        logger.info(
            "Next review hesaplandi | flashcard_id=%s rating=%s interval=%s next_review=%s",
            flashcard_id,
            user_rating,
            interval_days,
            next_review_date,
        )

        return next_review_date

    def calculate_easiness_factor(self, current_ef: float, user_rating: int) -> float:
        """
        Kolaylik faktorunu (EF) guncelle.

        Formul: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        Minimum EF = 1.3

        Args:
            current_ef: Mevcut EF degeri
            user_rating: Kullanici puani (1-5)

        Returns:
            Yeni EF degeri
        """
        self._validate_rating(user_rating)

        new_ef = current_ef + (
            0.1 - (5 - user_rating) * (0.08 + (5 - user_rating) * 0.02)
        )

        if new_ef < Config.SM2_MINIMUM_EF:
            new_ef = Config.SM2_MINIMUM_EF

        return round(new_ef, 4)

    def calculate_interval(
        self,
        repetition_number: int,
        easiness_factor: float,
        previous_interval: int,
    ) -> int:
        """
        Tekrar araligini (gun) hesapla.

        Args:
            repetition_number: Kacinci basarili tekrar (0-based)
            easiness_factor: Kolaylik faktoru
            previous_interval: Onceki aralik (gun)

        Returns:
            Yeni aralik (gun cinsinden)
        """
        if repetition_number == 0:
            return 1

        if repetition_number == 1:
            return 6

        return max(1, round(previous_interval * easiness_factor))

    def record_review(self, flashcard_id: int, user_rating: int) -> Dict:
        """
        Tekrar sonucunu ReviewLog'a kaydet.

        Args:
            flashcard_id: Flashcard ID
            user_rating: Kullanici puani (1-5)

        Returns:
            {'review_date': datetime, 'next_review_date': datetime,
             'easiness_factor': float, 'interval_days': int}
        """
        self._validate_rating(user_rating)
        self._get_flashcard(flashcard_id)

        state = self._reconstruct_state(flashcard_id)
        current_repetition = state["repetition_number"]
        current_ef = state["easiness_factor"]
        previous_interval = state["interval_days"]

        new_ef = self.calculate_easiness_factor(current_ef, user_rating)

        if user_rating >= 3:
            interval_days = self.calculate_interval(
                repetition_number=current_repetition,
                easiness_factor=new_ef,
                previous_interval=previous_interval,
            )
        else:
            interval_days = 1

        review_date = datetime.utcnow()
        next_review_date = review_date + timedelta(days=interval_days)

        review_log = ReviewLog(
            flashcard_id=flashcard_id,
            review_date=review_date,
            user_rating=user_rating,
            next_review_date=next_review_date,
        )

        self.db.add(review_log)
        self.db.commit()

        logger.info(
            "Review kaydedildi | flashcard_id=%s rating=%s interval=%s ef=%.4f next_review=%s",
            flashcard_id,
            user_rating,
            interval_days,
            new_ef,
            next_review_date,
        )

        return {
            "review_date": review_date,
            "next_review_date": next_review_date,
            "easiness_factor": new_ef,
            "interval_days": interval_days,
        }

    def get_due_flashcards(self, limit: int = None) -> List[Dict]:
        """
        Bugun tekrari gelmis flashcard'lari getir.

        Args:
            limit: Maksimum flashcard sayisi

        Returns:
            Tekrari gelmis flashcard listesi
        """
        if limit is None:
            limit = Config.SM2_DEFAULT_DUE_LIMIT

        now = datetime.utcnow()

        # Once consent'i olan event'lere ait kartlari al
        candidate_cards = (
            self.db.query(Flashcard)
            .join(Event, Flashcard.event_id == Event.event_id)
            .filter(Event.items.any(Item.has_consent.is_(True)))
            .order_by(Flashcard.flashcard_id.asc())
            .all()
        )

        due_cards: List[Dict] = []

        for card in candidate_cards:
            latest_review = (
                self.db.query(ReviewLog)
                .filter(ReviewLog.flashcard_id == card.flashcard_id)
                .order_by(ReviewLog.review_date.desc(), ReviewLog.log_id.desc())
                .first()
            )

            is_due = latest_review is None or latest_review.next_review_date <= now

            if is_due:
                due_cards.append(
                    {
                        "flashcard_id": card.flashcard_id,
                        "event_id": card.event_id,
                        "question": self._safe_decrypt(card.question),
                        "answer": self._safe_decrypt(card.answer),
                    }
                )

            if len(due_cards) >= limit:
                break

        logger.info("Due flashcard sayisi: %s", len(due_cards))
        return due_cards

    def get_flashcard_stats(self, flashcard_id: int) -> Dict:
        """
        Bir flashcard icin tekrar istatistiklerini getir.

        Args:
            flashcard_id: Flashcard ID

        Returns:
            {'total_reviews': int, 'average_rating': float,
             'current_interval': int, 'easiness_factor': float,
             'next_review_date': datetime}
        """
        self._get_flashcard(flashcard_id)

        logs = self._get_review_logs(flashcard_id)
        state = self._reconstruct_state(flashcard_id)

        total_reviews = len(logs)
        average_rating = (
            round(sum(log.user_rating for log in logs) / total_reviews, 2)
            if total_reviews > 0
            else 0.0
        )

        return {
            "flashcard_id": flashcard_id,
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            "current_interval": state["interval_days"],
            "easiness_factor": state["easiness_factor"],
            "next_review_date": state["next_review_date"],
        }

    def get_review_history(self, flashcard_id: int) -> List[Dict]:
        """
        Bir flashcard icin tum tekrar gecmisini getir.

        Args:
            flashcard_id: Flashcard ID

        Returns:
            ReviewLog kayitlarinin listesi
        """
        self._get_flashcard(flashcard_id)

        logs = self._get_review_logs(flashcard_id)

        return [
            {
                "log_id": log.log_id,
                "flashcard_id": log.flashcard_id,
                "review_date": log.review_date,
                "user_rating": log.user_rating,
                "next_review_date": log.next_review_date,
            }
            for log in logs
        ]

    def get_overall_stats(self) -> Dict:
        """
        Tum flashcard'lar icin genel istatistikleri getir.

        Returns:
            {'total_flashcards': int, 'due_today': int,
             'average_ef': float, 'total_reviews': int}
        """
        total_flashcards = self.db.query(Flashcard).count()
        total_reviews = self.db.query(ReviewLog).count()
        due_today = len(self.get_due_flashcards(limit=10**9))

        if total_flashcards == 0:
            return {
                "total_flashcards": 0,
                "due_today": 0,
                "average_ef": 0.0,
                "total_reviews": 0,
            }

        ef_values = []
        all_flashcards = self.db.query(Flashcard).all()

        for card in all_flashcards:
            state = self._reconstruct_state(card.flashcard_id)
            ef_values.append(state["easiness_factor"])

        average_ef = round(sum(ef_values) / len(ef_values), 4) if ef_values else 0.0

        return {
            "total_flashcards": total_flashcards,
            "due_today": due_today,
            "average_ef": average_ef,
            "total_reviews": total_reviews,
        }