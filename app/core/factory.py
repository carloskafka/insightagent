from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.core.rate_limit import RateLimitMiddleware
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.health import router as health_router
from app.routers.rag import router as rag_router
from app.routers.tools import router as tools_router
from app.services.file_service import ensure_upload_dir


def create_app() -> FastAPI:
    app = FastAPI(title="Chatbot API", version="1.0.0")
    configure_middleware(app)
    register_routers(app)
    initialize_app()
    return app


def configure_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)


def register_routers(app: FastAPI) -> None:
    for router in (health_router, auth_router, chat_router, tools_router, rag_router):
        app.include_router(router)


def initialize_app() -> None:
    ensure_upload_dir()
    init_db()
