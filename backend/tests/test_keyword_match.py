"""002a fix D.13 — ASCII word boundaries + CJK substring."""
from app.processing.keyword_match import match_keyword, matched_keywords


def test_ascii_word_boundary_hit():
    assert match_keyword("mcp", "MCP server design")
    assert match_keyword("multi-agent", "multi-agent system breakthrough")


def test_ascii_word_boundary_miss():
    assert not match_keyword("mcp", "bnp paribas pmcs setup")
    assert not match_keyword("tool use", "stool used by students")


def test_cjk_substring_hit():
    assert match_keyword("智能体", "AI 智能体框架")


def test_cjk_substring_miss():
    assert not match_keyword("智能体", "AI 模型")


def test_matched_keywords_collects_hits():
    text = "MCP server with multi-agent orchestration"
    hits = matched_keywords(["mcp", "multi-agent", "rag", "claude code"], text)
    assert hits == ["mcp", "multi-agent"]
