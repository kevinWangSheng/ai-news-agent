"""Process-wide LLM client singletons. Prompt cache requires shared client.

004 enricher / 005 scoring / 011 digest MUST go through get_claude() / get_voyage().
"""
from functools import lru_cache

from app.config import get_settings


@lru_cache(maxsize=1)
def get_claude():
    import anthropic

    s = get_settings()
    return anthropic.AsyncAnthropic(api_key=s.anthropic_api_key)


@lru_cache(maxsize=1)
def get_voyage():
    import voyageai

    s = get_settings()
    return voyageai.AsyncClient(api_key=s.voyage_api_key)


@lru_cache(maxsize=1)
def get_openai():
    import openai

    s = get_settings()
    return openai.AsyncOpenAI(api_key=s.openai_api_key)


@lru_cache(maxsize=1)
def get_ark():
    """ARK (火山方舟) embedding client — OpenAI-compatible API."""
    import openai

    s = get_settings()
    return openai.AsyncOpenAI(api_key=s.ark_api_key, base_url=s.ark_base_url)
