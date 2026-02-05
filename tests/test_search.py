# -*- coding: utf-8 -*-
"""
Arama sistemi testleri (Aşama 5)
Mock embedder ve mock DB session ile TextSearch unit testleri.
"""

import os
import sys
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime

# --- YOL AYARI ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.search.text_search import TextSearch
from database.schema import Item


# ========== FIXTURES ==========

def make_item(item_id, file_path="photo.jpg", has_consent=True, transcription=None):
    """Mock Item nesnesi oluşturur."""
    item = MagicMock(spec=Item)
    item.item_id = item_id
    item.file_path = file_path
    item.has_consent = has_consent
    item.transcription = transcription
    return item


@pytest.fixture
def mock_clip():
    clip = MagicMock()
    clip.encode_text.return_value = np.random.randn(512).astype('float32')
    return clip


@pytest.fixture
def mock_sbert():
    sbert = MagicMock()
    sbert.encode_text.return_value = np.random.randn(384).astype('float32')
    return sbert


@pytest.fixture
def mock_image_faiss():
    faiss = MagicMock()
    # Varsayılan: 3 sonuç döndür (item_id, distance)
    faiss.search.return_value = [(1, 0.2), (2, 0.4), (3, 0.6)]
    return faiss


@pytest.fixture
def mock_text_faiss():
    faiss = MagicMock()
    faiss.search.return_value = [(10, 0.1), (20, 0.3), (30, 0.5)]
    return faiss


@pytest.fixture
def mock_db_session():
    session = MagicMock()
    return session


@pytest.fixture
def searcher(mock_clip, mock_sbert, mock_image_faiss, mock_text_faiss, mock_db_session):
    return TextSearch(
        clip_embedder=mock_clip,
        sbert_embedder=mock_sbert,
        image_faiss=mock_image_faiss,
        text_faiss=mock_text_faiss,
        db_session=mock_db_session
    )


# ========== search_images TESTLERİ ==========

class TestSearchImages:
    def test_basic_image_search(self, searcher, mock_db_session):
        """Temel fotoğraf araması çalışır ve doğru format döner."""
        items = [
            make_item(1, "/photos/sunset.jpg", has_consent=True),
            make_item(2, "/photos/beach.jpg", has_consent=True),
            make_item(3, "/photos/city.jpg", has_consent=True),
        ]
        mock_db_session.query.return_value.filter.return_value.all.return_value = items

        results = searcher.search_images("plajda gün batımı", k=10)

        assert len(results) == 3
        assert all('item_id' in r for r in results)
        assert all('score' in r for r in results)
        assert all('file_path' in r for r in results)

    def test_consent_filtering(self, searcher, mock_db_session):
        """has_consent=False olan item'lar filtrelenir."""
        # DB sadece consent=True olanları döner (item 2 consent=False, DB'den gelmez)
        items = [
            make_item(1, "/photos/ok.jpg", has_consent=True),
            make_item(3, "/photos/ok2.jpg", has_consent=True),
        ]
        mock_db_session.query.return_value.filter.return_value.all.return_value = items

        results = searcher.search_images("test", k=10)

        item_ids = [r['item_id'] for r in results]
        assert 2 not in item_ids
        assert len(results) == 2

    def test_empty_query_returns_empty(self, searcher, mock_clip):
        """Boş sorgu None embedding döner → boş sonuç."""
        mock_clip.encode_text.return_value = None

        results = searcher.search_images("", k=10)

        assert results == []

    def test_no_faiss_results(self, searcher, mock_image_faiss, mock_db_session):
        """FAISS boş sonuç dönerse → boş liste."""
        mock_image_faiss.search.return_value = []

        results = searcher.search_images("test", k=10)

        assert results == []

    def test_score_calculation(self, searcher, mock_db_session, mock_image_faiss):
        """Score doğru hesaplanır: 1 - distance/2."""
        mock_image_faiss.search.return_value = [(1, 0.4)]
        items = [make_item(1, "/photos/test.jpg", has_consent=True)]
        mock_db_session.query.return_value.filter.return_value.all.return_value = items

        results = searcher.search_images("test", k=10)

        assert len(results) == 1
        expected_score = round(1 - 0.4 / 2, 4)  # 0.8
        assert results[0]['score'] == expected_score

    def test_k_limit_respected(self, searcher, mock_db_session, mock_image_faiss):
        """k parametresi sonuç sayısını sınırlar."""
        mock_image_faiss.search.return_value = [(i, 0.1 * i) for i in range(1, 11)]
        items = [make_item(i, f"/photos/{i}.jpg", has_consent=True) for i in range(1, 11)]
        mock_db_session.query.return_value.filter.return_value.all.return_value = items

        results = searcher.search_images("test", k=3)

        assert len(results) == 3

    def test_faiss_called_with_k_times_2(self, searcher, mock_image_faiss, mock_db_session):
        """FAISS'e k*2 gönderilir (consent filtresi için marj)."""
        items = [make_item(1, "/photos/a.jpg"), make_item(2, "/photos/b.jpg"), make_item(3, "/photos/c.jpg")]
        mock_db_session.query.return_value.filter.return_value.all.return_value = items

        searcher.search_images("test", k=5)

        _, kwargs = mock_image_faiss.search.call_args
        # Positional args check
        args = mock_image_faiss.search.call_args[0]
        assert args[1] == 10  # k*2 = 5*2 = 10


# ========== search_texts TESTLERİ ==========

class TestSearchTexts:
    def test_basic_text_search(self, searcher, mock_db_session):
        """Temel metin araması çalışır ve doğru format döner."""
        items = [
            make_item(10, "/audio/a.mp3", has_consent=True, transcription="bugün hava güzeldi"),
            make_item(20, "/audio/b.mp3", has_consent=True, transcription="parkta yürüyüş yaptık"),
            make_item(30, "/audio/c.mp3", has_consent=True, transcription="akşam yemeği hazırladık"),
        ]
        mock_db_session.query.return_value.filter.return_value.all.return_value = items

        results = searcher.search_texts("hava durumu", k=10)

        assert len(results) == 3
        assert all('item_id' in r for r in results)
        assert all('score' in r for r in results)
        assert all('transcript' in r for r in results)

    def test_transcript_returned(self, searcher, mock_db_session, mock_text_faiss):
        """Transcript doğru şekilde döner."""
        mock_text_faiss.search.return_value = [(10, 0.1)]
        items = [make_item(10, "/audio/a.mp3", has_consent=True, transcription="merhaba dünya")]
        mock_db_session.query.return_value.filter.return_value.all.return_value = items

        results = searcher.search_texts("selam", k=10)

        assert results[0]['transcript'] == "merhaba dünya"

    def test_none_transcription_returns_empty_string(self, searcher, mock_db_session, mock_text_faiss):
        """Transcription None ise boş string döner."""
        mock_text_faiss.search.return_value = [(10, 0.1)]
        items = [make_item(10, "/audio/a.mp3", has_consent=True, transcription=None)]
        mock_db_session.query.return_value.filter.return_value.all.return_value = items

        results = searcher.search_texts("test", k=10)

        assert results[0]['transcript'] == ''

    def test_empty_query_returns_empty(self, searcher, mock_sbert):
        """Boş sorgu → boş sonuç."""
        mock_sbert.encode_text.return_value = None

        results = searcher.search_texts("", k=10)

        assert results == []

    def test_consent_filtering(self, searcher, mock_db_session):
        """has_consent filtrelemesi metin aramasında da çalışır."""
        # Sadece consent=True olan item 10 ve 30 DB'den döner
        items = [
            make_item(10, "/audio/a.mp3", has_consent=True, transcription="text1"),
            make_item(30, "/audio/c.mp3", has_consent=True, transcription="text3"),
        ]
        mock_db_session.query.return_value.filter.return_value.all.return_value = items

        results = searcher.search_texts("test", k=10)

        item_ids = [r['item_id'] for r in results]
        assert 20 not in item_ids
        assert len(results) == 2


# ========== search_all TESTLERİ ==========

class TestSearchAll:
    def test_returns_both_keys(self, searcher, mock_db_session):
        """search_all hem 'images' hem 'texts' anahtarı döner."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        results = searcher.search_all("test", k=5)

        assert 'images' in results
        assert 'texts' in results

    def test_combines_results(self, searcher, mock_db_session, mock_image_faiss, mock_text_faiss):
        """Her iki arama sonucunu birleştirir."""
        img_items = [make_item(1, "/photos/a.jpg", has_consent=True)]
        txt_items = [make_item(10, "/audio/a.mp3", has_consent=True, transcription="hello")]

        # İlk çağrı (search_images) ve ikinci çağrı (search_texts) farklı sonuç dönsün
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            img_items, txt_items
        ]
        mock_image_faiss.search.return_value = [(1, 0.2)]
        mock_text_faiss.search.return_value = [(10, 0.3)]

        results = searcher.search_all("test", k=5)

        assert len(results['images']) == 1
        assert len(results['texts']) == 1
        assert results['images'][0]['item_id'] == 1
        assert results['texts'][0]['item_id'] == 10
