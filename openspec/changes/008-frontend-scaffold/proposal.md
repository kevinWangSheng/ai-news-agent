# 008 · Frontend Scaffold(前端骨架)

**Status: completed (2026-05-17)** — Next.js 16 + SWR + cmdk + 自实现 UI(跳过 shadcn 交互式 init);12 路由 `pnpm build` 通过

## 背景
001 已经 `pnpm create next-app` 出了空 Next.js 项目。本期把布局 / 主题 / 全局组件 / API client / 全局状态打底,后续 009-011 才能贴页面。

## 目标
- 全局 layout:顶栏 + 侧栏 + main 容器
- Tailwind 主题:暗色为主,可切亮色,系统色跟随
- shadcn/ui 集成,装一组基础组件
- API client(typed):基于后端 OpenAPI 自动生成
- 命令面板(Cmd/Ctrl+K)框架
- 全局错误边界 + toast

## 不在本变更范围
- 任何具体页面(inbox / library 等)留给 009-011

## 验收
- [ ] `pnpm dev` 起来,顶栏 + 侧栏 + 空 main 渲染
- [ ] 切深/浅色无闪烁
- [ ] Cmd/Ctrl+K 弹出命令面板(暂时只有"切主题"和"刷新"两条)
- [ ] API client 调 `GET /health` 返回类型化数据
- [ ] 全局 toast(成功/失败/警告)可用
