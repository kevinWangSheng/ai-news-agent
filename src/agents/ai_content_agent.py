"""
AI Agent内容搜索Agent
使用Tavily + Exa搜索API主动发现AI Agent相关文章、教程、Twitter讨论等
"""

import asyncio
import logging
from typing import List, Dict
from ..collectors.search_api_collector import SearchAPICollector

logger = logging.getLogger(__name__)


class AIContentAgent:
    """AI Agent内容搜索Agent"""

    def __init__(self, config: Dict):
        self.config = config
        self.search_config = config.get('search_apis', {})
        self.content_config = config.get('ai_content_searches', {})
        self.collector = SearchAPICollector(self.search_config)

    async def collect(self) -> Dict[str, List[Dict]]:
        """搜集所有AI Agent实践类内容"""
        logger.info("AIContentAgent: Starting AI Agent content collection via search APIs...")

        # 检查是否有可用的搜索API
        if not self.collector.tavily_client and not self.collector.exa_client:
            logger.warning("AIContentAgent: No search API available (missing TAVILY_API_KEY and EXA_API_KEY)")
            return {}

        results = {
            'agent_frameworks': [],
            'agent_protocols': [],
            'agentic_workflows': [],
            'agent_twitter': [],
            'agent_chinese': [],
        }

        # 并行执行所有搜索类别
        tasks = [
            ('agent_frameworks', self._search_agent_frameworks()),
            ('agent_protocols', self._search_agent_protocols()),
            ('agentic_workflows', self._search_agentic_workflows()),
            ('agent_twitter', self._search_agent_twitter()),
            ('agent_chinese', self._search_agent_chinese()),
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

        # 跨分类去重（按优先级保留）
        seen_urls = set()
        priority_order = ['agent_frameworks', 'agent_protocols', 'agentic_workflows', 'agent_chinese', 'agent_twitter']
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

    async def _search_agent_frameworks(self) -> List[Dict]:
        """搜索AI Agent框架教程"""
        category_config = self.content_config.get('agent_frameworks', {})
        queries = category_config.get('queries', [
            "LangChain agent tutorial guide 2025 2026",
            "CrewAI multi-agent tutorial getting started",
            "AutoGen agent framework tutorial practical",
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
                r['source_type'] = 'agent_frameworks'
                r['category_label'] = 'Agent框架教程'
            all_results.extend(results)

        return self._deduplicate(all_results)[:max_items]

    async def _search_agent_protocols(self) -> List[Dict]:
        """搜索Agent协议与工具集成（MCP / Function Calling）"""
        category_config = self.content_config.get('agent_protocols', {})
        queries = category_config.get('queries', [
            "MCP model context protocol server tool tutorial",
            "LLM tool use function calling implementation guide",
            "AI agent tool integration API orchestration",
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
                r['source_type'] = 'agent_protocols'
                r['category_label'] = '协议与工具集成'
            all_results.extend(results)

        return self._deduplicate(all_results)[:max_items]

    async def _search_agentic_workflows(self) -> List[Dict]:
        """搜索Agentic Workflow相关内容"""
        category_config = self.content_config.get('agentic_workflows', {})
        queries = category_config.get('queries', [
            "multi-agent system architecture design pattern",
            "agentic workflow orchestration deployment production",
            "AI agent memory planning reasoning implementation",
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
                r['source_type'] = 'agentic_workflows'
                r['category_label'] = 'Agentic Workflow'
            all_results.extend(results)

        return self._deduplicate(all_results)[:max_items]

    async def _search_agent_twitter(self) -> List[Dict]:
        """搜索Twitter/X上的AI Agent热门内容（仅用Exa）"""
        category_config = self.content_config.get('agent_twitter', {})
        queries = category_config.get('queries', [
            "AI agent framework LangChain CrewAI AutoGen update",
            "MCP tool use Claude agent announcement",
            "multi-agent system open source new release",
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
                r['source_type'] = 'agent_twitter'
                r['category_label'] = 'AI Agent Twitter热议'
            all_results.extend(results)

        return self._deduplicate(all_results)[:max_items]

    async def _search_agent_chinese(self) -> List[Dict]:
        """搜索中文AI Agent内容"""
        category_config = self.content_config.get('agent_chinese', {})
        queries = category_config.get('queries', [
            "AI Agent 智能体 教程 实践 开发",
            "LangChain MCP 智能体 中文教程",
            "多智能体 框架 应用 部署",
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
                r['source_type'] = 'agent_chinese'
                r['category_label'] = '中文AI Agent内容'
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
