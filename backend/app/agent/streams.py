"""
宽网采集：不预设「用户需要的是价格还是活动」，而是按主题撒网，把打到的原文全部归档。

系统 Watch 分成几类 stream：
- market_scan          市场全景（有哪些 App、怎么卖卡、口碑）
- community            论坛/Reddit/Telegram 等卖方社区
- news_risk            监管、跑路、诈骗、停服
- competitor_discovery 尚未入库的新平台/替代品
- rates                回收价相关材料（作为原文，而不是 平台×卡种 笛卡尔积）
- platform_watch       已知平台的官网/提及
- custom               用户自己加的网
"""
from __future__ import annotations

from dataclasses import dataclass

from .. import models


@dataclass(frozen=True)
class StreamSpec:
    key: str
    label: str
    query: str
    stream: str
    country_code: str | None = None
    include_domains: str = ""
    exa_category: str = ""
    notes: str = ""


COUNTRY_QUERIES: dict[str, dict[str, str]] = {
    "NG": {
        "name": "Nigeria",
        "currency": "naira NGN",
        "payout": "bank transfer or Opay or PalmPay",
        "forum": "Nairaland",
    },
    "GH": {
        "name": "Ghana",
        "currency": "cedi GHS",
        "payout": "MTN MoMo",
        "forum": "Reddit Ghana",
    },
    "CM": {
        "name": "Cameroon",
        "currency": "CFA XAF",
        "payout": "MTN MoMo or Orange Money",
        "forum": "Facebook groups",
    },
}


def system_stream_specs() -> list[StreamSpec]:
    specs: list[StreamSpec] = []
    for code, meta in COUNTRY_QUERIES.items():
        name = meta["name"]
        specs.extend(
            [
                StreamSpec(
                    key=f"market:{code}:landscape",
                    label=f"{name} 礼品卡交易市场全景",
                    query=f"gift card trading app {name} sell Amazon iTunes Steam rate 2024 2025",
                    stream="market_scan",
                    country_code=code,
                    notes="宽网：这个国家现在有哪些收卡 App、卖方怎么讨论它们",
                ),
                StreamSpec(
                    key=f"market:{code}:howto",
                    label=f"{name} 卖卡教程与坑点",
                    query=f"how to sell gift card in {name} {meta['payout']} delay rejected",
                    stream="market_scan",
                    country_code=code,
                ),
                StreamSpec(
                    key=f"community:{code}:forum",
                    label=f"{name} 卖方社区讨论",
                    query=f"{meta['forum']} gift card rate {name} Prestmit Cardtonic scam OR legit",
                    stream="community",
                    country_code=code,
                ),
                StreamSpec(
                    key=f"community:{code}:telegram",
                    label=f"{name} Telegram/社群",
                    query=f"telegram group sell gift card {name} rate list",
                    stream="community",
                    country_code=code,
                    exa_category="social",
                ),
                StreamSpec(
                    key=f"risk:{code}:scam",
                    label=f"{name} 诈骗/跑路/拒付",
                    query=f"{name} gift card scam OR fraud OR delayed payment OR platform shutdown",
                    stream="news_risk",
                    country_code=code,
                ),
                StreamSpec(
                    key=f"discover:{code}:newapps",
                    label=f"{name} 新平台/替代品",
                    query=f"best gift card buyer {name} alternative to Cardtonic Prestmit new app 2025",
                    stream="competitor_discovery",
                    country_code=code,
                ),
                StreamSpec(
                    key=f"rates:{code}:overview",
                    label=f"{name} 回收价材料",
                    query=f"{name} gift card rate today Amazon Apple Steam Google Play {meta['currency']}",
                    stream="rates",
                    country_code=code,
                ),
            ]
        )

    specs.append(
        StreamSpec(
            key="risk:regional:regulation",
            label="西非监管/支付政策",
            query="CBN Nigeria gift card crypto regulation MTN MoMo Ghana payment gift card",
            stream="news_risk",
            notes="支付通道和监管变化会直接影响卖方能不能收到钱",
        )
    )
    return specs


def platform_watch_spec(platform: models.Platform) -> StreamSpec:
    country = platform.country
    country_name = country.name_en if country else ""
    country_code = country.code if country else None
    handles = " ".join(filter(None, [platform.twitter_handle, platform.instagram_handle, platform.facebook_handle]))
    query = f'"{platform.name}" gift card {country_name} {handles} rate OR review OR announcement'.strip()
    domains = ""
    if platform.website:
        host = platform.website.split("//")[-1].split("/")[0]
        domains = host
    return StreamSpec(
        key=f"platform:{platform.slug}",
        label=f"{platform.name} 提及与官网",
        query=query,
        stream="platform_watch",
        country_code=country_code,
        include_domains=domains,
        notes=platform.notes or "",
    )
