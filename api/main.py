"""
FastAPI uygulama giris noktasi.
CORS yapilandirmasi, router kaydi ve uvicorn baslatma.
"""

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Proje kokunu Python path'ine ekle (api/ klasorunun bir ust dizini)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config, setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama baslatma ve kapatma islemleri."""
    setup_logging()
    logger.info("Memory Manager API baslatiliyor...")

    # DB tablolarini olustur (yoksa)
    from database.schema import DatabaseSchema
    db = DatabaseSchema()
    db.create_all_tables()

    logger.info(f"API hazir: http://{Config.API_HOST}:{Config.API_PORT}")
    yield
    logger.info("API kapatiliyor...")


def setup_cors(app: FastAPI) -> None:
    """CORS middleware yapilandirmasi — Flutter desktop client icin gerekli."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config.API_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def register_routers(app: FastAPI) -> None:
    """Tum router'lari uygulamaya kaydeder."""
    from api.routers.import_router import router as import_router
    from api.routers.gallery_router import router as gallery_router
    from api.routers.search_router import router as search_router
    from api.routers.privacy_router import router as privacy_router
    from api.routers.events_router import router as events_router
    from api.routers.flashcard_router import router as flashcard_router
    from api.routers.timeline_router import router as timeline_router
    from api.routers.settings_router import router as settings_router

    app.include_router(import_router)
    app.include_router(gallery_router)
    app.include_router(search_router)
    app.include_router(privacy_router)
    app.include_router(events_router)
    app.include_router(flashcard_router)
    app.include_router(timeline_router)
    app.include_router(settings_router)


def create_app() -> FastAPI:
    """FastAPI uygulamasini olusturur ve yapilandirir."""
    application = FastAPI(
        title="Memory Manager API",
        description="Kisisel Hafiza Yoneticisi — Privacy-First AI Desktop App",
        version="1.0.0",
        lifespan=lifespan,
    )
    setup_cors(application)

    # Baglanti testi icin basit health-check endpoint
    @application.get("/api/health")
    async def health_check():
        return {"status": "ok", "message": "Memory Manager API calisiyor"}

    register_routers(application)
    return application


def start_server() -> None:
    """Uvicorn sunucusunu baslatir."""
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,
    )


# Uygulama instance'i — uvicorn "api.main:app" ile bunu bulur
app = create_app()


if __name__ == "__main__":
    start_server()
