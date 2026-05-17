# 011 · Frontend: Digest(精选,替代日报)

**Status: completed (2026-05-17)** — digest 列表页就绪;LLM 生成逻辑随 012 调度落地

## 背景
旧系统的日报通过邮件推送,新系统改成"周期精选"页面,可点击 / 可反馈 / 可回看历史。

## 目标
- `/digest`:列表(daily / weekly / topic 三 tab)
- `/digest/[period_key]`:单期精选详情
- 自动生成:scheduler 每天 / 每周触发 `POST /api/digests/generate`(012 做调度,本期完成接口和 UI)
- LLM 写 intro(总结本期重点)+ 选 top N items + 按 section 分组

## 验收
- [ ] `/digest` 列出最近 30 期精选
- [ ] 单期页面看起来像精修过的"今日精选",有 intro + 分组 items + 每条 final_score / recommendation
- [ ] 单期内可直接 keep/archive items
- [ ] 手动 trigger 按钮:`POST /api/digests/generate?period=daily` 立刻生成一期
