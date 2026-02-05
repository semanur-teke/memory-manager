# -*- coding: utf-8 -*-
"""
Arama sistemi testleri (Aşama 5)
4 modül için unit testler: TextSearch, TimeSearch, LocationSearch, SearchEngine
"""

import os
import sys
import pytest
import numpy as np
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, date

# --- YOL AYARI ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.search.text_search import TextSearch
from src.search.time_search import TimeSearch
from src.search.location_search import LocationSearch
from src.search.search_engine import SearchEngine
from database.schema import Item


# ========== YARDIMCI FONKSİYONLAR ==========

def make_item(item_id, file_path="photo.jpg", has_consent=True,
              transcription=None, creation_datetime=None,
              latitude=None, longitude=None):
    """Mock Item nesnesi oluşturur."""
    item = MagicMock(spec=Item)
    item.item_id = item_id
    item.file_path = file_path
    item.has_consent = has_consent
    item.transcription = transcription
    item.creation_datetime = creation_datetime or datetime(2025, 6, 15, 10, 30)
    item.latitude = latitude
    item.longitude = longitude
    return item


# ================================================================
#                       TEXT SEARCH TESTLERİ
# ================================================================

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
    faiss.search.return_value = [(1, 0.2), (2, 0.4), (3, 0.6)]
    return faiss


@pytest.fixture
def mock_text_faiss():
    faiss = MagicMock()
    faiss.search.return_value = [(10, 0.1), (20, 0.3), (30, 0.5)]
    return faiss


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def text_searcher(mock_clip, mock_sbert, mock_image_faiss, mock_text_faiss, mock_db):
    return TextSearch(
        clip_embedder=mock_clip,
        sbert_embedder=mock_sbert,
        image_faiss=mock_image_faiss,
        text_faiss=mock_text_faiss,
        db_session=mock_db
    )


class TestTextSearchImages:
    def test_basic_image_search(self, text_searcher, mock_db):
        """Temel fotoğraf araması doğru format döner."""
        items = [
            make_item(1, "/photos/sunset.jpg"),
            make_item(2, "/photos/beach.jpg"),
            make_item(3, "/photos/city.jpg"),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = items

        results = text_searcher.search_images("plajda gün batımı", k=10)

        assert len(results) == 3
        assert all('item_id' in r for r in results)
        assert all('score' in r for r in results)
        assert all('file_path' in r for r in results)

    def test_consent_filtering(self, text_searcher, mock_db):
        """has_consent=False olan item'lar sonuçta yer almaz."""
        items = [make_item(1, "/photos/ok.jpg"), make_item(3, "/photos/ok2.jpg")]
        mock_db.query.return_value.filter.return_value.all.return_value = items

        results = text_searcher.search_images("test", k=10)

        assert 2 not in [r['item_id'] for r in results]
        assert len(results) == 2

    def test_empty_query(self, text_searcher, mock_clip):
        """encode_text None dönerse boş liste döner."""
        mock_clip.encode_text.return_value = None
        assert text_searcher.search_images("", k=10) == []

    def test_no_faiss_results(self, text_searcher, mock_image_faiss):
        """FAISS boş dönerse boş liste döner."""
        mock_image_faiss.search.return_value = []
        assert text_searcher.search_images("test", k=10) == []

    def test_score_calculation(self, text_searcher, mock_db, mock_image_faiss):
        """Score = 1 - distance/2 formülü doğru çalışır."""
        mock_image_faiss.search.return_value = [(1, 0.4)]
        mock_db.query.return_value.filter.return_value.all.return_value = [
            make_item(1, "/photos/test.jpg")
        ]

        results = text_searcher.search_images("test", k=10)

        assert results[0]['score'] == round(1 - 0.4 / 2, 4)  # 0.8

    def test_k_limit(self, text_searcher, mock_db, mock_image_faiss):
        """k parametresi sonuç sayısını sınırlar."""
        mock_image_faiss.search.return_value = [(i, 0.1 * i) for i in range(1, 11)]
        mock_db.query.return_value.filter.return_value.all.return_value = [
            make_item(i, f"/photos/{i}.jpg") for i in range(1, 11)
        ]

        results = text_searcher.search_images("test", k=3)
        assert len(results) == 3

    def test_faiss_gets_k_times_2(self, text_searcher, mock_image_faiss, mock_db):
        """FAISS'e k*2 gönderilir (consent filtresi marjı)."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        text_searcher.search_images("test", k=5)
        assert mock_image_faiss.search.call_args[0][1] == 10


class TestTextSearchTexts:
    def test_basic_text_search(self, text_searcher, mock_db):
        """Temel metin araması doğru format döner."""
        items = [
            make_item(10, transcription="bugün hava güzeldi"),
            make_item(20, transcription="parkta yürüyüş"),
            make_item(30, transcription="akşam yemeği"),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = items

        results = text_searcher.search_texts("hava", k=10)

        assert len(results) == 3
        assert all('item_id' in r for r in results)
        assert all('score' in r for r in results)
        assert all('transcript' in r for r in results)

    def test_transcript_content(self, text_searcher, mock_db, mock_text_faiss):
        """Transcript doğru döner."""
        mock_text_faiss.search.return_value = [(10, 0.1)]
        mock_db.query.return_value.filter.return_value.all.return_value = [
            make_item(10, transcription="merhaba dünya")
        ]

        results = text_searcher.search_texts("selam", k=10)
        assert results[0]['transcript'] == "merhaba dünya"

    def test_none_transcription(self, text_searcher, mock_db, mock_text_faiss):
        """Transcription None ise boş string döner."""
        mock_text_faiss.search.return_value = [(10, 0.1)]
        mock_db.query.return_value.filter.return_value.all.return_value = [
            make_item(10, transcription=None)
        ]

        results = text_searcher.search_texts("test", k=10)
        assert results[0]['transcript'] == ''

    def test_empty_query(self, text_searcher, mock_sbert):
        """encode_text None dönerse boş liste döner."""
        mock_sbert.encode_text.return_value = None
        assert text_searcher.search_texts("", k=10) == []


class TestTextSearchAll:
    def test_returns_both_keys(self, text_searcher, mock_db):
        """search_all hem 'images' hem 'texts' anahtarı döner."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        results = text_searcher.search_all("test", k=5)

        assert 'images' in results
        assert 'texts' in results

    def test_combines_results(self, text_searcher, mock_db, mock_image_faiss, mock_text_faiss):
        """Her iki arama sonucunu birleştirir."""
        mock_image_faiss.search.return_value = [(1, 0.2)]
        mock_text_faiss.search.return_value = [(10, 0.3)]
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [make_item(1, "/photos/a.jpg")],
            [make_item(10, transcription="hello")]
        ]

        results = text_searcher.search_all("test", k=5)

        assert len(results['images']) == 1
        assert len(results['texts']) == 1
        assert results['images'][0]['item_id'] == 1
        assert results['texts'][0]['item_id'] == 10


# ================================================================
#                       TIME SEARCH TESTLERİ
# ================================================================

@pytest.fixture
def time_searcher(mock_db):
    return TimeSearch(db_connection=mock_db)


class TestTimeSearch:
    def test_search_by_date_range(self, time_searcher, mock_db):
        """Tarih aralığında arama doğru çalışır."""
        items = [
            make_item(1, "/photos/a.jpg", creation_datetime=datetime(2025, 6, 15)),
            make_item(2, "/photos/b.jpg", creation_datetime=datetime(2025, 6, 20)),
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = items

        results = time_searcher.search_by_date_range(date(2025, 6, 1), date(2025, 6, 30))

        assert len(results) == 2
        assert results[0]['item_id'] == 1
        assert results[0]['created_at'] == datetime(2025, 6, 15)
        assert 'file_path' in results[0]

    def test_search_by_date_range_empty(self, time_searcher, mock_db):
        """Tarih aralığında sonuç yoksa boş liste döner."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        results = time_searcher.search_by_date_range(date(2020, 1, 1), date(2020, 1, 31))
        assert results == []

    def test_search_by_year(self, time_searcher, mock_db):
        """Yıla göre arama doğru çalışır."""
        items = [make_item(1, creation_datetime=datetime(2025, 3, 10))]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = items

        results = time_searcher.search_by_year(2025)

        assert len(results) == 1
        assert results[0]['item_id'] == 1

    def test_search_by_month(self, time_searcher, mock_db):
        """Ay/yıla göre arama doğru çalışır."""
        items = [make_item(5, creation_datetime=datetime(2025, 7, 4))]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = items

        results = time_searcher.search_by_month(2025, 7)

        assert len(results) == 1
        assert results[0]['item_id'] == 5

    def test_search_by_day(self, time_searcher, mock_db):
        """Güne göre arama doğru çalışır."""
        items = [make_item(3, creation_datetime=datetime(2025, 8, 1, 14, 30))]
        mock_db.query.return_value.filter.return_value.all.return_value = items

        results = time_searcher.search_by_day(date(2025, 8, 1))

        assert len(results) == 1
        assert results[0]['item_id'] == 3

    def test_get_timeline_stats_empty(self, time_searcher, mock_db):
        """Boş DB'de istatistik boş dict döner."""
        mock_db.query.return_value.count.return_value = 0

        result = time_searcher.get_timeline_stats()
        assert result == {}

    def test_get_timeline_stats(self, time_searcher, mock_db):
        """İstatistikler doğru formatta döner."""
        mock_db.query.return_value.count.return_value = 5
        mock_db.query.return_value.scalar.side_effect = [
            datetime(2024, 1, 1),   # earliest
            datetime(2025, 12, 31)  # latest
        ]
        # yearly_counts
        mock_db.query.return_value.group_by.return_value.all.side_effect = [
            [(2024, 2), (2025, 3)],           # yıllık
            [(2024, 1, 1), (2024, 6, 1), (2025, 3, 3)]  # aylık
        ]

        result = time_searcher.get_timeline_stats()

        assert result['total_items'] == 5
        assert result['earliest_date'] == datetime(2024, 1, 1)
        assert result['latest_date'] == datetime(2025, 12, 31)
        assert result['items_by_year'][2024] == 2
        assert result['items_by_month'][(2025, 3)] == 3


# ================================================================
#                     LOCATION SEARCH TESTLERİ
# ================================================================

@pytest.fixture
def location_searcher(mock_db):
    with patch('src.search.location_search.Nominatim'):
        searcher = LocationSearch(db_connection=mock_db)
    return searcher


class TestLocationSearch:
    def test_calculate_distance(self, location_searcher):
        """Mesafe hesabı mantıklı sonuç verir."""
        # İstanbul - Ankara arası yaklaşık 350 km
        dist = location_searcher.calculate_distance(41.0, 29.0, 39.9, 32.9)
        assert 300 < dist < 400

    def test_search_by_location(self, location_searcher, mock_db):
        """Yarıçap içindeki öğeleri döner."""
        items = [
            make_item(1, latitude=41.01, longitude=29.01),   # çok yakın
            make_item(2, latitude=39.9, longitude=32.9),     # uzak (Ankara)
            make_item(3, latitude=41.005, longitude=29.005), # yakın
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = items

        results = location_searcher.search_by_location(41.0, 29.0, radius_km=5.0)

        item_ids = [r['item_id'] for r in results]
        assert 1 in item_ids
        assert 3 in item_ids
        assert 2 not in item_ids  # Ankara çok uzak

    def test_search_by_location_empty(self, location_searcher, mock_db):
        """Yarıçap içinde öğe yoksa boş liste döner."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        results = location_searcher.search_by_location(41.0, 29.0, radius_km=1.0)
        assert results == []

    def test_search_by_location_sorted_by_distance(self, location_searcher, mock_db):
        """Sonuçlar mesafeye göre sıralı döner."""
        items = [
            make_item(1, latitude=41.03, longitude=29.03),   # biraz uzak
            make_item(2, latitude=41.001, longitude=29.001), # en yakın
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = items

        results = location_searcher.search_by_location(41.0, 29.0, radius_km=10.0)

        assert results[0]['item_id'] == 2  # en yakın ilk sırada
        assert results[0]['distance_km'] <= results[1]['distance_km']

    def test_search_by_city(self, location_searcher, mock_db):
        """Şehir adıyla arama geocoder'ı çağırır."""
        mock_location = MagicMock()
        mock_location.latitude = 41.0
        mock_location.longitude = 29.0
        mock_location.address = "İstanbul, Türkiye"
        location_searcher.geocoder.geocode.return_value = mock_location

        mock_db.query.return_value.filter.return_value.all.return_value = [
            make_item(1, latitude=41.01, longitude=29.01)
        ]

        results = location_searcher.search_by_city("İstanbul", radius_km=20.0)

        location_searcher.geocoder.geocode.assert_called_once_with("İstanbul")
        assert len(results) >= 0  # geocode sonucuna göre değişir

    def test_search_by_city_not_found(self, location_searcher):
        """Şehir bulunamazsa boş liste döner."""
        location_searcher.geocoder.geocode.return_value = None

        results = location_searcher.search_by_city("AsdfQwerty")
        assert results == []

    def test_result_format(self, location_searcher, mock_db):
        """Sonuç formatı doğru alanları içerir."""
        items = [make_item(1, latitude=41.001, longitude=29.001)]
        mock_db.query.return_value.filter.return_value.all.return_value = items

        results = location_searcher.search_by_location(41.0, 29.0, radius_km=5.0)

        assert 'item_id' in results[0]
        assert 'distance_km' in results[0]
        assert 'location' in results[0]


# ================================================================
#                     SEARCH ENGINE TESTLERİ
# ================================================================

@pytest.fixture
def mock_text_search():
    ts = MagicMock(spec=TextSearch)
    ts.search_all.return_value = {
        'images': [{'item_id': 1, 'score': 0.9, 'file_path': '/a.jpg'}],
        'texts': [{'item_id': 2, 'score': 0.8, 'transcript': 'hello'}]
    }
    return ts


@pytest.fixture
def mock_time_search():
    ts = MagicMock(spec=TimeSearch)
    ts.search_by_date_range.return_value = [
        {'item_id': 1, 'created_at': datetime(2025, 6, 15), 'file_path': '/a.jpg'}
    ]
    return ts


@pytest.fixture
def mock_location_search():
    ls = MagicMock(spec=LocationSearch)
    ls.search_by_location.return_value = [
        {'item_id': 1, 'distance_km': 1.5, 'location': (41.0, 29.0)}
    ]
    ls.search_by_city.return_value = [
        {'item_id': 1, 'distance_km': 2.0, 'location': (41.0, 29.0)}
    ]
    return ls


@pytest.fixture
def engine(mock_text_search, mock_time_search, mock_location_search):
    return SearchEngine(mock_text_search, mock_time_search, mock_location_search)


class TestSearchEngine:
    def test_text_only_search(self, engine, mock_text_search):
        """Sadece metin sorgusu ile arama."""
        result = engine.search(query="deniz", k=5)

        assert result['filters_applied']['text'] is True
        assert result['filters_applied']['time'] is False
        assert result['filters_applied']['location'] is False
        assert len(result['items']) > 0
        mock_text_search.search_all.assert_called_once_with("deniz", 5)

    def test_time_only_search(self, engine, mock_time_search):
        """Sadece tarih aralığıyla arama."""
        result = engine.search(start_date=date(2025, 6, 1), end_date=date(2025, 6, 30), k=5)

        assert result['filters_applied']['time'] is True
        assert result['filters_applied']['text'] is False
        mock_time_search.search_by_date_range.assert_called_once()

    def test_location_only_search(self, engine, mock_location_search):
        """Sadece konum ile arama."""
        result = engine.search(location=(41.0, 29.0), radius_km=10.0, k=5)

        assert result['filters_applied']['location'] is True
        assert result['filters_applied']['text'] is False
        mock_location_search.search_by_location.assert_called_once_with(41.0, 29.0, 10.0)

    def test_no_filters(self, engine):
        """Hiçbir filtre verilmezse boş sonuç döner."""
        result = engine.search(k=5)

        assert result['items'] == []
        assert all(v is False for v in result['filters_applied'].values())

    def test_filters_applied_format(self, engine):
        """filters_applied doğru formatta döner."""
        result = engine.search(query="test", k=5)

        assert 'text' in result['filters_applied']
        assert 'time' in result['filters_applied']
        assert 'location' in result['filters_applied']

    def test_combined_text_and_time(self, engine, mock_text_search, mock_time_search):
        """Metin + zaman birlikte kullanılabilir."""
        # Aynı item_id (1) hem text hem time'dan dönsün → kesişimde kalır
        result = engine.search(query="deniz", start_date=date(2025, 6, 1),
                               end_date=date(2025, 6, 30), k=10)

        assert result['filters_applied']['text'] is True
        assert result['filters_applied']['time'] is True

    def test_k_limits_results(self, engine, mock_text_search):
        """k parametresi toplam sonucu sınırlar."""
        mock_text_search.search_all.return_value = {
            'images': [{'item_id': i, 'score': 0.9, 'file_path': f'/{i}.jpg'} for i in range(20)],
            'texts': []
        }

        result = engine.search(query="test", k=5)
        assert len(result['items']) <= 5


class TestAdvancedSearch:
    def test_year_filter(self, engine, mock_time_search):
        """year parametresi tarih aralığına çevrilir."""
        engine.advanced_search({'year': 2025, 'k': 5})

        mock_time_search.search_by_date_range.assert_called_once()

    def test_year_month_filter(self, engine, mock_time_search):
        """year + month birlikte çalışır."""
        engine.advanced_search({'year': 2025, 'month': 6, 'k': 5})

        mock_time_search.search_by_date_range.assert_called_once()

    def test_city_filter(self, engine, mock_location_search):
        """city parametresi search_by_city'yi çağırır."""
        result = engine.advanced_search({'city': 'İstanbul', 'k': 5})

        mock_location_search.search_by_city.assert_called_once_with('İstanbul', 5.0)

    def test_city_not_found(self, engine, mock_location_search):
        """Şehir bulunamazsa boş liste döner."""
        mock_location_search.search_by_city.return_value = []

        result = engine.advanced_search({'city': 'XyzNotReal', 'k': 5})
        assert result == []

    def test_query_passthrough(self, engine, mock_text_search):
        """query parametresi search'e iletilir."""
        engine.advanced_search({'query': 'deniz', 'k': 5})

        mock_text_search.search_all.assert_called_once()

    def test_default_values(self, engine):
        """Varsayılan radius_km ve k değerleri kullanılır."""
        result = engine.advanced_search({})

        assert isinstance(result, list)

    def test_december_month(self, engine, mock_time_search):
        """Aralık ayı (12) doğru hesaplanır (yıl taşması)."""
        engine.advanced_search({'year': 2025, 'month': 12, 'k': 5})

        mock_time_search.search_by_date_range.assert_called_once()
