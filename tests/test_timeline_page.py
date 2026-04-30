from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from config import Config
from database.schema import Base, Event, Item, Flashcard
from security.encryption_manager import EncryptionManager
from src.ui.timeline_page import TimelinePage


class DummyTimeSearch:
    def __init__(self, stats):
        self._stats = stats

    def get_timeline_stats(self):
        return self._stats


class DummySearchEngine:
    def __init__(self, stats):
        self.time_search = DummyTimeSearch(stats)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def encryption_manager(tmp_path, monkeypatch):
    secret_key_path = tmp_path / "test_secret.key"
    monkeypatch.setattr(Config, "SECRET_KEY_PATH", str(secret_key_path))
    monkeypatch.setattr(Config, "TIMELINE_TEMP_DIR", str(tmp_path / "temp"))
    return EncryptionManager()


@pytest.fixture
def timeline_stats():
    return {
        "earliest_date": datetime(2024, 1, 1),
        "latest_date": datetime(2024, 12, 31),
        "total_items": 5,
        "items_by_year": {2024: 5},
        "items_by_month": {(2024, 3): 3, (2024, 4): 2},
    }


@pytest.fixture
def search_engine(timeline_stats):
    return DummySearchEngine(timeline_stats)


@pytest.fixture
def sample_data(session, encryption_manager, tmp_path):
    encrypted_cover_path = tmp_path / "cover1.jpg"
    encrypted_cover_path.write_bytes(b"fake-image-bytes")
    encryption_manager.encrypt_file(str(encrypted_cover_path))

    event1 = Event(
        title="Istanbul Gezisi",
        start_date=datetime(2024, 3, 15),
        end_date=datetime(2024, 3, 17),
        main_location="Istanbul, Kadikoy",
        summary=encryption_manager.encrypt_string("Gunesli bir hafta sonu gezisi."),
        cover_item_id=None,
    )
    session.add(event1)
    session.commit()

    item1 = Item(
        file_path=str(encrypted_cover_path),
        file_hash="hash_cover_1",
        type="Photo",
        has_consent=True,
        is_rotated=False,
        creation_datetime=datetime(2024, 3, 15, 10, 0, 0),
        latitude=41.0,
        longitude=29.0,
        transcription=None,
        faiss_index_id=None,
        event_id=event1.event_id,
    )
    item2 = Item(
        file_path="audio1.mp3",
        file_hash="hash_audio_1",
        type="Audio",
        has_consent=True,
        is_rotated=False,
        creation_datetime=datetime(2024, 3, 15, 11, 0, 0),
        latitude=None,
        longitude=None,
        transcription=encryption_manager.encrypt_string("Kadikoy sahilde yuruduk."),
        faiss_index_id=None,
        event_id=event1.event_id,
    )
    item3 = Item(
        file_path="hidden.mp3",
        file_hash="hash_hidden_1",
        type="Audio",
        has_consent=False,
        is_rotated=False,
        creation_datetime=datetime(2024, 3, 15, 12, 0, 0),
        latitude=None,
        longitude=None,
        transcription=encryption_manager.encrypt_string("Bu veri kullanilmamali."),
        faiss_index_id=None,
        event_id=event1.event_id,
    )
    session.add_all([item1, item2, item3])
    session.commit()

    event1.cover_item_id = item1.item_id
    session.commit()

    flashcard = Flashcard(
        event_id=event1.event_id,
        question=encryption_manager.encrypt_string("Bu olay nerede gerceklesti?"),
        answer=encryption_manager.encrypt_string("Istanbul, Kadikoy"),
        related_item_ids=None,
    )
    session.add(flashcard)
    session.commit()

    event2 = Event(
        title="Ankara Gezisi",
        start_date=datetime(2024, 4, 10),
        end_date=datetime(2024, 4, 10),
        main_location="Ankara, Cankaya",
        summary=encryption_manager.encrypt_string("Ankara'da kisa bir gezi."),
        cover_item_id=None,
    )
    session.add(event2)
    session.commit()

    item4 = Item(
        file_path="ankara_photo.jpg",
        file_hash="hash_photo_ankara",
        type="Photo",
        has_consent=True,
        is_rotated=False,
        creation_datetime=datetime(2024, 4, 10, 9, 0, 0),
        latitude=39.9,
        longitude=32.8,
        transcription=None,
        faiss_index_id=None,
        event_id=event2.event_id,
    )
    session.add(item4)
    session.commit()

    return {
        "event1": event1,
        "event2": event2,
        "cover_item": item1,
    }


@pytest.fixture
def timeline_page(session, search_engine, encryption_manager):
    return TimelinePage(
        db_connection=session,
        search_engine=search_engine,
        encryption_manager=encryption_manager,
    )


def test_get_timeline_data_returns_events(timeline_page, sample_data):
    data = timeline_page.get_timeline_data()

    assert len(data) == 2
    assert data[0]["title"] == "Istanbul Gezisi"
    assert data[1]["title"] == "Ankara Gezisi"


def test_get_timeline_data_decrypts_summary(timeline_page, sample_data):
    data = timeline_page.get_timeline_data()

    first_event = data[0]
    assert first_event["summary"] == "Gunesli bir hafta sonu gezisi."


def test_get_timeline_data_counts_only_consented_items(timeline_page, sample_data):
    data = timeline_page.get_timeline_data()

    first_event = data[0]
    assert first_event["item_count"] == 2


def test_get_timeline_data_applies_date_filter(timeline_page, sample_data):
    data = timeline_page.get_timeline_data(
        start_date=datetime(2024, 4, 1),
        end_date=datetime(2024, 4, 30),
    )

    assert len(data) == 1
    assert data[0]["title"] == "Ankara Gezisi"


def test_get_event_detail_returns_decrypted_and_filtered_data(timeline_page, sample_data):
    detail = timeline_page.get_event_detail(sample_data["event1"].event_id)

    assert detail["event_id"] == sample_data["event1"].event_id
    assert detail["summary"] == "Gunesli bir hafta sonu gezisi."
    assert detail["item_count"] == 2
    assert detail["flashcard_count"] == 1
    assert len(detail["items"]) == 2
    assert all(item["transcription"] != "Bu veri kullanilmamali." for item in detail["items"])


def test_decrypt_cover_photo_creates_temp_file(timeline_page, sample_data):
    temp_path = timeline_page.decrypt_cover_photo(sample_data["event1"].event_id)

    assert temp_path is not None
    assert Path(temp_path).exists()
    assert Path(temp_path).read_bytes() == b"fake-image-bytes"


def test_decrypt_cover_photo_returns_none_when_no_cover(timeline_page, sample_data):
    temp_path = timeline_page.decrypt_cover_photo(sample_data["event2"].event_id)
    assert temp_path is None


def test_group_events_by_month(timeline_page, sample_data):
    events = timeline_page.get_timeline_data()
    grouped = timeline_page.group_events_by_period(events, period="month")

    assert len(grouped) == 2
    all_keys = list(grouped.keys())
    assert any("2024" in key for key in all_keys)


def test_group_events_by_year(timeline_page, sample_data):
    events = timeline_page.get_timeline_data()
    grouped = timeline_page.group_events_by_period(events, period="year")

    assert "2024" in grouped
    assert len(grouped["2024"]) == 2


def test_group_events_by_invalid_period_raises_error(timeline_page, sample_data):
    events = timeline_page.get_timeline_data()

    with pytest.raises(ValueError):
        timeline_page.group_events_by_period(events, period="invalid")


def test_get_timeline_stats_returns_expected_fields(timeline_page, sample_data):
    stats = timeline_page.get_timeline_stats()

    assert stats["total_events"] == 2
    assert stats["total_items"] == 3
    assert stats["locations_count"] == 2
    assert "date_range" in stats
    assert "items_by_year" in stats
    assert "items_by_month" in stats


def test_cleanup_temp_files_removes_created_files(timeline_page, sample_data):
    temp_path_1 = timeline_page.decrypt_cover_photo(sample_data["event1"].event_id)
    assert temp_path_1 is not None
    assert Path(temp_path_1).exists()

    timeline_page.cleanup_temp_files()

    assert not Path(temp_path_1).exists()
    assert timeline_page._temp_files == []
