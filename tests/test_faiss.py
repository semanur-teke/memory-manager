# tests/test_faiss.py
"""
FaissManager testleri.
GERÇEK FAISS index kullanır (hafif, mock gerekmez).
"""

import pytest
import numpy as np
from pathlib import Path
from src.embedding.faiss_manager import FaissManager


@pytest.fixture
def faiss_flat(temp_dir):
    """FlatL2 (kaba kuvvet) index ile FaissManager."""
    return FaissManager(
        index_path=str(temp_dir / "test_flat.faiss"),
        dimension=384,
        index_type="flat"
    )


@pytest.fixture
def faiss_hnsw(temp_dir):
    """HNSW (hızlı yaklaşık) index ile FaissManager."""
    return FaissManager(
        index_path=str(temp_dir / "test_hnsw.faiss"),
        dimension=384,
        index_type="hnsw"
    )


class TestCreateIndex:
    """Index oluşturma testleri."""

    def test_flat_index_created(self, faiss_flat):
        """FlatL2 index başarıyla oluşturulur."""
        assert faiss_flat.index is not None
        assert faiss_flat.get_index_size() == 0

    def test_hnsw_index_created(self, faiss_hnsw):
        """HNSW index başarıyla oluşturulur."""
        assert faiss_hnsw.index is not None
        assert faiss_hnsw.get_index_size() == 0


class TestAddAndSearch:
    """Vektör ekleme ve arama testleri."""

    def test_add_single_vector(self, faiss_flat):
        """Tek bir vektör eklenir ve boyut artar."""
        vec = np.random.randn(1, 384).astype('float32')
        faiss_flat.add_embeddings(vec, [42])

        assert faiss_flat.get_index_size() == 1

    def test_add_multiple_vectors(self, faiss_flat):
        """Birden fazla vektör eklenir."""
        vecs = np.random.randn(5, 384).astype('float32')
        faiss_flat.add_embeddings(vecs, [1, 2, 3, 4, 5])

        assert faiss_flat.get_index_size() == 5

    def test_search_returns_correct_id(self, faiss_flat):
        """Arama, eklenen vektörün item_id'sini döner."""
        vec = np.random.randn(1, 384).astype('float32')
        faiss_flat.add_embeddings(vec, [999])

        results = faiss_flat.search(vec, k=1)

        assert len(results) > 0
        assert results[0][0] == 999

    def test_search_returns_distance(self, faiss_flat):
        """Arama sonuçları (item_id, distance) tuple'ı döner."""
        vec = np.random.randn(1, 384).astype('float32')
        faiss_flat.add_embeddings(vec, [1])

        results = faiss_flat.search(vec, k=1)

        item_id, distance = results[0]
        assert isinstance(item_id, int)
        assert isinstance(distance, float)

    def test_search_empty_index(self, faiss_flat):
        """Boş index'te arama boş liste döner."""
        query = np.random.randn(384).astype('float32')
        results = faiss_flat.search(query, k=5)

        assert results == []

    def test_search_k_limits_results(self, faiss_flat):
        """k parametresi sonuç sayısını sınırlar."""
        vecs = np.random.randn(10, 384).astype('float32')
        faiss_flat.add_embeddings(vecs, list(range(10)))

        query = np.random.randn(384).astype('float32')
        results = faiss_flat.search(query, k=3)

        assert len(results) <= 3

    def test_1d_vector_handled(self, faiss_flat):
        """1D vektör (384,) otomatik olarak 2D'ye dönüştürülür."""
        vec = np.random.randn(384).astype('float32')
        faiss_flat.add_embeddings(vec, [1])

        assert faiss_flat.get_index_size() == 1

    def test_nearest_neighbor_correct(self, faiss_flat):
        """En yakın komşu doğru bulunur."""
        v1 = np.ones((1, 384), dtype='float32') * 1.0
        v2 = np.ones((1, 384), dtype='float32') * 2.0
        v3 = np.ones((1, 384), dtype='float32') * 3.0

        faiss_flat.add_embeddings(v1, [10])
        faiss_flat.add_embeddings(v2, [20])
        faiss_flat.add_embeddings(v3, [30])

        results = faiss_flat.search(v1, k=1)

        assert results[0][0] == 10


class TestSaveLoad:
    """Kaydetme/yükleme testleri."""

    def test_save_and_load(self, temp_dir):
        """Kaydedilen index tekrar yüklenebilir."""
        index_path = str(temp_dir / "persist.faiss")

        fm1 = FaissManager(index_path=index_path, dimension=384)
        vec = np.random.randn(1, 384).astype('float32')
        fm1.add_embeddings(vec, [42])

        fm2 = FaissManager(index_path=index_path, dimension=384)

        assert fm2.get_index_size() == 1
        results = fm2.search(vec, k=1)
        assert results[0][0] == 42

    def test_id_mapping_persisted(self, temp_dir):
        """item_id eşleşmeleri de kaydedilir."""
        index_path = str(temp_dir / "id_map.faiss")

        fm1 = FaissManager(index_path=index_path, dimension=384)
        vecs = np.random.randn(3, 384).astype('float32')
        fm1.add_embeddings(vecs, [100, 200, 300])

        fm2 = FaissManager(index_path=index_path, dimension=384)
        assert 100 in fm2.id_to_item_id.values()
        assert 200 in fm2.id_to_item_id.values()
        assert 300 in fm2.id_to_item_id.values()
