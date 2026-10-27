"""FastAPI application factory.

Import-time table creation keeps the app self-contained for serverless
lifespan handlers (which Vercel does not invoke). The frontend SPA is served
from app/static when the directory exists (it is bundled by includeFiles on
Vercel), with a guard so a missing directory can never crash the import.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from app.config import get_settings
from app.database import Base, engine
from app.limiter import limiter
from app.routers import auth, conversations, documents, summarize

logger = logging.getLogger("sage")
settings = get_settings()

STATIC_DIR = Path(__file__).resolve().parent / "static"


def _init_db() -> None:
    Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()
    yield


def create_app() -> FastAPI:
    _init_db()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(documents.router)
    app.include_router(conversations.router)
    app.include_router(summarize.router)

    @app.get("/api/health", tags=["meta"])
    def health():
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }

    # Serve the SPA last, so API routes always win. The guard prevents the
    # exact crash that broke earlier days: StaticFiles on a missing directory
    # raises at import time and turns every /api/* call into a 500.
    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    @app.exception_handler(404)
    async def _not_found(request, exc):
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    return app


app = create_app()
