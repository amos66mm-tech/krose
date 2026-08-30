"""LLM 结构化抽取的输出契约。所有 schema 都要求 LLM 严格按 JSON 输出，再用 pydantic 校验。"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ExtractedPrice(BaseModel):
    found: bool = Field(description="该资料中是否包含明确的礼品卡回收/收购价格信息")
    rate_percent: Optional[float] = Field(default=None, description="相对礼品卡面值的回收百分比，例如 78.5 表示按面值 78.5% 收购")
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
