from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import get_settings
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/agent-status", response_model=schemas.AgentStatus)
def agent_status(db: Session = Depends(get_db)):
    settings = get_settings()
    return schemas.AgentStatus(
        has_exa=settings.has_exa,
        has_llm=settings.has_llm,
        live_mode=settings.can_collect,
        can_collect=settings.can_collect,
        llm_model=settings.llm_model,
        llm_base_url=settings.llm_base_url,
        collection_interval_minutes=settings.collection_interval_minutes,
        scheduler_enabled=settings.enable_scheduler,
        search_results_per_watch=settings.search_results_per_watch,
        document_count=db.query(models.Document).count(),
        watch_count=db.query(models.WatchQuery).filter(models.WatchQuery.is_active.is_(True)).count(),
    )


@router.get("/summary", response_model=schemas.DashboardSummary)
def summary(
    country_code: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    settings = get_settings()

    platform_q = db.query(models.Platform).filter(models.Platform.is_active.is_(True))
    if country_code:
        platform_q = platform_q.join(models.Country).filter(models.Country.code == country_code.upper())
    platforms = platform_q.all()
    platform_ids = [p.id for p in platforms]
    platform_lookup = {p.id: p for p in platforms}
    card_lookup = {c.id: c for c in db.query(models.GiftCardType).all()}

    now = dt.datetime.now(dt.timezone.utc)
    since_24h = now - dt.timedelta(hours=24)
    since_7d = now - dt.timedelta(days=7)

    price_q = db.query(models.PriceQuote).filter(models.PriceQuote.platform_id.in_(platform_ids)) if platform_ids else db.query(models.PriceQuote).filter(False)
    quotes_24h = price_q.filter(models.PriceQuote.collected_at >= since_24h).all()
    new_24h = [q for q in quotes_24h if q.is_new]

    activity_q = (
        db.query(models.Activity).filter(models.Activity.platform_id.in_(platform_ids))
        if platform_ids
        else db.query(models.Activity).filter(False)
    )
    promotions_7d = activity_q.filter(
        models.Activity.collected_at >= since_7d, models.Activity.activity_type == "promotion"
    ).count()

    social_q = (
        db.query(models.SocialPost).filter(models.SocialPost.platform_id.in_(platform_ids))
        if platform_ids
        else db.query(models.SocialPost).filter(False)
    )
    social_7d = social_q.filter(models.SocialPost.collected_at >= since_7d).count()

    all_quotes = (
        db.query(models.PriceQuote)
        .filter(models.PriceQuote.platform_id.in_(platform_ids))
        .order_by(models.PriceQuote.collected_at.desc())
        .all()
        if platform_ids
        else []
    )
    seen: set[tuple[int, int]] = set()
    latest_by_key: dict[tuple[int, int], models.PriceQuote] = {}
    for q in all_quotes:
        key = (q.platform_id, q.gift_card_type_id)
        if key not in seen:
            seen.add(key)
            latest_by_key[key] = q

    best_rate_per_card_type: dict[int, dict] = {}
    for (platform_id, card_type_id), q in latest_by_key.items():
        card = card_lookup.get(card_type_id)
        platform = platform_lookup.get(platform_id)
        if not card or not platform:
            continue
        current_best = best_rate_per_card_type.get(card_type_id)
        if not current_best or q.rate_percent > current_best["rate_percent"]:
            best_rate_per_card_type[card_type_id] = {
                "gift_card_type": card.name,
                "icon": card.icon,
                "platform": platform.name,
                "rate_percent": q.rate_percent,
                "currency": q.currency,
            }

    movers = sorted(
        (
            {
                "platform": platform_lookup[p_id].name,
                "gift_card_type": card_lookup[c_id].name,
                "change_percent": q.change_percent,
                "rate_percent": q.rate_percent,
                "currency": q.currency,
            }
            for (p_id, c_id), q in latest_by_key.items()
            if p_id in platform_lookup and c_id in card_lookup and abs(q.change_percent) > 0.01
        ),
        key=lambda x: abs(x["change_percent"]),
        reverse=True,
    )[:8]

    last_run = db.query(models.CollectionRun).order_by(models.CollectionRun.started_at.desc()).first()

    return schemas.DashboardSummary(
        total_countries=db.query(models.Country).filter(models.Country.is_active.is_(True)).count(),
        total_platforms=len(platforms),
        total_price_points_24h=len(quotes_24h),
        new_price_points_24h=len(new_24h),
        active_promotions_7d=promotions_7d,
        social_posts_7d=social_7d,
        live_mode=settings.is_live_mode,
        last_run=last_run,
        best_rate_per_card_type=list(best_rate_per_card_type.values()),
        biggest_movers=movers,
    )
