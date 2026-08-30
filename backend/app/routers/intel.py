from __future__ import annotations

import datetime as dt
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..agent.textutil import fts_match_query
from ..config import get_settings
from ..database import get_db

router = APIRouter(prefix="/api/intel", tags=["intel"])

DOC_TYPE_LABELS = {
    "rate_list": "报价/行情",
    "promotion": "活动",
    "complaint": "投诉/出金",
    "news": "新闻",
    "how_to": "教程/方法",
    "competitor": "新平台/竞品",
    "scam_report": "诈骗/风险",
    "policy": "监管/政策",
    "forum_thread": "论坛讨论",
    "review": "口碑",
    "social": "社媒",
    "other": "未分类",
}


def _tag_ref(tag: models.Tag, count: int = 0) -> schemas.TagRef:
    return schemas.TagRef(id=tag.id, slug=tag.slug, name=tag.name, category=tag.category, document_count=count)


def _entity_ref(entity: models.Entity) -> schemas.EntityRef:
    return schemas.EntityRef(
        id=entity.id,
        name=entity.name,
        entity_type=entity.entity_type,
        slug=entity.slug,
        mention_count=entity.mention_count or 0,
        is_seeded=entity.is_seeded,
        country_code=entity.country_code,
    )


def _doc_item(doc: models.Document) -> schemas.DocumentListItem:
    entities = [link.entity for link in doc.entity_links if link.entity]
    tags = [link.tag for link in doc.tag_links if link.tag]
    return schemas.DocumentListItem(
        id=doc.id,
        title=doc.title,
        url=doc.url,
        snippet=doc.snippet or (doc.full_text or "")[:280],
        summary_zh=doc.summary_zh,
        source_domain=doc.source_domain,
        source_kind=doc.source_kind,
        stream=doc.stream,
        country_code=doc.country_code,
        doc_type=doc.doc_type,
        sentiment=doc.sentiment,
        is_demo=doc.is_demo,
        is_analyzed=doc.is_analyzed,
        relevance=doc.relevance,
        collected_at=doc.collected_at,
        published_at=doc.published_at,
        entities=[_entity_ref(e) for e in entities[:8]],
        tags=[_tag_ref(t) for t in tags[:8]],
    )


def _eager(q):
    return q.options(
        selectinload(models.Document.entity_links).selectinload(models.DocumentEntity.entity),
        selectinload(models.Document.tag_links).selectinload(models.DocumentTag.tag),
    )


def _filtered_docs(
    db: Session,
    *,
    country_code: Optional[str],
    doc_type: Optional[str],
    stream: Optional[str],
    tag: Optional[str],
    entity_id: Optional[int],
    source_kind: Optional[str],
    q: Optional[str],
):
    query = _eager(db.query(models.Document))
    if country_code:
        query = query.filter(models.Document.country_code == country_code.upper())
    if doc_type:
        query = query.filter(models.Document.doc_type == doc_type)
    if stream:
        query = query.filter(models.Document.stream == stream)
    if source_kind:
        query = query.filter(models.Document.source_kind == source_kind)
    if tag:
        query = query.join(models.DocumentTag).join(models.Tag).filter(models.Tag.slug == tag)
    if entity_id:
        query = query.join(models.DocumentEntity).filter(models.DocumentEntity.entity_id == entity_id)
    if q and q.strip():
        term = q.strip()
        like = f"%{term}%"
        fts_ids: list[int] = []
        try:
            if db.get_bind().dialect.name == "sqlite":
                rows = db.execute(
                    text("SELECT rowid FROM documents_fts WHERE documents_fts MATCH :q LIMIT 500"),
                    {"q": fts_match_query(term)},
                )
                fts_ids = [r[0] for r in rows]
        except Exception:
            fts_ids = []
        clauses = [
            models.Document.title.ilike(like),
            models.Document.snippet.ilike(like),
            models.Document.full_text.ilike(like),
            models.Document.summary_zh.ilike(like),
            models.Document.source_domain.ilike(like),
        ]
        if fts_ids:
            clauses.append(models.Document.id.in_(fts_ids))
        query = query.filter(or_(*clauses))
    return query.distinct()


@router.get("/overview", response_model=schemas.IntelOverview)
def overview(country_code: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    settings = get_settings()
    docs = db.query(models.Document)
    if country_code:
        docs = docs.filter(models.Document.country_code == country_code.upper())
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(hours=24)
    week = now - dt.timedelta(days=7)

    total = docs.count()
    docs_24h = docs.filter(models.Document.collected_at >= since).count()
    unanalyzed = docs.filter(models.Document.is_analyzed.is_(False)).count()

    type_rows = (
        docs.with_entities(models.Document.doc_type, func.count(models.Document.id))
        .group_by(models.Document.doc_type)
        .all()
    )
    stream_rows = (
        docs.with_entities(models.Document.stream, func.count(models.Document.id))
        .group_by(models.Document.stream)
        .all()
    )
    domain_rows = (
        docs.with_entities(models.Document.source_domain, func.count(models.Document.id))
        .filter(models.Document.source_domain != "")
        .group_by(models.Document.source_domain)
        .order_by(func.count(models.Document.id).desc())
        .limit(8)
        .all()
    )

    tag_q = (
        db.query(models.Tag, func.count(models.DocumentTag.id).label("c"))
        .join(models.DocumentTag)
        .join(models.Document)
        .group_by(models.Tag.id)
        .order_by(func.count(models.DocumentTag.id).desc())
        .limit(12)
    )
    if country_code:
        tag_q = tag_q.filter(models.Document.country_code == country_code.upper())

    entity_q = db.query(models.Entity).order_by(models.Entity.mention_count.desc())
    if country_code:
        entity_q = entity_q.filter(
            (models.Entity.country_code == country_code.upper()) | (models.Entity.country_code.is_(None))
        )
    top_entities = entity_q.limit(10).all()
    emerging = (
        db.query(models.Entity)
        .filter(models.Entity.is_seeded.is_(False), models.Entity.first_seen_at >= week)
        .order_by(models.Entity.mention_count.desc(), models.Entity.first_seen_at.desc())
        .limit(8)
        .all()
    )
    last_run = db.query(models.CollectionRun).order_by(models.CollectionRun.started_at.desc()).first()

    return schemas.IntelOverview(
        total_documents=total,
        documents_24h=docs_24h,
        total_entities=db.query(models.Entity).count(),
        discovered_entities=db.query(models.Entity).filter(models.Entity.is_seeded.is_(False)).count(),
        unanalyzed=unanalyzed,
        watch_count=db.query(models.WatchQuery).filter(models.WatchQuery.is_active.is_(True)).count(),
        live_mode=settings.can_collect,
        last_run=last_run,
        doc_type_counts=[
            schemas.CountRow(key=k or "other", label=DOC_TYPE_LABELS.get(k or "other", k or "other"), count=c)
            for k, c in type_rows
        ],
        tag_counts=[schemas.CountRow(key=t.slug, label=t.name, count=c) for t, c in tag_q.all()],
        stream_counts=[schemas.CountRow(key=k or "other", label=k or "other", count=c) for k, c in stream_rows],
        top_entities=[_entity_ref(e) for e in top_entities],
        emerging_entities=[_entity_ref(e) for e in emerging],
        top_domains=[schemas.CountRow(key=k, label=k, count=c) for k, c in domain_rows],
    )


@router.get("/search", response_model=schemas.SearchResponse)
def search(
    q: str = Query(default=""),
    country_code: Optional[str] = None,
    doc_type: Optional[str] = None,
    stream: Optional[str] = None,
    tag: Optional[str] = None,
    entity_id: Optional[int] = None,
    source_kind: Optional[str] = None,
    limit: int = Query(default=40, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = _filtered_docs(
        db,
        country_code=country_code,
        doc_type=doc_type,
        stream=stream,
        tag=tag,
        entity_id=entity_id,
        source_kind=source_kind,
        q=q or None,
    )
    total = query.count()
    items = query.order_by(models.Document.collected_at.desc()).offset(offset).limit(limit).all()
    return schemas.SearchResponse(query=q, total=total, items=[_doc_item(d) for d in items])


@router.get("/documents/{doc_id}", response_model=schemas.DocumentDetail)
def document_detail(doc_id: int, db: Session = Depends(get_db)):
    doc = _eager(db.query(models.Document)).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    entity_ids = [link.entity_id for link in doc.entity_links]
    related: list[models.Document] = []
    if entity_ids:
        related_ids = (
            db.query(models.DocumentEntity.document_id)
            .filter(models.DocumentEntity.entity_id.in_(entity_ids), models.DocumentEntity.document_id != doc.id)
            .group_by(models.DocumentEntity.document_id)
            .order_by(func.count(models.DocumentEntity.id).desc())
            .limit(6)
            .all()
        )
        ids = [r[0] for r in related_ids]
        if ids:
            related = _eager(db.query(models.Document)).filter(models.Document.id.in_(ids)).all()
    try:
        facts = json.loads(doc.facts_json or "[]")
    except json.JSONDecodeError:
        facts = []
    item = _doc_item(doc)
    return schemas.DocumentDetail(
        **item.model_dump(),
        full_text=doc.full_text,
        author=doc.author,
        query=doc.query,
        hit_count=doc.hit_count,
        facts=facts if isinstance(facts, list) else [],
        related=[_doc_item(d) for d in related],
    )


@router.get("/entities", response_model=list[schemas.EntityRef])
def list_entities(
    entity_type: Optional[str] = None,
    q: Optional[str] = None,
    discovered_only: bool = False,
    limit: int = Query(default=80, ge=1, le=300),
    db: Session = Depends(get_db),
):
    query = db.query(models.Entity)
    if entity_type:
        query = query.filter(models.Entity.entity_type == entity_type)
    if discovered_only:
        query = query.filter(models.Entity.is_seeded.is_(False))
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(models.Entity.name.ilike(like), models.Entity.slug.ilike(like)))
    return [_entity_ref(e) for e in query.order_by(models.Entity.mention_count.desc()).limit(limit).all()]


@router.get("/entities/{entity_id}", response_model=schemas.EntityDetail)
def entity_detail(entity_id: int, db: Session = Depends(get_db)):
    entity = db.query(models.Entity).filter(models.Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")
    docs = (
        _eager(db.query(models.Document))
        .join(models.DocumentEntity)
        .filter(models.DocumentEntity.entity_id == entity.id)
        .order_by(models.Document.collected_at.desc())
        .limit(40)
        .all()
    )
    related_rows = (
        db.query(models.Entity, func.count(models.DocumentEntity.id))
        .join(models.DocumentEntity, models.DocumentEntity.entity_id == models.Entity.id)
        .filter(
            models.DocumentEntity.document_id.in_([d.id for d in docs] or [0]),
            models.Entity.id != entity.id,
        )
        .group_by(models.Entity.id)
        .order_by(func.count(models.DocumentEntity.id).desc())
        .limit(10)
        .all()
    )
    return schemas.EntityDetail(
        **_entity_ref(entity).model_dump(),
        description=entity.description,
        aliases=[a.alias for a in entity.aliases],
        first_seen_at=entity.first_seen_at,
        last_seen_at=entity.last_seen_at,
        platform_id=entity.platform_id,
        documents=[_doc_item(d) for d in docs],
        related_entities=[_entity_ref(e) for e, _ in related_rows],
    )


@router.get("/tags", response_model=list[schemas.TagRef])
def list_tags(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Tag, func.count(models.DocumentTag.id))
        .outerjoin(models.DocumentTag)
        .group_by(models.Tag.id)
        .order_by(func.count(models.DocumentTag.id).desc())
        .all()
    )
    return [_tag_ref(t, c) for t, c in rows]


@router.get("/doc-types")
def doc_types():
    return [{"key": k, "label": v} for k, v in DOC_TYPE_LABELS.items()]
