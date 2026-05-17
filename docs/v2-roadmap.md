# v2 Roadmap — 内容覆盖 + UI 重做讨论清单

> 这是 v1 (ebd40bb..5c1c9a1) 跑起来之后,基于真实数据(369 条 items / 26 个源 / ARK 99.7% embed 命中)发现的不足 + 改进想法。
>
> **状态:全部是「待讨论」**。优先级是我的建议,不是定论。逐条 review 后,确认的会拆成 `openspec/changes/014+` 正式跑。
>
> 阅读方式:`[P0]` = 阻塞性 / 基础;`[P1]` = 高 ROI;`[P2]` = 体验提升;`[P3]` = 可能不值;每条带 **症状**(为什么需要)+ **改法**(怎么做)+ **代价**(工作量级)。

---

## A. 内容覆盖 / 数据质量

### A1. [P0] 24 个 `type: "web"` 源根本没在跑

**症状**:`backend/config.yaml` 里配了 Anthropic News / Claude Blog / Meta AI / xAI / Mistral / Cohere / LangChain Blog / Cursor / Cognition / Manus / Liquid AI / Sebastian Raschka 等 24 个 `type: "web"` 源,但 `build_rss_sources` 不区分 web / rss,所有源都走 feedparser,HTML 页面返回空。**Anthropic 官方一条都没进库**。

**改法**:
- 新建 `backend/app/ingestion/sources/web.py` 实现 `WebSource`
- 抓 listing 页 → trafilatura 提取链接列表 → 各文章页抓正文
- `build_rss_sources` 拆成 `build_rss_sources` + `build_web_sources`,各自按 `type` 过滤

**代价**:中(2-4 小时)。`WebSource` 的难点是不同站点 listing 结构差异大 —— 可能要每站点配 selector,或用 LLM 抽链接(贵)。可以先做 30% 的站(Anthropic / Claude / Cursor / Cognition / Meta AI 这几个明确想看的),其余等。

### A2. [P0] OpenAI Blog / LlamaIndex Blog extract 全失败

**症状**:OpenAI Blog 15 条 / LlamaIndex 10 条都进了 DB 但 `processing_status='failed'`。OpenAI 的文章页是 JS-rendered,`trafilatura` 抓不到正文,playwright fallback 因为容器里没装 chromium 二进制而 graceful skip。

**改法**:
- `backend/Dockerfile` runtime stage 加 `RUN playwright install chromium`(增加 ~300MB)
- 或者只在需要时安装(processing job 启动时检测 + 拉)
- 重 build backend,把 29 条失败的复活重跑

**代价**:小(30 分钟改 + 5 分钟重 build + 5 分钟重跑)。

### A3. [P1] 内容质量检查 / 体检脚本

**症状**:现在没法系统看"哪些条目 enrich 质量差"。比如 title_cn 还是英文、summary_zh 太长 / 太短、tags 不合理。enrich 是黑盒。

**改法**:
- 写 `backend/app/scripts/quality_audit.py`:
  - 检测 title_cn 含 >50% 英文 → 列出来
  - summary_zh < 30 字或 > 300 字 → 列出来
  - tags 数量 < 1 或 > 8 → 列出来
  - content_md 长度 < 200(可能 extract 不全)→ 列出来
- 输出表格,人工抽查样本
- 之后可以加规则到 enricher prompt(few-shot)

**代价**:小(1-2 小时)。

### A4. [P1] 去重质量 —— 跨源同主题

**症状**:现在去重只看 URL。GitHub `awesome-llm-agents` 和 RSS 里 Lilian Weng 的文章同时讲"agent memory",会进库两条 —— 这正是想要的。但如果同一条 OpenAI 公告被 OpenAI Blog 转 + 被 HackerNews 转 + 被 swyx 转,会进 3 条。是否要 cross-source dedup?

**改法**:
- 选项 a:embedding 余弦 > 0.95 视为同条,后到的 link 到先到的 `parent_item_id`(需要加列)
- 选项 b:不做。允许重复,UI 上 cluster
- 我建议 b,因为不同源的视角本身就是价值

**代价**:讨论后决定。

### A5. [P2] 时效性 —— 太老的进库要不要?

**症状**:RSS 默认拉 `time_window_days: 30`,但有些 source(LeCun's AMI Labs)发文极慢,30 天没新。HackerNews 又太快(每天上百条)。

**改法**:每源单独配窗口 + 上限,在 yaml 里
**代价**:小,只动 config。

---

## B. UI 渲染 / 视觉

### B1. [P0] Markdown 没渲染

**症状**:`frontend/app/item/[id]/page.tsx:69` 用 `whitespace-pre-wrap` 直接显示 `content_md`。`**bold**` `# heading` `[link](x)` 全是文本。GitHub item(很多 emoji + ``` 代码块)体验最差。

**改法**:
- 装 `react-markdown` + `remark-gfm` + `rehype-highlight`(代码 highlight)
- 自定义渲染:外链开新窗口、图片懒加载、代码块加复制按钮
- 已经装了 `tailwindcss/typography` 的 `prose` class 但只有外壳,内容不是真 HTML

**代价**:小(1 小时)。

### B2. [P1] 整体风格 —— 现在的"AI 通用风"很乏味

**症状**:`globals.css` 只设了 `--background` / `--foreground` 两个变量,纯黑白,无个性。Sidebar 朴素,Card 朴素,详情页朴素。看一眼就像 ChatGPT 模板。

**改法**(讨论方向,我列几个选项):
- a. **报刊风**:衬线字标题 + 编号引用 + 列宽收窄,像 Stratechery / TechCrunch
- b. **终端风**:JetBrains Mono + 深绿/琥珀色高亮 + ASCII 边框,像 ranger / lazygit
- c. **杂志风**:大量空白 + 大图 + Display Serif 标题,像 The Verge
- d. **效率工具风**:密度高 + 多 tab + 键盘导航,像 Linear / Raycast(**最适合"信息中枢"语境**)
- e. **保留现状但调色**:加一个主色(比如 Anthropic 橙 / Karpathy 蓝)+ 卡片层级阴影 + 字体收紧

**代价**:大(一天起步)。需要决定方向再说。

### B3. [P1] Source tier 视觉区分

**症状**:`ItemCard` 把 `source_name` 当纯文本显示。`Anthropic News` 和 `github:mcp` 和 `Twitter @karpathy` 视觉上一样轻 —— 但价值差别很大。

**改法**:
- DB 加 `source_type` 已有(`rss/github/twitter/manual/exa_search/chinese`),前端按 type 给:
  - `rss` 内根据 source_name 再分:**官方**(Anthropic / OpenAI / Google / Meta / xAI / Mistral / Cohere / Qwen / DeepMind / HuggingFace)| **专家**(Karpathy / Lilian / Simon / Eugene / Chip / Hamel / Schmid / Raschka / Huyen / Husain / Clark) | **聚合**(AINews / Latent Space / The Batch / Import AI / HackerNews)
  - 三种 tier 不同色块小标(🏛️ 官方 / ✍️ 专家 / 📰 聚合 / 💻 github / 🐦 twitter)
- 后端可以在 `source_meta` 里返回一个 `tier` 字段,前端直接渲染

**代价**:小(1-2 小时,主要是 tier 字典 + Card 改色)。

### B4. [P2] 卡片信息密度 / 多形态

**症状**:无论是 GitHub repo 还是博客文章还是 tweet,卡片长得都一样。GitHub repo 应该显示 stars / 语言;tweet 应该显示作者头像 + 短文本;文章应该显示阅读时长。

**改法**:`ItemCard` 内部按 `source_type` 分 render —— GitHubCard / TweetCard / ArticleCard。复用大部分布局但局部差异化。

**代价**:中(半天)。

### B5. [P2] 日期 / 时间显示

**症状**:`{item.published_at.slice(0, 10)}` 显示 `2026-05-15` —— 不知道距今多久。"5 月 15 日" / "3 天前" 更直觉。

**改法**:`date-fns` 或自实现 `formatRelative`。

**代价**:超小(15 分钟)。

### B6. [P2] 暗色 / 亮色切换

**症状**:Tailwind 自动跟系统,但用户没有手动切的开关。

**改法**:`next-themes` 已经装了,只缺 TopBar 按钮。

**代价**:超小。

---

## C. 导航 / 浏览方式

### C1. [P0] Inbox 必须能筛选

**症状**:`/inbox` 现在是一个扁平的 50 条列表,无筛选无排序。340 条 ready 全堆在那。

**改法**:
- 顶部 sticky 工具栏:
  - **时间**:今天 / 本周 / 全部
  - **来源 tier**:官方 / 专家 / GitHub / Twitter / 聚合 / 中文
  - **主题**:从 topics.yaml 的 34 个主题点选
  - **分数**:>= 6 / >= 8 / 全部
- 状态写到 URL `?since=24h&tier=official&topic=mcp` —— 收藏 / 分享 / 后退
- 用 `useSearchParams` 实现

**代价**:中(半天)。

### C2. [P1] 键盘流(J/K/A/T/Space)

**症状**:Memory 说 v1 设计了"键盘流 keep/archive/trash"。代码里没看到实现。

**改法**:全局键盘 hook:
- `J/K` 上下条目(列表 + 详情)
- `O / Enter` 打开详情
- `K (keep)` / `A (archive)` / `D (delete)`
- `R` reload
- `/` 聚焦搜索
- Cheatsheet 用 `?` 弹出

**代价**:中(2-3 小时)。

### C3. [P1] CommandPalette(⌘K)真用起来

**症状**:`components/CommandPalette.tsx` 文件存在,但没看到挂在 layout。`cmdk` 装了,空跑。

**改法**:
- 全局 ⌘K / Ctrl+K 唤出
- 输入即搜:items / topics / entities / sources
- 跳转命令(`go inbox`, `go karpathy`)
- 最近访问

**代价**:中(半天)。

### C4. [P1] 作者页

**症状**:item 有 `author` 字段(`Lilian Weng` / `karpathy`),但前端没有 `/author/[slug]` 页面。

**改法**:加路由 + API `/api/authors`(按 author 聚合)+ 显示该 author 的全部 items + 关键统计(总条数 / 平均分 / 最近一篇)。

**代价**:小(2 小时)。

### C5. [P2] 信源页 `/sources` 真有用

**症状**:`/sources` 路由已存在,但内容平淡(46 个源列表)。可以做成"信源管理 + 健康面板"。

**改法**:每源显示 last_run / 24h 入库数 / extract 成功率 / 平均分 / 一键禁用。这能让你看到哪些源在拖后腿。

**代价**:中(半天,后端要补统计端点)。

### C6. [P2] Topic / Entity 详情页加时间线

**症状**:`/topics/[slug]` 现在好像是 placeholder。但 002 的设计是按月柱状时间线 + 相关 item 列表。

**改法**:对照 openspec/changes/010 检查实现,补缺失部分(可能已经做了,需要 dogfood 确认)。

**代价**:小到中。

### C7. [P2] 全文搜索 UI

**症状**:`/api/search?q=` 已经 work(我用 curl 验过),但前端没搜索框页面。

**改法**:`/search?q=` 页面 + CommandPalette 集成。后端已支持 tsvector + 向量混合 — 前端只挂 UI。

**代价**:小(1-2 小时)。

---

## D. 个性化 / 智能

### D1. [P1] Score breakdown 可见

**症状**:`score_breakdown` JSON 在 DB 里(`base / tag_boost / source_boost / entity_boost / time_decay / focus_hits / cold_start`),但前端没渲染。看到 `score=9.0` 不知道为什么。

**改法**:Card 上 hover 显示;详情页固定显示。**且 cold_start=true 要明确标红提示"还没到 50 次交互,推荐未启用"**。

**代价**:小(1 小时)。

### D2. [P1] Trending —— 多源 cluster

**症状**:5 个独立源同一天讨论"Computer Use"是强信号,但现在它们散在列表里。

**改法**:
- 用 embedding cosine > 0.85 做 daily clustering
- 单独 `/trending` 或在 inbox 顶部"今日热议 3 个话题"
- 点进去看属于这个 cluster 的所有 item

**代价**:中(半天)。

### D3. [P2] 状态机扩展

**症状**:现在 `status` 只有 `inbox / kept / archived / trashed`。深度阅读队列 / 已分享 / 待跟进等都没有。

**改法**:加几个 status:`deep-read`(深读队列)、`shared`(已分享)。或抽象为 `labels` 字段(数组)更灵活。
**代价**:讨论后决定;DB schema 影响小。

### D4. [P2] /ask 对话型 retrieval

**症状**:已经有 340 条向量 + Anthropic key,可以做"问个问题,从库里挑答案 + 回答"。这是从 reader 升级到 second brain 的关键。

**改法**:
- `/ask` 页面 / 接口
- 用 `embedding 余弦` 召回 top-k → Claude prompt 答 + 引用 item links
- 是 RAG 的最小实现

**代价**:中(1 天)。

### D5. [P3] Digest 真用起来 + LLM 调优

**症状**:`/digest` 页面渲染基本信息,LLM intro 看起来在 012 已经接入。但效果未知 —— 没人看过实际产物。

**改法**:scheduler 自动跑过几次后,人工 review 几篇,调 prompt + 选条策略。
**代价**:讨论后决定。

---

## E. 运维 / 监控

### E1. [P1] 29 条 extract failed 调查

**症状**:有 29 条永远卡在 failed。

**改法**:看 `last_error`,按 source 分类。多半是 OpenAI / LlamaIndex 在 A2 修了 chromium 后会救回来一部分;剩下的可能是无效 URL,直接 mark `dropped`。

**代价**:小(30 分钟调查 + 看情况修)。

### E2. [P1] Scheduler 健康面板

**症状**:`/health/scheduler` 端点存在,但前端没有可视化。每个 job 上次成功 / 下次执行 / 失败原因都看不到。

**改法**:`/settings` 或 `/sources` 加面板;读 `apscheduler_jobs` 表 + 内存里的 last_run 状态。

**代价**:中(半天)。

### E3. [P2] Ingestion 错误页

**症状**:`ingestion_errors` 表在记日志,但前端没暴露。

**改法**:`/sources/errors` 或类似,看最近 24h 各源的错误。

**代价**:小(1 小时)。

### E4. [P3] 真 24h 跑下来看数据增长

**症状**:scheduler 装好刚跑几小时,没看完整 24h 周期。

**改法**:**等**。然后跑 `select date_trunc('hour', ingested_at) AS h, count(*) FROM items GROUP BY 1 ORDER BY 1;` 看分布。

**代价**:0(让时间过)。

---

## F. CLI / 投喂

### F1. [P2] `hub add` 批量

**症状**:每次只能投一个 URL。如果有一篇文章里嵌入 5 个推荐链接,要手动 5 次。

**改法**:`hub add < urls.txt` 或 `hub add --from-clipboard`。

**代价**:小(30 分钟)。

### F2. [P3] `hub digest today` 终端看摘要

**症状**:每天 06:30 自动生成的 digest,只能在 web 看。CLI 直接看更顺手。

**改法**:`hub digest` 调 `/api/digests?period=daily&limit=1`,rich 渲染。

**代价**:小。

---

## G. 测试 / 健壮性

### G1. [P2] 一个 source 一周失活报警

**症状**:RSS 源换了 URL / 关站,我们这边 ingestion_errors 记一条,但不会主动通知。

**改法**:scheduler 加 weekly job,检查每源 7 天内入库数,若 = 0 标记 stale。**没有邮件通道(决议)**,所以放 `/sources` 页面显示。

**代价**:小(1 小时)。

### G2. [P3] e2e 测试

**症状**:目前测试都是单测。docker 起来 + 真 API 的 e2e 没有。

**改法**:`backend/tests/e2e/` + GitHub Actions(虽然我们决议不用 Actions 跑 ingestion,但跑测试可以)。

**代价**:中。

---

## 排队建议(我的)

如果一周可以推进,顺序建议:

**Day 1 — 内容补齐(没数据谈什么 UI)**
- A2 装 chromium(30 分钟)
- A1 实现 WebSource for 5 个核心站(Anthropic / Claude / Cursor / Meta / xAI)(3 小时)
- 重跑 → 看数据涨

**Day 2 — 渲染基础**
- B1 markdown 渲染(1 小时)
- B3 source tier 视觉区分(2 小时)
- B5/B6 日期 + 暗色切换(30 分钟)
- D1 score breakdown 可见(1 小时)

**Day 3 — 浏览 UX**
- C1 inbox 筛选工具栏(半天)
- C2 键盘流(2-3 小时)

**Day 4 — 风格决定**
- 讨论 B2(报刊 / 终端 / 杂志 / 效率工具 / 现状改调)
- 选定后,半天到一天落地

**Day 5+** — 智能层(D2 trending / D4 /ask)+ 运维(E1 / E2)

---

## 等你选

你逐条 review 这份单子,告诉我:
- 哪些直接 ✅ 我去做
- 哪些 ❌ 不要
- 哪些 🤔 改一下范围
- 哪些 ⏸ 推迟到更后面
- 我漏了什么必须加

确认后我会拆成对应的 `openspec/changes/014-*` 跑。
