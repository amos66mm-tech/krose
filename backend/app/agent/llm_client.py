"""遵循 OpenAI API 协议的 LLM 客户端，可指向 OpenAI 官方或任意兼容供应商（DeepSeek/Moonshot/vLLM/OpenRouter 等）。"""
from __future__ import annotations

import json
import logging
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

EXTRACTION_SYSTEM_PROMPT = (
    "你是一个严谨的数据抽取助手，任务是从给定的网页文本片段中抽取结构化信息。"
    "只依据给出的文本作答，不要编造未出现的数字或事实；无法确定时把 found 设为 false。"
    "必须只输出一个合法 JSON 对象，不要输出任何多余文字、注释或 markdown 代码块标记。"
)


class LLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.llm_api_key
        self._base_url = settings.llm_base_url
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature
        self._client = None
        if self._api_key:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    def _chat(self, system_prompt: str, user_content: str) -> str:
        if not self._client:
            raise RuntimeError("LLM client 未配置 LLM_API_KEY")
        completion = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return completion.choices[0].message.content or "{}"

    def extract(self, schema: Type[T], *, context_label: str, raw_text: str, extra_instructions: str = "") -> T | None:
        """把网页文本喂给 LLM，让它按 schema 抽取结构化字段。"""
        if not raw_text.strip():
            return None
        schema_hint = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        user_content = (
            f"资料来源：{context_label}\n"
            f"{extra_instructions}\n"
            f"目标 JSON Schema（仅供参考字段含义，输出时不要包含 schema 本身）：\n{schema_hint}\n\n"
            f"原始文本：\n{raw_text[:4000]}"
        )
        try:
            raw = self._chat(EXTRACTION_SYSTEM_PROMPT, user_content)
            data = json.loads(raw)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("LLM 抽取解析失败 (%s): %s", context_label, exc)
            return None
