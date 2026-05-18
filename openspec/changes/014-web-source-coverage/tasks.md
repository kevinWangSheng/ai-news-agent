# 014 · Web Source Coverage — Tasks

> 任务粒度 1-2 小时;`verify` 任务必须有可执行命令或可观察结果。

## 阶段 A:开发期工具

- [x] A1. 用户机器已有 `playwright-mcp --extension --browser chrome` 在跑(2026-05-17 确认),无需安装。
- [x] A2. **verify**:切到安装 Playwright Extension 的 Chrome `shenghui` profile 后,`mcp__playwright__.browser_navigate` 已能打开 https://www.anthropic.com/news 。

## 阶段 B:实现 `WebSource` HTTP 快路径

- [x] B1. 新建 `backend/app/ingestion/sources/web.py`,实现 listing HTTP → 链接抽取 → article HTTP → trafilatura markdown → RawItem。
- [x] B2. `build_web_sources(cfg)` 从 `tech_sources.*` 过滤 `type=="web"` 且 `disabled != true` 的源。
- [x] B3. `backend/app/ingestion/run.py:build_sources` 新增 `web` kind。
- [x] B4. `rss.py:build_rss_sources` 只处理 `type=="rss"`,避免 HTML 页面被 feedparser 静默吃掉。
- [x] B5. `config.yaml` 为 Anthropic / Claude / Cursor 等 web 站加 per-source `link_pattern`。
- [x] B6. `backend/tests/ingestion/test_web_source.py` 覆盖 listing link 过滤、article markdown、fallback listing。
- [x] B7. **verify**: `cd backend && uv run pytest -q tests/ingestion/test_web_source.py tests/ingestion/test_rss.py tests/processing/test_extract.py tests/processing/test_enricher.py` → 15 passed(2026-05-17)。
- [x] B8. **verify**:Docker DB 实跑 web ingestion 后,Anthropic 14 + Claude 20 + Cursor 10 均 ready。

## 阶段 C:Chromium + Playwright 浏览器路径

- [x] C1. `backend/Dockerfile` runtime stage 安装 Chromium 所需系统依赖 + `python -m playwright install chromium`。
- [x] C2. `WebSource` 支持 `js_render: true`:listing/article 优先 Playwright,HTTP 失败或正文过短时 fallback Playwright。
- [x] C3. `WebSource` 支持 `fallback_urls`:Qwen 主入口 `https://qwen.ai/blog` 无 `<a href>`,自动 fallback 到 `https://qwenlm.github.io/blog/`。
- [x] C4. `config.yaml` 启用 Meta / xAI / Mistral / Qwen / Cohere / AutoGen / The Batch 的浏览器抓取配置;AMI Labs 仍 disabled。
- [x] C5. **verify**:容器内 Playwright smoke 成功:
  ```bash
  docker compose exec -T backend python - <<'PY'
  from playwright.sync_api import sync_playwright
  with sync_playwright() as p:
      b=p.chromium.launch(headless=True,args=['--no-sandbox'])
      page=b.new_page(); page.goto('https://cohere.com/blog', wait_until='domcontentloaded')
      print(page.title(), len(page.content())); b.close()
  PY
  ```
  结果:`Cohere Blog | AI News, Insights, and Innovation`,HTML length 332968。
- [x] C6. **verify**:浏览器源实跑入库成功:Meta 12、xAI 10、Mistral 9、Qwen 5、Cohere 10、AutoGen 10、The Batch 7,全部 ready。

## 阶段 D:配置 / 死源处理

- [x] D1. Meta AI Blog:HTTP 曾返回 400,Playwright 路径可抓,保留并启用 `js_render`。
- [x] D2. AMI Labs (LeCun) 站点不可用,`config.yaml` 标 `disabled: true`。
- [x] D3. GitHub README 类无法 extract 时,用 GitHub metadata/title 组装 `content_md` 兜底。
- [x] D4. enricher 增加 Claude 坏 JSON 修复 fallback,避免偶发裸双引号/Markdown fence 卡住 processing。
- [x] D5. 文章正文提取增强:OpenAI 走 Playwright,Medium 走 RSS full summary,Buttondown/AINews 走 `article/.email-body` DOM fallback;AINews 两条短正文已由 295/328 字符重抓为 191k/174k 字符。

## 阶段 E:运行 + 收口

- [x] E1. 跑 web ingestion + processing + scoring。
- [x] E2. **verify** 库存 ≥ 600 —— 2026-05-17/18 实测 items=716。
- [x] E3. **verify** web 覆盖:23 个 web source ready,web_total=230,ready=230,failed=0。
- [x] E4. **verify** web 字段完整率 100%:230 ready web 的 `title_cn / summary_zh / final_score / content_md / embedding` 均 230/230。
- [x] E5. **verify** 浏览器抓取链路有效:本轮新增 Meta/xAI/Mistral/Cohere/AutoGen/The Batch/Qwen 共 63 条。
- [x] E6. **moved out / resolved by 015-J**:014 完成时默认 top50 被 GitHub 淹没,确认是 ranking/source_boost 问题而不是抓取问题。2026-05-18 在 015-J 中通过 `source_prior` + diversity rerank + `/api/items/lanes` 收口;`sort=score&limit=50` 实测 web 19 / github 18 / rss 13,并新增 Official Updates 专用 lane 承载官方源。
- [x] E7. **verify** 整体 failed 比例 <3% —— 修复 RSS/manual metadata fallback、Playwright no-sandbox、历史 embedding 锁死队列后,2026-05-18 实测 failed=0/716; 所有 source_type 的 content/title/summary/embedding/score 均 100%。

## 阶段 F:文档 / 收口

- [x] F1. `docs/content-truth.md` 顶部更新 2026-05-18 浏览器抓取验收结果。
- [x] F2. `docs/handoff.md` verify 命令同步更新(web + browser source SQL)。
- [x] F3. `CHANGELOG.md` 更新 v2.2.0 段落。
- [x] F4. `openspec/changes/014-web-source-coverage/proposal.md` 顶部改为 completed-for-source-coverage,并明确 ranking/old-failed 移出范围。
- [x] F5. commit + push。

## 当前最终验收快照(2026-05-18 00:17 UTC)

```sql
select count(*) total from items;                         -- 716
select source_type, processing_status, count(*) ...;
-- github ready 285
-- rss    ready 196
-- manual ready 5
-- web    ready 230

select count(*) web_total,
       count(*) filter (where processing_status='ready') ready,
       count(*) filter (where processing_status='failed') failed,
       count(title_cn) filter (where processing_status='ready') title_cn,
       count(summary_zh) filter (where processing_status='ready') summary_zh,
       count(final_score) filter (where processing_status='ready') final_score,
       count(content_md) filter (where processing_status='ready') content_md,
       count(embedding) filter (where processing_status='ready') embeddings
from items where source_type='web';
-- total=716, ready=716, failed=0; all source_type required fields complete, web_total=230
```

## 后续建议

- Ranking/source_boost 已由 015-J 初步收口;后续只做 dogfood 后的权重调参,不再阻塞 014。
- BrowserSource 性能优化:当前简单实现是每个 listing/article 启一次 Chromium,可后续改为每 source 复用 browser/page。
