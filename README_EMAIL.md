# 多Agent新闻聚合系统（邮件版）

基于MiniMax AI的智能新闻聚合系统，自动搜集全球科技资讯并通过**邮件**发送到 `ltwoggbuty2mh@gmail.com`

## 功能特点

- 🌏 **多地区新闻搜集**：中国、日本、新加坡、台湾、欧洲、美国、澳大利亚、俄罗斯
- 🤖 **AI科技资讯**：OpenAI、Claude、Google AI等厂商动态
- 💻 **GitHub热门项目**：最新开源项目和技术趋势
- 🧠 **AI智能评估**：MiniMax自动筛选高质量内容
- 📧 **邮件推送**：精美HTML格式日报直达邮箱
- ⚡ **并行处理**：多Agent并行，10秒完成搜集

## 快速开始

### 1. 安装依赖

```bash
cd news-agent-system
pip install -r requirements.txt
```

### 2. 配置Gmail（重要）

**系统需要一个Gmail账号作为发件人。**

#### 步骤A：生成Gmail App Password

1. 访问：https://myaccount.google.com/apppasswords
2. 启用两步验证（如果未启用）
3. 生成App Password（选择"邮件"和"其他设备"）
4. 复制16位密码（格式：xxxx xxxx xxxx xxxx）

**详细教程**：查看 `GMAIL_SETUP.md`

### 3. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env`，填入配置：

```env
# MiniMax API（需要新的密钥）
MINIMAX_API_KEY=your_new_minimax_key
MINIMAX_GROUP_ID=（可选）

# GitHub（需要新的Token）
GITHUB_TOKEN=your_new_github_token

# Gmail配置
EMAIL_SENDER=your_gmail@gmail.com          # 你的Gmail邮箱
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx         # 16位App Password
EMAIL_RECEIVER=ltwoggbuty2mh@gmail.com     # 收件人（已配置）
```

**重要安全提醒**：
- 你之前发送的GitHub Token和MiniMax API Key已经暴露
- 必须访问对应平台删除旧密钥并生成新的

### 4. 测试配置

```bash
python test_config.py
```

如果看到 `✓ 所有测试通过`，检查 `ltwoggbuty2mh@gmail.com` 是否收到测试邮件。

### 5. 运行系统

```bash
python main.py
```

几分钟后，`ltwoggbuty2mh@gmail.com` 将收到第一份AI日报！

## 邮件日报示例

**主题**：📰 每日科技资讯简报 - 2026-01-31

**内容格式**：
- 精美的HTML格式（带CSS样式）
- 分类清晰：全球要闻 / AI科技 / GitHub项目
- 包含链接、评分、AI点评
- 总长度800-1500字

**查看示例**：`EXAMPLE_OUTPUT.md`

## 部署到GitHub Actions（自动运行）

### 1. 创建GitHub仓库

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/news-agent.git
git push -u origin main
```

### 2. 配置GitHub Secrets

访问：`Settings` → `Secrets and variables` → `Actions`

添加6个Secrets：

| Secret Name | Value |
|-------------|-------|
| `MINIMAX_API_KEY` | 你的MiniMax API Key |
| `MINIMAX_GROUP_ID` | 你的Group ID（可选） |
| `GH_TOKEN` | 你的新GitHub Token |
| `EMAIL_SENDER` | 你的Gmail邮箱 |
| `EMAIL_PASSWORD` | Gmail App Password（16位） |
| `EMAIL_RECEIVER` | ltwoggbuty2mh@gmail.com |

### 3. 启用Actions

- 进入仓库的 `Actions` 标签
- 点击启用workflows
- 手动运行测试：`Run workflow`

### 4. 自动运行时间

系统默认每天运行2次：
- **早上8:00**（北京时间）
- **晚上8:00**（北京时间）

修改时间：编辑 `.github/workflows/daily_news.yml`

## 项目结构

```
news-agent-system/
├── src/
│   ├── agents/              # 8个并行Agent
│   ├── collectors/          # 新闻搜集工具
│   ├── evaluator/           # MiniMax AI评估
│   └── notifier/
│       └── email_notifier.py  # Gmail邮件发送
├── config/config.yaml       # 地区、关键词配置
├── .env                     # API密钥（本地）
├── main.py                  # 入口文件
└── test_config.py           # 配置测试
```

## 自定义配置

### 修改搜集地区

编辑 `config/config.yaml`：

```yaml
regions:
  asia:
    - name: "中国"
      keywords: ["AI", "科技"]  # 修改关键词
      max_items: 5              # 每地区条数
```

### 调整AI评分阈值

```yaml
evaluation:
  criteria:
    importance_threshold: 6  # 提高分数=更严格筛选
```

### 修改运行频率

编辑 `.github/workflows/daily_news.yml`：

```yaml
schedule:
  - cron: '0 0 * * *'   # 每天一次
  # 或
  - cron: '0 */6 * * *' # 每6小时一次
```

## 成本分析

### 免费部分：
- GitHub Actions: 2000分钟/月（足够）
- Gmail发送: 完全免费
- Google News RSS: 免费
- GitHub API: 免费

### 付费部分：
- MiniMax API: 约¥1-3/天
- **月成本：¥30-90**

### 降低成本：
1. 减少运行频率（每天1次）
2. 降低搜集条数
3. 使用Gemini免费层替代MiniMax

## 常见问题

### Q: 为什么收不到邮件？

**检查**：
1. 垃圾邮件文件夹
2. 促销邮件/订阅邮件分类
3. Gmail App Password是否正确
4. 运行 `python test_config.py` 查看错误

### Q: SMTP authentication failed

**原因**：App Password不正确

**解决**：
1. 确认使用App Password，不是Gmail登录密码
2. 重新生成：https://myaccount.google.com/apppasswords
3. 确保两步验证已启用

### Q: 想改成其他邮箱接收

**修改**：
1. 编辑 `.env` 中的 `EMAIL_RECEIVER`
2. 编辑 `config/config.yaml` 中的 `notification.email.receiver`

### Q: 邮件格式不好看

**自定义**：编辑 `src/notifier/email_notifier.py` 中的CSS样式

## 安全提示

- ✅ 使用App Password，不泄露Gmail主密码
- ✅ `.env` 文件不会上传到Git
- ✅ GitHub Secrets加密存储
- ✅ 可随时删除App Password

## 文档索引

- **快速配置**：`QUICKSTART.md`
- **Gmail设置**：`GMAIL_SETUP.md`（详细教程）
- **输出示例**：`EXAMPLE_OUTPUT.md`
- **完整文档**：`README.md`

## 故障排查

1. **测试配置**：`python test_config.py`
2. **查看日志**：`news_agent.log`
3. **手动运行**：`python main.py`

## 获取API密钥

### MiniMax API
- 注册：https://www.minimaxi.com/
- 删除旧密钥，生成新密钥

### GitHub Token
- 访问：https://github.com/settings/tokens
- 删除暴露的token
- 生成新token（勾选 `repo` 权限）

### Gmail App Password
- 访问：https://myaccount.google.com/apppasswords
- 生成16位密码

## 需要帮助？

- 运行测试：`python test_config.py`
- Gmail配置：查看 `GMAIL_SETUP.md`
- 查看日志：`news_agent.log`

---

**系统已配置为发送到：ltwoggbuty2mh@gmail.com**

祝使用愉快！📧
