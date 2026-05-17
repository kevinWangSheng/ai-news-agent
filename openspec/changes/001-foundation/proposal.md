# 001 · Foundation(地基)

**Status: completed (2026-05-17)** — docker compose verify (验收第 1-3 项) 待装 docker 后由用户跑

## 背景
旧仓库是单一 Python 项目根目录 + `src/` + `main.py` + GitHub Actions 调度。新系统是前后端分离 + Docker Compose 多服务,目录布局完全不同。

## 目标
把仓库改造成新布局的空壳:
- 顶层分 `backend/ frontend/ docker/ cli/`
- backend 是 FastAPI 应用骨架(uvicorn 起得来,健康检查 200)
- frontend 是 Next.js 14 空项目(`pnpm dev` 起得来)
- docker-compose 起 4 个 service(postgres / backend / frontend / scheduler 占位)
- 旧代码挪到 `backend/legacy/` 暂存(下一个 change 才真正迁移)

## 不在本变更范围
- 数据库 schema(002 做)
- 迁移现有 agent 业务逻辑(003 做)
- 任何 UI 页面(008+ 做)

## 验收
- [ ] `cd docker && docker compose up -d` 4 个 service 都 healthy
- [ ] `curl http://localhost:8000/health` 返回 `{"status":"ok"}`
- [ ] `curl http://localhost:3000` 返回 Next.js 默认欢迎页
- [ ] `git log` 保留(没有 git init 新仓库)
- [ ] 顶层 README.md 替换为新项目说明(指向 openspec/)
