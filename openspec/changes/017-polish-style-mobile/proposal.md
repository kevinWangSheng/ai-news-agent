**Status: planned-sketch** — 等 015+016 落地 + 真实使用形态稳定后再细化

# 017 · Polish, Style & Mobile — 视觉收尾 + 长尾体验

## 范围(全部待 dogfood 后细化)

### 视觉风格
- **B2 整体风格选定**:报刊 / 终端 / 杂志 / 效率工具 / 调现状,5 选 1
- 主色调 + 字体系统 + 卡片阴影层级
- Logo / 品牌色

### 手机响应
- sidebar 在小屏改 drawer / bottom nav
- inbox 卡片小屏紧凑布局
- 阅读详情页大屏 / 小屏字号
- 决议:目标是"小屏可看可点 keep/archive",**不期望复杂操作在小屏完成**

### 长尾交互
- Reader Mode(distraction-free 大字阅读)
- 阅读进度条
- annotation / highlight 持久化(`interactions.action='highlight'` 已支持,前端没用)
- 14 天前未交互自动 archive 提示
- review 页:本周 keep 了什么 / 高分主题 / 阅读时长统计

### 可访问性
- 键盘 focus 可见
- aria 标签全覆盖
- 暗色 / 高对比模式
- 屏幕阅读器支持

### 备份 / 导出
- 一键 SQL dump
- 导出 kept 为 markdown / Notion / Bear / Obsidian
- 导入 / migrate 工具

### onboarding
- 第一次打开教学引导
- 5 个推荐入门 item
- 键盘 shortcut 介绍

## 等 015+016 完成且用一段时间后再细化

到那时已经有更具体的痛点和品味偏好,不会在空气里设计。
