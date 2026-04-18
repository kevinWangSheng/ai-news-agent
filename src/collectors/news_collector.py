"""
新闻搜集工具
支持多种来源：Google News RSS, Bing News, RSS订阅等
"""

import feedparser
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class NewsCollector:
    """新闻搜集器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def collect_google_news(
        self,
        region_code: str,
        language: str,
        keywords: List[str],
        max_items: int = 10
    ) -> List[Dict]:
        """
        从Google News RSS获取新闻

        Args:
            region_code: 地区代码 (CN, US, JP等)
            language: 语言代码 (zh-CN, en, ja等)
            keywords: 关键词列表
            max_items: 最大条目数
        """
        results = []

        for keyword in keywords:
            try:
                # Google News RSS URL
                url = f"https://news.google.com/rss/search?q={keyword}&hl={language}&gl={region_code}&ceid={region_code}:{language}"

                logger.info(f"Fetching news for keyword: {keyword} in {region_code}")

                feed = feedparser.parse(url)

                for entry in feed.entries[:max_items]:
                    article = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'source': entry.get('source', {}).get('title', 'Google News'),
                        'summary': entry.get('summary', ''),
                        'keyword': keyword,
                        'region': region_code
                    }
                    results.append(article)

            except Exception as e:
                logger.error(f"Error fetching news for {keyword}: {e}")
                continue

        return results[:max_items]

    def collect_rss_feed(self, feed_url: str, max_items: int = 10) -> List[Dict]:
        """
        从RSS源获取内容

        Args:
            feed_url: RSS订阅地址
            max_items: 最大条目数
        """
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")
            feed = feedparser.parse(feed_url)

            results = []
            for entry in feed.entries[:max_items]:
                article = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', entry.get('description', '')),
                    'source': feed.feed.get('title', 'RSS Feed')
                }
                results.append(article)

            return results

        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return []

    def collect_github_trending(
        self,
        language: Optional[str] = None,
        since: str = "daily"
    ) -> List[Dict]:
        """
        获取GitHub Trending项目
        使用 GitHub Search API 按 star 增长排序模拟 trending

        Args:
            language: 编程语言 (python, typescript等)
            since: 时间范围 (daily, weekly, monthly)
        """
        try:
            from datetime import datetime, timedelta

            since_days = {"daily": 1, "weekly": 7, "monthly": 30}.get(since, 1)
            date_threshold = (datetime.now() - timedelta(days=since_days)).strftime('%Y-%m-%d')

            lang_query = f"language:{language}" if language else ""
            search_query = f"stars:>50 pushed:>{date_threshold} {lang_query}".strip()

            url = "https://api.github.com/search/repositories"
            params = {
                'q': search_query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': 10
            }

            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                results = []

                for repo in data.get('items', []):
                    project = {
                        'name': repo.get('name', ''),
                        'author': repo.get('owner', {}).get('login', ''),
                        'url': repo.get('html_url', ''),
                        'description': repo.get('description', ''),
                        'language': repo.get('language', ''),
                        'stars': repo.get('stargazers_count', 0),
                        'forks': repo.get('forks_count', 0),
                        'stars_today': 0,
                    }
                    results.append(project)

                return results
            else:
                logger.error(f"GitHub trending search failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Error fetching GitHub trending: {e}")

        return []

    def search_github_repos(
        self,
        query: str,
        token: Optional[str] = None,
        max_items: int = 10
    ) -> List[Dict]:
        """
        搜索GitHub仓库

        Args:
            query: 搜索关键词
            token: GitHub Token (可选，提高限额)
            max_items: 最大结果数
        """
        try:
            headers = {'Accept': 'application/vnd.github.v3+json'}
            if token:
                headers['Authorization'] = f'Bearer {token}'

            url = "https://api.github.com/search/repositories"

            # 搜索最近更新的高星项目
            params = {
                'q': f'{query} stars:>100',
                'sort': 'updated',
                'order': 'desc',
                'per_page': max_items
            }

            response = self.session.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = []

                for repo in data.get('items', []):
                    project = {
                        'name': repo['name'],
                        'author': repo['owner']['login'],
                        'url': repo['html_url'],
                        'description': repo.get('description', ''),
                        'language': repo.get('language', ''),
                        'stars': repo['stargazers_count'],
                        'forks': repo['forks_count'],
                        'updated_at': repo['updated_at']
                    }
                    results.append(project)

                return results

        except Exception as e:
            logger.error(f"Error searching GitHub repos: {e}")

        return []
