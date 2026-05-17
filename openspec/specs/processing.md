# Spec: Processing(处理流水线)

## 目的
把 `items.status=inbox` 的原始条目加工成可消费的"知识单元":全文 + 中文标题 + 摘要 + 标签 + 实体 + 向量 + 评分。

## 流水线阶段

```
inbox → extracted → enriched → embedded → scored → ready
                                                    ↓
                                                ready_for_user
```

每阶段独立 worker,失败可重试,状态写 `items.processing_status`。

### 1. extract(全文抓取)
- 输入:`url`
- 工具:trafilatura 主路径,失败 fallback 到 playwright
- 输出:`content_md`(markdown)、`content_html`、`meta`(author/published_at/lang)
- 跳过:source_type=manual 且 url 为空(纯笔记) → 跳到 enrich

### 2. enrich(LLM 加工)
- 工具:Claude Haiku 4.5,prompt cache 复用现有 `claude_evaluator.py` 的 system prompt
- 输出字段:
  - `title_cn`(中文标题,最多 40 字符)
  - `summary_zh`(中文摘要,150-300 字)
  - `summary_en`(英文摘要,可选,直接用原文压缩)
  - `tags`(3-7 个,英文小写连字符:`mcp` `multi-agent` `claude-code` etc)
  - `entities`(实体列表:`{type, name, role?}`,type 取 `person / company / project / model / paper`)
  - `quality_score`(1-10 LLM 主观)
  - `recommendation`(一句话推荐语,中文)
- 复用:`config.yaml` 的 `evaluation.filters.exclude_keywords / focus_keywords` 做 prefilter

### 3. embed(向量化)
- 工具:Voyage-3(input_type=document),fallback OpenAI text-embedding-3-small
- 输入:`title + summary_zh + tags` 拼接(避免全文过长)
- 输出:`embedding vector(1024)` 写 pgvector

### 4. score(评分)
- 基础分:`quality_score`(LLM 给的)
- 偏好分增量:
  - 同 `tags` 历史 keep 多 → 加分
  - 同 `entities` 历史 keep 多 → 加分
  - 同 source 历史 trash 率高 → 减分
  - 时间衰减:发布时间越近基础加分越多
- 输出:`final_score`(0-10)、`score_breakdown`(JSONB 解释字段)

### 5. ready
- 写 `items.status = ready`
- inbox 视图显示 final_score >= 阈值的(默认 6,可配置)

## 错误处理
- 每阶段错误写 `items.last_error` + `processing_attempts++`
- 超过 3 次重试 → `status = failed`,需人工查看
- 一阶段失败不阻塞下一条目

## 验收
- 一条 manual 投喂(纯 URL)能 60s 内走完 5 阶段到 `ready`
- 1000 条历史条目能在 30 分钟内批量处理完(并发参数可调)
- prefilter 命中 exclude_keywords 的条目跳过 enrich,直接 archive
- 处理统计可观察(API `/api/health/processing` 返回各阶段队列长度)
