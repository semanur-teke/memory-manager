"""
SM-2 Aralikli Tekrar Zamanlayicisi (Asama 10)

SuperMemo SM-2 algoritmasini kullanarak flashcard tekrar
zamanlamasini hesaplar. ReviewLog tablosunu kullanir.
Kullanici puanina (1-5) gore next_review_date gunceller.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta


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
                         1: Tamamen unutulmus
                         2: Yanlis hatirlanmis
                         3: Zor hatirlanmis
                         4: Kolay hatirlanmis
                         5: Mukemmel hatirlanmis

        Returns:
            Bir sonraki tekrar tarihi
        """
        pass

    def calculate_easiness_factor(self, current_ef: float, user_rating: int) -> float:
        """
        Kolaylik faktorunu (EF) guncelle.

        Formul: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        Minimum EF = 1.3

        Args:
            current_ef: Mevcut EF degeri (varsayilan baslangic: 2.5)
            user_rating: Kullanici puani (1-5)

        Returns:
            Yeni EF degeri
        """
        pass

    def calculate_interval(self, repetition_number: int, easiness_factor: float,
                          previous_interval: int) -> int:
        """
        Tekrar araligini (gun) hesapla.

        Args:
            repetition_number: Kacinci basarili tekrar (0-based)
            easiness_factor: Kolaylik faktoru
            previous_interval: Onceki aralik (gun)

        Returns:
            Yeni aralik (gun cinsinden)
        """
        pass

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
        pass

    def get_due_flashcards(self, limit: int = 20) -> List[Dict]:
        """
        Bugun tekrari gelmis flashcard'lari getir.

        Args:
            limit: Maksimum flashcard sayisi

        Returns:
            Tekrari gelmis flashcard listesi (next_review_date <= bugun)
        """
        pass

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
        pass

    def get_review_history(self, flashcard_id: int) -> List[Dict]:
        """
        Bir flashcard icin tum tekrar gecmisini getir.

        Args:
            flashcard_id: Flashcard ID

        Returns:
            ReviewLog kayitlarinin listesi (tarih sirasina gore)
        """
        pass

    def get_overall_stats(self) -> Dict:
        """
        Tum flashcard'lar icin genel istatistikleri getir.

        Returns:
            {'total_flashcards': int, 'due_today': int,
             'average_ef': float, 'total_reviews': int}
        """
        pass
