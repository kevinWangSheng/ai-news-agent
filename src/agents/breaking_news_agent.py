"""
Breaking News Agent - 专抓'今日/近两日'发布的 AI Agent 领域内容

为什么独立成一个 agent:
- tech_agent 用 30 天窗口，覆盖性好但没有时效突出
- ai_content_agent 查的是教程类泛关键词，抓不到当日发布
- 这个 agent 用三种机制互补:
  1. Exa 站点限定 + start_published_date=today 查各大实验室官网
  2. Exa 跨站关键词 + today 窗口抓突发新闻
  3. 官方 RSS 1-2 天窗口前置拉取（RSS 命中就不必走搜索 API）

所有结果在报告里置顶 (priority_tier='breaking')，保证'今天发的东西今天能看到'。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ..collectors.news_collector import NewsCollector
from ..collectors.search_api_collector import SearchAPICollector

logger = logging.getLogger(__name__)


class BreakingNewsAgent:
    """AI Agent 领域当日突发新闻 Agent"""

    def __init__(self, config: Dict):
        self.config = config
        self.bn_config = config.get("breaking_news", {}) or {}
        self.enabled = self.bn_config.get("enabled", True)
        self.days = int(self.bn_config.get("days", 2))
        self.max_per_query = int(self.bn_config.get("max_items_per_query", 8))
        self.total_max = int(self.bn_config.get("total_max_items", 25))

        self.search = SearchAPICollector(config.get("search_apis", {}))
        self.rss = NewsCollector()

        self.tech_sources = config.get("tech_sources", {}) or {}

    # ------------------------------------------------------------------
    async def collect(self) -> Dict[str, List[Dict]]:
        if not self.enabled:
            logger.info("BreakingNewsAgent: disabled")
            return {}

        logger.info(
            f"BreakingNewsAgent: 抓取最近 {self.days} 天 Agent 领域突发内容…"
        )

        # 三路并行
        tasks = [
            self._collect_from_site_queries(),
            self._collect_from_keyword_queries(),
            self._collect_from_official_rss(),
        ]

        path_labels = ["site_search", "keyword_search", "official_rss"]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        combined: List[Dict] = []
        per_path_stats: Dict[str, int] = {}
        for label, result in zip(path_labels, raw_results):
            if isinstance(result, Exception):
                logger.error(f"BreakingNewsAgent: {label} failed: {result}")
                per_path_stats[label] = 0
                continue
            per_path_stats[label] = len(result)
            combined.extend(result)

        deduped = self._dedupe(combined)

        # 只保留最近 N 天的
        filtered = self._filter_recent(deduped)

        # 按已有 score_relevance 或发布时间降序
        filtered.sort(
            key=lambda x: (
                x.get("score_relevance") or 0,
                x.get("_parsed_ts") or 0,
            ),
            reverse=True,
        )

        top = filtered[: self.total_max]
        logger.info(
            f"BreakingNewsAgent: site={per_path_stats.get('site_search', 0)} "
            f"keyword={per_path_stats.get('keyword_search', 0)} "
            f"rss={per_path_stats.get('official_rss', 0)} "
            f"→ dedup后 {len(deduped)} → 近{self.days}天 {len(filtered)} → top{len(top)}"
        )

        # 打标便于下游渲染
        for item in top:
            item["priority_tier"] = "breaking"

        return {"items": top}

    # ------------------------------------------------------------------
    # 路径1: 站点限定 + 时效搜索
    # ------------------------------------------------------------------
    async def _collect_from_site_queries(self) -> List[Dict]:
        if not self.search.exa_client:
            logger.info("BreakingNewsAgent: Exa 未配置，跳过站点限定搜索")
            return []

        site_queries = self.bn_config.get("site_queries", []) or []
        if not site_queries:
            return []

        results: List[Dict] = []
        for entry in site_queries:
            site = entry.get("site", "").strip()
            query = entry.get("query", "").strip() or site
            if not site:
                continue
            try:
                # 同步 API，放线程池避免阻塞 event loop
                hits = await asyncio.to_thread(
                    self.search.search_exa,
                    query=query,
                    num_results=self.max_per_query,
                    days=self.days,
                    include_domains=[site],
                )
                for h in hits:
                    h["source_type"] = "breaking_news"
                    h["breaking_channel"] = f"site:{site}"
                results.extend(hits)
            except Exception as exc:
                logger.error(f"BreakingNewsAgent: site search failed ({site}): {exc}")

        return results

    # ------------------------------------------------------------------
    # 路径2: 泛关键词 + 时效搜索（Tavily + Exa）
    # ------------------------------------------------------------------
    async def _collect_from_keyword_queries(self) -> List[Dict]:
        kw_queries = self.bn_config.get("keyword_queries", []) or []
        if not kw_queries:
            return []

        if not self.search.exa_client and not self.search.tavily_client:
            logger.info("BreakingNewsAgent: 搜索 API 未配置，跳过关键词搜索")
            return []

        results: List[Dict] = []
        for query in kw_queries:
            try:
                hits = await asyncio.to_thread(
                    self.search.search_all,
                    query=query,
                    max_per_api=self.max_per_query,
                    days=self.days,
                )
                for h in hits:
                    h["source_type"] = "breaking_news"
                    h["breaking_channel"] = "keyword"
                results.extend(hits)
            except Exception as exc:
                logger.error(f"BreakingNewsAgent: keyword search failed: {exc}")

        return results

    # ------------------------------------------------------------------
    # 路径3: 官方 RSS 1-2 天窗口
    # ------------------------------------------------------------------
    async def _collect_from_official_rss(self) -> List[Dict]:
        if not self.bn_config.get("prioritize_official_rss", True):
            return []

        official = self.tech_sources.get("official_blogs", []) or []
        if not official:
            return []

        results: List[Dict] = []

        def _fetch(url: str) -> List[Dict]:
            return self.rss.collect_rss_feed(url, max_items=10)

        # 只抓 rss 类型的源，避免对全部站点做 HTML 抓取
        rss_sources = [b for b in official if b.get("type") == "rss"]

        tasks = [asyncio.to_thread(_fetch, b["url"]) for b in rss_sources if b.get("url")]
        fetched = await asyncio.gather(*tasks, return_exceptions=True)

        for blog, items in zip(rss_sources, fetched):
            if isinstance(items, Exception):
                logger.warning(
                    f"BreakingNewsAgent: RSS fail {blog.get('name')}: {items}"
                )
                continue
            for art in items or []:
                art["source"] = blog.get("name", art.get("source", ""))
                art["source_type"] = "breaking_news"
                art["breaking_channel"] = f"rss:{blog.get('name')}"
                art["priority"] = blog.get("priority", "high")
                results.append(art)

        return results

    # ------------------------------------------------------------------
    # 去重
    # ------------------------------------------------------------------
    def _dedupe(self, items: List[Dict]) -> List[Dict]:
        seen: set = set()
        out: List[Dict] = []
        for it in items:
            url = (it.get("link") or "").strip().lower()
            if not url:
                continue
            for prefix in ("https://", "http://", "www."):
                if url.startswith(prefix):
                    url = url[len(prefix) :]
            url = url.rstrip("/")
            if url in seen:
                continue
            seen.add(url)
            out.append(it)
        return out

    # ------------------------------------------------------------------
    # 近 N 天过滤（尽量宽松 - 没有 published 就保留）
    # ------------------------------------------------------------------
    def _filter_recent(self, items: List[Dict]) -> List[Dict]:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=self.days)
        keep: List[Dict] = []

        for it in items:
            pub = it.get("published")
            if not pub:
                keep.append(it)
                continue

            ts = self._parse_dt(pub)
            if ts is None:
                keep.append(it)
                continue

            if ts >= cutoff:
                it["_parsed_ts"] = ts.timestamp()
                keep.append(it)

        return keep

    @staticmethod
    def _parse_dt(value: Any) -> Optional[datetime]:
        if not value:
            return None
        try:
            from dateutil import parser

            dt = parser.parse(str(value))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None
