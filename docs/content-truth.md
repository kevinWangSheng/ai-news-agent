# 内容真相报告 — 配置 vs 实际

> 不是评估 UI、不是讨论效率,只回答两件事:
>
> 1. 配的源里有多少没在跑?
> 2. 跑下来的数据质量怎么样?
>
> 数据采样日期 2026-05-17,基于 369 条已入库 items + config.yaml 实测。

> 2026-05-18 update: change 014 已完成 HTTP + Chromium/Playwright `WebSource` Docker DB 验收并清零历史 failed：items=716，ready=716，failed=0；所有 source_type 的 `content_md / title_cn / summary_zh / final_score / embedding` 完整率均 100%。web=230，web ready=230，核心源已入库并 ready：Anthropic 14、Claude 20、Cursor 10、Meta 12、xAI 10、Mistral 9、Qwen 5、Cohere 10、AutoGen 10、The Batch 7。剩余问题不在抓取/处理层：按当前 final_score top50 仍全是 GitHub，需要后续 source_boost/ranking 修正。本文下方原始审计保留为变更前基线。

---

## 1. 源覆盖 —— 配了 42 个,17 个 critical/high 没在跑

### 1.1 整体对账

| Bucket | RSS(代码实现且 work)| Web(代码没实现) | 缺口 |
|---|---|---|---|
| official_blogs | 5 | **22** | **22 个官方源全空** |
| expert_blogs | 8 | 1(Sebastian Raschka)| 1 |
| aggregator_sources | 3 | 1(The Batch)| 1 |
| research_sources | 2 | 0 | 0 |
| **合计** | **18** | **24** | **24 个未实现** |

### 1.2 critical 优先级的 9 个源里,7 个没在跑

| 名字 | 配置 type | 状态 |
|---|---|---|
| OpenAI Blog | rss | ⚠️ 入库 15 条,**正文 extract 全 failed**(JS 渲染 + 403) |
| **Anthropic News** | web | ❌ 0 条入库,**代码没实现 web type** |
| **Claude Blog** | web | ❌ 同上 |
| Google AI Blog | rss | ✅ 15 条入库 + extract OK |
| Google DeepMind | rss | ✅ 15 条 + extract OK |
| **Meta AI Blog** | web | ❌ 同上 |
| **xAI News** | web | ❌ 同上 |
| **LangChain Blog** | web | ❌ 同上 |
| **Thinking Machines Lab** | web | ❌ 同上 |

**真实情况:critical 源 9 个里,只有 Google AI / DeepMind 这 2 个完整 work**。

### 1.3 24 个 web 源真实可抓性(实测 curl)

实际拉了一次 listing 页,按返回结构分类:

| 类别 | 数 | 名单 |
|---|---|---|
| ✅ **直接 curl + UA 就能拿** | **17** | Anthropic, Claude, Cohere, LangChain, Thinking Machines, Cognition, Cursor, Reka, Liquid AI, Sierra, Glean, Magic.dev, Browserbase, World Labs, Manus, Genspark, Sebastian Raschka |
| 🔧 JS 渲染(playwright 必需)| 5 | xAI, Mistral, Qwen, AutoGen, The Batch |
| 🔍 URL 错 / 站点死 | 2 | Meta AI, AMI Labs (LeCun) |

**结论:71% 的 web 源用最朴素的 HTTP+trafilatura 就能抓**。加 playwright 覆盖到 92%。不存在"理论上做不到",**就是代码没实现这个 source type**。

### 1.4 OpenAI 文章 403 问题

OpenAI 文章 RSS 进了 15 条,但每条文章页直接 curl 是 `HTTP 403`。需要:
- a. 装 chromium + playwright 走 JS 渲染
- b. 或用 Anthropic 帮忙抓正文(贵)
- c. 或换个 UA / 代理(脆,不推荐)

a 是已有方案,只是 backend Dockerfile 没装 chromium 二进制。

---

## 2. 已有 340 条数据的质量

只看跑通的 340 条。

### 2.1 字段完整度

| 字段 | 完整率 |
|---|---|
| title_cn | 100% |
| summary_zh | 100% |
| content_md | 100% |
| tags | 100% (5-8 个) |
| quality_score | 100% |
| final_score | 100% (含 ARK embed → 评分链路全通) |

### 2.2 summary 长度分布

| 长度区间 | 条数 | 占比 |
|---|---|---|
| < 30 字 | 0 | 0% |
| 30-80 字 | 0 | 0% |
| **80-200 字** | **262** | **77%** |
| 200-400 字 | 78 | 23% |
| > 400 字 | 0 | 0% |

✅ 完全合理,没有过短(信息不足)或过长(冗余)。

### 2.3 tag 数量分布

| n_tags | 条数 |
|---|---|
| 5 | 29 |
| 6 | 77 |
| 7 | **233** |
| 8 | 1 |

✅ enricher prompt 锁 7 个 tag,执行良好。

### 2.4 title_cn 中文化程度(看汉字占比)

| 中文占比 | 条数 | 占比 |
|---|---|---|
| 主要中文 (>=80%) | 42 | 12% |
| 50-80% 中文 | 102 | 30% |
| 30-50% 中文 | 135 | 40% |
| **几乎全英文 (<30%)** | **61** | **18%** |

抽样看真实情况:
- `LangChain — Agent 工程平台` —— 半英半中,但 LangChain 是专名,这种 OK
- `Geargrafx:PC Engine/TurboGrafx-16 模拟器与嵌入式 MCP 调试服务器` —— 专名居多,可以接受
- 真正"懒了没翻译"的不多,但 prompt 可以再激进点

**结论:enrich 质量整体合格,无系统性问题**。可改进点是 title_cn 的中文化激进度(prompt 调整,小活)。

### 2.5 失败的 29 条

全部卡在 extract 阶段:
- OpenAI Blog 15 条:文章页 403 + JS 渲染
- LlamaIndex Blog 10 条:Cloudflare / 反爬
- 其他 4 条:个别 RSS link 失效

**这 29 条不是 enrich 烂,是从头就没拿到正文**。

---

## 3. 优先级建议(只针对内容,UI 先放一边)

### 3.1 P0 —— 一周内解决,直接 +17 个官方 / 创业团队源

**实现 `WebSource`**(`backend/app/ingestion/sources/web.py`):
- 拉 listing 页(curl + UA + 30s 超时)
- 正则 / trafilatura 提取文章链接
- 各文章页走现有 extract.py 流水线
- 每个 source 配 `link_pattern` 可选(精细控制要不要 `/blog/*` 这种)

预期效果:Anthropic / Claude / Cursor / Cohere / Reka / Liquid AI / Thinking Machines 等 17 个 critical / high 源全部进库。**库存从 369 涨到 600-1000+,且头部信源(尤其是 Anthropic)有真实覆盖**。

代价:**2-4 小时单源实现 + 1-2 小时调试**。

### 3.2 P0 —— 修 OpenAI / LlamaIndex 文章 extract

`backend/Dockerfile` runtime stage 加:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libxkbcommon0 libdrm2 libgbm1 libasound2 libatk-bridge2.0-0 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
 && rm -rf /var/lib/apt/lists/*
RUN playwright install chromium
```

加完镜像约 +300MB。然后把 29 条 failed 复活重跑。

代价:**30 分钟 + 重 build 5-10 分钟**。

### 3.3 P1 —— 5 个 JS 渲染源接入

`xAI, Mistral, Qwen, AutoGen, The Batch` 的 listing 也用 playwright 拉,而不只是文章页。可以在 WebSource 里加 `js_render: true` 配置。

代价:1-2 小时(playwright + WebSource 整合)。

### 3.4 P2 —— 修 Meta / AMI Labs URL

Meta `ai.meta.com/blog` 404,需要找正确 URL(可能是 `https://ai.meta.com/research/publications/` 或 `https://about.fb.com/news/category/ai/` 单独适配)。AMI Labs 连不上,可能站点真死了,直接禁用。

代价:30 分钟。

### 3.5 P2 —— enrich title_cn 中文化激进度

调 `backend/app/processing/enricher.py` 的 prompt,加示例 / 规则:"专名保留英文,描述部分必须中文"。

代价:15 分钟 prompt 调 + 跑 100 条样本对比。

### 3.6 P3 —— 跨源去重(同主题多源覆盖)

可不可以做,但**不建议现在做**。原因:同一个主题在不同源出现是有价值的信号(B2 节讨论的 trending)。等真 dogfood 一段时间,看到底有多少重复才决定。

---

## 4. 我的建议

**第一波就做 3.1 + 3.2**,顺序:

1. **先做 3.2**(30 分钟):装 chromium 后重 build,救回 OpenAI Blog 等 29 条 failed
2. **再做 3.1**(半天):实现 WebSource for 17 个 OK 源,Anthropic / Claude 等全进库
3. 跑一遍数据,**库存达到 500-800 条**
4. 再 review 一次质量(可能要做 3.5 调 prompt)
5. 然后才进入 UI 讨论

3.3 / 3.4 / 3.5 是后续小补;3.6 推迟。

---

## 5. 等你确认

- ✅ 3.1(WebSource for 17 个源) → 我去拆 `openspec/changes/014-web-sources/` 落地
- ✅ 3.2(chromium 修 extract)→ 单独 commit / 或合并进 014
- 🤔 3.1 范围调整(只先做 critical 9 个,还是一口气 17 个?)
- ⏸ 3.3-3.6 排队

或者你看到这份报告觉得我哪里看错了 / 漏了,直接说。
