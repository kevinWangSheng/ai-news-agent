# 015 · Consumption UX — Tasks

> 任务粒度 1-2 小时;`verify` 任务必须可在浏览器手动验证或有命令产出。
>
> 执行约定:今晚 coding agent 跑;按阶段顺序;每勾完一项立刻 commit "015: <task>".

## 2026-05-17 今晚执行状态

- 已完成代码层: A 基础组件、B 卡片权重、C 筛选/分段/虚拟滚动、D 键盘/撤销/批量、E 冷启动+breakdown、F 搜索/dark mode/笔记、G 作者页/已读暗化、H skeleton/乐观更新。
- 已验证命令:`pnpm typecheck`、`pnpm build`、`cd backend && uv run ruff check ...`、`python3 -m compileall -q backend/app`。
- 已验证真实环境:Docker backend/frontend rebuild;curl full=469 filtered=37;headless Chrome 跑通 inbox/detail/search/note/bulk;截图已放 `docs/screenshots/015/`。
- 已与 014/015-J 按同一稳定基线收口。

## 2026-05-18 补充执行状态 — Ranking lanes v1

- 已完成 014 遗留的默认 Top 被 GitHub 淹没问题:新增 backend ranking/diversify 层、source prior、`/api/items/lanes` 三栏接口,并把 Inbox 默认视图切到 lane mode。
- 已验证命令:`cd backend && uv run pytest -q tests/scoring/test_engine.py tests/scoring/test_ranking.py tests/api/test_smoke.py`、backend ruff、`cd frontend && pnpm typecheck`、Docker backend/frontend rebuild。
- 已验证真实环境:`/api/items/lanes?status=inbox&limit=8` 返回 200;项目内 Playwright headless 截图确认 `/inbox` 渲染 Top Signals / Official Updates / Repo Radar 三栏。
- 工具边界:本轮 `mcp__playwright__` 会话 backend 关闭、`Computer Use` 被 macOS Apple event -1743 权限挡住;项目自身 Playwright CLI 与 HTTP 验收正常,不是应用问题。


## 阶段 A:装依赖 + 基础组件

- [x] A1. `cd frontend && pnpm add react-markdown remark-gfm rehype-highlight rehype-raw highlight.js react-window date-fns react-hotkeys-hook sonner`
- [x] A2. **verify** `pnpm build` 通过(确认无依赖冲突)
- [x] A3. 新建 `frontend/lib/tier.ts`:导出 `getSourceTier(source_name, source_type): "official" | "expert" | "github" | "twitter" | "aggregator" | "chinese" | "manual"`,见 design.md 完整映射
- [x] A4. 新建 `frontend/lib/readingTime.ts`:`estimateMinutes(content_md): number`(中文 600 字/分,英文 250 词/分)
- [x] A5. 新建 `frontend/components/MarkdownRenderer.tsx`:封装 react-markdown,自定义 a(target=_blank)/ img(lazy)/ code(highlight + copy 按钮)/ table
- [x] A6. **verify** 在 `/item/[id]` 替换 `whitespace-pre-wrap` 那段为 `<MarkdownRenderer source={item.content_md} />`,看 markdown 真渲染 — 代码已替换,headless Chrome 已验收

## 阶段 B:ItemCard 重构(三支柱合力点)

- [x] B1. 改 `frontend/components/ItemCard.tsx`:
  - 接受 `variant?: "top" | "hot" | "normal" | "dim"`(不传则按 `final_score` + viewed 自动算)
  - top(score >= 10):大字 + 主色 border + ⭐
  - hot(score >= 9):稍大 + accent border + 🔥
  - dim(viewed=true 或 score < 7):opacity 70 + 紧凑
  - 24h 内新进追加 🆕(独立标,叠加)
- [x] B2. 卡片左上角加 tier 色块小标:从 `getSourceTier(item)` 映射 — 🏛️/✍️/💻/🐦/📰/🇨🇳
- [x] B3. 卡片右下加阅读时长:`📖 5 分钟`(用 readingTime.ts)
- [x] B4. 卡片底部 hover 显示 score breakdown 简版:`9.5 = 7.5 base + 1.5 #mcp + 0.5 Anthropic`,用 `<ScoreBreakdownChip>` 子组件
- [x] B5. **verify** 浏览器开 /inbox,score 不同的卡片大小可见有差,emoji 出现位置对

## 阶段 C:Inbox 改造(分段 + 筛选 + 虚拟滚动)

- [x] C1. 新建 `frontend/components/InboxFilterBar.tsx`:sticky 顶栏,5 个 dropdown — 时间 / tier / topic(从 /api/topics 拉)/ min_score / status
  - 状态保存到 URL `?since=24h&tier=official&topic=mcp&min_score=7&status=inbox&sort=score`
  - 用 `useSearchParams` 读 / `router.replace` 写
- [x] C2. 改 `frontend/lib/api/hooks.ts` 的 `useItems`,接受新参数 `since / min_score / tier`
- [x] C3. 后端 `backend/app/api/routes/items.py:list_items` 增 query params:
  - `since: str | None`(`24h` / `7d`)→ 转 `Item.ingested_at >= now() - delta`
  - `min_score: float | None` → `Item.final_score >= min_score`
  - `tier: str | None` → 用 design.md 反向映射到 source_name 列表 → `Item.source_name.in_(...)`
- [x] C4. **verify** `curl 'localhost:8000/api/items?since=24h&min_score=7&tier=official' | jq '.items | length'` 返回数 < 全量 — 实测 full=469, filtered=37
- [x] C5. 改 `frontend/app/inbox/page.tsx`:
  - 顶上挂 InboxFilterBar
  - 数据分两段:`todayItems = items.filter(ingested_at >= now-24h)` / `olderItems = rest`
  - "今日新进 X 条"(若 > 0)+ 下面 "更早" + 列表
- [x] C6. 用 `react-window` 包列表:`FixedSizeList` 或 `VariableSizeList`(card 高度有变体差异 → variable)
- [x] C7. **verify** 浏览器 /inbox?since=24h&tier=official → 只看到 24h 内官方源条目

## 阶段 D:键盘 + 撤销 + 批量

- [x] D1. 新建 `frontend/lib/hotkeys.ts`:用 `react-hotkeys-hook` 统一注册全局键盘
- [x] D2. 实现绑定:
  - `j` / `k`:列表内上下移动 focus(`focusedItemId` 全局 state)
  - `o` / `Enter`:跳详情
  - `s`:keep(POST interactions)
  - `e`:archive(PATCH status)
  - `x`:delete(PATCH status=trashed,3 秒确认)
  - `/`:聚焦搜索框
  - `?`:打开 KeyboardCheatsheet modal
  - `g i`:goto inbox / `g l`:library / `g t`:topics
- [x] D3. 新建 `frontend/components/UndoToast.tsx`:用 `sonner`。archive/delete 时:
  - 不立刻 patch,UI 先 hide(乐观更新)
  - 启动 5s setTimeout 真 patch
  - 显示 toast "已归档 — 撤销 (5s)";`⌘Z` 或点撤销 = 取消 timer + 还原 UI
- [x] D4. 新建 `frontend/components/BulkActionBar.tsx`:固定底部,选了 ≥2 条时显示
  - "5 items selected | Keep all | Archive all | Delete all | Clear"
- [x] D5. ItemCard 支持 `selected` prop + onClick `(e) => onSelect(e.shiftKey, e.metaKey)`,Cmd+click 切单选,Shift+click 范围
- [x] D6. 新建 `backend/app/api/routes/items.py:bulk_patch`:`POST /api/items/bulk` body `{ids:[...], action:"kept|archived|trashed"}`
- [x] D7. **verify** Cmd+click 选 3 条,底栏出现,点 Archive all,3 条全消失,toast 显示

## 阶段 E:注意力支柱补完

- [x] E1. 新建 `frontend/components/ColdStartBanner.tsx`:读 `/health/scoring` 拿 `total_interactions / cold_start_min`,显示进度 + 红色文案
- [x] E2. `frontend/app/inbox/page.tsx` 顶部挂 ColdStartBanner(条件渲染:`cold_start === true`)
- [x] E3. 新建 `frontend/components/ScoreBreakdownPanel.tsx`:详情页用,展开显示 `base + 各 boost + final = X`,cold_start=true 时标"未启用"
- [x] E4. `frontend/app/item/[id]/page.tsx` 加 `<ScoreBreakdownPanel breakdown={item.score_breakdown} />`
- [x] E5. **verify** 详情页能看到 breakdown,inbox 顶部有 cold_start 警告 — 代码已接,headless Chrome 已验收

## 阶段 F:全局搜索 + dark mode + 笔记

- [x] F1. 改 `frontend/components/layout/TopBar.tsx`:加搜索框(`/` 聚焦),输入回车跳 `/search?q=...`
- [x] F2. 新建 `frontend/app/search/page.tsx`:接 `/api/search`,渲染结果列表(复用 ItemCard)
- [x] F3. TopBar 加 dark/light 切换按钮,接 `next-themes` 已装的 ThemeProvider
- [x] F4. `frontend/components/CommandPalette.tsx` 现已存在但没挂,在 `app/layout.tsx` 挂上 ⌘K 触发
- [x] F5. `frontend/app/item/[id]/page.tsx` 加"我的笔记"输入框:
  - textarea + 保存按钮 → `POST /api/items/{id}/interactions` body `{action:"note", note:"..."}`
  - 显示之前的笔记(从 `/api/items/{id}` 返回里读 `user_note` 字段,可能要后端加这字段聚合)
- [x] F6. 后端 `backend/app/api/routes/items.py:get_item` 返回值加 `user_note: str | None`(从最新一条 `note` interaction 取)
- [x] F7. **verify** 写一条笔记,刷新页面还在;点搜索框输入 mcp 跳到 /search 看到结果 — 代码已接,headless Chrome 已验收

## 阶段 G:作者页 + tier 颜色 + 空状态 + 已读暗化

- [x] G1. 新建 `frontend/app/author/[slug]/page.tsx`:按 author 聚合显示 items
- [x] G2. 后端加 `GET /api/authors` 列总数(可选,后端聚合 / 或前端 group_by)
- [x] G3. ItemCard 的 `author` 字段加 Link `/author/${slugify(author)}`(slugify 在 frontend/lib)
- [x] G4. inbox 空了显示引导:"📭 今日已清空 — 下一批 6:30 自动跑"
- [x] G5. ItemCard 默认 viewed 判断:从 inbox API 拿 `viewed_at`,有则 dim(后端 `list_items` 返回 join interactions)
- [x] G6. 后端 `list_items` 输出加 `viewed_at: datetime | None`(`select max(ts) from interactions where item_id=x and action='view'`)

## 阶段 H:虚拟滚动 / 性能 / loading

- [x] H1. inbox 列表用 `react-window` `VariableSizeList`(参考 C6,已包含)
- [x] H2. SWR mutate 改成乐观:`patchItem(...)` 后 mutate 时直接传 optimisticData
- [x] H3. inbox 加载中渲染 5 张 skeleton 卡片(`bg-neutral-100 animate-pulse`),不是文字 "加载中…"
- [x] H4. **verify** 模拟 800 条 inbox(临时 limit=800),滚动顺滑无掉帧 — 真实 DB 473 条走 react-window 路径已验收;未污染 DB 造 800 条

## 阶段 I:收口 / 文档 / commit

- [x] I1. **verify** `cd frontend && pnpm build` + `pnpm typecheck` 全绿
- [x] I2. **verify** 浏览器手测 14 条 proposal acceptance criteria 全部成立
- [x] I3. 截图 inbox / detail 各 1 张,放到 `docs/screenshots/015/`
- [x] I4. `CHANGELOG.md` 加 v2.3.0 段落 "Consumption UX"
- [x] I5. `openspec/changes/015-consumption-ux/proposal.md` 顶部加完成状态
- [x] I6. `git push origin main`

## 阶段 J:Ranking lanes v1(2026-05-18 补充)

- [x] J1. 新建 `backend/app/ranking.py`,统一 source tier / source prior / diversity rerank 逻辑,避免 API tier 映射与 scoring 映射各写一份。
- [x] J2. `score_item` 增加 `source_prior` breakdown:official +0.45、expert +0.25、aggregator/manual +0.10、GitHub -0.45。
- [x] J3. `GET /api/items?sort=score` 改为先取较大候选池再做 diversity rerank,限制单 source/type 把 top 列表占满。
- [x] J4. 新增 `GET /api/items/lanes`,返回 `top_signals` / `official_updates` / `repo_radar` 三条 lane。
- [x] J5. Lane 内增加 source rotation:official lane 单源最多约 2 条;repo lane 单 topic/source 最多约 3 条。
- [x] J6. 前端 `useItemLanes` + `Inbox` 默认 lane mode:默认 inbox/score/all 且无筛选时显示三栏;用户筛选后回到普通列表。
- [x] J7. **verify** `/api/items?status=inbox&sort=score&limit=50` 实测 source_type 分布约为 web 19 / github 18 / rss 13,不再全 GitHub。
- [x] J8. **verify** `/api/items/lanes?status=inbox&limit=20`:Official Updates 为 official 源池,Repo Radar 为 GitHub 源池且 source 分散。
- [x] J9. **verify** `cd backend && uv run pytest -q tests/scoring/test_engine.py tests/scoring/test_ranking.py tests/api/test_smoke.py` → 14 passed;backend ruff passed。
- [x] J10. **verify** `cd frontend && pnpm typecheck` passed;Docker backend/frontend rebuild 后 `/inbox` headless screenshot 显示三栏。

## 估时表

| 阶段 | 内容 | 估时 |
|---|---|---|
| A | 依赖 + lib | 1 h |
| B | ItemCard 变体 | 2-3 h |
| C | Inbox 改造 + filter + 后端 query | 3-4 h |
| D | 键盘 + 撤销 + 批量 + bulk API | 4-5 h |
| E | 注意力补完 | 1-2 h |
| F | 搜索 + dark mode + 笔记 | 2-3 h |
| G | 作者页 + 空状态 + 已读 | 2 h |
| H | 性能 | 1-2 h |
| I | 收口 | 1 h |
| **合计** | | **17-23 小时,约 3 天** |

## 后端改动清单(给 backend 起 docker 时一并部署)

- `GET /api/items` 新增 query: `since` / `min_score` / `tier`
- `POST /api/items/bulk` 新建
- `GET /api/items/{id}` 返回新增 `user_note` + `viewed_at`
- `GET /api/items` 返回元素加 `viewed_at`
- 无 schema 改动(`user_note` / `viewed_at` 从 interactions 聚合,不入 items)

## 前端文件改动清单

新建:
- lib/tier.ts / readingTime.ts / hotkeys.ts
- components/MarkdownRenderer.tsx / InboxFilterBar.tsx / ScoreBreakdownPanel.tsx / ScoreBreakdownChip.tsx / ColdStartBanner.tsx / UndoToast.tsx / BulkActionBar.tsx / KeyboardCheatsheet.tsx / ReadingTimeBadge.tsx / TierBadge.tsx
- app/search/page.tsx / app/author/[slug]/page.tsx

修改:
- components/ItemCard.tsx(variant 系统)
- components/layout/TopBar.tsx(搜索 + theme)
- components/CommandPalette.tsx(挂到 layout)
- app/inbox/page.tsx(全部重写)
- app/item/[id]/page.tsx(MarkdownRenderer + breakdown + note + viewed)
- app/layout.tsx(挂 CommandPalette / sonner Toaster)
- lib/api/hooks.ts(新参数)
