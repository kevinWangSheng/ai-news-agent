**Status: planned-outline** — 等 015 落地后 + 真跑 1-2 周看到具体运维痛点再细化 tasks.md

# 018 · Ops & Tooling — 长期运行的健康监控 + CLI 加料

## 背景

015/016 是"产品本身好不好用",018 是**"系统长期跑得稳不稳、问题能不能发现"**。

跑超过 1 周后,真实运维问题会冒出来:
- 哪些源最近没新条目?(源失活了还是真没新?)
- 哪些 cron job 上次失败了?(完全没人通知)
- ingestion_errors 表在累积,UI 看不到
- CLI 投喂 5 个 URL 要点 5 次

这些不是 UI 不好用,是**没监控 / 没工具**。

## 候选项(从 v2-roadmap.md 的 E/F/G 段挑出)

### E1. 修 ~29 条 extract failed 系统调查
- 看 `last_error` 字段按 source 分类统计
- 部分通过 D3 (RSS description 兜底)已解决
- 剩下的标 `dropped` 或重试策略改
- 跟 014 阶段 D3 重合,可能不需要单独做

### E2. Scheduler 健康面板(UI)
- `/health/scheduler` 已有端点,前端没渲染
- 设计:`/settings/scheduler` 或 `/sources` 加一栏
- 每 job 显示:next_run / last_run / last_success / 最近 5 次执行结果
- 失败的高亮红色

### E3. Ingestion 错误页(UI)
- `ingestion_errors` 表已有数据,前端没暴露
- 设计:`/sources/errors`,最近 7 天按源聚合
- 看到"哪些源在拖后腿"

### G1. 源 1 周失活报警
- daily / weekly job:每源 7 天内 `created` 数 = 0 → 标 `stale`
- 不发邮件(决议),写到 `/sources` 页上标红
- 简单实用

### F1. `hub add` 批量
- `hub add < urls.txt` 从 stdin
- `hub add --from-clipboard`(Mac 上特别顺)
- 真实场景:看 newsletter 时一次想投 5 个链接

### F2. `hub digest today` 终端查看
- 调 `/api/digests?period=daily&limit=1`,rich 渲染
- 早上不开浏览器就能看本日精选

### 推迟 / 不在 018 范围

- E4 (24h 调度真观察) —— 不是任务,是验证,留 docs/handoff 即可
- G2 (e2e 测试) —— 工程债,单独 019 或永远不做
- G3 (自动归档老低分) —— 已经放 016
- 备份 / 导出 —— 放 017

## 估时(每条粗估,等真细化时再说)

| 候选 | 工作量 |
|---|---|
| E1 调查 + 决议 | 1-2 小时 |
| E2 scheduler 面板 | 半天 |
| E3 错误页 | 2-3 小时 |
| G1 失活报警 | 1-2 小时 |
| F1 hub 批量投喂 | 30 分钟 |
| F2 hub digest CLI | 30 分钟 |
| **合计粗估** | **1-1.5 天** |

## 不破坏 / 不动

- 数据库 schema 不动
- 现有 API 端点不破坏(只新增)
- scheduler 不动核心,只加 monitoring 旁路
- CLI 不破坏现有命令

## 等你 dogfood 几天后细化

到那时已经知道哪些 ops 痛点真出现了 / 哪些 false positive。届时优先级会自然清晰,不在空气里设计。
