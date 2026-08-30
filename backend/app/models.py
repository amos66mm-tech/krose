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
    code: Mapped[str] = mapped_column(String(4), unique=True, index=True)
    name_zh: Mapped[str] = mapped_column(String(64))
    name_en: Mapped[str] = mapped_column(String(64))
    currency_code: Mapped[str] = mapped_column(String(8))
    flag_emoji: Mapped[str] = mapped_column(String(8), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    platforms: Mapped[list["Platform"]] = relationship(back_populates="country")


class Platform(Base):
    """某个国家里的礼品卡交易 App / 平台。"""

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
    trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    country: Mapped[Country] = relationship(back_populates="platforms")
    price_quotes: Mapped[list["PriceQuote"]] = relationship(back_populates="platform")
    activities: Mapped[list["Activity"]] = relationship(back_populates="platform")
    social_posts: Mapped[list["SocialPost"]] = relationship(back_populates="platform")


class GiftCardType(Base):
    """礼品卡种类，例如 Amazon / iTunes / Steam。"""

    __tablename__ = "gift_card_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    icon: Mapped[str] = mapped_column(String(16), default="🎁")

    price_quotes: Mapped[list["PriceQuote"]] = relationship(back_populates="gift_card_type")


class PriceQuote(Base):
    """从原文中抽取出来的回收价——这是情报库的派生视图，不是唯一真相。"""

    __tablename__ = "price_quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), index=True)
    gift_card_type_id: Mapped[int] = mapped_column(ForeignKey("gift_card_types.id"), index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)

    direction: Mapped[str] = mapped_column(String(16), default="sell_to_platform")
    rate_percent: Mapped[float] = mapped_column(Float)
    price_value: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="NGN")
    unit_description: Mapped[str] = mapped_column(String(128), default="per $100 card")

    source_url: Mapped[str] = mapped_column(String(512), default="")
    source_title: Mapped[str] = mapped_column(String(256), default="")
    raw_snippet: Mapped[str] = mapped_column(Text, default="")

    is_new: Mapped[bool] = mapped_column(Boolean, default=False)
    change_percent: Mapped[float] = mapped_column(Float, default=0.0)

    collected_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    platform: Mapped[Platform] = relationship(back_populates="price_quotes")
    gift_card_type: Mapped[GiftCardType] = relationship(back_populates="price_quotes")
    document: Mapped["Document | None"] = relationship()


class Activity(Base):
    """从原文中抽取的活动 / 公告（派生视图）。"""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)

    activity_type: Mapped[str] = mapped_column(String(32), default="announcement")
    title: Mapped[str] = mapped_column(String(256))
    summary: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(String(512), default="")

    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    platform: Mapped[Platform] = relationship(back_populates="activities")


class SocialPost(Base):
    """从原文中抽取的社媒动态（派生视图）。"""

    __tablename__ = "social_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)

    network: Mapped[str] = mapped_column(String(32), default="twitter")
    author: Mapped[str] = mapped_column(String(128), default="")
    content: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(512), default="")
    sentiment: Mapped[str] = mapped_column(String(16), default="neutral")
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)

    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    platform: Mapped[Platform] = relationship(back_populates="social_posts")


class CollectionRun(Base):
    """每次采集任务的执行记录。"""

    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(32), default="intel")
    mode: Mapped[str] = mapped_column(String(16), default="demo")
    status: Mapped[str] = mapped_column(String(16), default="running")
    targets_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")

    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Document(Base):
    """情报原文。每一条搜索命中、网页、帖子都先完整归档，再谈抽取。"""

    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("canonical_url", name="uq_documents_canonical_url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(768), default="")
    canonical_url: Mapped[str] = mapped_column(String(768), index=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    snippet: Mapped[str] = mapped_column(Text, default="")
    full_text: Mapped[str] = mapped_column(Text, default="")
    source_domain: Mapped[str] = mapped_column(String(256), default="", index=True)
    source_kind: Mapped[str] = mapped_column(String(32), default="web", index=True)
    stream: Mapped[str] = mapped_column(String(32), default="market_scan", index=True)
    country_code: Mapped[str | None] = mapped_column(String(4), nullable=True, index=True)
    query: Mapped[str] = mapped_column(String(512), default="")
    author: Mapped[str] = mapped_column(String(256), default="")
    content_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    last_seen_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=1)
    collection_run_id: Mapped[int | None] = mapped_column(ForeignKey("collection_runs.id"), nullable=True)

    # 整理后的字段（启发式或 LLM 写入；原文始终保留）
    summary_zh: Mapped[str] = mapped_column(Text, default="")
    doc_type: Mapped[str] = mapped_column(String(32), default="other", index=True)
    sentiment: Mapped[str] = mapped_column(String(16), default="neutral")
    facts_json: Mapped[str] = mapped_column(Text, default="[]")
    is_analyzed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    relevance: Mapped[float] = mapped_column(Float, default=0.5)

    entity_links: Mapped[list["DocumentEntity"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    tag_links: Mapped[list["DocumentTag"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Entity(Base):
    """从原文里抽出或从种子目录提升上来的实体：平台、卡种、支付通道、人物、主题等。"""

    __tablename__ = "entities"
    __table_args__ = (UniqueConstraint("slug", "entity_type", name="uq_entity_slug_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(256), index=True)
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    country_code: Mapped[str | None] = mapped_column(String(4), nullable=True, index=True)
    platform_id: Mapped[int | None] = mapped_column(ForeignKey("platforms.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    mention_count: Mapped[int] = mapped_column(Integer, default=0)
    is_seeded: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    first_seen_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    aliases: Mapped[list["EntityAlias"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    document_links: Mapped[list["DocumentEntity"]] = relationship(back_populates="entity", cascade="all, delete-orphan")


class EntityAlias(Base):
    __tablename__ = "entity_aliases"
    __table_args__ = (UniqueConstraint("normalized", name="uq_entity_alias_normalized"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), index=True)
    alias: Mapped[str] = mapped_column(String(256))
    normalized: Mapped[str] = mapped_column(String(256), index=True)

    entity: Mapped[Entity] = relationship(back_populates="aliases")


class DocumentEntity(Base):
    __tablename__ = "document_entities"
    __table_args__ = (UniqueConstraint("document_id", "entity_id", name="uq_doc_entity"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), index=True)
    salience: Mapped[float] = mapped_column(Float, default=1.0)
    mention_context: Mapped[str] = mapped_column(String(256), default="")

    document: Mapped[Document] = relationship(back_populates="entity_links")
    entity: Mapped[Entity] = relationship(back_populates="document_links")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(32), default="topic")

    document_links: Mapped[list["DocumentTag"]] = relationship(back_populates="tag", cascade="all, delete-orphan")


class DocumentTag(Base):
    __tablename__ = "document_tags"
    __table_args__ = (UniqueConstraint("document_id", "tag_id", name="uq_doc_tag"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), index=True)

    document: Mapped[Document] = relationship(back_populates="tag_links")
    tag: Mapped[Tag] = relationship(back_populates="document_links")


class WatchQuery(Base):
    """一张采集网。系统预置一批宽网，用户随时可以再加——因为事先不知道要什么。"""

    __tablename__ = "watch_queries"
    __table_args__ = (UniqueConstraint("key", name="uq_watch_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(128), index=True)
    label: Mapped[str] = mapped_column(String(256))
    query: Mapped[str] = mapped_column(String(768))
    stream: Mapped[str] = mapped_column(String(32), default="custom", index=True)
    country_code: Mapped[str | None] = mapped_column(String(4), nullable=True, index=True)
    include_domains: Mapped[str] = mapped_column(Text, default="")
    exa_category: Mapped[str] = mapped_column(String(32), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
