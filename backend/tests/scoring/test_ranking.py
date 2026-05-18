from types import SimpleNamespace

from app.ranking import diversify_ranked_items, source_prior, source_tier


def _item(source_type: str, source_name: str, i: int):
    return SimpleNamespace(source_type=source_type, source_name=source_name, id=i)


def test_source_prior_by_tier():
    assert source_tier("web", "Anthropic News") == "official"
    assert source_prior("web", "Anthropic News") > 0
    assert source_prior("github", "github:mcp") < 0
    assert source_prior("rss", "Lilian Weng") > 0


def test_diversify_caps_github_in_top50_candidate_pool():
    rows = [_item("github", "github:mcp", i) for i in range(60)]
    rows += [_item("web", f"Official {i}", 100 + i) for i in range(20)]

    selected = diversify_ranked_items(rows, 50)

    assert len(selected) == 50
    assert sum(1 for item in selected if item.source_type == "web") == 20
    assert selected[18].source_type == "web"


def test_diversify_backfills_when_only_github_exists():
    rows = [_item("github", "github:mcp", i) for i in range(10)]

    selected = diversify_ranked_items(rows, 8)

    assert len(selected) == 8
