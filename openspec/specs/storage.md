# Spec: Storage(数据模型)

## 引擎
- Postgres 16
- 扩展:`pgvector`(向量),`pg_trgm`(模糊),内置 tsvector(全文)
- 迁移:Alembic

## 核心表

### items(信息主表)
```sql
CREATE TABLE items (
  id              BIGSERIAL PRIMARY KEY,
  url             TEXT,
  url_normalized  TEXT UNIQUE,                  -- 去重 key
  title           TEXT,
  title_cn        TEXT,
  content_md      TEXT,
  summary_zh      TEXT,
  summary_en      TEXT,
  recommendation  TEXT,
  source_type     TEXT NOT NULL,                 -- manual/rss/github/exa_search/twitter/chinese_platform
  source_name     TEXT,                           -- "Anthropic News" / "OpenAI Blog" / etc
  source_meta     JSONB,                          -- 原始字段保留
  author          TEXT,
  published_at    TIMESTAMPTZ,
  ingested_at     TIMESTAMPTZ DEFAULT now(),
  status          TEXT NOT NULL DEFAULT 'inbox', -- inbox/kept/archived/trashed
  processing_status TEXT NOT NULL DEFAULT 'pending', -- pending/extracted/enriched/embedded/ready/failed
  processing_attempts INT DEFAULT 0,
  last_error      TEXT,
  tags            TEXT[],                            -- enrich 产出,3-7 个英文小写连字符
  quality_score   NUMERIC(3,1),                   -- LLM 给的 1-10
  final_score     NUMERIC(3,1),                   -- 加偏好分后
  score_breakdown JSONB,
  embedding       vector(1024),
  search_vector   tsvector,                       -- 全文检索
  user_note       TEXT,                           -- 用户手写笔记
  user_highlight  TEXT[],                         -- 高亮片段
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_source ON items(source_type, source_name);
CREATE INDEX idx_items_published ON items(published_at DESC);
CREATE INDEX idx_items_score ON items(final_score DESC);
CREATE INDEX idx_items_search ON items USING GIN(search_vector);
CREATE INDEX idx_items_embedding ON items USING hnsw (embedding vector_cosine_ops);
```

### topics(主题)
```sql
CREATE TABLE topics (
  id              BIGSERIAL PRIMARY KEY,
  slug            TEXT UNIQUE NOT NULL,            -- "mcp" / "multi-agent" / "claude-code"
  name_zh         TEXT NOT NULL,
  name_en         TEXT,
  description     TEXT,
  watch_keywords  TEXT[],                          -- 触发自动归类的关键词
  is_pinned       BOOLEAN DEFAULT FALSE,
  item_count      INT DEFAULT 0,
  last_item_at    TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT now()
);
```

### entities(人/公司/项目/模型/论文)
```sql
CREATE TABLE entities (
  id              BIGSERIAL PRIMARY KEY,
  slug            TEXT UNIQUE NOT NULL,
  type            TEXT NOT NULL,                   -- person/company/project/model/paper
  name            TEXT NOT NULL,
  aliases         TEXT[],
  canonical_url   TEXT,
  description     TEXT,
  metadata        JSONB,                           -- twitter handle / github org / homepage 等
  item_count      INT DEFAULT 0,
  last_item_at    TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT now()
);
```

### 多对多
```sql
CREATE TABLE item_topics (
  item_id  BIGINT REFERENCES items(id) ON DELETE CASCADE,
  topic_id BIGINT REFERENCES topics(id) ON DELETE CASCADE,
  confidence NUMERIC(3,2),                          -- 0-1,LLM 给的归类置信度
  PRIMARY KEY (item_id, topic_id)
);

CREATE TABLE item_entities (
  item_id   BIGINT REFERENCES items(id) ON DELETE CASCADE,
  entity_id BIGINT REFERENCES entities(id) ON DELETE CASCADE,
  role      TEXT,                                   -- "author" / "mentioned" / "subject"
  PRIMARY KEY (item_id, entity_id, role)
);
```

### interactions(偏好燃料)
```sql
CREATE TABLE interactions (
  id            BIGSERIAL PRIMARY KEY,
  item_id       BIGINT REFERENCES items(id) ON DELETE CASCADE,
  action        TEXT NOT NULL,                      -- view/keep/archive/trash/highlight/note/share
  dwell_seconds INT,
  note_text     TEXT,
  highlight_text TEXT,
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_interactions_item ON interactions(item_id, created_at DESC);
CREATE INDEX idx_interactions_action ON interactions(action, created_at DESC);
```

### digests(周期精选)
```sql
CREATE TABLE digests (
  id            BIGSERIAL PRIMARY KEY,
  period        TEXT NOT NULL,                      -- daily/weekly/topic
  period_key    TEXT NOT NULL,                      -- "2026-05-15" / "2026-W20" / "topic:mcp:2026-05"
  title         TEXT,
  intro         TEXT,
  item_ids      BIGINT[],
  generated_at  TIMESTAMPTZ DEFAULT now(),
  UNIQUE (period, period_key)
);
```

### ingestion_errors
```sql
CREATE TABLE ingestion_errors (
  id           BIGSERIAL PRIMARY KEY,
  source_type  TEXT,
  source_name  TEXT,
  url          TEXT,
  error_type   TEXT,
  error_msg    TEXT,
  raw          JSONB,
  created_at   TIMESTAMPTZ DEFAULT now()
);
```

## 不变量
- `url_normalized` UNIQUE 是去重唯一硬约束
- `items.search_vector` 由 trigger 自动维护(title_cn + summary_zh + tags + content_md 前 N 字)
- `topics.item_count` / `entities.item_count` 由 trigger 维护
- 软删:`status='trashed'` 但行不删,可恢复;真删需 admin CLI

## 验收
- 完整 schema 通过 Alembic 单次 migration apply / rollback 干净
- 1 万条 items + 全部索引建好后,典型查询 < 50ms
- 向量检索 top-20 在 5 万条规模下 < 200ms
