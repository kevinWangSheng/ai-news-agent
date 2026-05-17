# 从 v1(ai-news-agent)迁移到 v2(ai-agent-hub)

## 核心变化

| 维度 | v1 | v2 |
|---|---|---|
| 形态 | GitHub Actions 每天跑一次 → 邮件 | 本机常驻服务 + Web + CLI |
| 存储 | 无(每次都 markdown 一次性产物) | Postgres 16 + pgvector(持久) |
| 通知 | 邮件 / 可选 Telegram | Web inbox + 命令面板 + CLI |
| 反馈 | 无(单向) | keep / archive / trash / note / highlight → 偏好打分 |
| 检索 | 无 | 全文 + 向量 + hybrid(RRF k=60) |
| 调度 | GitHub Actions cron | 本机 APScheduler |
| 投喂 | 无 | bookmarklet + `hub` CLI + REST /api/ingest |

## 数据迁移

- **数据不可迁**。v1 没有持久化,DB 从 0 开始
- `backend/legacy/config/config.yaml` 完整保留,新 source 代码也读它
- 旧的 `output/daily_report.md` 是只读历史快照,不导入

## 部署变化

```bash
# v1
git clone ... && pip install -r requirements.txt
# GitHub Actions 自动跑

# v2
cd docker
cp .env.example .env   # 填 ANTHROPIC / VOYAGE / EXA / GITHUB key
docker compose up -d   # 起 postgres + backend + frontend + scheduler
docker compose exec backend alembic upgrade head
```

访问:
- Web: <http://localhost:3000>
- API docs: <http://localhost:8000/docs>
- CLI: `cd cli && pipx install -e . && hub --help`

## 环境变量改变

删除(v1 → v2):
- `EMAIL_SENDER` / `EMAIL_PASSWORD` / `EMAIL_RECEIVER` / `RESEND_API_KEY`
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`

新增:
- `DATABASE_URL`(`postgresql+asyncpg://hub:hub@postgres:5432/hub`)
- `VOYAGE_API_KEY`(主 embedding;不填用 OpenAI fallback)
- `OPENAI_API_KEY`(可选 embedding fallback)

保留:
- `ANTHROPIC_API_KEY`(主 enricher)
- `EXA_API_KEY` / `GITHUB_TOKEN`

## 兼容性说明

- `backend/legacy/` 暂保留,迁移完成且 verify 通过后由 013 `git rm`
- 旧 GH Actions workflow 已删除(`.github/workflows/daily_news.yml`)
- 旧根目录的 `setup.py` / `main.py` / `*EMAIL*.md` / `QUICKSTART*.md` 已删
