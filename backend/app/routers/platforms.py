from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["platforms"])


@router.get("/platforms", response_model=list[schemas.PlatformOut])
def list_platforms(
    country_code: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(models.Platform).filter(models.Platform.is_active.is_(True))
    if country_code:
        q = q.join(models.Country).filter(models.Country.code == country_code.upper())
    return q.order_by(models.Platform.name).all()


@router.get("/gift-card-types", response_model=list[schemas.GiftCardTypeOut])
def list_gift_card_types(db: Session = Depends(get_db)):
    return db.query(models.GiftCardType).order_by(models.GiftCardType.name).all()
