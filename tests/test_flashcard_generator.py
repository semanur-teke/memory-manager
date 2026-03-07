from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from config import Config
from database.schema import Base, Event, Flashcard, Item
from security.encryption_manager import EncryptionManager
from src.flashcards.flashcard_generator import FlashcardGenerator


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
    return EncryptionManager()


@pytest.fixture
def generator(session, encryption_manager):
    return FlashcardGenerator(
        db_connection=session,
        encryption_manager=encryption_manager,
    )


@pytest.fixture
def sample_event(session, encryption_manager):
    event_obj = Event(
        title="Istanbul Gezisi",
        start_date=datetime(2024, 3, 15),
        end_date=datetime(2024, 3, 17),
        main_location="Istanbul, Kadikoy",
        summary=encryption_manager.encrypt_string("Gunesli bir hafta sonu gezisi ve kahve molasi."),
        cover_item_id=None,
    )
    session.add(event_obj)
    session.commit()
    return event_obj


@pytest.fixture
def sample_items(session, encryption_manager, sample_event):
    items = [
        Item(
            file_path="photo1.jpg",
            file_hash="hash_photo_1",
            type="Photo",
            has_consent=True,
            is_rotated=False,
            creation_datetime=datetime(2024, 3, 15, 10, 0, 0),
            latitude=41.0,
            longitude=29.0,
            transcription=None,
            faiss_index_id=None,
            event_id=sample_event.event_id,
        ),
        Item(
            file_path="photo2.jpg",
            file_hash="hash_photo_2",
            type="Photo",
            has_consent=True,
            is_rotated=False,
            creation_datetime=datetime(2024, 3, 15, 11, 0, 0),
            latitude=41.1,
            longitude=29.1,
            transcription=None,
            faiss_index_id=None,
            event_id=sample_event.event_id,
        ),
        Item(
            file_path="audio1.mp3",
            file_hash="hash_audio_1",
            type="Audio",
            has_consent=True,
            is_rotated=False,
            creation_datetime=datetime(2024, 3, 15, 12, 0, 0),
            latitude=None,
            longitude=None,
            transcription=encryption_manager.encrypt_string(
                "Kadikoy sahilde yuruduk ve uzun uzun proje konustuk."
            ),
            faiss_index_id=None,
            event_id=sample_event.event_id,
        ),
        Item(
            file_path="hidden_audio.mp3",
            file_hash="hash_audio_hidden",
            type="Audio",
            has_consent=False,
            is_rotated=False,
            creation_datetime=datetime(2024, 3, 15, 13, 0, 0),
            latitude=None,
            longitude=None,
            transcription=encryption_manager.encrypt_string(
                "Bu kayit consent olmadigi icin kullanilmamali."
            ),
            faiss_index_id=None,
            event_id=sample_event.event_id,
        ),
    ]
    session.add_all(items)
    session.commit()
    return items


def test_create_location_card(generator, sample_event):
    result = generator.create_location_card(sample_event)

    assert result is not None
    question, answer = result
    assert "nerede" in question.lower()
    assert "Istanbul" in answer


def test_create_location_card_returns_none_when_location_missing(generator, session, encryption_manager):
    event_obj = Event(
        title="Konumsuz Event",
        start_date=datetime(2024, 5, 1),
        end_date=datetime(2024, 5, 1),
        main_location=None,
        summary=encryption_manager.encrypt_string("Konum bilgisi yok."),
        cover_item_id=None,
    )
    session.add(event_obj)
    session.commit()

    result = generator.create_location_card(event_obj)
    assert result is None


def test_create_date_card_single_day(generator, session, encryption_manager):
    event_obj = Event(
        title="Tek Gunluk Event",
        start_date=datetime(2024, 4, 10),
        end_date=datetime(2024, 4, 10),
        main_location="Ankara",
        summary=encryption_manager.encrypt_string("Tek gunluk test"),
        cover_item_id=None,
    )
    session.add(event_obj)
    session.commit()

    question, answer = generator.create_date_card(event_obj)

    assert "ne zaman" in question.lower()
    assert "2024" in answer
    assert "10" in answer


def test_create_date_card_multi_day(generator, sample_event):
    question, answer = generator.create_date_card(sample_event)

    assert "ne zaman" in question.lower()
    assert "2024" in answer
    assert "15" in answer
    assert "17" in answer


def test_create_content_card(generator, sample_event, sample_items):
    result = generator.create_content_card(sample_event, sample_items)

    assert result is not None
    question, answer = result
    assert "icerigi" in question.lower() or "nedir" in question.lower()
    assert "Kadikoy" in answer or "proje" in answer
    assert "consent olmadigi" not in answer


def test_create_content_card_returns_none_without_transcript(generator, session, encryption_manager, sample_event):
    items = [
        Item(
            file_path="photo_only.jpg",
            file_hash="hash_photo_only",
            type="Photo",
            has_consent=True,
            is_rotated=False,
            creation_datetime=datetime(2024, 3, 16, 10, 0, 0),
            latitude=None,
            longitude=None,
            transcription=None,
            faiss_index_id=None,
            event_id=sample_event.event_id,
        )
    ]
    session.add_all(items)
    session.commit()

    result = generator.create_content_card(sample_event, items)
    assert result is None


def test_create_count_card(generator, sample_event, sample_items):
    question, answer = generator.create_count_card(sample_event, sample_items)

    assert "kac" in question.lower()
    assert "2" in answer
    assert "fotograf" in answer.lower()
    assert "1" in answer
    assert "ses" in answer.lower()


def test_save_flashcard_encrypts_data(generator, session, sample_event):
    flashcard_id = generator.save_flashcard(
        event_id=sample_event.event_id,
        question="Bu olay nerede gerceklesti?",
        answer="Istanbul, Kadikoy",
    )

    raw = (
        session.query(Flashcard)
        .filter(Flashcard.flashcard_id == flashcard_id)
        .first()
    )

    assert raw is not None
    assert raw.question != "Bu olay nerede gerceklesti?"
    assert raw.answer != "Istanbul, Kadikoy"


def test_get_flashcard_decrypted_returns_plain_text(generator, sample_event):
    flashcard_id = generator.save_flashcard(
        event_id=sample_event.event_id,
        question="Bu olay nerede gerceklesti?",
        answer="Istanbul, Kadikoy",
    )

    decrypted = generator.get_flashcard_decrypted(flashcard_id)

    assert decrypted["flashcard_id"] == flashcard_id
    assert decrypted["event_id"] == sample_event.event_id
    assert decrypted["question"] == "Bu olay nerede gerceklesti?"
    assert decrypted["answer"] == "Istanbul, Kadikoy"


def test_generate_for_event_creates_expected_cards(generator, session, sample_event, sample_items):
    created_cards = generator.generate_for_event(sample_event.event_id)

    assert len(created_cards) >= 3

    saved_cards = (
        session.query(Flashcard)
        .filter(Flashcard.event_id == sample_event.event_id)
        .all()
    )

    assert len(saved_cards) == len(created_cards)

    decrypted_cards = [
        generator.get_flashcard_decrypted(card.flashcard_id)
        for card in saved_cards
    ]
    questions = [card["question"] for card in decrypted_cards]

    assert any("nerede" in q.lower() for q in questions)
    assert any("ne zaman" in q.lower() for q in questions)
    assert any("kac" in q.lower() for q in questions)


def test_generate_for_event_uses_only_consented_items(generator, session, sample_event, sample_items):
    generator.generate_for_event(sample_event.event_id)

    saved_cards = (
        session.query(Flashcard)
        .filter(Flashcard.event_id == sample_event.event_id)
        .all()
    )

    decrypted_cards = [
        generator.get_flashcard_decrypted(card.flashcard_id)
        for card in saved_cards
    ]

    answers = " ".join(card["answer"] for card in decrypted_cards)
    assert "consent olmadigi" not in answers


def test_generate_for_all_events_creates_cards_only_for_events_without_flashcards(
    generator,
    session,
    encryption_manager,
    sample_event,
    sample_items,
):
    existing_id = generator.save_flashcard(
        event_id=sample_event.event_id,
        question="Onceden var olan kart?",
        answer="Evet",
    )

    second_event = Event(
        title="Ankara Gezisi",
        start_date=datetime(2024, 6, 1),
        end_date=datetime(2024, 6, 2),
        main_location="Ankara, Cankaya",
        summary=encryption_manager.encrypt_string("Ikinci event ozeti"),
        cover_item_id=None,
    )
    session.add(second_event)
    session.commit()

    second_items = [
        Item(
            file_path="ankara_photo.jpg",
            file_hash="hash_ankara_photo",
            type="Photo",
            has_consent=True,
            is_rotated=False,
            creation_datetime=datetime(2024, 6, 1, 9, 0, 0),
            latitude=None,
            longitude=None,
            transcription=None,
            faiss_index_id=None,
            event_id=second_event.event_id,
        ),
        Item(
            file_path="ankara_audio.mp3",
            file_hash="hash_ankara_audio",
            type="Audio",
            has_consent=True,
            is_rotated=False,
            creation_datetime=datetime(2024, 6, 1, 10, 0, 0),
            latitude=None,
            longitude=None,
            transcription=encryption_manager.encrypt_string("Ankara event transkripti"),
            faiss_index_id=None,
            event_id=second_event.event_id,
        ),
    ]
    session.add_all(second_items)
    session.commit()

    total_created = generator.generate_for_all_events()

    assert total_created >= 1

    first_event_cards = (
        session.query(Flashcard)
        .filter(Flashcard.event_id == sample_event.event_id)
        .all()
    )
    second_event_cards = (
        session.query(Flashcard)
        .filter(Flashcard.event_id == second_event.event_id)
        .all()
    )

    assert len(first_event_cards) == 1
    assert len(second_event_cards) >= 1
    assert existing_id in [card.flashcard_id for card in first_event_cards]