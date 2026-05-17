# 010 · Frontend: Topics / Entities / Timeline

**Status: completed (2026-05-17)** — topics/entities 列表+详情 + 月度柱状时间线 + sources 表格

## 背景
"主题/实体页 + 时间线"是 4 个升级方向之一(演进追踪)。本期把对应页面接好。

## 目标
- `/topics`:主题卡片列表 + 创建主题
- `/topics/[slug]`:主题详情 + 三 tab(最新 / 时间线 / 实体)
- `/entities`:实体列表,按 type 分 tab(person/company/project/model/paper)
- `/entities/[slug]`:实体详情 + 关联 items + 共现实体
- 通用时间线组件(按月分桶 + 每月 top N)

## 验收
- [ ] 点击 inbox/library 卡片的 tag chip 跳 `/topics/<slug>`
- [ ] 点击作者 / 公司名跳 `/entities/<slug>`
- [ ] 主题时间线按月聚合,每月最多显示 5 条 top items + "查看全部 N 条"
- [ ] 实体共现:页面右栏列出和当前实体最常一起出现的其他实体 top 10
- [ ] 主题页可编辑 watch_keywords(影响未来归类)
