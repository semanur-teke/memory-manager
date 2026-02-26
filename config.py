"""
Merkezi Yapılandırma (Centralized Configuration)

Tüm sabit değerler ve logging ayarları bu dosyada toplanmıştır.
Modüller bu değerleri import ederek kullanır, constructor parametreleri
ile override edilebilir (geriye uyumluluk).

Kullanım:
    from config import Config
    model = Config.CLIP_MODEL_NAME

Logging başlatma (uygulama giriş noktasında bir kez çağrılır):
    from config import setup_logging
    setup_logging()
"""

import logging
import sys
from pathlib import Path

# =====================================================================
# PROJE KÖK DİZİNİ
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Tüm yapılandırma sabitleri."""

    # -----------------------------------------------------------------
    # Model İsimleri
    # -----------------------------------------------------------------
    SBERT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    CLIP_IMAGE_MODEL = "clip-ViT-B-32"
    CLIP_TEXT_MODEL = "clip-ViT-B-32-multilingual-v1"
    WHISPER_MODEL_SIZE = "small"

    # -----------------------------------------------------------------
    # Veritabanı
    # -----------------------------------------------------------------
    DATABASE_URL = "sqlite:///./metadata.db"

    # -----------------------------------------------------------------
    # Güvenlik
    # -----------------------------------------------------------------
    SECRET_KEY_PATH = "secret.key"
    PRIVACY_AUDIT_LOG = "privacy_audit.log"

    # -----------------------------------------------------------------
    # Ağ (Network)
    # -----------------------------------------------------------------
    GEOCODER_USER_AGENT = "MemoryManager_App_v1"

    # -----------------------------------------------------------------
    # Desteklenen Dosya Formatları
    # -----------------------------------------------------------------
    SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".heic"}
    SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".mp4", ".aac", ".wma"}

    # -----------------------------------------------------------------
    # Sayısal Parametreler
    # -----------------------------------------------------------------
    IMAGE_MAX_SIZE = 2000
    SBERT_BATCH_SIZE = 32
    CLIP_BATCH_SIZE = 32
    HNSW_NEIGHBORS = 32
    DEFAULT_SEARCH_RADIUS_KM = 5.0
    CITY_SEARCH_RADIUS_KM = 20.0
    DEFAULT_SEARCH_K = 10

    # -----------------------------------------------------------------
    # API Ayarlari
    # -----------------------------------------------------------------
    API_HOST = "127.0.0.1"
    API_PORT = 8000
    API_CORS_ORIGINS = ["http://localhost:*"]
    THUMBNAIL_SIZE = (200, 200)
    THUMBNAIL_QUALITY = 80
    THUMBNAIL_CACHE_MAX_SIZE = 500
    GALLERY_PAGE_SIZE = 40
    SEARCH_RESULTS_PAGE_SIZE = 20

    # -----------------------------------------------------------------
    # Logging
    # -----------------------------------------------------------------
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """
    Merkezi logging yapılandırması. Uygulama başlatılırken bir kez çağrılır.

    - Konsola (stderr) tüm modül loglarını yazar.
    - privacy_audit.log dosyasına güvenlik loglarını yazar.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(Config.LOG_LEVEL)

    # Mevcut handler'ları temizle (tekrar çağrılırsa duplikasyon olmasın)
    root_logger.handlers.clear()

    # --- Konsol Handler ---
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(Config.LOG_LEVEL)
    console_handler.setFormatter(
        logging.Formatter(Config.LOG_FORMAT, datefmt=Config.LOG_DATE_FORMAT)
    )
    root_logger.addHandler(console_handler)

    # --- Güvenlik Denetim Logu (Privacy Audit) ---
    audit_handler = logging.FileHandler(Config.PRIVACY_AUDIT_LOG)
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    # Sadece security.* logger'larına bağla
    security_logger = logging.getLogger("security")
    security_logger.addHandler(audit_handler)
