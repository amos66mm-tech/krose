"""SQLite FTS5 index over the intelligence corpus."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from . import models

FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title,
    snippet,
    full_text,
    summary_zh
);
"""


def ensure_fts(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as conn:
        conn.execute(text(FTS_DDL))


def fts_upsert(db: Session, doc: models.Document) -> None:
    if db.get_bind().dialect.name != "sqlite" or not doc.id:
        return
    db.execute(text("DELETE FROM documents_fts WHERE rowid = :id"), {"id": doc.id})
    db.execute(
        text(
            """
            INSERT INTO documents_fts(rowid, title, snippet, full_text, summary_zh)
            VALUES (:id, :title, :snippet, :full_text, :summary_zh)
            """
        ),
        {
            "id": doc.id,
            "title": doc.title or "",
            "snippet": doc.snippet or "",
            "full_text": doc.full_text or "",
            "summary_zh": doc.summary_zh or "",
        },
    )


def rebuild_fts(db: Session) -> None:
    if db.get_bind().dialect.name != "sqlite":
        return
    db.execute(text("DELETE FROM documents_fts"))
    for doc in db.query(models.Document).all():
        fts_upsert(db, doc)
