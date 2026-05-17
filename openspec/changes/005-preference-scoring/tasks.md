# 005 · Preference Scoring — Tasks

- [x] 1. `backend/app/scoring/preferences.py` — `compute_{tag,entity,source}_signals` + `total_interactions`,单 SQL group by(无 N+1)
- [x] 2. `backend/app/scoring/engine.py` — `score_item(item, signals, total) -> ScoreBreakdown`(base + tag/entity/source boost + time_decay + focus floor 6 + cold-start gate)
- [x] 3. `backend/app/scoring/preference.py` — `compute_preference_delta(session, item)`(每次重抓 signals;recompute 共享)
- [x] 4. `backend/app/scoring/recompute.py` — `--all` / `--since 7d|24h`,分页 batch,signals 在调用前抓一次共享
- [x] 5. 冷启动门槛:`total_interactions < settings.preference_cold_start_min_interactions`(默认 50)→ tag/entity/source boost 全归零
- [x] 6. `backend/tests/scoring/test_engine.py` — **6 passed**:cold_start / tag boost / tag penalty / time decay / focus floor / mcp-vs-image-gen 差 ≥2(spec verify 9)
- [ ] 7. `test_recompute.py` e2e — 需 testcontainer,留给用户
- [x] 8. `/health/scoring` 返回 `total_interactions / cold_start_passed / cold_start_min`
- [x] 9. **verify (单测代替)** spec 场景 mcp keep vs image-gen trash gap ≥2 — pass
- [x] 11. **修改** `backend/app/processing/finalize.py` 使用 `compute_preference_delta` 写 final_score + score_breakdown
- [ ] 10. **verify** `recompute --all` 后所有 ready item 有 breakdown — 需 docker + 真数据

## 注意
- signals 单次 SQL group by;recompute 跨条目共享 signals 快照
- preference 系数控制在 ±1 量级,基础 quality_score 主导
