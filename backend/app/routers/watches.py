from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models, schemas
from ..agent.exa_client import ExaClient
from ..agent.ingest import ingest_hit
from ..agent.llm_client import LLMClient
from ..agent.organize import organize_document
from ..agent.pipeline import persist_custom_watch, sync_system_watches
from ..config import get_settings
from ..database import get_db

router = APIRouter(prefix="/api/watches", tags=["watches"])


class WatchPatch(BaseModel):
    is_active: Optional[bool] = None
    label: Optional[str] = None


@router.get("", response_model=list[schemas.WatchOut])
def list_watches(db: Session = Depends(get_db)):
    sync_system_watches(db)
    return db.query(models.WatchQuery).order_by(models.WatchQuery.is_system.desc(), models.WatchQuery.id).all()


@router.post("", response_model=schemas.WatchOut)
def create_watch(payload: schemas.WatchCreate, db: Session = Depends(get_db)):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="查询词不能为空")
    watch = persist_custom_watch(
        db,
        query=payload.query.strip(),
        label=payload.label.strip() or payload.query[:80],
        country_code=payload.country_code,
        stream=payload.stream or "custom",
    )
    return watch


@router.patch("/{watch_id}", response_model=schemas.WatchOut)
def patch_watch(watch_id: int, payload: WatchPatch, db: Session = Depends(get_db)):
    watch = db.get(models.WatchQuery, watch_id)
    if not watch:
        raise HTTPException(status_code=404, detail="监控网不存在")
    if payload.is_active is not None:
        watch.is_active = payload.is_active
    if payload.label:
        watch.label = payload.label
    db.commit()
    db.refresh(watch)
    return watch


@router.delete("/{watch_id}")
def delete_watch(watch_id: int, db: Session = Depends(get_db)):
    watch = db.get(models.WatchQuery, watch_id)
    if not watch:
        raise HTTPException(status_code=404, detail="监控网不存在")
    if watch.is_system:
        raise HTTPException(status_code=400, detail="系统预置的网不能删除，只能停用")
    db.delete(watch)
    db.commit()
    return {"ok": True}


@router.post("/{watch_id}/run")
def run_one_watch(watch_id: int, db: Session = Depends(get_db)):
    """立刻用这一张网去搜并把原文入库（需要 Exa）。"""
    settings = get_settings()
    watch = db.get(models.WatchQuery, watch_id)
    if not watch:
        raise HTTPException(status_code=404, detail="监控网不存在")
    if not settings.can_collect:
        raise HTTPException(status_code=501, detail="尚未配置 EXA_API_KEY，无法真实撒网。演示语料已在情报库里，请先搜索。")
    exa = ExaClient()
    llm = LLMClient() if settings.has_llm else None
    domains = [p.strip() for p in (watch.include_domains or "").split(",") if p.strip()] or None
    hits = exa.search(watch.query, num_results=settings.search_results_per_watch, include_domains=domains, category=watch.exa_category or None)
    created = 0
    docs = []
    for hit in hits:
        doc, is_new = ingest_hit(
            db,
            hit,
            stream=watch.stream,
            query=watch.query,
            country_code=watch.country_code,
            is_demo=False,
        )
        organize_document(db, doc, llm)
        if is_new:
            created += 1
        docs.append({"id": doc.id, "title": doc.title, "url": doc.url, "created": is_new})
    db.commit()
    return {"created": created, "total_hits": len(hits), "documents": docs}
