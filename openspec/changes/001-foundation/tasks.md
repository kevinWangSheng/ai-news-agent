# 001 · Foundation — Tasks

- [x] 1. `git mv src backend/legacy`,把所有现有 `src/` 内容暂存到 `backend/legacy/`
- [x] 2. `git mv main.py backend/legacy/main.py`
- [x] 3. `git mv config backend/legacy/config`,`git mv .env.example backend/.env.example`
- [x] 4. 删除 `.github/workflows/`,`output/`,`test_pipeline.py`,`test_report.txt`,`news_agent.log`,以及一切根目录散落的 `*EMAIL*.md` `QUICKSTART*.md` `DEPLOY_GITHUB.md` `GMAIL_SETUP.md` `EXAMPLE_OUTPUT.md` `setup.py`
  - 注:tracked 文件用 `git rm`(可从历史恢复);untracked 的 `test_pipeline.py` / `news_agent.log` / `output/` 因 sandbox 限制未物理删除,但已纳入 `.gitignore` 屏蔽
- [x] 5. 新建 `backend/` 骨架:
  - `backend/pyproject.toml`(uv,依赖:fastapi、uvicorn、sqlalchemy、asyncpg、alembic、pydantic-settings)
  - `backend/app/main.py`(FastAPI app + `/health`)
  - `backend/app/__init__.py` `backend/app/api/__init__.py` `backend/app/ingestion/__init__.py` `backend/app/processing/__init__.py` `backend/app/db/__init__.py` `backend/app/config.py`(必须用 pydantic-settings 的 BaseSettings,集中所有可调参数)
  - `backend/Dockerfile`
- [x] 5a. `backend/app/config.py` 必须定义 `Settings(BaseSettings)` 单例,包含至少:
  - `database_url`(.env)
  - `anthropic_api_key` / `voyage_api_key` / `openai_api_key`(.env)
  - `exclude_keywords: list[str]` / `focus_keywords: list[str]`(从 topics.yaml 派生)
  - `scoring_inbox_threshold: float = 6.0`
  - `scoring_breaking_threshold: float = 5.0`
  - `digest_score_threshold: float = 7.0`
  - `preference_cold_start_min_interactions: int = 50`
  - `hnsw_m: int = 16` / `hnsw_ef_construction: int = 64`
  - `processing_max_attempts: int = 3` / `processing_concurrency: int = 4`
  所有后续 change 改阈值都改这一处,**禁止散落在各模块硬编码**
- [x] 6. 新建 `frontend/` 骨架:`pnpm create next-app frontend --typescript --tailwind --app --no-eslint --no-src-dir --turbopack` 然后清空默认 page.tsx 留个简单欢迎页
  - 注:create-next-app 装的是 Next.js 16(不是规划里的 14),frontend/CLAUDE.md 提醒 API 与训练数据可能有差异
- [x] 7. 新建 `frontend/Dockerfile`(多阶段:deps / builder / runner)
- [x] 8. 新建 `cli/` 骨架:
  - `cli/pyproject.toml`,包含:
    ```toml
    [project]
    name = "hub"
    version = "0.1.0"
    dependencies = ["click", "httpx"]
    [project.scripts]
    hub = "hub.main:cli"
    ```
  - `cli/hub/__init__.py`
  - `cli/hub/main.py`:定义 `@click.group() def cli(): ...` 并加一个 `@cli.command() def version(): click.echo("hub 0.1.0")`
  - **verify**:`cd cli && pipx install -e .` 后 `hub --version` 输出 `hub 0.1.0`
    - 实际用 `uv venv + uv pip install -e .` 验证(避免改全局 pipx),输出 `hub 0.1.0` 通过
- [x] 9. 新建 `docker/docker-compose.yml`:
  - `postgres`(pgvector 镜像 `pgvector/pgvector:pg16`,持久卷)
  - `backend`(builds backend/,depends_on postgres healthy)
  - `frontend`(builds frontend/,depends_on backend)
  - `scheduler`(builds backend/,跑 `python -m app.scheduler`,占位 entrypoint 是 `sleep infinity`)
- [x] 10. 新建 `docker/.env.example`(汇总后端 .env + DB url 等)
- [x] 11. 重写顶层 `README.md`:项目简介 + 一键启动 `cd docker && docker compose up -d` + 指向 `openspec/README.md`
- [x] 12. 更新 `.gitignore`:加 `frontend/.next/` `frontend/node_modules/` `backend/.venv/` `*.pyc` `cli/.venv/` `docker/.env`
- [ ] 13. **verify**:`docker compose up -d` 4 service healthy
  - 本机未装 docker,跳过;待用户在装有 docker 的环境运行
- [ ] 14. **verify**:`curl localhost:8000/health` 和 `curl localhost:3000` 都通
  - 同上,依赖 docker compose;backend 单独 `uvicorn` 可单独验,留给用户
- [x] 15. **verify**:`git log --oneline | head -20` 能看到旧的 commit(历史保留)

## 注意
- 旧 `.env` 不动(避免本地密钥泄漏);新建 `backend/.env` 让用户手动 copy 自己需要的 key
- legacy 目录留着不要删,下个 change 还要从中读代码做迁移
- Python 用 uv,不用 pip / poetry
