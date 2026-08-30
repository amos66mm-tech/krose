"""把原文整理成实体、标签、摘要、派生报价。没有 LLM 时走启发式，原文始终保留。"""
from __future__ import annotations

import json
import logging
import re
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from .. import models
from ..config import get_settings
from ..fts import fts_upsert
from .extract_schemas import DocumentOrganization, ExtractedPrice
from .llm_client import LLMClient
from .textutil import normalize_alias, slugify

logger = logging.getLogger(__name__)

DOC_TYPE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("scam_report", ("scam", "fraud", "cheat", "stolen", "fake rate", "ponzi", "诈骗", "跑路")),
    ("complaint", ("delay", "pending", "didn't pay", "did not pay", "rejected", "failed payout", "still waiting", "拒付", "不到账")),
    ("rate_list", ("rate today", "today's rate", "buy rate", "we pay", "%", "₦", "ngn", "ghs", "xaf", "回收价")),
    ("promotion", ("bonus", "promo", "cashback", "extra rate", "limited time", "加价")),
    ("policy", ("cbn", "regulation", "kyc", "banned", "license", "政策", "监管")),
    ("how_to", ("how to sell", "step by step", "tutorial", "guide", "教程")),
    ("forum_thread", ("nairaland", "reddit", "who has used", "legit?", "who can vouch")),
    ("review", ("review", "trustpilot", "rating", "stars")),
    ("competitor", ("alternative", "vs ", "compared", "new app", "competitor")),
    ("news", ("announces", "launches", "shutdown", "raises", "news")),
    ("social", ("twitter", "instagram", "facebook", "telegram")),
]

TAG_KEYWORDS: list[tuple[str, str, tuple[str, ...]]] = [
    ("scam", "风险", ("scam", "fraud", "cheat", "诈骗")),
    ("payout-delay", "出金", ("delay", "pending", "not paid", "不到账")),
    ("momo", "支付", ("momo", "mtn money", "mobile money")),
    ("orange-money", "支付", ("orange money",)),
    ("amazon", "卡种", ("amazon",)),
    ("itunes", "卡种", ("itunes", "apple gift")),
    ("steam", "卡种", ("steam",)),
    ("google-play", "卡种", ("google play",)),
    ("kyc", "合规", ("kyc", "verification", "nin", "bvn")),
    ("telegram", "渠道", ("telegram", "t.me")),
    ("nairaland", "社区", ("nairaland",)),
]


def _blob(doc: models.Document) -> str:
    return " ".join(filter(None, [doc.title, doc.snippet, doc.full_text, doc.summary_zh])).lower()


def infer_doc_type(doc: models.Document) -> str:
    if doc.source_kind == "forum":
        text = _blob(doc)
        for dtype, keys in DOC_TYPE_KEYWORDS:
            if dtype in {"scam_report", "complaint", "rate_list"} and any(k in text for k in keys):
                return dtype
        return "forum_thread"
    if doc.source_kind == "social":
        return "social"
    if doc.source_kind == "news":
        return "news"
    text = _blob(doc)
    for dtype, keys in DOC_TYPE_KEYWORDS:
        if any(k in text for k in keys):
            return dtype
    return doc.doc_type or "other"


def infer_tags(doc: models.Document) -> list[tuple[str, str]]:
    text = _blob(doc)
    found: list[tuple[str, str]] = []
    for slug, category, keys in TAG_KEYWORDS:
        if any(k in text for k in keys):
            found.append((slug, category))
    return found


def _get_or_create_tag(db: Session, slug: str, category: str = "topic") -> models.Tag:
    tag = db.query(models.Tag).filter(models.Tag.slug == slug).first()
    if tag:
        return tag
    tag = models.Tag(slug=slug, name=slug.replace("-", " "), category=category)
    db.add(tag)
    db.flush()
    return tag


def _pending_doc_entity(db: Session, document_id: int, entity_id: int) -> bool:
    for obj in list(db.new):
        if isinstance(obj, models.DocumentEntity) and obj.document_id == document_id and obj.entity_id == entity_id:
            return True
    return False


def _pending_doc_tag(db: Session, document_id: int, tag_id: int) -> bool:
    for obj in list(db.new):
        if isinstance(obj, models.DocumentTag) and obj.document_id == document_id and obj.tag_id == tag_id:
            return True
    return False


def link_tag(db: Session, doc: models.Document, slug: str, category: str = "topic") -> None:
    tag = _get_or_create_tag(db, slugify(slug) or slug, category)
    exists = (
        db.query(models.DocumentTag)
        .filter(models.DocumentTag.document_id == doc.id, models.DocumentTag.tag_id == tag.id)
        .first()
    )
    if exists or _pending_doc_tag(db, doc.id, tag.id):
        return
    db.add(models.DocumentTag(document_id=doc.id, tag_id=tag.id))


def find_entity_by_name(db: Session, name: str) -> models.Entity | None:
    norm = normalize_alias(name)
    if not norm:
        return None
    alias = db.query(models.EntityAlias).filter(models.EntityAlias.normalized == norm).first()
    if alias:
        return alias.entity
    return db.query(models.Entity).filter(models.Entity.name.ilike(name.strip())).first()


def upsert_entity(
    db: Session,
    name: str,
    entity_type: str,
    *,
    aliases: Iterable[str] = (),
    country_code: Optional[str] = None,
    platform_id: Optional[int] = None,
    description: str = "",
    is_seeded: bool = False,
) -> models.Entity:
    entity = find_entity_by_name(db, name)
    if entity is None:
        slug = slugify(name)
        clash = (
            db.query(models.Entity)
            .filter(models.Entity.slug == slug, models.Entity.entity_type == entity_type)
            .first()
        )
        if clash:
            entity = clash
        else:
            entity = models.Entity(
                slug=slug,
                name=name.strip(),
                entity_type=entity_type,
                country_code=country_code,
                platform_id=platform_id,
                description=description,
                is_seeded=is_seeded,
            )
            db.add(entity)
            db.flush()

    seen: set[str] = set()
    for raw in [name, *aliases]:
        norm = normalize_alias(raw)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        taken = db.query(models.EntityAlias).filter(models.EntityAlias.normalized == norm).first()
        if taken:
            continue
        db.add(models.EntityAlias(entity_id=entity.id, alias=raw.strip(), normalized=norm))
    db.flush()
    if country_code and not entity.country_code:
        entity.country_code = country_code
    if platform_id and not entity.platform_id:
        entity.platform_id = platform_id
    if description and not entity.description:
        entity.description = description
    return entity


def link_entity(db: Session, doc: models.Document, entity: models.Entity, salience: float = 1.0) -> None:
    exists = (
        db.query(models.DocumentEntity)
        .filter(models.DocumentEntity.document_id == doc.id, models.DocumentEntity.entity_id == entity.id)
        .first()
    )
    now = models.utcnow()
    entity.last_seen_at = now
    if exists or _pending_doc_entity(db, doc.id, entity.id):
        return
    db.add(models.DocumentEntity(document_id=doc.id, entity_id=entity.id, salience=salience))
    entity.mention_count = (entity.mention_count or 0) + 1


def link_known_entities(db: Session, doc: models.Document) -> None:
    text = _blob(doc)
    aliases = db.query(models.EntityAlias).all()
    # longer aliases first so "Cardtonic Ghana" wins over "Cardtonic"
    aliases_sorted = sorted(aliases, key=lambda a: len(a.normalized), reverse=True)
    claimed_spans: list[tuple[int, int]] = []
    for alias in aliases_sorted:
        if len(alias.normalized) < 3:
            continue
        pattern = re.compile(re.escape(alias.normalized), re.IGNORECASE)
        match = pattern.search(text)
        if not match:
            continue
        span = match.span()
        if any(not (span[1] <= s or span[0] >= e) for s, e in claimed_spans):
            continue
        claimed_spans.append(span)
        link_entity(db, doc, alias.entity, salience=min(1.0, len(alias.normalized) / 8))


def _is_plausible_rate(rate_percent: float) -> bool:
    return 5.0 <= rate_percent <= 150.0


def _normalize_price_result(result: ExtractedPrice, fallback_currency: Optional[str]) -> tuple[Optional[float], Optional[str]]:
    if not result or not result.found:
        return None, None
    if result.rate_percent:
        return result.rate_percent, result.currency
    if result.absolute_price_local and result.absolute_price_face_value_usd:
        currency = (result.currency or fallback_currency or "").upper()
        fx_rate = get_settings().fx_table.get(currency)
        if fx_rate:
            face_value_local = result.absolute_price_face_value_usd * fx_rate
            if face_value_local > 0:
                return round((result.absolute_price_local / face_value_local) * 100, 2), currency
    return None, None


def _match_platform(db: Session, name: Optional[str], country_code: Optional[str]) -> models.Platform | None:
    if not name:
        return None
    q = db.query(models.Platform).filter(models.Platform.is_active.is_(True))
    if country_code:
        q = q.join(models.Country).filter(models.Country.code == country_code.upper())
    for p in q.all():
        if normalize_alias(p.name) in normalize_alias(name) or normalize_alias(name) in normalize_alias(p.name):
            return p
        if p.slug.replace("-", " ") in normalize_alias(name):
            return p
    return None


def _match_card(db: Session, name: Optional[str]) -> models.GiftCardType | None:
    if not name:
        return None
    needle = normalize_alias(name)
    for card in db.query(models.GiftCardType).all():
        if normalize_alias(card.name) in needle or needle in normalize_alias(card.name) or card.slug.replace("-", " ") in needle:
            return card
        if "apple" in needle and "apple" in normalize_alias(card.name):
            return card
        if "visa" in needle and "visa" in normalize_alias(card.name):
            return card
    return None


def derive_price_quote(
    db: Session,
    doc: models.Document,
    *,
    platform: models.Platform,
    card: models.GiftCardType,
    rate_percent: float,
    currency: str,
    unit_description: str = "",
) -> None:
    last = (
        db.query(models.PriceQuote)
        .filter(
            models.PriceQuote.platform_id == platform.id,
            models.PriceQuote.gift_card_type_id == card.id,
        )
        .order_by(models.PriceQuote.collected_at.desc())
        .first()
    )
    is_new = last is None
    change_percent = 0.0
    if last and last.rate_percent:
        change_percent = round(((rate_percent - last.rate_percent) / last.rate_percent) * 100, 2)
        if abs(change_percent) < 0.05 and last.document_id == doc.id:
            return
    db.add(
        models.PriceQuote(
            platform_id=platform.id,
            gift_card_type_id=card.id,
            document_id=doc.id,
            rate_percent=rate_percent,
            currency=currency,
            unit_description=unit_description or "per $100 e-code",
            source_url=doc.url,
            source_title=doc.title,
            raw_snippet=(doc.snippet or doc.full_text or "")[:500],
            is_new=is_new,
            change_percent=change_percent,
        )
    )


def apply_organization(db: Session, doc: models.Document, org: DocumentOrganization) -> None:
    doc.summary_zh = org.summary_zh or doc.summary_zh
    doc.doc_type = org.doc_type or infer_doc_type(doc)
    doc.sentiment = org.sentiment or "neutral"
    doc.relevance = org.relevance
    doc.facts_json = json.dumps([f.model_dump() for f in org.facts], ensure_ascii=False)
    doc.is_analyzed = True
    if org.countries and not doc.country_code:
        doc.country_code = org.countries[0]

    for tag in org.tags:
        if tag.strip():
            link_tag(db, doc, tag.strip())
    for slug, category in infer_tags(doc):
        link_tag(db, doc, slug, category)

    for mention in org.entities:
        entity = upsert_entity(
            db,
            mention.name,
            mention.entity_type,
            aliases=mention.aliases,
            country_code=doc.country_code,
        )
        link_entity(db, doc, entity)

    link_known_entities(db, doc)

    for price in org.prices:
        fake = ExtractedPrice(
            found=True,
            rate_percent=price.rate_percent,
            absolute_price_local=price.absolute_price_local,
            absolute_price_face_value_usd=price.absolute_price_face_value_usd,
            currency=price.currency,
            unit_description=price.unit_description,
        )
        rate, currency = _normalize_price_result(fake, None)
        if not rate or not _is_plausible_rate(rate):
            continue
        platform = _match_platform(db, price.platform_name, doc.country_code)
        card = _match_card(db, price.card_name)
        if platform and card:
            derive_price_quote(
                db,
                doc,
                platform=platform,
                card=card,
                rate_percent=rate,
                currency=currency or price.currency or "USD",
                unit_description=price.unit_description or "",
            )

    fts_upsert(db, doc)


def heuristic_organization(db: Session, doc: models.Document) -> DocumentOrganization:
    doc_type = infer_doc_type(doc)
    tags = [slug for slug, _ in infer_tags(doc)]
    snippet = (doc.snippet or doc.full_text or "")[:220]
    summary = doc.summary_zh or f"{doc.title}。来源 {doc.source_domain or 'unknown'}。{snippet}"
    return DocumentOrganization(
        summary_zh=summary[:400],
        doc_type=doc_type,  # type: ignore[arg-type]
        tags=tags,
        entities=[],
        facts=[],
        prices=[],
        sentiment="negative" if doc_type in {"scam_report", "complaint"} else "neutral",
        countries=[doc.country_code] if doc.country_code else [],
        relevance=0.6 if doc_type != "other" else 0.35,
    )


def llm_organization(llm: LLMClient, doc: models.Document) -> DocumentOrganization | None:
    raw = (doc.full_text or doc.snippet or "").strip()
    if not raw:
        return None
    return llm.extract(
        DocumentOrganization,
        context_label=f"{doc.title} ({doc.url})",
        raw_text=raw,
        extra_instructions=(
            "这是非洲（尼日利亚/加纳/喀麦隆）礼品卡买卖市场的公开材料。"
            "请尽量多抽出出现过的平台名、卡种、支付通道、金额、投诉和风险事实。"
            "不要编造原文没有的数字。doc_type 选最贴近的一个。"
        ),
    )


def organize_document(db: Session, doc: models.Document, llm: LLMClient | None = None, force: bool = False) -> None:
    if doc.is_analyzed and not force:
        link_known_entities(db, doc)
        return
    org = None
    if llm and llm.is_configured:
        try:
            org = llm_organization(llm, doc)
        except Exception as exc:  # noqa: BLE001
            status = getattr(exc, "status_code", None)
            logger.warning("LLM 整理失败 document=%s (%s): %s", doc.id, type(exc).__name__, exc)
            if status not in {401, 403}:
                logger.debug("LLM 整理堆栈", exc_info=True)
    if org is None:
        org = heuristic_organization(db, doc)
    apply_organization(db, doc, org)


def organize_pending(db: Session, llm: LLMClient | None = None, limit: int = 200) -> int:
    pending = (
        db.query(models.Document)
        .filter(models.Document.is_analyzed.is_(False))
        .order_by(models.Document.collected_at.desc())
        .limit(limit)
        .all()
    )
    for doc in pending:
        organize_document(db, doc, llm)
    return len(pending)
