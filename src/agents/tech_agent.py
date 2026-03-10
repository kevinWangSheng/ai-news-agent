"""
AI Agent科技资讯Agent
负责搜集OpenAI、Anthropic、LangChain等AI Agent相关厂商的博客文章
支持时间窗口过滤、多源聚合
"""

import logging
from typing import List, Dict
from datetime import datetime, timedelta
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
            'research_papers': [],     # 研究论文
            'community': [],           # 社区讨论
        }

        # 计算时间窗口
        cutoff_date = datetime.now() - timedelta(days=self.time_window_days)

        # 1. 搜集官方博客（优先级最高）
        official_blogs = self.tech_sources.get('official_blogs', [])
        for blog in official_blogs:
            articles = await self._collect_blog(blog, cutoff_date, 'official_blogs')
            results['official_blogs'].extend(articles)

        # 2. 搜集专家博客
        expert_blogs = self.tech_sources.get('expert_blogs', [])
        for blog in expert_blogs:
            articles = await self._collect_blog(blog, cutoff_date, 'expert_blogs')
            results['expert_blogs'].extend(articles)

        # 3. 搜集AI研究论文
        research_sources = self.tech_sources.get('research_sources', [])
        for source in research_sources:
            articles = await self._collect_research(source, cutoff_date)
            results['research_papers'].extend(articles)

        # 4. 搜集社区热门讨论
        community_sources = self.tech_sources.get('community_sources', [])
        for source in community_sources:
            articles = await self._collect_community(source, cutoff_date)
            results['community'].extend(articles)

        # 统计
        total = sum(len(articles) for articles in results.values())
        logger.info(f"Tech Agent: Collected {total} total articles")
        logger.info(f"  - Official blogs: {len(results['official_blogs'])}")
        logger.info(f"  - Expert blogs: {len(results['expert_blogs'])}")
        logger.info(f"  - Research papers: {len(results['research_papers'])}")
        logger.info(f"  - Community: {len(results['community'])}")

        return results

    async def _collect_blog(self, blog: Dict, cutoff_date: datetime, category: str) -> List[Dict]:
        """搜集单个博客"""
        blog_name = blog.get('name')
        blog_url = blog.get('url')
        blog_type = blog.get('type')
        priority = blog.get('priority', 'medium')
        max_items = blog.get('max_items', 20)

        try:
            if blog_type == 'rss':
                logger.info(f"Fetching {blog_name} RSS...")
                articles = self.collector.collect_rss_feed(blog_url, max_items=max_items)

                # 过滤时间
                filtered = self._filter_by_date(articles, cutoff_date)

                for article in filtered:
                    article['source_type'] = category
                    article['source'] = blog_name
                    article['priority'] = priority

                logger.info(f"Collected {len(filtered)} articles from {blog_name} (from last {self.time_window_days} days)")
                return filtered

            elif blog_type == 'web':
                # 网页抓取（适用于Anthropic等）
                logger.info(f"Scraping {blog_name} website...")
                articles = await self._scrape_web_blog(blog_url, blog_name, max_items)

                for article in articles:
                    article['source_type'] = category
                    article['source'] = blog_name
                    article['priority'] = priority

                logger.info(f"Collected {len(articles)} articles from {blog_name}")
                logger.info(f"  Category: {category}, Priority: {priority}")
                if articles:
                    logger.info(f"  First article: {articles[0].get('title', '')[:50]}")
                    logger.info(f"  Source type: {articles[0].get('source_type')}")
                return articles

        except Exception as e:
            logger.error(f"Error collecting from {blog_name}: {e}")

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
            elif 'claude.com/blog' in url:
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

            logger.info(f"Scraped {len(articles)} articles from {source_name}")
            return articles[:max_items]

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []

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
