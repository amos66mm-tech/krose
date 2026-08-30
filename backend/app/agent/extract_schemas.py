"""LLM 结构化抽取的输出契约。所有 schema 都要求 LLM 严格按 JSON 输出，再用 pydantic 校验。"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ExtractedPrice(BaseModel):
    found: bool = Field(
        description=(
            "该资料中是否包含任何可用的礼品卡回收/收购价格信息——"
            "可以是「占面值百分比」，也可以是「某个面额的卡对应的本地货币金额/区间」。"
            "只要能读到一个具体数字就设为 true，交给后续逻辑换算，不要仅因为格式不是百分比就设为 false。"
        )
    )
    rate_percent: Optional[float] = Field(
        default=None,
        description=(
            "如果原文直接给出了「占卡面值百分比」，填这里，取值范围通常在 5~150 之间，例如 78.5 表示按面值 78.5% 收购。"
            "如果原文没有直接给百分比，就把这个字段留空（null），改用下面的 absolute_price_local 字段。"
        ),
    )
    absolute_price_local: Optional[float] = Field(
        default=None,
        description=(
            "如果原文给出的是绝对本地货币金额（例如 '₦35,000–₦42,000'），填该区间的中位数（如 38500）。"
            "只在 rate_percent 为空时使用这个字段。"
        ),
    )
    absolute_price_face_value_usd: Optional[float] = Field(
        default=None,
        description="上面 absolute_price_local 对应的卡面额，用美元计价，例如 100（表示这是一张 $100 面值的卡）。",
    )
    currency: Optional[str] = Field(default=None, description="结算货币的 ISO 代码，例如 NGN/GHS/XAF/USD")
    unit_description: Optional[str] = Field(default=None, description="价格适用的卡面额/条件说明，例如 'per $100 physical card'")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractedActivity(BaseModel):
    found: bool
    activity_type: Optional[Literal["promotion", "announcement", "policy", "outage"]] = None
    title: Optional[str] = None
    summary: Optional[str] = Field(default=None, description="不超过80字的简洁中文摘要")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractedSocialPost(BaseModel):
    found: bool
    author: Optional[str] = None
    content_summary: Optional[str] = Field(default=None, description="不超过80字的中文摘要")
    sentiment: Optional[Literal["positive", "neutral", "negative"]] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class GenericExtraction(BaseModel):
    """给「爬万物」的自定义监控目标用的通用抽取结果。"""

    found: bool
    headline: Optional[str] = None
    summary: Optional[str] = Field(default=None, description="不超过120字的中文摘要")
    key_facts: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


DocType = Literal[
    "rate_list",
    "promotion",
    "complaint",
    "news",
    "how_to",
    "competitor",
    "scam_report",
    "policy",
    "forum_thread",
    "review",
    "social",
    "other",
]

EntityType = Literal["platform", "card_type", "org", "person", "place", "payment_rail", "topic", "other"]


class ExtractedEntityMention(BaseModel):
    name: str
    entity_type: EntityType = "other"
    aliases: list[str] = Field(default_factory=list)


class ExtractedFact(BaseModel):
    claim: str = Field(description="一条可独立阅读的事实，尽量带数字/主体/时间")
    kind: str = Field(default="other", description="rate/event/warning/opinion/payout/other")
    value: Optional[str] = None


class ExtractedPriceMention(BaseModel):
    found: bool = True
    platform_name: Optional[str] = None
    card_name: Optional[str] = None
    rate_percent: Optional[float] = None
    absolute_price_local: Optional[float] = None
    absolute_price_face_value_usd: Optional[float] = None
    currency: Optional[str] = None
    unit_description: Optional[str] = None


class DocumentOrganization(BaseModel):
    """把一篇原文整理成可浏览/可检索的结构。宁可多标实体和事实，也不要丢掉原文里出现的名字。"""

    summary_zh: str = Field(description="不超过160字的中文摘要，说明这篇材料对礼品卡交易市场意味着什么")
    doc_type: DocType = "other"
    tags: list[str] = Field(default_factory=list, description="短标签，英文或中文均可，例如 scam / momo / amazon-rate")
    entities: list[ExtractedEntityMention] = Field(default_factory=list)
    facts: list[ExtractedFact] = Field(default_factory=list)
    prices: list[ExtractedPriceMention] = Field(default_factory=list)
    sentiment: Literal["positive", "neutral", "negative", "mixed"] = "neutral"
    countries: list[str] = Field(default_factory=list, description="NG/GH/CM 等 ISO 代码")
    relevance: float = Field(default=0.5, ge=0.0, le=1.0, description="与非洲礼品卡买卖市场的相关程度")
