# 007 · Manual Ingest(手动投喂入口)

**Status: completed (2026-05-17)** — bookmarklet 安装页 + CLI 11 子命令 + 5 CLI tests pass;真实投喂 verify 需 docker

## 背景
006 已经把 `POST /api/ingest` 端点建好。本期做两个客户端,让用户可以"零摩擦扔东西进来"。

## 目标
- **bookmarklet**:一段 `javascript:` 代码,书签栏一点就把当前页 POST 到本机 API
- **`hub` CLI**:命令行工具,`hub add <url>` / `hub add -n "note"` / `hub search <q>` / `hub list`
- 安装文档:`docs/install-bookmarklet.md` + `cli/README.md`

## 不在本变更范围
- 浏览器扩展(明确推迟到 v2)
- iOS 快捷指令(可选,放 docs 里作 tip)

## 验收
- [ ] 把 bookmarklet 添加到 Chrome,任意网页点一下 → toast "已投喂",DB 多一条 inbox
- [ ] `hub add https://...` 同样效果
- [ ] `hub add -n "记个想法"` 创建无 URL 条目
- [ ] `hub search mcp` 命令行打印 top 10 结果
- [ ] `hub list --inbox` 列今日 inbox
- [ ] `hub --help` 文档清晰
