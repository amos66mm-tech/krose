"""演示语料：没有 Exa Key 时，用一批多样化的「像真的一样」的公开材料填充情报库。

目的不是伪造报价矩阵，而是让用户立刻能搜索、按实体浏览、从投诉/新平台/监管里自己发现线索。
真实采集路径永远不会把这些文档写进库。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .. import models
from .exa_client import SearchHit
from .extract_schemas import DocumentOrganization, ExtractedEntityMention, ExtractedFact, ExtractedPriceMention
from .ingest import ingest_hit
from .organize import apply_organization, upsert_entity


@dataclass
class DemoItem:
    title: str
    url: str
    text: str
    summary_zh: str
    stream: str
    country_code: str | None
    source_kind: str
    doc_type: str
    tags: list[str]
    entities: list[tuple[str, str]]
    facts: list[tuple[str, str]]
    sentiment: str = "neutral"
    days_ago: int = 3
    author: str = ""
    prices: list[dict] = field(default_factory=list)
    relevance: float = 0.8


def _items() -> list[DemoItem]:
    return [
        DemoItem(
            title="Nigeria gift card rates today: Amazon, iTunes, Steam (March comparison)",
            url="https://rateswatch.africa/ng/gift-card-rates-today",
            source_kind="web",
            stream="rates",
            country_code="NG",
            doc_type="rate_list",
            tags=["amazon", "itunes", "steam", "rates"],
            entities=[("Prestmit", "platform"), ("Cardtonic", "platform"), ("Amazon", "card_type"), ("Apple / iTunes", "card_type"), ("Steam", "card_type")],
            facts=[
                ("Prestmit 今日 Amazon e-code 约 ₦1,180 / $1（约 78.7%）", "rate"),
                ("Cardtonic Amazon 报价区间 ₦1,150–1,210 / $1", "rate"),
                ("Steam 两家都明显低于 Amazon", "rate"),
            ],
            prices=[
                {"platform_name": "Prestmit", "card_name": "Amazon", "rate_percent": 78.7, "currency": "NGN"},
                {"platform_name": "Cardtonic", "card_name": "Amazon", "rate_percent": 78.7, "currency": "NGN"},
                {"platform_name": "Prestmit", "card_name": "Steam", "rate_percent": 72.4, "currency": "NGN"},
                {"platform_name": "Cardtonic", "card_name": "Apple / iTunes", "rate_percent": 76.0, "currency": "NGN"},
            ],
            days_ago=0,
            text=(
                "Gift card sellers in Lagos are comparing buy rates again this week. "
                "Prestmit's public calculator listed Amazon e-code around ₦1,180 per dollar of face value, "
                "while Cardtonic's range sat between ₦1,150 and ₦1,210 depending on card class. "
                "iTunes/Apple rates clustered near 76% of face after FX conversion. Steam remains weaker — "
                "Prestmit quoted the equivalent of 72.4%. Physical Vanilla/Visa cards were described as "
                "'case by case' and several sellers warned that high-value Vanilla is frequently rejected. "
                "Payouts: Prestmit bank transfer usually same day, Cardtonic similar but weekend KYC queues exist."
            ),
            summary_zh="尼日利亚公开比价材料：Amazon 仍是主流高价卡种，Prestmit 与 Cardtonic 价差不大；Steam 更低；Vanillla/Visa 容易拒卡。",
        ),
        DemoItem(
            title="Who still uses Prestmit? Payout delayed 36 hours (Nairaland)",
            url="https://www.nairaland.com/threads/prestmit-payout-delay-gift-card",
            source_kind="forum",
            stream="community",
            country_code="NG",
            doc_type="complaint",
            tags=["payout-delay", "prestmit", "nairaland"],
            entities=[("Prestmit", "platform"), ("Opay", "payment_rail")],
            facts=[
                ("多名卖家称周末提交的单会拖到周一", "payout"),
                ("客服把延迟归咎于银行/Opay 通道", "warning"),
            ],
            sentiment="negative",
            days_ago=1,
            author="nairaland/giftcardplug",
            text=(
                "Thread: I traded $200 Amazon on Prestmit Friday night. Status stuck on 'processing' for 36 hours. "
                "Support said the Opay/bank corridor was congested. Two other users chimed in that weekend trades "
                "often land Monday. One user said Cardtonic paid them in 20 minutes the same weekend. "
                "Nobody called it a scam — they say the company still pays — but several people moved their "
                "high-value cards elsewhere when they need cash the same day. Admin closed with 'use their live chat, don't panic'."
            ),
            summary_zh="Nairaland 投诉帖：Prestmit 周末出金可拖 36 小时，用户并未定性诈骗，但急需现金的人会改去 Cardtonic。",
        ),
        DemoItem(
            title="Cardtonic vs Prestmit vs LegitCards — which gift card buyer is legit in 2025?",
            url="https://www.reddit.com/r/Nigeria/comments/cardtonic-vs-prestmit",
            source_kind="forum",
            stream="community",
            country_code="NG",
            doc_type="forum_thread",
            tags=["trust", "amazon"],
            entities=[("Cardtonic", "platform"), ("Prestmit", "platform"), ("LegitCards", "platform"), ("FlashCards NG", "platform")],
            facts=[
                ("Reddit 用户认为 Cardtonic 品牌更老、客服更稳", "opinion"),
                ("LegitCards 被指汇率高但额度/卡种更挑", "opinion"),
            ],
            sentiment="mixed",
            days_ago=4,
            text=(
                "r/Nigeria discussion. Cardtonic is described as the 'default' because of years of ads and a virtual dollar card product. "
                "Prestmit is called faster on crypto + airtime + gift cards in one app. LegitCards allegedly posts higher Amazon rates "
                "but rejects more cards and has thinner social proof. Several comments warn that Telegram 'rate list' broadcasts "
                "with random bank accounts are a common scam pattern — always cash out inside a known app, never to a personal account "
                "sent in DM. One commenter mentioned a new app called FlashCards NG offering +2% above Cardtonic for first trade."
            ),
            summary_zh="Reddit 对比帖：Cardtonic 更稳，Prestmit 更全能，LegitCards 汇率高但挑剔。有人提到未入库新 App「FlashCards NG」用首单加价获客。出现私聊转账诈骗手法提醒。",
        ),
        DemoItem(
            title="FlashCards NG launches in Lagos — first-trade bonus on Amazon",
            url="https://techpoint.africa/2026/08/flashcards-ng-gift-card-app",
            source_kind="news",
            stream="competitor_discovery",
            country_code="NG",
            doc_type="competitor",
            tags=["competitor", "amazon", "bonus"],
            entities=[("FlashCards NG", "platform"), ("Amazon", "card_type"), ("Lagos", "place")],
            facts=[
                ("FlashCards NG 宣称首单 Amazon 加 2 个百分点", "event"),
                ("目前只有 Lagos 银行账户出金，尚未做 KYC 等级说明", "warning"),
            ],
            prices=[{"platform_name": "FlashCards NG", "card_name": "Amazon", "rate_percent": 80.5, "currency": "NGN"}],
            days_ago=6,
            text=(
                "A Lagos-based startup branded FlashCards NG started taking Amazon and iTunes e-codes last month. "
                "Their landing page advertises 'Cardtonic rate +2% on your first Amazon trade' and bank payout in under an hour. "
                "They are not on Google Play as a verified merchant yet; downloads currently go through a website PWA. "
                "Sellers in WhatsApp groups are split: some chased the bonus, others refuse to try an app with no NIN/BVN statement "
                "and only a handful of Twitter followers. No regulator mention. This is the kind of new buyer that does not appear "
                "in a pre-seeded platform list."
            ),
            summary_zh="新发现的买家 FlashCards NG：用首单 Amazon +2% 拉新，尚无应用商店认证和清晰 KYC。这是种子名单里没有的平台。",
        ),
        DemoItem(
            title="Telegram: FREE RATE LIST Nigeria — send card to this account",
            url="https://t.me/ng_giftcard_rates_free/2188",
            source_kind="social",
            stream="community",
            country_code="NG",
            doc_type="scam_report",
            tags=["scam", "telegram", "amazon"],
            entities=[("Telegram", "topic"), ("Amazon", "card_type")],
            facts=[
                ("广播账号要卖方把卡密私发给个人账户", "warning"),
                ("承诺高于 Cardtonic 4% 的价格", "warning"),
            ],
            sentiment="negative",
            days_ago=2,
            author="@ng_giftcard_rates_free",
            text=(
                "Forwarded message: TODAY AMAZON 84% UNLOCKED. Send code to 0813-XXX now, we pay 10 minutes. "
                "Better than Cardtonic. Admin will never ask you to install an app. Several replies later a user posted "
                "'this is the third time this handle changed username after people got burned'. Pattern: above-market rate, "
                "no in-app escrow, payment to personal bank, then block. Relevant as a risk object even if it is not a real buyer."
            ),
            summary_zh="Telegram 假汇率广播：用高于市价的 Amazon 84% 诱使把卡密打到个人账户。情报价值在于识别诈骗模式，而不是当成真实报价。",
        ),
        DemoItem(
            title="CBN reiterates rules on unlicensed payment and virtual dollar products",
            url="https://www.punchng.com/cbn-virtual-dollar-gift-card-payments",
            source_kind="news",
            stream="news_risk",
            country_code="NG",
            doc_type="policy",
            tags=["kyc", "cbn", "policy"],
            entities=[("CBN", "org"), ("Cardtonic", "platform")],
            facts=[
                ("CBN 再次强调无牌支付与虚拟美元产品的合规口径", "event"),
                ("可能影响带虚拟卡功能的礼品卡平台的营销话术", "warning"),
            ],
            days_ago=8,
            text=(
                "The Central Bank of Nigeria restated that only licensed operators may market certain payment products. "
                "The article does not ban gift card trading, but it flags virtual dollar cards bundled with gift-card apps "
                "as an area where advertising has gotten ahead of licences. Cardtonic is mentioned as an example of a "
                "consumer brand that also sells a dollar card, not as a target of enforcement. Sellers should watch whether "
                "payout bank corridors tighten, because that hits cash-out speed more than posted rates."
            ),
            summary_zh="CBN 合规新闻：未禁礼品卡买卖，但点名虚拟美元卡营销。对卖方的实际影响可能是出金通道变慢，而不一定是汇率。",
        ),
        DemoItem(
            title="How to sell Amazon gift cards in Nigeria without getting reversed",
            url="https://www.nairaland.com/how-to-sell-amazon-gift-card-nigeria",
            source_kind="forum",
            stream="market_scan",
            country_code="NG",
            doc_type="how_to",
            tags=["amazon", "kyc", "how-to"],
            entities=[("Amazon", "card_type"), ("Prestmit", "platform"), ("Cardtonic", "platform"), ("BVN", "topic")],
            facts=[
                ("卖方建议先完成 NIN/BVN 再走大额", "warning"),
                ("截图收据、避免截图卡密发到群里", "warning"),
            ],
            days_ago=12,
            text=(
                "A long Nairaland guide: 1) Complete KYC (NIN/BVN) on the app before large trades. "
                "2) Prefer e-code over receipt photos when the app allows it. 3) Never paste the full code in a WhatsApp group. "
                "4) Check whether the card is 'receipt required' — Amazon often is. 5) If a platform suddenly offers 90%, walk away. "
                "Prestmit and Cardtonic both appear as 'known' options. The guide also lists typical rejection reasons: "
                "wrong country card, already redeemed, blurry receipt, VPN on the buyer side."
            ),
            summary_zh="卖方教程：KYC、收据、不要把卡密发群、警惕 90% 超高价。同时列出常见拒卡原因，是运营论坛内容的好原料。",
        ),
        DemoItem(
            title="Chapmall weekend promo: extra 1.5% on iTunes",
            url="https://chapmall.com/blog/weekend-itunes-promo",
            source_kind="web",
            stream="platform_watch",
            country_code="NG",
            doc_type="promotion",
            tags=["promotion", "itunes"],
            entities=[("Chapmall", "platform"), ("Apple / iTunes", "card_type")],
            facts=[("Chapmall 周末 iTunes 加价 1.5 个百分点，周日 23:59 结束", "event")],
            prices=[{"platform_name": "Chapmall", "card_name": "Apple / iTunes", "rate_percent": 77.5, "currency": "NGN"}],
            sentiment="positive",
            days_ago=1,
            text=(
                "Chapmall announced a weekend boost on Apple/iTunes e-codes: extra 1.5 percentage points until Sunday 23:59 WAT. "
                "The blog post says the promo does not apply to physical cards or to cards below $50. Payout remains to Nigerian banks."
            ),
            summary_zh="Chapmall 官方周末活动：iTunes e-code 加 1.5 个百分点，排除实物卡和小面额。",
        ),
        DemoItem(
            title="Sellcaddy Amazon rate quietly dropped this week, sellers say",
            url="https://nairametrics.com/sellcaddy-amazon-rate-drop",
            source_kind="news",
            stream="rates",
            country_code="NG",
            doc_type="news",
            tags=["amazon", "rates"],
            entities=[("Sellcaddy", "platform"), ("Amazon", "card_type")],
            facts=[("卖家观察 Sellcaddy Amazon 回收价本周下调约 2 个百分点", "rate")],
            prices=[{"platform_name": "Sellcaddy", "card_name": "Amazon", "rate_percent": 74.0, "currency": "NGN"}],
            sentiment="negative",
            days_ago=3,
            text=(
                "Informal reports from seller groups claim Sellcaddy cut Amazon e-code payouts by about two points compared "
                "with last week, now near 74% of face after naira conversion. The company did not publish a blog post. "
                "Some sellers speculate inventory risk after a US-side Amazon claim spike. Unconfirmed."
            ),
            summary_zh="非正式消息：Sellcaddy 的 Amazon 价本周大约下调 2 个点。公司未发公告，属于需要交叉验证的信号。",
        ),
        DemoItem(
            title="LegitCards review: high rates, slow support, strict card class",
            url="https://www.trustpilot.com/review/legitcards.com",
            source_kind="web",
            stream="platform_watch",
            country_code="NG",
            doc_type="review",
            tags=["trust", "review"],
            entities=[("LegitCards", "platform")],
            facts=[
                ("好评集中在高汇率", "opinion"),
                ("差评集中在客服慢和拒卡不说明原因", "complaint"),
            ],
            sentiment="mixed",
            days_ago=9,
            text=(
                "Mixed Trustpilot-style reviews. Five-star posts praise Amazon rates beating Cardtonic. One-star posts "
                "say support takes a day to reply and rejected a $500 Vanilla without a reason code. "
                "Useful as a trust signal, not as a live price feed."
            ),
            summary_zh="LegitCards 口碑两极：汇率吸引人，客服和拒卡透明度差。适合做信任分，而不是当行情源。",
        ),
        DemoItem(
            title="Ghana: selling gift cards via MTN MoMo — KolaCash vs Cardtonic",
            url="https://www.reddit.com/r/Ghana/comments/momo-gift-card-kolacash",
            source_kind="forum",
            stream="community",
            country_code="GH",
            doc_type="forum_thread",
            tags=["momo", "rates"],
            entities=[("KolaCash (Ghana)", "platform"), ("Cardtonic (Ghana)", "platform"), ("MTN MoMo", "payment_rail"), ("Ghana", "place")],
            facts=[
                ("加纳卖方更关心 MoMo 是否当天到，而不是多 0.5% 汇率", "opinion"),
                ("KolaCash 被指 MoMo 通道更熟，Cardtonic 汇率有时更高", "opinion"),
            ],
            days_ago=5,
            text=(
                "Ghanaian sellers argue that MTN MoMo reliability beats a slightly higher posted rate. "
                "KolaCash is repeatedly mentioned as 'they know MoMo'. Cardtonic Ghana sometimes quotes better Amazon "
                "but a few users reported MoMo name-mismatch failures. Sogo is mentioned once as an alternative with bank payout."
            ),
            summary_zh="加纳社区：出金通道（MTN MoMo）比多 0.5% 汇率更重要。KolaCash 通道口碑好，Cardtonic 有时价更高但会因户名失败。",
        ),
        DemoItem(
            title="MTN MoMo limits: why your gift card payout is split",
            url="https://www.kolacash.com/ghana.html#momo-limits",
            source_kind="web",
            stream="news_risk",
            country_code="GH",
            doc_type="policy",
            tags=["momo", "payout-delay"],
            entities=[("MTN MoMo", "payment_rail"), ("KolaCash (Ghana)", "platform")],
            facts=[("MoMo 日限额会导致大额礼品卡拆成多笔出金", "warning")],
            days_ago=7,
            text=(
                "Explainer: Ghana MoMo wallets have daily receive limits depending on KYC tier. "
                "A $300 Amazon cash-out can be split across two days. Sellers who need the full amount immediately "
                "should use a bank payout product instead of MoMo. This is not a platform scam, it is rail infrastructure."
            ),
            summary_zh="加纳 MoMo 日限额会把大额出金拆单。看起来像平台拖款，实际是支付轨道限制——这类信息很容易被误判为诈骗。",
        ),
        DemoItem(
            title="Cardtonic Ghana Amazon rate board screenshot discussion",
            url="https://twitter.com/giftcardghana/status/rates-aug",
            source_kind="social",
            stream="rates",
            country_code="GH",
            doc_type="rate_list",
            tags=["amazon", "rates"],
            entities=[("Cardtonic (Ghana)", "platform"), ("Amazon", "card_type")],
            facts=[("截图显示 Cardtonic Ghana Amazon 约 78%", "rate")],
            prices=[{"platform_name": "Cardtonic (Ghana)", "card_name": "Amazon", "rate_percent": 78.0, "currency": "GHS"}],
            days_ago=0,
            author="@giftcardghana",
            text=(
                "Screenshot tweet: Cardtonic Ghana Amazon 78%, iTunes 74%, Steam 70%. Comments ask if physical cards differ. "
                "Author says e-code only. Not an official Cardtonic account."
            ),
            summary_zh="非官方推文截图：Cardtonic Ghana 的 Amazon 约 78%。需要和官网计算器交叉验证。",
        ),
        DemoItem(
            title="Prestmit now paying Ghana sellers in GHS via bank",
            url="https://prestmit.io/blog/ghana-bank-payout",
            source_kind="web",
            stream="platform_watch",
            country_code="GH",
            doc_type="news",
            tags=["payout"],
            entities=[("Prestmit (Ghana)", "platform")],
            facts=[("Prestmit 宣布加纳支持银行 GHS 出金，不再只靠第三方", "event")],
            sentiment="positive",
            days_ago=11,
            text=(
                "Prestmit blog: Ghana bank payout in GHS is live for verified accounts. "
                "They still support the existing MoMo flow. The post is product news, not a rate change."
            ),
            summary_zh="Prestmit 加纳银行出金上线。这是产品/通道情报，不是价格情报——但卖方会据此决定去哪家。",
        ),
        DemoItem(
            title="Cameroon: SellCardNow vs KolaCash on Orange Money",
            url="https://facebook.com/groups/yaounde.deals/posts/orange-money-giftcard",
            source_kind="forum",
            stream="community",
            country_code="CM",
            doc_type="forum_thread",
            tags=["orange-money", "momo"],
            entities=[("SellCardNow (Cameroon)", "platform"), ("KolaCash (Cameroon)", "platform"), ("Orange Money", "payment_rail"), ("MTN MoMo", "payment_rail")],
            facts=[
                ("Yaoundé 群里有人说 Orange Money 比 MTN 更容易被平台拒绝户名", "warning"),
                ("SellCardNow 覆盖多国，KolaCash 更本地", "opinion"),
            ],
            days_ago=6,
            text=(
                "Facebook group (Yaoundé): sellers debating Orange Money vs MTN MoMo cash-out. "
                "SellCardNow is described as a pan-African site that sometimes takes longer. KolaCash Cameroon is 'local but smaller limits'. "
                "One user said a $100 Steam card was declined because the Orange Money name did not match the ID on file."
            ),
            summary_zh="喀麦隆社群：出金方式（Orange Money / MTN）和户名匹配，比选择哪家平台更常被讨论。",
        ),
        DemoItem(
            title="KolaCash Cameroon rate note: Steam and Razer weaker than Amazon",
            url="https://www.kolacash.com/cameroon.html",
            source_kind="web",
            stream="rates",
            country_code="CM",
            doc_type="rate_list",
            tags=["steam", "amazon", "razer-gold"],
            entities=[("KolaCash (Cameroon)", "platform"), ("Amazon", "card_type"), ("Steam", "card_type"), ("Razer Gold", "card_type")],
            facts=[("喀麦隆站 Amazon 明显高于 Steam / Razer", "rate")],
            prices=[
                {"platform_name": "KolaCash (Cameroon)", "card_name": "Amazon", "rate_percent": 73.0, "currency": "XAF"},
                {"platform_name": "KolaCash (Cameroon)", "card_name": "Steam", "rate_percent": 66.0, "currency": "XAF"},
            ],
            days_ago=2,
            text=(
                "KolaCash Cameroon page copy lists indicative payouts: Amazon stronger than Steam and Razer Gold. "
                "Exact XAF numbers vary with FX. Physical cards require extra photos. Orange Money and MTN supported."
            ),
            summary_zh="KolaCash 喀麦隆页：Amazon 好于 Steam/Razer。精确 XAF 数字随汇率变，页面只给方向。",
        ),
        DemoItem(
            title="Cameroon gift card scams impersonating SellCardNow support",
            url="https://sellcardnow.com/blog/impersonation-warning",
            source_kind="web",
            stream="news_risk",
            country_code="CM",
            doc_type="scam_report",
            tags=["scam"],
            entities=[("SellCardNow (Cameroon)", "platform")],
            facts=[("假客服在 WhatsApp 上要卡密", "warning")],
            sentiment="negative",
            days_ago=10,
            text=(
                "SellCardNow warned that WhatsApp accounts claiming to be 'SellCardNow Cameroon support' are asking customers "
                "to paste unused codes for 'verification'. Official support never asks for full codes outside the app."
            ),
            summary_zh="SellCardNow 官方防诈骗声明：假客服要卡密。说明即便是平台自己也会成为被冒充对象。",
        ),
        DemoItem(
            title="Sogo.africa positions as bank-payout specialist in Ghana",
            url="https://sogo.africa/blog/bank-payout-ghana",
            source_kind="web",
            stream="platform_watch",
            country_code="GH",
            doc_type="news",
            tags=["payout"],
            entities=[("Sogo", "platform")],
            facts=[("Sogo 强调银行出金，避开 MoMo 限额", "event")],
            sentiment="positive",
            days_ago=14,
            text=(
                "Sogo marketing post: bank account payout in Ghana for verified sellers, targeting people who hit MoMo limits. "
                "No live rate table in the article. Mentions Amazon and iTunes as core cards."
            ),
            summary_zh="Sogo 用「银行出金、避开 MoMo 限额」做差异化。这是产品定位情报，不是报价。",
        ),
        DemoItem(
            title="Google Play gift cards flooding Lagos groups, rates collapsing",
            url="https://www.nairaland.com/google-play-gift-card-rate-collapse",
            source_kind="forum",
            stream="rates",
            country_code="NG",
            doc_type="forum_thread",
            tags=["google-play", "rates"],
            entities=[("Google Play", "card_type"), ("Prestmit", "platform")],
            facts=[("卖方称 Google Play 供给过多，回收价明显弱于 Amazon", "rate")],
            prices=[{"platform_name": "Prestmit", "card_name": "Google Play", "rate_percent": 68.0, "currency": "NGN"}],
            sentiment="negative",
            days_ago=2,
            text=(
                "Sellers say Google Play e-codes are everywhere after a promo wave, so buyer apps dropped payouts. "
                "Prestmit users screenshot ~68% equivalent. Amazon demand is described as still healthy. "
                "Advice in-thread: don't dump Play cards on Friday night."
            ),
            summary_zh="Google Play 供给冲击导致回收价走弱（Prestmit 约 68%）。说明卡种维度的供给冲击是独立情报，不是平台维度。",
        ),
        DemoItem(
            title="Walmart and eBay cards: almost no reliable buyer in West Africa",
            url="https://giftcardforum.africa/walmart-ebay-west-africa",
            source_kind="web",
            stream="market_scan",
            country_code="NG",
            doc_type="how_to",
            tags=["walmart", "ebay"],
            entities=[("Walmart", "card_type"), ("eBay", "card_type")],
            facts=[("Walmart/eBay 在西非几乎没有稳定收卡方，常被拒", "warning")],
            days_ago=20,
            text=(
                "A market note: US grocery/retail cards like Walmart and eBay have thin liquidity on NG/GH/CM apps. "
                "Posted rates if any are stale. Sellers trying to unload them often get 'card class not supported'."
            ),
            summary_zh="Walmart/eBay 在西非流动性极差。价格看板空白不一定是采集失败，可能是市场本身没有这笔买卖。",
        ),
        DemoItem(
            title="Sephora cards spike before holidays, then vanish",
            url="https://www.reddit.com/r/GiftCards/sephora-nigeria-sellers",
            source_kind="forum",
            stream="market_scan",
            country_code="NG",
            doc_type="forum_thread",
            tags=["sephora"],
            entities=[("Sephora", "card_type"), ("Cardtonic", "platform")],
            facts=[("节日前 Sephora 偶尔有报价，平时很多 App 不收", "event")],
            days_ago=18,
            text=(
                "Seasonal liquidity: Sephora appears on Cardtonic around US holidays and disappears. "
                "Not a core card for African cash-out. Still worth watching because holiday spikes create forum traffic."
            ),
            summary_zh="Sephora 是季节性卡种。平时看板空、节日突然有价——这种「时令情报」只有持续收原文才能看见。",
        ),
        DemoItem(
            title="Xbox and PlayStation: gamers sell, rates trail Amazon",
            url="https://nairaland.com/xbox-playstation-gift-card-nigeria",
            source_kind="forum",
            stream="rates",
            country_code="NG",
            doc_type="rate_list",
            tags=["xbox", "playstation"],
            entities=[("Xbox", "card_type"), ("PlayStation", "card_type"), ("Cardtonic", "platform")],
            facts=[("主机卡种有成交但价低于 Amazon", "rate")],
            prices=[
                {"platform_name": "Cardtonic", "card_name": "Xbox", "rate_percent": 70.5, "currency": "NGN"},
                {"platform_name": "Cardtonic", "card_name": "PlayStation", "rate_percent": 71.0, "currency": "NGN"},
            ],
            days_ago=4,
            text=(
                "Gaming cards trade, but buyer demand is thinner than Amazon. Cardtonic screenshots show Xbox ~70.5% and PS ~71%. "
                "Physical vs digital matters; region-locked US cards preferred."
            ),
            summary_zh="Xbox/PS 有市场但弱于 Amazon。实体/数字、区服都会改价。",
        ),
        DemoItem(
            title="Amex gift cards almost never cash out cleanly",
            url="https://www.nairaland.com/amex-gift-card-nigeria-rejected",
            source_kind="forum",
            stream="community",
            country_code="NG",
            doc_type="complaint",
            tags=["amex"],
            entities=[("American Express", "card_type")],
            facts=[("Amex 礼品卡在 NG 平台拒卡率很高", "warning")],
            sentiment="negative",
            days_ago=15,
            text=(
                "Multiple sellers report American Express gift cards rejected on Prestmit and Cardtonic as 'unsupported class'. "
                "A Telegram broker offered 60% then disappeared. Consensus: don't buy Amex expecting West African cash-out."
            ),
            summary_zh="Amex 礼品卡在西非变现极差，甚至引出更低价的场外掮客。负向流动性也是情报。",
        ),
        DemoItem(
            title="Vanilla Visa: high face value, high dispute risk",
            url="https://cardtonic.com/blog/vanilla-visa-requirements",
            source_kind="web",
            stream="platform_watch",
            country_code="NG",
            doc_type="how_to",
            tags=["vanilla", "kyc"],
            entities=[("Vanilla / Visa", "card_type"), ("Cardtonic", "platform")],
            facts=[("Vanilla/Visa 通常要收据+开卡证明，纠纷率高", "warning")],
            days_ago=13,
            text=(
                "Cardtonic help center style post: Vanilla/Visa requires receipt, often a photo of the physical card, "
                "and may be held for review. High dispute rate from original purchasers. Rate looks attractive and then the trade is reversed."
            ),
            summary_zh="Vanilla/Visa 看起来汇率好，但审查和拒付风险高。只看价格看板会误判。",
        ),
        DemoItem(
            title="Razer Gold is a gamer cash-out niche in Ghana",
            url="https://www.kolacash.com/ghana.html#razer",
            source_kind="web",
            stream="rates",
            country_code="GH",
            doc_type="rate_list",
            tags=["razer-gold"],
            entities=[("Razer Gold", "card_type"), ("KolaCash (Ghana)", "platform")],
            facts=[("加纳有少量 Razer Gold 需求", "rate")],
            prices=[{"platform_name": "KolaCash (Ghana)", "card_name": "Razer Gold", "rate_percent": 69.0, "currency": "GHS"}],
            days_ago=5,
            text="KolaCash Ghana lists Razer Gold as supported. Volume comments on Twitter suggest it is lumpy, not daily.",
            summary_zh="Razer Gold 在加纳是有但不大的利基卡种。",
        ),
        DemoItem(
            title="iTunes region mismatch is the #1 silent rejection",
            url="https://prestmit.io/help/itunes-region",
            source_kind="web",
            stream="platform_watch",
            country_code="NG",
            doc_type="how_to",
            tags=["itunes", "kyc"],
            entities=[("Prestmit", "platform"), ("Apple / iTunes", "card_type")],
            facts=[("非美区 iTunes 卡经常被拒且不显示在汇率表上", "warning")],
            days_ago=16,
            text=(
                "Prestmit help: US iTunes/Apple codes only. UK/EU cards are rejected. Sellers who compare 'iTunes rates' "
                "without region are comparing different products."
            ),
            summary_zh="iTunes 区服不匹配是静默拒卡第一名。汇率表上的「iTunes」其实默认美区。",
        ),
        DemoItem(
            title="Why African gift card apps quote naira per dollar instead of percent",
            url="https://rateswatch.africa/explainers/naira-per-dollar",
            source_kind="web",
            stream="market_scan",
            country_code="NG",
            doc_type="how_to",
            tags=["rates", "fx"],
            entities=[("NGN", "topic")],
            facts=[("公开页面多用 ₦/$ 而不是百分比，百分比是后换算的", "opinion")],
            days_ago=21,
            text=(
                "Explainer for operators: landing pages show ₦1,180 / $1 not '78.7%'. Parallel FX vs official FX "
                "changes the implied percent. Any intelligence system that only stores percent without the raw naira figure "
                "throws away the actual market quote."
            ),
            summary_zh="市场原话是 ₦/$，百分比只是换算。情报库必须保留原文数字，不能只存一张百分比表。",
        ),
        DemoItem(
            title="Facebook group 'Lagos Gift Card Sellers' weekly complaint digest",
            url="https://facebook.com/groups/lagos.giftcards/permalink/weekly-complaints",
            source_kind="forum",
            stream="community",
            country_code="NG",
            doc_type="complaint",
            tags=["payout-delay", "scam"],
            entities=[("Prestmit", "platform"), ("Chapmall", "platform"), ("FlashCards NG", "platform")],
            facts=[
                ("本周投诉主题：出金慢、假 Telegram 汇率、新 App 首单加价不兑现", "complaint"),
            ],
            sentiment="negative",
            days_ago=0,
            text=(
                "Weekly roundup compiled by a group moderator: 12 delay complaints (mostly weekend bank), "
                "4 impersonation scams, 2 reports that FlashCards NG first-trade bonus was not applied. "
                "Chapmall promo praised by three people. This is unstructured community signal."
            ),
            summary_zh="拉各斯卖家群周报：出金慢仍是主投诉；新平台 FlashCards NG 被指首单加价未兑现。社区周报往往比官网更早出现信号。",
        ),
        DemoItem(
            title="Ghana SEC-style warning on random investment+giftcard hybrids",
            url="https://citinewsroom.com/ghana-investment-giftcard-warning",
            source_kind="news",
            stream="news_risk",
            country_code="GH",
            doc_type="policy",
            tags=["scam", "policy"],
            entities=[("Ghana", "place")],
            facts=[("监管提醒警惕「投资礼品卡返利」盘子", "warning")],
            sentiment="negative",
            days_ago=17,
            text=(
                "Local news: authorities warn about schemes that mix 'gift card trading desks' with guaranteed weekly returns. "
                "Not aimed at Cardtonic-type buy desks, but sellers get confused. Useful to separate cash-out apps from HYIP clones."
            ),
            summary_zh="加纳新闻：有人打着礼品卡交易旗号做高返利盘子。合格情报系统要能把「收卡台」和「资金盘」分开。",
        ),
        DemoItem(
            title="Steam wallet cards vs Steam gift cards — buyers pay different rates",
            url="https://cardtonic.com/help/steam-types",
            source_kind="web",
            stream="platform_watch",
            country_code="NG",
            doc_type="how_to",
            tags=["steam"],
            entities=[("Cardtonic", "platform"), ("Steam", "card_type")],
            facts=[("Steam wallet 与 Steam gift 在买家那里不是同一个 SKU", "warning")],
            days_ago=19,
            text=(
                "Cardtonic distinguishes Steam wallet codes and Steam gift cards. Wallet codes from some regions are rejected. "
                "A single 'Steam' column on a price board hides this."
            ),
            summary_zh="「Steam」其实至少两种 SKU。只按卡种名存一列价格会把不同商品混在一起。",
        ),
        DemoItem(
            title="Opay and PalmPay as the real cash-out layer in Nigeria",
            url="https://techcabal.com/opay-palmpay-gift-card-payouts",
            source_kind="news",
            stream="market_scan",
            country_code="NG",
            doc_type="news",
            tags=["payout"],
            entities=[("Opay", "payment_rail"), ("PalmPay", "payment_rail"), ("Prestmit", "platform")],
            facts=[("很多「平台到账慢」其实是 Opay/PalmPay/银行走廊的问题", "opinion")],
            days_ago=9,
            text=(
                "Analysis: Nigerian gift-card apps sit on top of Opay, PalmPay and commercial banks. "
                "When those rails hiccup, every buyer looks like they are delaying. Intelligence that only watches the gift-card brand "
                "will mis-attribute rail failures to the trading app."
            ),
            summary_zh="尼日利亚真正的出金层是 Opay/PalmPay/银行。只监控礼品卡品牌会把通道故障误判成平台跑路。",
        ),
        DemoItem(
            title="Cardtonic Instagram: we are hiring agents in Accra",
            url="https://instagram.com/p/cardtonic-accra-agents",
            source_kind="social",
            stream="platform_watch",
            country_code="GH",
            doc_type="social",
            tags=["hiring"],
            entities=[("Cardtonic (Ghana)", "platform"), ("Accra", "place")],
            facts=[("Cardtonic 在阿克拉招线下代理，说明加纳仍在铺渠道", "event")],
            sentiment="positive",
            days_ago=3,
            author="@cardtonic",
            text="Instagram post seeking city agents in Accra to onboard gift-card sellers. Comments ask about current Amazon rate, unanswered.",
            summary_zh="社媒招聘信号：Cardtonic 还在加纳铺代理。评论区在问汇率但官方没回——社媒往往有线索没有数字。",
        ),
        DemoItem(
            title="Is Chapmall the same company as Chapal / CapitaStar? (disambiguation)",
            url="https://rateswatch.africa/disambiguation/chapmall",
            source_kind="web",
            stream="competitor_discovery",
            country_code="NG",
            doc_type="how_to",
            tags=["disambiguation"],
            entities=[("Chapmall", "platform")],
            facts=[("Chapmall 是尼日利亚收卡 App，与新加坡 CapitaStar、其它 Chapal 公司无关", "warning")],
            days_ago=22,
            text=(
                "Name collision note: Chapmall (Nigeria gift cards / bills) is not CapitaStar and not Chapal properties. "
                "Open web search frequently mixes them. An intel system must keep the raw URL so analysts can reject the wrong company."
            ),
            summary_zh="同名消歧：Chapmall ≠ CapitaStar。这就是为什么必须存原文 URL，而不是只存 LLM 抽出来的「公司动态」。",
        ),
        DemoItem(
            title="Weekend bank maintenance in Nigeria hits every gift card desk at once",
            url="https://www.vanguardngr.com/nigeria-bank-weekend-maintenance",
            source_kind="news",
            stream="news_risk",
            country_code="NG",
            doc_type="news",
            tags=["payout-delay"],
            entities=[("Nigeria", "place")],
            facts=[("银行周末维护会造成所有收卡 App 同时到账变慢", "event")],
            days_ago=1,
            text=(
                "National weekend banking maintenance window. Unrelated to gift cards, but seller Telegram groups fill with delay complaints "
                "against Prestmit, Cardtonic and Chapmall at the same time — a fingerprint of rail issues, not a single company failing."
            ),
            summary_zh="全国性银行维护导致多家平台同时被投诉出金慢。这是「跨实体共振」信号，只有把投诉原文放在一起看才会发现。",
        ),
    ]


def seed_demo_corpus(db: Session) -> int:
    if db.query(models.Document).filter(models.Document.is_demo.is_(True)).first():
        return 0

    extra_entities = [
        ("FlashCards NG", "platform", "拉各斯新出现的收卡 App，种子名单里没有", None),
        ("Opay", "payment_rail", "尼日利亚电子钱包/出金通道", "NG"),
        ("PalmPay", "payment_rail", "尼日利亚电子钱包/出金通道", "NG"),
        ("MTN MoMo", "payment_rail", "加纳/喀麦隆移动钱包", None),
        ("Orange Money", "payment_rail", "喀麦隆等市场的移动钱包", "CM"),
        ("CBN", "org", "尼日利亚央行", "NG"),
        ("Telegram", "topic", "场外汇率广播与诈骗高发渠道", None),
        ("BVN", "topic", "尼日利亚银行验证号，KYC 关键字段", "NG"),
        ("NIN", "topic", "尼日利亚国家身份号", "NG"),
        ("Lagos", "place", "尼日利亚卖方最集中的城市", "NG"),
        ("Accra", "place", "加纳卖方集中地", "GH"),
        ("NGN", "topic", "奈拉报价习惯（₦ per $）", "NG"),
    ]
    for name, etype, desc, cc in extra_entities:
        upsert_entity(db, name, etype, description=desc, country_code=cc, is_seeded=False)

    now = datetime.now(timezone.utc)
    created = 0
    for item in _items():
        entities = list(item.entities)

        published = (now - timedelta(days=item.days_ago)).isoformat()
        hit = SearchHit(
            title=item.title,
            url=item.url,
            text=item.text,
            summary=item.text[:400],
            published_date=published,
            author=item.author or None,
        )
        doc, is_new = ingest_hit(
            db,
            hit,
            stream=item.stream,
            query=f"demo:{item.stream}:{item.country_code or 'all'}",
            country_code=item.country_code,
            is_demo=True,
            source_kind=item.source_kind,
        )
        if not is_new:
            continue
        doc.collected_at = now - timedelta(days=item.days_ago)
        doc.last_seen_at = doc.collected_at
        org = DocumentOrganization(
            summary_zh=item.summary_zh,
            doc_type=item.doc_type,  # type: ignore[arg-type]
            tags=item.tags,
            entities=[ExtractedEntityMention(name=n, entity_type=t) for n, t in entities],  # type: ignore[arg-type]
            facts=[ExtractedFact(claim=c, kind=k) for c, k in item.facts],
            prices=[ExtractedPriceMention(**p) for p in item.prices],
            sentiment=item.sentiment,  # type: ignore[arg-type]
            countries=[item.country_code] if item.country_code else [],
            relevance=item.relevance,
        )
        apply_organization(db, doc, org)
        created += 1

    db.commit()
    return created


def demo_document_count(db: Session) -> int:
    return db.query(models.Document).filter(models.Document.is_demo.is_(True)).count()
