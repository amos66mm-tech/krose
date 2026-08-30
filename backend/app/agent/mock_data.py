"""
演示/开发模式下的模拟数据生成器。

当尚未配置 EXA_API_KEY / LLM_API_KEY 时，面板依然可以展示一份「看起来真实」的数据，
方便你在接入真实 Key 之前先把数据库结构、API、前端面板跑通。
一旦在 Cursor Dashboard -> Secrets 里配置好两把 Key，`Settings.is_live_mode` 会自动变为 True，
后续采集会切换为真实的 Exa 搜索 + LLM 抽取。
"""
from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone

MOCK_TAG = "[DEMO] "

_ACTIVITY_TEMPLATES = [
    ("promotion", "{platform} 上线周末加价活动，{card} 回收价临时上浮 3%-5%"),
    ("promotion", "{platform} 邀请好友注册可得额外现金奖励"),
    ("announcement", "{platform} 新增 {card} 礼品卡支持，覆盖更多面额"),
    ("policy", "{platform} 更新实名认证与限额政策"),
    ("outage", "{platform} 系统维护通知，预计 2 小时内恢复交易"),
    ("announcement", "{platform} 上线新版 App，优化提现到账速度"),
]

_SOCIAL_TEMPLATES = [
    ("twitter", "positive", "刚刚以超预期的价格卖出了 {card} 礼品卡，到账很快！"),
    ("twitter", "neutral", "{platform} 今日 {card} 汇率更新，欢迎大家来对比。"),
    ("instagram", "positive", "{platform} 本周抽奖活动开启，参与就有机会赢现金奖励 🎉"),
    ("facebook", "negative", "有用户反馈 {platform} 今天到账稍有延迟，官方正在处理。"),
    ("twitter", "positive", "{platform} 上线新功能：一键比价，卖家再也不用到处问价了。"),
]


def _stable_seed(*parts: str) -> random.Random:
    h = hashlib.sha256("::".join(parts).encode()).hexdigest()
    return random.Random(int(h[:12], 16))


def mock_price_point(platform_name: str, card_name: str, base_seed: str, day_offset: int = 0) -> dict:
    rnd = _stable_seed(platform_name, card_name, base_seed)
    base_rate = rnd.uniform(62, 88)
    daily_noise = _stable_seed(platform_name, card_name, base_seed, str(day_offset)).uniform(-2.5, 2.5)
    rate = round(max(35.0, min(95.0, base_rate + daily_noise)), 2)
    return {
        "rate_percent": rate,
        "unit_description": "per $100 e-code",
        "source_title": f"{MOCK_TAG}{platform_name} 官方汇率页（模拟）",
        "source_url": "",
        "raw_snippet": f"{MOCK_TAG}模拟生成：{platform_name} 的 {card_name} 参考回收价",
    }


def mock_activity(platform_name: str, seed_extra: str, card_pool: list[str]) -> dict:
    rnd = _stable_seed(platform_name, seed_extra, "activity")
    activity_type, template = rnd.choice(_ACTIVITY_TEMPLATES)
    card = rnd.choice(card_pool) if card_pool else "礼品卡"
    title = template.format(platform=platform_name, card=card)
    published_at = datetime.now(timezone.utc) - timedelta(hours=rnd.randint(1, 96))
    return {
        "activity_type": activity_type,
        "title": MOCK_TAG + title,
        "summary": f"{MOCK_TAG}系统根据历史模式模拟生成的示例动态，接入真实 API Key 后将替换为真实抓取内容。",
        "source_url": "",
        "published_at": published_at,
    }


def mock_social_post(platform_name: str, seed_extra: str, card_pool: list[str], handle: str = "") -> dict:
    rnd = _stable_seed(platform_name, seed_extra, "social")
    network, sentiment, template = rnd.choice(_SOCIAL_TEMPLATES)
    card = rnd.choice(card_pool) if card_pool else "礼品卡"
    content = template.format(platform=platform_name, card=card)
    published_at = datetime.now(timezone.utc) - timedelta(hours=rnd.randint(1, 72))
    return {
        "network": network,
        "author": handle or f"@{platform_name.lower().replace(' ', '')}",
        "content": MOCK_TAG + content,
        "url": "",
        "sentiment": sentiment,
        "engagement_score": round(rnd.uniform(5, 500), 1),
        "published_at": published_at,
    }
