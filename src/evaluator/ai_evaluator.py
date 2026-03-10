"""
AI评估器 - 使用MiniMax API评估、排序和筛选内容
"""

import os
import json
import requests
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# 每批评估的最大文章数
BATCH_SIZE = 15


class MiniMaxEvaluator:
    """MiniMax AI评估器"""

    def __init__(self, api_key: str, group_id: str):
        self.api_key = api_key
        self.group_id = group_id
        self.base_url = "https://api.minimax.io/v1/text/chatcompletion_v2"

    # ------------------------------------------------------------------
    # 通用评估入口：适用于任何类型的文章列表
    # ------------------------------------------------------------------
    def evaluate_and_rank(
        self,
        articles: List[Dict],
        context: str = "AI Agent",
        max_output: int = 10,
        fetch_content: bool = False,
    ) -> List[Dict]:
        """
        通用评估：给文章打分、翻译标题、生成推荐语，按分数排序返回。

        Args:
            articles: 文章列表
            context: 评估上下文描述（如 "AI Agent官方博客", "Agent框架教程"）
            max_output: 最终返回的最大数量
            fetch_content: 是否抓取正文辅助评估
        """
        if not articles:
            return []

        # 可选：抓取正文
        if fetch_content:
            self._fetch_contents(articles[:10])

        # 分批评估
        all_evaluated = []
        for i in range(0, len(articles), BATCH_SIZE):
            batch = articles[i:i + BATCH_SIZE]
            evaluated_batch = self._evaluate_batch(batch, context)
            all_evaluated.extend(evaluated_batch)

        # 按分数降序排序
        all_evaluated.sort(key=lambda x: x.get('score', 0), reverse=True)

        return all_evaluated[:max_output]

    # ------------------------------------------------------------------
    # GitHub 项目专用评估
    # ------------------------------------------------------------------
    def evaluate_github_projects(
        self,
        projects: List[Dict],
        max_output: int = 8,
    ) -> List[Dict]:
        """评估GitHub项目的AI Agent相关性和价值"""
        if not projects:
            return []

        prompt = self._build_github_prompt(projects)

        try:
            response = self._call_minimax(prompt, max_tokens=2000)
            evaluated = self._parse_evaluation_results(response, projects)
            evaluated.sort(key=lambda x: x.get('score', 0), reverse=True)
            return evaluated[:max_output]
        except Exception as e:
            logger.error(f"Error evaluating GitHub projects: {e}")
            # 降级：按 stars 排序
            projects.sort(key=lambda x: x.get('stars', 0), reverse=True)
            for p in projects:
                p['score'] = 7
            return projects[:max_output]

    # ------------------------------------------------------------------
    # 内部：单批评估
    # ------------------------------------------------------------------
    def _evaluate_batch(self, articles: List[Dict], context: str) -> List[Dict]:
        """评估一批文章"""
        prompt = self._build_ranking_prompt(articles, context)

        try:
            response = self._call_minimax(prompt, max_tokens=3000)
            evaluated = self._parse_evaluation_results(response, articles)
            return evaluated
        except Exception as e:
            logger.error(f"Error evaluating batch ({context}): {e}")
            # 降级：给默认分数
            for article in articles:
                if 'score' not in article:
                    article['score'] = 6
            return articles

    def _build_ranking_prompt(self, articles: List[Dict], context: str) -> str:
        """构建通用排序评估 Prompt"""

        articles_text = ""
        for idx, article in enumerate(articles, 1):
            articles_text += f"\n{idx}. 标题: {article.get('title', '')}\n"
            source = article.get('source', '') or article.get('source_api', '')
            if source:
                articles_text += f"   来源: {source}\n"
            link = article.get('link', '')
            if link:
                articles_text += f"   链接: {link}\n"

            # 正文或摘要
            if 'full_content' in article:
                articles_text += f"   内容摘录: {article['full_content'][:800]}\n"
            else:
                summary = article.get('summary', '')
                if summary:
                    articles_text += f"   摘要: {summary[:300]}\n"

        prompt = f"""你是 AI Agent 领域资深专家和技术博客编辑。

**当前评估板块：{context}**

以下是待评估的文章列表：
{articles_text}

任务：
1. 评估每篇文章与 AI Agent 领域的相关性和价值（1-10分）
2. 将英文标题翻译为简洁的中文标题
3. 用1句话写出推荐理由（中文，像朋友推荐给你一样自然）

评分标准（从高到低）：
- 9-10分：直接关于 Agent 架构/框架/MCP/tool use/多智能体 的深度内容
- 7-8分：与 Agent 生态相关（LLM 新能力、API 更新、开发工具）
- 5-6分：泛 AI 内容，间接相关
- 1-4分：与 Agent 无关或低质量内容

返回JSON格式（只返回JSON，不要其他内容）：
{{
  "evaluations": [
    {{
      "index": 1,
      "score": 9,
      "title_cn": "中文标题",
      "recommendation": "一句话推荐理由"
    }}
  ]
}}"""
        return prompt

    def _build_github_prompt(self, projects: List[Dict]) -> str:
        """构建GitHub项目评估Prompt"""

        projects_text = ""
        for idx, project in enumerate(projects, 1):
            projects_text += f"\n{idx}. {project.get('author', '')}/{project.get('name', '')}\n"
            projects_text += f"   描述: {project.get('description', '')}\n"
            projects_text += f"   语言: {project.get('language', '')} | Stars: {project.get('stars', 0)}\n"

        prompt = f"""你是 AI Agent 领域技术专家，评估以下 GitHub 项目与 AI Agent 的相关性和价值。

{projects_text}

评分标准（1-10分）：
- 9-10: 核心 Agent 框架/MCP server/多智能体工具
- 7-8: Agent 生态相关（LLM 工具、RAG、向量数据库）
- 5-6: 泛 AI/ML 项目
- 1-4: 与 Agent 无关

返回JSON（只返回JSON）：
{{
  "evaluations": [
    {{"index": 1, "score": 9, "title_cn": "中文项目名或简述", "recommendation": "一句话推荐"}}
  ]
}}"""
        return prompt

    # ------------------------------------------------------------------
    # 内容抓取
    # ------------------------------------------------------------------
    def _fetch_contents(self, articles: List[Dict]):
        """尝试抓取文章正文"""
        try:
            from ..collectors.content_fetcher import ContentFetcher
            fetcher = ContentFetcher()

            for article in articles:
                url = article.get('link', '')
                if url:
                    content = fetcher.fetch_article_content(url, max_length=2000)
                    if content:
                        article['full_content'] = content
                        logger.info(f"Fetched content: {article.get('title', '')[:50]}")
                    elif article.get('summary'):
                        article['full_content'] = article['summary']
        except Exception as e:
            logger.error(f"Error fetching contents: {e}")

    # ------------------------------------------------------------------
    # MiniMax API 调用
    # ------------------------------------------------------------------
    def _call_minimax(
        self,
        prompt: str,
        max_tokens: int = 1500,
    ) -> str:
        """调用MiniMax API"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "M2-her",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "tokens_to_generate": max_tokens,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
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

    # ------------------------------------------------------------------
    # 解析 LLM 返回
    # ------------------------------------------------------------------
    def _parse_evaluation_results(
        self,
        response: str,
        original_items: List[Dict]
    ) -> List[Dict]:
        """解析评估结果并合并到原始数据"""

        try:
            response = response.strip()

            # 移除markdown代码块标记
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            # 找JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1:
                response = response[start_idx:end_idx + 1]

            data = json.loads(response)

            if isinstance(data, dict):
                evaluations = data.get('evaluations', [])
            elif isinstance(data, list):
                evaluations = data
            else:
                raise ValueError("Invalid data format")

            # 合并到原始数据
            for eval_item in evaluations:
                if not isinstance(eval_item, dict):
                    continue

                idx = eval_item.get('index', 0) - 1
                if 0 <= idx < len(original_items):
                    original_items[idx]['score'] = eval_item.get('score', 5)
                    if 'title_cn' in eval_item and eval_item['title_cn']:
                        original_items[idx]['title_cn'] = eval_item['title_cn']
                    if 'recommendation' in eval_item and eval_item['recommendation']:
                        original_items[idx]['recommendation'] = eval_item['recommendation']
                    if 'reason' in eval_item:
                        original_items[idx]['ai_reason'] = eval_item['reason']
                    if 'highlight' in eval_item:
                        original_items[idx]['highlight'] = eval_item['highlight']

            return original_items

        except Exception as e:
            logger.error(f"Error parsing evaluation results: {e}")
            logger.debug(f"Response was: {response[:200] if response else 'empty'}")

            # 解析失败，给默认分数
            for item in original_items:
                if 'score' not in item:
                    item['score'] = 6
            return original_items
