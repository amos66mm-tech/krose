"""
初始种子数据：目标国家 + 该国常见礼品卡交易 App + 通用礼品卡种类。

这份列表只是一个「可编辑的起点」，用于让面板开箱即有数据可看、Agent 开箱即有抓取目标。
生产环境中你可以随时通过数据库或后续的管理接口增删平台/国家（例如新增肯尼亚、贝宁、科特迪瓦等）。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from . import models

COUNTRIES = [
    dict(code="NG", name_zh="尼日利亚", name_en="Nigeria", currency_code="NGN", flag_emoji="🇳🇬"),
    dict(code="GH", name_zh="加纳", name_en="Ghana", currency_code="GHS", flag_emoji="🇬🇭"),
    dict(code="CM", name_zh="喀麦隆", name_en="Cameroon", currency_code="XAF", flag_emoji="🇨🇲"),
]

# country_code -> list of platforms
PLATFORMS: dict[str, list[dict]] = {
    "NG": [
        dict(slug="prestmit", name="Prestmit", website="https://prestmit.io",
             twitter_handle="prestmit_io", instagram_handle="prestmit.io", notes="综合数字资产交易平台，支持礼品卡/加密货币/话费变现"),
        dict(slug="cardtonic", name="Cardtonic", website="https://cardtonic.com",
             twitter_handle="cardtonic", instagram_handle="cardtonic", notes="尼日利亚/加纳双市场礼品卡交易平台，支持虚拟美元卡"),
        dict(slug="legitcards", name="LegitCards", website="https://legitcards.com",
             notes="以大额礼品卡高汇率著称的精简运营平台"),
        dict(slug="sellcaddy", name="Sellcaddy", website="https://sellcaddy.com",
             notes="尼日利亚本地礼品卡回收平台"),
        dict(slug="chapmall", name="Chapmall", website="https://chapmall.com",
             notes="尼日利亚礼品卡/话费/账单支付一体化平台"),
    ],
    "GH": [
        dict(slug="cardtonic-gh", name="Cardtonic (Ghana)", website="https://cardtonic.com",
             twitter_handle="cardtonic", instagram_handle="cardtonic", notes="Cardtonic 加纳市场"),
        dict(slug="prestmit-gh", name="Prestmit (Ghana)", website="https://prestmit.io",
             twitter_handle="prestmit_io", notes="Prestmit 加纳市场，支持 Cedis 提现"),
        dict(slug="kolacash-gh", name="KolaCash (Ghana)", website="https://www.kolacash.com/ghana.html",
             notes="通过 MTN MoMo 移动钱包结算的礼品卡交易平台"),
        dict(slug="sogo", name="Sogo", website="https://sogo.africa",
             notes="尼日利亚/加纳礼品卡兑现平台，支持银行账户提现"),
    ],
    "CM": [
        dict(slug="kolacash-cm", name="KolaCash (Cameroon)", website="https://www.kolacash.com/cameroon.html",
             notes="喀麦隆礼品卡交易，支持 MTN MoMo / Orange Money 提现"),
        dict(slug="sellcardnow-cm", name="SellCardNow (Cameroon)", website="https://sellcardnow.com/cameroon",
             notes="覆盖多个非洲国家的统一礼品卡结算平台，喀麦隆走 XAF 通道"),
    ],
}

GIFT_CARD_TYPES = [
    dict(slug="amazon", name="Amazon", icon="🛒"),
    dict(slug="apple-itunes", name="Apple / iTunes", icon="🍎"),
    dict(slug="steam", name="Steam", icon="🎮"),
    dict(slug="google-play", name="Google Play", icon="▶️"),
    dict(slug="razer-gold", name="Razer Gold", icon="🐍"),
    dict(slug="vanilla-visa", name="Vanilla / Visa", icon="💳"),
    dict(slug="xbox", name="Xbox", icon="🕹️"),
    dict(slug="playstation", name="PlayStation", icon="🎮"),
    dict(slug="ebay", name="eBay", icon="🏷️"),
    dict(slug="walmart", name="Walmart", icon="🏬"),
    dict(slug="sephora", name="Sephora", icon="💄"),
    dict(slug="american-express", name="American Express", icon="💵"),
]


def run_seed(db: Session) -> None:
    country_by_code: dict[str, models.Country] = {c.code: c for c in db.query(models.Country).all()}
    for c in COUNTRIES:
        if c["code"] not in country_by_code:
            country = models.Country(**c)
            db.add(country)
            db.flush()
            country_by_code[c["code"]] = country

    existing_platform_keys = {
        (p.country_id, p.slug) for p in db.query(models.Platform).all()
    }
    for country_code, platforms in PLATFORMS.items():
        country = country_by_code[country_code]
        for p in platforms:
            key = (country.id, p["slug"])
            if key not in existing_platform_keys:
                db.add(models.Platform(country_id=country.id, **p))

    existing_card_slugs = {g.slug for g in db.query(models.GiftCardType).all()}
    for g in GIFT_CARD_TYPES:
        if g["slug"] not in existing_card_slugs:
            db.add(models.GiftCardType(**g))

    db.commit()
