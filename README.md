# 🤖 AI新闻聚合系统

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-success)](https://github.com/kevinWangSheng/ai-news-agent/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

基于多Agent架构的智能新闻聚合系统，使用MiniMax AI自动搜集、翻译、评估全球科技资讯，并通过邮件每日推送。

🔗 **GitHub仓库**: https://github.com/kevinWangSheng/ai-news-agent

---

## ✨ 核心特性

### 🌍 多地区新闻搜集
- **8个地区**：中国、日本、新加坡、台湾、美国、欧洲、澳大利亚、俄罗斯
- **智能翻译**：自动将俄语、日语等外语新闻翻译成中文
- **中文摘要**：AI生成一句话新闻摘要，快速了解内容
- **重要性评分**：1-10分智能评估，过滤低质量内容

### 🤖 AI科技博客追踪
- **Claude Blog** - Claude产品更新、最佳实践（10篇/期）
- **Anthropic News** - Anthropic官方发布（3篇/期）
- **OpenAI Blog** - GPT系列产品动态（3篇/期）
- **DeepMind Blog** - 研究进展和突破
- **HuggingFace Blog** - 开源AI工具和模型
- **专家博客** - Simon Willison等行业专家观点
- **30天时间窗口**：捕获不频繁更新的高质量内容

### 💻 GitHub开源项目
- 每日热门AI项目（Python、TypeScript、Rust、Go）
- 人工智能、机器学习主题项目
- Star数量、编程语言、项目描述

### 📧 自动化邮件推送
- **QQ邮箱**发送，支持Gmail、Outlook等接收
- **Markdown格式**，链接可直接点击
- **每天2次**：早上8:00和晚上20:00（北京时间）
- **完全自动**：GitHub Actions云端运行，无需本地开机

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────┐
│   主控制器 (Orchestrator)                │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼────┐   ┌───▼────┐   ┌───▼────┐
│ 新闻Agent  │ AI博客Agent│ GitHub   │
│         │   │        │   │ Agent  │
│ 8个地区  │   │ 67篇   │   │ 8项目  │
└───┬────┘   └───┬────┘   └────────┘
    │            │
    └────┬───────┘
         │
    ┌────▼──────────────────┐
    │  MiniMax AI评估器      │
    │  - 翻译外语新闻        │
    │  - 生成中文摘要        │
    │  - 评估重要性(1-10分)  │
    └────┬──────────────────┘
         │
    ┌────▼──────────────┐
    │  报告生成器         │
    │  - Markdown格式    │
    │  - 分类整理         │
    └────┬──────────────┘
         │
    ┌────▼──────────────┐
    │  邮件推送 (QQ Mail) │
    │  → Gmail收件       │
    └───────────────────┘
```

---

## 🚀 快速开始

### 方式1：GitHub Actions部署（推荐）

已完成部署！系统每天自动运行2次。

**仓库地址**: https://github.com/kevinWangSheng/ai-news-agent

**查看运行状态**:
```bash
gh run list --repo kevinWangSheng/ai-news-agent
```

**手动触发运行**:
```bash
gh workflow run "Daily News Aggregation" --repo kevinWangSheng/ai-news-agent
```

### 方式2：本地运行

#### 1. 克隆仓库
```bash
git clone https://github.com/kevinWangSheng/ai-news-agent.git
cd ai-news-agent
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入配置：

```env
# MiniMax API配置（用于AI评估和翻译）
MINIMAX_API_KEY=your_minimax_api_key
MINIMAX_GROUP_ID=                    # 可选，留空即可

# GitHub Token（用于搜集GitHub项目）
GITHUB_TOKEN=your_github_token

# QQ邮箱配置（发送邮件）
EMAIL_SENDER=your_qq_email@qq.com
EMAIL_PASSWORD=your_qq_auth_code     # QQ邮箱授权码，非密码
EMAIL_RECEIVER=receiver@gmail.com    # 接收邮箱
```

#### 4. 获取必要的API密钥

**MiniMax API Key**:
1. 访问 https://www.minimaxi.com/
2. 注册账号并创建API密钥
3. 每天约¥1-3费用

**GitHub Token**:
1. 访问 https://github.com/settings/tokens
2. 生成新Token，勾选 `repo` 权限
3. 完全免费

**QQ邮箱授权码**:
1. 登录QQ邮箱 → 设置 → 账户
2. 开启"SMTP服务"
3. 生成授权码（16位字符）

#### 5. 测试运行

```bash
python main.py
```

成功后，您的收件邮箱会收到测试邮件📧

## 📝 GitHub Actions部署详情

本项目已部署到GitHub Actions，每天自动运行。

**仓库地址**: https://github.com/kevinWangSheng/ai-news-agent

### 已配置的Secrets

系统已配置以下6个Secrets：
- ✅ `MINIMAX_API_KEY` - MiniMax AI评估接口
- ✅ `MINIMAX_GROUP_ID` - MiniMax组ID（可选）
- ✅ `GH_TOKEN` - GitHub API访问令牌
- ✅ `EMAIL_SENDER` - QQ邮箱发送地址
- ✅ `EMAIL_PASSWORD` - QQ邮箱授权码
- ✅ `EMAIL_RECEIVER` - Gmail接收地址

### 运行计划

- 🕐 **每天 08:00** 北京时间（UTC 00:00）
- 🕐 **每天 20:00** 北京时间（UTC 12:00）

### 如需重新部署

详细步骤请参考 [DEPLOY_GITHUB.md](DEPLOY_GITHUB.md)

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
│   │   └── email_notifier.py
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
- QQ邮箱SMTP: 完全免费
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

### 2. 邮件发送失败

```
错误：SMTP认证失败
解决：
1. 确认QQ邮箱已开启SMTP服务
2. 检查授权码是否正确（不是QQ密码）
3. 确认EMAIL_SENDER和EMAIL_PASSWORD配置正确
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

### 添加新的AI博客源

编辑 `config/config.yaml`，在 `tech_sources` 下添加：

```yaml
tech_sources:
  - name: "新博客名称"
    url: "https://example.com/blog"
    type: "rss"  # 或 "web" 如果需要网页抓取
    priority: "high"
    max_items: 10
```

## 贡献

欢迎提交Issue和Pull Request！

## 许可

MIT License

---

**警告：请保护好你的API密钥，不要泄露！**
