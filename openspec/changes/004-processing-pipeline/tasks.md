# 004 · Processing Pipeline — Tasks

- [x] 1. `backend/app/processing/extract.py` — trafilatura + playwright fallback;manual+无 url 跳过
- [x] 2. `backend/pyproject.toml` 加 `trafilatura/playwright/anthropic/voyageai/openai/feedparser/pyyaml`
- [x] 2a. `backend/app/llm/client.py` — `get_claude()` / `get_voyage()` / `get_openai()` lru_cache 单例
- [x] 3. `backend/app/processing/enricher.py` — Claude system+cache_control prompt,JSON 解析,exclude prefilter 走 keyword_match,命中 → archive + ready,写 title_cn/summary_zh/tags/quality_score
- [x] 4. `backend/app/processing/topic_entity.py` — slugify / upsert_topic / upsert_entity / link_item_topic / link_item_entity(ON CONFLICT DO NOTHING)
- [x] 5. `backend/app/processing/embed.py` — Voyage `voyage-3` 首选,OpenAI text-embedding-3-small 截前 1024 维 fallback
- [x] 6. `backend/app/processing/finalize.py` — `final_score = quality_score`(005 Task 11 替换)
- [x] 7. `backend/app/processing/run.py` — `run_once(factory)` + `run_loop(factory, interval_s)` + CLI(`--once|--loop`);scheduler 同进程 await,不 spawn 子进程;每阶段独立 Semaphore;异常 catch + processing_attempts++ → failed
- [x] 8. `backend/tests/processing/test_extract.py` — HTML fixture via MockTransport,2 case
- [x] 9. `backend/tests/processing/test_enricher.py` — mock `_call_claude` 返回固定 JSON,2 case(含 exclude archive)
- [ ] 10. e2e test — 需 testcontainer + 真实 LLM,留给用户
- [x] 11. `/health/processing` 返回各 status 队列长度
- [ ] 12-14. **verify** — `run --once` / 坏 URL 重试 / 5 阶段走完 — 需 docker + API key,留给用户

## 注意
- prompt cache 通过共享 `get_claude()` 单例 + `cache_control: ephemeral` 落地
- playwright 仅在 trafilatura 失败时 fallback;ImportError 时优雅降级返回 None
