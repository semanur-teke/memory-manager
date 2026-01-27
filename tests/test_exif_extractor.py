import os
import sys
import pytest
from pathlib import Path

# --- YOL AYARI ---
# Test klasöründen src klasörüne erişmek için kök dizini sys.path'e ekliyoruz.
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.ingestion.exif_extractor import EXIFExtractor

# --- FIXTURES (Ön Hazırlık) ---
@pytest.fixture
def extractor():
    """Her testten önce extractor nesnesi oluşturur."""
    return EXIFExtractor()

@pytest.fixture
def test_image_path():
    """Senin kullandığın gerçek fotoğrafın yolu."""
    return Path(r"C:\Users\sema\Desktop\memory-manager\SAM_0307~2.JPG")

# --- TEST SENARYOLARI ---

def test_metadata_extraction_type(extractor, test_image_path):
    """Metadatanın bir sözlük (dict) olarak döndüğünü doğrula."""
    if not test_image_path.exists():
        pytest.skip(f"Test dosyası bulunamadı: {test_image_path}")
    
    metadata = extractor.extract_metadata(test_image_path)
    assert isinstance(metadata, dict), "Metadata bir Python sözlüğü olmalı!"

def test_metadata_contains_basic_info(extractor, test_image_path):
    """En azından dosya adı veya tarih gibi temel bilgilerin çekildiğini kontrol et."""
    if not test_image_path.exists():
        pytest.skip("Test dosyası yok, atlanıyor.")
        
    metadata = extractor.extract_metadata(test_image_path)
    # Fotoğrafta EXIF olmasa bile fonksiyonun en azından dosya yolunu döndürdüğünü varsayıyoruz
    assert len(metadata) > 0, "Metadata boş olmamalı!"

def test_invalid_file_path(extractor):
    """Var olmayan bir dosya verildiğinde sistemin hata sözlüğü döndürdüğünü doğrula."""
    fake_path = Path("olmayan_foto.jpg")
    metadata = extractor.extract_metadata(fake_path)
    
    # Beklentimizi yeni kod yapımıza göre güncelliyoruz:
    assert isinstance(metadata, dict)
    assert "error" in metadata
    assert metadata["error"] == "File not found"