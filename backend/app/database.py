import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

_url = settings.DATABASE_URL
_connect_args: dict = {}

if _url.startswith("sqlite"):
    if "libsql" not in _url:
        _connect_args["check_same_thread"] = False

    # On Vercel serverless, use in-memory SQLite since /tmp may not be writable
    # across invocations. For Turso (libsql), use the provided URL as-is.
    if os.environ.get("VERCEL") or os.environ.get("ENVIRONMENT") == "production":
        if "libsql" not in _url:
            _url = "sqlite:///:memory:"

engine = create_engine(_url, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
