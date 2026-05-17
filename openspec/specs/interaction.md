# Spec: Interaction(用户交互)

## 目的
记录用户对每条 item 的所有动作,作为偏好学习的燃料。

## 用户可发起的动作

| Action | 触发场景 | 落 interactions 表 |
|---|---|---|
| `view` | 打开详情页 / inbox 卡片展开 | 是,带 dwell_seconds |
| `keep` | 点"留下"按钮 | 是,items.status → kept |
| `archive` | 点"归档" | 是,items.status → archived |
| `trash` | 点"丢弃" | 是,items.status → trashed |
| `highlight` | 选中文本 → 高亮 | 是,带 highlight_text |
| `note` | 写笔记 | 是,带 note_text;items.user_note 也写 |
| `tag_add` | 手动加 tag | 是 |
| `tag_remove` | 手动删 tag | 是 |
| `topic_pin` | 把某 topic pin 到首页 | 是 |
| `share` | 复制链接 / 导出 | 是 |

## 偏好学习的使用方式

### 在 scoring 阶段(processing 第 4 步)
- 计算 `tag_keep_rate[tag]` = `keep / (keep+archive+trash)` 历史窗口 30 天
- 同 entity / source 同理
- 给新 item 的 final_score 加权:
  - 命中高 keep 率 tag → +0.5 ~ +1.5
  - 命中高 trash 率 source → -0.5 ~ -2
- 全部偏好系数对用户**可见**(item 详情页"为什么推荐"展开看)

### 在 inbox 排序
- 默认按 final_score desc
- 用户可切"按时间 desc / 按 source / 按 topic 分组"

### 冷启动
- interactions 表 < 50 条时偏好分一律为 0
- 不学,避免噪音放大

## 不显式记录"未读"
- 进入详情页 = view 一次
- 多次 view 算 view 多次
- 没 view 过的 item 在 inbox 用未读小圆点表示

## 验收
- 每个动作 100ms 内落库
- 偏好分变化可在"为什么推荐"面板看到具体加减分依据
- 一周累积 50 条 interactions 后,偏好分明显生效(对比有/无偏好分的 final_score 排序)
- 撤销:`POST /api/items/{id}/interactions/{id}/undo` 能撤销最近一次状态变更
