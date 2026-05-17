**Status: planned-outline** — 等 015 落地 + 用户 dogfood 几天后基于真实痛点细化 tasks.md / design.md

# 016 · Second Brain — 从 Reader 升级到主动协助

## 背景

014 解决"内容拿得到吗",015 解决"内容看得舒服吗"。**但你打开 hub 还是要花脑力**:这 600 条里哪个跟我昨天看的有关?哪个值得深读?谁在 follow 哪个主题?

016 把 hub 从被动 reader 升级为**主动协助**:LLM 帮你看、帮你连、帮你提醒。

## 候选功能(等 015 dogfood 后细化优先级)

### F1 「问问 Claude 这条说了啥」
- item 详情页"AI 解读"按钮
- 弹层:Claude 把 content_md 用更短、更直接的中文重写 + 你能追问"这个跟 XX 协议有啥区别?"
- 价值:长文章不想读完时,先看 AI 几句话定位是否值得深读
- 技术:已有 `get_claude()` + content_md,prompt 写好就行

### F2 找跟它相关的之前条目(LLM 二次思考)
- 当前 `/api/items/{id}/related` 用 pgvector cosine,返回 top-5
- 升级:再走一遍 Claude,问"这 5 条里哪个跟当前这条**真有 substantive 关联**(不是表面词汇相似)"
- 输出:筛过的 2-3 条 + 一句话说明关系
- 价值:从"看起来像"升级到"真的相关"

### F4 `/ask` 全库自然语言问答
- 一个搜索框,输入 "MCP 协议解决了什么问题?"
- 后端:cosine 召回 top-10 → Claude prompt(带 chunk + cite)→ 回答 + 引用链接
- 价值:hub 真正变 "second brain",问任何问题都能从你的库里找答案
- 技术:embedding 已有,只需一个新端点 + 一个简单页面

### E1 关注主题 / 实体 → 新条目高亮
- 「关注 #mcp」按钮 → 入库到新表 `user_follows`
- 新条目匹配关注 → inbox 顶部"关注主题更新"区块
- 价值:不用手动 filter,新内容自己冒出来

### E2 信源 mute / boost(UI 上)
- /settings 加面板:每源显示 24h 入库数 + mute 开关 + +/- boost 分
- 改动写回 `config.yaml` 还是入 DB?(讨论)
- 价值:不喜欢 LangChain 频繁发广告 → mute;Anthropic 必看 → +2 分

### E3 自定义主题
- 自己定义 "RAG 工程化" 主题 + 关键词
- 已有 topics 表,只需 UI 让用户增/改
- 价值:不只看 yaml 配的 34 个

### C6 trending cluster(从 015 推迟)
- 多个独立源同一天讨论同一关键词 / topic → cluster
- inbox 顶部"今日热议 3 个话题",每个 cluster 进去看属于它的 items
- 算法:简单的 `tag + 同日 + 源数 ≥ 2`,后续可改 embedding 聚类
- 价值:发现高信号 trending

### G3 自动归档老低分(降噪)
- daily job:`status='inbox' AND final_score < 5 AND ingested_at < now - 7d` → 自动 archived
- 可选,有人喜欢"自己掌控"
- 价值:inbox 不爆炸

## 等你 dogfood 后细化

015 完成后,真用一周,把以下几条挑出来:
- 哪些功能"用过就回不去"
- 哪些"听起来好,真用了发现没必要"
- 哪些没列出来但实际需要

然后再写 016 的 tasks.md / design.md。

## 已知的范围边界

不在 016 做:
- 风格大改(017)
- 手机响应(017)
- 浏览器扩展(memory: v3 推迟)
- 多用户(永不,本系统是单用户 second brain)
