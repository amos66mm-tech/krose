from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/social", tags=["social"])


@router.get("", response_model=list[schemas.SocialPostOut])
def list_social_posts(
    country_code: Optional[str] = Query(default=None),
    platform_id: Optional[int] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(models.SocialPost)
    if platform_id:
        q = q.filter(models.SocialPost.platform_id == platform_id)
    elif country_code:
        platform_ids = [
            p.id
            for p in db.query(models.Platform)
            .join(models.Country)
            .filter(models.Country.code == country_code.upper())
            .all()
        ]
        q = q.filter(models.SocialPost.platform_id.in_(platform_ids))
    return q.order_by(models.SocialPost.collected_at.desc()).limit(limit).all()
