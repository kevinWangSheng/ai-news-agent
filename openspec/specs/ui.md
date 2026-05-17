# Spec: UI(Web 前端)

## 目的
给用户提供"看 / 找 / 反馈 / 管理"四类操作的统一 Web 界面。

## 技术约束
- Next.js 14 App Router + TypeScript
- Tailwind CSS + shadcn/ui 组件库
- 数据获取:Server Component + Route Handler 调 FastAPI
- 状态:URL 是 source of truth;localStorage 存只读偏好(主题、列表密度)
- 主题:暗色为主,可切亮色;系统色跟随
- 默认中文

## 信息架构

```
/                     重定向到 /inbox
/inbox                今日待处理(processing_status=ready 且 status=inbox)
/library              全库浏览 + 检索
/topics               主题列表 + 创建 / pin
/topics/[slug]        单主题页 + 时间线
/entities             实体列表(person/company/project/model/paper 分 tab)
/entities/[slug]      单实体页 + 关联 items + 时间线
/digest               精选(daily/weekly/topic)
/digest/[period_key]  单期精选(替代旧日报的角色)
/item/[id]            条目详情 + 笔记 + 高亮
/sources              source 健康检查 + 手动 trigger
/settings             配置项编辑(focus/exclude keywords / topic 监控关键词)
```

## 核心页面契约

### /inbox
- 顶部:投喂表单(URL + 可选标题/笔记 + tag),回车提交
- 主区:卡片列表,默认按 final_score desc
- 卡片显示:title_cn / source / time / final_score / 1 行 recommendation / 3 个 tag
- 卡片交互:← keep / → trash / ↓ archive(键盘)或对应按钮
- 顶部 stats:今日新增 N,今日处理 M
- 空状态:引导贴 bookmarklet / 安装 CLI

### /library
- 顶部搜索框(`/`键聚焦);右上角 mode 切换(hybrid / fulltext / semantic)
- 左侧 facet:source / topic / entity / date / status
- 主区:列表,可切详细 / 紧凑 / 卡片 三视图
- 每条:title / 源 / 时间 / score / tags / 一段 summary_zh

### /topics/[slug]
- 头部:topic 名 / 描述 / item_count / last_item_at / 监控关键词
- 主区切 tab:
  - **最新**:按 published_at desc
  - **时间线**:按月分桶,每月 top 3
  - **实体**:该主题下高频 entity
- 操作:编辑监控关键词(影响未来归类)、pin / unpin

### /entities/[slug]
- 头部:名 / 别名 / canonical_url / 类型 / metadata(twitter / github 等)
- 主区:关联 items 时间线 + 共现 entities

### /digest
- 顶部 tab:daily / weekly / topic
- 列表:每期一个卡片
- 点入:详细页 = 编辑过的"今日/本周精选"(类似旧日报但可点击 + 可反馈)

### /item/[id]
- 左:标题 / 摘要 / 全文(可折叠) / 笔记 / 高亮
- 右:metadata / 推荐打分依据(score_breakdown) / 关联 topics / entities / 相似 items(向量近邻)
- 顶部:keep / archive / trash 大按钮

## 全局
- 顶部条:全局搜索框 + inbox 未读数 + 今日精选按钮
- 命令面板(Cmd/Ctrl+K):快速跳页 / 投喂 / 切 source

## 验收
- 所有页面 < 1s 首屏(本地 docker compose 环境)
- 键盘流可完成:投喂 → 查看 → keep/archive/trash 全流程
- 切深/浅色无闪烁
- 1000 条 inbox 仍流畅(虚拟滚动)
