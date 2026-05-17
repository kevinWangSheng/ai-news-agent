# 004 · Processing Pipeline(处理流水线)

**Status: completed (2026-05-17)** — 5 阶段就绪 + 4 unit tests pass + /health/processing;e2e 需 docker+API key

## 背景
003 让 items 进库 status=inbox。本变更负责把它们加工成 ready:抓全文 → LLM 总结/标签/实体 → embedding → 写回。

## 目标
- 5 个阶段独立 worker:extract / enrich / embed / score(下个 change 做)/ ready
- 每阶段读 `processing_status` 队列,做完推进
- 复用 `backend/legacy/evaluator/claude_evaluator.py` 的 prompt cache 模板
- 失败 3 次进 `failed`,人工恢复
- 可配并发度,默认 5

## 不在本变更范围
- 偏好评分加权(005 做)
- HTTP API 触发(006 做)
- 调度(012 做,本期靠 `python -m app.processing.run`)

## 验收
- [ ] `python -m app.processing.run --once` 把所有 inbox 条目推到 ready
- [ ] 失败条目进 failed,`last_error` 有内容
- [ ] 一条手动塞的纯 URL inbox 条目 60s 内变 ready
- [ ] enrich 输出包含中文标题 / 摘要 / 3-7 个 tag / 0+ entity
- [ ] embedding 写库可查
- [ ] prefilter 命中 exclude_keywords 的直接 status=archived 不进 enrich
