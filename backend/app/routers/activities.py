from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("", response_model=list[schemas.ActivityOut])
def list_activities(
    country_code: Optional[str] = Query(default=None),
    platform_id: Optional[int] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(models.Activity)
    if platform_id:
        q = q.filter(models.Activity.platform_id == platform_id)
    elif country_code:
        platform_ids = [
            p.id
            for p in db.query(models.Platform)
            .join(models.Country)
            .filter(models.Country.code == country_code.upper())
            .all()
        ]
        q = q.filter(models.Activity.platform_id.in_(platform_ids))
    return q.order_by(models.Activity.collected_at.desc()).limit(limit).all()
