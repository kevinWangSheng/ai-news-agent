# 000 · Plan Corrections — Tasks

> 每条任务:**[文件路径] 找到 [锚点字符串] → 改成 [新内容]**
> 执行 agent 必须用 Edit 工具精准替换,不要重写整段。

---

## A. Blocking 必改(6 条)

### A1. 002 spec ↔ task 不一致:items 表缺 tags 列

- [x] 1. **编辑** `openspec/specs/storage.md`
  在 items 表 CREATE TABLE 内,在 `quality_score NUMERIC(3,1)` 上一行插入:
  ```
  tags            TEXT[],                            -- enrich 产出,3-7 个英文小写连字符
  ```

- [x] 2. **编辑** `openspec/changes/002-data-model/tasks.md` Task 4
  在 `Item(含 url_normalized UNIQUE...)` 这条 bullet 末尾追加 `、tags TEXT[]`,例:
  ```
  - `Item`(含 url_normalized UNIQUE、embedding vector(1024)、search_vector tsvector、status/processing_status enum 字符串、tags TEXT[])
  ```

- [x] 3. **编辑** `openspec/changes/002-data-model/tasks.md` Task 9
  删除 trigger SQL 末尾的注释 `(注:`tags` 列也要加进 items 模型,`TEXT[]`)` — 已在 Task 4 明列,不需重复

---

### A2. 001 Task 8 缺 CLI 入口点(007 会装失败)

- [x] 4. **编辑** `openspec/changes/001-foundation/tasks.md` Task 8
  把原内容:
  ```
  - [ ] 8. 新建 `cli/` 骨架:`cli/pyproject.toml`,`cli/hub/__init__.py`,`cli/hub/main.py`(click,`hub --version` 可跑通)
  ```
  改为:
  ```
  - [ ] 8. 新建 `cli/` 骨架:
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
  ```

---

### A3. 012 ↔ 004 调用模式未定(子进程 vs 同进程)

- [x] 5. **编辑** `openspec/changes/004-processing-pipeline/tasks.md` Task 7
  把原内容:
  ```
  - [ ] 7. 新建 `backend/app/processing/run.py`(orchestrator):
    - `--once`:每阶段处理当前队列后退出
    - `--loop`:持续拉队列(供 scheduler 用)
  ```
  改为:
  ```
  - [ ] 7. 新建 `backend/app/processing/run.py`(orchestrator):
    - 暴露 `async def run_once(session_factory) -> ProcessingStats`:每阶段处理当前队列后返回,不退出进程(供 scheduler 同进程 await)
    - 暴露 `async def run_loop(session_factory, interval_s=60)`:while True 循环 run_once + sleep,用于本地手动调试
    - 提供 CLI 入口 `python -m app.processing.run --once` / `--loop`:在 `if __name__ == "__main__":` 里包一层,内部仍调上面两个 async 函数
    - **scheduler 路径不走 CLI,不 spawn 子进程**;直接 `from app.processing.run import run_once`
  ```

- [x] 6. **编辑** `openspec/changes/012-scheduler-migration/tasks.md` Task 3
  把 `processing_loop` 这一条:
  ```
  - `processing_loop`:`@interval(minutes=1)` 跑 `processing.run --once`
  ```
  改为:
  ```
  - `processing_loop`:`@interval(minutes=1)` 调用 `from app.processing.run import run_once; await run_once(session_factory)`(同进程,共享 DB engine,不 spawn 子进程)
  ```

---

### A4. 012 Task 7 /health/scheduler 数据来源未定

- [x] 7. **编辑** `openspec/changes/012-scheduler-migration/tasks.md` Task 1
  把:
  ```
  - [ ] 1. 在 backend 依赖加 `apscheduler[asyncio]`
  ```
  改为:
  ```
  - [ ] 1. 在 backend 依赖加 `apscheduler[asyncio,sqlalchemy]`(后者用于 SQLAlchemyJobStore,持久化 job 元数据 + last_run/next_run)
  ```

- [x] 8. **编辑** `openspec/changes/012-scheduler-migration/tasks.md` Task 2
  在 AsyncIOScheduler 实例那条 bullet 之后追加:
  ```
    - 配置 jobstores={'default': SQLAlchemyJobStore(url=settings.database_url)}:APScheduler 自动建/管 `apscheduler_jobs` 表
    - 配置 job_defaults={'misfire_grace_time': 300, 'coalesce': True}
  ```

- [x] 9. **编辑** `openspec/changes/012-scheduler-migration/tasks.md` Task 4
  把:
  ```
  - [ ] 4. 每个 job 包一层:记录开始 / 完成 / 异常 → 写 `scheduler_runs` 表(可选,或只打日志)
  ```
  改为:
  ```
  - [ ] 4. 每个 job 用 decorator 包一层 `@track_run`:
    - 入口:`logger.info("job=X start")`
    - 出口:`logger.info("job=X done duration=N items=M")`
    - 异常:`logger.exception("job=X failed")` + 必须 catch 住不重抛(scheduler 不能死)
    - 不单独建 scheduler_runs 表;last_run / next_run 数据全部从 APScheduler 的 SQLAlchemyJobStore 读
  ```

- [x] 10. **编辑** `openspec/changes/012-scheduler-migration/tasks.md` Task 7
  把:
  ```
  - [ ] 7. `/health/scheduler` 端点:返回各 job 的 last_run / last_success / next_run
  ```
  改为:
  ```
  - [ ] 7. `/health/scheduler` 端点:从 `scheduler.get_jobs()` 读每个 job 的 `next_run_time`;`last_run` / `last_success` 从 APScheduler `JobExecutionEvent` 听 + 写内存 dict(scheduler 进程重启会丢,这是已知 trade-off,不另建表)
  ```

---

### A5. 013 Task 5 路径错(必失败)

- [x] 11. **编辑** `openspec/changes/013-decommission-old/tasks.md` Task 5
  把:
  ```
  - [ ] 5. `git rm -r src/notifier/` (如果 001 没顺手 rm 的话)
  ```
  改为:
  ```
  - [ ] 5. `git rm -r backend/legacy/notifier/`(001 把 src/ 整体 mv 到 backend/legacy/,所以路径在 legacy 下)
  ```

---

### A6. 005 ↔ 004 finalize.py 改写顺序

- [x] 12. **编辑** `openspec/changes/005-preference-scoring/tasks.md`
  在 005 现有 tasks 列表**最后一条之前**插入一条新 task(取下一个未用编号):
  ```
  - [ ] N. **修改** `backend/app/processing/finalize.py`:把 004 Task 6 留的占位 `final_score = quality_score` 替换为:
    ```python
    from app.scoring.preference import compute_preference_delta
    delta = await compute_preference_delta(session, item)
    item.final_score = max(0, min(10, item.quality_score + delta))
    item.score_breakdown = {"base": item.quality_score, "preference_delta": delta, "details": ...}
    ```
    不要新建文件覆盖,就地改 finalize.py 的同一函数
  ```
  (注:N 取 005/tasks.md 当前最大编号 + 1,Edit 前先 Read 该文件确认)

---

## B. 建议补充(3 条)

### B1. 002 testcontainer fixture 二选一

- [x] 13. **编辑** `openspec/changes/002-data-model/tasks.md` Task 14
  把:
  ```
  - [ ] 14. 写 `backend/tests/test_schema.py`:fixture 起 testcontainer(或 docker compose 已起的 postgres),跑 upgrade → smoke insert → downgrade
  ```
  改为:
  ```
  - [ ] 14. 写 `backend/tests/test_schema.py` + `backend/tests/conftest.py`:
    - 用 `testcontainers[postgres]` 起一次性 postgres(避免依赖外部 docker compose 状态)
    - conftest fixture:`@pytest.fixture(scope="session") async def pg_engine(): ...` 起容器 → `alembic upgrade head` → yield engine → 容器自动销毁
    - test_schema.py:smoke insert items / topics / interactions → 验证 trigger 维护 search_vector 和 item_count
    - 在 backend/pyproject.toml dev deps 加 `testcontainers[postgres]`
  ```

### B2. 004 缺统一 LLM 客户端

- [x] 14. **编辑** `openspec/changes/004-processing-pipeline/tasks.md` Task 2
  把:
  ```
  - [ ] 2. 在 `backend/pyproject.toml` 加依赖:`trafilatura`、`playwright`、`anthropic`、`voyageai`
  ```
  改为:
  ```
  - [ ] 2. 在 `backend/pyproject.toml` 加依赖:`trafilatura`、`playwright`、`anthropic`、`voyageai`
  - [ ] 2a. 新建 `backend/app/llm/__init__.py` + `backend/app/llm/client.py`:
    - `def get_claude() -> anthropic.AsyncAnthropic`:进程内单例,system prompt cache 复用要靠所有调用方共享同一 client
    - `def get_voyage() -> voyageai.AsyncClient`:同上
    - 004 enricher / 005 scoring / 011 digest 三处所有 LLM 调用必须经此入口,不允许各自 new Anthropic()
  ```

### B3. 008 Cmd+K 与 / 键冲突

- [x] 15. **编辑** `openspec/changes/008-frontend-scaffold/tasks.md` Task 6
  在 CommandPalette 那条 task 末尾追加(或独立一段):
  ```
    - 键位分工(避免与 TopBar 全局搜索框冲突):
      - `/`:聚焦 TopBar 搜索框(用于快速跳 /library?q=)
      - `Cmd/Ctrl+K`:唤起 CommandPalette(用于导航命令、切 source、投喂)
      - 搜索框内 `Esc` 失焦;CommandPalette 内 `Esc` 关闭
  ```

---

## C. 整体性缺口(3 条)

### C1. 没有统一配置 Settings class

- [x] 16. **编辑** `openspec/changes/001-foundation/tasks.md` Task 5
  在 `backend/app/config.py` 那个 bullet 末尾追加注释 `(必须用 pydantic-settings 的 BaseSettings,集中所有可调参数)`,然后在 Task 5 列表之后追加新 Task 5a:
  ```
  - [ ] 5a. `backend/app/config.py` 必须定义 `Settings(BaseSettings)` 单例,包含至少:
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
  ```

### C2. bookmarklet 安装路径未交代

- [x] 17. **编辑** `openspec/changes/007-manual-ingest/tasks.md`
  在 bookmarklet 任务(应是 Task 2)之后插入一条新 task:
  ```
  - [ ] Nx. 在 `frontend/app/settings/page.tsx` 增一节"Bookmarklet 安装":
    - 渲染一个可拖拽的 `<a href="javascript:...">📥 投喂到 hub</a>`,提示文案"拖到书签栏即可"
    - 同时显示原始 javascript 代码(用 `<pre>`),便于手动复制
    - 提示 CORS 配置:bookmarklet 调 `/api/ingest`,后端必须允许 `Access-Control-Allow-Origin: *`(或精确白名单当前页 origin),在 006-rest-api 的 CORS 中间件加宽
  ```
  (Nx 取 007/tasks.md 当前最大编号 + 1)

### C3. playwright 镜像膨胀

- [x] 18. **编辑** `openspec/changes/004-processing-pipeline/tasks.md` 文件末尾「注意」节
  把:
  ```
  - playwright 二进制:dockerfile 里要 `playwright install chromium`(注意镜像大小)
  ```
  改为:
  ```
  - playwright 二进制策略:
    - backend Dockerfile 用 multi-stage:`builder` 阶段 `playwright install chromium`,最终阶段 `COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright`
    - 仅 extract 路径用 playwright,且只在 trafilatura 失败时 fallback;90% 条目不会触发
    - 若镜像 > 2GB 仍嫌大,可把 playwright fallback 抽到独立 `extractor` service(本期不做,记录到 v2)
  ```

---

## D. 收尾

- [x] 19. **编辑** `openspec/README.md` 依赖图,在 `001 foundation` 之前加 `000 plan-corrections`(纯文档,不阻塞 001 的物理执行但建议先做):
  ```
  000 plan-corrections      ← 修订规划文档,执行 agent 先跑这个
   ↓
  001 foundation
   ├─ 002  data-model       ┐
   └─ 002a source-tuning    ┘
  ...
  ```

- [x] 20. **verify**:在 `openspec/changes/000-plan-corrections/proposal.md` 顶部加 `Status: completed (YYYY-MM-DD)`

- [x] 21. **verify**:跑一遍 `git diff openspec/` 看 12 处编辑落实;不应该有任何 `backend/` `frontend/` `cli/` 路径下的改动(注:openspec/ 目录此前未提交;`git status` 显示编辑全部局限在 openspec/,无 backend/frontend/cli 路径改动)

## 注意

- 本 change 由"另一个执行 agent"接手:全程只用 Edit 工具改 openspec/ 下的 markdown,**不要 Write 整文件**(覆盖原版会丢失我后续可能的小改)
- 每条任务的 [文件路径] 都是绝对 openspec/ 相对路径,Edit 前先 Read 一次确认锚点字符串还在
- 12 处修改互不依赖,可任意顺序;但请按 A → B → C 顺序做,先消 blocking
