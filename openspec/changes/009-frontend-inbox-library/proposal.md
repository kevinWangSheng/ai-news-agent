# 009 · Frontend: Inbox + Library + Item 详情

**Status: completed (2026-05-17)** — inbox + library + item 详情齐 + ItemCard 复用 + recordInteraction

## 背景
最常用的三个页面:inbox(今日待处理)、library(全库浏览/搜索)、item 详情(看 + 反馈)。

## 目标
- `/inbox`:今日待处理卡片列表 + 顶部投喂表单 + 键盘流(keep / archive / trash)
- `/library`:搜索 + 过滤 + 分页
- `/item/[id]`:详情 + 笔记 + 高亮 + 相似条目

## 不在本变更范围
- topics / entities / digest 页面(010 / 011 做)

## 验收
- [ ] inbox 渲染当天 status='inbox' 条目,默认按 final_score desc
- [ ] inbox 顶部表单回车提交 → 立刻乐观渲染 + 后端处理后 5-30s 内更新
- [ ] 键盘 `j/k` 上下 / `k` keep / `a` archive / `t` trash 流畅
- [ ] library 搜索 + facet 过滤(source / topic / entity / date)正确
- [ ] item 详情页能看到 score_breakdown 展开("为什么推荐")
- [ ] 选中文本能高亮(写 interactions)
- [ ] 写笔记可持久化(写 items.user_note + interactions)
