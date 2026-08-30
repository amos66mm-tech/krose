# GiftRadar

一个面向**尼日利亚 / 加纳 / 喀麦隆礼品卡回收市场**的通用采集 Agent + 数据看板。

业务背景：论坛用户是礼品卡**卖方**，平台方在交易中扮演**买方/付款方**角色。GiftRadar 持续采集各交易 App
（Prestmit、Cardtonic、Sellcaddy、LegitCards、KolaCash、Sogo、SellCardNow 等）的**回收价格**、**活动/公告**、
**社交媒体动态**，写入数据库，并通过 Web 面板按国家 → App 分类展示，帮助你比价、发现平台动态、
以及为后续的论坛内容运营提供数据支撑。

Agent 本身是通用的「监控目标（Watch Target）」框架：搜索用 [Exa](https://exa.ai) API，结构化信息抽取用任意
遵循 **OpenAI API 协议**的 LLM（OpenAI 官方 / DeepSeek / Moonshot / OpenRouter / 自建 vLLM 均可）。
没有配置 Key 时，系统自动使用确定性模拟数据，保证面板开箱即有数据可看；配置好 Key 后自动切换为真实抓取。

围绕这门业务可以如何拓展、丰富论坛内容/提升用户粘性，见 [`docs/FORUM_GROWTH_IDEAS.md`](docs/FORUM_GROWTH_IDEAS.md)
（同样的内容也在面板「论坛增长点子」页面里）。架构设计细节见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)。

## 目录结构

```
backend/    FastAPI + SQLAlchemy 后端，含采集 Agent（Exa 搜索 + LLM 结构化抽取）
frontend/   React + Vite + Tailwind + Recharts 数据看板
docs/       架构说明 & 论坛内容拓展点子
```

## 快速开始

### 1. 后端

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # 按需填入 EXA_API_KEY / LLM_API_KEY，不填则自动进入演示模式

uvicorn app.main:app --reload --port 8000
```

首次启动会自动建表、写入种子数据（国家/平台/礼品卡种类）、并跑一次初始采集。
浏览器打开 http://localhost:8000/docs 可以看到自动生成的 API 文档。

也可以用命令行手动触发一次采集（适合接入 cron 定时任务）：

```bash
python run_agent.py                 # 采集全部
python run_agent.py --scope price   # 只采集价格
python run_agent.py --country NG    # 只处理尼日利亚
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173 。开发模式下 Vite 已配置好 `/api` 反向代理到
`http://localhost:8000`，无需额外配置跨域。

### 3. 配置真实的抓取能力

在 `backend/.env`（本地）或 Cursor Dashboard → Secrets（云端）中配置：

| 变量名 | 说明 |
| --- | --- |
| `EXA_API_KEY` | [Exa](https://exa.ai) 搜索 API Key，用于发现最新网页内容 |
| `LLM_API_KEY` | 任意遵循 OpenAI Chat Completions 协议的 LLM Key |
| `LLM_BASE_URL` | LLM 服务地址，默认 `https://api.openai.com/v1`，可换成 DeepSeek/Moonshot/OpenRouter 等 |
| `LLM_MODEL` | 模型名，默认 `gpt-4o-mini` |

两把 Key 都配置好后，下一次采集（定时任务或手动触发）会自动切换为真实的「Exa 搜索 + LLM 抽取」模式，
无需修改代码。面板「Agent 探针」页面会实时显示当前是「演示模式」还是「实时抓取模式」。

## 面板功能一览

- **总览**：核心指标卡片、各卡种当前最佳回收价排行、近期波动最大的报价、Agent 运行状态。
- **价格看板**：平台 × 礼品卡种类矩阵，点击任意格子查看近 30 天历史趋势折线图。
- **活动情报**：各平台的限时加价 / 新卡种上线 / 政策变化 / 系统维护动态。
- **社媒动态**：各平台在 Twitter / Facebook / Instagram / Telegram 上的最新动态与舆情倾向。
- **Agent 探针**：查看 API Key 配置状态、手动按范围（价格/活动/社媒/全部）触发采集、
  以及一个「万物皆可爬」的即时探针（任意关键词 → Exa 搜索 → LLM 结构化摘要），
  为未来扩展到礼品卡之外的监控场景预留入口。
- **论坛增长点子**：围绕核心业务可以衍生的论坛内容/功能清单，按优先级（P0/P1/P2）排列。

## 扩展新国家 / 新平台 / 新监控对象

- 新增国家或交易 App：编辑 `backend/app/seed.py`。
- 新增一类监控目标（例如追踪竞品论坛话题、汇率新闻）：参考 `backend/app/agent/targets.py`，
  详见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#扩展指南)。
