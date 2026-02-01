"""
内容抓取器 - 访问URL获取文章正文
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ContentFetcher:
    """网页内容抓取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_article_content(self, url: str, max_length: int = 3000) -> Optional[str]:
        """
        抓取文章正文内容

        Args:
            url: 文章URL
            max_length: 最大内容长度（避免太长）

        Returns:
            文章正文，失败返回None
        """
        try:
            logger.info(f"Fetching content from: {url[:50]}...")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # 使用BeautifulSoup解析
            soup = BeautifulSoup(response.content, 'html.parser')

            # 移除脚本和样式
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # 尝试提取主要内容
            content = self._extract_main_content(soup)

            if content:
                # 限制长度
                content = content[:max_length]
                logger.info(f"Extracted {len(content)} characters from article")
                return content
            else:
                logger.warning(f"Could not extract content from {url}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None

    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[str]:
        """
        从HTML中提取主要内容

        尝试多种策略找到文章正文
        """
        # 策略1: 查找常见的文章容器
        article_tags = [
            ('article', {}),
            ('div', {'class': ['post-content', 'article-content', 'entry-content', 'main-content']}),
            ('div', {'id': ['content', 'main', 'article']}),
            ('main', {}),
        ]

        for tag_name, attrs in article_tags:
            if attrs:
                for attr_name, attr_values in attrs.items():
                    for attr_value in attr_values:
                        element = soup.find(tag_name, {attr_name: lambda x: x and attr_value in str(x).lower()})
                        if element:
                            text = element.get_text(separator='\n', strip=True)
                            if len(text) > 200:  # 至少200字符
                                return text
            else:
                element = soup.find(tag_name)
                if element:
                    text = element.get_text(separator='\n', strip=True)
                    if len(text) > 200:
                        return text

        # 策略2: 查找所有段落
        paragraphs = soup.find_all('p')
        if paragraphs and len(paragraphs) > 3:
            text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
            if len(text) > 200:
                return text

        # 策略3: 整个body
        body = soup.find('body')
        if body:
            text = body.get_text(separator='\n', strip=True)
            # 清理多余空行
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            return text

        return None

    def fetch_multiple_articles(self, urls: list, max_concurrent: int = 3) -> dict:
        """
        批量抓取多篇文章

        Args:
            urls: URL列表
            max_concurrent: 最大并发数

        Returns:
            字典 {url: content}
        """
        results = {}

        for url in urls[:max_concurrent]:  # 限制数量避免太慢
            content = self.fetch_article_content(url)
            if content:
                results[url] = content

        return results
