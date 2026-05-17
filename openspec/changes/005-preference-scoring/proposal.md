# 005 · Preference Scoring(偏好打分)

**Status: completed (2026-05-17)** — engine/preferences/recompute + finalize 集成 + 6 unit tests pass(含 spec verify 9 场景)

## 背景
004 已经把 quality_score(LLM 主观)放进 final_score。本期把"用户历史交互"喂回打分,实现"系统越来越懂我"。

## 目标
- `interactions` 表填充逻辑(API 在 006 做,这期定义数据流和重算)
- 偏好引擎:基于 tags / entities / sources 的历史 keep / archive / trash 比例算加权
- 冷启动门槛:interactions 总数 < 50 时偏好分一律为 0
- 透明:每条 item 的 `score_breakdown` JSONB 字段写明各加权项

## 不在本变更范围
- API 端点(006 做)
- UI"为什么推荐"展开(009/010 做)

## 验收
- [ ] `python -m app.scoring.recompute --all` 重算所有 ready 条目的 final_score
- [ ] 手动插一组 interactions(15 个 keep with tag=mcp,15 个 trash with tag=image-gen),冷启动门槛后,新条目带 mcp tag 的 final_score 显著高于带 image-gen 的
- [ ] score_breakdown 字段可读,显示 `quality_base / tag_boost / entity_boost / source_boost / time_decay`
- [ ] cold start(< 50 interactions)时所有偏好分为 0,final_score == quality_score
