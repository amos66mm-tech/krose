# GiftRadar 架构说明

## 一句话概述

GiftRadar 是一个「可配置监控目标 + Exa 搜索 + OpenAI 协议 LLM 结构化抽取」的通用采集 Agent，
预置了尼日利亚 / 加纳 / 喀麦隆礼品卡交易市场的价格、活动、社交媒体三条采集流水线，
并配套一个 Web 面板用于查看和管理这些数据。

## 为什么这么设计

你的核心诉求可以拆成三层：

1. **数据层**：需要持续获取「礼品卡回收价格」「平台活动」「平台社媒动态」，并且要能识别「新出现的价格/消息」。
2. **产品层**：需要一个按国家 → App 分类、能看价格、看趋势、看动态的面板。
3. **战略层**：这套数据未来要反哺一个论坛，因此系统要足够通用，方便你随时新增监控对象（新国家、新平台，
   甚至完全不相关的信息源），而不是一个写死的爬虫脚本。

对应到代码里：

- `backend/app/agent/targets.py` 里的 `WatchTarget` 是整个系统的核心抽象——一个「监控目标」只是
  `(搜索词, 抽取schema, 落库方式)` 的组合。价格/活动/社媒只是三种预置目标构造函数，
  `build_custom_target()` 则演示了如何用任意关键词临时生成一个目标，这就是「万物皆可爬」的落地方式。
- `backend/app/agent/exa_client.py` 封装 Exa 搜索（发现网页/最新内容）。
- `backend/app/agent/llm_client.py` 封装任意遵循 OpenAI Chat Completions 协议的 LLM
  （官方 OpenAI、DeepSeek、Moonshot、OpenRouter、自建 vLLM 均可，只需换 `LLM_BASE_URL`），
  用于把网页文本转成结构化 JSON（`extract_schemas.py` 定义了每种抽取的字段契约）。
- `backend/app/agent/pipeline.py` 是「搜索 → 抽取 → 判断是否为新记录/计算涨跌幅 → 落库」的完整流程，
  三条流水线（价格/活动/社媒）复用同一套骨架。
- `backend/app/agent/mock_data.py` + `Settings.is_live_mode`：在没有配置 API Key 时，
  系统自动退化为「确定性模拟数据」模式，保证数据库结构、API、面板在拿到真实 Key 之前也能跑通、可演示。
  一旦两把 Key（`EXA_API_KEY` + `LLM_API_KEY`）都配置好，下一次采集会自动切换为真实抓取，无需改代码。

## 数据模型

```
Country (国家)
  └── Platform (该国的礼品卡交易 App/平台)
        ├── PriceQuote (某个 App 对某种礼品卡的回收价历史)
        ├── Activity (该 App 的活动/公告/政策变化)
        └── SocialPost (该 App 的社媒动态)
GiftCardType (礼品卡种类，跨平台共享，如 Amazon/Steam/Apple 等)
CollectionRun (每次采集任务的执行记录，用于面板展示 Agent 运行状态)
```

`PriceQuote.rate_percent` 表示「相对礼品卡面值的回收百分比」——因为你们的业务模型里，
论坛用户（卖家）把礼品卡卖给各交易平台变现，所以竞品价格的可比口径就是这个回收折扣率。
`is_new` / `change_percent` 由 pipeline 在写入时对比同一 `(platform, gift_card_type)`
的上一条记录自动计算，用来驱动面板里的「🆕 新报价」「▲/▼ 涨跌」标记。

## 采集调度

- 应用启动时（`main.py` 的 `lifespan`）会自动执行一次 `run_seed()`（幂等，写入国家/平台/卡种种子数据）
  和一次初始采集（如果数据库里还没有任何价格记录）。
- `scheduler.py` 用 APScheduler 按 `COLLECTION_INTERVAL_MINUTES`（默认 180 分钟）周期性调用
  `run_all_collections()`。
- 面板「Agent 探针」页面提供手动触发按钮，也可以直接调用 `POST /api/collect/run?scope=all` 或用
  `backend/run_agent.py` 命令行脚本（适合接入 cron / GitHub Actions 定时任务）。

## 扩展指南

- **新增国家/平台**：编辑 `backend/app/seed.py` 里的 `COUNTRIES` / `PLATFORMS`，重启服务即可（seed 逻辑是幂等的）。
- **新增礼品卡种类**：编辑 `GIFT_CARD_TYPES`。
- **新增一类监控目标（"爬万物"）**：在 `backend/app/agent/targets.py` 里参考
  `build_price_targets` / `build_activity_targets` 写一个新的 `build_xxx_targets()`，
  在 `extract_schemas.py` 定义对应的抽取 schema，再在 `pipeline.py` 加一个 `run_xxx_collection()`。
  也可以完全不落库，直接用 `POST /api/collect/custom` 做一次性探测（面板「Agent 探针」页已有现成 UI）。
- **切换数据库为 Postgres**：把 `DATABASE_URL` 改成
  `postgresql+psycopg://user:pass@host:5432/dbname` 并 `pip install psycopg[binary]`，其余代码无需改动
  （SQLAlchemy 已经是数据库无关的写法）。
- **接入真实社媒 API**（如 Twitter/X API、Meta Graph API）：可以在 `pipeline.py` 里给
  `run_social_collection` 增加一个「优先走官方 API，失败再回退 Exa 搜索」的分支，
  数据模型（`SocialPost`）已经足够通用，不需要改表结构。

## 目录结构

```
backend/
  app/
    main.py            FastAPI 入口，装配路由/调度器/启动初始化
    config.py           环境变量配置（Pydantic Settings）
    database.py          SQLAlchemy engine/session
    models.py             ORM 表结构
    schemas.py             API 出参 Pydantic 模型
    seed.py                国家/平台/卡种种子数据
    agent/
      targets.py            监控目标构造（可扩展的核心抽象）
      exa_client.py           Exa 搜索封装
      llm_client.py            OpenAI 协议 LLM 封装 + 结构化抽取
      extract_schemas.py        抽取结果的 Pydantic 契约
      pipeline.py               价格/活动/社媒三条采集流水线
      mock_data.py               无 API Key 时的确定性模拟数据
    routers/                  REST API 路由（countries/platforms/prices/activities/social/dashboard/collect/ideas）
    scheduler.py               APScheduler 定时任务
  run_agent.py                命令行手动触发采集
  requirements.txt
  .env.example
frontend/
  src/
    api/client.ts               后端 API 的 axios 封装
    pages/                       总览/价格看板/活动/社媒/Agent探针/论坛增长点子 六个页面
    components/                  Layout、StatCard、Badge、趋势图 Modal 等
    context/CountryContext.tsx    全局国家筛选状态
docs/
  ARCHITECTURE.md（本文件）
  FORUM_GROWTH_IDEAS.md（论坛内容拓展点子，同样通过 /api/ideas 暴露给面板）
```
