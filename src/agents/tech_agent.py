"""
AI Agent科技资讯Agent
负责搜集OpenAI、Anthropic、LangChain等AI Agent相关厂商的博客文章
支持时间窗口过滤、多源聚合
"""

import logging
import re
from typing import Any, Dict, List
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from ..collectors.news_collector import NewsCollector

logger = logging.getLogger(__name__)


class TechNewsAgent:
    """AI Agent科技资讯Agent"""

    def __init__(self, config: Dict):
        self.config = config
        self.collector = NewsCollector()
        self.tech_sources = config.get('tech_sources', {})
        self.time_window_days = self.tech_sources.get('time_window_days', 30)

    async def collect(self) -> Dict[str, List[Dict]]:
        """搜集AI科技文章（支持时间窗口）"""
        logger.info(f"Tech Agent: Collecting AI articles from last {self.time_window_days} days...")

        results = {
            'official_blogs': [],      # 官方博客
            'expert_blogs': [],        # 专家博客
            'aggregator_blogs': [],    # AI 新闻聚合源
            'research_papers': [],     # 研究论文
            'community': [],           # 社区讨论
        }

        # 每源统计（便于诊断'哪个源没抓到'）
        source_stats: List[Dict[str, Any]] = []

        # 计算时间窗口
        cutoff_date = datetime.now() - timedelta(days=self.time_window_days)

        # 1. 官方博客（优先级最高）
        for blog in self.tech_sources.get('official_blogs', []) or []:
            items = await self._collect_blog(blog, cutoff_date, 'official_blogs')
            results['official_blogs'].extend(items)
            source_stats.append({'name': blog.get('name'), 'category': 'official', 'count': len(items)})

        # 2. 专家博客
        for blog in self.tech_sources.get('expert_blogs', []) or []:
            items = await self._collect_blog(blog, cutoff_date, 'expert_blogs')
            results['expert_blogs'].extend(items)
            source_stats.append({'name': blog.get('name'), 'category': 'expert', 'count': len(items)})

        # 2.5 聚合源（The Batch / Import AI / AINews）
        for blog in self.tech_sources.get('aggregator_sources', []) or []:
            items = await self._collect_blog(blog, cutoff_date, 'aggregator_blogs')
            results['aggregator_blogs'].extend(items)
            source_stats.append({'name': blog.get('name'), 'category': 'aggregator', 'count': len(items)})

        # 3. 研究论文
        for source in self.tech_sources.get('research_sources', []) or []:
            items = await self._collect_research(source, cutoff_date)
            results['research_papers'].extend(items)
            source_stats.append({'name': source.get('name'), 'category': 'research', 'count': len(items)})

        # 4. 社区
        for source in self.tech_sources.get('community_sources', []) or []:
            items = await self._collect_community(source, cutoff_date)
            results['community'].extend(items)
            source_stats.append({'name': source.get('name'), 'category': 'community', 'count': len(items)})

        # 统计
        total = sum(len(v) for v in results.values())
        logger.info(f"Tech Agent: Collected {total} total articles")
        for category in ('official_blogs', 'expert_blogs', 'aggregator_blogs', 'research_papers', 'community'):
            logger.info(f"  - {category}: {len(results[category])}")

        # 打印每个源的采集条数（便于发现静默失败）
        empty_sources = [s['name'] for s in source_stats if s['count'] == 0]
        if empty_sources:
            logger.warning(f"Tech Agent: 以下源采集到 0 条，建议检查: {empty_sources}")

        return results

    async def _collect_blog(self, blog: Dict, cutoff_date: datetime, category: str) -> List[Dict]:
        """搜集单个博客 — 支持 fallback_urls 降级"""
        blog_name = blog.get('name')
        blog_type = blog.get('type')
        priority = blog.get('priority', 'medium')
        max_items = blog.get('max_items', 20)

        # 构造 URL 候选列表：主 URL 先试，失败再按序降级
        url_candidates: List[str] = []
        if blog.get('url'):
            url_candidates.append(blog['url'])
        url_candidates.extend(blog.get('fallback_urls', []) or [])

        for idx, url in enumerate(url_candidates):
            try:
                if blog_type == 'rss':
                    logger.info(f"Fetching {blog_name} RSS ({'primary' if idx == 0 else f'fallback #{idx}'}): {url}")
                    articles = self.collector.collect_rss_feed(url, max_items=max_items)
                    articles = self._filter_by_date(articles, cutoff_date)
                elif blog_type == 'web':
                    logger.info(f"Scraping {blog_name} ({'primary' if idx == 0 else f'fallback #{idx}'}): {url}")
                    articles = await self._scrape_web_blog(url, blog_name, max_items)
                else:
                    logger.warning(f"Unknown blog type '{blog_type}' for {blog_name}")
                    return []

                if articles:
                    for a in articles:
                        a['source_type'] = category
                        a['source'] = blog_name
                        a['priority'] = priority
                    logger.info(f"  → {blog_name}: {len(articles)} 条")
                    return articles
                else:
                    logger.info(f"  → {blog_name}: 0 条 (URL #{idx})，{'尝试下一个 URL' if idx < len(url_candidates) - 1 else '全部 URL 均为空'}")

            except Exception as e:
                logger.error(f"{blog_name} fetch failed at {url}: {e}")

        return []

    async def _scrape_web_blog(self, url: str, source_name: str, max_items: int = 20) -> List[Dict]:
        """抓取网页博客（用于没有RSS的网站，如Anthropic）"""
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.error(f"Failed to fetch {url}: {response.status_code}")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []

            # 专门处理Anthropic News页面
            if 'anthropic.com/news' in url:
                # 查找所有新闻链接
                links = soup.find_all('a', href=True)
                news_links = []

                for link in links:
                    href = link.get('href', '')
                    # Anthropic新闻链接格式：/news/article-slug
                    if href.startswith('/news/') and len(href) > 6:
                        full_url = f"https://www.anthropic.com{href}"
                        if full_url not in [a['link'] for a in articles]:
                            # 获取标题（通常在链接文本中）
                            title_raw = link.get_text(strip=True)

                            # 清理标题（移除日期和分类标签）
                            import re
                            # 移除日期（如 "Nov 24, 2025", "Jan 28, 2026"）
                            title = re.sub(r'[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}', '', title_raw)
                            # 移除分类标签（如 "Announcements", "Product"）
                            title = re.sub(r'^(Announcements|Product|Research|News|Press)\s*', '', title)
                            title = title.strip()

                            # 在数字后跟大写字母处添加空格（修复"4.5The"变成"4.5 The"）
                            title = re.sub(r'(\d)([A-Z])', r'\1 \2', title)

                            # 清理标题：只保留主标题部分
                            # "Introducing Claude Opus 4.5 The best model..." -> "Introducing Claude Opus 4.5"

                            if title.startswith('Introducing'):
                                # 提取"Introducing [产品名] [版本号]"
                                match = re.search(r'^(Introducing\s+[\w\s]+?[\d.]+)', title)
                                if match:
                                    title = match.group(1).strip()
                                else:
                                    # 如果没版本号，在第50个字符或第一个"The/A/An"前截断
                                    match = re.search(r'^(Introducing\s+[^.]+?)(?:\s+(?:The|A|An|for|with|to|in)\s+|$)', title)
                                    if match:
                                        title = match.group(1).strip()

                            # 通用清理：限制最大长度80字符
                            if len(title) > 80:
                                title = title[:80]
                                last_space = title.rfind(' ')
                                if last_space > 40:
                                    title = title[:last_space] + '...'

                            if title and len(title) > 15:  # 过滤掉太短的
                                articles.append({
                                    'title': title,
                                    'link': full_url,
                                    'source': source_name,
                                    'published': '',  # 网页抓取通常没有日期
                                    'summary': ''
                                })

                                if len(articles) >= max_items:
                                    break

            # 处理Claude Blog页面
            elif 'claude.com/blog' in url or 'claude.ai/blog' in url:
                # 查找所有博客链接
                links = soup.find_all('a', href=True)

                for link in links:
                    href = link.get('href', '')
                    # Claude博客链接格式：/blog/article-slug
                    if href.startswith('/blog/') and len(href) > 6 and href != '/blog':
                        full_url = f"https://claude.com{href}"
                        if full_url not in [a['link'] for a in articles]:
                            # 获取标题
                            title_raw = link.get_text(strip=True)

                            # 清理标题
                            import re
                            # 移除日期
                            title = re.sub(r'[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}', '', title_raw)
                            title = title.strip()

                            # 在数字后跟大写字母处添加空格
                            title = re.sub(r'(\d)([A-Z])', r'\1 \2', title)

                            # 限制标题长度
                            if len(title) > 80:
                                title = title[:80]
                                last_space = title.rfind(' ')
                                if last_space > 40:
                                    title = title[:last_space] + '...'

                            if title and len(title) > 15:  # 过滤掉太短的
                                articles.append({
                                    'title': title,
                                    'link': full_url,
                                    'source': source_name,
                                    'published': '',
                                    'summary': ''
                                })

                                if len(articles) >= max_items:
                                    break

            # 通用抓取：对未显式适配的官方博客做链接提取
            else:
                articles = self._extract_generic_blog_links(
                    soup=soup, base_url=url, source_name=source_name, max_items=max_items
                )

            logger.info(f"Scraped {len(articles)} articles from {source_name}")
            return articles[:max_items]

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []

    def _extract_generic_blog_links(
        self,
        soup: Any,
        base_url: str,
        source_name: str,
        max_items: int,
    ) -> List[Dict]:
        """
        通用博客链接提取：适用于 Meta AI / xAI / Mistral / Cohere / Perplexity 等未显式适配的官方博客。

        策略：
          1. 只保留与 base_url 同域的链接
          2. 路径包含 /blog/ /news/ /post/ /article/ /hub/ 任一即视为博文
          3. 用链接文本作为标题，过滤太短（< 15 字）和导航词
          4. 按出现顺序保留前 max_items 条，去重
        """
        parsed_base = urlparse(base_url)
        base_host = parsed_base.netloc.replace('www.', '')

        blog_patterns = re.compile(
            r'/(blog|news|post|posts|article|articles|hub|research|announcement|announcements)/',
            re.IGNORECASE,
        )
        nav_words = {
            'blog', 'news', 'home', 'next', 'previous', 'more', 'read more',
            'view all', 'see all', 'about', 'contact', 'careers', 'pricing',
            'products', 'product', 'docs', 'documentation', 'sign in', 'sign up',
        }

        seen_urls = set()
        articles: List[Dict] = []

        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            if not href or href.startswith('#') or href.startswith('mailto:'):
                continue

            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            host = parsed.netloc.replace('www.', '')
            if base_host and base_host not in host:
                continue

            if not blog_patterns.search(parsed.path or ''):
                continue

            # 排除 index / 列表页本身
            if parsed.path.rstrip('/').endswith(('/blog', '/news', '/posts', '/hub')):
                continue

            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # 标题提取
            title = link.get_text(strip=True)
            # 子元素可能有更丰富的标题（<h2>, <h3>）
            heading = link.find(['h1', 'h2', 'h3', 'h4'])
            if heading:
                h_text = heading.get_text(strip=True)
                if h_text and len(h_text) > len(title):
                    title = h_text

            # 清理：移除前后日期，去多余空格
            title = re.sub(r'[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}', '', title).strip()
            title = re.sub(r'\s+', ' ', title)

            if len(title) < 15:
                continue
            if title.lower() in nav_words:
                continue

            articles.append({
                'title': title[:120],
                'link': full_url,
                'source': source_name,
                'published': '',
                'summary': '',
            })

            if len(articles) >= max_items:
                break

        return articles

    async def _collect_research(self, source: Dict, cutoff_date: datetime) -> List[Dict]:
        """搜集研究论文"""
        source_name = source.get('name')
        source_url = source.get('url')
        max_items = source.get('max_items', 5)

        try:
            if 'arxiv' in source_url.lower():
                logger.info(f"Fetching {source_name}...")
                articles = self.collector.collect_rss_feed(source_url, max_items=max_items)

                for article in articles:
                    article['source_type'] = 'research'
                    article['source'] = source_name

                logger.info(f"Collected {len(articles)} papers from {source_name}")
                return articles

        except Exception as e:
            logger.error(f"Error collecting research from {source_name}: {e}")

        return []

    async def _collect_community(self, source: Dict, cutoff_date: datetime) -> List[Dict]:
        """搜集社区内容"""
        source_name = source.get('name')
        source_type = source.get('type')

        try:
            if source_type == 'rss':
                source_url = source.get('url')
                logger.info(f"Fetching {source_name}...")
                articles = self.collector.collect_rss_feed(source_url, max_items=10)

                for article in articles:
                    article['source_type'] = 'community'
                    article['source'] = source_name

                logger.info(f"Collected {len(articles)} posts from {source_name}")
                return articles

        except Exception as e:
            logger.error(f"Error collecting from {source_name}: {e}")

        return []

    def _filter_by_date(self, articles: List[Dict], cutoff_date: datetime) -> List[Dict]:
        """根据发布时间过滤文章"""
        filtered = []

        for article in articles:
            published = article.get('published', '')

            if not published:
                # 如果没有日期，保留（可能是最新的）
                filtered.append(article)
                continue

            try:
                # 尝试解析日期
                from dateutil import parser
                pub_date = parser.parse(published)

                # 移除时区信息以便比较
                if pub_date.tzinfo:
                    pub_date = pub_date.replace(tzinfo=None)

                if pub_date >= cutoff_date:
                    filtered.append(article)

            except Exception as e:
                # 解析失败，保留
                filtered.append(article)

        return filtered
