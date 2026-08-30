from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models, schemas
from ..agent import targets as target_builders
from ..agent.exa_client import ExaClient
from ..agent.extract_schemas import GenericExtraction
from ..agent.llm_client import LLMClient
from ..agent.pipeline import run_activity_collection, run_all_collections, run_price_collection, run_social_collection
from ..config import get_settings
from ..database import get_db

router = APIRouter(prefix="/api/collect", tags=["collect"])

Scope = Literal["price", "activity", "social", "all"]


@router.post("/run", response_model=list[schemas.CollectionRunOut])
def trigger_collection(
    scope: Scope = Query(default="all"),
    country_code: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """手动触发一次采集，便于在面板上按需刷新数据或做演示。"""
    platform_ids = None
    if country_code:
        platform_ids = [
            p.id
            for p in db.query(models.Platform)
            .join(models.Country)
            .filter(models.Country.code == country_code.upper())
            .all()
        ]
        if not platform_ids:
            raise HTTPException(status_code=404, detail="未找到该国家/地区对应的平台")

    if scope == "price":
        return [run_price_collection(db, platform_ids)]
    if scope == "activity":
        return [run_activity_collection(db, platform_ids)]
    if scope == "social":
        return [run_social_collection(db, platform_ids)]
    return run_all_collections(db, platform_ids)


@router.get("/runs", response_model=list[schemas.CollectionRunOut])
def list_runs(limit: int = Query(default=20, ge=1, le=200), db: Session = Depends(get_db)):
    return db.query(models.CollectionRun).order_by(models.CollectionRun.started_at.desc()).limit(limit).all()


class CustomWatchRequest(BaseModel):
    query: str
    label: str = "自定义监控目标"
    num_results: int = 3


class CustomWatchResult(BaseModel):
    url: str
    title: str
    extraction: Optional[GenericExtraction]


@router.post("/custom", response_model=list[CustomWatchResult])
def custom_watch(payload: CustomWatchRequest):
    """
    “万物皆可爬”的即时探针接口：给一个任意关键词，立刻做一次 Exa 搜索 + LLM 结构化摘要。
    未配置 API Key 时返回 501，提示用户先在 Secrets 中配置 EXA_API_KEY / LLM_API_KEY。
    这是留给论坛未来扩展（例如追踪竞品论坛话题、监控汇率新闻等）的通用入口。
    """
    settings = get_settings()
    if not settings.is_live_mode:
        raise HTTPException(
            status_code=501,
            detail="尚未配置 EXA_API_KEY 与 LLM_API_KEY，无法执行真实抓取。请先在 Cursor Dashboard -> Secrets 中配置。",
        )
    exa = ExaClient()
    llm = LLMClient()
    target = target_builders.build_custom_target(payload.query, payload.label)
    hits = exa.search(target.query, num_results=payload.num_results)
    results: list[CustomWatchResult] = []
    for hit in hits:
        extraction = llm.extract(
            GenericExtraction,
            context_label=target.context_label,
            raw_text=hit.summary or hit.text,
        )
        results.append(CustomWatchResult(url=hit.url, title=hit.title, extraction=extraction))
    return results
