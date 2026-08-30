"""采集流水线：搜索 -> 结构化抽取 -> 落库。三条流水线（价格/活动/社媒）共享同一套骨架。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .. import models
from ..config import get_settings
from . import mock_data, targets as target_builders
from .exa_client import ExaClient
from .extract_schemas import ExtractedActivity, ExtractedPrice, ExtractedSocialPost
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class CollectionStats:
    def __init__(self) -> None:
        self.targets_processed = 0
        self.records_created = 0
        self.errors: list[str] = []


def _start_run(db: Session, scope: str, mode: str) -> models.CollectionRun:
    run = models.CollectionRun(scope=scope, mode=mode, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _finish_run(db: Session, run: models.CollectionRun, stats: CollectionStats, status: str = "success") -> None:
    run.status = status
    run.targets_processed = stats.targets_processed
    run.records_created = stats.records_created
    run.error_message = "\n".join(stats.errors[:20])
    run.finished_at = datetime.now(timezone.utc)
    db.add(run)
    db.commit()


def _card_pool_names(db: Session) -> list[str]:
    return [c.name for c in db.query(models.GiftCardType).all()]


def _is_plausible_rate(rate_percent: float) -> bool:
    """礼品卡回收率的合理区间粗略过滤，避免 LLM 把绝对货币金额误当成百分比抽出来。"""
    return 5.0 <= rate_percent <= 150.0


def _normalize_price_result(result, fallback_currency: Optional[str]) -> tuple[Optional[float], Optional[str]]:
    """
    把 LLM 抽取结果统一换算成「占面值百分比」。
    - 如果 LLM 直接给了 rate_percent，直接用。
    - 如果只给了绝对本地货币金额 + 对应美元面额，用近似汇率表（config.fx_table）换算成百分比。
      注意：这里的汇率是粗略兜底值，不是实时汇率，换算结果仅供参考。
    """
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
                rate_percent = round((result.absolute_price_local / face_value_local) * 100, 2)
                return rate_percent, currency
    return None, None


def run_price_collection(db: Session, platform_ids: Optional[list[int]] = None) -> models.CollectionRun:
    settings = get_settings()
    live = settings.is_live_mode
    run = _start_run(db, "price", "live" if live else "mock")
    stats = CollectionStats()

    exa = ExaClient() if live else None
    llm = LLMClient() if live else None
    wanted_targets = target_builders.build_price_targets(db, platform_ids)

    try:
        for t in wanted_targets:
            stats.targets_processed += 1
            platform = db.get(models.Platform, t.platform_id)
            gift_card_type = db.get(models.GiftCardType, t.extra["gift_card_type_id"])
            if not platform or not gift_card_type:
                continue

            extracted: Optional[ExtractedPrice] = None
            source_url = ""
            source_title = ""
            raw_snippet = ""

            if live and exa and llm:
                try:
                    hits = exa.search(t.query, num_results=3, include_domains=t.include_domains)
                    for hit in hits:
                        result = llm.extract(
                            ExtractedPrice,
                            context_label=t.context_label,
                            raw_text=hit.summary or hit.text,
                            extra_instructions=(
                                "这段文本可能来自一个平台的博客/价格计算器/公告页面。"
                                "优先寻找「占卡面值百分比」的直接表述；如果没有，就找「某个面额（通常按 $100 换算）"
                                "对应的本地货币金额或区间」，把中位数填进 absolute_price_local，"
                                "并把对应的美元面额填进 absolute_price_face_value_usd。"
                                "只有当文本完全没有任何具体价格数字时才把 found 设为 false。"
                            ),
                        )
                        normalized_rate, normalized_currency = _normalize_price_result(result, t.extra.get("currency"))
                        if result and result.found and normalized_rate and _is_plausible_rate(normalized_rate):
                            extracted = result
                            extracted.rate_percent = normalized_rate
                            if normalized_currency:
                                extracted.currency = normalized_currency
                            source_url = hit.url
                            source_title = hit.title
                            raw_snippet = (hit.summary or hit.text)[:500]
                            break
                except Exception as exc:  # noqa: BLE001
                    stats.errors.append(f"{t.key}: {exc}")
                    logger.exception("价格采集失败 %s", t.key)

            if extracted and extracted.rate_percent:
                rate_percent = extracted.rate_percent
                currency = extracted.currency or t.extra.get("currency", "USD")
                unit_description = extracted.unit_description or "per $100 e-code"
            else:
                mock = mock_data.mock_price_point(platform.name, gift_card_type.name, base_seed=t.key)
                rate_percent = mock["rate_percent"]
                currency = t.extra.get("currency", "USD")
                unit_description = mock["unit_description"]
                source_title = mock["source_title"]
                source_url = mock["source_url"]
                raw_snippet = mock["raw_snippet"]

            last = (
                db.query(models.PriceQuote)
                .filter(
                    models.PriceQuote.platform_id == platform.id,
                    models.PriceQuote.gift_card_type_id == gift_card_type.id,
                )
                .order_by(models.PriceQuote.collected_at.desc())
                .first()
            )
            is_new = last is None
            change_percent = 0.0
            if last and last.rate_percent:
                change_percent = round(((rate_percent - last.rate_percent) / last.rate_percent) * 100, 2)

            quote = models.PriceQuote(
                platform_id=platform.id,
                gift_card_type_id=gift_card_type.id,
                direction="sell_to_platform",
                rate_percent=rate_percent,
                price_value=0.0,
                currency=currency,
                unit_description=unit_description,
                source_url=source_url,
                source_title=source_title,
                raw_snippet=raw_snippet,
                is_new=is_new,
                change_percent=change_percent,
            )
            db.add(quote)
            stats.records_created += 1
        db.commit()
        _finish_run(db, run, stats, "success")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        stats.errors.append(str(exc))
        _finish_run(db, run, stats, "failed")
        raise
    return run


def run_activity_collection(db: Session, platform_ids: Optional[list[int]] = None) -> models.CollectionRun:
    settings = get_settings()
    live = settings.is_live_mode
    run = _start_run(db, "activity", "live" if live else "mock")
    stats = CollectionStats()

    exa = ExaClient() if live else None
    llm = LLMClient() if live else None
    card_pool = _card_pool_names(db)
    wanted_targets = target_builders.build_activity_targets(db, platform_ids)

    try:
        for t in wanted_targets:
            stats.targets_processed += 1
            platform = db.get(models.Platform, t.platform_id)
            if not platform:
                continue

            extracted: Optional[ExtractedActivity] = None
            source_url = ""
            published_at = None

            if live and exa and llm:
                try:
                    hits = exa.search(t.query, num_results=3)
                    for hit in hits:
                        result = llm.extract(
                            ExtractedActivity,
                            context_label=t.context_label,
                            raw_text=hit.summary or hit.text,
                        )
                        if result and result.found and result.title:
                            extracted = result
                            source_url = hit.url
                            published_at = _parse_date(hit.published_date)
                            break
                except Exception as exc:  # noqa: BLE001
                    stats.errors.append(f"{t.key}: {exc}")
                    logger.exception("活动采集失败 %s", t.key)

            if extracted and extracted.title:
                activity = models.Activity(
                    platform_id=platform.id,
                    activity_type=extracted.activity_type or "announcement",
                    title=extracted.title,
                    summary=extracted.summary or "",
                    source_url=source_url,
                    published_at=published_at,
                )
            else:
                mock = mock_data.mock_activity(platform.name, seed_extra=t.key, card_pool=card_pool)
                activity = models.Activity(
                    platform_id=platform.id,
                    activity_type=mock["activity_type"],
                    title=mock["title"],
                    summary=mock["summary"],
                    source_url=mock["source_url"],
                    published_at=mock["published_at"],
                )
            db.add(activity)
            stats.records_created += 1
        db.commit()
        _finish_run(db, run, stats, "success")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        stats.errors.append(str(exc))
        _finish_run(db, run, stats, "failed")
        raise
    return run


def run_social_collection(db: Session, platform_ids: Optional[list[int]] = None) -> models.CollectionRun:
    settings = get_settings()
    live = settings.is_live_mode
    run = _start_run(db, "social", "live" if live else "mock")
    stats = CollectionStats()

    exa = ExaClient() if live else None
    llm = LLMClient() if live else None
    card_pool = _card_pool_names(db)
    wanted_targets = target_builders.build_social_targets(db, platform_ids)

    try:
        for t in wanted_targets:
            stats.targets_processed += 1
            platform = db.get(models.Platform, t.platform_id)
            if not platform:
                continue

            extracted: Optional[ExtractedSocialPost] = None
            source_url = ""
            published_at = None

            if live and exa and llm:
                try:
                    hits = exa.search(t.query, num_results=3, category="social")
                    for hit in hits:
                        result = llm.extract(
                            ExtractedSocialPost,
                            context_label=t.context_label,
                            raw_text=hit.summary or hit.text,
                        )
                        if result and result.found and result.content_summary:
                            extracted = result
                            source_url = hit.url
                            published_at = _parse_date(hit.published_date)
                            break
                except Exception as exc:  # noqa: BLE001
                    stats.errors.append(f"{t.key}: {exc}")
                    logger.exception("社媒采集失败 %s", t.key)

            if extracted and extracted.content_summary:
                post = models.SocialPost(
                    platform_id=platform.id,
                    network="twitter",
                    author=extracted.author or platform.twitter_handle or platform.name,
                    content=extracted.content_summary,
                    url=source_url,
                    sentiment=extracted.sentiment or "neutral",
                    engagement_score=0.0,
                    published_at=published_at,
                )
            else:
                mock = mock_data.mock_social_post(
                    platform.name, seed_extra=t.key, card_pool=card_pool, handle=platform.twitter_handle
                )
                post = models.SocialPost(
                    platform_id=platform.id,
                    network=mock["network"],
                    author=mock["author"],
                    content=mock["content"],
                    url=mock["url"],
                    sentiment=mock["sentiment"],
                    engagement_score=mock["engagement_score"],
                    published_at=mock["published_at"],
                )
            db.add(post)
            stats.records_created += 1
        db.commit()
        _finish_run(db, run, stats, "success")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        stats.errors.append(str(exc))
        _finish_run(db, run, stats, "failed")
        raise
    return run


def run_all_collections(db: Session, platform_ids: Optional[list[int]] = None) -> list[models.CollectionRun]:
    return [
        run_price_collection(db, platform_ids),
        run_activity_collection(db, platform_ids),
        run_social_collection(db, platform_ids),
    ]


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
