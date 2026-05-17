"""
AI Agent 技术博客聚合系统 - 主入口
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator import NewsOrchestrator


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('news_agent.log', encoding='utf-8')
        ]
    )


async def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("AI Agent Blog Aggregation System Starting...")

    # 评估器至少得有一个 key
    if not (os.getenv('ANTHROPIC_API_KEY') or os.getenv('MINIMAX_API_KEY')):
        logger.error("Missing evaluator API key: set ANTHROPIC_API_KEY (recommended) or MINIMAX_API_KEY")
        sys.exit(1)

    # 邮件通知 optional 化（没配置也不 sys.exit，保留跑报告 + 落地本地文件的能力）
    email_vars = ['EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECEIVER']
    missing_email = [v for v in email_vars if not os.getenv(v)]
    if missing_email:
        logger.warning(
            f"Email not configured ({', '.join(missing_email)}) — 报告仍会生成到 output/daily_report.md 但不发邮件"
        )

    # 搜索 API 诊断（breaking_news 依赖 Exa/Tavily 时效搜索）
    search_keys = [v for v in ('TAVILY_API_KEY', 'EXA_API_KEY') if os.getenv(v)]
    if search_keys:
        logger.info(f"Search APIs available: {', '.join(search_keys)}")
    else:
        logger.warning(
            "未配置 TAVILY_API_KEY / EXA_API_KEY — breaking_news 只能走 RSS 通道，"
            "建议补全以抓'今日发布'"
        )

    # 配置文件路径
    config_path = Path(__file__).parent / 'config' / 'config.yaml'

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    try:
        # 创建并运行orchestrator
        orchestrator = NewsOrchestrator(str(config_path))
        success = await orchestrator.run()

        if success:
            logger.info("AI Agent blog aggregation completed successfully!")
            sys.exit(0)
        else:
            logger.error("AI Agent blog aggregation failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
