"""
GitHub项目Agent
负责搜集GitHub上的热门和有趣项目
支持：trending、topic 搜索、star 增速排名、新项目发现
"""

import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from ..collectors.news_collector import NewsCollector

logger = logging.getLogger(__name__)


class GitHubAgent:
    """GitHub项目Agent"""

    def __init__(self, config: Dict):
        self.config = config
        self.collector = NewsCollector()
        self.github_config = config.get('github', {})
        self.github_token = os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')

    async def collect(self) -> Dict[str, List[Dict]]:
        """搜集GitHub热门项目"""
        logger.info("GitHub Agent: Starting project collection...")

        results = {
            'trending': [],
            'ai_projects': [],
            'rising_stars': [],
            'new_projects': [],
        }

        # 1. 获取Trending项目
        trending_config = self.github_config.get('trending', {})
        languages = trending_config.get('languages', ['python'])
        since = trending_config.get('since', 'daily')

        for language in languages:
            try:
                logger.info(f"Fetching {language} trending projects...")
                projects = self.collector.collect_github_trending(
                    language=language,
                    since=since
                )
                results['trending'].extend(projects)
            except Exception as e:
                logger.error(f"Error fetching trending for {language}: {e}")

        # 2. 搜索AI相关项目（按 topic）
        topics = self.github_config.get('topics', [])
        max_topic_searches = self.github_config.get('max_topic_searches', 4)
        for topic in topics[:max_topic_searches]:
            try:
                logger.info(f"Searching projects for topic: {topic}")
                projects = self.collector.search_github_repos(
                    query=topic,
                    token=self.github_token,
                    max_items=5
                )
                results['ai_projects'].extend(projects)
            except Exception as e:
                logger.error(f"Error searching topic {topic}: {e}")

        # 3. Star 增速最快的 AI Agent 项目（最近7天创建/更新，按 stars 排序）
        try:
            logger.info("Searching rising star AI Agent projects...")
            rising = self._search_rising_stars()
            results['rising_stars'] = rising
        except Exception as e:
            logger.error(f"Error searching rising stars: {e}")

        # 4. 新项目发现（最近14天内创建的高潜力项目）
        try:
            logger.info("Searching newly created AI Agent projects...")
            new_projects = self._search_new_projects()
            results['new_projects'] = new_projects
        except Exception as e:
            logger.error(f"Error searching new projects: {e}")

        # 全局去重
        seen_urls = set()
        for key in ['trending', 'rising_stars', 'new_projects', 'ai_projects']:
            unique = []
            for project in results.get(key, []):
                url = project.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique.append(project)
            results[key] = unique[:10]

        total = sum(len(v) for v in results.values())
        logger.info(f"GitHub Agent: Collected {total} unique projects")

        return results

    def _search_rising_stars(self) -> List[Dict]:
        """搜索 star 增速最快的 AI Agent 相关项目"""
        rising_config = self.github_config.get('rising_stars', {})
        days = rising_config.get('days', 7)
        min_stars = rising_config.get('min_stars', 50)
        max_items = rising_config.get('max_items', 10)

        queries = rising_config.get('queries', [
            "ai agent",
            "mcp server",
            "llm tool",
            "multi-agent",
        ])

        all_projects = []
        date_threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        for query in queries:
            try:
                search_query = f"{query} stars:>{min_stars} pushed:>{date_threshold}"
                projects = self._search_github_api(
                    query=search_query,
                    sort="stars",
                    order="desc",
                    max_items=5
                )
                for p in projects:
                    p['discovery_type'] = 'rising_star'
                all_projects.extend(projects)
            except Exception as e:
                logger.error(f"Error in rising stars query '{query}': {e}")

        # 按 stars 排序
        all_projects.sort(key=lambda x: x.get('stars', 0), reverse=True)
        return self._deduplicate(all_projects)[:max_items]

    def _search_new_projects(self) -> List[Dict]:
        """搜索最近新创建的高潜力 AI Agent 项目"""
        new_config = self.github_config.get('new_projects', {})
        days = new_config.get('days', 14)
        min_stars = new_config.get('min_stars', 10)
        max_items = new_config.get('max_items', 8)

        queries = new_config.get('queries', [
            "ai agent framework",
            "mcp server tool",
            "llm agent",
            "agentic workflow",
        ])

        all_projects = []
        date_threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        for query in queries:
            try:
                search_query = f"{query} stars:>{min_stars} created:>{date_threshold}"
                projects = self._search_github_api(
                    query=search_query,
                    sort="stars",
                    order="desc",
                    max_items=5
                )
                for p in projects:
                    p['discovery_type'] = 'new_project'
                all_projects.extend(projects)
            except Exception as e:
                logger.error(f"Error in new projects query '{query}': {e}")

        all_projects.sort(key=lambda x: x.get('stars', 0), reverse=True)
        return self._deduplicate(all_projects)[:max_items]

    def _search_github_api(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        max_items: int = 10
    ) -> List[Dict]:
        """调用 GitHub Search API（无 token 也可用，有限额）"""
        import requests
        import time

        headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.github_token:
            headers['Authorization'] = f'Bearer {self.github_token}'

        url = "https://api.github.com/search/repositories"
        params = {
            'q': query,
            'sort': sort,
            'order': order,
            'per_page': max_items
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
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
                        'updated_at': repo['updated_at'],
                        'created_at': repo.get('created_at', ''),
                    }
                    results.append(project)
                return results
            elif response.status_code == 401 or response.status_code == 403:
                if self.github_token:
                    logger.warning(f"GitHub token may be expired (HTTP {response.status_code}), retrying without token...")
                    headers_no_token = {'Accept': 'application/vnd.github.v3+json'}
                    time.sleep(1)
                    response2 = requests.get(url, params=params, headers=headers_no_token, timeout=15)
                    if response2.status_code == 200:
                        data = response2.json()
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
                                'updated_at': repo['updated_at'],
                                'created_at': repo.get('created_at', ''),
                            }
                            results.append(project)
                        return results
                    logger.error(f"GitHub API error without token: {response2.status_code}")
                else:
                    logger.error(f"GitHub API error: {response.status_code} - rate limited or auth issue")
            else:
                logger.error(f"GitHub API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Error calling GitHub API: {e}")

        return []

    @staticmethod
    def _deduplicate(projects: List[Dict]) -> List[Dict]:
        """按 URL 去重"""
        seen = set()
        unique = []
        for p in projects:
            url = p.get('url', '').rstrip('/').lower()
            if url and url not in seen:
                seen.add(url)
                unique.append(p)
        return unique
