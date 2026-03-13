"""
Twitter/X Agent
专门追踪 AI Agent 领域 KOL 推文和热门讨论
使用 Exa 的 tweet 分类搜索 + KOL 账号追踪
"""

import asyncio
import logging
from typing import List, Dict
from ..collectors.search_api_collector import SearchAPICollector

logger = logging.getLogger(__name__)

# AI Agent 领域核心 KOL 列表
DEFAULT_AI_KOLS = [
    # AI 公司/实验室负责人
    "sama",              # Sam Altman - OpenAI CEO
    "aaborovkov",        # Anthropic
    "ylecun",            # Yann LeCun - Meta AI
    "AndrewYNg",         # Andrew Ng
    "kaboroevich",       # Andrej Karpathy

    # Agent 框架/工具创始人
    "hwchase17",         # Harrison Chase - LangChain
    "joaomdmoura",       # João Moura - CrewAI
    "jerryjliu0",        # Jerry Liu - LlamaIndex

    # AI Agent 领域活跃研究者/开发者
    "siaborisov",        # Simon Willison
    "swaborisov",        # Swyx
    "alexalbert__",      # Alex Albert - Anthropic
    "mcaborisov",        # McKay Wrigley
    "emaborisov",        # Emad Mostaque
    "bindureddy",        # Bindu Reddy - Abacus.AI
    "chiefaioff",        # Chief AI Officer
    "DrJimFan",          # Jim Fan - NVIDIA
    "oaborisov",         # Oran Looney

    # 中文 AI 圈 KOL
    "dotey",             # 宝玉
    "9hills",            # 九山
]


class TwitterAgent:
    """Twitter/X AI Agent 内容追踪 Agent"""

    def __init__(self, config: Dict):
        self.config = config
        self.twitter_config = config.get('twitter', {})
        self.search_config = config.get('search_apis', {})
        self.collector = SearchAPICollector(self.search_config)

        # KOL 列表（可从配置覆盖）
        self.kol_accounts = self.twitter_config.get('kol_accounts', DEFAULT_AI_KOLS)
        self.max_items_per_category = self.twitter_config.get('max_items_per_category', 10)
        self.days = self.twitter_config.get('days', 3)

    async def collect(self) -> Dict[str, List[Dict]]:
        """搜集 Twitter/X 上 AI Agent 相关的高质量内容"""
        logger.info("TwitterAgent: Starting Twitter/X content collection...")

        if not self.collector.exa_client:
            logger.warning("TwitterAgent: Exa client not available (required for tweet search)")
            return {}

        results = {
            'kol_tweets': [],
            'trending_discussions': [],
            'new_releases': [],
        }

        tasks = [
            ('kol_tweets', self._collect_kol_tweets()),
            ('trending_discussions', self._collect_trending_discussions()),
            ('new_releases', self._collect_new_releases()),
        ]

        task_results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        for (key, _), result in zip(tasks, task_results):
            if isinstance(result, Exception):
                logger.error(f"TwitterAgent error in {key}: {result}")
            else:
                results[key] = result

        # 跨分类去重
        seen_urls = set()
        for key in ['kol_tweets', 'new_releases', 'trending_discussions']:
            unique = []
            for tweet in results.get(key, []):
                url = tweet.get('link', '').rstrip('/').lower()
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique.append(tweet)
            results[key] = unique

        total = sum(len(v) for v in results.values())
        logger.info(f"TwitterAgent: Collected {total} unique tweets")
        for key, tweets in results.items():
            if tweets:
                logger.info(f"  - {key}: {len(tweets)}")

        return results

    async def _collect_kol_tweets(self) -> List[Dict]:
        """追踪 AI KOL 的推文"""
        logger.info(f"Collecting KOL tweets from {len(self.kol_accounts)} accounts...")

        all_tweets = []

        # 分批查询 KOL（每批 5 个账号，用 Exa 的 include_domains 限定 x.com）
        batch_size = 5
        for i in range(0, len(self.kol_accounts), batch_size):
            batch = self.kol_accounts[i:i + batch_size]

            # 构建查询：KOL 用户名 + AI Agent 关键词
            kol_query = " OR ".join([f"from:{handle}" for handle in batch])
            search_query = f"({kol_query}) AI agent LLM tool"

            try:
                results = self.collector.search_exa(
                    query=search_query,
                    num_results=8,
                    category="tweet",
                    days=self.days,
                    include_domains=["x.com", "twitter.com"],
                )
                for r in results:
                    r['source_type'] = 'kol_tweet'
                    r['category_label'] = 'AI KOL 推文'
                all_tweets.extend(results)
            except Exception as e:
                logger.error(f"Error collecting KOL batch tweets: {e}")

        # 补充：直接搜 AI Agent 话题在 KOL 圈的讨论
        topic_queries = self.twitter_config.get('kol_topic_queries', [
            "AI agent framework new release announcement",
            "MCP protocol Claude tool use update",
            "multi-agent system breakthrough demo",
        ])

        for query in topic_queries:
            try:
                results = self.collector.search_exa(
                    query=query,
                    num_results=5,
                    category="tweet",
                    days=self.days,
                    include_domains=["x.com", "twitter.com"],
                )
                for r in results:
                    r['source_type'] = 'kol_tweet'
                    r['category_label'] = 'AI KOL 推文'
                all_tweets.extend(results)
            except Exception as e:
                logger.error(f"Error collecting topic tweets: {e}")

        return self._deduplicate(all_tweets)[:self.max_items_per_category]

    async def _collect_trending_discussions(self) -> List[Dict]:
        """搜集 AI Agent 领域的热门 Twitter 讨论"""
        logger.info("Collecting trending AI Agent discussions on Twitter...")

        queries = self.twitter_config.get('trending_queries', [
            "AI agent best practices production deployment",
            "LangChain CrewAI AutoGen comparison review",
            "Claude Sonnet Opus agent coding capability",
            "AI agent memory context window breakthrough",
            "open source AI agent tool impressive demo",
            "AI coding agent benchmark evaluation results",
        ])

        all_tweets = []
        for query in queries:
            try:
                results = self.collector.search_exa(
                    query=query,
                    num_results=5,
                    category="tweet",
                    days=self.days,
                    include_domains=["x.com", "twitter.com"],
                )
                for r in results:
                    r['source_type'] = 'trending_discussion'
                    r['category_label'] = 'AI Agent 热门讨论'
                all_tweets.extend(results)
            except Exception as e:
                logger.error(f"Error collecting trending discussion: {e}")

        return self._deduplicate(all_tweets)[:self.max_items_per_category]

    async def _collect_new_releases(self) -> List[Dict]:
        """搜集 AI Agent 相关的新发布/新工具推文"""
        logger.info("Collecting new release announcements on Twitter...")

        queries = self.twitter_config.get('release_queries', [
            "just released launched new AI agent tool",
            "open source AI agent framework v2 v3 release",
            "new MCP server plugin released GitHub",
            "AI agent SDK library just shipped",
        ])

        all_tweets = []
        for query in queries:
            try:
                results = self.collector.search_exa(
                    query=query,
                    num_results=5,
                    category="tweet",
                    days=self.days,
                    include_domains=["x.com", "twitter.com"],
                )
                for r in results:
                    r['source_type'] = 'new_release'
                    r['category_label'] = '新工具/新发布'
                all_tweets.extend(results)
            except Exception as e:
                logger.error(f"Error collecting new release tweets: {e}")

        return self._deduplicate(all_tweets)[:self.max_items_per_category]

    @staticmethod
    def _deduplicate(tweets: List[Dict]) -> List[Dict]:
        """按 URL 去重"""
        seen = set()
        unique = []
        for tweet in tweets:
            url = tweet.get('link', '').rstrip('/').lower()
            if url and url not in seen:
                seen.add(url)
                unique.append(tweet)
        return unique
