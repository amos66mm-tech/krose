from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("/board", response_model=list[schemas.PriceBoardCell])
def price_board(
    country_code: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """返回「平台 x 礼品卡种类」矩阵中每个格子的最新价格，用于面板首屏的价格看板。"""
    platform_q = db.query(models.Platform).filter(models.Platform.is_active.is_(True))
    if country_code:
        platform_q = platform_q.join(models.Country).filter(models.Country.code == country_code.upper())
    platform_ids = [p.id for p in platform_q.all()]
    if not platform_ids:
        return []

    quotes = (
        db.query(models.PriceQuote)
        .filter(models.PriceQuote.platform_id.in_(platform_ids))
        .order_by(models.PriceQuote.collected_at.desc())
        .all()
    )

    seen: set[tuple[int, int]] = set()
    platform_lookup = {p.id: p for p in platform_q.all()}
    card_lookup = {c.id: c for c in db.query(models.GiftCardType).all()}

    cells: list[schemas.PriceBoardCell] = []
    for q in quotes:
        key = (q.platform_id, q.gift_card_type_id)
        if key in seen:
            continue
        seen.add(key)
        platform = platform_lookup.get(q.platform_id)
        card = card_lookup.get(q.gift_card_type_id)
        if not platform or not card:
            continue
        cells.append(
            schemas.PriceBoardCell(
                platform_id=platform.id,
                platform_name=platform.name,
                gift_card_type_id=card.id,
                gift_card_type_name=card.name,
                gift_card_icon=card.icon,
                rate_percent=q.rate_percent,
                currency=q.currency,
                is_new=q.is_new,
                change_percent=q.change_percent,
                collected_at=q.collected_at,
                source_url=q.source_url,
            )
        )
    return cells


@router.get("/history", response_model=list[schemas.PriceQuoteOut])
def price_history(
    platform_id: int,
    gift_card_type_id: int,
    days: int = Query(default=30, ge=1, le=180),
    db: Session = Depends(get_db),
):
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    return (
        db.query(models.PriceQuote)
        .filter(
            models.PriceQuote.platform_id == platform_id,
            models.PriceQuote.gift_card_type_id == gift_card_type_id,
            models.PriceQuote.collected_at >= since,
        )
        .order_by(models.PriceQuote.collected_at.asc())
        .all()
    )


@router.get("/latest", response_model=list[schemas.PriceQuoteOut])
def latest_prices(
    country_code: Optional[str] = Query(default=None),
    platform_id: Optional[int] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(models.PriceQuote)
    if platform_id:
        q = q.filter(models.PriceQuote.platform_id == platform_id)
    elif country_code:
        platform_ids = [
            p.id
            for p in db.query(models.Platform)
            .join(models.Country)
            .filter(models.Country.code == country_code.upper())
            .all()
        ]
        q = q.filter(models.PriceQuote.platform_id.in_(platform_ids))
    return q.order_by(models.PriceQuote.collected_at.desc()).limit(limit).all()
