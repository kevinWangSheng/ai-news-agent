# 014 · Web Source Coverage — Tasks

> 任务粒度 1-2 小时;`verify` 任务必须有可执行命令或可观察结果。

## 阶段 A:开发期工具

- [x] A1. ~~装 Playwright MCP~~ —— 用户机器已有 `playwright-mcp --extension --browser chrome` 在跑(2026-05-17 确认),只需在 Claude Code 项目 / session 里接上即可,无需安装
- [ ] A2. **verify**:本次会话(或下次)看到 MCP 工具里有 playwright_* 可调,能开浏览器看 https://www.anthropic.com/news

## 阶段 B:实现 `WebSource`(纯 HTTP 路径,先解锁 17 个站)

- [ ] B1. 新建 `backend/app/ingestion/sources/web.py`,定义 `WebSource(Source)` 类
  - 输入:`name / listing_url / link_pattern(可选)/ max_items`
  - 方法:`async fetch() -> AsyncIterator[RawItem]`
  - 流程:listing HTTP → 抽链接 → 每篇文章 HTTP → trafilatura 提正文
- [ ] B2. 在 `web.py` 加 `build_web_sources(cfg) -> list[WebSource]`,从 `tech_sources.*` 各 bucket 过滤 `type=="web"` 的源
- [ ] B3. 修 `backend/app/ingestion/run.py:build_sources`,把 web 类型从 `rss.py` 的处理里剥离,改走 `web.py`
- [ ] B4. 修 `rss.py:build_rss_sources`,只处理 `type=="rss"` 的源(目前是全吃)
- [ ] B5. `config.yaml` 给 Anthropic / Claude / Cursor 三个站加 `link_pattern` 字段(精确控制 URL 模式)
- [ ] B6. 写 `backend/tests/test_web_source.py`:
  - 单测 listing HTML → 链接列表
  - 单测 link_pattern 过滤
  - 单测 article HTML → markdown 转换
- [ ] B7. **verify**:`uv run pytest tests/test_web_source.py` 通过
- [ ] B8. **verify**:容器内手动跑 `python -m app.ingestion.run web` 单源测试,DB items 来自这 3 站点的 ≥ 30 条
  ```bash
  docker compose exec backend python -m app.ingestion.run web
  docker compose exec postgres psql -U hub -d hub -c \
    "select source_name, count(*) from items where source_type='web' group by 1;"
  ```

## 阶段 C:装 chromium + playwright 路径(解锁剩 7 个站 + 救 OpenAI)

> **本 change 不做**(2026-05-17 决议),整段推迟到 015 或之后。理由:17 个简单站已经覆盖最关键的 Anthropic / Claude / Cursor 等;OpenAI / xAI 等 7 个 JS 站等真用一周看是否缺得慌再说;镜像 +300MB 是一次性代价,可以晚点付。

- [ ] ~~C1~~. 推迟
- [ ] C1. `backend/Dockerfile` runtime stage 加:
  ```
  RUN apt-get update && apt-get install -y --no-install-recommends \
      libnss3 libxkbcommon0 libdrm2 libgbm1 libasound2 libatk-bridge2.0-0 libatspi2.0-0 \
      libxcomposite1 libxdamage1 libxfixes3 libxrandr2 fonts-noto-cjk \
   && rm -rf /var/lib/apt/lists/*
  RUN python -m playwright install chromium
  ```
- [ ] C2. `WebSource` 加 `_fetch_listing_with_js(url)` 和 `_fetch_article_with_js(url)` —— 当 HTTP 路径失败或返回过短时自动 fallback
- [ ] C3. `backend/app/processing/extract.py:_fetch_via_playwright` 现已 graceful skip;装 chromium 后应该真生效。**verify** 它现在能拉到 OpenAI 一篇文章正文
- [ ] C4. 给 xAI / Mistral / Qwen / AutoGen / The Batch 在 `config.yaml` 加 `js_render: true` 标记,WebSource 见此优先 playwright
- [ ] C5. **verify**:`docker compose build backend` + 重启 + 跑 `python -m app.ingestion.run web` 单点测一篇 OpenAI / 一篇 xAI 文章

## 阶段 D:配置 / 死源处理

- [ ] D1. Meta AI Blog `url` 改为可用的(候选:`https://ai.meta.com/research/publications/` 或 `https://about.fb.com/news/category/ai/`,先 curl 验)
- [ ] D2. AMI Labs (LeCun) 站点连不上,`config.yaml` 标 `disabled: true`(或直接注释掉)
- [ ] D3. 处理 GitHub README 类无法 extract 的情况(29 条 failed 里部分):若 `source_type=github` 且 extract 失败 ≥ 2 次,**直接用 RSS 给的 description 当 content_md**,不强求抓 README

## 阶段 E:运行 + 收口

- [ ] E1. 复活当前 29 条 `processing_status=failed` 的:
  ```sql
  UPDATE items SET processing_status='pending', processing_attempts=0, last_error=NULL
  WHERE processing_status='failed';
  ```
- [ ] E2. 跑一次完整 ingestion + processing + scoring:
  ```bash
  docker compose exec backend python -m app.ingestion.run all
  for i in 1 2 3 4 5 6 7 8 9 10; do
    docker compose exec backend python -m app.processing.run --once
  done
  docker compose exec backend python -m app.scoring.recompute --all
  ```
- [ ] E3. **verify** 库存 ≥ 600 条
- [ ] E4. **verify** inbox 默认 50 条里,至少 5 条来自 `Anthropic News` 或 `Claude Blog`:
  ```sql
  SELECT source_name, count(*) FROM items
  WHERE status='inbox' AND source_name IN ('Anthropic News', 'Claude Blog')
  GROUP BY 1;
  ```
- [ ] E5. **verify** `processing_status='failed'` 比例 < 3%
- [ ] E6. 跑一遍 `docs/content-truth.md` §2 的质量审计 SQL,**完成度 ≥ 98%**
- [ ] E7. 抽样人工 review 10 条 Anthropic / Claude 的 title_cn / summary_zh,无明显翻译错误

## 阶段 F:文档 / 收口

- [ ] F1. `docs/content-truth.md` 顶部加 "2026-XX-XX:已通过 change 014 解决" 横幅 + 更新对账表
- [ ] F2. `docs/handoff.md` §3 / §4 的 verify 命令同步更新(数据量 / 预期源数)
- [ ] F3. CHANGELOG.md 加 v2.2.0 段落
- [ ] F4. `openspec/changes/014-web-source-coverage/proposal.md` 顶部加 `Status: completed (YYYY-MM-DD)`
- [ ] F5. commit + push

## 阶段 G:未尽 / 推迟到 015

- [ ] G1. enrich prompt 优化(title_cn 中文化激进度)—— 等 600+ 条样本到位后,基于数据看是否真要改,推迟 015
- [ ] G2. 5 个 JS 渲染站如果 playwright 仍抓不到(比如 Cloudflare 拦),允许标记 `disabled` 暂时跳过,不阻塞本 change

## 估时(收窄到 A 选项后)

| 阶段 | 内容 | 估时 |
|---|---|---|
| A | Playwright MCP(用户机器已有)| 0(已就绪)|
| B | WebSource 纯 HTTP 路径 | 3-4 小时 |
| ~~C~~ | ~~chromium + playwright~~ | 推迟到 015 |
| D | 死源 / 配置清理 | 30 分钟 |
| E | 运行 + verify | 1 小时 |
| F | 文档 / 收口 | 30 分钟 |
| **合计** | | **5-6 小时**(半个工作日)|
