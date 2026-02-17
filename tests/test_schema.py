# tests/test_schema.py
"""
Veritabanı şema testleri.
Tabloların doğru oluşturulduğunu ve ORM ilişkilerinin çalıştığını doğrular.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from database.schema import Base, DatabaseSchema, Item, Event, Flashcard, ReviewLog


class TestDatabaseCreation:
    """Veritabanı oluşturma testleri."""

    def test_create_all_tables(self):
        """create_all_tables() 4 tabloyu da oluşturur."""
        schema = DatabaseSchema(db_url="sqlite:///:memory:")
        schema.create_all_tables()

        inspector = inspect(schema.engine)
        tables = inspector.get_table_names()

        assert "items" in tables
        assert "events" in tables
        assert "flashcards" in tables
        assert "review_logs" in tables

    def test_items_table_columns(self):
        """items tablosu gerekli sütunlara sahip."""
        schema = DatabaseSchema(db_url="sqlite:///:memory:")
        schema.create_all_tables()

        inspector = inspect(schema.engine)
        columns = {col['name'] for col in inspector.get_columns('items')}

        expected = {
            'item_id', 'file_path', 'file_hash', 'type',
            'has_consent', 'is_rotated', 'creation_datetime',
            'latitude', 'longitude', 'transcription',
            'faiss_index_id', 'event_id'
        }
        assert expected.issubset(columns)


class TestItemModel:
    """Item ORM model testleri."""

    def test_create_item(self, db_session):
        """Item oluşturma ve kaydetme."""
        item = Item(
            file_path="/test/photo.jpg",
            file_hash="abc123",
            type="Photo",
            has_consent=True,
            is_rotated=False,
            creation_datetime=datetime(2025, 6, 15, 10, 30)
        )
        db_session.add(item)
        db_session.commit()

        assert item.item_id is not None
        assert item.item_id > 0

    def test_item_default_consent_false(self, db_session):
        """has_consent varsayılan olarak False."""
        item = Item(
            file_path="/test/default.jpg",
            file_hash="def456",
            type="Photo",
            is_rotated=False,
            creation_datetime=datetime.now()
        )
        db_session.add(item)
        db_session.commit()

        fetched = db_session.query(Item).filter(Item.file_hash == "def456").first()
        assert fetched.has_consent is False

    def test_item_unique_file_path(self, db_session):
        """file_path unique constraint çalışıyor."""
        item1 = Item(
            file_path="/test/unique.jpg",
            file_hash="hash1",
            type="Photo",
            is_rotated=False,
            creation_datetime=datetime.now()
        )
        item2 = Item(
            file_path="/test/unique.jpg",
            file_hash="hash2",
            type="Photo",
            is_rotated=False,
            creation_datetime=datetime.now()
        )
        db_session.add(item1)
        db_session.commit()

        db_session.add(item2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_item_unique_file_hash(self, db_session):
        """file_hash unique constraint çalışıyor."""
        item1 = Item(
            file_path="/test/a.jpg",
            file_hash="same_hash",
            type="Photo",
            is_rotated=False,
            creation_datetime=datetime.now()
        )
        item2 = Item(
            file_path="/test/b.jpg",
            file_hash="same_hash",
            type="Photo",
            is_rotated=False,
            creation_datetime=datetime.now()
        )
        db_session.add(item1)
        db_session.commit()

        db_session.add(item2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_item_nullable_fields(self, db_session):
        """latitude, longitude, transcription gibi alanlar nullable."""
        item = Item(
            file_path="/test/no_gps.jpg",
            file_hash="no_gps_hash",
            type="Photo",
            is_rotated=False,
            creation_datetime=datetime.now(),
            latitude=None,
            longitude=None,
            transcription=None,
            faiss_index_id=None,
        )
        db_session.add(item)
        db_session.commit()

        fetched = db_session.query(Item).filter(Item.file_hash == "no_gps_hash").first()
        assert fetched.latitude is None
        assert fetched.longitude is None
        assert fetched.transcription is None

    def test_item_repr(self, db_session):
        """__repr__ doğru formatta string döner."""
        item = Item(
            file_path="/test/repr.jpg",
            file_hash="repr_hash",
            type="Photo",
            has_consent=True,
            is_rotated=False,
            creation_datetime=datetime.now()
        )
        db_session.add(item)
        db_session.commit()

        repr_str = repr(item)
        assert "Item" in repr_str
        assert "Photo" in repr_str


class TestEventItemRelationship:
    """Event - Item ilişki testleri."""

    def test_event_has_items(self, db_session):
        """Event'e bağlı Item'lar listelenebilir."""
        event = Event(
            title="Yaz Tatili",
            start_date=datetime(2025, 7, 1),
            end_date=datetime(2025, 7, 15),
        )
        db_session.add(event)
        db_session.commit()

        item = Item(
            file_path="/test/vacation.jpg",
            file_hash="vacation_hash",
            type="Photo",
            is_rotated=False,
            creation_datetime=datetime(2025, 7, 5),
            event_id=event.event_id,
        )
        db_session.add(item)
        db_session.commit()

        db_session.refresh(event)
        assert len(event.items) == 1
        assert event.items[0].file_path == "/test/vacation.jpg"

    def test_item_belongs_to_event(self, db_session):
        """Item üzerinden Event'e erişilebilir."""
        event = Event(
            title="Doğum Günü",
            start_date=datetime(2025, 8, 10),
            end_date=datetime(2025, 8, 10),
        )
        db_session.add(event)
        db_session.commit()

        item = Item(
            file_path="/test/birthday.jpg",
            file_hash="bday_hash",
            type="Photo",
            is_rotated=False,
            creation_datetime=datetime(2025, 8, 10),
            event_id=event.event_id,
        )
        db_session.add(item)
        db_session.commit()

        db_session.refresh(item)
        assert item.event.title == "Doğum Günü"
