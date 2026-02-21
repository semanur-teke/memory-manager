"""
Flashcard Uretici (Asama 10)

Event bilgilerinden soru-cevap ciftleri uretir.
Flashcard icerik alanlari (question, answer) DB'ye encrypt_string() ile
sifrelenerek yazilir, gosterimde decrypt_string() ile cozulur.
"""

from typing import List, Dict, Tuple


class FlashcardGenerator:
    """
    Event bazli flashcard (soru-cevap cifti) uretici.

    Ornek kartlar:
    - "Bu olay nerede gerceklesti?" -> "Istanbul, Kadikoy"
    - "Bu olayda kimler vardi?" -> transkript ozeti
    - "Bu olay ne zaman oldu?" -> "15 Mart 2024"
    """

    def __init__(self, db_connection, encryption_manager=None):
        """
        Args:
            db_connection: Veritabani baglantisi
            encryption_manager: Sifreleme yoneticisi (encrypt_string/decrypt_string icin)
        """
        self.db = db_connection
        self.encryption_manager = encryption_manager

    def generate_for_event(self, event_id: int) -> List[Dict]:
        """
        Bir event icin flashcard'lar uret ve DB'ye kaydet.

        Adimlar:
        1. Event ve item bilgilerini getir (has_consent == True)
        2. Soru-cevap ciftleri olustur
        3. question ve answer alanlarini encrypt_string() ile sifrele
        4. Flashcard tablosuna kaydet

        Args:
            event_id: Flashcard uretilecek event'in ID'si

        Returns:
            Uretilen flashcard'larin listesi
        """
        pass

    def create_location_card(self, event: Dict) -> Tuple[str, str]:
        """
        Konum bazli flashcard olustur.

        Ornek: ("Bu olay nerede gerceklesti?", "Istanbul, Kadikoy")

        Args:
            event: Event bilgileri

        Returns:
            (question, answer) tuple'i
        """
        pass

    def create_date_card(self, event: Dict) -> Tuple[str, str]:
        """
        Tarih bazli flashcard olustur.

        Ornek: ("Bu olay ne zaman oldu?", "15-17 Mart 2024")

        Args:
            event: Event bilgileri

        Returns:
            (question, answer) tuple'i
        """
        pass

    def create_content_card(self, event: Dict, items: List[Dict]) -> Tuple[str, str]:
        """
        Icerik bazli flashcard olustur (transkript ozetinden).

        Ornek: ("Bu olayda neler konusuldu?", transkript ozeti)

        Args:
            event: Event bilgileri
            items: Event'e ait item'lar (transkriptler decrypt edilmis)

        Returns:
            (question, answer) tuple'i
        """
        pass

    def create_count_card(self, event: Dict, items: List[Dict]) -> Tuple[str, str]:
        """
        Sayisal bilgi flashcard'i olustur.

        Ornek: ("Bu olayda kac fotograf var?", "12 fotograf ve 3 ses kaydi")

        Args:
            event: Event bilgileri
            items: Event'e ait item'lar

        Returns:
            (question, answer) tuple'i
        """
        pass

    def save_flashcard(self, event_id: int, question: str, answer: str) -> int:
        """
        Flashcard'i sifreleyerek DB'ye kaydet.

        Args:
            event_id: Iliskili event ID
            question: Soru metni (sifresiz)
            answer: Cevap metni (sifresiz)

        Returns:
            Olusturulan flashcard_id
        """
        pass

    def get_flashcard_decrypted(self, flashcard_id: int) -> Dict:
        """
        Flashcard'i DB'den getir ve decrypt et.

        Args:
            flashcard_id: Flashcard ID

        Returns:
            {'flashcard_id': int, 'question': str, 'answer': str, 'event_id': int}
        """
        pass

    def generate_for_all_events(self) -> int:
        """
        Tum event'ler icin flashcard uret (henuz flashcard'i olmayanlari).

        Returns:
            Uretilen toplam flashcard sayisi
        """
        pass
