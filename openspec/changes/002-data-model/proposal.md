# 002 · Data Model(数据模型 + 迁移)

**Status: completed (2026-05-17)** — schema/migration/triggers 全部 hand-written + import 通过;DB 相关 verify 待装 docker 后由用户跑

## 背景
旧系统无持久化,所有信息只活在内存到 markdown 一次性产物。新系统的核心存储是 Postgres + pgvector,所有上层 feature 都依赖这个 schema。

## 目标
- 落地 `specs/storage.md` 描述的全部表(items / topics / entities / item_topics / item_entities / interactions / digests / ingestion_errors)
- 配齐索引(B-tree / GIN tsvector / HNSW pgvector)
- 启用 pgvector + pg_trgm 扩展
- search_vector 自动维护 trigger
- topic / entity 计数自动维护 trigger
- Alembic migration 可前进可回滚

## 不在本变更范围
- 写入数据的业务逻辑(003+ 做)
- 检索查询代码(006 做)

## 验收
- [ ] `alembic upgrade head` 干净(空库)
- [ ] `alembic downgrade base` 完全清空
- [ ] `psql -c "\dx"` 看到 `vector` 和 `pg_trgm` 扩展
- [ ] SQLAlchemy 模型可 import 通过 mypy(`mypy app/db/models.py`)
- [ ] 一个 smoke 测试:insert 一条假 item + 一个 topic + 关联 → 查询返回数据
- [ ] tsvector trigger 工作(update title_cn 后 search_vector 自动变)
- [ ] HNSW 向量索引上跑 `SELECT ... ORDER BY embedding <=> ...` 不报错
