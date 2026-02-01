"""
美洲地区新闻Agent
主要负责美国新闻
"""

import logging
from typing import List, Dict
from ..collectors.news_collector import NewsCollector

logger = logging.getLogger(__name__)


class AmericasNewsAgent:
    """美洲新闻Agent"""

    def __init__(self, config: Dict):
        self.config = config
        self.collector = NewsCollector()
        self.regions = config.get('regions', {}).get('americas', [])

    async def collect(self) -> Dict[str, List[Dict]]:
        """搜集美洲地区新闻"""
        logger.info("Americas Agent: Starting news collection...")

        results = {}

        for region in self.regions:
            region_name = region.get('name')
            region_code = region.get('code')
            language = region.get('language')
            keywords = region.get('keywords', [])
            max_items = region.get('max_items', 10)

            logger.info(f"Collecting news for {region_name}...")

            try:
                articles = self.collector.collect_google_news(
                    region_code=region_code,
                    language=language,
                    keywords=keywords,
                    max_items=max_items
                )

                for article in articles:
                    article['region_name'] = region_name

                results[region_name] = articles
                logger.info(f"Collected {len(articles)} articles from {region_name}")

            except Exception as e:
                logger.error(f"Error collecting news from {region_name}: {e}")
                results[region_name] = []

        return results
