from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CountryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name_zh: str
    name_en: str
    currency_code: str
    flag_emoji: str


class PlatformOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    country_id: int
    slug: str
    name: str
    website: str
    category: str
    logo_url: str
    twitter_handle: str
    facebook_handle: str
    instagram_handle: str
    telegram_handle: str
    trust_score: float
    notes: str


class GiftCardTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name: str
    icon: str


class PriceQuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    platform_id: int
    gift_card_type_id: int
    direction: str
    rate_percent: float
    price_value: float
    currency: str
    unit_description: str
    source_url: str
    source_title: str
    is_new: bool
    change_percent: float
    collected_at: dt.datetime


class PriceBoardCell(BaseModel):
    """看板中「平台 x 卡种」矩阵里的一个单元格。"""

    platform_id: int
    platform_name: str
    gift_card_type_id: int
    gift_card_type_name: str
    gift_card_icon: str
    rate_percent: float
    currency: str
    is_new: bool
    change_percent: float
    collected_at: dt.datetime
    source_url: str


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    platform_id: int
    activity_type: str
    title: str
    summary: str
    source_url: str
    published_at: Optional[dt.datetime]
    collected_at: dt.datetime


class SocialPostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    platform_id: int
    network: str
    author: str
    content: str
    url: str
    sentiment: str
    engagement_score: float
    published_at: Optional[dt.datetime]
    collected_at: dt.datetime


class CollectionRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    scope: str
    mode: str
    status: str
    targets_processed: int
    records_created: int
    error_message: str
    started_at: dt.datetime
    finished_at: Optional[dt.datetime]


class DashboardSummary(BaseModel):
    total_countries: int
    total_platforms: int
    total_price_points_24h: int
    new_price_points_24h: int
    active_promotions_7d: int
    social_posts_7d: int
    live_mode: bool
    last_run: Optional[CollectionRunOut]
    best_rate_per_card_type: list[dict]
    biggest_movers: list[dict]


class AgentStatus(BaseModel):
    has_exa: bool
    has_llm: bool
    live_mode: bool
    can_collect: bool
    llm_model: str
    llm_base_url: str
    collection_interval_minutes: int
    scheduler_enabled: bool
    search_results_per_watch: int
    document_count: int = 0
    watch_count: int = 0


class EntityRef(BaseModel):
    id: int
    name: str
    entity_type: str
    slug: str
    mention_count: int
    is_seeded: bool
    country_code: Optional[str] = None


class TagRef(BaseModel):
    id: int
    slug: str
    name: str
    category: str
    document_count: int = 0


class DocumentListItem(BaseModel):
    id: int
    title: str
    url: str
    snippet: str
    summary_zh: str
    source_domain: str
    source_kind: str
    stream: str
    country_code: Optional[str]
    doc_type: str
    sentiment: str
    is_demo: bool
    is_analyzed: bool
    relevance: float
    collected_at: dt.datetime
    published_at: Optional[dt.datetime]
    entities: list[EntityRef] = []
    tags: list[TagRef] = []


class DocumentDetail(DocumentListItem):
    full_text: str
    author: str
    query: str
    hit_count: int
    facts: list[dict]
    related: list[DocumentListItem] = []


class EntityDetail(EntityRef):
    description: str
    aliases: list[str]
    first_seen_at: dt.datetime
    last_seen_at: dt.datetime
    platform_id: Optional[int] = None
    documents: list[DocumentListItem] = []
    related_entities: list[EntityRef] = []


class WatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    label: str
    query: str
    stream: str
    country_code: Optional[str]
    include_domains: str
    exa_category: str
    is_active: bool
    is_system: bool
    notes: str
    created_at: dt.datetime


class WatchCreate(BaseModel):
    query: str
    label: str = "自定义监控"
    country_code: Optional[str] = None
    stream: str = "custom"
    save: bool = True
    run_now: bool = True
    num_results: int = 8


class CountRow(BaseModel):
    key: str
    label: str
    count: int


class IntelOverview(BaseModel):
    total_documents: int
    documents_24h: int
    total_entities: int
    discovered_entities: int
    unanalyzed: int
    watch_count: int
    live_mode: bool
    last_run: Optional[CollectionRunOut]
    doc_type_counts: list[CountRow]
    tag_counts: list[CountRow]
    stream_counts: list[CountRow]
    top_entities: list[EntityRef]
    emerging_entities: list[EntityRef]
    top_domains: list[CountRow]


class SearchResponse(BaseModel):
    query: str
    total: int
    items: list[DocumentListItem]
