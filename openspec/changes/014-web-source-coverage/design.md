# 014 · Design — `WebSource` 实现细节

## 类设计

```python
# backend/app/ingestion/sources/web.py
from dataclasses import dataclass, field
from app.ingestion.base import Source, RawItem

@dataclass
class WebSource(Source):
    name: str
    listing_url: str
    link_pattern: str = r"^/(blog|news|post|p|article)/.+"  # relative or absolute
    max_items: int = 15
    js_render: bool = False           # 强制走 playwright
    article_min_chars: int = 300      # 正文低于此长度视为失败 → fallback playwright

    async def fetch(self) -> AsyncIterator[RawItem]:
        listing_html = await self._fetch_listing()
        article_urls = self._extract_article_urls(listing_html)
        for url in article_urls[:self.max_items]:
            article = await self._fetch_article(url)
            if article:
                yield article

    async def _fetch_listing(self) -> str: ...
    async def _fetch_article(self, url: str) -> RawItem | None: ...
    def _extract_article_urls(self, html: str) -> list[str]: ...
```

## listing → 链接抽取算法

1. 解析 HTML → 找所有 `<a href="...">`
2. 把 relative URL 拼到 listing_url 的 host
3. 用 `re.match(link_pattern, parsed.path)` 过滤
4. 去重 + 保持顺序

为什么用 regex 不用 CSS selector / BeautifulSoup:
- 24 个站结构各异,通用 selector 写不出
- regex 简单可调,后续 per-source 覆盖也方便

## article 抓取流程

```
def _fetch_article(url):
    if self.js_render:
        return _via_playwright(url)
    
    # HTTP path
    try:
        resp = await httpx.AsyncClient(...).get(url, timeout=10)
        if resp.status_code in (403, 429):
            return _via_playwright(url)   # 反爬可能 → playwright
        md = trafilatura.extract(resp.text, output_format="markdown")
        if md and len(md) >= self.article_min_chars:
            return RawItem(url=url, title=..., content_md=md, ...)
    except (httpx.TimeoutException, ConnectError):
        pass
    
    # Fallback
    return _via_playwright(url)
```

## 与 RSS 路径的关系

`base.py:Source` 是已有抽象。`WebSource` 是另一个实现,不复用 `RssSource`。两者通过 `IngestionService.create_item` 同一去重(`url_normalized` 唯一约束)。

## ingestion run 命令扩展

`backend/app/ingestion/run.py` 已有 `python -m app.ingestion.run <source|all>`,本 change 加:
- `python -m app.ingestion.run web` 跑全部 web 源
- `python -m app.ingestion.run web:anthropic-news` 跑单个(可选,推迟)

## scheduler job 加

`backend/app/scheduler/__main__.py` 加一个 cron job:
```python
sched.add_job(jobs.ingestion_web, CronTrigger.from_crontab("55 * * * *"),
              id="ingestion_web", replace_existing=True)
```

`jobs.py` 加 `ingestion_web` 函数,模仿现有 `ingestion_rss` 但跑 web 源。

## 配置示例

`config.yaml` 中 web 源条目改为:

```yaml
- name: "Anthropic News"
  url: "https://www.anthropic.com/news"
  type: "web"
  priority: "critical"
  max_items: 20
  link_pattern: "^/news/[a-z0-9-]+$"   # 新加可选字段

- name: "xAI News"
  url: "https://x.ai/news"
  type: "web"
  priority: "critical"
  js_render: true                       # 新加
  link_pattern: "^/news/[a-z0-9-]+$"
```

## 不引入新依赖

`trafilatura` / `playwright` / `httpx` 已经在 pyproject.toml 里。**只用现有 stack**,不加新包。

## 测试样本

`tests/test_web_source.py` 用本地 fixture HTML(从真实站点保存的快照):

```
tests/fixtures/web/
├── anthropic_news_listing.html
├── anthropic_news_article.html
├── claude_blog_listing.html
└── ...
```

测试覆盖:
1. `_extract_article_urls` 给定 fixture 返回正确数量 + 正确 URL
2. `link_pattern` 过滤掉无关链接(`/research/`, `/careers/`)
3. `_fetch_article` (用 mock httpx) 返回 `RawItem` 有 title + content_md > 300 字符
4. 一个 happy-path e2e:模拟 listing → 2 篇文章 → 2 个 RawItem
