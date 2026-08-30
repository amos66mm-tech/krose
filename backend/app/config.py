"""全局配置。所有密钥/开关均通过环境变量注入（本地用 .env，云端用 Secrets）。"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- 基础 ---
    app_name: str = "GiftRadar"
    environment: str = "development"
    database_url: str = "sqlite:///./data/giftradar.db"

    # --- Exa 搜索 API ---
    exa_api_key: Optional[str] = None

    # --- LLM（遵循 OpenAI API 协议，可指向任意兼容供应商） ---
    llm_api_key: Optional[str] = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1

    # --- 采集调度 ---
    collection_interval_minutes: int = 180
    enable_scheduler: bool = True
    # 未配置 Exa Key 时，是否加载演示语料库（便于本地发现体验；真实采集永不写入演示文档）
    allow_mock_fallback: bool = True
    # 每个监控目标一次拉取多少条原文（全部归档，而不是只留第一条抽取结果）
    search_results_per_watch: int = 8

    # --- CORS ---
    cors_origins: str = "*"

    # --- 粗略汇率兜底（本地货币 / 1 USD），仅用于把"某面额卡在本地卖多少钱"换算成"占面值百分比"。
    # 这是一个近似值，不代表实时汇率；生产环境建议接入实时汇率 API 替换。可用同名环境变量覆盖，例如 FX_NGN_PER_USD=1600 ---
    fx_ngn_per_usd: float = 1500.0
    fx_ghs_per_usd: float = 15.5
    fx_xaf_per_usd: float = 600.0

    @property
    def fx_table(self) -> dict[str, float]:
        return {"NGN": self.fx_ngn_per_usd, "GHS": self.fx_ghs_per_usd, "XAF": self.fx_xaf_per_usd}

    @property
    def has_exa(self) -> bool:
        return bool(self.exa_api_key)

    @property
    def has_llm(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def can_collect(self) -> bool:
        """有 Exa Key 就能把公开网页收进情报库；没有 LLM 也至少能检索原文。"""
        return self.has_exa

    @property
    def is_live_mode(self) -> bool:
        """能真实采集即视为 live。LLM 只负责整理，不再作为采集开关。"""
        return self.can_collect


@lru_cache
def get_settings() -> Settings:
    return Settings()
