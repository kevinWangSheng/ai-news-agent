"""
AI实践内容Agent
使用Tavily + Exa搜索API主动发现AI实践类文章、教程、Twitter讨论等
"""

import asyncio
import logging
from typing import List, Dict
from datetime import datetime, timedelta
from ..collectors.search_api_collector import SearchAPICollector

logger = logging.getLogger(__name__)


class AIContentAgent:
    """AI实践内容搜索Agent"""

    def __init__(self, config: Dict):
        self.config = config
        self.search_config = config.get('search_apis', {})
        self.content_config = config.get('ai_content_searches', {})
        self.collector = SearchAPICollector(self.search_config)

    async def collect(self) -> Dict[str, List[Dict]]:
        """搜集所有AI实践类内容"""
        logger.info("AIContentAgent: Starting AI content collection via search APIs...")

        # 检查是否有可用的搜索API
        if not self.collector.tavily_client and not self.collector.exa_client:
            logger.warning("AIContentAgent: No search API available (missing TAVILY_API_KEY and EXA_API_KEY)")
            return {}

        results = {
            'practical_tutorials': [],
            'ai_twitter': [],
            'claude_anthropic': [],
            'openai_practical': [],
            'ai_engineering': [],
        }

        # 并行执行所有搜索类别
        tasks = [
            ('practical_tutorials', self._search_practical_tutorials()),
            ('ai_twitter', self._search_twitter_ai()),
            ('claude_anthropic', self._search_claude_content()),
            ('openai_practical', self._search_openai_content()),
            ('ai_engineering', self._search_ai_engineering()),
        ]

        task_results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        for (key, _), result in zip(tasks, task_results):
            if isinstance(result, Exception):
                logger.error(f"Error in {key} search: {result}")
            else:
                results[key] = result

        # 跨分类去重（按优先级保留：claude > openai > engineering > tutorials > twitter）
        seen_urls = set()
        priority_order = ['claude_anthropic', 'openai_practical', 'ai_engineering', 'practical_tutorials', 'ai_twitter']
        for key in priority_order:
            if key in results:
                unique = []
                for article in results[key]:
                    url = article.get('link', '').rstrip('/').lower()
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        unique.append(article)
                results[key] = unique

        # 统计
        total = sum(len(v) for v in results.values())
        logger.info(f"AIContentAgent: Collected {total} total articles")
        for key, articles in results.items():
            if articles:
                logger.info(f"  - {key}: {len(articles)}")

        return results

    async def _search_practical_tutorials(self) -> List[Dict]:
        """搜索AI实践教程"""
        category_config = self.content_config.get('practical_tutorials', {})
        queries = category_config.get('queries', [
            "AI tutorial hands-on implementation guide 2025 2026",
            "LLM application development tutorial practical",
            "machine learning practical project walkthrough",
        ])
        max_items = category_config.get('max_items', 10)
        days = category_config.get('days', 14)

        all_results = []
        for query in queries:
            results = self.collector.search_all(
                query=query,
                max_per_api=5,
                days=days,
            )
            for r in results:
                r['source_type'] = 'practical_tutorials'
                r['category_label'] = 'AI实践教程'
            all_results.extend(results)

        return self._deduplicate(all_results)[:max_items]

    async def _search_twitter_ai(self) -> List[Dict]:
        """搜索Twitter/X上的AI热门内容（仅用Exa）"""
        category_config = self.content_config.get('ai_twitter', {})
        queries = category_config.get('queries', [
            "AI breakthrough LLM new model release",
            "Claude Anthropic OpenAI new feature announcement",
            "AI agent framework tool open source",
        ])
        max_items = category_config.get('max_items', 8)
        days = category_config.get('days', 7)

        all_results = []
        for query in queries:
            results = self.collector.search_all(
                query=query,
                max_per_api=5,
                category="tweet",
                days=days,
                exa_only=True,
            )
            for r in results:
                r['source_type'] = 'ai_twitter'
                r['category_label'] = 'AI Twitter热议'
            all_results.extend(results)

        return self._deduplicate(all_results)[:max_items]

    async def _search_claude_content(self) -> List[Dict]:
        """搜索Claude/Anthropic实践内容"""
        category_config = self.content_config.get('claude_anthropic', {})
        queries = category_config.get('queries', [
            "Claude API tutorial anthropic best practices guide",
            "Claude Code skills MCP server development guide",
            "Anthropic Claude model practical usage tips",
            "Claude prompt engineering techniques examples",
        ])
        max_items = category_config.get('max_items', 8)
        days = category_config.get('days', 30)

        all_results = []
        for query in queries:
            results = self.collector.search_all(
                query=query,
                max_per_api=5,
                days=days,
            )
            for r in results:
                r['source_type'] = 'claude_anthropic'
                r['category_label'] = 'Claude/Anthropic实践'
            all_results.extend(results)

        return self._deduplicate(all_results)[:max_items]

    async def _search_openai_content(self) -> List[Dict]:
        """搜索OpenAI实践内容"""
        category_config = self.content_config.get('openai_practical', {})
        queries = category_config.get('queries', [
            "OpenAI API tutorial GPT practical guide",
            "ChatGPT custom GPT development building",
            "OpenAI function calling assistants API tutorial",
            "GPT-4 practical use cases implementation",
        ])
        max_items = category_config.get('max_items', 8)
        days = category_config.get('days', 30)

        all_results = []
        for query in queries:
            results = self.collector.search_all(
                query=query,
                max_per_api=5,
                days=days,
            )
            for r in results:
                r['source_type'] = 'openai_practical'
                r['category_label'] = 'OpenAI实践'
            all_results.extend(results)

        return self._deduplicate(all_results)[:max_items]

    async def _search_ai_engineering(self) -> List[Dict]:
        """搜索AI工程实践"""
        category_config = self.content_config.get('ai_engineering', {})
        queries = category_config.get('queries', [
            "AI agent building framework LangChain CrewAI tutorial",
            "RAG retrieval augmented generation implementation guide",
            "LLM deployment production optimization best practices",
            "prompt engineering advanced techniques examples",
            "AI coding assistant development workflow",
        ])
        max_items = category_config.get('max_items', 10)
        days = category_config.get('days', 14)

        all_results = []
        for query in queries:
            results = self.collector.search_all(
                query=query,
                max_per_api=5,
                days=days,
            )
            for r in results:
                r['source_type'] = 'ai_engineering'
                r['category_label'] = 'AI工程实践'
            all_results.extend(results)

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
