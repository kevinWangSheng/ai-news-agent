# ai-agent-hub 升级总规划

> 把 `ai-news-agent`(单向新闻聚合)升级为 `ai-agent-hub`(个人 AI 信息中枢)。
> 决策日期:2026-05-15。
> 仓库:原地重命名 + 升级,保留 git 历史。

---

## 1. 目标(WHY)

旧系统是**单向、无状态、一次性**的:GitHub Actions 跑 → 抓 → 评分 → 邮件 → 落地 `output/daily_report.md` → 下次重来。
没有"读过没有"、没有"我标重要"、没有"上周那篇是哪个"、没有"这个项目过去 1 个月发了什么"。

新系统是**双向、持久、累积**的:
- **我能把东西扔进去**(投喂 URL / 笔记 / 想法)
- **系统记得我读过 / 标记过什么**,并据此调整未来推送
- **我能问它**:全文搜、语义搜、按主题/实体/时间检索
- **我能看演进**:主题时间线、人物动态、项目轨迹

---

## 2. 目标架构(WHAT)

```
┌─────────────── 投喂层 ───────────────┐
│ ① 手动:bookmarklet / `hub` CLI       │
│ ② 自动:6 个 ingestion source         │
│    (RSS / GitHub / Exa / Twitter / 中文平台)│
└──────────────────┬────────────────────┘
                   ▼
┌─────────────── 处理流水线 ──────────────┐
│ 抓全文(trafilatura,JS 页面 fallback   │
│        playwright)                      │
│  ↓                                       │
│ Claude enricher(总结/中文标题/标签/    │
│        实体抽取,prompt cache)          │
│  ↓                                       │
│ Embedding(Voyage-3 / OpenAI)           │
│  ↓                                       │
│ 评分(基础分 + 偏好分)                 │
└──────────────────┬──────────────────────┘
                   ▼
┌────── Postgres 16 + pgvector ──────┐
│ items / topics / entities /         │
│ item_topics / item_entities /       │
│ interactions / digests              │
└──────────────────┬───────────────────┘
                   ▼
┌──────────── 消费层 ────────────┐
│ FastAPI REST                    │
│  ↓                               │
│ Next.js 14 Web 站                │
│  /inbox    今日待处理            │
│  /library  全库浏览 + 检索       │
│  /topics   主题 + 时间线         │
│  /entities 人 / 公司 / 项目页    │
│  /digest   周期精选(替代日报)  │
└──────────────────────────────────┘
```

## 3. 技术栈(决定项)

| 层 | 选择 | 理由 |
|---|---|---|
| 后端 | FastAPI(Python 3.11+) | 现有代码 Python,迁移阻力低 |
| 前端 | Next.js 14 App Router + Tailwind + shadcn/ui | 留产品化空间 |
| DB | Postgres 16 + pgvector + tsvector | 单一存储解决主数据 / 全文 / 向量 |
| 调度 | APScheduler(进程内) | 替代 GH Actions,本地一直在线 |
| 部署 | 本地 Mac · Docker Compose | 零月费 / 数据自有 |
| 包管理 | uv (后端) / pnpm (前端) | 快 |
| 测试 | pytest + Vitest + Playwright(E2E) | 标配 |
| Embedding | Voyage-3(1024 维)首选,可降级 OpenAI text-embedding-3-small | 性价比 |
| LLM 评估 | Claude Haiku 4.5 + prompt cache;MiniMax 降级 | 沿用现状 |

## 4. 现状 → 目标 文件映射

| 现状 | 目标 | 处置 |
|---|---|---|
| `main.py` | `backend/main.py` | 重写为 uvicorn 入口 |
| `src/orchestrator.py` | 拆解到 `scheduler.py` + 删报告渲染 | 拆解 |
| `src/agents/tech_agent.py` | `backend/ingestion/sources/rss.py` | 迁移,输出改成写库 |
| `src/agents/github_agent.py` | `backend/ingestion/sources/github.py` | 迁移 |
| `src/agents/breaking_news_agent.py` + `ai_content_agent.py` | `backend/ingestion/sources/exa_search.py` | 合并迁移 |
| `src/agents/twitter_agent.py` | `backend/ingestion/sources/twitter.py` | 迁移 |
| `src/agents/chinese_platform_agent.py` | `backend/ingestion/sources/chinese.py` | 迁移 |
| `src/collectors/*` | `backend/ingestion/collectors/` | 迁移 |
| `src/evaluator/claude_evaluator.py` | `backend/processing/enricher.py` + `scorer.py` | 拆分,prompt cache 保留 |
| `src/evaluator/ai_evaluator.py` | 同上的 MiniMax 分支 | 迁移作为 fallback |
| `src/notifier/*` | — | **删除** |
| `.github/workflows/` | — | **删除** |
| `output/daily_report.md` | — | **删除** |
| `config/config.yaml` | `backend/config.yaml` | 迁移,扩展 user_preferences 节 |
| `.env` / `.env.example` | `backend/.env` / `.env.example` | 迁移 + 加新 key(DATABASE_URL 等) |
| 全新 | `frontend/` Next.js 应用 | 新建 |
| 全新 | `docker/docker-compose.yml` | 新建 |
| 全新 | `cli/hub` | 新建(Python click) |

代码复用率:**60-70%**(ingestion + enricher 主体可复用,orchestrator 和 notifier 重写/删除)。

## 5. 关键决策记录

- **为什么 Postgres 一站式而非 SQLite + 向量库分离**:运维成本相同(都进 Docker Compose),Postgres 同事务保证强,跨表 JOIN 友好
- **为什么砍邮件**:邮件不可反馈、不可累积、不可检索,与"双向 + 持久"目标冲突
- **为什么 v1 不做 Bot**:集中精力做 Web 闭环,Bot 可作 v2 加,数据接 API 即可
- **为什么用 APScheduler 不用 systemd timer**:跨平台、可读 yaml 配置、与 FastAPI 同进程方便
- **为什么 Voyage-3 而非 OpenAI**:1024 维省存储,质量评测领先,可降级
- **为什么 Next.js 而非 HTMX**:留未来产品化空间,SSR + 客户端交互对 inbox/library 类应用更合适

## 6. 不在本期范围内(明确不做)

- 多用户 / 用户系统 / 权限(单用户)
- 移动端 App(浏览器即可,后续可 PWA)
- 实时同步(轮询 / 手动刷新即可)
- 离线模式
- 跨设备同步(本地服务 + Tailscale 即可)
- 评论 / 分享 / 公开页(纯私人)
- 协同(单用户)
