from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Country(Base):
    """目标市场国家，例如尼日利亚 / 加纳 / 喀麦隆。"""

    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(4), unique=True, index=True)  # NG / GH / CM ...
    name_zh: Mapped[str] = mapped_column(String(64))
    name_en: Mapped[str] = mapped_column(String(64))
    currency_code: Mapped[str] = mapped_column(String(8))
    flag_emoji: Mapped[str] = mapped_column(String(8), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    platforms: Mapped[list["Platform"]] = relationship(back_populates="country")


class Platform(Base):
    """某个国家里的礼品卡交易 App / 平台，例如 Nigeria 的 Prestmit、Cardtonic 等。"""

    __tablename__ = "platforms"
    __table_args__ = (UniqueConstraint("country_id", "slug", name="uq_platform_country_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), index=True)
    slug: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128))
    website: Mapped[str] = mapped_column(String(256), default="")
    category: Mapped[str] = mapped_column(String(64), default="gift_card_exchange")
    logo_url: Mapped[str] = mapped_column(String(256), default="")
    twitter_handle: Mapped[str] = mapped_column(String(64), default="")
    facebook_handle: Mapped[str] = mapped_column(String(64), default="")
    instagram_handle: Mapped[str] = mapped_column(String(64), default="")
    telegram_handle: Mapped[str] = mapped_column(String(64), default="")
    trust_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100，可由社媒/活动情绪汇总得出
    notes: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    country: Mapped[Country] = relationship(back_populates="platforms")
    price_quotes: Mapped[list["PriceQuote"]] = relationship(back_populates="platform")
    activities: Mapped[list["Activity"]] = relationship(back_populates="platform")
    social_posts: Mapped[list["SocialPost"]] = relationship(back_populates="platform")


class GiftCardType(Base):
    """礼品卡种类，例如 Amazon / iTunes / Steam / Google Play / Sephora 等。"""

    __tablename__ = "gift_card_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    icon: Mapped[str] = mapped_column(String(16), default="🎁")

    price_quotes: Mapped[list["PriceQuote"]] = relationship(back_populates="gift_card_type")


class PriceQuote(Base):
    """
    一条价格记录（回收价 / 出售价）。

    我们的业务模型里，卖方（论坛用户）把礼品卡卖给平台变现，我们扮演买方（付款方）的角色，
    所以这里的价格通常是「平台向卖家收卡的折扣价」，即 rate_percent 表示相对面值的折扣比例。
    """

    __tablename__ = "price_quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), index=True)
    gift_card_type_id: Mapped[int] = mapped_column(ForeignKey("gift_card_types.id"), index=True)

    direction: Mapped[str] = mapped_column(String(16), default="sell_to_platform")
    rate_percent: Mapped[float] = mapped_column(Float)  # 例如 78.5 表示按面值78.5%回收
    price_value: Mapped[float] = mapped_column(Float, default=0.0)  # 折算后的本地货币单价（可选）
    currency: Mapped[str] = mapped_column(String(8), default="NGN")
    unit_description: Mapped[str] = mapped_column(String(128), default="per $100 card")

    source_url: Mapped[str] = mapped_column(String(512), default="")
    source_title: Mapped[str] = mapped_column(String(256), default="")
    raw_snippet: Mapped[str] = mapped_column(Text, default="")

    is_new: Mapped[bool] = mapped_column(Boolean, default=False)  # 相较上一条记录是否为新出现的价格点
    change_percent: Mapped[float] = mapped_column(Float, default=0.0)  # 相较上一条记录的变化幅度

    collected_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    platform: Mapped[Platform] = relationship(back_populates="price_quotes")
    gift_card_type: Mapped[GiftCardType] = relationship(back_populates="price_quotes")


class Activity(Base):
    """平台的活动 / 公告 / 政策变化，例如“限时加价”、“新增卡种”、“系统维护”等。"""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), index=True)

    activity_type: Mapped[str] = mapped_column(String(32), default="announcement")  # promotion/announcement/policy/outage
    title: Mapped[str] = mapped_column(String(256))
    summary: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(String(512), default="")

    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    platform: Mapped[Platform] = relationship(back_populates="activities")


class SocialPost(Base):
    """平台在社交媒体上的最新动态。"""

    __tablename__ = "social_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), index=True)

    network: Mapped[str] = mapped_column(String(32), default="twitter")  # twitter/facebook/instagram/telegram
    author: Mapped[str] = mapped_column(String(128), default="")
    content: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(512), default="")
    sentiment: Mapped[str] = mapped_column(String(16), default="neutral")  # positive/neutral/negative
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)

    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    platform: Mapped[Platform] = relationship(back_populates="social_posts")


class CollectionRun(Base):
    """每次采集任务的执行记录，便于在面板上展示 Agent 运行状态。"""

    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(32), default="all")  # price/activity/social/all
    mode: Mapped[str] = mapped_column(String(16), default="mock")  # live/mock
    status: Mapped[str] = mapped_column(String(16), default="running")  # running/success/failed
    targets_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")

    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
