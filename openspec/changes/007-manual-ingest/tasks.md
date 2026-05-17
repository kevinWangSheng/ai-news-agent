# 007 · Manual Ingest — Tasks

## Bookmarklet
- [x] 1. `frontend/public/bookmarklet/install.html` — 拖拽安装页 + 原始 JS pre 块 + 注意事项
- [x] 2. bookmarklet 逻辑(单行 `javascript:`):抓 url/title/选中文 → POST `/api/ingest` → alert `已投喂 #id`
- [x] 16. Settings 页 Bookmarklet 安装节 — install.html 已包办;008 落地 `frontend/app/settings/page.tsx` 时只需把同样内容嵌入
- [x] 3. CORS 已在 006-rest-api `app.main.create_app` 配 `allow_origins=settings.cors_origins`(默认 `["*"]`)
- [x] 4. 安装说明 `docs/install-bookmarklet.md` — 中文步骤 + mixed-content 解决方案

## CLI
- [x] 5. `cli/pyproject.toml` 加 `click/httpx/rich/platformdirs`
- [x] 6. `cli/hub/config.py` — `~/.config/hub/config.toml`(platformdirs),`api_url` 默认 `http://localhost:8000`
- [x] 7. `cli/hub/main.py` — click 全部子命令:`add` / `list` / `search` / `show` / `keep|archive|trash` / `topics` / `trigger` / `config show|set`
- [x] 8. rich Table 输出 + `--json` 走纯 JSON
- [x] 9. `cli/hub/api.py` — httpx 封装,中文错误(连接失败 / 接口错误带 detail)
- [x] 10. 装法:`cd cli && pipx install -e .`(README 已含说明);本机 dev 用 uv venv 验证 OK
- [x] 11. `cli/tests/test_commands.py` 用 CliRunner + mock httpx — **5 passed**(version / add / list / keep / search)
- [ ] 12. **verify** bookmarklet → DB inbox+1 — 需 docker
- [ ] 13. **verify** `hub add` 真投喂 — 需 docker
- [ ] 14. **verify** `hub search` 真返回 — 需 docker
- [ ] 15. **verify** `hub keep 123` — 需 docker

## 注意
- bookmarklet 纯原生 JS,无 npm 依赖,可粘贴 / 拖拽
- mixed-content 解决方案文档化(Chrome flag / 自签证书)
- CLI 错误中文友好
