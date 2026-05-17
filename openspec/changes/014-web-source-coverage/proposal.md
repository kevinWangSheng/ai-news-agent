**Status: pending** — 范围已收窄(2026-05-17,用户确认):**只做纯 HTTP 路径的 17 个站**,阶段 C(chromium + JS 渲染)推迟到 015 或更后。OpenAI / LlamaIndex / xAI / Mistral / Qwen / AutoGen / The Batch 这 7 个站本 change 不解决。

# 014 · Web Source Coverage — 把 24 个 `type: web` 源真正接进来

## 背景

v1 (`ai-news-agent`) 升级到 v2 之后,`backend/config.yaml` 里配了 42 个源,其中 24 个标为 `type: "web"`(Anthropic News / Claude Blog / Cursor / LangChain Blog / Thinking Machines Lab / ...)。

但在 003-ingestion-sources 实现时,只写了 `RssSource`。`build_rss_sources` 函数不按 type 过滤,把所有源都送给 feedparser —— HTML 页面被当 RSS 解析,静默返回 0 条。

**实测结果**(2026-05-17):
- 369 条 items 入库,**0 条来自 Anthropic / Claude 等关键官方源**
- critical 优先级 9 个源里,只有 Google AI / DeepMind 2 个完整 work
- OpenAI Blog 入库 15 条但**正文 extract 全 failed**(JS 渲染 + 403)
- 现在用户打开 inbox 95% 是 GitHub repo,根本看不到官方厂商的内容

详细体检:[`docs/content-truth.md`](../../../docs/content-truth.md)

## 目标(验收)

跑完本 change 后:

1. `backend/app/ingestion/sources/web.py` 存在,实现 `WebSource`
2. `Anthropic News` / `Claude Blog` / `Cursor` 至少 3 个站,跑完一次 `python -m app.ingestion.run web`,DB 有 ≥30 条来自这 3 站的 items 进入 inbox
3. 跑完 5 阶段 pipeline,这些 items 完整 `ready`,有 title_cn + summary_zh + final_score
4. 启用全部 17 个"curl OK"的 web 站,**预期 24h 库存涨到 600-1000**
5. `processing_status='failed'` 的总数比当前 29 条**下降 50% 以上**(救回 OpenAI / LlamaIndex 等)

## 范围

### 本 change 做

- 实现纯 HTTP 的 `WebSource`(listing → 链接抽取 → 文章页 → trafilatura 提正文)
- 给 Dockerfile 加 chromium + playwright fallback,**让 `_fetch_via_playwright` 真正能用**(目前 graceful skip)
- 启用 17 个"curl OK"的站
- 处理 5 个 JS 渲染站(xAI / Mistral / Qwen / AutoGen / The Batch)—— **listing 也走 playwright**
- 修 Meta AI URL 配置 / 禁用 AMI Labs
- 重跑全量数据 + 二次质量审计

### 本 change 不做

- enrich prompt 改进(放 015,跟"内容质量提升"一起)
- UI 重做(放 016+)
- 跨源去重 / trending(放更后)

## 设计取舍

### 1. WebSource 用 HTTP 还是直接全部 playwright?

**选 HTTP 优先,playwright 兜底**。17/24 站点 curl 就能拿 → playwright 慢、占资源、需要 chromium 二进制。优先走快路径。

具体策略:
```
fetch listing:
  1. trafilatura.fetch_url(url, with UA)  → 拿 HTML
  2. 如果 HTML 没有任何 href="/blog/..." 等链接 → fallback playwright
extract article:
  1. trafilatura.extract(article_html) → markdown
  2. 长度 < 500 字符 → fallback playwright
```

### 2. 链接提取规则

每站结构不同。先用通用规则,后续按需 per-source 覆写:

通用:
- 找 `<a href="...">` where href 匹配站点配的 `link_pattern`(配置默认 `^/(blog|news|post|p)/.+`)
- 同 host 优先;外链跳过
- 去重

per-source 覆盖(`config.yaml` 里加可选 `link_pattern`):
```yaml
- name: "Anthropic News"
  type: "web"
  url: "https://www.anthropic.com/news"
  link_pattern: "^/news/[a-z-]+$"
```

### 3. 抓取频率

跟 RSS 一样按 cron 一小时一次(走 `ingestion_rss` 还是新加 `ingestion_web` 一个 job?)。

**选择**:新加 `ingestion_web` job,错峰 `:55`,降低同时打外部站的并发。

### 4. chromium 装哪个层

- `backend/Dockerfile` runtime stage 加 chromium + 系统依赖
- 镜像体积 +300MB(可接受)
- **或者**:只在 scheduler image 装,backend image 不装 —— playwright 只在 extract 阶段用,而 extract 由 scheduler 触发 → 但 backend 也跑 processing_loop API,会用到。**结论:都装,共享同一 image 简单**。

## 不破坏

- 现有 RSS 18 个源继续工作,不动 `rss.py`
- DB schema 不动
- API / 前端不动
- scheduler 已有 cron 不动,新加一个 `ingestion_web`

## 完成定义

- `processing_status` 分布:`ready / failed` 比例从 92/8 提到 ≥97/3
- 库存:items ≥ 600
- inbox 默认 50 条里,至少 5 条来自 `Anthropic News` 或 `Claude Blog`(用 SQL 验证)
- 新写的 `WebSource` 单测 ≥ 3 个(listing 解析 / 链接过滤 / 单文章抓取)
- `proposal.md` 顶上加 `Status: completed (YYYY-MM-DD)`

## 可能踩到的坑

- 各站 listing 结构差异大,通用正则会漏;**接受 80% 命中,剩下用 per-source link_pattern**
- chromium 在 colima VM 里跑慢(arm 模拟 x86?)—— colima 默认是 arm,chromium 也有 arm 版,应该不慢
- 某些站(xAI)有 Cloudflare bot challenge,即使 playwright headless 也可能被识别;**这种站允许直接放弃,标记 disabled**
- trafilatura 对中文页面(Qwen)的提取质量未知
