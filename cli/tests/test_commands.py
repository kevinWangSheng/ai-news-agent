from unittest.mock import patch

from click.testing import CliRunner

from hub.main import cli


def test_version():
    r = CliRunner().invoke(cli, ["version"])
    assert r.exit_code == 0
    assert "hub 0.1.0" in r.output


def test_add_calls_post_with_payload():
    with patch("hub.main.Api") as ApiMock:
        ApiMock.return_value.post.return_value = {"item_id": 42, "created": True}
        r = CliRunner().invoke(cli, ["add", "https://example.com/x", "-t", "Hi", "-n", "note"])
        assert r.exit_code == 0
        assert "42" in r.output or "item_id" in r.output
        args, kw = ApiMock.return_value.post.call_args
        assert args[0] == "/api/ingest"
        assert kw["json"]["url"] == "https://example.com/x"
        assert kw["json"]["title"] == "Hi"
        assert kw["json"]["note"] == "note"


def test_list_passes_status_filter():
    with patch("hub.main.Api") as ApiMock:
        ApiMock.return_value.get.return_value = {"items": [], "next_cursor": None}
        r = CliRunner().invoke(cli, ["list", "--kept", "--limit", "5"])
        assert r.exit_code == 0, r.output
        args, kw = ApiMock.return_value.get.call_args
        assert args[0] == "/api/items"
        assert kw["params"]["status"] == "kept"
        assert kw["params"]["limit"] == 5


def test_keep_patches_status():
    with patch("hub.main.Api") as ApiMock:
        ApiMock.return_value.patch.return_value = {"id": 7, "status": "kept"}
        r = CliRunner().invoke(cli, ["keep", "7"])
        assert r.exit_code == 0
        assert "#7" in r.output
        args, kw = ApiMock.return_value.patch.call_args
        assert args[0] == "/api/items/7"
        assert kw["json"] == {"status": "kept"}


def test_search_passes_mode():
    with patch("hub.main.Api") as ApiMock:
        ApiMock.return_value.get.return_value = {"items": [], "total": 0, "facets": {}}
        r = CliRunner().invoke(cli, ["search", "agent", "--mode", "semantic"])
        assert r.exit_code == 0
        args, kw = ApiMock.return_value.get.call_args
        assert kw["params"]["mode"] == "semantic"
