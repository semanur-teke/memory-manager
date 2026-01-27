import pytest
import numpy as np
from pathlib import Path
from src.embedding.sbert_embedder import SBERTEmbedder
from src.embedding.clip_embedder import CLIPEmbedder
from src.embedding.faiss_manager import FaissManager

# --- 1. SBERT TESTİ ---
def test_sbert_dimensions():
    """SBERT'in 384 boyutlu ve float32 tipinde vektör ürettiğini doğrular."""
    embedder = SBERTEmbedder()
    text = "Anlamsal arama testi."
    vector = embedder.encode_text(text)
    
    assert vector is not None
    assert vector.shape == (384,)
    assert vector.dtype == np.float32

# --- 2. CLIP TESTİ ---
def test_clip_dimensions():
    """CLIP'in 512 boyutlu görsel vektör ürettiğini doğrular."""
    test_image = Path(r"C:\Users\sema\Desktop\memory-manager\IMG-20260123-WA0024.jpeg")
    
    if not test_image.exists():
        pytest.skip("test_image.jpg bulunamadığı için bu test atlandı.")
    
    embedder = CLIPEmbedder()
    vector = embedder.encode_image(test_image)
    
    assert vector is not None
    assert vector.shape == (512,)
    assert vector.dtype == np.float32

# --- 3. FAISS TESTİ ---
def test_faiss_indexing():
    """FAISS'in veri kaydedip doğru ID ile geri döndürdüğünü doğrular."""
    # Test için geçici bir index
    fm = FaissManager(index_path="database/test_index.faiss", dimension=384)
    
    # Sahte bir vektör oluştur (384 boyutlu)
    fake_vector = np.random.random((1, 384)).astype('float32')
    item_id = [999]
    
    fm.add_embeddings(fake_vector, item_id)
    results = fm.search(fake_vector, k=1)
    
    assert len(results) > 0
    assert results[0][0] == 999  # Kaydettiğimiz ID'yi geri almalıyız

# --- 4. MULTIMODAL FUSION TESTİ (Opsiyonel ama önerilir) ---
def test_fusion_logic():
    """Görsel ve metin vektörlerinin doğru birleştiğini doğrular."""
    from src.embedding.multimodal_fuser import MultimodalFuser
    fuser = MultimodalFuser()
    
    # 512 + 384 = 896 boyutunda bir sonuç bekliyoruz
    v_image = np.zeros(512, dtype='float32')
    v_text = np.zeros(384, dtype='float32')
    
    fused = fuser.fuse(v_image, v_text)
    assert fused.shape == (896,)