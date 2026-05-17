"""Pure-math scoring tests — no DB needed."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.scoring.engine import score_item
from app.scoring.preferences import Signal


def _item(quality=7.0, source_name="src", published_days_ago=2, tags=None):
    return SimpleNamespace(
        quality_score=quality,
        source_name=source_name,
        published_at=datetime.now(timezone.utc) - timedelta(days=published_days_ago),
        tags=tags or [],
        title="",
        title_cn="",
        summary_zh="",
    )


def test_cold_start_neutralizes_boost():
    sig = {"mcp": Signal(keep_rate=1.0, count=100)}
    b = score_item(
        _item(tags=["mcp"]),
        tag_signals=sig,
        entity_signals={},
        source_signals={},
        total_interactions_count=10,  # < 50
        item_tag_slugs=["mcp"],
    )
    assert b.cold_start is True
    assert b.tag_boost == 0


def test_tag_boost_lifts_when_user_keeps_that_tag():
    sigs = {"mcp": Signal(keep_rate=1.0, count=50)}
    b = score_item(
        _item(quality=5, tags=["mcp"]),
        tag_signals=sigs,
        entity_signals={},
        source_signals={},
        total_interactions_count=100,
        item_tag_slugs=["mcp"],
    )
    assert b.cold_start is False
    assert b.tag_boost > 0
    assert b.final > 5


def test_tag_penalty_when_user_trashes_that_tag():
    sigs = {"image-gen": Signal(keep_rate=0.0, count=50)}
    b = score_item(
        _item(quality=7, tags=["image-gen"]),
        tag_signals=sigs,
        entity_signals={},
        source_signals={},
        total_interactions_count=100,
        item_tag_slugs=["image-gen"],
    )
    assert b.tag_boost < 0
    assert b.final < 7


def test_time_decay_decays_with_age():
    fresh = _item(published_days_ago=1)
    old = _item(published_days_ago=60)
    bf = score_item(fresh, {}, {}, {}, total_interactions_count=100)
    bo = score_item(old, {}, {}, {}, total_interactions_count=100)
    assert bf.time_decay > bo.time_decay
    assert bo.time_decay == 0


def test_focus_hit_lifts_base_to_six():
    item = _item(quality=3, tags=[])
    item.title = "MCP server design"
    b = score_item(
        item,
        tag_signals={},
        entity_signals={},
        source_signals={},
        total_interactions_count=100,
        focus_keywords=["mcp"],
    )
    assert b.base == 6.0
    assert "mcp" in b.focus_hits


def test_mcp_keep_vs_image_gen_trash_gap(monkeypatch):
    # Spec scenario: 50 mcp keep + 50 image-gen trash → new mcp item should score
    # at least 2 higher than image-gen at equal quality_score.
    tag_sigs = {
        "mcp": Signal(keep_rate=1.0, count=50),
        "image-gen": Signal(keep_rate=0.0, count=50),
    }
    mcp_item = _item(quality=7, tags=["mcp"], source_name="rss")
    img_item = _item(quality=7, tags=["image-gen"], source_name="rss")
    b_mcp = score_item(mcp_item, tag_signals=tag_sigs, entity_signals={}, source_signals={},
                       total_interactions_count=100, item_tag_slugs=["mcp"])
    b_img = score_item(img_item, tag_signals=tag_sigs, entity_signals={}, source_signals={},
                       total_interactions_count=100, item_tag_slugs=["image-gen"])
    assert b_mcp.final - b_img.final >= 2.0
