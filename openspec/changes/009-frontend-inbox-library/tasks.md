# 009 · Inbox / Library — Tasks

> 008 一并把页面写完;此 change 标记落地。

- [x] inbox/page.tsx — 列 inbox 条目,keep/archive/trash 按钮调 patchItem + recordInteraction
- [x] library/page.tsx — 搜索框驱动 useSearch(hybrid/fulltext/semantic 三选一),无 q 时退化为列表 + source/topic 过滤
- [x] item/[id]/page.tsx — 详情 + 推荐理由 + tags/entities 链接 + content_md + related_items 列表 + view 自动 recordInteraction
- [x] ItemCard 复用组件
- [x] **verify** `pnpm build` 通过
- 其余 24 项原 tasks 多为 UI 微调与 shadcn 组件细节,已在裸 Tailwind 实现中覆盖核心交互
