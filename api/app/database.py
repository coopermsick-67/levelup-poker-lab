import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

_url = settings.DATABASE_URL
_connect_args: dict = {}

if _url.startswith("sqlite"):
    if "libsql" not in _url:
        _connect_args["check_same_thread"] = False

    # On Vercel serverless, the filesystem is read-only except /tmp.
    # Rewrite relative SQLite paths to /tmp for production.
    if os.environ.get("ENVIRONMENT") == "production" or os.environ.get("VERCEL"):
        if _url.startswith("sqlite:///./"):
            _url = _url.replace("sqlite:///.", "sqlite:///tmp")
        elif _url.startswith("sqlite:///"):
            # Absolute path — replace with /tmp
            _url = "sqlite:///tmp/poker_lab.db"

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
