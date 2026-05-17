# 002a · Source Tuning — Tasks

## A. 数据级修复
- [x] 1. 修正 KOL handle:`kaboroevich` → `karpathy`,`9hills` 注释 → 九原客,`ylecun` 加 AMI Labs 注释,`alexalbert__` 注释加 Head of Claude Relations
- [x] 2. `Lilian Weng` priority high → low,加注释停更说明
- [x] 3. Adept / Inflection — 当前 config 不存在这两个条目,无需操作(no-op)

## B. topics.yaml 主题字典
- [x] 4. 新建 `backend/legacy/config/topics.yaml`(34 个 topic)
- [x] 5. 收录 ≥25 个 topic(实际 34)
- [x] 6. 写 `backend/legacy/scripts/_generate_focus_keywords.py`;config.yaml `focus_keywords` 块替换为脚本生成 91 条(原 12)+ AUTO-GENERATED 注释
- [x] 7. 在 `kol_topic_queries` / `site_queries` / `keyword_queries` / `ai_content_searches` 顶端加 `# DEPRECATED: 应从 topics.yaml 派生,003 平移时统一处理`

## C. 2025-2026 新玩家
- [x] 8. 加 Thinking Machines Lab(`official_blogs` critical)
- [x] 9. 加 Cognition / Cursor / Reka / Liquid AI / Sierra / Glean / Magic.dev / Browserbase / World Labs / AMI Labs / Manus / Genspark — 全部入 `official_blogs`,URL 沙盒无外网无法 WebFetch 校验,带 `# URL 待 003 平移时人工校验` 注释
- [x] 10. xAI `fallback_urls` 加 GitHub release atom;Qwen `fallback_urls` 加 release atom + HF feed
- [x] 11. KOL 追加 14 条(miramurati / lilianweng / barret_zoph / ilyasut / btaylor / scottwu46 / amanrsanger / varunmohan / pk_iv / gregpr07 / karinanguyen_ / ramin_m_h / drfeifei / yitayml)
- [x] 12. 新增 `twitter.official_accounts` 节(8 个公司官号)

## D. 过滤代码 bug 修复 — **改写为 backend/app/ 模块,不再 patch legacy**
> 理由:003 全面替换 orchestrator;patch legacy 等于浪费两次。把 "词边界 + 决策日志 + soft penalty" 实现成 backend/app/processing/keyword_match.py + 决策落表,004 enricher prefilter 直接复用。
- [x] 13. 新建 `backend/app/processing/keyword_match.py`:ASCII 走 `\b...\b` 正则,CJK 走子串,自动判断
- [ ] 14. soft penalty(hard exclude → -3)— 推迟到 004 enricher 实现,届时按 spec 落到 `score_breakdown.exclude_penalty`
- [ ] 15. 决策日志(`prefilter_decisions.jsonl`)— 推迟到 004 enricher,届时改为入库 `ingestion_errors` / 单独 `prefilter_decisions` 表
- [ ] 16. focus_boost 改"下限抬到 6 + 记录 _focus_hits"— 推迟到 005 scoring engine

## E. 测试 + 验收
- [x] 17. 写 `backend/tests/test_keyword_match.py` 覆盖 5 case(mcp / multi-agent / 词边界 miss / CJK / 多关键词)— **5 passed**
- [x] 18. 写 `backend/legacy/scripts/verify_kol_handles.py`(沙盒无外网无法跑;脚本就绪,留给用户)
- [ ] 19. **verify** orchestrator dry-run prefilter 50-100 历史样本 — 推迟到 003,届时新 enricher 用 keyword_match 决策日志
- [x] 20. **verify** focus_keywords ≥35(实际 91);topics.yaml ≥25 个 topic(实际 34)
- [x] 21. **verify** focus_keywords 不再手维护(头部加了 AUTO-GENERATED 注释)

## 注意
- D.14-16 / E.19 全部在 003-005 真实代码上落地,不在 legacy 留死代码
- 002a 实质完成:整治后的 yaml + topics.yaml + keyword_match.py + 测试基准
