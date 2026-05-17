# 013 · Decommission Old — Tasks

## 删 legacy
- [x] 1. `rg "from app|import app" backend/legacy/` 无命中 — legacy 未引用新代码
- [x] 2. 反向 `rg "legacy" backend/app/ frontend/ cli/`:`backend/app/ingestion/run.py:load_config/load_topics` 的 fallback 已移除(2026-05-17 handoff),剩余命中仅为 source 文件 docstring 标注
- [ ] 3. `git rm -r backend/legacy/` — **不在本会话执行**(规模大、不可逆,需用户明确签字。前置条件已满足:`backend/config.yaml` + `backend/topics.yaml` 是唯一配置源,代码不再 fallback)
- [ ] 4. `backend/config.yaml` / `backend/topics.yaml` 保留作唯一源,不删

## 删邮件相关
- [ ] 5. `git rm -r backend/legacy/notifier/` — 同 3,推迟
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
- [ ] 15. **verify** 干净环境按 README 跑通 — 需用户实测
- [ ] 16. **verify** `ls backend/legacy` 报 No such file — 推迟到用户执行 git rm 后
- [x] 17. 全部 14 个 proposal 顶部已加 `Status: completed (2026-05-17)`
- [ ] 18. 顶层 commit — 留给用户

## 注意
- ~~`backend/app/ingestion/run.py:load_config` 仍 fallback 读 `backend/legacy/config/config.yaml`~~ — 已修(2026-05-17,canonical 与 legacy yaml 100% 同步后移除 fallback,见 [docs/handoff.md](../../../docs/handoff.md) §9)
- README 截图(inbox/library/topic 时间线)需用户跑 docker 后截
