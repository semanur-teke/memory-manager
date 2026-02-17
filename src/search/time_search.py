"""
Zamana Göre Arama (Aşama 5.2)
Tarih aralığına göre öğeleri filtreler.
"""

from datetime import datetime, date
from typing import List, Dict, Optional
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from database.schema import Item  # Veritabanı modelin

class TimeSearch:
    """
    Zaman bazlı arama yapar.
    """
    
    def __init__(self, db_connection: Session):
        """
        Args:
            db_connection: SQLAlchemy veritabanı oturumu
        """
        self.db = db_connection
    
    def search_by_date_range(self, start_date: date, end_date: date) -> List[Dict]:
        """
        Belirli bir tarih aralığındaki öğeleri bulur.
        """
        # created_at sütunu üzerinden BETWEEN sorgusu atıyoruz
        items = self.db.query(Item).filter(
            Item.creation_datetime >= start_date,
            Item.creation_datetime <= end_date,
            Item.has_consent == True
        ).order_by(Item.creation_datetime.desc()).all()

        return [{'item_id': item.item_id, 'created_at': item.creation_datetime, 'file_path': item.file_path} for item in items]
    
    def search_by_year(self, year: int) -> List[Dict]:
        """
        Belirli bir yıldaki öğeleri bulur (Örn: 2025).
        """
        items = self.db.query(Item).filter(
            extract('year', Item.creation_datetime) == year,
            Item.has_consent == True
        ).order_by(Item.creation_datetime.asc()).all()

        return [{'item_id': item.item_id, 'created_at': item.creation_datetime, 'file_path': item.file_path} for item in items]
    
    def search_by_month(self, year: int, month: int) -> List[Dict]:
        """
        Belirli bir ay ve yıldaki öğeleri bulur (Örn: Haziran 2025).
        """
        items = self.db.query(Item).filter(
            extract('year', Item.creation_datetime) == year,
            extract('month', Item.creation_datetime) == month,
            Item.has_consent == True
        ).order_by(Item.creation_datetime.asc()).all()

        return [{'item_id': item.item_id, 'created_at': item.creation_datetime, 'file_path': item.file_path} for item in items]
    
    def search_by_day(self, target_date: date) -> List[Dict]:
        """
        Tam olarak belirli bir gündeki (Yıl-Ay-Gün) öğeleri bulur.
        """
        # func.date kullanarak timestamp verisini sadece tarih kısmıyla kıyaslıyoruz
        items = self.db.query(Item).filter(
            func.date(Item.creation_datetime) == target_date,
            Item.has_consent == True
        ).all()

        return [{'item_id': item.item_id, 'created_at': item.creation_datetime, 'file_path': item.file_path} for item in items]
    
    def get_timeline_stats(self) -> Dict:
        """
        Zaman çizelgesi istatistiklerini döndürür.
        """
        # Toplam öğe sayısı
        total_items = self.db.query(Item).filter(Item.has_consent == True).count()
        if total_items == 0:
            return {}

        # En eski ve en yeni tarihler
        earliest = self.db.query(func.min(Item.creation_datetime)).filter(Item.has_consent == True).scalar()
        latest = self.db.query(func.max(Item.creation_datetime)).filter(Item.has_consent == True).scalar()

        # Yıllara göre dağılım
        yearly_counts = self.db.query(
            extract('year', Item.creation_datetime).label('year'),
            func.count(Item.item_id)
        ).filter(Item.has_consent == True).group_by('year').all()

        # Aylara göre dağılım
        monthly_counts = self.db.query(
            extract('year', Item.creation_datetime).label('year'),
            extract('month', Item.creation_datetime).label('month'),
            func.count(Item.item_id)
        ).filter(Item.has_consent == True).group_by('year', 'month').all()

        return {
            'earliest_date': earliest,
            'latest_date': latest,
            'total_items': total_items,
            'items_by_year': {int(y): c for y, c in yearly_counts},
            'items_by_month': {(int(y), int(m)): c for y, m, c in monthly_counts}
        }