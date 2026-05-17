# OpenSpec — ai-agent-hub 升级规划

本目录是把 `ai-news-agent`(单向新闻聚合)升级为 `ai-agent-hub`(个人 AI 信息中枢)的全部规划。
**这里只有规划文档,没有代码。执行 agent 按下文流程消费。**

---

## 目录布局

```
openspec/
├── README.md              ← 你现在看的
├── project.md             总目标 / 架构 / 现状→目标对照 / 复用映射
├── specs/                 目标能力规范(WHAT — 升级完成后系统应具备什么)
│   ├── ingestion.md
│   ├── processing.md
│   ├── storage.md
│   ├── retrieval.md
│   ├── interaction.md
│   └── ui.md
└── changes/               变更包(HOW — 怎么从现状走到目标)
    ├── 000-plan-corrections/      ← 规划文档修订,必须先做(只动 openspec/)
    ├── 001-foundation/
    ├── 002-data-model/
    ├── 002a-source-tuning/        ← 信源关键词整治,与 002 并行,在 003 之前
    ├── 003-ingestion-sources/
    ├── 004-processing-pipeline/
    ├── 005-preference-scoring/
    ├── 006-rest-api/
    ├── 007-manual-ingest/
    ├── 008-frontend-scaffold/
    ├── 009-frontend-inbox-library/
    ├── 010-frontend-topics-entities-timeline/
    ├── 011-frontend-digest/
    ├── 012-scheduler-migration/
    └── 013-decommission-old/
```

每个 `changes/NNN-*/` 内含:
- `proposal.md` — 这次变更要做什么 / 为什么 / 验收标准
- `tasks.md` — 原子任务清单(checkbox,执行时改成 `[x]`)
- `design.md` — 仅在需要技术决策时存在(部分变更没有)

---

## 执行流程(给执行 agent 看)

### 1. 启动
- 进入此仓库,读 `openspec/project.md` 拿到全局架构
- 读 `openspec/specs/` 下相关的能力规范,知道目标长什么样
- 看 `openspec/changes/` 找下一个 `Status: pending` 的变更(从 001 开始)

### 2. 执行一个变更
- 读对应 `proposal.md` 拿到背景、目标、验收
- 按 `tasks.md` 顺序做,完成一项把 `[ ]` 改成 `[x]`,**单次提交可以只完成 1-N 项,不必一口气吃完**
- 遇到 `design.md` 引用,先读完再动手
- 改动落到代码上 → 跑验收 → 在 `proposal.md` 顶部加一行 `Status: completed (YYYY-MM-DD)`

### 3. 任务粒度约定
- 每条任务应该是 1-2 小时内可完成 + 可独立验证的
- 任务包含 "create / modify / delete / verify" 等动词起头
- 验证类任务(`verify ...`)必须有可执行的命令或可观察的结果

### 4. 提交约定
- 一个 change 一个 PR(或一组相关提交),提交信息以 change 编号起头:
  - 例:`001 foundation: scaffold backend/ frontend/ docker/`
- 不要跨 change 改文件,如果发现依赖跑岔了,回头补依赖 change 而不是混改

---

## 依赖图

```
000 plan-corrections      ← 修订规划文档,执行 agent 先跑这个
 ↓
001 foundation
 ├─ 002  data-model       ┐
 └─ 002a source-tuning    ┘  (并行,都完成后开 003/004)
     ├─ 003 ingestion-sources ──┐
     ├─ 004 processing-pipeline ─┤
     │                           │
     │                           ▼
     │                       005 preference-scoring
     │                           │
     ▼                           ▼
006 rest-api ◄──────────────────┘
 ├─ 007 manual-ingest
 ├─ 008 frontend-scaffold
 │   ├─ 009 inbox-library
 │   ├─ 010 topics-entities-timeline
 │   └─ 011 digest
 └─ 012 scheduler-migration

013 decommission-old   ← 最后,所有上面 done 后执行
```

可以并行的(同一层级):
- 002 / 002a (一个改 schema 一个改 config,完全独立)
- 003 / 004 (但 005 依赖 004)
- 009 / 010 / 011 (都依赖 008)
- 012 与 006 并行

---

## 不变量(所有 change 都要遵守)

1. **不引入 Postgres 之外的存储** — 主存 / 全文 / 向量都在 Postgres
2. **不引入 Bot / Email 通道** — v1 只做 Web + CLI
3. **不引入 GitHub Actions 定时** — 调度在 APScheduler
4. **中文优先** — UI 默认中文,LLM 输出 `title_cn / summary_zh`
5. **AI Agent 领域聚焦** — focus / exclude 关键词配置沿用并扩展
6. **代码复用优先** — 现有 `src/agents/*`、`src/evaluator/claude_evaluator.py` 应迁移而非重写

---

## 当前状态

- 全部 changes:`Status: pending`
- 现仓库还是 `ai-news-agent` 旧形态,001-foundation 的第一步就是改名 / 改结构
