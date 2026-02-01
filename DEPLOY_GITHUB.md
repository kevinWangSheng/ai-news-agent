# 🚀 GitHub Actions 部署指南

## 步骤1：创建GitHub仓库

1. 打开 https://github.com/new
2. 填写仓库信息：
   - **仓库名**: `ai-news-agent` （或任意名称）
   - **可见性**: 选择 `Private`（私有仓库，保护隐私）
   - **不要**勾选 "Add a README file"
   - **不要**勾选 "Add .gitignore"
3. 点击 **Create repository**

---

## 步骤2：配置GitHub Secrets（重要！）

1. 进入刚创建的仓库
2. 点击 **Settings** （设置）
3. 左侧菜单找到 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**
5. 添加以下6个密钥：

### 需要添加的Secrets：

| Name | Value (从.env文件中获取) |
|------|------------------------|
| `MINIMAX_API_KEY` | `sk-api-snkcC-0gtPYdMhw3suhW8QXzMut-af6wLllhnM85mfux9P9LnT7ebyWq8EIfaVHYxbLncAEu8_fraHNKdVEnd1m_fiEQGWpYdwb8jMj0HNhx2ex8iHLN4A0` |
| `MINIMAX_GROUP_ID` | 留空（或您的Group ID，如果有的话） |
| `GH_TOKEN` | `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` |
| `EMAIL_SENDER` | `2545321988@qq.com` |
| `EMAIL_PASSWORD` | `qefjbhzndnpmechf` |
| `EMAIL_RECEIVER` | `ltwoggbuty2mh@gmail.com` |

**⚠️ 重要提示：**
- 每个Secret都要单独添加
- Name必须完全一致（区分大小写）
- Value从上表中复制

---

## 步骤3：推送代码到GitHub

回到本地终端，运行以下命令：

```bash
cd /c/dev/ai/news-agent-system

# 添加远程仓库（替换YOUR_USERNAME和YOUR_REPO_NAME）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 推送代码
git branch -M main
git push -u origin main
```

**示例：**
如果您的GitHub用户名是 `john`，仓库名是 `ai-news-agent`，则运行：
```bash
git remote add origin https://github.com/john/ai-news-agent.git
git branch -M main
git push -u origin main
```

---

## 步骤4：验证部署

1. 推送成功后，访问您的GitHub仓库
2. 点击 **Actions** 标签
3. 应该看到工作流：`Daily News Aggregation`
4. 点击工作流名称，然后点击右侧 **Run workflow** → **Run workflow**
5. 等待几分钟，检查是否运行成功（绿色✓）
6. 检查邮箱是否收到测试邮件

---

## 步骤5：自动化已启用！

✅ 系统将自动在以下时间运行：
- **每天 08:00** 北京时间（UTC 00:00）
- **每天 20:00** 北京时间（UTC 12:00）

✅ 您也可以随时手动运行：
1. 进入 GitHub 仓库
2. 点击 **Actions**
3. 选择 **Daily News Aggregation**
4. 点击 **Run workflow**

---

## 📊 查看运行日志

1. 进入 **Actions** 标签
2. 点击任意运行记录
3. 点击 **run-news-agent** 查看详细日志
4. 如果失败，会自动上传日志文件

---

## 🔧 故障排查

### 问题1：Secrets配置错误
**现象**：运行失败，显示API错误

**解决**：
1. 检查所有6个Secrets是否都已添加
2. 检查Secret名称是否完全匹配（区分大小写）
3. 检查Value是否正确复制（没有多余空格）

### 问题2：推送被拒绝
**现象**：`git push` 失败

**解决**：
```bash
# 确认远程仓库地址正确
git remote -v

# 如果地址错误，删除并重新添加
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### 问题3：邮件未收到
**现象**：GitHub Actions运行成功，但没收到邮件

**解决**：
1. 检查垃圾邮件文件夹
2. 确认 `EMAIL_RECEIVER` Secret配置正确
3. 查看Actions日志中的邮件发送状态

---

## 🎉 完成！

现在您的新闻聚合系统已经完全自动化了：
- ✅ 每天自动运行2次
- ✅ 自动发送邮件到您的邮箱
- ✅ 无需本地电脑开机
- ✅ 完全免费

享受您的自动化新闻服务！📧
