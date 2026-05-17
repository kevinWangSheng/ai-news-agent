"""Ingestion CLI: `python -m app.ingestion.run <source|all>`.

Iterates configured sources, calls fetch(), persists via IngestionService,
records errors but never bubbles them out so one source's failure can't kill the run.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from typing import Sequence

import yaml

from app.config import get_settings
from app.db.session import get_session_factory
from app.ingestion.base import Source
from app.ingestion.service import IngestionService
from app.ingestion.sources.chinese import ChineseSource
from app.ingestion.sources.exa_search import ExaSearchSource
from app.ingestion.sources.github import GitHubSource
from app.ingestion.sources.rss import build_rss_sources
from app.ingestion.sources.twitter import TwitterSource

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def load_config() -> dict:
    from pathlib import Path

    cfg_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))


def load_topics() -> dict:
    from pathlib import Path

    p = Path(__file__).resolve().parent.parent.parent / "topics.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def build_sources(cfg: dict, topics: dict) -> dict[str, list[Source]]:
    rss = build_rss_sources(cfg)

    gh_topics = [t["slug"] for t in topics["topics"]][:10]
    github = [GitHubSource(topics=gh_topics)]

    exa_sites = []
    exa_keywords = []
    for t in topics["topics"]:
        exa_sites += t.get("site_queries", []) or []
        exa_keywords += t.get("keywords_en", []) or []
    exa = [ExaSearchSource(site_queries=exa_sites, keyword_queries=exa_keywords[:20])]

    tw_cfg = cfg.get("twitter", {})
    twitter = [
        TwitterSource(
            kol_accounts=tw_cfg.get("kol_accounts", []),
            official_accounts=tw_cfg.get("official_accounts", []),
            topic_queries=[
                q for t in topics["topics"] for q in (t.get("kol_topic_queries") or [])
            ][:8],
        )
    ]

    cn_keywords = []
    for t in topics["topics"]:
        cn_keywords += t.get("keywords_zh", []) or []
    chinese = [ChineseSource(keywords=cn_keywords[:10])]

    return {
        "rss": rss,
        "github": github,
        "exa_search": exa,
        "twitter": twitter,
        "chinese": chinese,
    }


async def run_source(source: Source) -> tuple[int, int, int]:
    """Returns (fetched, created, deduped)."""
    factory = get_session_factory()
    try:
        raws = await source.fetch()
    except Exception as exc:
        logger.exception("source=%s fetch failed", source.name)
        async with factory() as s:
            svc = IngestionService(s)
            await svc.record_error(source.source_type, source.name, None, exc)
            await s.commit()
        return 0, 0, 0

    created = deduped = 0
    async with factory() as s:
        svc = IngestionService(s)
        for raw in raws:
            try:
                _, was_new = await svc.create_item(raw)
            except Exception as exc:
                await svc.record_error(raw.source_type, raw.source_name, raw.url, exc)
                continue
            if was_new:
                created += 1
            else:
                deduped += 1
        await s.commit()
    return len(raws), created, deduped


async def amain(targets: Sequence[str]) -> int:
    cfg = load_config()
    topics = load_topics()
    sources_by_kind = build_sources(cfg, topics)

    if not targets or targets == ("all",):
        targets = tuple(sources_by_kind.keys())

    for kind in targets:
        if kind not in sources_by_kind:
            logger.warning("unknown source kind: %s", kind)
            continue
        for source in sources_by_kind[kind]:
            fetched, created, deduped = await run_source(source)
            logger.info(
                "source=%s name=%s fetched=%d created=%d deduped=%d",
                kind,
                source.name,
                fetched,
                created,
                deduped,
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    targets = tuple(argv) if argv else ("all",)
    return asyncio.run(amain(targets))


if __name__ == "__main__":
    sys.exit(main())
