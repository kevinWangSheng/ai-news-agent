"""
主控制器 - 协调所有Agent并行工作
"""

import asyncio
import logging
import os
from typing import Dict, Any
import yaml

from .agents.asia_agent import AsiaNewsAgent
from .agents.americas_agent import AmericasNewsAgent
from .agents.europe_agent import EuropeNewsAgent
from .agents.others_agent import OthersNewsAgent
from .agents.tech_agent import TechNewsAgent
from .agents.github_agent import GitHubAgent
from .agents.ai_content_agent import AIContentAgent
from .evaluator.ai_evaluator import MiniMaxEvaluator
from .notifier.email_notifier import EmailNotifier

logger = logging.getLogger(__name__)


class NewsOrchestrator:
    """新闻聚合系统主控制器"""

    def __init__(self, config_path: str):
        """
        初始化控制器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)

        # 初始化各个Agent
        self.asia_agent = AsiaNewsAgent(self.config)
        self.americas_agent = AmericasNewsAgent(self.config)
        self.europe_agent = EuropeNewsAgent(self.config)
        self.others_agent = OthersNewsAgent(self.config)
        self.tech_agent = TechNewsAgent(self.config)
        self.github_agent = GitHubAgent(self.config)
        self.ai_content_agent = AIContentAgent(self.config)

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
        """
        运行完整的新闻聚合流程

        Returns:
            是否成功
        """
        logger.info("=" * 50)
        logger.info("Starting News Aggregation System")
        logger.info("=" * 50)

        try:
            # 第一步：并行搜集所有信息
            logger.info("\n[Step 1] Collecting news from all sources...")
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
                logger.info("✓ Daily report sent successfully!")
            else:
                logger.error("✗ Failed to send daily report")

            logger.info("=" * 50)
            return success

        except Exception as e:
            logger.error(f"Error in orchestrator run: {e}", exc_info=True)
            return False

    async def _collect_all_news(self) -> Dict[str, Any]:
        """并行搜集所有新闻"""

        # 创建所有搜集任务
        tasks = {
            'asia': self.asia_agent.collect(),
            'americas': self.americas_agent.collect(),
            'europe': self.europe_agent.collect(),
            'others': self.others_agent.collect(),
            'tech': self.tech_agent.collect(),
            'github': self.github_agent.collect(),
            'ai_content': self.ai_content_agent.collect(),
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
        """并行评估所有内容"""

        evaluated = {}

        # AI评估开关（分开控制）
        USE_AI_FOR_NEWS = True      # 地区新闻启用AI（翻译外语）
        USE_AI_FOR_TECH = False     # AI博客禁用AI（避免不稳定）

        # 评估各地区新闻
        for region_type in ['asia', 'americas', 'europe', 'others']:
            if region_type in all_results:
                evaluated[region_type] = {}

                for region_name, articles in all_results[region_type].items():
                    if articles:
                        if USE_AI_FOR_NEWS:
                            logger.info(f"Evaluating {len(articles)} articles from {region_name}...")
                            evaluated_articles = self.evaluator.evaluate_news(
                                articles=articles,
                                region=region_name,
                                criteria=self.eval_criteria
                            )
                        else:
                            # 不使用AI，直接添加默认分数
                            evaluated_articles = articles[:5]  # 取前5条
                            for article in evaluated_articles:
                                article['score'] = 7  # 默认分数
                                article['ai_reason'] = 'No AI evaluation'

                        evaluated[region_type][region_name] = evaluated_articles
                    else:
                        evaluated[region_type][region_name] = []

        # 评估科技文章（新数据结构）
        if 'tech' in all_results:
            evaluated['tech'] = {}
            tech_data = all_results['tech']

            # 合并所有类型的文章
            all_tech_articles = []
            all_tech_articles.extend(tech_data.get('official_blogs', []))
            all_tech_articles.extend(tech_data.get('expert_blogs', []))
            all_tech_articles.extend(tech_data.get('research_papers', []))
            all_tech_articles.extend(tech_data.get('community', []))
            all_tech_articles.extend(tech_data.get('news_articles', []))

            logger.info(f"Total tech articles collected: {len(all_tech_articles)}")
            logger.info(f"  - Official blogs: {len(tech_data.get('official_blogs', []))}")
            logger.info(f"  - Expert blogs: {len(tech_data.get('expert_blogs', []))}")
            logger.info(f"  - Research: {len(tech_data.get('research_papers', []))}")

            if all_tech_articles:
                if USE_AI_FOR_TECH:
                    # 优先评估官方博客（深度分析）
                    official = tech_data.get('official_blogs', [])
                    if official:
                        logger.info(f"Deep analyzing {len(official)} official blog articles...")
                        # 调试：显示各来源的文章数量
                        sources_count = {}
                        for article in official:
                            source = article.get('source', 'Unknown')
                            sources_count[source] = sources_count.get(source, 0) + 1
                        logger.info(f"Official blogs by source: {sources_count}")

                        evaluated_official = self.evaluator.evaluate_tech_articles(
                            articles=official,
                            criteria=self.eval_criteria,
                            fetch_content=True  # 官方博客启用深度分析
                        )
                    else:
                        evaluated_official = []

                    # 其他文章快速评估
                    other_articles = []
                    other_articles.extend(tech_data.get('expert_blogs', []))
                    other_articles.extend(tech_data.get('research_papers', []))

                    if other_articles:
                        logger.info(f"Quick evaluating {len(other_articles)} other articles...")
                        evaluated_other = self.evaluator.evaluate_tech_articles(
                            articles=other_articles,
                            criteria=self.eval_criteria,
                            fetch_content=False  # 其他文章不抓取内容（更快）
                        )
                    else:
                        evaluated_other = []

                    # 合并并排序
                    all_evaluated = evaluated_official + evaluated_other

                    # 如果评估结果太少，补充原始文章（确保有内容）
                    if len(all_evaluated) < 15:
                        logger.warning(f"Only {len(all_evaluated)} articles after evaluation, adding more from original...")
                        # 从各来源均衡选取文章
                        sources_articles = {}
                        for article in official:
                            source = article.get('source', 'Unknown')
                            if source not in sources_articles:
                                sources_articles[source] = []
                            sources_articles[source].append(article)

                        # 从每个来源选取文章（优先Claude Blog、Anthropic和OpenAI）
                        priority_sources = ['Claude Blog', 'Anthropic News', 'OpenAI Blog', 'DeepMind Blog', 'Google AI Blog']
                        added_count = 0

                        for source in priority_sources:
                            if source in sources_articles:
                                for article in sources_articles[source][:3]:  # 每个来源取3篇
                                    if article not in all_evaluated and added_count < 15:
                                        article['score'] = article.get('score', 8 if source in ['Claude Blog', 'Anthropic News', 'OpenAI Blog'] else 7)
                                        all_evaluated.append(article)
                                        added_count += 1
                                        logger.info(f"Added: {article.get('title', '')[:50]} from {source}")

                        # 如果还不够，从其他来源补充
                        if added_count < 15:
                            for source, articles in sources_articles.items():
                                if source not in priority_sources:
                                    for article in articles[:2]:
                                        if article not in all_evaluated and added_count < 15:
                                            article['score'] = article.get('score', 7)
                                            all_evaluated.append(article)
                                            added_count += 1

                        logger.info(f"Added {added_count} articles from original official blogs")

                    all_evaluated.sort(key=lambda x: (
                        x.get('priority', 'medium') == 'critical',  # critical优先
                        x.get('score', 0)  # 然后按分数
                    ), reverse=True)

                    evaluated['tech']['articles'] = all_evaluated[:15]  # 取前15篇
                else:
                    # 不使用AI，直接显示原始文章，从各来源均衡选取
                    official = tech_data.get('official_blogs', [])
                    expert = tech_data.get('expert_blogs', [])

                    logger.info(f"No AI evaluation - Official blogs count: {len(official)}")
                    logger.info(f"No AI evaluation - Expert blogs count: {len(expert)}")

                    # 按来源分组
                    sources_articles = {}
                    for article in official:
                        source = article.get('source', 'Unknown')
                        if source not in sources_articles:
                            sources_articles[source] = []
                        sources_articles[source].append(article)

                    logger.info(f"Sources found: {list(sources_articles.keys())}")
                    for source, articles in sources_articles.items():
                        logger.info(f"  {source}: {len(articles)} articles")

                    # 从各来源选取文章
                    all_articles = []
                    priority_sources = ['Claude Blog', 'Anthropic News', 'OpenAI Blog', 'DeepMind Blog', 'Google AI Blog', 'HuggingFace Blog']

                    for source in priority_sources:
                        if source in sources_articles:
                            # Claude Blog取更多文章（因为内容质量高且更新频繁）
                            count = 10 if source == 'Claude Blog' else 3
                            for article in sources_articles[source][:count]:
                                article['score'] = 8 if source in ['Claude Blog', 'Anthropic News', 'OpenAI Blog'] else 7
                                all_articles.append(article)

                    # 添加专家博客
                    for article in expert[:5]:
                        article['score'] = 7
                        all_articles.append(article)

                    evaluated['tech']['articles'] = all_articles

        # 评估AI实践内容（搜索API结果）
        if 'ai_content' in all_results and all_results['ai_content']:
            evaluated['ai_content'] = {}
            ai_data = all_results['ai_content']

            for category, articles in ai_data.items():
                if articles:
                    # 搜索API结果不用AI评估，直接给默认分数
                    for article in articles:
                        article['score'] = article.get('score', 7)
                    evaluated['ai_content'][category] = articles
                    logger.info(f"AI content - {category}: {len(articles)} articles")

        # 评估GitHub项目
        if 'github' in all_results:
            evaluated['github'] = {}
            github_data = all_results['github']

            all_projects = []
            all_projects.extend(github_data.get('trending', []))
            all_projects.extend(github_data.get('ai_projects', []))

            if all_projects:
                # GitHub项目不使用AI评估（直接显示）
                projects = all_projects[:8]
                for project in projects:
                    project['score'] = 8
                evaluated['github']['projects'] = projects

        return evaluated

    def _generate_report(self, evaluated_results: Dict) -> str:
        """生成最终报告（可选择用AI生成或模板生成）"""

        # AI摘要开关 - 关闭，使用模板保证链接正确
        USE_AI_SUMMARY = False  # 使用模板生成（保证链接可点击）

        if USE_AI_SUMMARY:
            # 方案1：使用AI生成摘要（推荐）
            try:
                logger.info("Generating AI-powered summary...")
                report = self.evaluator.generate_summary(evaluated_results)
                if report and len(report) > 100:  # 确保有内容
                    return report
            except Exception as e:
                logger.error(f"AI summary generation failed: {e}")

        # 降级到模板生成
        logger.info("Using template to generate report...")
        return self._generate_template_report(evaluated_results)

    def _generate_template_report(self, evaluated_results: Dict) -> str:
        """使用模板生成报告（降级方案）"""

        report = "## 📰 全球科技要闻\n\n"

        # 各地区新闻（简洁格式）
        for region_type in ['asia', 'americas', 'europe', 'others']:
            if region_type in evaluated_results:
                for region_name, articles in evaluated_results[region_type].items():
                    if articles:
                        report += f"### {region_name}\n\n"
                        for idx, article in enumerate(articles[:3], 1):
                            score = article.get('score', 0)
                            # 优先使用中文标题
                            title_cn = article.get('title_cn', article.get('title', ''))
                            title_original = article.get('title', '')
                            link = article.get('link', '')
                            summary_cn = article.get('summary_cn', '')

                            # 简洁格式
                            report += f"**{idx}. {title_cn}** `{score}/10`\n"

                            # 如果有翻译，显示原标题
                            if title_cn != title_original and len(title_original) > 0:
                                report += f"   _原标题：{title_original}_\n"

                            # 中文摘要
                            if summary_cn:
                                report += f"   {summary_cn}\n"

                            # 链接
                            if link:
                                report += f"   🔗 {link}\n\n"
                            else:
                                report += "\n"

                        report += "\n"

        # AI科技博客（简化格式 - 确保显示）
        if 'tech' in evaluated_results and evaluated_results['tech'].get('articles'):
            articles = evaluated_results['tech']['articles']

            report += "## 🤖 AI科技博客\n\n"
            report += f"_本期搜集到 {len(articles)} 篇AI博客文章_\n\n"

            # 按来源分类
            official = [a for a in articles if a.get('source_type') == 'official_blogs']
            expert = [a for a in articles if a.get('source_type') == 'expert_blogs']

            # 调试信息
            logger.info(f"Report generation - Total articles: {len(articles)}")
            logger.info(f"Report generation - Official blogs: {len(official)}")
            logger.info(f"Report generation - Expert blogs: {len(expert)}")
            if articles:
                logger.info(f"First article source_type: {articles[0].get('source_type')}")
                logger.info(f"First article source: {articles[0].get('source')}")

            # 显示官方博客（最多10篇）
            if official:
                report += "### OpenAI / Anthropic / Google / DeepMind 官方博客\n\n"
                for idx, article in enumerate(official[:10], 1):
                    title_original = article.get('title', '')
                    title_cn = article.get('title_cn', title_original)
                    link = article.get('link', '')
                    source = article.get('source', '')
                    score = article.get('score', 0)

                    # 简洁格式
                    report += f"**{idx}. {title_cn}**\n"
                    if title_cn != title_original:
                        report += f"   _({title_original})_\n"
                    report += f"   来源：{source} | 评分：{score}/10\n"
                    report += f"   🔗 {link}\n\n"

            # 显示专家博客（最多5篇）
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
                    report += f"   🔗 {link}\n\n"

            report += "---\n\n"

        # AI实践内容（搜索API发现）
        if 'ai_content' in evaluated_results and evaluated_results['ai_content']:
            ai_content = evaluated_results['ai_content']

            report += "## 🔬 AI实践精选\n\n"

            # 定义各分类的显示顺序和标题
            category_display = [
                ('claude_anthropic', '### Claude / Anthropic 实践', 8),
                ('openai_practical', '### OpenAI 实践', 8),
                ('ai_engineering', '### AI工程与工具', 10),
                ('practical_tutorials', '### AI实践教程', 8),
                ('ai_twitter', '### AI Twitter 热议', 6),
            ]

            for category_key, section_title, max_show in category_display:
                articles = ai_content.get(category_key, [])
                if articles:
                    report += f"{section_title}\n\n"
                    for idx, article in enumerate(articles[:max_show], 1):
                        title = article.get('title', '')
                        link = article.get('link', '')
                        summary = article.get('summary', '')
                        source_api = article.get('source_api', '')
                        author = article.get('author', '')

                        report += f"**{idx}. {title}**\n"
                        if author:
                            report += f"   作者：{author}\n"
                        if summary:
                            # 截断摘要到150字符
                            display_summary = summary[:150] + '...' if len(summary) > 150 else summary
                            report += f"   {display_summary}\n"
                        if link:
                            report += f"   🔗 {link}\n\n"
                        else:
                            report += "\n"

                    report += "\n"

            report += "---\n\n"

        # GitHub热门项目（简洁格式）
        if 'github' in evaluated_results and evaluated_results['github'].get('projects'):
            report += "## 💻 GitHub开源项目\n\n"

            for idx, project in enumerate(evaluated_results['github']['projects'][:8], 1):
                name = project.get('name', '')
                author = project.get('author', '')
                url = project.get('url', '')
                description = project.get('description', '')
                stars = project.get('stars', 0)
                language = project.get('language', '')

                # 格式化stars
                if stars >= 10000:
                    stars_display = f"{stars/1000:.1f}k"
                else:
                    stars_display = str(stars)

                # 简洁格式
                report += f"**{idx}. {author}/{name}**\n"
                if description:
                    report += f"   {description}\n"
                report += f"   ⭐ {stars_display}"
                if language:
                    report += f" | 📝 {language}"
                report += "\n"
                if url:
                    report += f"   🔗 {url}\n\n"
                else:
                    report += "\n"

        return report
