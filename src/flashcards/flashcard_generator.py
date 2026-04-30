"""
Flashcard Uretici (Asama 10)

Event bilgilerinden soru-cevap ciftleri uretir.
Flashcard icerik alanlari (question, answer) DB'ye encrypt_string() ile
sifrelenerek yazilir, gosterimde decrypt_string() ile cozulur.
"""

import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from config import Config
from database.schema import Event, Item, Flashcard  # schema.py'ya dokunmadan sadece import
# Not: DatabaseSchema import etmen gerekmiyor; session zaten db_connection olarak geliyor.

logger = logging.getLogger(__name__)

_TR_MONTHS = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}


def _format_tr_date(dt: datetime) -> str:
    # Locale bağımlılığına girmeden TR ay adı basıyoruz
    return f"{dt.day:02d} {_TR_MONTHS.get(dt.month, dt.strftime('%B'))} {dt.year}"


def _format_tr_date_range(start: datetime, end: Optional[datetime]) -> str:
    if end is None:
        return _format_tr_date(start)
    if start.date() == end.date():
        return _format_tr_date(start)

    # Aynı ay-yıl ise: 15-17 Mart 2024
    if start.year == end.year and start.month == end.month:
        return f"{start.day:02d}-{end.day:02d} {_TR_MONTHS.get(start.month)} {start.year}"

    # Farklı ay/yıl ise: 28 Şubat 2024 - 02 Mart 2024
    return f"{_format_tr_date(start)} - {_format_tr_date(end)}"


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
            db_connection: Veritabani baglantisi (SQLAlchemy session)
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
        event_obj = self.db.query(Event).filter(Event.event_id == event_id).first()
        if not event_obj:
            logger.warning("Event bulunamadi: event_id=%s", event_id)
            return []

        # Event'i dict'e çevir (iskelet Dict bekliyor)
        event: Dict = {
            "event_id": int(event_obj.event_id),
            "main_location": getattr(event_obj, "main_location", None),
            "start_date": getattr(event_obj, "start_date", None),
            "end_date": getattr(event_obj, "end_date", None),
        }

        # Item'lari çek (GUVENLIK: has_consent == True)
        items_obj = (
            self.db.query(Item)
            .filter(Item.event_id == event_id)
            .filter(Item.has_consent == True)  # noqa: E712
            .all()
        )

        items: List[Dict] = []
        for it in items_obj:
            d = {
                "item_id": int(getattr(it, "item_id")),
                "event_id": int(getattr(it, "event_id")),
                "type": getattr(it, "type", None),
                "has_consent": getattr(it, "has_consent", None),
                "transcription": getattr(it, "transcription", None),
            }
            # Transkript decrypt (varsa)
            if d.get("transcription"):
                try:
                    d["transcription_decrypted"] = self.encryption_manager.decrypt_string(d["transcription"])
                except Exception:
                    logger.exception("Transkript decrypt edilemedi: item_id=%s", d.get("item_id"))
                    d["transcription_decrypted"] = None
            else:
                d["transcription_decrypted"] = None

            items.append(d)

        created: List[Dict] = []

        # 1) Location card (opsiyonel)
        loc_card = self.create_location_card(event)
        if loc_card:
            q, a = loc_card
            fid = self.save_flashcard(event_id, q, a)
            created.append({"flashcard_id": fid, "event_id": event_id, "type": "location"})

        # 2) Date card (opsiyonel)
        date_card = self.create_date_card(event)
        if date_card:
            q, a = date_card
            fid = self.save_flashcard(event_id, q, a)
            created.append({"flashcard_id": fid, "event_id": event_id, "type": "date"})

        # 3) Content card (opsiyonel)
        content_card = self.create_content_card(event, items)
        if content_card:
            q, a = content_card
            fid = self.save_flashcard(event_id, q, a)
            created.append({"flashcard_id": fid, "event_id": event_id, "type": "content"})

        # 4) Count card (her zaman)
        q, a = self.create_count_card(event, items)
        fid = self.save_flashcard(event_id, q, a)
        created.append({"flashcard_id": fid, "event_id": event_id, "type": "count"})

        return created

    def create_location_card(self, event: Dict) -> Optional[Tuple[str, str]]:
        """
        Konum bazli flashcard olustur.

        Ornek: ("Bu olay nerede gerceklesti?", "Istanbul, Kadikoy")
        """
        loc = (event.get("main_location") or "").strip()
        if not loc:
            return None
        return ("Bu olay nerede gerçekleşti?", loc)

    def create_date_card(self, event: Dict) -> Optional[Tuple[str, str]]:
        """
        Tarih bazli flashcard olustur.

        Ornek: ("Bu olay ne zaman oldu?", "15-17 Mart 2024")
        """
        start = event.get("start_date")
        if not start:
            return None
        end = event.get("end_date")
        return ("Bu olay ne zaman oldu?", _format_tr_date_range(start, end))

    def create_content_card(self, event: Dict, items: List[Dict]) -> Optional[Tuple[str, str]]:
        """
        Icerik bazli flashcard olustur (transkript ozetinden).
        - Sadece transkripti olan item'lar
        - Birlestir, ilk N karakteri al (Config)
        - Max cevap uzunlugunu uygula (Config)
        """
        texts: List[str] = []
        for it in items:
            t = (it.get("transcription_decrypted") or "").strip()
            if t:
                texts.append(t)

        if not texts:
            return None

        merged = "\n".join(texts)

        preview_len = int(getattr(Config, "FLASHCARD_TRANSCRIPT_PREVIEW", 200))
        max_len = int(getattr(Config, "FLASHCARD_MAX_ANSWER_LENGTH", 200))

        answer = merged[:preview_len].strip()
        answer = answer[:max_len].strip()

        if not answer:
            return None

        return ("Bu olayda neler konuşuldu?", answer)

    def create_count_card(self, event: Dict, items: List[Dict]) -> Tuple[str, str]:
        """
        Sayisal bilgi flashcard'i olustur.

        Ornek: ("Bu olayda kac fotograf var?", "12 fotograf ve 3 ses kaydi")
        """
        foto = len([i for i in items if i.get("type") == "Photo"])
        ses = len([i for i in items if i.get("type") == "Audio"])
        return ("Bu olayda kaç anı var?", f"{foto} fotoğraf ve {ses} ses kaydı")

    def save_flashcard(self, event_id: int, question: str, answer: str) -> int:
        """
        Flashcard'i sifreleyerek DB'ye kaydet.
        """
        if self.encryption_manager is None:
            raise ValueError("encryption_manager is required for save_flashcard()")

        enc_q = self.encryption_manager.encrypt_string(question)
        enc_a = self.encryption_manager.encrypt_string(answer)

        card = Flashcard(
            event_id=event_id,
            question=enc_q,
            answer=enc_a,
            # related_item_ids bu iskelette yok; schema'da varsa istersen burada set edebilirsin
        )
        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return int(card.flashcard_id)

    def get_flashcard_decrypted(self, flashcard_id: int) -> Dict:
        """
        Flashcard'i DB'den getir ve decrypt et.
        """
        if self.encryption_manager is None:
            raise ValueError("encryption_manager is required for get_flashcard_decrypted()")

        card = self.db.query(Flashcard).filter(Flashcard.flashcard_id == flashcard_id).first()
        if not card:
            raise ValueError(f"Flashcard bulunamadi: {flashcard_id}")

        return {
            "flashcard_id": int(card.flashcard_id),
            "event_id": int(card.event_id),
            "question": self.encryption_manager.decrypt_string(card.question),
            "answer": self.encryption_manager.decrypt_string(card.answer),
        }

    def generate_for_all_events(self) -> int:
        """
        Tum event'ler icin flashcard uret (henuz flashcard'i olmayanlari).
        """
        # Flashcard üretilmiş event_id seti
        existing_event_ids = set(
            r[0] for r in self.db.query(Flashcard.event_id).distinct().all()
        )

        events = self.db.query(Event).all()
        total = 0
        for e in events:
            eid = int(e.event_id)
            if eid in existing_event_ids:
                continue
            created = self.generate_for_event(eid)
            total += len(created)
        return total