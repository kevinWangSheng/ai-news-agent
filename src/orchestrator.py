"""
主控制器 - 协调所有Agent并行工作（AI Agent技术博客聚合版）
"""

import asyncio
import logging
import os
from typing import Dict, Any, List
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

            # 第二步：AI评估、排序和筛选
            logger.info("\n[Step 2] AI evaluating and ranking content...")
            evaluated_results = await self._evaluate_all_content(all_results)

            # 第三步：生成日报
            logger.info("\n[Step 3] Generating daily report...")
            report = self._generate_report(evaluated_results)

            # 保存报告
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

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

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
                for sub, items in data.items():
                    if isinstance(items, list):
                        total_items += len(items)
        logger.info(f"Total items collected: {total_items}")

        return all_results

    # ------------------------------------------------------------------
    # 核心：所有板块过 LLM 评估 + 排序
    # ------------------------------------------------------------------
    async def _evaluate_all_content(self, all_results: Dict) -> Dict:
        """用 LLM 对所有内容评分、翻译、排序"""

        evaluated = {}

        # ---- 1. 官方博客 + 专家博客 ----
        if 'tech' in all_results and all_results['tech']:
            tech_data = all_results['tech']

            official = tech_data.get('official_blogs', [])
            expert = tech_data.get('expert_blogs', [])
            logger.info(f"Evaluating tech: {len(official)} official + {len(expert)} expert blogs")

            evaluated_official = self.evaluator.evaluate_and_rank(
                articles=official,
                context="AI Agent 官方博客（来自 Anthropic/OpenAI/LangChain/Google 等）",
                max_output=12,
                fetch_content=False,
            )

            evaluated_expert = self.evaluator.evaluate_and_rank(
                articles=expert,
                context="AI 领域专家博客（Simon Willison/Karpathy/Lilian Weng 等）",
                max_output=5,
                fetch_content=False,
            )

            evaluated['tech'] = {
                'official': evaluated_official,
                'expert': evaluated_expert,
            }

        # ---- 2. AI Agent 框架/协议/工作流 ----
        if 'ai_content' in all_results and all_results['ai_content']:
            ai_data = all_results['ai_content']
            evaluated['ai_content'] = {}

            section_map = {
                'agent_frameworks': ("Agent 框架教程（LangChain/CrewAI/AutoGen）", 8),
                'agent_protocols': ("Agent 协议与工具集成（MCP/Function Calling）", 8),
                'agentic_workflows': ("Agentic Workflow / 多智能体架构", 8),
                'agent_twitter': ("AI Agent Twitter/X 动态", 5),
                'agent_chinese': ("中文 AI Agent 内容", 8),
            }

            for category, (context, max_out) in section_map.items():
                articles = ai_data.get(category, [])
                if articles:
                    logger.info(f"Evaluating ai_content/{category}: {len(articles)} articles")
                    ranked = self.evaluator.evaluate_and_rank(
                        articles=articles,
                        context=context,
                        max_output=max_out,
                    )
                    evaluated['ai_content'][category] = ranked

        # ---- 3. 中文平台 ----
        if 'chinese_platform' in all_results and all_results['chinese_platform']:
            cn_data = all_results['chinese_platform']
            # 合并所有平台文章一起评估
            all_cn_articles = []
            for platform, articles in cn_data.items():
                for a in articles:
                    a['platform'] = platform  # 保留来源平台
                all_cn_articles.extend(articles)

            if all_cn_articles:
                logger.info(f"Evaluating chinese_platform: {len(all_cn_articles)} articles")
                ranked = self.evaluator.evaluate_and_rank(
                    articles=all_cn_articles,
                    context="中文技术社区 AI Agent 内容（掘金/知乎/CSDN）",
                    max_output=10,
                )
                evaluated['chinese_platform'] = ranked

        # ---- 4. GitHub 项目 ----
        if 'github' in all_results and all_results['github']:
            github_data = all_results['github']
            all_projects = []
            all_projects.extend(github_data.get('trending', []))
            all_projects.extend(github_data.get('ai_projects', []))

            if all_projects:
                logger.info(f"Evaluating github: {len(all_projects)} projects")
                ranked = self.evaluator.evaluate_github_projects(
                    projects=all_projects,
                    max_output=8,
                )
                evaluated['github'] = ranked

        return evaluated

    # ------------------------------------------------------------------
    # 报告生成（展示 LLM 推荐语 + 按分数排序后的结果）
    # ------------------------------------------------------------------
    def _generate_report(self, evaluated_results: Dict) -> str:
        """生成最终报告"""
        logger.info("Generating report from evaluated results...")
        return self._generate_template_report(evaluated_results)

    def _generate_template_report(self, evaluated_results: Dict) -> str:
        """生成AI Agent技术博客日报"""

        report = ""

        # === 1. AI Agent 官方博客与专家动态 ===
        tech = evaluated_results.get('tech', {})
        official = tech.get('official', [])
        expert = tech.get('expert', [])

        if official or expert:
            report += "## AI Agent 官方博客与专家动态\n\n"

            if official:
                report += "### 官方博客\n\n"
                report += self._render_articles(official, show_source=True, show_score=True)

            if expert:
                report += "### 专家博客\n\n"
                report += self._render_articles(expert, show_source=True)

            report += "---\n\n"

        # === 2. AI Agent 框架与工具 ===
        ai_content = evaluated_results.get('ai_content', {})
        frameworks = ai_content.get('agent_frameworks', [])
        protocols = ai_content.get('agent_protocols', [])
        workflows = ai_content.get('agentic_workflows', [])

        if frameworks or protocols or workflows:
            report += "## AI Agent 框架与工具\n\n"

            if frameworks:
                report += "### Agent 框架教程\n\n"
                report += self._render_articles(frameworks)

            if protocols:
                report += "### 协议与工具集成 (MCP / Function Calling)\n\n"
                report += self._render_articles(protocols)

            if workflows:
                report += "### Agentic Workflow\n\n"
                report += self._render_articles(workflows)

            report += "---\n\n"

        # === 3. GitHub Agent 开源项目 ===
        github_projects = evaluated_results.get('github', [])
        if github_projects:
            report += "## GitHub Agent 开源项目\n\n"

            for idx, project in enumerate(github_projects, 1):
                name = project.get('name', '')
                author = project.get('author', '')
                url = project.get('url', '')
                description = project.get('description', '')
                stars = project.get('stars', 0)
                language = project.get('language', '')
                score = project.get('score', 0)
                title_cn = project.get('title_cn', '')
                recommendation = project.get('recommendation', '')

                stars_display = f"{stars/1000:.1f}k" if stars >= 10000 else str(stars)

                report += f"**{idx}. {author}/{name}**"
                if score:
                    report += f" `{score}/10`"
                report += "\n"

                if title_cn:
                    report += f"   {self._truncate(title_cn, 40)}\n"
                elif description:
                    report += f"   {self._truncate(description, 80)}\n"
                if recommendation:
                    report += f"   > {self._truncate(recommendation, 50)}\n"
                report += f"   Stars: {stars_display}"
                if language:
                    report += f" | {language}"
                report += "\n"
                if url:
                    report += f"   {url}\n\n"

            report += "---\n\n"

        # === 4. 中文社区 Agent 动态 ===
        cn_articles = evaluated_results.get('chinese_platform', [])
        if cn_articles:
            report += "## 中文社区 Agent 动态\n\n"
            report += self._render_articles(cn_articles, show_platform=True)
            report += "---\n\n"

        # === 5. AI Agent 中文精选（搜索API发现） ===
        agent_chinese = ai_content.get('agent_chinese', [])
        if agent_chinese:
            report += "## AI Agent 中文精选\n\n"
            report += self._render_articles(agent_chinese)
            report += "---\n\n"

        # === 6. AI Agent Twitter/X 热议 ===
        twitter = ai_content.get('agent_twitter', [])
        if twitter:
            report += "## AI Agent Twitter/X 热议\n\n"
            report += self._render_articles(twitter, show_author=True)

        return report

    # ------------------------------------------------------------------
    # 渲染文章列表的通用方法
    # ------------------------------------------------------------------
    def _render_articles(
        self,
        articles: List[Dict],
        show_source: bool = False,
        show_score: bool = False,
        show_author: bool = False,
        show_platform: bool = False,
    ) -> str:
        """渲染文章列表为 Markdown"""
        text = ""
        for idx, article in enumerate(articles, 1):
            title_original = article.get('title', '')
            title_cn = article.get('title_cn', '')
            link = article.get('link', '')
            score = article.get('score', 0)
            recommendation = article.get('recommendation', '')
            source = article.get('source', '')
            author = article.get('author', '')
            platform = article.get('platform', '') or article.get('source', '')

            # 标题：优先中文，截断保护
            display_title = self._truncate(title_cn or title_original, 60)
            text += f"**{idx}. {display_title}**"
            if show_score and score:
                text += f" `{score}/10`"
            text += "\n"

            # 来源信息（一行）
            meta_parts = []
            if show_source and source:
                meta_parts.append(f"来源：{source}")
            if show_platform and platform:
                meta_parts.append(f"平台：{platform}")
            if show_author and author:
                meta_parts.append(f"作者：{author}")
            if meta_parts:
                text += f"   {' | '.join(meta_parts)}\n"

            # 推荐语（严格截断）
            if recommendation:
                rec = self._truncate(recommendation, 60)
                text += f"   > {rec}\n"

            # 链接
            if link:
                text += f"   {link}\n"

            text += "\n"

        return text

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        """截断文本，去除换行"""
        text = text.replace('\n', ' ').replace('\r', '').strip()
        if len(text) > max_len:
            return text[:max_len] + '...'
        return text
