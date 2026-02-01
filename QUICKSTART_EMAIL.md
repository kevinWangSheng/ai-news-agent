# 快速入门指南（邮件版）

## 5分钟配置邮件日报

系统会自动将AI日报发送到：**ltwoggbuty2mh@gmail.com**

---

## 第1步：安全警告（必读！）⚠️

**你之前发送的API密钥已经暴露！必须立即撤销：**

### 撤销暴露的密钥：

1. **GitHub Token**
   - 访问：https://github.com/settings/tokens
   - 删除旧token → 生成新token（勾选 `repo` 权限）

2. **MiniMax API Key**
   - 登录：https://www.minimaxi.com/
   - 删除旧密钥 → 生成新密钥

---

## 第2步：配置Gmail发件邮箱（3分钟）

### 需要一个Gmail账号作为"发件人"

可以使用现有Gmail或创建新的。

### 生成App Password（重要！）

**为什么需要？**
- Gmail不允许第三方用普通密码登录
- 必须使用"应用专用密码"

**步骤**：

1. **启用两步验证**
   - 访问：https://myaccount.google.com/security
   - 找到"两步验证" → 启用

2. **生成App Password**
   - 访问：https://myaccount.google.com/apppasswords
   - 选择"邮件"和"Windows/Mac"
   - 点击"生成"
   - **复制16位密码**（格式：xxxx xxxx xxxx xxxx）

3. **保存密码**
   - 密码只显示一次，立即复制

> **详细图文教程**：查看 `GMAIL_SETUP.md`

---

## 第3步：配置环境变量（1分钟）

在项目根目录创建 `.env` 文件：

```env
# MiniMax API（新密钥）
MINIMAX_API_KEY=你的新MiniMax密钥
MINIMAX_GROUP_ID=

# GitHub（新Token）
GITHUB_TOKEN=你的新GitHub_Token

# Gmail配置
EMAIL_SENDER=你的gmail@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_RECEIVER=ltwoggbuty2mh@gmail.com
```

**填写说明**：
- `EMAIL_SENDER`：你的Gmail邮箱地址
- `EMAIL_PASSWORD`：刚才生成的16位App Password
- `EMAIL_RECEIVER`：已设置好，不需要修改

**示例**：
```env
EMAIL_SENDER=mywork@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
EMAIL_RECEIVER=ltwoggbuty2mh@gmail.com
```

---

## 第4步：安装依赖（1分钟）

```bash
cd news-agent-system
pip install -r requirements.txt
```

---

## 第5步：测试配置（30秒）

```bash
python test_config.py
```

**期望输出**：
```
✓ 环境变量: 通过
✓ 邮件发送: 通过
✓ 测试邮件发送成功，请检查收件箱
✓ MiniMax API: 通过
✓ 新闻搜集: 通过

✓ 所有测试通过！
```

**检查邮箱**：
- 打开 `ltwoggbuty2mh@gmail.com`
- 应该收到一封测试邮件
- 标题：🧪 新闻聚合系统测试邮件

> 如果在垃圾邮件文件夹，标记为"非垃圾邮件"

---

## 第6步：运行系统 🚀

```bash
python main.py
```

**运行过程**（约2-5分钟）：
1. 搜集8个地区的新闻
2. 搜集AI科技文章
3. 搜集GitHub热门项目
4. AI评估和筛选
5. 生成日报
6. 发送邮件

**完成后**：
- 检查 `ltwoggbuty2mh@gmail.com`
- 应该收到完整的AI日报！

---

## 部署到GitHub（自动运行）

### 1. 创建仓库

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/news-agent.git
git push -u origin main
```

### 2. 配置Secrets

访问：仓库 → `Settings` → `Secrets and variables` → `Actions`

点击 `New repository secret`，添加6个：

| Name | Value |
|------|-------|
| `MINIMAX_API_KEY` | 你的MiniMax密钥 |
| `MINIMAX_GROUP_ID` | （可选，没有就留空） |
| `GH_TOKEN` | 你的新GitHub Token |
| `EMAIL_SENDER` | 你的Gmail邮箱 |
| `EMAIL_PASSWORD` | 16位App Password |
| `EMAIL_RECEIVER` | ltwoggbuty2mh@gmail.com |

### 3. 启用Actions

- 仓库 → `Actions` 标签
- 点击 `I understand my workflows, go ahead and enable them`
- 点击 `Daily News Aggregation`
- 点击 `Run workflow` → 绿色按钮

### 4. 自动运行时间

配置完成后，系统会**自动**运行：
- ⏰ 每天早上 8:00（北京时间）
- ⏰ 每天晚上 8:00（北京时间）

日报会自动发送到 `ltwoggbuty2mh@gmail.com`

---

## 邮件日报包含什么？

📧 **主题**：📰 每日科技资讯简报 - 2026-01-31

📄 **内容**：
- 🌏 全球要闻精选（8个地区）
- 🤖 AI科技动态（OpenAI/Claude/Google等）
- 💻 GitHub热门项目（AI相关）
- 每条新闻都有AI评分和点评
- 精美的HTML格式

📊 **长度**：800-1500字（5分钟阅读）

---

## 常见问题

### ❌ 测试时"SMTP authentication failed"

**原因**：App Password不正确

**解决**：
1. 确认用的是App Password，不是Gmail登录密码
2. 检查两步验证是否已启用
3. 重新生成App Password

### ❌ 收不到邮件

**检查**：
1. 垃圾邮件/促销邮件文件夹
2. 发件人是否被屏蔽
3. 运行 `python test_config.py` 看报错

### ❌ GitHub Actions运行失败

**检查**：
1. 所有6个Secrets是否都配置了
2. Secrets名称是否正确（区分大小写）
3. 查看Actions页面的错误日志

### ⚙️ 想改成每天运行1次

编辑 `.github/workflows/daily_news.yml`：

```yaml
schedule:
  - cron: '0 0 * * *'  # 只保留一行
```

### 📧 想添加更多收件人

编辑 `src/notifier/email_notifier.py`，修改发送逻辑支持多收件人。

---

## 文档参考

- 📖 **Gmail详细配置**：`GMAIL_SETUP.md`
- 📖 **完整文档**：`README_EMAIL.md`
- 📖 **输出示例**：`EXAMPLE_OUTPUT.md`

---

## 需要帮助？

1. **测试配置**：`python test_config.py`
2. **查看日志**：`news_agent.log`
3. **Gmail教程**：`GMAIL_SETUP.md`

---

## ✅ 检查清单

在运行系统前，确认：

- [ ] 已撤销暴露的GitHub Token和MiniMax密钥
- [ ] 已生成新的API密钥
- [ ] Gmail两步验证已启用
- [ ] 已生成Gmail App Password
- [ ] `.env` 文件已创建并填写完整
- [ ] 运行 `python test_config.py` 全部通过
- [ ] 收到测试邮件

全部完成？运行 `python main.py` 开始使用！

---

**系统配置收件人：ltwoggbuty2mh@gmail.com** ✉️

祝使用愉快！
