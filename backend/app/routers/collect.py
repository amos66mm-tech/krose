from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..agent.exa_client import ExaClient
from ..agent.ingest import ingest_hit
from ..agent.llm_client import LLMClient
from ..agent.organize import organize_document
from ..agent.pipeline import persist_custom_watch, run_intel_collection
from ..config import get_settings
from ..database import get_db

router = APIRouter(prefix="/api/collect", tags=["collect"])

Scope = Literal["intel", "rates", "community", "news_risk", "competitor_discovery", "platform_watch", "market_scan", "all", "price", "activity", "social"]

SCOPE_MAP = {
    "price": "rates",
    "activity": "platform_watch",
    "social": "community",
    "all": "intel",
}


@router.post("/run", response_model=list[schemas.CollectionRunOut])
def trigger_collection(
    scope: Scope = Query(default="intel"),
    country_code: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    stream = SCOPE_MAP.get(scope, scope)
    return [run_intel_collection(db, country_code=country_code, stream=stream)]


@router.get("/runs", response_model=list[schemas.CollectionRunOut])
def list_runs(limit: int = Query(default=20, ge=1, le=200), db: Session = Depends(get_db)):
    return db.query(models.CollectionRun).order_by(models.CollectionRun.started_at.desc()).limit(limit).all()


@router.post("/custom")
def custom_watch(payload: schemas.WatchCreate, db: Session = Depends(get_db)):
    """
    即时撒一张网：搜索命中全部入库并整理。
    save=true（默认）时同时变成持久监控，下次全量采集还会再跑。
    """
    settings = get_settings()
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="查询词不能为空")

    watch = None
    watch_out = None
    if payload.save:
        watch = persist_custom_watch(
            db,
            query=payload.query.strip(),
            label=payload.label.strip() or payload.query[:80],
            country_code=payload.country_code,
            stream=payload.stream or "custom",
        )
        watch_out = schemas.WatchOut.model_validate(watch)

    if not settings.can_collect:
        return {
            "watch": watch_out,
            "mode": "demo",
            "detail": "未配置 EXA_API_KEY。这张网已保存，配置 Key 后的下一次采集会真正去搜。请先在情报库里搜索现有原文。",
            "documents": [],
        }

    exa = ExaClient()
    llm = LLMClient() if settings.has_llm else None
    hits = exa.search(payload.query.strip(), num_results=payload.num_results or settings.search_results_per_watch)
    documents = []
    for hit in hits:
        doc, created = ingest_hit(
            db,
            hit,
            stream=(watch.stream if watch else "custom"),
            query=payload.query.strip(),
            country_code=payload.country_code,
            is_demo=False,
        )
        organize_document(db, doc, llm)
        documents.append(
            {
                "id": doc.id,
                "title": doc.title,
                "url": doc.url,
                "summary_zh": doc.summary_zh,
                "doc_type": doc.doc_type,
                "created": created,
            }
        )
    db.commit()
    return {"watch": watch_out, "mode": "live", "documents": documents}
