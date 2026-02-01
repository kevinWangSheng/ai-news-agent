"""
其他地区新闻Agent
包括澳大利亚、俄罗斯等
"""

import logging
from typing import List, Dict
from ..collectors.news_collector import NewsCollector

logger = logging.getLogger(__name__)


class OthersNewsAgent:
    """其他地区新闻Agent"""

    def __init__(self, config: Dict):
        self.config = config
        self.collector = NewsCollector()
        self.regions = config.get('regions', {}).get('others', [])

    async def collect(self) -> Dict[str, List[Dict]]:
        """搜集其他地区新闻"""
        logger.info("Others Agent: Starting news collection...")

        results = {}

        for region in self.regions:
            region_name = region.get('name')
            region_code = region.get('code')
            language = region.get('language')
            keywords = region.get('keywords', [])
            max_items = region.get('max_items', 5)

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
