import tempfile
from pathlib import Path
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database.schema import Base, Event, Flashcard, ReviewLog, Item
from security.encryption_manager import EncryptionManager
from src.flashcards.sm2_scheduler import SM2Scheduler


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

    from config import Config
    monkeypatch.setattr(Config, "SECRET_KEY_PATH", str(secret_key_path))

    return EncryptionManager()


@pytest.fixture
def sample_event(session):
    event_obj = Event(
        title="Istanbul Gezisi",
        start_date=datetime(2024, 3, 15),
        end_date=datetime(2024, 3, 17),
        main_location="Istanbul, Kadikoy",
        summary="dummy-summary",
        cover_item_id=None,
    )
    session.add(event_obj)
    session.commit()

    item = Item(
        file_path="test_file.jpg",
        file_hash="hash_123",
        type="Photo",
        has_consent=True,
        is_rotated=False,
        creation_datetime=datetime(2024, 3, 15, 10, 0, 0),
        latitude=41.0,
        longitude=29.0,
        transcription=None,
        faiss_index_id=None,
        event_id=event_obj.event_id,
    )
    session.add(item)
    session.commit()

    return event_obj


@pytest.fixture
def sample_flashcard(session, encryption_manager, sample_event):
    flashcard = Flashcard(
        event_id=sample_event.event_id,
        question=encryption_manager.encrypt_string("Bu olay nerede gerceklesti?"),
        answer=encryption_manager.encrypt_string("Istanbul, Kadikoy"),
        related_item_ids=None,
    )
    session.add(flashcard)
    session.commit()
    return flashcard


def test_calculate_easiness_factor_rating_4(session):
    scheduler = SM2Scheduler(session)
    ef = scheduler.calculate_easiness_factor(2.5, 4)
    assert ef == 2.5


def test_calculate_easiness_factor_has_minimum(session):
    scheduler = SM2Scheduler(session)
    ef = scheduler.calculate_easiness_factor(1.3, 1)
    assert ef == 1.3


def test_calculate_interval_first_review(session):
    scheduler = SM2Scheduler(session)
    interval = scheduler.calculate_interval(0, 2.5, 0)
    assert interval == 1


def test_calculate_interval_second_review(session):
    scheduler = SM2Scheduler(session)
    interval = scheduler.calculate_interval(1, 2.5, 1)
    assert interval == 6


def test_calculate_interval_third_review(session):
    scheduler = SM2Scheduler(session)
    interval = scheduler.calculate_interval(2, 2.36, 6)
    assert interval == 14


def test_record_first_review_creates_review_log(session, sample_flashcard):
    scheduler = SM2Scheduler(session)

    result = scheduler.record_review(sample_flashcard.flashcard_id, 4)

    logs = session.query(ReviewLog).filter(
        ReviewLog.flashcard_id == sample_flashcard.flashcard_id
    ).all()

    assert len(logs) == 1
    assert logs[0].user_rating == 4
    assert result["interval_days"] == 1
    assert result["easiness_factor"] == 2.5


def test_second_successful_review_interval_becomes_6(session, sample_flashcard):
    scheduler = SM2Scheduler(session)

    scheduler.record_review(sample_flashcard.flashcard_id, 4)
    result = scheduler.record_review(sample_flashcard.flashcard_id, 4)

    assert result["interval_days"] == 6


def test_failed_review_resets_interval_to_1(session, sample_flashcard):
    scheduler = SM2Scheduler(session)

    scheduler.record_review(sample_flashcard.flashcard_id, 5)
    scheduler.record_review(sample_flashcard.flashcard_id, 5)
    result = scheduler.record_review(sample_flashcard.flashcard_id, 2)

    assert result["interval_days"] == 1


def test_calculate_next_review_returns_future_date(session, sample_flashcard):
    scheduler = SM2Scheduler(session)

    next_review = scheduler.calculate_next_review(sample_flashcard.flashcard_id, 4)

    assert isinstance(next_review, datetime)
    assert next_review > datetime.utcnow()


def test_get_due_flashcards_includes_unreviewed_card(session, sample_flashcard):
    scheduler = SM2Scheduler(session)

    due_cards = scheduler.get_due_flashcards()

    assert len(due_cards) >= 1
    assert due_cards[0]["flashcard_id"] == sample_flashcard.flashcard_id
    assert due_cards[0]["question"] == "Bu olay nerede gerceklesti?"
    assert due_cards[0]["answer"] == "Istanbul, Kadikoy"


def test_get_due_flashcards_excludes_not_due_card(session, sample_flashcard):
    scheduler = SM2Scheduler(session)

    future_log = ReviewLog(
        flashcard_id=sample_flashcard.flashcard_id,
        review_date=datetime.utcnow(),
        user_rating=5,
        next_review_date=datetime.utcnow() + timedelta(days=10),
    )
    session.add(future_log)
    session.commit()

    due_cards = scheduler.get_due_flashcards()

    assert all(card["flashcard_id"] != sample_flashcard.flashcard_id for card in due_cards)


def test_get_flashcard_stats(session, sample_flashcard):
    scheduler = SM2Scheduler(session)

    scheduler.record_review(sample_flashcard.flashcard_id, 4)
    scheduler.record_review(sample_flashcard.flashcard_id, 5)

    stats = scheduler.get_flashcard_stats(sample_flashcard.flashcard_id)

    assert stats["flashcard_id"] == sample_flashcard.flashcard_id
    assert stats["total_reviews"] == 2
    assert stats["average_rating"] == 4.5
    assert stats["current_interval"] == 6
    assert stats["easiness_factor"] >= 2.5


def test_get_review_history(session, sample_flashcard):
    scheduler = SM2Scheduler(session)

    scheduler.record_review(sample_flashcard.flashcard_id, 4)
    scheduler.record_review(sample_flashcard.flashcard_id, 3)

    history = scheduler.get_review_history(sample_flashcard.flashcard_id)

    assert len(history) == 2
    assert history[0]["user_rating"] == 4
    assert history[1]["user_rating"] == 3


def test_get_overall_stats(session, sample_flashcard):
    scheduler = SM2Scheduler(session)

    scheduler.record_review(sample_flashcard.flashcard_id, 4)

    stats = scheduler.get_overall_stats()

    assert stats["total_flashcards"] == 1
    assert stats["total_reviews"] == 1
    assert "average_ef" in stats
    assert "due_today" in stats


def test_invalid_rating_raises_error(session, sample_flashcard):
    scheduler = SM2Scheduler(session)

    with pytest.raises(ValueError):
        scheduler.record_review(sample_flashcard.flashcard_id, 0)

    with pytest.raises(ValueError):
        scheduler.record_review(sample_flashcard.flashcard_id, 6)