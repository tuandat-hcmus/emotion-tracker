from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.conversations import router as conversations_router
from app.api.auth import router as auth_router
from app.api.checkins import router as checkins_router
from app.api.demo import router as demo_router
from app.api.dev import router as dev_router
from app.api.health import router as health_router
from app.api.me import router as me_router
from app.api.resources import router as resources_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.errors import http_exception_handler, validation_exception_handler
from app.models import (
    ConversationSession,
    ConversationTurn,
    JournalEntry,
    ProcessingAttempt,
    TreeState,
    TreeStateEvent,
    User,
    UserPreference,
    WrapupSnapshot,
)

settings = get_settings()

def initialize_database() -> None:
    ConversationSession.__table__
    ConversationTurn.__table__
    JournalEntry.__table__
    ProcessingAttempt.__table__
    TreeState.__table__
    TreeStateEvent.__table__
    User.__table__
    UserPreference.__table__
    WrapupSnapshot.__table__


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


def configure_cors(app: FastAPI, app_settings) -> None:
    if hasattr(app_settings, "cors_origins"):
        cors_origins = app_settings.cors_origins()
    else:
        raw_origins = getattr(app_settings, "backend_cors_origins", "")
        cors_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    if not cors_origins:
        return
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    configure_cors(app, settings)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    @app.get("/")
    def health_check() -> dict[str, str]:
        return {
            "app": settings.app_name,
            "status": "ok",
            "message": "Backend is running",
        }

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(checkins_router)
    app.include_router(conversations_router)
    app.include_router(demo_router)
    app.include_router(dev_router)
    app.include_router(me_router)
    app.include_router(resources_router)
    app.include_router(users_router)
    return app


app = create_app()
