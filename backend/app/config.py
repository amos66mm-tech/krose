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
    # 未配置任何真实 API Key 时，是否允许使用模拟数据填充看板（便于本地演示/开发）
    allow_mock_fallback: bool = True

    # --- CORS ---
    cors_origins: str = "*"

    @property
    def has_exa(self) -> bool:
        return bool(self.exa_api_key)

    @property
    def has_llm(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def is_live_mode(self) -> bool:
        """两把钥匙都配置好了，才认为进入“真实抓取”模式，否则回退模拟数据。"""
        return self.has_exa and self.has_llm


@lru_cache
def get_settings() -> Settings:
    return Settings()
