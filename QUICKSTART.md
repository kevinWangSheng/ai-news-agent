# 快速入门指南

## 5分钟快速配置

### 第1步：安全警告（必读！）

**你之前发送的API密钥已经暴露！必须立即撤销：**

1. **GitHub Token**：
   - 访问：https://github.com/settings/tokens
   - 找到并删除暴露的token
   - 点击 `Generate new token (classic)`
   - 勾选 `repo` 和 `read:user` 权限
   - 生成并保存新token

2. **MiniMax API Key**：
   - 登录：https://www.minimaxi.com/
   - 删除旧的API Key
   - 生成新的API Key

### 第2步：获取Telegram Bot（2分钟）

1. 打开Telegram，搜索 `@BotFather`
2. 发送：`/newbot`
3. 按提示设置Bot名称和用户名
4. 复制Bot Token（格式：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`）
5. 搜索 `@userinfobot`，发送任意消息
6. 复制你的Chat ID（纯数字，如：`123456789`）

### 第3步：配置环境变量（1分钟）

在项目根目录创建 `.env` 文件：

```env
# MiniMax API
MINIMAX_API_KEY=你的新MiniMax密钥
MINIMAX_GROUP_ID=（如果有的话）

# GitHub
GITHUB_TOKEN=你的新GitHub_Token

# Telegram
TELEGRAM_BOT_TOKEN=你的Bot_Token
TELEGRAM_CHAT_ID=你的Chat_ID
```

**重要**：
- 不要在 `.env` 周围添加引号
- 直接粘贴密钥即可
- 确保 `.env` 文件不被提交到Git

### 第4步：安装依赖（1分钟）

```bash
cd news-agent-system
pip install -r requirements.txt
```

### 第5步：测试配置（1分钟）

```bash
python test_config.py
```

如果看到 `✓ 所有测试通过`，说明配置成功！

你会收到一条Telegram测试消息。

### 第6步：运行系统

```bash
python main.py
```

几分钟后，你会收到第一份AI日报！

## 部署到GitHub Actions（自动运行）

### 1. 初始化Git仓库

```bash
git init
git add .
git commit -m "Initial commit"
```

### 2. 创建GitHub私有仓库

- 访问：https://github.com/new
- 仓库名：`news-agent`
- 设置为 **Private**（重要！）
- 不要初始化README

### 3. 推送代码

```bash
git remote add origin https://github.com/你的用户名/news-agent.git
git branch -M main
git push -u origin main
```

### 4. 配置GitHub Secrets

访问仓库页面：`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

添加以下5个Secrets：

| Name | Value |
|------|-------|
| `MINIMAX_API_KEY` | 你的MiniMax API Key |
| `MINIMAX_GROUP_ID` | 你的Group ID（如果有） |
| `GH_TOKEN` | 你的新GitHub Token |
| `TELEGRAM_BOT_TOKEN` | 你的Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | 你的Telegram Chat ID |

### 5. 启用Actions

- 仓库 → `Actions` 标签
- 点击 `I understand my workflows, go ahead and enable them`

### 6. 测试运行

- 进入 `Actions` 标签
- 点击左侧 `Daily News Aggregation`
- 点击右侧 `Run workflow`
- 点击绿色的 `Run workflow` 按钮

等待1-2分钟，你会收到日报！

## 自动运行时间

系统默认每天运行2次：
- 早上 8:00（北京时间）
- 晚上 8:00（北京时间）

## 自定义配置

### 修改运行时间

编辑 `.github/workflows/daily_news.yml`：

```yaml
schedule:
  - cron: '0 0 * * *'   # UTC 00:00 = 北京 08:00
  - cron: '0 12 * * *'  # UTC 12:00 = 北京 20:00
```

在线工具：https://crontab.guru/

### 修改搜集地区

编辑 `config/config.yaml`，添加或删除地区。

### 调整评分阈值

编辑 `config/config.yaml`：

```yaml
evaluation:
  criteria:
    importance_threshold: 6  # 降低此值会得到更多新闻
```

## 常见问题

### Q: 为什么没有收到消息？

A: 检查：
1. Telegram Chat ID是否正确（纯数字）
2. 是否启动了和Bot的对话（发送 `/start`）
3. 查看 `news_agent.log` 日志文件

### Q: MiniMax API调用失败？

A: 检查：
1. API Key是否正确
2. 是否有余额
3. 是否超过调用限额

### Q: GitHub Actions运行失败？

A: 检查：
1. Secrets是否全部配置
2. 仓库是否启用了Actions
3. 查看Actions的日志输出

### Q: 新闻质量不高？

A: 调整配置：
1. 增加 `importance_threshold` 值（更严格）
2. 修改关键词列表
3. 调整 `max_items` 数量

## 进阶使用

### 本地定时运行（不用GitHub Actions）

Windows任务计划程序：
```
程序：python
参数：C:\path\to\news-agent-system\main.py
触发器：每天2次
```

Linux crontab：
```bash
0 8,20 * * * cd /path/to/news-agent-system && python main.py
```

### 添加邮件通知

编辑 `config/config.yaml`：

```yaml
notification:
  email:
    enabled: true
```

在 `.env` 添加：
```env
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=app_password
EMAIL_RECEIVER=receiver@email.com
```

## 需要帮助？

- 查看详细文档：`README.md`
- 检查日志：`news_agent.log`
- 运行测试：`python test_config.py`

---

祝使用愉快！
