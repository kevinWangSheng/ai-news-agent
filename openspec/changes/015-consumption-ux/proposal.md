**Status: completed + ranking-lanes-v1 (2026-05-18)**

## 2026-05-17 当前状态

今晚已落地并真实验收 015 的核心可用链路:Markdown 详情渲染、source tier/阅读时长、inbox URL 筛选与今日/更早分段、高分卡片视觉权重、score breakdown/cold_start 可见、键盘流、5 秒撤销 toast、批量动作、全局搜索页、作者页、详情笔记、后端 since/min_score/tier/bulk/viewed_at/API authors。

已验证:`cd frontend && pnpm typecheck`、`cd frontend && pnpm build`、`cd backend && uv run ruff check ...`、`python3 -m compileall -q backend/app`、Docker backend/frontend rebuild、curl API 验收、headless Chrome 浏览器验收。截图在 `docs/screenshots/015/`。

补充修复:`/api/search` query embedding 已改为 ARK → Voyage → OpenAI,避免有 ARK key 时仍优先撞 Voyage 401。

014/015/015-J 已按同一稳定基线收口;016/017 仍按原计划等 015 使用反馈后再细化。

## 2026-05-18 补充状态 — Ranking lanes v1

014 完成后遗留的核心体验问题是:内容已经抓到,但默认 Top 仍可能被 GitHub/repo 类内容占满,官方与专家内容在阅读界面里没有稳定曝光位。该问题已在 015 补充收口:

- scoring 增加 `source_prior`,让 official/expert/aggregator/GitHub 的默认权重更符合阅读价值。
- `GET /api/items?sort=score` 增加 diversity rerank,避免单一 source/type 占满默认 top。
- 新增 `GET /api/items/lanes`,把默认消费面拆为 `top_signals` / `official_updates` / `repo_radar`。
- Inbox 默认状态切到三栏 lane UI;筛选条件变化后仍回到原有列表/虚拟滚动模式。

验证:backend 相关 tests 14 passed + ruff passed;frontend typecheck passed;Docker backend/frontend rebuild;`/api/items/lanes` 返回 200;项目内 Playwright headless 截图确认 `/inbox` 已渲染三栏。工具层的 MCP Playwright/Computer Use 权限失败已确认不是应用失败。

# 015 · Consumption UX — 渲染 + 浏览 + 注意力

## 背景

014 跑完后,DB 预计有 600-800 条 ready items。但当前 frontend 有三个硬伤:

1. **渲染层**:`/item/[id]` 用 `whitespace-pre-wrap` 显示 markdown,`**bold**` `# h1` ```` ``` ```` 代码块全是原文。
2. **浏览层**:`/inbox` 是 50 条扁平列表,无筛选无排序,600+ 条根本没法用。
3. **注意力层**:所有卡片视觉重量一样,9.5 分跟 6.0 分长得一模一样,眼睛不知道往哪看;`score_breakdown` 在 DB 里但前端从不渲染;`cold_start=true` 警告完全没暴露。

完整诊断见 [`docs/v2-roadmap.md`](../../../docs/v2-roadmap.md) B / C / D 三节。

## 目标(验收)

跑完本 change,以下场景必须成立:

1. `/item/N` 详情页中 markdown 正常渲染(标题层级、加粗、代码块带 highlight、链接新窗口打开)
2. `/inbox` 顶部有 sticky 筛选栏,支持「时间 / 来源 tier / 主题 / 最低分 / 状态」5 维过滤,URL 同步
3. inbox 高分卡片视觉显著大于低分卡片,满分有 ⭐ 标,9-10 有 🔥 标,24h 内新进有 🆕 标
4. 详情页固定显示 score breakdown(`base 7.5 + tag_boost 1.5 (#mcp) + source_boost 0.5 (Anthropic) = 9.5`)
5. cold_start=true 时 inbox 顶部红色横幅:"还没到 50 次交互(目前 N),推荐未启用,先正常 keep/archive"
6. 已查看过的(`interactions.action='view'`)卡片在 inbox 暗化 70%
7. 顶栏全局搜索框 + dark mode 切换
8. archive/delete 后有 5 秒撤销 toast(`⌘Z` 也行)
9. 支持 shift+click 范围选 / Cmd+click 单选 → 底部 BulkActionBar 批量动作
10. 全局键盘流:`j/k` 上下导航、`s` keep、`e` archive、`x` delete、`o/Enter` 打开详情、`/` 聚焦搜索、`?` cheatsheet
11. 来源 tier 颜色编码(🏛️ 官方 / ✍️ 专家 / 💻 GitHub / 🐦 Twitter / 📰 聚合 / 🇨🇳 中文)
12. 卡片 + 详情页显示阅读时长估算("5 分钟读完")
13. item 详情页有"我的笔记"输入框 → 写入 `interactions.action='note', content=...`
14. 600+ 条 inbox 列表用虚拟滚动,首屏 < 1s 加载

## 范围

### 本 change 做

| 支柱 | 子项 |
|---|---|
| **A 渲染** | A1 markdown 渲染 / A2 来源 tier 视觉 / A3 日期相对时间 / A4 dark mode 切换 / A5 阅读时长 |
| **B 浏览** | B1 inbox 筛选栏 / B2 键盘流 / B3 CommandPalette ⌘K / B4 作者页 / B5 全局搜索栏 |
| **C 注意力** | C1 今日分段 / C2 高分卡片放大 / C3 重点 emoji 标 / C4 score breakdown 可见 / C5 cold_start 警告 / C7 已读暗化 / C9 tier 色编码 / C10 空状态引导 |
| **D 友好交互** | D1 撤销 toast / D2 批量选 / D3 全局搜索栏(同 B5) / D4 阅读时长(同 A5) / D6 笔记 UI |
| **E** | E5 "为什么看到这条"(与 C4 合并) |
| **H** | H1 虚拟滚动 / H2 乐观更新 / H3 loading skeleton |

### 本 change 不做(留给 016+)

- C6 trending cluster(D2 from v2-roadmap)→ 016
- C8 「今天最值得读」头部块 → 与 C1/C2 合并,不单做
- D5 Reader Mode → 017
- D7 阅读进度条 → 017
- E1 主题/实体 follow + alerts → 016
- E2 信源 mute/boost UI → 016
- E3 自定义主题 → 016
- E4 导出 / 备份 → 017
- F1/F2/F3/F4 LLM 二次加工 → 016 主菜
- G1 onboarding / G2 手机响应 / G3 自动归档老低分 / G4 review 页 → 017
- H4 可访问性系统改造 → 017

### 不动

- DB schema 不动
- 后端 API 端点:**新增 2 个,不破坏现有**:
  - `GET /api/items` 加 query 参数:`since`(`24h`/`7d`)、`min_score`、`tier`
  - `GET /api/items/{id}/related` 已存在,无需改
  - **新加** `POST /api/items/bulk` for 批量动作
- scheduler 不动

## 设计取舍(详见 design.md)

1. **tier 在前端用常量映射**,不动后端。原因:UI 概念,不该污染 DB;后续要改 mapping 不需要迁移
2. **markdown 用 `react-markdown` + `remark-gfm` + `rehype-highlight`**,自定义 link / image / code 渲染
3. **键盘绑定参考 Gmail / Linear**:j/k 导航 / s 保留 / e 归档 / x 删除 / o 打开 / / 搜索 / ? cheatsheet
4. **撤销实现**:archive/delete 时不立即 patch,而是先 UI 隐藏 + 启动 5s timer,timer 到点才真 patch。`⌘Z` 取消 timer
5. **虚拟滚动用 `react-window`**:简单稳定,SSR 友好
6. **状态在 URL**:`?since=24h&tier=official&topic=mcp&min_score=7` 用 `useSearchParams` 同步,后退/收藏可用

## 工作量预估

| 阶段 | 内容 | 估时 |
|---|---|---|
| A | 装依赖 + 基础组件 | 半天 |
| B | InboxFilterBar + URL state | 半天 |
| C | ItemCard 变体 + score breakdown + 今日分段 | 半天 |
| D | 键盘 + 撤销 + 批量 | 半天 |
| E | 后端 query 参数补 + bulk API | 半天 |
| F | dogfood + bug 修 | 半天 |
| **合计** | | **3-4 天** |

## 不破坏 / 兼容

- 现有 /inbox URL 无 query 时,行为跟现在一样(默认 status=inbox, limit=50)
- 现有 PATCH /api/items/{id} 不变,bulk 是新增
- ItemDetail 字段不变,只是前端开始用它

## 完成定义

- 全部 14 条目标都可手动验证(详情见 tasks.md verify 命令)
- `pnpm build` 通过,无 TS error
- `pnpm typecheck` 通过
- 浏览器手动跑通:打开 /inbox 看到分段 + 筛选 + 暗化,点开任意 item 看到 markdown 渲染 + breakdown + 笔记
- 顶上 `Status: completed (YYYY-MM-DD)`
