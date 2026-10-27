"""Database engine, session factory, and declarative base.

SQLite for development and tests; PostgreSQL when DATABASE_URL points at one.
On Vercel the filesystem is read-only except /tmp, so a file-based SQLite URL
is transparently redirected there.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()


def _resolve_database_url() -> str:
    url = settings.database_url
    if url.startswith("sqlite:///") and os.getenv("VERCEL"):
        path = url.replace("sqlite:///", "")
        if path and not path.startswith("/tmp"):
            filename = os.path.basename(path) or "sage.db"
            return f"sqlite:////tmp/{filename}"
    return url


_resolved = _resolve_database_url()
_connect_args = {"check_same_thread": False} if _resolved.startswith("sqlite") else {}

engine = create_engine(_resolved, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
