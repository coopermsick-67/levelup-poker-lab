from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

_url = settings.DATABASE_URL
_connect_args: dict = {}

if _url.startswith("sqlite"):
    # Local SQLite needs check_same_thread=False for async contexts
    # Turso (libsql) does not
    if "libsql" not in _url:
        _connect_args["check_same_thread"] = False

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
