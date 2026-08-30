from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

engine = None
SessionLocal = None


class Base(DeclarativeBase):
    pass


def _make_engine(database_url: str):
    if database_url.startswith("sqlite"):
        db_path = database_url.split("///")[-1]
        if db_path not in {":memory:", ""} and not db_path.startswith("file:"):
            parent = os.path.dirname(db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}
    return create_engine(database_url, connect_args=connect_args)


def configure_database(database_url: str | None = None) -> None:
    """(Re)bind the global engine. Used at import time and by tests."""
    global engine, SessionLocal
    if engine is not None:
        engine.dispose()
    url = database_url or get_settings().database_url
    engine = _make_engine(url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    if url.startswith("sqlite"):
        with engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.execute(text("PRAGMA journal_mode=WAL"))


configure_database()


def init_db() -> None:
    from . import fts, models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    fts.ensure_fts(engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
