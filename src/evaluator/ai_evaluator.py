"""
AI评估器 - 使用MiniMax API评估和筛选内容
"""

import os
import json
import requests
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MiniMaxEvaluator:
    """MiniMax AI评估器"""

    def __init__(self, api_key: str, group_id: str):
        self.api_key = api_key
        self.group_id = group_id
        self.base_url = "https://api.minimax.io/v1/text/chatcompletion_v2"

    def evaluate_tech_articles(
        self,
        articles: List[Dict],
        criteria: Dict,
        fetch_content: bool = True
    ) -> List[Dict]:
        """
        评估AI科技文章（深度分析）

        Args:
            articles: 文章列表
            criteria: 评估标准
            fetch_content: 是否抓取文章正文进行深度分析
        """

        if not articles:
            return []

        # 准备深度分析内容
        if fetch_content:
            from ..collectors.content_fetcher import ContentFetcher
            fetcher = ContentFetcher()

            # 尝试抓取前5篇文章内容
            for article in articles[:5]:
                url = article.get('link', '')
                if url:
                    # 尝试抓取完整内容
                    content = fetcher.fetch_article_content(url, max_length=2000)
                    if content:
                        article['full_content'] = content
                        logger.info(f"Fetched full content for: {article.get('title', '')[:50]}")
                    elif article.get('summary'):
                        # 如果抓取失败，使用RSS摘要
                        article['full_content'] = article.get('summary', '')
                        logger.info(f"Using RSS summary for: {article.get('title', '')[:50]}")

        prompt = self._build_tech_evaluation_prompt(articles, criteria)

        try:
            response = self._call_minimax(prompt, max_tokens=3000)
            evaluated = self._parse_evaluation_results(response, articles)

            threshold = criteria.get('importance_threshold', 7)
            filtered = [
                article for article in evaluated
                if article.get('score', 0) >= threshold
            ]

            filtered.sort(key=lambda x: x.get('score', 0), reverse=True)
            return filtered

        except Exception as e:
            logger.error(f"Error evaluating tech articles: {e}")
            return articles[:5]

    def evaluate_github_projects(
        self,
        projects: List[Dict],
        criteria: Dict
    ) -> List[Dict]:
        """评估GitHub项目"""

        if not projects:
            return []

        prompt = self._build_github_evaluation_prompt(projects, criteria)

        try:
            response = self._call_minimax(prompt)
            evaluated = self._parse_evaluation_results(response, projects)

            threshold = criteria.get('importance_threshold', 6)
            filtered = [
                project for project in evaluated
                if project.get('score', 0) >= threshold
            ]

            filtered.sort(key=lambda x: x.get('score', 0), reverse=True)
            return filtered

        except Exception as e:
            logger.error(f"Error evaluating GitHub projects: {e}")
            return projects[:8]

    def generate_summary(
        self,
        all_results: Dict[str, Any]
    ) -> str:
        """
        生成最终的日报摘要

        Args:
            all_results: 包含所有地区和主题的结果

        Returns:
            格式化的Markdown日报
        """
        prompt = f"""
你是一个专业的AI Agent领域编辑，负责生成每日AI Agent技术博客精选。

以下是今天收集到的AI Agent相关博客、框架教程和GitHub项目：

{json.dumps(all_results, ensure_ascii=False, indent=2)}

请生成一份简洁、专业的日报，要求：

1. 使用Markdown格式
2. 分为以下几个部分：
   - AI Agent 官方博客与专家动态
   - AI Agent 框架与工具
   - GitHub Agent 开源项目
   - 中文社区 Agent 动态
3. 每条内容只用1-2句话概括核心内容
4. 标注信息来源
5. 突出与Agent架构、tool use、MCP等的关联
6. 总长度控制在800字以内

开始生成日报：
"""

        try:
            response = self._call_minimax(prompt, max_tokens=2000)
            return response

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "生成摘要失败，请查看详细数据。"

    def _build_tech_evaluation_prompt(
        self,
        articles: List[Dict],
        criteria: Dict
    ) -> str:
        """构建科技文章评估Prompt（深度分析版）"""

        articles_text = ""
        for idx, article in enumerate(articles, 1):
            articles_text += f"\n{idx}. 标题: {article.get('title', '')}\n"
            articles_text += f"   来源: {article.get('source', '')}\n"
            articles_text += f"   链接: {article.get('link', '')}\n"

            # 如果有完整内容，添加到prompt
            if 'full_content' in article:
                content_preview = article['full_content'][:1000]  # 前1000字
                articles_text += f"   内容摘录:\n   {content_preview}\n"
            else:
                summary = article.get('summary', '')
                if summary:
                    articles_text += f"   简介: {summary[:200]}\n"

        prompt = f"""
你是AI Agent领域资深专家，负责深度评估AI Agent相关文章的价值并生成友好的推荐语。

以下是待评估的AI科技文章：

{articles_text}

任务：
1. 评估技术价值（1-10分）：创新性、实用性、影响力
2. 生成吸引人的中文推荐语（1-2句话，拟人化、友好）
3. 提取核心亮点（技术突破/应用场景/重要观点）

评估标准：
- 优先关注：Agent架构、tool use、MCP、多智能体、框架更新
- 降低分数：营销软文、无实质内容、与Agent无关的内容
- 特别重视：来自LangChain、Anthropic、OpenAI等Agent领域厂商的官方博客

返回JSON格式：
{{
  "evaluations": [
    {{
      "index": 1,
      "score": 9,
      "title_cn": "中文标题（如果是英文则翻译）",
      "highlight": "核心亮点（一句话）",
      "recommendation": "友好的推荐语，告诉读者为什么值得读",
      "reason": "评分理由"
    }}
  ]
}}

要求：
- recommendation要拟人化、有趣，像朋友推荐一样
- 避免官方、生硬的语言
- 突出文章的实际价值

只返回JSON，不要其他内容。
"""
        return prompt

    def _build_github_evaluation_prompt(
        self,
        projects: List[Dict],
        criteria: Dict
    ) -> str:
        """构建GitHub项目评估Prompt"""

        projects_text = ""
        for idx, project in enumerate(projects, 1):
            projects_text += f"\n{idx}. 名称: {project.get('name', '')}\n"
            projects_text += f"   作者: {project.get('author', '')}\n"
            projects_text += f"   描述: {project.get('description', '')}\n"
            projects_text += f"   语言: {project.get('language', '')}\n"
            projects_text += f"   Stars: {project.get('stars', 0)}\n"

        prompt = f"""
你是技术专家，评估以下GitHub项目的价值：

{projects_text}

评估标准（1-10分）：
1. 创新性
2. 实用价值
3. 代码质量（根据stars/forks判断）
4. 项目成熟度

返回JSON格式：
{{
  "evaluations": [
    {{"index": 1, "score": 8, "reason": "创新的AI工具"}},
    ...
  ]
}}
"""
        return prompt

    def _call_minimax(
        self,
        prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.7
    ) -> str:
        """调用MiniMax API"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "M2-her",  # MiniMax模型
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "tokens_to_generate": max_tokens,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return content
            else:
                logger.error(f"MiniMax API error: {response.status_code} - {response.text}")
                raise Exception(f"API call failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Error calling MiniMax API: {e}")
            raise

    def _parse_evaluation_results(
        self,
        response: str,
        original_items: List[Dict]
    ) -> List[Dict]:
        """解析评估结果并合并到原始数据"""

        try:
            # 提取JSON部分
            response = response.strip()

            # 移除markdown代码块标记
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]

            if response.endswith("```"):
                response = response[:-3]

            response = response.strip()

            # 尝试找到JSON对象的开始和结束
            start_idx = response.find('{')
            end_idx = response.rfind('}')

            if start_idx != -1 and end_idx != -1:
                response = response[start_idx:end_idx+1]

            data = json.loads(response)

            # 处理evaluations字段
            if isinstance(data, dict):
                evaluations = data.get('evaluations', [])
            elif isinstance(data, list):
                evaluations = data
            else:
                raise ValueError("Invalid data format")

            # 合并评分和翻译到原始数据
            for eval_item in evaluations:
                if not isinstance(eval_item, dict):
                    continue

                idx = eval_item.get('index', 0) - 1
                if 0 <= idx < len(original_items):
                    original_items[idx]['score'] = eval_item.get('score', 5)
                    original_items[idx]['ai_reason'] = eval_item.get('reason', '')

                    # 添加翻译和摘要
                    if 'title_cn' in eval_item:
                        original_items[idx]['title_cn'] = eval_item.get('title_cn', '')
                    if 'summary_cn' in eval_item:
                        original_items[idx]['summary_cn'] = eval_item.get('summary_cn', '')

                    # 添加新字段：核心亮点和推荐语
                    if 'highlight' in eval_item:
                        original_items[idx]['highlight'] = eval_item.get('highlight', '')
                    if 'recommendation' in eval_item:
                        original_items[idx]['recommendation'] = eval_item.get('recommendation', '')

            return original_items

        except Exception as e:
            logger.error(f"Error parsing evaluation results: {e}")
            logger.debug(f"Response was: {response[:200]}")

            # 解析失败，给所有项目默认分数
            for item in original_items:
                if 'score' not in item:
                    item['score'] = 6  # 默认及格分
                if 'ai_reason' not in item:
                    item['ai_reason'] = 'AI evaluation failed'

            return original_items
