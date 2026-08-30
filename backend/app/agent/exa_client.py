"""Exa 搜索客户端的轻量封装。"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SearchHit:
    title: str
    url: str
    text: str
    summary: str
    published_date: Optional[str]
    author: Optional[str]


class ExaClient:
    """对 exa_py SDK 的薄封装，统一异常处理与结果格式，方便被 pipeline / mock 互换。"""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.exa_api_key
        self._client = None
        if self._api_key:
            from exa_py import Exa  # 延迟导入，避免没装 key 时也强依赖网络库

            self._client = Exa(api_key=self._api_key)

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def search(
        self,
        query: str,
        *,
        num_results: int = 5,
        include_domains: Optional[list[str]] = None,
        category: Optional[str] = None,
        start_published_date: Optional[str] = None,
    ) -> list[SearchHit]:
        if not self._client:
            raise RuntimeError("Exa client 未配置 EXA_API_KEY")

        kwargs = {
            "num_results": num_results,
            "contents": {"text": {"max_characters": 2500}, "summary": True},
        }
        if include_domains:
            kwargs["include_domains"] = include_domains
        if category:
            kwargs["category"] = category
        if start_published_date:
            kwargs["start_published_date"] = start_published_date

        response = self._client.search(query, **kwargs)
        hits: list[SearchHit] = []
        for r in response.results:
            hits.append(
                SearchHit(
                    title=r.title or "",
                    url=r.url or "",
                    text=r.text or "",
                    summary=r.summary or "",
                    published_date=r.published_date,
                    author=r.author,
                )
            )
        return hits
