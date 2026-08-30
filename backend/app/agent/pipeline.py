"""情报采集流水线：撒网搜索 → 原文全部归档 → 整理（实体/标签/摘要）→ 能抽到的价格再写入派生表。

真实采集从不写入模拟文档。没有 Exa Key 时只保证演示语料已就位。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .. import models
from ..config import get_settings
from . import streams
from .demo_corpus import seed_demo_corpus
from .exa_client import ExaClient
from .ingest import ingest_hit
from .llm_client import LLMClient
from .organize import organize_document, organize_pending
from .textutil import slugify

logger = logging.getLogger(__name__)


class CollectionStats:
    def __init__(self) -> None:
        self.targets_processed = 0
        self.records_created = 0
        self.errors: list[str] = []


def _start_run(db: Session, scope: str, mode: str) -> models.CollectionRun:
    run = models.CollectionRun(scope=scope, mode=mode, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _finish_run(db: Session, run: models.CollectionRun, stats: CollectionStats, status: str = "success") -> None:
    run.status = status
    run.targets_processed = stats.targets_processed
    run.records_created = stats.records_created
    run.error_message = "\n".join(stats.errors[:20])
    run.finished_at = datetime.now(timezone.utc)
    db.add(run)
    db.commit()


def sync_system_watches(db: Session) -> None:
    """把宽网 + 已知平台监控写成 WatchQuery（幂等）。用户自己加的网不会被覆盖。"""
    specs = list(streams.system_stream_specs())
    platforms = db.query(models.Platform).filter(models.Platform.is_active.is_(True)).all()
    for p in platforms:
        specs.append(streams.platform_watch_spec(p))

    existing = {w.key: w for w in db.query(models.WatchQuery).filter(models.WatchQuery.is_system.is_(True)).all()}
    seen_keys: set[str] = set()
    for spec in specs:
        seen_keys.add(spec.key)
        row = existing.get(spec.key)
        if row is None:
            db.add(
                models.WatchQuery(
                    key=spec.key,
                    label=spec.label,
                    query=spec.query,
                    stream=spec.stream,
                    country_code=spec.country_code,
                    include_domains=spec.include_domains,
                    exa_category=spec.exa_category,
                    is_system=True,
                    notes=spec.notes,
                )
            )
        else:
            row.label = spec.label
            row.query = spec.query
            row.stream = spec.stream
            row.country_code = spec.country_code
            row.include_domains = spec.include_domains
            row.exa_category = spec.exa_category
            row.notes = spec.notes
    db.commit()


def _active_watches(
    db: Session,
    *,
    country_code: Optional[str],
    stream: Optional[str],
) -> list[models.WatchQuery]:
    q = db.query(models.WatchQuery).filter(models.WatchQuery.is_active.is_(True))
    if country_code:
        q = q.filter(
            (models.WatchQuery.country_code == country_code.upper()) | (models.WatchQuery.country_code.is_(None))
        )
    if stream and stream not in {"all", "intel"}:
        q = q.filter(models.WatchQuery.stream == stream)
    return q.order_by(models.WatchQuery.id).all()


def _domains(raw: str) -> list[str] | None:
    parts = [p.strip() for p in (raw or "").replace("\n", ",").split(",") if p.strip()]
    return parts or None


def run_intel_collection(
    db: Session,
    *,
    country_code: Optional[str] = None,
    stream: Optional[str] = None,
) -> models.CollectionRun:
    settings = get_settings()
    live = settings.can_collect
    scope = stream or "intel"
    run = _start_run(db, scope, "live" if live else "demo")
    stats = CollectionStats()
    sync_system_watches(db)

    try:
        if not live:
            if settings.allow_mock_fallback:
                seed_demo_corpus(db)
            n = organize_pending(db, None)
            stats.targets_processed = db.query(models.WatchQuery).filter(models.WatchQuery.is_active.is_(True)).count()
            stats.records_created = n
            _finish_run(db, run, stats, "success")
            return run

        exa = ExaClient()
        llm = LLMClient() if settings.has_llm else None
        watches = _active_watches(db, country_code=country_code, stream=stream)
        per = settings.search_results_per_watch

        for watch in watches:
            stats.targets_processed += 1
            try:
                hits = exa.search(
                    watch.query,
                    num_results=per,
                    include_domains=_domains(watch.include_domains),
                    category=watch.exa_category or None,
                )
                for hit in hits:
                    doc, created = ingest_hit(
                        db,
                        hit,
                        stream=watch.stream,
                        query=watch.query,
                        country_code=watch.country_code or country_code,
                        run_id=run.id,
                        is_demo=False,
                    )
                    if created:
                        stats.records_created += 1
                    organize_document(db, doc, llm)
                db.commit()
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                stats.errors.append(f"{watch.key}: {exc}")
                logger.exception("采集失败 %s", watch.key)

        _finish_run(db, run, stats, "success" if not stats.errors else "success")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        stats.errors.append(str(exc))
        _finish_run(db, run, stats, "failed")
        raise
    return run


def run_price_collection(db: Session, platform_ids: Optional[list[int]] = None) -> models.CollectionRun:
    country = None
    if platform_ids:
        p = db.get(models.Platform, platform_ids[0])
        country = p.country.code if p and p.country else None
    return run_intel_collection(db, country_code=country, stream="rates")


def run_activity_collection(db: Session, platform_ids: Optional[list[int]] = None) -> models.CollectionRun:
    country = None
    if platform_ids:
        p = db.get(models.Platform, platform_ids[0])
        country = p.country.code if p and p.country else None
    return run_intel_collection(db, country_code=country, stream="platform_watch")


def run_social_collection(db: Session, platform_ids: Optional[list[int]] = None) -> models.CollectionRun:
    country = None
    if platform_ids:
        p = db.get(models.Platform, platform_ids[0])
        country = p.country.code if p and p.country else None
    return run_intel_collection(db, country_code=country, stream="community")


def run_all_collections(db: Session, platform_ids: Optional[list[int]] = None) -> list[models.CollectionRun]:
    country = None
    if platform_ids:
        p = db.get(models.Platform, platform_ids[0])
        country = p.country.code if p and p.country else None
    return [run_intel_collection(db, country_code=country, stream="intel")]


def persist_custom_watch(
    db: Session,
    *,
    query: str,
    label: str,
    country_code: Optional[str] = None,
    stream: str = "custom",
) -> models.WatchQuery:
    key = f"custom:{slugify(label)}:{slugify(query)[:40]}"
    existing = db.query(models.WatchQuery).filter(models.WatchQuery.key == key).first()
    if existing:
        existing.query = query
        existing.label = label
        existing.is_active = True
        db.commit()
        return existing
    watch = models.WatchQuery(
        key=key,
        label=label or query[:80],
        query=query,
        stream=stream,
        country_code=country_code.upper() if country_code else None,
        is_system=False,
    )
    db.add(watch)
    db.commit()
    db.refresh(watch)
    return watch
