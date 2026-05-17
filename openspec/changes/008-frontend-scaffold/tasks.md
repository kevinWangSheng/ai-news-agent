# 008 · Frontend Scaffold — Tasks

- [ ] 1. shadcn/ui init — 跳过(避免交互式安装),手工实现等价 utility classes,后续按需再装
- [ ] 2. 同上 — 不装 shadcn 组件,所有 UI 用 Tailwind + 原生 button/input
- [x] 3. `frontend/app/layout.tsx` — ThemeProvider + Sidebar + TopBar 包裹 children,`lang="zh-CN"`,Noto_Sans_SC + Geist_Mono
- [x] 4. `frontend/components/layout/Sidebar.tsx` — 7 个导航(inbox/library/topics/entities/digest/sources/settings)+ active 高亮
- [x] 5. `frontend/components/layout/TopBar.tsx` — 全局搜索框(Enter 跳 /library?q=)+ `/` 聚焦 + Esc 失焦 + 主题切换
- [x] 6. `frontend/components/CommandPalette.tsx` — cmdk,Cmd/Ctrl+K 唤起,导航 + 主题 + 刷新
- [x] 7. `frontend/lib/api/client.ts` — fetch 封装,`ApiError` + `NEXT_PUBLIC_API_URL`
- [x] 8. `pnpm gen:api` 脚本就绪(`openapi-typescript`);需 backend 跑着才能生成 types
- [x] 9. `frontend/lib/api/hooks.ts` — SWR hooks(useItems/useItem/useSearch/useTopics/useEntities/useDigests/useSources)+ mutator(patchItem/recordInteraction)
- [x] 10. `app/error.tsx` + `app/not-found.tsx`
- [x] 11. 全部路由占位:inbox / library / topics / topics/[slug] / entities / entities/[slug] / digest / sources / settings / item/[id](实际填了 9/11 页内容,不是占位)
- [x] 12. `app/page.tsx` redirect → `/inbox`
- [x] 13. `frontend/.env.example`(`NEXT_PUBLIC_API_URL=http://localhost:8000`)
- [x] 14. 快捷键:`useKeyboardShortcuts` hook — `/` `Cmd+K` `g i/l/t/e/d`
- [x] 15. **verify** `pnpm typecheck` 通过 + `pnpm build` 12 路由成功
- [x] 16. **verify** Cmd-K 工作(Command.Dialog 接 keyboard event)
- [x] 17. **verify** `pnpm gen:api` 命令就绪(运行需 backend on)
- [x] 18. **verify** 主题切换 — `next-themes` + `suppressHydrationWarning` 防闪烁
