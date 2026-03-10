"""
主控制器 - 协调所有Agent并行工作（AI Agent技术博客聚合版）
"""

import asyncio
import logging
import os
from typing import Dict, Any
import yaml

from .agents.tech_agent import TechNewsAgent
from .agents.github_agent import GitHubAgent
from .agents.ai_content_agent import AIContentAgent
from .agents.chinese_platform_agent import ChinesePlatformAgent
from .evaluator.ai_evaluator import MiniMaxEvaluator
from .notifier.email_notifier import EmailNotifier

logger = logging.getLogger(__name__)


class NewsOrchestrator:
    """AI Agent技术博客聚合系统主控制器"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)

        # 初始化各个Agent
        self.tech_agent = TechNewsAgent(self.config)
        self.github_agent = GitHubAgent(self.config)
        self.ai_content_agent = AIContentAgent(self.config)
        self.chinese_platform_agent = ChinesePlatformAgent(self.config)

        # 初始化AI评估器
        minimax_key = os.getenv('MINIMAX_API_KEY')
        minimax_group = os.getenv('MINIMAX_GROUP_ID', '')

        self.evaluator = MiniMaxEvaluator(
            api_key=minimax_key,
            group_id=minimax_group
        )

        # 初始化通知器
        self.notifier = EmailNotifier()

        # 评估标准
        self.eval_criteria = self.config.get('evaluation', {})

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Config loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise

    async def run(self) -> bool:
        """运行完整的AI Agent博客聚合流程"""
        logger.info("=" * 50)
        logger.info("Starting AI Agent Blog Aggregation System")
        logger.info("=" * 50)

        try:
            # 第一步：并行搜集所有信息
            logger.info("\n[Step 1] Collecting AI Agent content from all sources...")
            all_results = await self._collect_all_news()

            # 第二步：AI评估和筛选
            logger.info("\n[Step 2] Evaluating content with AI...")
            evaluated_results = await self._evaluate_all_content(all_results)

            # 第三步：生成日报摘要
            logger.info("\n[Step 3] Generating daily report...")
            report = self._generate_report(evaluated_results)

            # 保存报告到文件用于检查
            report_file = "output/daily_report.md"
            os.makedirs("output", exist_ok=True)
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"Report saved to {report_file}")

            # 第四步：推送通知
            logger.info("\n[Step 4] Sending notifications...")
            success = self.notifier.send_daily_report(report)

            if success:
                logger.info("Daily report sent successfully!")
            else:
                logger.error("Failed to send daily report")

            logger.info("=" * 50)
            return success

        except Exception as e:
            logger.error(f"Error in orchestrator run: {e}", exc_info=True)
            return False

    async def _collect_all_news(self) -> Dict[str, Any]:
        """并行搜集所有AI Agent内容"""

        tasks = {
            'tech': self.tech_agent.collect(),
            'github': self.github_agent.collect(),
            'ai_content': self.ai_content_agent.collect(),
            'chinese_platform': self.chinese_platform_agent.collect(),
        }

        # 并行执行所有任务
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # 组合结果
        all_results = {}
        for key, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error in {key} agent: {result}")
                all_results[key] = {}
            else:
                all_results[key] = result

        # 统计
        total_items = 0
        for category, data in all_results.items():
            if isinstance(data, dict):
                for region, items in data.items():
                    if isinstance(items, list):
                        total_items += len(items)

        logger.info(f"Total items collected: {total_items}")

        return all_results

    async def _evaluate_all_content(self, all_results: Dict) -> Dict:
        """评估所有内容"""

        evaluated = {}

        # AI评估开关
        USE_AI_FOR_TECH = False  # AI博客禁用AI评估（避免不稳定）

        # 评估科技文章
        if 'tech' in all_results:
            evaluated['tech'] = {}
            tech_data = all_results['tech']

            all_tech_articles = []
            all_tech_articles.extend(tech_data.get('official_blogs', []))
            all_tech_articles.extend(tech_data.get('expert_blogs', []))
            all_tech_articles.extend(tech_data.get('research_papers', []))
            all_tech_articles.extend(tech_data.get('community', []))

            logger.info(f"Total tech articles collected: {len(all_tech_articles)}")
            logger.info(f"  - Official blogs: {len(tech_data.get('official_blogs', []))}")
            logger.info(f"  - Expert blogs: {len(tech_data.get('expert_blogs', []))}")
            logger.info(f"  - Research: {len(tech_data.get('research_papers', []))}")

            if all_tech_articles:
                if USE_AI_FOR_TECH:
                    official = tech_data.get('official_blogs', [])
                    if official:
                        logger.info(f"Deep analyzing {len(official)} official blog articles...")
                        evaluated_official = self.evaluator.evaluate_tech_articles(
                            articles=official,
                            criteria=self.eval_criteria,
                            fetch_content=True
                        )
                    else:
                        evaluated_official = []

                    other_articles = []
                    other_articles.extend(tech_data.get('expert_blogs', []))
                    other_articles.extend(tech_data.get('research_papers', []))

                    if other_articles:
                        evaluated_other = self.evaluator.evaluate_tech_articles(
                            articles=other_articles,
                            criteria=self.eval_criteria,
                            fetch_content=False
                        )
                    else:
                        evaluated_other = []

                    all_evaluated = evaluated_official + evaluated_other
                    all_evaluated.sort(key=lambda x: (
                        x.get('priority', 'medium') == 'critical',
                        x.get('score', 0)
                    ), reverse=True)

                    evaluated['tech']['articles'] = all_evaluated[:15]
                else:
                    # 不使用AI，直接显示原始文章
                    official = tech_data.get('official_blogs', [])
                    expert = tech_data.get('expert_blogs', [])

                    logger.info(f"No AI evaluation - Official blogs count: {len(official)}")
                    logger.info(f"No AI evaluation - Expert blogs count: {len(expert)}")

                    all_articles = []
                    priority_sources = [
                        'Claude Blog', 'Anthropic News', 'OpenAI Blog',
                        'LangChain Blog', 'Google AI Blog', 'HuggingFace Blog',
                        'AutoGen Blog'
                    ]

                    # 按来源分组
                    sources_articles = {}
                    for article in official:
                        source = article.get('source', 'Unknown')
                        if source not in sources_articles:
                            sources_articles[source] = []
                        sources_articles[source].append(article)

                    for source in priority_sources:
                        if source in sources_articles:
                            count = 5 if source in ['Claude Blog', 'Anthropic News', 'LangChain Blog'] else 3
                            for article in sources_articles[source][:count]:
                                article['score'] = 8 if source in ['Claude Blog', 'Anthropic News', 'OpenAI Blog', 'LangChain Blog'] else 7
                                all_articles.append(article)

                    # 添加专家博客
                    for article in expert[:5]:
                        article['score'] = 7
                        all_articles.append(article)

                    evaluated['tech']['articles'] = all_articles

        # 评估AI Agent内容（搜索API结果）
        if 'ai_content' in all_results and all_results['ai_content']:
            evaluated['ai_content'] = {}
            ai_data = all_results['ai_content']

            for category, articles in ai_data.items():
                if articles:
                    for article in articles:
                        article['score'] = article.get('score', 7)
                    evaluated['ai_content'][category] = articles
                    logger.info(f"AI content - {category}: {len(articles)} articles")

        # 评估中文平台内容
        if 'chinese_platform' in all_results and all_results['chinese_platform']:
            evaluated['chinese_platform'] = {}
            cn_data = all_results['chinese_platform']

            for platform, articles in cn_data.items():
                if articles:
                    for article in articles:
                        article['score'] = article.get('score', 7)
                    evaluated['chinese_platform'][platform] = articles
                    logger.info(f"Chinese platform - {platform}: {len(articles)} articles")

        # 评估GitHub项目
        if 'github' in all_results:
            evaluated['github'] = {}
            github_data = all_results['github']

            all_projects = []
            all_projects.extend(github_data.get('trending', []))
            all_projects.extend(github_data.get('ai_projects', []))

            if all_projects:
                projects = all_projects[:8]
                for project in projects:
                    project['score'] = 8
                evaluated['github']['projects'] = projects

        return evaluated

    def _generate_report(self, evaluated_results: Dict) -> str:
        """生成最终报告"""
        logger.info("Using template to generate report...")
        return self._generate_template_report(evaluated_results)

    def _generate_template_report(self, evaluated_results: Dict) -> str:
        """生成AI Agent技术博客日报"""

        report = ""

        # === 1. AI Agent 官方博客与专家动态 ===
        if 'tech' in evaluated_results and evaluated_results['tech'].get('articles'):
            articles = evaluated_results['tech']['articles']

            report += "## AI Agent 官方博客与专家动态\n\n"
            report += f"_本期搜集到 {len(articles)} 篇AI Agent相关博客文章_\n\n"

            # 按来源分类
            official = [a for a in articles if a.get('source_type') == 'official_blogs']
            expert = [a for a in articles if a.get('source_type') == 'expert_blogs']

            # 显示官方博客
            if official:
                report += "### 官方博客\n\n"
                for idx, article in enumerate(official[:10], 1):
                    title_original = article.get('title', '')
                    title_cn = article.get('title_cn', title_original)
                    link = article.get('link', '')
                    source = article.get('source', '')
                    score = article.get('score', 0)

                    report += f"**{idx}. {title_cn}**\n"
                    if title_cn != title_original:
                        report += f"   _({title_original})_\n"
                    report += f"   来源：{source} | 评分：{score}/10\n"
                    if link:
                        report += f"   {link}\n\n"

            # 显示专家博客
            if expert:
                report += "### 专家博客\n\n"
                for idx, article in enumerate(expert[:5], 1):
                    title_original = article.get('title', '')
                    title_cn = article.get('title_cn', title_original)
                    link = article.get('link', '')
                    source = article.get('source', '')

                    report += f"**{idx}. {title_cn}**\n"
                    if title_cn != title_original:
                        report += f"   _({title_original})_\n"
                    report += f"   来源：{source}\n"
                    if link:
                        report += f"   {link}\n\n"

            report += "---\n\n"

        # === 2. AI Agent 框架与工具 ===
        if 'ai_content' in evaluated_results and evaluated_results['ai_content']:
            ai_content = evaluated_results['ai_content']

            report += "## AI Agent 框架与工具\n\n"

            category_display = [
                ('agent_frameworks', '### Agent 框架教程', 10),
                ('agent_protocols', '### 协议与工具集成 (MCP / Function Calling)', 10),
                ('agentic_workflows', '### Agentic Workflow', 10),
            ]

            for category_key, section_title, max_show in category_display:
                articles = ai_content.get(category_key, [])
                if articles:
                    report += f"{section_title}\n\n"
                    for idx, article in enumerate(articles[:max_show], 1):
                        title = article.get('title', '')
                        link = article.get('link', '')
                        summary = article.get('summary', '')
                        author = article.get('author', '')

                        report += f"**{idx}. {title}**\n"
                        if author:
                            report += f"   作者：{author}\n"
                        if summary:
                            display_summary = summary[:150] + '...' if len(summary) > 150 else summary
                            report += f"   {display_summary}\n"
                        if link:
                            report += f"   {link}\n\n"

                    report += "\n"

            report += "---\n\n"

        # === 3. GitHub Agent 开源项目 ===
        if 'github' in evaluated_results and evaluated_results['github'].get('projects'):
            report += "## GitHub Agent 开源项目\n\n"

            for idx, project in enumerate(evaluated_results['github']['projects'][:8], 1):
                name = project.get('name', '')
                author = project.get('author', '')
                url = project.get('url', '')
                description = project.get('description', '')
                stars = project.get('stars', 0)
                language = project.get('language', '')

                if stars >= 10000:
                    stars_display = f"{stars/1000:.1f}k"
                else:
                    stars_display = str(stars)

                report += f"**{idx}. {author}/{name}**\n"
                if description:
                    report += f"   {description}\n"
                report += f"   Stars: {stars_display}"
                if language:
                    report += f" | {language}"
                report += "\n"
                if url:
                    report += f"   {url}\n\n"

            report += "---\n\n"

        # === 4. 中文社区 Agent 动态 ===
        if 'chinese_platform' in evaluated_results and evaluated_results['chinese_platform']:
            cn_data = evaluated_results['chinese_platform']

            report += "## 中文社区 Agent 动态\n\n"

            for platform_name, articles in cn_data.items():
                if articles:
                    report += f"### {platform_name}\n\n"
                    for idx, article in enumerate(articles[:6], 1):
                        title = article.get('title', '')
                        link = article.get('link', '')
                        summary = article.get('summary', '')

                        report += f"**{idx}. {title}**\n"
                        if summary:
                            display_summary = summary[:150] + '...' if len(summary) > 150 else summary
                            report += f"   {display_summary}\n"
                        if link:
                            report += f"   {link}\n\n"

                    report += "\n"

            report += "---\n\n"

        # === 5. AI Agent 中文内容 ===
        if 'ai_content' in evaluated_results and evaluated_results['ai_content']:
            ai_content = evaluated_results['ai_content']
            chinese_articles = ai_content.get('agent_chinese', [])
            if chinese_articles:
                report += "## AI Agent 中文精选\n\n"
                for idx, article in enumerate(chinese_articles[:8], 1):
                    title = article.get('title', '')
                    link = article.get('link', '')
                    summary = article.get('summary', '')

                    report += f"**{idx}. {title}**\n"
                    if summary:
                        display_summary = summary[:150] + '...' if len(summary) > 150 else summary
                        report += f"   {display_summary}\n"
                    if link:
                        report += f"   {link}\n\n"

                report += "---\n\n"

        # === 6. AI Agent Twitter/X 热议 ===
        if 'ai_content' in evaluated_results and evaluated_results['ai_content']:
            ai_content = evaluated_results['ai_content']
            twitter_articles = ai_content.get('agent_twitter', [])
            if twitter_articles:
                report += "## AI Agent Twitter/X 热议\n\n"
                for idx, article in enumerate(twitter_articles[:6], 1):
                    title = article.get('title', '')
                    link = article.get('link', '')
                    author = article.get('author', '')

                    report += f"**{idx}. {title}**\n"
                    if author:
                        report += f"   作者：{author}\n"
                    if link:
                        report += f"   {link}\n\n"

        return report
