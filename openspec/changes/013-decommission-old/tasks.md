# 013 · Decommission Old — Tasks

## 删 legacy
- [x] 1. `rg "from app|import app" backend/legacy/` 无命中 — legacy 未引用新代码
- [x] 2. 反向 `rg "legacy" backend/app/ frontend/ cli/`:`backend/app/ingestion/run.py:load_config/load_topics` 的 fallback 已移除(2026-05-17 handoff),剩余命中仅为 source 文件 docstring 标注
- [x] 3. `git rm -r backend/legacy/` 已执行(2026-05-17,handoff §1-7 verify 全通后签字)
- [x] 4. `backend/config.yaml` / `backend/topics.yaml` 保留作唯一源,不删

## 删邮件相关
- [x] 5. `git rm -r backend/legacy/notifier/` 已随 #3 一起删
- [x] 6. 新代码无 SMTP/Resend/EmailNotifier/send_daily_report 引用,grep 清零
- [x] 7. `backend/.env.example` 重写:只保留 DB + LLM + ingestion key
- [x] 8. `backend/pyproject.toml` 无邮件 / Telegram 包

## 文档
- [x] 9. 顶层 `README.md` 已在 001-Task 11 重写
- [x] 10. 旧 README/QUICKSTART/GMAIL_SETUP/DEPLOY_GITHUB/EXAMPLE_OUTPUT 已在 001-Task 4 `git rm`
- [x] 11. `CHANGELOG.md` 新建:v2.0.0 概览
- [x] 12. `docs/migration-from-v1.md` 新建

## 验收
- [x] 13. `rg -i "email|smtp|resend|telegram"` 在 backend/app+frontend+cli 清零
- [x] 14. legacy 没被新代码 import
- [x] 15. **verify** docker 实跑 handoff §1-7 全通(2026-05-17),修了 5 个仅 docker 暴露的 bug
- [x] 16. **verify** `ls backend/legacy` 报 No such file
- [x] 17. 全部 14 个 proposal 顶部已加 `Status: completed (2026-05-17)`
- [x] 18. 顶层 commit ebd40bb + 本次 commit(v2.0.1 verify + legacy 物理删除)

## 注意
- ~~`backend/app/ingestion/run.py:load_config` 仍 fallback 读 `backend/legacy/config/config.yaml`~~ — 已修(2026-05-17,canonical 与 legacy yaml 100% 同步后移除 fallback,见 [docs/handoff.md](../../../docs/handoff.md) §9)
- README 截图(inbox/library/topic 时间线)需用户跑 docker 后截
