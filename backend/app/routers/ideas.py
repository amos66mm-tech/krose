from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/ideas", tags=["ideas"])

# 围绕「尼日利亚/加纳/喀麦隆礼品卡回收」主业务，可以衍生出的论坛内容/功能点子。
# 目标：提升卖家（用户）粘性、建立信任、把「比价」这个刚需变成日常访问论坛的理由。
CONTENT_IDEAS = [
    {
        "category": "实时比价 / 核心留存",
        "items": [
            {
                "title": "每日/每小时价格榜（本网站数据驱动）",
                "description": "把本工具采集到的各平台回收价格做成「今日最佳出货渠道」榜单，钉在论坛首页置顶，用户每天都要来看一眼。",
                "priority": "P0",
            },
            {
                "title": "价格预警订阅",
                "description": "用户设置某卡种目标汇率，一旦有平台价格触达阈值就站内信/邮件/Telegram通知，把「被动浏览」变成「主动召回」。",
                "priority": "P0",
            },
            {
                "title": "套利机会雷达",
                "description": "自动比较同一卡种在不同平台/不同国家的价差，生成「搬砖」提示帖，激发老用户的活跃讨论。",
                "priority": "P1",
            },
        ],
    },
    {
        "category": "信任与风控（对卖方极其关键）",
        "items": [
            {
                "title": "平台信誉分 / 黑名单预警",
                "description": "综合社媒负面舆情、到账延迟投诉、公告类型，给每个平台打「信任分」，帮卖家避坑，也是论坛区别于纯比价站的护城河。",
                "priority": "P0",
            },
            {
                "title": "到账速度/纠纷案例众包库",
                "description": "允许用户提交真实交易反馈（到账时长、客服响应），沉淀成结构化数据库，反哺信誉分模型。",
                "priority": "P1",
            },
            {
                "title": "官方渠道核验标记",
                "description": "结合社媒抓取识别官方账号 vs 仿冒账号，给帖子/平台打上「已核验」标签，降低钓鱼诈骗风险。",
                "priority": "P1",
            },
        ],
    },
    {
        "category": "情报 / 内容自动化",
        "items": [
            {
                "title": "App 动态情报站",
                "description": "自动聚合各平台的活动、限时加价、新卡种上线、版本更新，生成「情报周报」，减少用户手动关注多个App的成本。",
                "priority": "P0",
            },
            {
                "title": "LLM 自动生成的每周市场总结帖",
                "description": "用采集到的价格趋势 + 活动 + 社媒数据，让 LLM 自动生成一篇「本周尼日利亚礼品卡市场综述」置顶帖，作为论坛内容引擎。",
                "priority": "P1",
            },
            {
                "title": "汇率/宏观新闻联动",
                "description": "结合尼日利亚奈拉、加纳塞地、喀麦隆法郎汇率新闻（可用 Exa 搜索联动），解释价格波动原因，提升内容深度。",
                "priority": "P2",
            },
        ],
    },
    {
        "category": "社区互动 / 粘性机制",
        "items": [
            {
                "title": "积分/徽章体系",
                "description": "用户提交真实价格/交易反馈可获得积分，积分兑换手续费折扣或论坛特权，形成数据众包飞轮。",
                "priority": "P1",
            },
            {
                "title": "新手卖家指南自动生成",
                "description": "基于高频问题（如何验证卡、常见拒收原因）自动生成/更新 FAQ 专区，降低客服压力。",
                "priority": "P2",
            },
            {
                "title": "排行榜 & 冲榜活动",
                "description": "「本周最佳汇率贡献者」「最活跃卖家」榜单，配合小额奖励，制造归属感和竞争氛围。",
                "priority": "P2",
            },
        ],
    },
    {
        "category": "商业化 / 拓展方向",
        "items": [
            {
                "title": "比价小工具嵌入/Widget",
                "description": "把价格看板做成可嵌入其他站点/Telegram Bot 的小组件，反向为论坛导流。",
                "priority": "P2",
            },
            {
                "title": "多国横向扩展看板",
                "description": "在尼日利亚/加纳/喀麦隆基础上，逐步接入肯尼亚、贝宁、科特迪瓦等（Watch Target 机制已支持任意扩展），把论坛做成「非洲礼品卡市场」的统一情报入口。",
                "priority": "P1",
            },
            {
                "title": "买方（你们自身）报价策略辅助",
                "description": "既然你们本身是买方付款方，这套竞对价格监控还能反哺你们自己的收卡定价策略，形成「用户看得到的比价」和「你们内部风控定价」的双重价值。",
                "priority": "P0",
            },
        ],
    },
]


@router.get("")
def list_ideas():
    return CONTENT_IDEAS
