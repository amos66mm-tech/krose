# GiftRadar 架构说明

## 设计原则

合格的情报系统不事先决定用户需要哪几张表。流程是：

1. **收集**：用多张宽网（市场、社区、风险、新平台、行情、已知 App、用户自建）去公开网页上捞材料。
2. **归档**：每一条搜索命中都整篇入库（URL 去重、FTS 索引）。抽取失败也不丢原文。
3. **整理**：摘要、材料类型、实体、标签、事实。有 LLM 更好；没有则启发式，原文仍可搜。
4. **发现**：检索、实体页、主题、相关原文。用户靠浏览发现自己需要什么。
5. **派生**：如果原文里真有回收价 / 活动，再写入价格看板等产品视图。

上一版把系统做成「价格 / 活动 / 社媒」三条流水线 + 模拟数据填表。那会让你只能看见事先假定的东西，并且把假数据和真数据混在一起。

## 数据模型

```
WatchQuery          一张采集网（系统预置 + 用户自建，持久化）
Document            原文（title/url/full_text/摘要/类型/事实 JSON）
  ├── DocumentEntity → Entity ← EntityAlias
  └── DocumentTag    → Tag
CollectionRun       一次撒网的执行记录

Country / Platform / GiftCardType   种子目录（已知市场对象）
PriceQuote / Activity / SocialPost  从原文派生的产品视图（可空）
```

`Entity.is_seeded=false` 表示这个名字是从原文里长出来的，不在初始名单里——这通常比种子平台更有情报价值。

## 采集

- `backend/app/agent/streams.py` 定义系统宽网（每国市场全景 / 论坛 / Telegram / 诈骗 / 新 App / 行情，外加每个已知平台一张网）。
- `pipeline.run_intel_collection()` 对每张活跃的网：Exa 搜索 N 条 → `ingest_hit` 全部归档 → `organize_document`。
- 自定义网：`POST /api/watches` 或面板「再加一张网」。默认保存，下次定时任务也会跑。
- **没有 Exa Key 绝不写假网页进库**。演示模式只加载 `demo_corpus.py` 里那批多样化语料。
- 有 Exa、没有 LLM：照样归档原文，用启发式打实体/标签。

启动时不再自动跑全量真实搜索（避免阻塞）。演示语料在 `run_seed()` 里写入；真实采集请用面板或 `python run_agent.py`。

## 检索

SQLite FTS5（`documents_fts`）+ `LIKE` 兜底（中文分词不稳时仍能命中摘要）。  
API：`GET /api/intel/search`、`/documents/{id}`、`/entities`、`/overview`。

## 已知限制

- 公开网页对小型非洲收卡 App 覆盖仍然稀疏。宽网的意义是把**打到的东西留下**，而不是保证每个种子平台每天都有报价。
- 百分比报价仍可能是用近似汇率从 ₦/$ 换算的，原文数字在 `Document.full_text` / `facts_json` 里。
- 同名公司误匹配无法从根上消灭；所以必须保留 URL，让人能一票否决。
- Exa 不是官方推特/Meta API。社媒类原文质量取决于公开网页能搜到什么。

## 目录

```
backend/app/
  models.py                 原文/实体/网/派生表
  fts.py                    SQLite FTS5
  seed.py                   国家/平台/卡种 + 实体提升 + 演示语料
  agent/
    streams.py              系统宽网
    ingest.py               命中 → Document（去重）
    organize.py             启发式 + LLM 整理、实体对齐
    demo_corpus.py          无 Key 时的多样化语料
    pipeline.py             撒网主流程
    exa_client.py / llm_client.py
  routers/intel.py          发现 API
  routers/watches.py        监控网 CRUD
frontend/src/pages/         情报库 / 检索 / 原文 / 实体 / 主题 / 价格 / 采集
```
