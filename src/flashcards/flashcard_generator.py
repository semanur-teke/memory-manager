"""
Flashcard Uretici (Asama 10)

Event bilgilerinden soru-cevap ciftleri uretir.
Flashcard icerik alanlari (question, answer) DB'ye encrypt_string() ile
sifrelenerek yazilir, gosterimde decrypt_string() ile cozulur.
"""
from __future__ import annotations
from typing import List, Dict, Tuple,Optional,Any
import json
from datetime import datetime
from config import Config

try:
    # Proje ORM modelleri
    from database.schema import Event, Item, Flashcard
except Exception:  # pragma: no cover
    Event = Item = Flashcard = None  # type: ignore

_TR_MONTHS = {
    1: "Ocak",
    2: "Şubat",
    3: "Mart",
    4: "Nisan",
    5: "Mayıs",
    6: "Haziran",
    7: "Temmuz",
    8: "Ağustos",
    9: "Eylül",
    10: "Ekim",
    11: "Kasım",
    12: "Aralık",
}

def _format_date_tr(dt:datetime)->str:
    """15 Mart 2024 gibi."""
    if not isinstance(dt,datetime):
        return str(dt)
    return f"{dt.day} {_TR_MONTHS.get(dt.month,str(dt.month))} {dt.year}"
def _format_date_range_tr(start: datetime,end:datetime) -> str:
    if not isinstance(start,datetime) or not isinstance(end,datetime):
        return f"{start}-{end}"
    if start.date()==end.date():
        return _format_date_tr(start)
    # Aynı ay/yıl ise: 15-17 Mart 2024
    if start.year==end.year and start.month==end.month:
        return f"{start.day}-{end.day} {_TR_MONTHS.get(start.month,str(start.month))} {start.year}"
    # Farklı ise: 28 Şubat 2024 - 1 Mart 2024
    return f"{_format_date_tr(start)}-{_format_date_tr(end)}"
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

    def generate_for_event(self, event_id: int):
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
        if Flashcard is None or Event is None or Item is None:
            raise RuntimeError("ORM modelleri import edilemedi.(database.schema)")
        # 0) Zaten var mi? (idempotent)
        existing=(
            self.db.query(Flashcard)
            .filter(Flashcard.event_id==event_id)
            .order_by(Flashcard.flashcard_id.asc())
            .all()
        )
        if existing:
            return [self._flashcard_to_decrypted_dict(fc) for fc in existing]
        # 1) Event getir
        event=self.db.query(Event).filter(Event.event_id==event_id).first()
        if not event:
            return []
        # 2) Consent'li item'lari getir
        items=(
            self.db.query(Item)
            .filter(Item.event_id==event_id,Item.has_consent.is_(True))
            .order_by(Item.item_id.asc())
            .all()
        )
    
        cards: List[Tuple[str,str,Optional[List[int]]]]=[]

        location_card=self.create_location_card(event)
        if location_card is not None:
            q,a=location_card
            if a and a.strip():
                cards.append((q,a,None))
        
        date_card=self.create_date_card(event)
        if date_card is not None:
            q,a=date_card
            if a and a.strip():
                cards.append((q,a,None))
        content_card=self.create_content_card(event,items)
        if content_card is not None:
            q,a=content_card
            related_ids=[
                item.item_id
                for item in items if item.transcription
            ]
            if a and a.strip():
                cards.append((q,a,related_ids or None))

        count_card=self.create_count_card(event,items)
        if count_card is not None:
            q,a=count_card
            if a and a.strip():
                cards.append((q,a,None))
        created: List[Dict]=[]
        for question,answer,related_items_ids in cards:
            flashcard_id=self.save_flashcard(
                event_id,
                question,
                answer,
                related_item_ids=related_items_ids,
            )
            created.append(self.get_flashcard_decrypted(flashcard_id))
        return created


       
        

        
    def create_location_card(self, event):
        question="Bu olay nerede gerceklesti?"
        loc=(self._value(event,"main_location","")or "").strip()
        if not loc:
            return None
        return question,loc
    
    def create_date_card(self, event):
        start=self._value(event,"start_date")
        end=self._value(event,"end_date")

        if not start:
            return None
        if end and start.date() != end.date():
            answer=f"{start.strftime('%d %B %Y')}-{end.strftime('%d %B %Y')}"
        else:
            answer=start.strftime("%d %B %Y")
        return("Bu olay ne zaman oldu?",answer)


    def create_content_card(self, event, items):
        transcript_texts=[]

        for item in items or []:
            has_consent=self._value(item,"has_consent",False)
            transcription=self._value(item,"transcription")

            if not has_consent:
                continue
            if not transcription:
                continue
            try:
                text=self.encryption_manager.decrypt_string(transcription)
            except Exception:
                text=transcription
            text=(text or"").strip()
            if text:
                transcript_texts.append(text)
        if not transcript_texts:
            return None
        
        merged=" ".join(transcript_texts)
        limit=Config.FLASHCARD_TRANSCRIPT_PREVIEW
        preview=merged[:limit].strip()
        if len(merged) > limit:
            preview+="..."

        return("Bu olayın icerigi nedir?",preview)

        
    def create_count_card(self, event, items):
        question="Bu olayda kac iliskili dosya var?"
        counts={"photo":0,"audio":0,"note":0,"other":0}
        for it in items or []:
            if not it.has_consent:
                continue
            t=(it.type or"").strip().lower()
            if t in {"photo","image","jpg","png"}:
                counts["photo"]+=1
            elif t in {"audio","sound","voice"}:
                counts["audio"]+=1
            elif t in {"note","text"}:
                counts["note"] +=1
            else:
                counts["other"]+=1
        parts=[]
        if counts["photo"]:
            parts.append(f"{counts['photo']} fotograf")
        if counts["audio"]:
            parts.append(f"{counts['audio']} ses kaydi")
        if counts["note"]:
            parts.append(f"{counts['note']} not")
        if counts["other"]:
            parts.append(f"{counts['other']} diger")

        if not parts:
            return question,"0 dosya"
        return question, ", ".join(parts)
    
    def save_flashcard(self, event_id: int, question: str, answer: str,related_item_ids: Optional[List[int]]=None) -> int:
        """
        Flashcard'i sifreleyerek DB'ye kaydet.
        """
        if Flashcard is None:
            raise RuntimeError("Flashcard modeli import edilemedi.")
        q=question or ""
        a=answer or ""

        if self.encryption_manager is not None:
            q=self.encryption_manager.encrypt_string(q)
            a=self.encryption_manager.encrypt_string(a)
        
        fc= Flashcard(event_id=event_id,question=q,answer=a)
        # Schema'da optional alan var: related_items_ids
        if related_item_ids is not None:
            try:
                fc.related_item_ids=json.dumps(related_item_ids,ensure_ascii=False)
            except Exception:
                fc.related_item_ids=None
        self.db.add(fc)
        self.db.commit()
        self.db.refresh(fc)
        return int(fc.flashcard_id)



    def get_flashcard_decrypted(self, flashcard_id: int) -> Dict:
        """
        Flashcard'i DB'den getir ve decrypt et.
        """
        if Flashcard is None:
            raise RuntimeError("Flashcard modeli import edilemedi.")
        fc=self.db.query(Flashcard).filter(Flashcard.flashcard_id==flashcard_id).first()
        if not fc:
            return {}
        return self._flashcard_to_decrypted_dict(fc)

    def generate_for_all_events(self) -> int:
        """
        Tum event'ler icin flashcard uret (henuz flashcard'i olmayanlari).

        Returns:
            Uretilen toplam flashcard sayisi
        """
        if Event is None or Flashcard is None:
            raise RuntimeError("ORM modelleri import edilemedi.")
        existing_event_ids=self.db.query(Flashcard.event_id).distinct()

        events=(
            self.db.query(Event)
            .filter(~Event.event_id.in_(existing_event_ids))
            .all()
        )
        total_created=0
        for ev in events:
            created=self.generate_for_event(int(ev.event_id))
            total_created += len(created)
        return total_created
    #-----------Helpers---------------
    def _value(self,obj,key,default=None):
        if obj is None:
            return default
        if isinstance(obj,dict):
            return obj.get(key,default)
        return getattr(obj,key,default)
    
    def _flashcard_to_decrypted_dict(self,fc) -> Dict[str,Any]:
        q= fc.question
        a=fc.answer
        if self.encryption_manager is not None:
            try:
                q=self.encryption_manager.decrypt_string(q)
            except Exception:
                pass
            try:
                a=self.encryption_manager.decrypt_string(a)
            except Exception:
                pass
        out={
            "flashcard_id":int(fc.flashcard_id),
            "event_id":int(fc.event_id),
            "question":q,
            "answer":a,
        }
        rid=getattr(fc,"related_item_ids",None)
        if rid:
            try:
                out["related_item_ids"]=json.loads(rid)
            except Exception:
                out["related_item_ids"]=rid
        return out

