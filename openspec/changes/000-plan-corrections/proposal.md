# 000 · Plan Corrections(规划修订)

**Status: completed (2026-05-16)**
**特殊性:本 change 只动 `openspec/` 下的规划文档,不动任何代码。必须在 001 开始执行前完成。**

## 背景

整套 openspec 规划完成后做了一轮审计,发现 6 条 **blocking 级**问题 + 3 条**建议补充**项 + 3 条**整体性缺口**。如果不修,执行 agent 跑到中段会卡住或做错,届时回头打补丁成本更高。

审计对象:`openspec/specs/*.md` 和 `openspec/changes/001..013/*.md`(共 13 个原始 change + 002a)。

## 目标

把下列 12 处问题就地修进对应的 `proposal.md` / `tasks.md` / `specs/*.md`,让执行 agent 拿到的就是已修订过的规划。

## 不在本变更范围

- 不动 `backend/` `frontend/` `cli/` 下的任何代码(那是 001-013 的事)
- 不重排既有 change 顺序
- 不新增 change 包(只编辑现有的)

## 验收

- [x] tasks.md 里 12 个 fix 全部 `[x]`
- [x] `rg "tags" openspec/specs/storage.md` 能在 items 表定义里找到 `tags TEXT[]` 字段
- [x] `rg "project.scripts" openspec/changes/001-foundation/tasks.md` 命中
- [x] `rg "backend/legacy/notifier" openspec/changes/013-decommission-old/tasks.md` 命中(`src/notifier` 实际移除由 001-foundation 负责)
- [x] `openspec/changes/005-preference-scoring/tasks.md` 出现修改 `finalize.py` 的明确任务
- [x] 跑一遍 `find openspec/ -name '*.md' | xargs rg -l "TODO|XXX|FIXME"` 应该清零(本 change 不引入新 TODO;唯一命中为本验证命令本身的字面引用)
