# 006 · REST API

**Status: completed (2026-05-17)** — 28 端点全部就绪 + 4 smoke tests pass;真实 CRUD verify 需 docker

## 背景
前端(008+)和 CLI(007)都需要 HTTP 入口。这期把所有读写端点一次性建好。

## 目标
完整 FastAPI 路由覆盖:
- 投喂:`POST /api/ingest`
- 条目:`GET/PATCH/DELETE /api/items`、`POST /api/items/{id}/interactions`
- 检索:`GET /api/search`(hybrid / fulltext / semantic 三模式)
- 主题:`GET/POST/PATCH /api/topics`、`GET /api/topics/{slug}/items`、`GET /api/topics/{slug}/timeline`
- 实体:`GET /api/entities`、`GET /api/entities/{slug}/items`、`GET /api/entities/{slug}/timeline`
- 精选:`GET /api/digests`、`POST /api/digests/generate`
- 源管理:`GET /api/sources`、`POST /api/sources/{name}/trigger`
- 健康:`GET /health`、`/health/processing`、`/health/scoring`

## 不在本变更范围
- 任何 UI / 前端代码(008 做)
- CLI 客户端(007 做)
- 实际调度(012 做)

## 验收
- [ ] 全部端点 OpenAPI 在 `/docs` 可见
- [ ] `POST /api/ingest` 接受 `{url}` 创建 inbox 条目
- [ ] `GET /api/search?q=mcp&mode=hybrid` 返回融合排序结果
- [ ] `POST /api/items/{id}/interactions {action:"keep"}` 修改 items.status 且写 interactions
- [ ] `GET /api/topics/mcp/timeline` 返回按月分桶 items
- [ ] httpx 集成测试覆盖所有端点(200 + 主要 400/404 路径)
