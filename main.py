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

    # 检查必需的环境变量
    required_vars = ['MINIMAX_API_KEY', 'EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECEIVER']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please create a .env file with all required variables")
        logger.error("For Gmail, you need an App Password: https://myaccount.google.com/apppasswords")
        sys.exit(1)

    # 检查可选的搜索API环境变量
    optional_search_vars = ['TAVILY_API_KEY', 'EXA_API_KEY']
    available_search = [var for var in optional_search_vars if os.getenv(var)]
    if available_search:
        logger.info(f"Search APIs available: {', '.join(available_search)}")
    else:
        logger.warning("No search API keys found (TAVILY_API_KEY, EXA_API_KEY). AI content search will be skipped.")

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
