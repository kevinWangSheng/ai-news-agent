# Changelog

## v2.3.1 (2026-05-18) — Ranking lanes v1

在 change 014 内容抓取清零 failed 后,新增首页 ranking v1:把“分数”和“版面编排”分开。

- scoring 增加 `source_prior` breakdown:official +0.45, expert +0.25, aggregator +0.10, GitHub -0.45。
- `/api/items?sort=score` 增加 diversity rerank,避免单一 source/type 占满 top 列表。
- 新增 `/api/items/lanes`:返回 `top_signals` / `official_updates` / `repo_radar` 三条 lane。
- lane 内加入 source rotation:official lane 单源最多约 2 条;repo lane 单 topic/source 最多约 3 条。
- 前端 API hook 新增 `useItemLanes`;Inbox 默认状态已改成 lane 版,显示 Top Signals / Official Updates / Repo Radar 三栏。筛选条件变化后回到原列表模式。

实测(当前 DB items=724):

- `sort=score&limit=50`:web 19 / github 18 / rss 13。
- `/api/items/lanes?limit=20`:Top Signals 为跨源冠军榜;Official Updates 为 web 15 / rss 5;Repo Radar 为 GitHub 20 且 source 分散。

验证:`cd backend && uv run pytest -q tests/scoring/test_engine.py tests/scoring/test_ranking.py tests/api/test_smoke.py`;backend ruff passed;`cd frontend && pnpm typecheck` passed;Docker backend/frontend rebuild;项目内 Playwright headless 截图确认 `/inbox` 三栏渲染。

待定:Top Signals 仍偏 RSS/GitHub,但 Official Updates 已承载官方源;下一步重点转为 UI 信息密度、lane 去重/折叠、真实 dogfood 后的权重调参。

## v2.3.0 (2026-05-17) — Consumption UX 验收通过

change 015 的核心消费体验已推进完成并通过真实容器 + headless Chrome 验收。

- 详情页:Markdown 真渲染、代码高亮/copy、score breakdown、source tier、阅读时长、我的笔记。
- Inbox:sticky 筛选栏、URL 状态、今日/更早分段、高分视觉权重、已读暗化、cold_start 横幅、键盘流、撤销 toast、批量动作、skeleton、react-window 虚拟滚动。
- 后端:items 支持 `since`/`tier`/`min_score`/`sort`,新增 bulk patch、viewed_at 聚合、authors API。
- 搜索/导航:顶栏跳 `/search`,新增搜索结果页和作者页。

验证:`cd frontend && pnpm typecheck`,`cd frontend && pnpm build`,`cd backend && uv run ruff check ...`,`python3 -m compileall -q backend/app`;Docker backend/frontend rebuild;curl full=469 filtered=37;headless Chrome 跑通 inbox/detail/search/note/bulk;截图见 `docs/screenshots/015/`。

补充: `/api/search` query embedding 改为 ARK → Voyage → OpenAI,避免有 ARK key 时仍优先打 Voyage 401。


## v2.2.0 (2026-05-17/18) — WebSource + Browser 覆盖落地

change 014 已完成 source coverage 层面的闭环:HTTP 快路径 + Chromium/Playwright 浏览器路径均已落地,`backend/config.yaml` 的 `type: web` 官方源不再静默空跑。

已完成:

- 新增 `backend/app/ingestion/sources/web.py`:listing → same-host `link_pattern` 抽链接 → article → trafilatura markdown → RawItem
- `build_rss_sources` 只吃 `type: rss`;`build_sources` 新增 `web` kind;scheduler 新增 `ingestion_web` 每小时 `:55` 错峰跑
- `backend/Dockerfile` runtime 安装 Chromium 依赖 + `python -m playwright install chromium`,backend/scheduler 容器内可真实跑 Playwright
- `WebSource` 支持 `js_render: true` 与 `fallback_urls`;Qwen 主入口无链接时自动 fallback 到 `qwenlm.github.io/blog/`
- config 启用 Anthropic / Claude / Cursor 等 HTTP 源,并启用 Meta / xAI / Mistral / Qwen / Cohere / AutoGen / The Batch 等浏览器源;AMI Labs 暂 disabled
- GitHub extract 失败时用 repo title/source_meta 兜底;RSS/manual article 抓取失败时使用 feed summary/title 兜底;trafilatura 失败时增加 `article/main/.email-body` DOM fallback,修复 Buttondown/AINews 完整正文抽取;enricher 增加 Claude 坏 JSON 修复 fallback
- 新增/扩展 `tests/ingestion/test_web_source.py` 与 `tests/processing/test_enricher.py`

验证:

- `cd backend && uv run pytest -q tests/ingestion/test_web_source.py tests/ingestion/test_rss.py tests/processing/test_extract.py tests/processing/test_enricher.py` → 18 passed
- 触达文件 ruff passed
- 容器 Playwright smoke:打开 `https://cohere.com/blog`,title 正常,HTML length 332968
- Docker DB 实跑后:items=716,ready=716,failed=0;web=230,web ready=230,web failed=0
- 字段完整率:所有 source_type 的 `title_cn / summary_zh / final_score / content_md / embedding` 均 100%;AINews 两条短正文由 295/328 字符重抓为 191k/174k 字符
- 浏览器源入库:Meta 12、xAI 10、Mistral 9、Qwen 5、Cohere 10、AutoGen 10、The Batch 7,全部 ready

014 当时移出的 ranking/source_boost 问题已在 v2.3.1 / 015-J 中收口:默认 score 排序加入 diversity rerank,并新增三栏 lane UI。

## v2.2.0-planning (2026-05-17) — 下一波规划拆分

基于 v2.1.0 实跑发现的内容缺口 + UX 痛点,把后续工作拆成 5 个 change 包:

- `openspec/changes/014-web-source-coverage/`(`completed-for-source-coverage`)— HTTP + Chromium/Playwright `WebSource` 已接入 23 个 web source,web ready=230/230
- `openspec/changes/015-consumption-ux/`(`completed + ranking-lanes-v1`)— Markdown 真渲染 / inbox 筛选栏 / 注意力分层(score 变体 / today 分段 / breakdown 可见 / cold_start 警告) / 键盘流 J/K/S/E/X / Undo toast / 批量选 / 笔记 UI / 虚拟滚动 / Top-Official-Repo 三栏
- `openspec/changes/016-second-brain/`(`planned-outline`)— LLM 二次加工(ask / find-related / `/ask`)/ 关注主题 / 信源 mute boost UI / trending cluster
- `openspec/changes/017-polish-style-mobile/`(`planned-sketch`)— 风格 5 选 1 / 手机响应 / Reader Mode / 备份导出 / onboarding / 可访问性
- `openspec/changes/018-ops-and-tooling/`(`planned-outline`)— scheduler 健康面板 / ingestion 错误页 / 源失活报警 / hub 批量投喂

支撑文档:

- `docs/content-truth.md` — 内容覆盖 + 数据质量实证报告
- `docs/v2-roadmap.md` — 24 条候选改进的总清单(历史索引,已被上面 5 个 change 包细化)
- `docs/troubleshooting.md` — 常见环境问题速查(Playwright MCP / Docker / Colima / Next.js / Backend / CLI)

`openspec/README.md` 依赖图同步更新。

## v2.0.0 (2026-05-17) — ai-agent-hub

从 `ai-news-agent`(单向新闻聚合,GH Actions+邮件)升级为 `ai-agent-hub`(双向、持久、累积的个人 AI 信息中枢)。

### 升级路径(14 个 openspec change)

- **000 plan-corrections** — 12 处规划文档修订
- **001 foundation** — 仓库重构:`backend/` `frontend/` `cli/` `docker/`,旧代码迁到 `backend/legacy/`
- **002 data-model** — Postgres 16 + pgvector + tsvector,8 个表 + 3 个 trigger + HNSW 索引
- **002a source-tuning** — KOL handle 修正、`topics.yaml` 主题字典(34 个)、focus_keywords 自动生成(91 个)
- **003 ingestion-sources** — 6 个 source(RSS / GitHub / Exa / Twitter / 中文平台 / manual)+ `IngestionService` 幂等去重
- **004 processing-pipeline** — extract(trafilatura+playwright)→ enrich(Claude prompt cache)→ embed(Voyage-3 + OpenAI fallback)→ finalize
- **005 preference-scoring** — 基础分 + tag/entity/source boost + time decay + focus floor 6 + 冷启动门槛 50
- **006 rest-api** — 28 个端点(8 标签:ingest/items/search/topics/entities/digests/sources/health)
- **007 manual-ingest** — bookmarklet 安装页 + `hub` CLI(11 个子命令)
- **008-011 frontend** — Next.js 16 + SWR + cmdk;12 路由(inbox/library/topics+timeline/entities/digest/sources/settings/item)
- **012 scheduler-migration** — APScheduler + SQLAlchemyJobStore,9 个 job(替代 GH Actions)
- **013 decommission-old** — 删邮件依赖、重写 README + 本 changelog

### Breaking

- 不再有邮件 / Telegram 通道,改为 Web + CLI
- 不再有 GitHub Actions 调度,改为本地 APScheduler(`docker compose up -d scheduler`)
- 旧 `output/daily_report.md` 一次性产物退役,数据全部入 Postgres
- 配置:旧 `config/config.yaml` → `backend/config.yaml` + `backend/topics.yaml`;邮件/Telegram 环境变量删除

### 不破坏

- 6 个 source 的网络抓取逻辑完整迁移
- Claude prompt cache + MiniMax fallback 思路保留
- AI Agent 领域聚焦关键词扩展(原 12 → 91)

详见 [`docs/migration-from-v1.md`](docs/migration-from-v1.md)。

### v2.0.0 修补(2026-05-17 handoff)

- `backend/Dockerfile`:补 COPY `config.yaml` / `topics.yaml` / `alembic/` / `alembic.ini`(原版漏拷,容器内 `load_config()` 必 `FileNotFoundError`);加 HEALTHCHECK 走 `/health`
- `docker/docker-compose.yml`:新增 `migrate` 一次性服务执行 `alembic upgrade head`,`backend` / `scheduler` 用 `condition: service_completed_successfully` 等它
- `backend/app/ingestion/run.py`:移除 `load_config` / `load_topics` 的 legacy yaml fallback(canonical 与 legacy 100% 同步,fallback 是死代码且会让以后误删 backend yaml 时静默回退)
- `docs/handoff.md`:新增,装好 docker 后按 10 节顺序跑可收口 7 个 change 的 verify 挂账

### v2.0.1 真机 verify 通过 + 修 5 个 docker 起来才暴露的 bug(2026-05-17)

装 colima/docker 后实跑 `docs/handoff.md` §1-7,过程中发现并修复:

- `backend/app/scoring/preferences.py`:`func.cast(..., func.Integer)` 写错 —— `func.Integer` 不是类型是 SQL 函数调用。改成 `cast(expr, Integer)`,3 处。`recompute --all` 之前必崩
- `frontend/Dockerfile`:`corepack prepare pnpm@latest` 在 node 20 上拉到 pnpm 11(要求 node 22),`node:sqlite` 内建模块不存在。改 base 到 `node:22-alpine`、pin `pnpm@10.30.1`
- `frontend/next.config.ts` + `Dockerfile`:Next.js 16 在 docker 里 `next start` 所有路由 404(包括 /),改 `output: "standalone"` + COPY `.next/standalone` + `node server.js`
- `docker/docker-compose.yml`:scheduler 借用 backend 镜像但不跑 uvicorn,加 `healthcheck: disable: true` 避免 5 次 retry 后被标 unhealthy
- `docker/postgres/Dockerfile`(新):pgvector 官方镜像那两个 blob 在我们这边的 Cloudflare 边缘一直 EOF(`pgvector/pgvector:pg16` 和 `:0.8.0-pg16` 都中招,alpine/postgres 官方都通,即只针对 pgvector 镜像的问题)。改为本地 build `postgres:16` + `apt-get install postgresql-16-pgvector`,永久绕开 + 不变更行为

verify 结果(均通过):

| § | 内容 | 结果 |
|---|---|---|
| 1 | 4 服务起来 + healthcheck | postgres / backend healthy;frontend / scheduler 跑 |
| 2 | DB schema:9 表 + vector/pg_trgm extension + 3 个 trigger | psql `\d items` + trigger 行为复测全通 |
| 3 | RSS ingestion + dedupe | 195 条入库,二次跑 0 created 全 deduped |
| 4 | 5 阶段 processing | extract→enrich 85 条,embed 因没 VOYAGE key graceful fail |
| 5 | scoring recompute | breakdown JSON 完整(base/final/tag_boost/cold_start/focus_hits/time_decay/entity_boost/source_boost) |
| 6 | POST /api/ingest + items/search/sources | 新 item 创建,46 sources,search 返回 hit |
| 7 | bookmarklet 安装页 + `hub` CLI | settings 页 200,`hub add/search/list/keep` 全通 |
| 8(附带) | scheduler 自动跑 github cron | 期间 151 条 github 条目入库,012 调度器实战通过 |

13 修补完成:`git rm -r backend/legacy/`(代码层面无 import / runtime 引用,3 个手动 verify 全通后签字)

### v2.1.0 ARK 火山方舟 embedding 接入(2026-05-17)

替代 Voyage 作为 primary embedding 提供商,链路:**ARK → Voyage → OpenAI**。

**为什么**:Voyage 需翻墙 + 付费;火山方舟提供 Doubao 系列 embedding 国内直连免代理,且与 OpenAI API 完全兼容。

**接入细节**:

- 端点 `https://ark.cn-beijing.volces.com/api/coding/v3/embeddings`(`/api/coding` 网关自带模型开通,免 ARK 控制台 activate)
- 模型 `doubao-embedding-vision`(自动解析到 `-251215` 最新版,文本输入也 OK)
- `dimensions=1024` 参数原生支持,直接对齐 DB schema 的 `Vector(1024)`,无需客户端切片

**改动**:

- `backend/app/config.py`:加 `ark_api_key` / `ark_base_url` / `ark_embed_model` 三项 settings
- `backend/app/llm/client.py`:加 `get_ark()` 单例(OpenAI client + 自定义 base_url)
- `backend/app/processing/embed.py`:加 `_ark()` 函数,在 `embed_one` 中放在 `_voyage` / `_openai` 之前
- `docker/.env.example`:加 `ARK_API_KEY` + 注释里说明 `ARK_BASE_URL` / `ARK_EMBED_MODEL` 默认值

**端到端 verify**:

- 320 条 enriched → embed → ready 全部通过,ARK 命中率 99.7%(1 条 500 重试后成功)
- 单条 latency 约 200ms,batch 50 条用时 ~5s
- 真实 final_score 分布:9-10 分 124 条,10+(满分)94 条,集中在 MCP / Agent / LangChain 相关 GitHub 项目
