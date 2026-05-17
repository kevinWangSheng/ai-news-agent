# 002a · Source Tuning(信源关键词整治)

**Status: completed (2026-05-17)** — D.14-16 / E.19 推迟到 003/004/005 真实代码上落地,避免 patch legacy 二次浪费

## 背景

`config/config.yaml` 是 v1 攒了一年多的产物,有 3 类积累问题,如果不在 003 平移之前整治,等于把垃圾搬到新库:

1. **数据级错误**(影响抓取目标)
   - `twitter.kol_accounts` 里 `kaboroevich` 注释写 Karpathy,实际真账号是 `karpathy`,这条至今抓的是别人
   - `9hills` 注释写"九山",实际是"九原客"
   - `ylecun` 2025-11 离开 Meta 去 AMI Labs,profile 明示"不写帖子只转链",信号价值大降
   - `lilianweng.github.io` 2025-05 起基本停更(她去了 Thinking Machines),保留要降权

2. **覆盖缺口**(2025-2026 整代新玩家没进清单)
   - **公司缺**:Thinking Machines / SSI / Cognition(Devin)/ Anysphere(Cursor)/ Magic.dev / Reka / Liquid AI / Glean / Sierra / AMI Labs / Browserbase / Browser Use / Manus / Genspark / World Labs
   - **死/吸走需移**:Adept(Amazon acqui-hire 已死)/ Inflection(转 enterprise,降权)
   - **focus_keywords 缺**:`claude code` `cursor` `windsurf` `devin` `computer use` `browser agent` `deep research` `MCP server` `Tinker` `interaction model` `world model / 世界模型` `embodied / 具身智能` `agentic browser` `agentic commerce` `Comet` `agentic OS` `A2A` `sub-agent / 子智能体` `AlphaEvolve` `outcome-based pricing`

3. **过滤实现 3 个 bug**(`src/orchestrator.py:251-279`)
   - **无英文词边界**:`"mcp" in blob` 会误命中 `mcps3 / compress`;`"tool use" in blob` 误命中 `school used`。应用正则 `\bmcp\b`
   - **硬过滤无证据**:`logger.info(f"Hard filter dropped {dropped} items")` 只记数不记 URL,事后想调阈值不知道误杀了什么
   - **focus_boost 力度太小**:满分 10 的 LLM 评分上 +2 噪音都能淹没。改成"命中 focus → 基础分下限抬到 6"

4. **配置散在 6 处**(改一处不够) — `evaluation.filters` / `community_sources.search_keywords` / `twitter.*_queries` / `ai_content_searches.*.queries` / `github.topics+rising_stars.queries+new_projects.queries` / `chinese_platforms.keywords` / `breaking_news.site_queries+keyword_queries`。每次想加一个新主题(比如 "computer use")要扫 6 处。应抽出 `topics.yaml` 主题字典,各 source 的 queries 从字典派生。

## 目标

- 修正所有数据级错误(KOL handle / 注释 / 死链)
- 把 2025-2026 新玩家补全(公司源 + KOL + focus_keywords)
- 把 6 处分散 keyword 抽到统一的 `topics.yaml`
- 过滤代码 3 个 bug 修掉
- 改 hard exclude → soft penalty + 命中证据落表/落日志

## 不在本变更范围

- 不动 schema(那是 002 的事)
- 不写新 source(那是 003 的事)
- 不改 LLM 评分逻辑本体(那是 004/005 的事)
- 不做 KOL 的实时活跃度自动监控(可作 v2)

## 依赖

- 上游:001 完成(`config.yaml` 已 mv 到 `backend/legacy/config/`)
- 与 002 (data-model) 可并行执行
- 下游:003 (ingestion-sources) 必须等 002a 完成,Task 10 拷贝的就是整治后的 yaml

## 验收

- [ ] `backend/legacy/config/config.yaml` 里所有 KOL handle 都经过校验(单元测试或脚本输出 PASS)
- [ ] `backend/legacy/config/topics.yaml` 存在,所有原本散在 6 处的 keyword 都已迁移过去
- [ ] focus_keywords 不少于 35 项(原 12 + 新增 ≥23)
- [ ] 跑 1 次旧 orchestrator(legacy 路径),被 prefilter dropped 的条目能在 `output/prefilter_dropped.jsonl` 找到 URL + 匹配关键词
- [ ] `orchestrator.py` 的过滤函数有单元测试覆盖 "词边界"(`mcp` 不命中 `mcps`)
- [ ] focus_boost 改造后,命中条目 final_score 下限可观察(测试数据演示)
- [ ] 不删 Adept / Inflection,但 priority 降到 low 或加 `deprecated: true` 注释,便于 003 平移时一并决定是否保留
