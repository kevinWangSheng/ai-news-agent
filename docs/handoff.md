# 接手清单 — 装好 Docker 后照着跑

> 2026-05-17 §1-7 已由 Claude Code 真机跑通(colima + docker compose),过程中修了 5 个仅 docker 暴露的 bug,见 [CHANGELOG.md v2.0.1](../CHANGELOG.md)。
> `backend/legacy/` 已物理删除。本文档保留作为重建环境的 runbook。

> Playwright MCP 提示 `Extension connection timeout` 时，先看 [docs/troubleshooting.md](troubleshooting.md)：本机常见原因是 Chrome profile 没切到安装 Playwright Extension 的 `shenghui`。

openspec 14 个 change 都已经标 completed,本清单按顺序走完即可完整复现一次端到端 verify。

---

## 0. 前置(只做一次)

```bash
# CLI-only(推荐,无需 Docker Desktop GUI):
brew install colima docker docker-compose
mkdir -p ~/.docker
echo '{"cliPluginsExtraDirs":["/opt/homebrew/lib/docker/cli-plugins"]}' > ~/.docker/config.json
colima start --cpu 4 --memory 6 --disk 30

# 或装 Docker Desktop / OrbStack(GUI):
brew install --cask docker
open -a Docker && sleep 10            # 等 daemon

cd docker/
cp .env.example .env
# 编辑 .env,至少填:
#   ANTHROPIC_API_KEY=sk-ant-...     # 必填,enrich + digest 用
#   VOYAGE_API_KEY=pa-...            # 必填,embed 用(无则 embed 全 fail)
#   EXA_API_KEY=...                  # 可选,启用 Exa search 源
#   TWITTER_BEARER_TOKEN=...         # 可选,启用 Twitter 源
```

> 启动前确认主机 `:3000` 没被其他 `next dev` 占着(`lsof -nP -iTCP:3000 -sTCP:LISTEN`),否则 docker frontend 转发会被截胡导致全部路由 404。

---

## 1. 起服务(收 001 #13-14)

```bash
cd docker/
docker compose up -d --build
docker compose ps
# 期望:postgres healthy, migrate exited (0), backend healthy, frontend running, scheduler running

curl http://localhost:8000/health           # → {"status":"ok"}
curl -I http://localhost:3000                # → 200 OK
```

`migrate` 是一次性服务,跑完 `alembic upgrade head` 后退出 (0),backend / scheduler 才会启动 —— 这是设计如此。

---

## 2. DB schema 体检(收 002 #16-18)

```bash
# alembic 已由 migrate 服务执行,这里只验
docker compose exec postgres psql -U hub -d hub -c '\d items'
docker compose exec postgres psql -U hub -d hub -c "\di"   # 索引存在
docker compose exec backend python -m pytest tests/test_schema.py -v
```

---

## 3. Ingestion 真拉(收 003 #13-16)

```bash
docker compose exec backend python -m app.ingestion.run rss
docker compose exec backend python -m app.ingestion.run web   # 014: HTTP + Playwright web 源,含 Meta/xAI/Mistral/Qwen/Cohere 等浏览器源
docker compose exec backend python -m app.ingestion.run rss   # 第二次应 dedupe
docker compose exec backend python -m app.ingestion.run all   # 6 source kind 失败隔离

docker compose exec postgres psql -U hub -d hub -c "select count(*) from items;"
docker compose exec postgres psql -U hub -d hub -c "select source_type, count(*) from items group by 1 order by 2 desc;"
docker compose exec postgres psql -U hub -d hub -c "select source_name, count(*) from items where source_type='web' group by 1 order by 2 desc;"
docker compose exec postgres psql -U hub -d hub -c "select count(*) web_total, count(*) filter (where processing_status='ready') ready, count(*) filter (where processing_status='failed') failed from items where source_type='web';"
```

---

## 4. Processing 5 阶段(收 004 #10, #12-14)

```bash
docker compose exec backend python -m app.processing.run --once
# 看日志应看到 stage=extract/enrich/embed/finalize 各自 processed/succeeded/failed

docker compose exec postgres psql -U hub -d hub \
  -c "select processing_status, count(*) from items group by 1;"
# 期望:大部分到 ready
```

---

## 5. Scoring(收 005 #7, #10)

```bash
docker compose exec backend python -m app.scoring.recompute --all
docker compose exec postgres psql -U hub -d hub \
  -c "select count(*) from items where score_breakdown is not null;"
```

---

## 6. API smoke(收 006 #15)

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","title":"smoke"}'

curl http://localhost:8000/api/items?limit=3 | jq .
curl http://localhost:8000/api/search?q=agent&limit=3 | jq .
```

---

## 7. 手动投喂(收 007 #12-15)

```bash
# bookmarklet 安装页
open http://localhost:3000/settings

# CLI 投喂 — cli 是另一个项目
cd ../cli && pipx install -e . && cd -
hub add https://www.anthropic.com/news
hub search agent
hub keep 1
hub list
```

---

## 8. Scheduler 24h 观察(收 012 #8-11)

```bash
docker compose logs -f scheduler   # 看 9 个 job 注册 + cron 触发
docker compose restart scheduler   # 重启后应自动恢复(SQLAlchemyJobStore 持久化)
# 24h 后:
docker compose exec postgres psql -U hub -d hub \
  -c "select date_trunc('hour', created_at) h, count(*) from items group by 1 order by 1;"
```

---

## 9. 删 legacy(已完成于 2026-05-17,留作 runbook 参考)

前提:1-8 步全通,且业务跑了至少 24h 没问题。

```bash
git rm -r backend/legacy/
# backend/config.yaml / backend/topics.yaml 是当前唯一源,不删
git status
git commit -m "013 decommission-old: physically remove backend/legacy/"
git push
```

删除前已确认:
- `backend/app/ingestion/run.py:load_config` 不再 fallback 读 legacy yaml
- `backend/app` 全量 grep `legacy` 只剩 docstring 标注,无 import / runtime 引用

---

## 10. 体检脚本(随时可跑)

```bash
# 后端
cd backend && uv run pytest -q                  # 不依赖 docker 的部分(24 个测试)
cd backend && uv run pytest -q tests/test_schema.py   # 依赖 postgres

# 前端
cd frontend && pnpm build                       # 12 路由编译

# docker 状态
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs --tail=50 backend
```
