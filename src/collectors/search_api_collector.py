"""
搜索API统一封装 - Tavily + Exa
通过搜索引擎主动发现AI实践类内容
"""

import os
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SearchAPICollector:
    """统一封装 Tavily 和 Exa 搜索API"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.tavily_client = None
        self.exa_client = None
        self._init_clients()

    def _init_clients(self):
        """初始化API客户端（仅在有key时初始化）"""
        tavily_key = os.getenv('TAVILY_API_KEY')
        if tavily_key:
            try:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=tavily_key)
                logger.info("Tavily client initialized")
            except ImportError:
                logger.warning("tavily-python not installed, skipping Tavily")
            except Exception as e:
                logger.error(f"Failed to init Tavily client: {e}")

        exa_key = os.getenv('EXA_API_KEY')
        if exa_key:
            try:
                from exa_py import Exa
                self.exa_client = Exa(api_key=exa_key)
                logger.info("Exa client initialized")
            except ImportError:
                logger.warning("exa-py not installed, skipping Exa")
            except Exception as e:
                logger.error(f"Failed to init Exa client: {e}")

    def search_tavily(
        self,
        query: str,
        search_depth: str = "basic",
        topic: str = "general",
        max_results: int = 5,
        days: int = 7,
        include_domains: List[str] = None,
        exclude_domains: List[str] = None
    ) -> List[Dict]:
        """
        Tavily搜索

        Args:
            query: 搜索关键词
            search_depth: "basic" 或 "advanced"
            topic: "general", "news", "finance"
            max_results: 最大结果数 (0-20)
            days: 搜索最近N天
            include_domains: 限定域名
            exclude_domains: 排除域名
        """
        if not self.tavily_client:
            logger.debug("Tavily client not available, skipping")
            return []

        try:
            kwargs = {
                'query': query,
                'search_depth': search_depth,
                'topic': topic,
                'max_results': max_results,
            }

            if days:
                kwargs['time_range'] = f"{days}d" if days <= 7 else None
                if days > 7:
                    start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                    kwargs['start_date'] = start

            if include_domains:
                kwargs['include_domains'] = include_domains
            if exclude_domains:
                kwargs['exclude_domains'] = exclude_domains

            response = self.tavily_client.search(**kwargs)

            results = []
            for item in response.get('results', []):
                results.append(self._normalize_tavily(item))

            logger.info(f"Tavily: {len(results)} results for '{query[:50]}'")
            return results

        except Exception as e:
            logger.error(f"Tavily search error for '{query[:50]}': {e}")
            return []

    def search_exa(
        self,
        query: str,
        num_results: int = 5,
        category: Optional[str] = None,
        days: int = 7,
        include_domains: List[str] = None,
        exclude_domains: List[str] = None
    ) -> List[Dict]:
        """
        Exa搜索

        Args:
            query: 搜索关键词
            num_results: 最大结果数
            category: "tweet", "research paper", "blog post", "news", "company", "pdf"
            days: 搜索最近N天
            include_domains: 限定域名
            exclude_domains: 排除域名
        """
        if not self.exa_client:
            logger.debug("Exa client not available, skipping")
            return []

        try:
            kwargs = {
                'query': query,
                'num_results': num_results,
            }

            if category:
                kwargs['category'] = category
            if days:
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
                kwargs['start_published_date'] = start_date
            if include_domains:
                kwargs['include_domains'] = include_domains
            if exclude_domains:
                kwargs['exclude_domains'] = exclude_domains

            response = self.exa_client.search(**kwargs)

            results = []
            for item in response.results:
                results.append(self._normalize_exa(item))

            logger.info(f"Exa: {len(results)} results for '{query[:50]}'")
            return results

        except Exception as e:
            logger.error(f"Exa search error for '{query[:50]}': {e}")
            return []

    def search_all(
        self,
        query: str,
        max_per_api: int = 5,
        category: Optional[str] = None,
        days: int = 7,
        include_domains: List[str] = None,
        exclude_domains: List[str] = None,
        exa_only: bool = False
    ) -> List[Dict]:
        """
        同时调用所有可用API搜索，合并去重

        Args:
            query: 搜索关键词
            max_per_api: 每个API的最大结果数
            category: Exa专用分类
            days: 搜索天数
            exa_only: 是否只用Exa（如Twitter搜索）
        """
        all_results = []

        # Exa搜索
        exa_results = self.search_exa(
            query=query,
            num_results=max_per_api,
            category=category,
            days=days,
            include_domains=include_domains,
            exclude_domains=exclude_domains
        )
        all_results.extend(exa_results)

        # Tavily搜索（除非exa_only）
        if not exa_only:
            tavily_results = self.search_tavily(
                query=query,
                max_results=max_per_api,
                days=days,
                include_domains=include_domains,
                exclude_domains=exclude_domains
            )
            all_results.extend(tavily_results)

        # 按URL去重
        seen_urls = set()
        unique_results = []
        for item in all_results:
            url = item.get('link', '')
            # 规范化URL去重
            normalized_url = url.rstrip('/').lower()
            if normalized_url and normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_results.append(item)

        logger.info(f"search_all: {len(unique_results)} unique results for '{query[:50]}' (from {len(all_results)} total)")
        return unique_results

    def _normalize_tavily(self, item: Dict) -> Dict:
        """将Tavily结果标准化"""
        return {
            'title': item.get('title', ''),
            'link': item.get('url', ''),
            'summary': item.get('content', '')[:500] if item.get('content') else '',
            'published': item.get('published_date', ''),
            'source': 'Tavily Search',
            'source_api': 'tavily',
            'score_relevance': item.get('score', 0),
        }

    def _normalize_exa(self, item) -> Dict:
        """将Exa结果标准化"""
        url = getattr(item, 'url', '') or ''
        # 修复缺少协议的URL（如 x.com/... -> https://x.com/...）
        if url and not url.startswith('http'):
            url = 'https://' + url

        return {
            'title': getattr(item, 'title', '') or '',
            'link': url,
            'summary': (getattr(item, 'text', '') or '')[:500],
            'published': getattr(item, 'published_date', '') or '',
            'source': 'Exa Search',
            'source_api': 'exa',
            'author': getattr(item, 'author', '') or '',
            'score_relevance': getattr(item, 'score', 0),
        }
