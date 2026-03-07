"""
Zaman Cizelgesi Sayfasi (Asama 11)

TimeSearch.get_timeline_stats() verisini gorsel bir timeline'a donusturur.
Her event'in ozeti, kapak fotografi ve tarih araligi gosterilir.
Gosterim oncesi decrypt_string() ile ozet cozulur,
decrypt_file() ile kapak fotografi gecici olarak cozulur.
"""
import logging
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime,timedelta

from database.schema import Event,Item,Flashcard
from security.encryption_manager import EncryptionManager
from src.search.time_search import TimeSearch
from config import Config

logger=logging.getLogger(__name__)


class TimelinePage:
    """
    Kronolojik olay goruntuleme sinifi.

    TimeSearch.get_timeline_stats() verisini alir ve
    gorsel timeline verisi olarak duzenler.
    """

    def __init__(self, db_connection, search_engine=None, encryption_manager=None):
        """
        Args:
            db_connection: Veritabani baglantisi
            search_engine: SearchEngine instance (TimeSearch icin)
            encryption_manager: Sifreleme yoneticisi (decrypt icin)
        """
        self.db = db_connection
        self.search_engine = search_engine
        self.encryption_manager = encryption_manager or EncryptionManager()
        self._temp_files: List[str]=[]

        temp_dir=Path(Config.TIMELINE_TEMP_DIR)
        temp_dir.mkdir(parents=True,exist_ok=True)
        self._temp_dir=temp_dir
    def _safe_decrypt_string(self,encrypted_text: Optional[str]) -> Optional[str]:
        """ metni guvenli sekilde decrypt et; olmazsa ham veriyi dondur."""
        if not encrypted_text:
            return encrypted_text
        
        try:
            return self.encryption_manager.decrypt_string(encrypted_text)
        except Exception as exc:
            logger.warning("Metin decrypt edilemedi, ham veri donduruluyor: %s",exc)
            return encrypted_text
        
    def _get_time_search(self) -> TimeSearch:
        """
        timeSearch instance getir.
        search_engine icinden varsa onu kullan,yoksa dogrudan olustur.
        """
        if self.search_engine is not None:
            time_search=getattr(self.search_engine,"time_search",None)
            if time_search is not None:
                return time_search
            
        return TimeSearch(self.db)
    
    def get_timeline_data(self, start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Timeline icin event verilerini hazirla.
        """
        query=self.db.query(Event).order_by(Event.start_date.asc(),Event.event_id.asc())
        if start_date is not None:
            query=query.filter(Event.end_date >= start_date)

        if end_date is not None:
            query=query.filter(Event.start_date <= end_date)

        events=query.all()
        timeline_data:List[Dict]=[]

        for event in events:
            consented_items=[item for item in event.items if item.has_consent]
            summary=self._safe_decrypt_string(event.summary)
            cover_photo_path=self.decrypt_cover_photo(event.event_id)

            timeline_data.append(
                {
                    "event_id":event.event_id,
                    "title": event.title,
                    "summary":summary,
                    "start_date":event.start_date,
                    "end_date":event.end_date,
                    "cover_photo_path":cover_photo_path,
                    "item_count": len(consented_items),
                    "location": event.main_location,
                }
            )
        logger.info("Timeline verisi hazirlandi: %s event",len(timeline_data))
        return timeline_data
    
    def get_event_detail(self, event_id: int) -> Dict:
        """
        Bir event'in detayli bilgilerini getir (timeline tiklandiginda).
        """
        event=self.db.query(Event).filter(Event.event_id==event_id).first()
        if event is None:
            raise ValueError(f"Event bulunamadi:{event_id}")
        
        consented_items=[item for item in event.items if item.has_consent]
        flashcard_count=(
            self.db.query(Flashcard)
            .filter(Flashcard.event_id==event_id)
            .count()
        )
        item_list=[]
        for item in consented_items:
            item_list.append(
                {
                    "item_id":item.item_id,
                    "file_path":item.file_path,
                    "type":item.type,
                    "creation_datetime":item.creation_datetime,
                    "latitude": item.latitude,
                    "longitude":item.longitude,
                    "transcription": self._safe_decrypt_string(item.transcription),
                }
            )
        return{
            "event_id":event.event_id,
            "title": event.title,
            "summary":self._safe_decrypt_string(event.summary),
            "start_date":event.start_date,
            "end_date":event.end_date,
            "location":event.main_location,
            "cover_photo_path":self.decrypt_cover_photo(event_id),
            "item_count":len(consented_items),
            "flashcard_count":flashcard_count,
            "items":item_list,
        }

    def decrypt_cover_photo(self, event_id: int) -> Optional[str]:
        """
        Event'in kapak fotografini gecici olarak decrypt et.
        """
        event=self.db.query(Event).filter(Event.event_id==event_id).first()
        if event is None:
            raise ValueError(f"Event bulunamadi: {event_id}")
        
        if event.cover_item_id is None:
            return None
        
        cover_item=(
            self.db.query(Item)
            .filter(
                Item.item_id==event.cover_item_id,
                Item.has_consent.is_(True),
            )
            .first()
        )
        if cover_item is None:
            logger.warning("izinli kapak fotografi bulunamadi | event_id=%s",event_id)
            return None
        try:
            decrypted_bytes=self.encryption_manager.decrypt_file(cover_item.file_path)
        except Exception as exc:
            logger.error("Kapak fotografi decrypt edilemedi | event_id=%s error=%s",event_id,exc)
            return None
        suffix=Path(cover_item.file_path).suffix or ".bin"
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            dir=self._temp_dir,
        )as temp_file:
            temp_file.write(decrypted_bytes)
            temp_path=temp_file.name
        self._temp_files.append(temp_path)
        logger.info("Kapak fotografi gecici olarak decrypt edildi: %s",temp_path)
        return temp_path

    def group_events_by_period(self, events: List[Dict],
                                period: str = "month") -> Dict[str, List[Dict]]:
        """
        Event'leri zaman dilimine gore grupla.
        """
        grouped: Dict[str,List[Dict]]=defaultdict(list)

        for event in events:
            event_date=event["start_date"]

            if period=="day":
                key=event_date.strftime("%d %B %Y")
            elif period=="week":
                week_start=event_date - timedelta(days=event_date.weekday())
                key=f"Hafta of {week_start.strftime('%d %B %Y')}"
            elif period == "month":
                key=event_date.strftime("%B %Y")
            elif period=="year":
                key=event_date.strftime("%Y")
            else:
                raise ValueError("periyot sadece 'gün','hafta','ay', veya 'yıl' olabilir. ")

            grouped[key].append(event)
        
        return dict(grouped)
    
    def get_timeline_stats(self) -> Dict:
        """
        Timeline genel istatistikleri.
        """
        time_search=self._get_time_search()
        base_stats=time_search.get_timeline_stats()

        total_events=self.db.query(Event).count()

        consented_items=(
            self.db.query(Item)
            .filter(Item.has_consent.is_(True))
            .count()
        )

        distinct_locations={location for(location,)in self.db.query(Event.main_location).all() if location}
        date_range=(base_stats.get("earliest_date"),base_stats.get("latest_date"),)
        return{
            "total_events":total_events,
            "date_range":date_range,
            "total_items":consented_items,
            "locations_count":len(distinct_locations),
            "items_by_year":base_stats.get("items_by_year",{}),
            "items_by_month":base_stats.get("items_by_month",{}),
        }

    def cleanup_temp_files(self) -> None:
        """
        Gecici olarak decrypt edilen kapak fotograflarini temizle.
        """
        removed_count=0
        for temp_path in self._temp_files:
            try:
                path=Path(temp_path)
                if path.exists():
                    path.unlink()
                    removed_count +=1
            except Exception as exc:
                logger.warning("Gecici dosya silinemedi: %s | %s",temp_path,exc)
        self._temp_files.clear()
        logger.info("Gecici dosyalar temizlendi: %s",removed_count)
