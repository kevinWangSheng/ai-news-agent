# 安装 bookmarklet — 一键投喂任意网页

## 步骤

1. 启动本机服务:`cd docker && docker compose up -d`(backend 监听 8000)
2. 浏览器打开 `http://localhost:3000/bookmarklet/install.html`(开发态);或 frontend 部署后等价路径
3. **把页面里的 「📥 投喂到 hub」按钮拖到书签栏**
4. 在任意网页点击书签栏的「📥 投喂到 hub」,即可把当前页 URL + 标题 + 选中文字写入 inbox

## 验证

- 点击 bookmarklet → 浏览器弹窗 `已投喂 #123`
- `hub list --inbox` 或 `http://localhost:3000/inbox` 能看到刚投的条目

## Mixed-content 问题

在 https 页面调 `http://localhost:8000` 会被浏览器拦截,处理选项:

- **(简单)** Chrome 站点设置 → 不安全内容 → 允许 `localhost`
- **(干净)** 给 backend 配自签证书,bookmarklet 改 `https://localhost:8000`
- **(开发态)** Chrome 启动加 `--allow-running-insecure-content`

## 改 API 地址

bookmarklet 里写死了 `http://localhost:8000`。如果你的 backend 在另一台机器:

```js
window.HUB_API = 'http://10.0.0.5:8000';
```

在浏览器控制台执行一次,bookmarklet 会读 `window.HUB_API`。
