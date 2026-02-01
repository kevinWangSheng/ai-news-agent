"""
GitHub项目Agent
负责搜集GitHub上的热门和有趣项目
"""

import logging
import os
from typing import List, Dict
from ..collectors.news_collector import NewsCollector

logger = logging.getLogger(__name__)


class GitHubAgent:
    """GitHub项目Agent"""

    def __init__(self, config: Dict):
        self.config = config
        self.collector = NewsCollector()
        self.github_config = config.get('github', {})
        self.github_token = os.getenv('GITHUB_TOKEN')

    async def collect(self) -> Dict[str, List[Dict]]:
        """搜集GitHub热门项目"""
        logger.info("GitHub Agent: Starting project collection...")

        results = {
            'trending': [],
            'ai_projects': []
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

        # 2. 搜索AI相关项目
        topics = self.github_config.get('topics', [])

        for topic in topics[:2]:  # 限制主题数量
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

        # 去重
        seen_urls = set()
        unique_trending = []
        for project in results['trending']:
            url = project.get('url')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_trending.append(project)

        unique_ai = []
        for project in results['ai_projects']:
            url = project.get('url')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_ai.append(project)

        results['trending'] = unique_trending[:10]
        results['ai_projects'] = unique_ai[:10]

        total = len(results['trending']) + len(results['ai_projects'])
        logger.info(f"GitHub Agent: Collected {total} unique projects")

        return results
