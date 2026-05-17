# Spec: Ingestion(投喂)

## 目的
把任意来源的"一条信息"统一吸入系统,落到 `items` 表的 `inbox` 状态。

## 信息单元定义
一条 `item` 至少有:`url`(或 `content_hash`)、`title`、`source_type`、`raw_payload`(原始字段保留)、`ingested_at`。

## 来源(source_type 枚举)
1. **manual**:用户手动投喂(bookmarklet / CLI / Web 表单)
2. **rss**:订阅源(原 tech_agent 的官方/专家/聚合/研究/社区博客)
3. **github**:trending / topics / rising_stars / new_projects
4. **exa_search**:Exa/Tavily 站点限定 + 关键词搜索(原 breaking_news + ai_content)
5. **twitter**:Exa Twitter/X 搜索(KOL + 话题 + 新发布)
6. **chinese_platform**:掘金 / 知乎 / CSDN 搜索

每个 source 实现统一接口:
```python
class Source(Protocol):
    name: str
    source_type: str
    async def fetch(self) -> list[RawItem]: ...
```

调度入口 `scheduler.py` 按 cron 触发各 source 的 `fetch()` → 写入 `items`(status=inbox)。

## 去重(必须)
- 入库前对 `url` 做规范化(去 `https://` `www.` 尾部 `/`、小写)
- 命中现有 `url_normalized` 直接 skip,不更新已存在条目
- 文本内容相似度去重放到 processing 层(用 embedding 算)

## 投喂入口
- **bookmarklet**:`javascript:` 协议,POST `/api/ingest` 带 `url + title + selected_text`
- **CLI**:`hub add <url>` / `hub add -t "title" -n "note text"`
- **Web 表单**:`/inbox` 页面顶部
- **manual API**:`POST /api/ingest` with `{url?, title?, content?, note?, tags?[]}`

## 验收
- 6 个 source 都能独立 dry-run(`source.fetch()` 不写库)
- 同一 URL 被两个 source 同时抓到 → 仅入库一次
- 手动投喂可只给 URL(标题/内容由 processing 抓取)
- 手动投喂可只给笔记文本(无 URL,作为想法存储)
- 失败的 fetch 写入 `ingestion_errors`,不影响其他 source
