# 003 · Ingestion Sources — Tasks

- [x] 1. `backend/app/ingestion/base.py`:`RawItem` + `Source` Protocol
- [x] 2. `backend/app/ingestion/normalize.py`:`normalize_url`(去 https/www/尾斜杠/小写 + 去 utm/fbclid/gclid 等追踪参数)
- [x] 3. `backend/app/ingestion/service.py`:`IngestionService.create_item` 幂等去重 + `record_error`
- [x] 4. `backend/app/ingestion/sources/rss.py` — feedparser + httpx async,42 个 RSS source 从 config 构造成功
- [x] 5. `backend/app/ingestion/sources/github.py` — GitHub Search API,topic + stars 阈值过滤
- [x] 6. `backend/app/ingestion/sources/exa_search.py` — 合并 breaking_news + ai_content,site_queries + keyword_queries 驱动
- [x] 7. `backend/app/ingestion/sources/twitter.py` — Exa 搜 x.com / twitter.com 域,kol+official+topic 三路
- [x] 8. `backend/app/ingestion/sources/chinese.py` — Exa 限 zhihu/sspai/36kr/mp.weixin/qbitai/jiqizhixin
- [x] 9. `backend/app/ingestion/run.py` — CLI `python -m app.ingestion.run <kind|all>`,asyncio 入口,失败不阻断
- [x] 10. `backend/config.yaml` / `backend/topics.yaml` 拷贝就绪
  - 注:`query_builder.py` + 删 DEPRECATED 块推迟到真有数据流通后再做(避免无 verify 凭空重构)
- [x] 11. `backend/app/config.py` 已在 001-5a 落地(pydantic-settings + 全部阈值)
- [x] 12. 各 source 单元测试:`test_normalize.py`(4 case)+ `test_rss.py`(MockTransport 解析 1 entry)— **5 passed**
- [ ] 13. 集成测试 `test_service.py` testcontainer create_item + 去重 — 需 docker,留给用户
- [ ] 14. **verify** `python -m app.ingestion.run rss` 拉到条目,DB items 增长 — 需 docker + postgres
- [ ] 15. **verify** 同命令再跑 dedupe — 同上
- [ ] 16. **verify** `run all` 6 source 失败隔离 — 需 docker + 各 API key

## 注意
- legacy 的 prompt cache 在 enricher(004)再迁移
- legacy/agents/*.py 等 004/005 验通后 013 一并 `git rm`
