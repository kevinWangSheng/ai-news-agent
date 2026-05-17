# 003 · Ingestion Sources(信源迁移)

**Status: completed (2026-05-17)** — 6 source + service + run.py + 5 unit tests pass;DB 集成 verify 需 docker

## 背景
旧系统 6 个 agent(`backend/legacy/agents/*.py`)输出是 dict,塞给 orchestrator 评分后写 markdown。新系统这些 agent 改成 `Source` 协议,输出写库 `items.status=inbox`,然后让 processing 流水线接手。

## 目标
- 定义统一 `Source` 抽象 + 6 个 source 实现
- 复用 legacy 的网络抓取 / API 调用代码(不重写)
- 改造输出:每条 raw item 通过 `IngestionService.create_item()` 写库
- URL 规范化去重在写库前完成
- 失败写 `ingestion_errors` 不阻塞其他

## 不在本变更范围
- 抓全文 / LLM 加工(004 做)
- 调度 / 定时(012 做,本期手动 trigger 验收)
- 手动投喂(007 做)

## 验收
- [ ] `python -m app.ingestion.run rss` 拉一次,DB 多出来若干 inbox 条目
- [ ] 同 URL 再跑一次,记录数不增加
- [ ] 6 个 source 任一失败,其他不受影响
- [ ] `SELECT count(*) FROM ingestion_errors` 可观察失败情况
- [ ] 各 source 单元测试:mock 一个 fixture(假 RSS / 假 Exa 响应),解析正确
