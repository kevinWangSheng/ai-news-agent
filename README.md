# 多Agent新闻聚合系统

基于MiniMax AI的智能新闻聚合系统，自动搜集全球科技资讯并推送到Telegram。

## 功能特点

- 🌏 **多地区新闻搜集**：亚洲（中国、日本、新加坡、台湾）、欧洲、美洲、其他地区
- 🤖 **AI科技资讯**：自动追踪OpenAI、Claude、Google AI等厂商动态
- 💻 **GitHub热门项目**：发现最新的开源项目和技术趋势
- 🧠 **AI智能评估**：使用MiniMax API自动筛选高质量内容
- 📱 **即时推送**：通过Telegram Bot推送到手机
- ⚡ **并行处理**：多Agent并行工作，10秒内完成所有搜集

## 架构设计

```
主控Agent (Orchestrator)
    ├─→ 亚洲Agent (中国/日本/新加坡/台湾)
    ├─→ 美洲Agent (美国)
    ├─→ 欧洲Agent
    ├─→ 其他地区Agent (澳大利亚/俄罗斯)
    ├─→ AI科技Agent
    └─→ GitHub Agent
          ↓
    AI评估Agent (MiniMax)
          ↓
    Telegram推送
```

## 快速开始

### 1. 安装依赖

```bash
cd news-agent-system
pip install -r requirements.txt
```

### 2. 配置环境变量

**重要：先撤销你之前暴露的API密钥！**

#### 撤销已暴露的密钥：
1. GitHub Token：访问 https://github.com/settings/tokens 删除旧token
2. MiniMax API Key：登录MiniMax控制台删除旧密钥

#### 创建新的密钥：
复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的密钥：

```env
# MiniMax API配置
MINIMAX_API_KEY=your_new_minimax_key
MINIMAX_GROUP_ID=your_group_id

# GitHub配置（重新生成）
GITHUB_TOKEN=your_new_github_token

# Telegram配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. 获取Telegram Bot Token

1. 打开Telegram，搜索 `@BotFather`
2. 发送 `/newbot`
3. 按提示创建Bot，获取Token
4. 搜索 `@userinfobot`，获取你的Chat ID

### 4. 测试运行

```bash
python main.py
```

## 部署到GitHub Actions（免费）

### 1. 创建GitHub仓库

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/news-agent.git
git push -u origin main
```

### 2. 配置GitHub Secrets

访问仓库设置：`Settings` → `Secrets and variables` → `Actions`

添加以下Secrets：
- `MINIMAX_API_KEY`
- `MINIMAX_GROUP_ID`
- `GH_TOKEN`（新的GitHub Token）
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 3. 启用GitHub Actions

- 仓库 → `Actions` → 启用workflows
- 每天自动运行2次（早8点/晚8点）
- 也可以手动触发

## 配置说明

### 修改搜集地区和关键词

编辑 `config/config.yaml`：

```yaml
regions:
  asia:
    - name: "中国"
      keywords: ["AI", "科技", "创新"]  # 修改关键词
      max_items: 5  # 每个地区最多几条
```

### 修改运行时间

编辑 `.github/workflows/daily_news.yml`：

```yaml
schedule:
  - cron: '0 0 * * *'   # UTC时间，需要转换成北京时间
```

### 修改AI评估标准

编辑 `config/config.yaml`：

```yaml
evaluation:
  criteria:
    importance_threshold: 6  # 评分阈值（1-10）
    min_quality_score: 7
```

## 项目结构

```
news-agent-system/
├── src/
│   ├── agents/           # 各地区Agent
│   │   ├── asia_agent.py
│   │   ├── americas_agent.py
│   │   ├── europe_agent.py
│   │   ├── others_agent.py
│   │   ├── tech_agent.py
│   │   └── github_agent.py
│   ├── collectors/       # 数据搜集工具
│   │   └── news_collector.py
│   ├── evaluator/        # AI评估器
│   │   └── ai_evaluator.py
│   ├── notifier/         # 通知器
│   │   └── telegram_bot.py
│   └── orchestrator.py   # 主控制器
├── config/
│   └── config.yaml       # 配置文件
├── .github/workflows/
│   └── daily_news.yml    # GitHub Actions配置
├── main.py               # 入口文件
├── requirements.txt      # 依赖列表
├── .env.example          # 环境变量模板
└── .gitignore
```

## 成本估算

### 免费层：
- GitHub Actions: 免费2000分钟/月
- Telegram: 完全免费
- Google News RSS: 免费
- GitHub API: 免费（有token：5000次/小时）

### 付费部分：
- MiniMax API: 约¥1-3/天
- 月成本：¥30-90

## 故障排查

### 1. MiniMax API错误

```
错误：401 Unauthorized
解决：检查API Key是否正确，是否过期
```

### 2. Telegram推送失败

```
错误：chat_id不正确
解决：确保使用的是你的Chat ID（纯数字）
```

### 3. GitHub Actions失败

```
错误：Secrets未配置
解决：检查仓库Settings → Secrets是否都配置了
```

## 安全建议

- ✅ 永远不要在代码中硬编码API密钥
- ✅ 使用 `.env` 文件存储本地密钥
- ✅ 确保 `.env` 已添加到 `.gitignore`
- ✅ GitHub Secrets用于CI/CD环境
- ✅ 定期更换API密钥

## 扩展功能

### 添加新地区

编辑 `config/config.yaml`，在相应区域添加：

```yaml
regions:
  asia:
    - name: "韩国"
      code: "KR"
      language: "ko"
      keywords: ["기술", "AI"]
      max_items: 5
```

### 添加邮件通知

安装依赖：
```bash
pip install secure-smtplib
```

在 `.env` 添加：
```env
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECEIVER=receiver@email.com
```

## 贡献

欢迎提交Issue和Pull Request！

## 许可

MIT License

---

**警告：请保护好你的API密钥，不要泄露！**
