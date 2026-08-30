"""
可配置的监控目标（Watch Target）。

这是「万物皆可爬」的关键抽象：Agent 本身并不知道什么是“礼品卡”，
它只知道如何针对一个 (查询词, 抽取schema, 落库方式) 三元组去执行「搜索 -> 抽取 -> 入库」。
礼品卡价格/活动/社媒只是当前预置的三类目标，未来要扩展到其他数据源，只需要新增一个 target 构造函数即可。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from sqlalchemy.orm import Session

from .. import models


@dataclass
class WatchTarget:
    key: str
    label: str
    query: str
    context_label: str
    platform_id: Optional[int] = None
    include_domains: Optional[list[str]] = None
    category: Optional[str] = None
    extra: dict = field(default_factory=dict)


def build_price_targets(db: Session, platform_ids: Optional[list[int]] = None) -> list[WatchTarget]:
    q = db.query(models.Platform).filter(models.Platform.is_active.is_(True))
    if platform_ids:
        q = q.filter(models.Platform.id.in_(platform_ids))
    targets: list[WatchTarget] = []
    card_types = db.query(models.GiftCardType).all()
    for platform in q.all():
        for card in card_types:
            domains = [platform.website.split("//")[-1].split("/")[0]] if platform.website else None
            targets.append(
                WatchTarget(
                    key=f"price:{platform.slug}:{card.slug}",
                    label=f"{platform.name} - {card.name} 回收价",
                    query=(
                        f"{platform.name} {card.name} gift card selling rate today "
                        f"in {platform.country.name_en if platform.country else ''}"
                    ),
                    context_label=f"{platform.name} 官网/公告中关于 {card.name} 礼品卡回收价格的信息",
                    platform_id=platform.id,
                    include_domains=domains,
                    category="price",
                    extra={"gift_card_type_id": card.id, "currency": platform.country.currency_code if platform.country else "USD"},
                )
            )
    return targets


def build_activity_targets(db: Session, platform_ids: Optional[list[int]] = None) -> list[WatchTarget]:
    q = db.query(models.Platform).filter(models.Platform.is_active.is_(True))
    if platform_ids:
        q = q.filter(models.Platform.id.in_(platform_ids))
    targets: list[WatchTarget] = []
    for platform in q.all():
        targets.append(
            WatchTarget(
                key=f"activity:{platform.slug}",
                label=f"{platform.name} 最新活动/公告",
                query=f"{platform.name} gift card app new promotion OR announcement OR update",
                context_label=f"{platform.name} 近期的活动、公告、政策变化或产品更新",
                platform_id=platform.id,
                category="activity",
            )
        )
    return targets


def build_social_targets(db: Session, platform_ids: Optional[list[int]] = None) -> list[WatchTarget]:
    q = db.query(models.Platform).filter(models.Platform.is_active.is_(True))
    if platform_ids:
        q = q.filter(models.Platform.id.in_(platform_ids))
    targets: list[WatchTarget] = []
    for platform in q.all():
        handles = " OR ".join(
            filter(None, [platform.twitter_handle, platform.instagram_handle, platform.facebook_handle])
        )
        targets.append(
            WatchTarget(
                key=f"social:{platform.slug}",
                label=f"{platform.name} 最新社交媒体动态",
                query=f"{platform.name} {handles} latest post twitter OR instagram OR facebook",
                context_label=f"{platform.name} 最近在社交媒体上发布的内容",
                platform_id=platform.id,
                category="social",
            )
        )
    return targets


def build_custom_target(query: str, label: str = "自定义监控目标") -> WatchTarget:
    """供“爬万物”场景使用：任意关键词都可以立即变成一个可执行的监控目标。"""
    return WatchTarget(
        key=f"custom:{abs(hash(query))}",
        label=label,
        query=query,
        context_label=label,
        category="custom",
    )
