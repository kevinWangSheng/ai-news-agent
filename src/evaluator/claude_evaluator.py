"""
Claude 评估器 - 使用 Anthropic Claude Haiku 4.5 评估、翻译、排序 AI Agent 内容

为什么用 Claude:
- Agent 领域专业判断力更强（Anthropic 自家模型，对 MCP/tool use 语义理解好）
- prompt caching 能把系统指令缓存 5 分钟，多批次评估成本降一个数量级
- JSON 输出稳定，不易解析失败

接口与 MiniMaxEvaluator 保持一致:
- evaluate_and_rank(articles, context, max_output, fetch_content)
- evaluate_github_projects(projects, max_output)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BATCH_SIZE = 15
DEFAULT_MODEL = "claude-haiku-4-5"

# 系统指令 — 打到 cache_control，重复调用只付第一次 cache write，后续只付 cache hit
EVAL_SYSTEM_PROMPT = """你是 AI Agent 领域的资深技术编辑，熟悉 LLM、Agent 框架（LangChain/CrewAI/AutoGen/LangGraph/LlamaIndex）、协议（MCP、tool use、function calling）、多智能体架构。

你的任务是评估一批候选内容，为每条打分并生成简短中文标题和推荐语。

评分标准（1-10 分，严格区分）:
- 10: Agent 生态里程碑级事件（新模型发布、重大协议/框架版本、重要 paper）
- 9:  Agent 核心主题深度内容（MCP、多智能体、tool use、agent 架构、LLM 工程）
- 8:  Agent 生态相关（LLM 能力更新、API/SDK 重要变化、Agent 评测）
- 7:  泛 LLM / RAG / 向量检索等 Agent 上下游相关技术
- 5-6: 泛 AI 新闻，间接相关
- 1-4: 与 Agent 基本无关（纯图像生成、娱乐、商业八卦、招聘稿等）

加权线索:
- 来自 OpenAI/Anthropic/Google/Meta/Mistral/xAI/DeepSeek 官方发布: +1
- 出现 "released"、"announcing"、"launches"、"introduce"、"发布"、"推出" 等发布动词: +1
- Simon Willison / Karpathy / Chip Huyen / Hamel Husain / swyx 等实战派作者: +1

翻译规则:
- 原文是中文则保留，去掉多余空格和 emoji
- 英文标题翻译成简洁自然的中文（≤ 25 个字）
- 产品名/公司名/术语保留英文（Claude、OpenAI、LangChain、MCP 等）

推荐语规则:
- ≤ 30 字，像给技术朋友的一句话推荐
- 讲清"这篇讲了什么、为什么值得看"，不要套话
- 示例："Anthropic 首次披露 tool use 自我纠错机制，做 Agent 必看"

严格输出 JSON，不要任何解释文字:
{
  "evaluations": [
    {"index": 1, "score": 9, "title_cn": "...", "recommendation": "..."}
  ]
}"""


GITHUB_SYSTEM_PROMPT = """你是 AI Agent 领域的开源项目评审专家。

评分标准（1-10）:
- 10: 核心 Agent 框架（LangChain/CrewAI/AutoGen/LangGraph/AutoGPT 级别）
- 9:  MCP server、agent 工具链、多智能体核心项目
- 8:  Agent 周边（工具、评测、UI、memory/RAG 基础设施）
- 6-7: 泛 LLM 应用或工具
- 1-5: 与 Agent 无关

title_cn ≤ 15 字；recommendation ≤ 25 字。

严格 JSON 输出:
{
  "evaluations": [
    {"index": 1, "score": 9, "title_cn": "...", "recommendation": "..."}
  ]
}"""


class ClaudeEvaluator:
    """基于 Claude Haiku 4.5 的评估器 (兼容 MiniMaxEvaluator 接口)"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[Dict] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for ClaudeEvaluator")

        self.config = config or {}
        eval_config = self.config.get("evaluation", {})
        self.model = model or eval_config.get("claude_model") or DEFAULT_MODEL

        # 初始化 SDK（延迟导入，避免没装 anthropic 时主流程完全跑不起来）
        from anthropic import Anthropic
        self._client = Anthropic(api_key=self.api_key)

        # 统计
        self._stats = {"batches": 0, "ok": 0, "failed": 0}

    # ------------------------------------------------------------------
    # 通用评估入口
    # ------------------------------------------------------------------
    def evaluate_and_rank(
        self,
        articles: List[Dict],
        context: str = "AI Agent",
        max_output: int = 10,
        fetch_content: bool = False,
    ) -> List[Dict]:
        if not articles:
            return []

        if fetch_content:
            self._fetch_contents(articles[:10])

        all_evaluated: List[Dict] = []
        for i in range(0, len(articles), BATCH_SIZE):
            batch = articles[i : i + BATCH_SIZE]
            all_evaluated.extend(self._evaluate_batch(batch, context))

        all_evaluated.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_evaluated[:max_output]

    # ------------------------------------------------------------------
    # GitHub 项目评估
    # ------------------------------------------------------------------
    def evaluate_github_projects(
        self,
        projects: List[Dict],
        max_output: int = 8,
    ) -> List[Dict]:
        if not projects:
            return []

        user_prompt = self._build_github_user_prompt(projects)
        try:
            raw = self._call_claude(GITHUB_SYSTEM_PROMPT, user_prompt, max_tokens=2000)
            evaluated = self._parse_evaluation_results(raw, projects)
            evaluated.sort(key=lambda x: x.get("score", 0), reverse=True)
            return evaluated[:max_output]
        except Exception as exc:
            logger.error(f"ClaudeEvaluator: GitHub evaluation failed: {exc}")
            projects.sort(key=lambda x: x.get("stars", 0), reverse=True)
            for p in projects:
                p.setdefault("score", 7)
            return projects[:max_output]

    # ------------------------------------------------------------------
    # 单批评估
    # ------------------------------------------------------------------
    def _evaluate_batch(self, articles: List[Dict], context: str) -> List[Dict]:
        user_prompt = self._build_ranking_user_prompt(articles, context)
        self._stats["batches"] += 1
        try:
            raw = self._call_claude(EVAL_SYSTEM_PROMPT, user_prompt, max_tokens=3000)
            result = self._parse_evaluation_results(raw, articles)
            self._stats["ok"] += 1
            return result
        except Exception as exc:
            self._stats["failed"] += 1
            logger.error(f"ClaudeEvaluator: batch eval failed ({context}): {exc}")
            for a in articles:
                a.setdefault("score", 6)
            return articles

    # ------------------------------------------------------------------
    # Prompt 构造
    # ------------------------------------------------------------------
    def _build_ranking_user_prompt(self, articles: List[Dict], context: str) -> str:
        lines = [f"当前板块: {context}", "", "待评估内容:"]
        for idx, art in enumerate(articles, 1):
            lines.append(f"\n[{idx}] 标题: {art.get('title', '')}")
            src = art.get("source") or art.get("source_api") or ""
            if src:
                lines.append(f"    来源: {src}")
            author = art.get("author", "")
            if author:
                lines.append(f"    作者: {author}")
            link = art.get("link", "")
            if link:
                lines.append(f"    链接: {link}")
            body = art.get("full_content") or art.get("summary") or ""
            if body:
                lines.append(f"    摘要: {str(body)[:300]}")
        lines.append("")
        lines.append("输出 JSON (严格按照 index 对应):")
        return "\n".join(lines)

    def _build_github_user_prompt(self, projects: List[Dict]) -> str:
        lines = ["待评估 GitHub 项目:"]
        for idx, p in enumerate(projects, 1):
            lines.append(
                f"\n[{idx}] {p.get('author', '')}/{p.get('name', '')}"
                f"  ({p.get('language', '')}, ★{p.get('stars', 0)})"
            )
            desc = p.get("description", "")
            if desc:
                lines.append(f"    描述: {desc[:200]}")
        lines.append("")
        lines.append("输出 JSON:")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Claude API 调用（带 prompt caching）
    # ------------------------------------------------------------------
    def _call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
    ) -> str:
        # system 放 cache_control，下次调用命中缓存只付 10% token 费
        system_blocks = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_blocks,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # 兼容多段 content
        parts = []
        for block in response.content:
            if getattr(block, "type", "") == "text":
                parts.append(block.text)
        text = "".join(parts).strip()

        usage = getattr(response, "usage", None)
        if usage is not None:
            logger.debug(
                "Claude usage: in=%s out=%s cache_read=%s cache_write=%s",
                getattr(usage, "input_tokens", 0),
                getattr(usage, "output_tokens", 0),
                getattr(usage, "cache_read_input_tokens", 0),
                getattr(usage, "cache_creation_input_tokens", 0),
            )

        if not text:
            raise RuntimeError("Claude returned empty content")
        return text

    # ------------------------------------------------------------------
    # JSON 解析（容错）
    # ------------------------------------------------------------------
    def _parse_evaluation_results(
        self,
        response: str,
        original_items: List[Dict],
    ) -> List[Dict]:
        try:
            text = response.strip()
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # 找第一个 { 到最后一个 }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]

            data = json.loads(text)

            if isinstance(data, dict):
                evaluations = data.get("evaluations", [])
            elif isinstance(data, list):
                evaluations = data
            else:
                raise ValueError("Unexpected JSON root")

            for item in evaluations:
                if not isinstance(item, dict):
                    continue
                idx = item.get("index", 0) - 1
                if 0 <= idx < len(original_items):
                    original_items[idx]["score"] = item.get("score", 5)
                    if item.get("title_cn"):
                        original_items[idx]["title_cn"] = item["title_cn"]
                    if item.get("recommendation"):
                        original_items[idx]["recommendation"] = item["recommendation"]

            # 没拿到分的条目给默认值，保留 pipeline 正常
            for art in original_items:
                art.setdefault("score", 6)
            return original_items

        except Exception as exc:
            logger.error(f"ClaudeEvaluator: parse failed: {exc}")
            logger.debug(f"Raw response: {response[:400]}")
            for art in original_items:
                art.setdefault("score", 6)
            return original_items

    # ------------------------------------------------------------------
    # 可选：抓取正文（复用旧 ContentFetcher）
    # ------------------------------------------------------------------
    def _fetch_contents(self, articles: List[Dict]) -> None:
        try:
            from ..collectors.content_fetcher import ContentFetcher
            fetcher = ContentFetcher()
            for art in articles:
                url = art.get("link", "")
                if not url:
                    continue
                content = fetcher.fetch_article_content(url, max_length=2000)
                if content:
                    art["full_content"] = content
                elif art.get("summary"):
                    art["full_content"] = art["summary"]
        except Exception as exc:
            logger.error(f"ClaudeEvaluator: content fetch failed: {exc}")

    # ------------------------------------------------------------------
    # 运行统计（orchestrator 末尾打印）
    # ------------------------------------------------------------------
    def stats(self) -> Dict[str, int]:
        return dict(self._stats)
