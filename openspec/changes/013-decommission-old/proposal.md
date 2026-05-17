# 013 · Decommission Old(收尾,删旧代码 / 文档)

**Status: completed (2026-05-17)** — 邮件依赖清零 + CHANGELOG + migration doc + .env 重写;legacy 物理删除留给用户签字

## 背景
001-012 全部完成后,`backend/legacy/`、邮件 notifier、邮件相关文档、`output/` 这些应该已经不再有依赖。本期一次性清掉。

## 目标
- 删除 `backend/legacy/`(确认没有 import)
- 删除所有邮件相关代码 / 文档
- 重写顶层 README + 项目截图 / 演示动图
- 写迁移笔记(如果用户想从旧 ai-news-agent 旧库迁移)

## 验收
- [ ] `rg backend/legacy` 全仓库无引用
- [ ] `rg EmailNotifier|ResendNotifier|telegram_bot` 全仓库无引用(除非有意保留作 v2 参考)
- [ ] 顶层 README 是新项目说明,带架构图 / 截图
- [ ] 一次完整冷启动测试:`git clone → cd docker → cp .env.example .env(填 key)→ docker compose up -d → 浏览器打开 localhost:3000` 全流程跑通
- [ ] CHANGELOG.md 记录从 ai-news-agent 到 ai-agent-hub 的版本跃迁
