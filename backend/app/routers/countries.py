from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/countries", tags=["countries"])


@router.get("", response_model=list[schemas.CountryOut])
def list_countries(db: Session = Depends(get_db)):
    return db.query(models.Country).filter(models.Country.is_active.is_(True)).order_by(models.Country.name_en).all()
