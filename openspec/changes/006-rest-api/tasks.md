# 006 · REST API — Tasks

- [x] 1. `backend/app/api/schemas.py` — Item/Topic/Entity/Digest/Source/Page/Search/Interaction/Ingest models
- [x] 2. `backend/app/api/routes/ingest.py` — `POST /api/ingest`(bookmarklet+CLI 共用)
- [x] 3. `backend/app/api/routes/items.py` — GET 列表(分页+多过滤)/ GET 详情(含 topics/entities/向量近邻 top5)/ PATCH / DELETE 软删 / POST interactions(写表+联动 status)
- [x] 4. `backend/app/api/routes/search.py` — hybrid(RRF k=60 + final_score 加权)/ fulltext(websearch_to_tsquery + ts_rank)/ semantic(pgvector cosine_distance)
- [x] 5. `backend/app/api/routes/topics.py` — list / create / patch / items / `timeline?bucket=month|week`(date_trunc 聚合)
- [x] 6. `backend/app/api/routes/entities.py` — list(type 过滤)/ get / items
- [x] 7. `backend/app/api/routes/digests.py` — list / get / generate(011 填 LLM)
- [x] 8. `backend/app/api/routes/sources.py` — list(error_count + last_success_at)+ trigger(BackgroundTasks 异步)
- [x] 9. `backend/app/api/routes/health.py` — health / db / processing / scoring 4 端点统一
- [x] 10. `app/main.py` 注册全部 router + CORS allow_origins(从 Settings)
- [x] 11. `backend/tests/api/test_smoke.py` — TestClient 起 app + openapi 列表完整性 + cursor roundtrip + RRF — **4 passed**
- [x] 12. OpenAPI 标签:8 个(ingest/items/search/topics/entities/digests/sources/health)
- [x] 13. **verify** /openapi.json 列出 28 个端点(24 /api + 4 /health)
- [x] 14. **verify** `pytest tests/api/` 通过(4/4)
- [ ] 15. **verify** `curl -X POST /api/ingest` 创建条目 — 需 docker(postgres)

## 注意
- 全 async session;cursor 用 base64(`(created_at, id)`)而非 offset
- 错误统一 `HTTPException(status, detail)`;FastAPI 默认 envelope `{"detail": ...}`
