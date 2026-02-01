"""
亚洲地区新闻Agent
负责搜集中国、日本、新加坡、台湾的新闻
"""

import logging
from typing import List, Dict
from ..collectors.news_collector import NewsCollector

logger = logging.getLogger(__name__)


class AsiaNewsAgent:
    """亚洲新闻Agent"""

    def __init__(self, config: Dict):
        self.config = config
        self.collector = NewsCollector()
        self.regions = config.get('regions', {}).get('asia', [])

    async def collect(self) -> Dict[str, List[Dict]]:
        """
        并行搜集亚洲各地区新闻

        Returns:
            按地区分组的新闻字典
        """
        logger.info("Asia Agent: Starting news collection...")

        results = {}

        for region in self.regions:
            region_name = region.get('name')
            region_code = region.get('code')
            language = region.get('language')
            keywords = region.get('keywords', [])
            max_items = region.get('max_items', 5)

            logger.info(f"Collecting news for {region_name}...")

            try:
                articles = self.collector.collect_google_news(
                    region_code=region_code,
                    language=language,
                    keywords=keywords,
                    max_items=max_items
                )

                # 添加地区标识
                for article in articles:
                    article['region_name'] = region_name

                results[region_name] = articles
                logger.info(f"Collected {len(articles)} articles from {region_name}")

            except Exception as e:
                logger.error(f"Error collecting news from {region_name}: {e}")
                results[region_name] = []

        total_articles = sum(len(articles) for articles in results.values())
        logger.info(f"Asia Agent: Collected {total_articles} total articles")

        return results

    def get_summary(self, results: Dict[str, List[Dict]]) -> str:
        """生成亚洲地区摘要"""
        summary = "## 🌏 亚洲地区新闻\n\n"

        for region_name, articles in results.items():
            if articles:
                summary += f"### {region_name} ({len(articles)}条)\n"
                for article in articles[:3]:  # 只显示前3条
                    summary += f"- {article.get('title', '')}\n"
                summary += "\n"

        return summary
