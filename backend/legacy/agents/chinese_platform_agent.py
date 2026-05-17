"""
中文平台Agent
搜集掘金、知乎、CSDN上的AI Agent相关文章
使用搜索API作为主要数据源，避免反爬问题
"""

import asyncio
import logging
from typing import List, Dict
from ..collectors.search_api_collector import SearchAPICollector

logger = logging.getLogger(__name__)


class ChinesePlatformAgent:
    """中文平台AI Agent内容搜集"""

    def __init__(self, config: Dict):
        self.config = config
        self.platform_config = config.get('chinese_platforms', {})
        self.search_config = config.get('search_apis', {})
        self.collector = SearchAPICollector(self.search_config)

    async def collect(self) -> Dict[str, List[Dict]]:
        """搜集中文平台AI Agent内容"""
        logger.info("ChinesePlatformAgent: Starting Chinese platform collection...")

        if not self.platform_config.get('enabled', True):
            logger.info("ChinesePlatformAgent: Disabled in config")
            return {}

        # 检查搜索API可用性
        if not self.collector.tavily_client and not self.collector.exa_client:
            logger.warning("ChinesePlatformAgent: No search API available")
            return {}

        platforms = self.platform_config.get('platforms', [])
        results = {}

        # 并行搜集各平台
        tasks = []
        for platform in platforms:
            name = platform.get('name', '')
            tasks.append((name, self._collect_platform(platform)))

        task_results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        for (name, _), result in zip(tasks, task_results):
            if isinstance(result, Exception):
                logger.error(f"Error collecting from {name}: {result}")
                results[name] = []
            else:
                results[name] = result

        # 统计
        total = sum(len(v) for v in results.values())
        logger.info(f"ChinesePlatformAgent: Collected {total} total articles")
        for name, articles in results.items():
            if articles:
                logger.info(f"  - {name}: {len(articles)}")

        return results

    async def _collect_platform(self, platform: Dict) -> List[Dict]:
        """搜集单个平台的内容"""
        name = platform.get('name', '')
        domain = platform.get('domain', '')
        keywords = platform.get('keywords', ['AI Agent'])
        max_items = platform.get('max_items', 8)

        all_results = []

        for keyword in keywords:
            # 使用搜索API限定域名搜索
            query = f"site:{domain} {keyword}"
            try:
                results = self.collector.search_all(
                    query=query,
                    max_per_api=3,
                    days=14,
                    include_domains=[domain],
                )
                for r in results:
                    r['source_type'] = 'chinese_platform'
                    r['source'] = name
                    r['category_label'] = f'{name} AI Agent'
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error searching {name} for '{keyword}': {e}")

        # 去重
        return self._deduplicate(all_results)[:max_items]

    def _deduplicate(self, articles: List[Dict]) -> List[Dict]:
        """按URL去重"""
        seen = set()
        unique = []
        for article in articles:
            url = article.get('link', '').rstrip('/').lower()
            if url and url not in seen:
                seen.add(url)
                unique.append(article)
        return unique
