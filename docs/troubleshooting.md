# Troubleshooting

## Playwright MCP: `Extension connection timeout`

如果 Codex 的 `mcp__playwright__` 工具报:

```text
Error: Extension connection timeout. Make sure the "Playwright MCP Bridge" extension is installed.
```

不要先怀疑项目代码或 Playwright runtime。这个项目在 2026-05-17 已确认:

- 底层 Playwright 可以直接打开 `https://www.anthropic.com/news`。
- Codex 的 `~/.codex/config.toml` 使用的是 extension 模式:
  `playwright-mcp --extension --browser chrome`。
- 该模式依赖 Chrome 里的 Playwright Extension / MCP Bridge 回连。
- 本机扩展 ID: `mmlmfjhmonkocbjadbfplnigmagldckm`。
- 本机扩展装在 Chrome `Profile 1`，profile 名为 `shenghui`；不是 `Default` / `Wang`。
- 切到 `shenghui` profile 后，`mcp__playwright__.browser_tabs` 能看到 extension connect 页，`browser_navigate` 能打开 Anthropic News。

快速处理:

```bash
pgrep -af 'playwright.*mcp|mcp.*playwright'
find "$HOME/Library/Application Support/Google/Chrome" \
  -path '*/Extensions/*/*/manifest.json' -maxdepth 6 -print \
  | xargs grep -il 'Playwright Extension'
```

然后在 Chrome 切到装有 Playwright Extension 的 profile，确认扩展已启用，再重试 MCP 工具。

如果只需要自动化浏览器、不需要控制当前 Chrome，也可以把 `~/.codex/config.toml` 的 Playwright MCP 参数从 extension 模式改成普通模式，去掉 `--extension`，让 MCP 自己启动浏览器。

---

## Docker / Colima

### 症状:`docker compose` 找不到子命令

```
docker: unknown command: docker compose
```

`docker-compose` 是独立 binary,`docker compose`(v2 subcommand)需要 plugin 路径配置:

```bash
mkdir -p ~/.docker
echo '{"cliPluginsExtraDirs":["/opt/homebrew/lib/docker/cli-plugins"]}' > ~/.docker/config.json
docker compose version
```

### 症状:`docker compose build` 退出 137

Colima VM 内存不够,build 过程被 OOM killed。

```bash
colima stop
colima start --cpu 4 --memory 8 --disk 30   # 默认 6G,build 阶段 4G 起步可能不够
```

### 症状:`pgvector/pgvector:pg16` 一直 EOF 拉不下来

这两个 blob 在我们 Cloudflare 边缘有问题(同样的 IP 拉 `alpine`/`postgres` 都没事)。已在 `docker/postgres/Dockerfile` 本地 build 绕开,无需手工干预。

---

## Next.js 前端

### 症状:`/inbox` `/library` 等全部路由返回 404,只 `/` 是 200

主机 `:3000` 被其他进程(常见:其他项目的 `next dev`)占了,docker 端口转发被截胡。

```bash
lsof -nP -iTCP:3000 -sTCP:LISTEN
# 看到不是 docker 的进程 → kill 掉或换端口
pkill -f "<占用进程名>"
docker compose restart frontend
```

### 症状:`pnpm install` 报 `node:sqlite` builtin not found

`corepack prepare pnpm@latest` 拉到 pnpm 11+,要求 Node 22.13+。本项目 base 已切 Node 22-alpine + pin `pnpm@10.30.1`,fork 改 Dockerfile 时注意保持。

---

## Backend / Processing

### 症状:`processing_status='failed'` 一堆,日志 `voyage embed failed`

`VOYAGE_API_KEY` 没填且 `OPENAI_API_KEY` 也没填,fallback 全失败。

**修法**:在 `docker/.env` 里填 `ARK_API_KEY`(火山方舟,无需翻墙)。代码已加 ARK 为 primary,见 [CHANGELOG v2.1.0](../CHANGELOG.md)。

### 症状:OpenAI Blog / LlamaIndex Blog 文章正文一直 extract failed

文章页 JS-rendered + 反爬,curl 直接 403,trafilatura 抓不到,playwright fallback 因为容器没装 chromium 也 graceful skip。

**已知问题**,openspec/changes/014 阶段 C 计划装 chromium 解决,目前明确推迟。这 ~25 条 failed 不影响其他源运行。

---

## 数据库维护

### 复活全部 failed items 重跑

```sql
UPDATE items SET processing_status='pending', processing_attempts=0, last_error=NULL
WHERE processing_status='failed';
```

```bash
docker compose exec backend python -m app.processing.run --once
# 重复多次直到 stage=embed processed=0
```

### 清空 DB 重来(警告不可逆)

```bash
docker compose down -v   # 删 volume
docker compose up -d
docker compose run --rm migrate
```

---

## CLI(`hub`)

### `hub: command not found`

```bash
cd cli && pipx install -e .
hub --version
```

### `hub` 连不上 API

```bash
hub config set api_url http://localhost:8000
```

确认 backend 容器在跑 + 8000 端口可访问。
