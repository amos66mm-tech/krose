"""把搜索命中归档成 Document。命中即入库，抽取失败也不丢原文。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .. import models
from ..fts import fts_upsert
from .exa_client import SearchHit
from .textutil import canonicalize_url, content_hash, domain_of, source_kind_of


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def ingest_hit(
    db: Session,
    hit: SearchHit,
    *,
    stream: str,
    query: str,
    country_code: Optional[str] = None,
    run_id: Optional[int] = None,
    is_demo: bool = False,
    source_kind: Optional[str] = None,
) -> tuple[models.Document, bool]:
    """
    按 canonical URL 去重。同一 URL 再次出现只更新 last_seen / hit_count，
    若新文本明显更长则刷新 full_text。
    """
    url = hit.url or ""
    canonical = canonicalize_url(url) or url or f"demo://{content_hash(hit.title + hit.text)[:16]}"
    existing = db.query(models.Document).filter(models.Document.canonical_url == canonical).first()
    body = (hit.text or hit.summary or "").strip()
    if existing:
        existing.last_seen_at = datetime.now(timezone.utc)
        existing.hit_count = (existing.hit_count or 1) + 1
        if body and len(body) > len(existing.full_text or ""):
            existing.full_text = body
            existing.snippet = (hit.summary or body)[:500]
            existing.content_hash = content_hash(body)
            fts_upsert(db, existing)
        return existing, False

    doc = models.Document(
        url=url or canonical,
        canonical_url=canonical,
        title=(hit.title or "")[:512],
        snippet=(hit.summary or body)[:800],
        full_text=body,
        source_domain=domain_of(url),
        source_kind=source_kind or source_kind_of(url),
        stream=stream,
        country_code=country_code,
        query=query,
        author=hit.author or "",
        content_hash=content_hash(body or hit.title),
        published_at=_parse_date(hit.published_date),
        collection_run_id=run_id,
        is_demo=is_demo,
    )
    db.add(doc)
    db.flush()
    fts_upsert(db, doc)
    return doc, True
