# database/schema.py

import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import create_engine, event, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column, Session, sessionmaker
from config import Config

logger = logging.getLogger(__name__)

# 1. Temel Sınıfı Oluşturma
Base = declarative_base()

# ----------------- Flashcards Tablosu -----------------
class Flashcard(Base):
    __tablename__ = 'flashcards'
    
    flashcard_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    
    # İlişki - Event (Foreign Key)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.event_id'))
    event: Mapped['Event'] = relationship(back_populates='flashcards')
    
    # İlişki - ReviewLog
    reviews: Mapped[List['ReviewLog']] = relationship(back_populates='flashcard', cascade='all, delete-orphan')

    # Bu kartın oluşturulmasında kullanılan Items ID'leri (JSON string)
    related_item_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True) 

    def __repr__(self) -> str:
        return f"<Flashcard(id={self.flashcard_id}, event_id={self.event_id})>"


# ----------------- ReviewLog Tablosu -----------------
class ReviewLog(Base):
    __tablename__ = 'review_logs'
    
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # İlişki - Flashcard (Foreign Key)
    flashcard_id: Mapped[int] = mapped_column(ForeignKey('flashcards.flashcard_id'))
    flashcard: Mapped['Flashcard'] = relationship(back_populates='reviews')
    
    # Tekrar Verileri
    review_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_rating: Mapped[int] = mapped_column(Integer) # 1-5 arası zorluk
    next_review_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    
    def __repr__(self) -> str:
        return f"<ReviewLog(id={self.log_id}, rating={self.user_rating})>"


# ----------------- Events Tablosu -----------------
class Event(Base):
    __tablename__ = 'events'
    
    event_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Olay Bilgileri
    title: Mapped[str] = mapped_column(String)
    start_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    main_location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # İlişki - Items
    # NOT: cascade='all, delete-orphan' KULLANILAMAZ — Event silinince
    # fotograflar da silinirdi. Fotograflar event'ten bagimsiz vardir.
    # Event silindiginde Item.event_id otomatik NULL olur (ondelete='SET NULL').
    items: Mapped[List['Item']] = relationship(back_populates='event')
    
    # İlişki - Flashcards
    flashcards: Mapped[List['Flashcard']] = relationship(back_populates='event', cascade='all, delete-orphan')

    # Kapak Fotoğrafı İlişkisi
    cover_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey('items.item_id', ondelete='SET NULL'), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Event(id={self.event_id}, title='{self.title}')>"


# ----------------- Items Tablosu (Ana Veri Girişi) -----------------
class Item(Base):
    __tablename__ = 'items'
    
    # Anahtar ve Dosya Bilgileri
    item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_path: Mapped[str] = mapped_column(String, unique=True, index=True)
    file_hash: Mapped[str] = mapped_column(String, unique=True)
    type: Mapped[str] = mapped_column(String(50)) # Photo, Audio, Note
    
    # Gizlilik ve İşleme Flagleri (Kritik)
    has_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_rotated: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Metadata
    creation_datetime: Mapped[datetime] = mapped_column(DateTime, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # AI İşleme Sonuçları
    transcription: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    faiss_index_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True) 
    
    # İlişki - Event (Foreign Key)
    event_id: Mapped[Optional[int]] = mapped_column(ForeignKey('events.event_id', ondelete='SET NULL'), nullable=True)
    event: Mapped['Event'] = relationship(back_populates='items')

    def __repr__(self) -> str:
        return f"<Item(id={self.item_id}, type='{self.type}', consent={self.has_consent})>"


# ----------------- DB Yönetimi -----------------
class DatabaseSchema:
    def __init__(self, db_url: str = Config.DATABASE_URL):
        self.engine = create_engine(db_url)
        # SQLite foreign key desteğini aktif et (varsaylanda kapali)
        # Bu olmadan ondelete='SET NULL' calismaz
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_all_tables(self):
        Base.metadata.create_all(self.engine)
        logger.info("Veritabanı şeması başarıyla güncellendi.")

if __name__ == '__main__':
    from config import setup_logging
    setup_logging()
    schema_manager = DatabaseSchema()
    schema_manager.create_all_tables()