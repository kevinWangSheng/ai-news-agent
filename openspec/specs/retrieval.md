# Spec: Retrieval(检索)

## 目的
让用户能从知识库里"找到那条"或"找到一类"。

## 检索模式

### 1. 全文检索(BM25 via tsvector)
- 输入:中文/英文关键词
- 字段:`title_cn` + `summary_zh` + `content_md` + `tags`(权重递减)
- 实现:tsvector + `websearch_to_tsquery`
- 适用:精确词、专有名词

### 2. 语义检索(向量 cosine)
- 输入:任意自然语言短句
- 查询:把输入用相同 embedding 模型编码 → pgvector ANN(HNSW)
- 适用:"上次那篇讲 agent 怎么处理上下文压缩的"

### 3. 混合检索(默认)
- 同时跑 BM25 和向量,各取 top-50
- 用 Reciprocal Rank Fusion(RRF, k=60)合并
- 再按 `final_score * 0.3 + rrf * 0.7` 重排
- 输出 top-20

### 4. 过滤维度
所有检索都支持:
- `status`(inbox/kept/archived/all)
- `source_type` / `source_name`
- `topic` / `entity`
- `date_range`
- `min_score`
- `has_note` / `has_highlight`(已交互过的)

### 5. 时间线检索
- 按 `topic` 或 `entity` 查:返回该范围内所有 items,按 `published_at` desc
- 聚合视图:按月分桶 + 每月 top-3 重要事件

## API 形态

```
GET /api/search?q=...&mode=hybrid&status=ready&source_type=rss&topic=mcp&from=2026-04-01

返回:{
  total: int,
  items: [Item],
  facets: {
    sources: [{name, count}],
    topics: [{slug, count}],
    entities: [{slug, count}]
  }
}
```

## 验收
- 中文查询"多智能体编排"能找到包含 "multi-agent orchestration" 的英文条目(语义路径)
- 关键词"langchain v0.3" 能精确返回相关条目(BM25 路径)
- 时间线视图:`/timeline?topic=mcp&from=2026-01` 返回按月分组 + 每月 top items
- p95 延迟 < 300ms(5 万条规模)
