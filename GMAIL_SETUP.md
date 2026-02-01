# Gmail邮件配置指南

系统已配置为通过Gmail发送邮件到：**ltwoggbuty2mh@gmail.com**

## 步骤1：准备一个Gmail账号

你需要一个Gmail账号作为**发件人**（用于发送日报）。

可以：
- 使用你的个人Gmail账号
- 或创建一个专门的Gmail账号

## 步骤2：生成Gmail App Password（重要！）

**为什么需要App Password？**
- Gmail不允许使用普通密码登录第三方应用
- 必须使用App Password（应用专用密码）

### 生成步骤：

1. **开启两步验证**（如果还没开启）
   - 访问：https://myaccount.google.com/security
   - 找到"两步验证"并启用

2. **生成App Password**
   - 访问：https://myaccount.google.com/apppasswords
   - 或：Google账号 → 安全 → 应用专用密码
   - 选择"邮件"和"Windows计算机"（或其他设备）
   - 点击"生成"
   - **复制16位密码**（格式：xxxx xxxx xxxx xxxx）

3. **保存密码**
   - 这个密码只显示一次
   - 将它填入 `.env` 文件的 `EMAIL_PASSWORD`

## 步骤3：配置 .env 文件

创建 `.env` 文件（或复制 `.env.example`）：

```env
# MiniMax API
MINIMAX_API_KEY=你的新MiniMax密钥
MINIMAX_GROUP_ID=（可选）

# GitHub
GITHUB_TOKEN=你的新GitHub_Token

# Gmail配置
EMAIL_SENDER=your_gmail@gmail.com           # 你的Gmail邮箱
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx          # 16位App Password
EMAIL_RECEIVER=ltwoggbuty2mh@gmail.com      # 收件人（已设置好）
```

### 示例：

```env
EMAIL_SENDER=myaccount@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
EMAIL_RECEIVER=ltwoggbuty2mh@gmail.com
```

**注意**：
- `EMAIL_SENDER` 必须是Gmail邮箱（@gmail.com）
- `EMAIL_PASSWORD` 是16位App Password，不是你的Gmail登录密码
- `EMAIL_RECEIVER` 已经设置为你提供的邮箱

## 步骤4：测试配置

运行测试脚本：

```bash
python test_config.py
```

你应该看到：
```
✓ 环境变量: 通过
✓ 邮件发送: 通过
✓ 测试邮件发送成功，请检查收件箱
```

然后检查 `ltwoggbuty2mh@gmail.com` 的收件箱，应该收到测试邮件。

## 步骤5：运行系统

```bash
python main.py
```

几分钟后，`ltwoggbuty2mh@gmail.com` 将收到第一份AI日报！

## 邮件格式

你会收到：
- **主题**：📰 每日科技资讯简报 - 2026-01-31
- **格式**：精美的HTML格式（带样式）+ 纯文本备用
- **内容**：AI筛选的高质量资讯

## 常见问题

### Q1: "SMTP authentication failed"

**原因**：App Password不正确

**解决**：
1. 确认使用的是App Password，不是Gmail登录密码
2. 重新生成App Password
3. 确保 `.env` 文件中没有多余的空格或引号

### Q2: "两步验证未启用"

**解决**：
1. 访问 https://myaccount.google.com/security
2. 启用两步验证
3. 然后才能生成App Password

### Q3: 收不到邮件

**检查**：
1. 查看垃圾邮件/促销邮件文件夹
2. 检查发件人邮箱配置是否正确
3. 运行 `python test_config.py` 查看错误

### Q4: 想用其他邮箱服务（QQ/163/Outlook）

**可以**，但需要修改SMTP配置：

编辑 `src/notifier/email_notifier.py`：

```python
# QQ邮箱
smtp_server = "smtp.qq.com"
smtp_port = 587

# 163邮箱
smtp_server = "smtp.163.com"
smtp_port = 465

# Outlook
smtp_server = "smtp.office365.com"
smtp_port = 587
```

## 安全提示

- ✅ App Password 只用于此应用，不会泄露Gmail主密码
- ✅ 如果担心安全，可以随时删除App Password
- ✅ `.env` 文件已添加到 `.gitignore`，不会上传到Git
- ✅ 在GitHub Actions中使用Secrets存储密码

## 部署到GitHub Actions

### 配置Secrets

访问仓库：`Settings` → `Secrets and variables` → `Actions`

添加以下Secrets：

| Name | Value |
|------|-------|
| `MINIMAX_API_KEY` | 你的MiniMax API Key |
| `MINIMAX_GROUP_ID` | 你的Group ID（可选） |
| `GH_TOKEN` | 你的GitHub Token |
| `EMAIL_SENDER` | 你的Gmail邮箱 |
| `EMAIL_PASSWORD` | 你的16位App Password |
| `EMAIL_RECEIVER` | ltwoggbuty2mh@gmail.com |

### 自动运行

配置完成后，系统会自动：
- 每天早上8点运行
- 每天晚上8点运行
- 将日报发送到 ltwoggbuty2mh@gmail.com

## 需要帮助？

- 运行测试：`python test_config.py`
- 查看日志：`news_agent.log`
- 参考完整文档：`README.md`

---

**提示**：测试时会立即收到一封测试邮件，确认配置成功后再运行完整系统。
