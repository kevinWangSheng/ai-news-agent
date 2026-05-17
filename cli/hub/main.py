"""hub CLI — rich output, JSON mode, friendly Chinese errors."""
from __future__ import annotations

import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from hub import __version__
from hub.api import Api
from hub.config import api_url, load, save

console = Console()


def _table_for_items(rows: list[dict]) -> Table:
    t = Table(show_header=True, header_style="bold")
    t.add_column("id", justify="right")
    t.add_column("score", justify="right")
    t.add_column("status")
    t.add_column("title", max_width=60)
    t.add_column("source")
    for r in rows:
        t.add_row(
            str(r["id"]),
            f"{r['final_score']:.1f}" if r.get("final_score") is not None else "-",
            r.get("status", "?"),
            (r.get("title_cn") or r.get("title") or "")[:120],
            r.get("source_name") or r.get("source_type") or "?",
        )
    return t


def _output(payload: Any, as_json: bool) -> None:
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    elif isinstance(payload, list) and payload and isinstance(payload[0], dict) and "title" in payload[0] or "title_cn" in (payload[0] if isinstance(payload, list) and payload else {}):
        console.print(_table_for_items(payload))
    elif isinstance(payload, dict) and "items" in payload:
        console.print(_table_for_items(payload["items"]))
    else:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@click.group()
@click.version_option(__version__, prog_name="hub")
def cli() -> None:
    """ai-agent-hub command line."""


@cli.command()
def version() -> None:
    click.echo(f"hub {__version__}")


@cli.command()
@click.argument("url", required=False)
@click.option("-t", "--title", help="标题(可选)")
@click.option("-n", "--note", help="附笔记")
@click.option("--tags", "tags", multiple=True, help="可重复 --tags")
@click.option("--json", "as_json", is_flag=True)
def add(url: str | None, title: str | None, note: str | None, tags: tuple[str, ...], as_json: bool) -> None:
    """投喂一个 URL 或纯笔记(`hub add -` 从 stdin 读 content)。"""
    content = None
    if url == "-":
        url = None
        content = sys.stdin.read().strip()
    payload = {
        "url": url,
        "title": title,
        "content": content,
        "note": note,
        "tags": list(tags) if tags else None,
        "source_type": "manual",
        "source_name": "cli",
    }
    res = Api().post("/api/ingest", json={k: v for k, v in payload.items() if v is not None})
    _output(res, as_json)


@cli.command(name="list")
@click.option("--inbox", "filter_status", flag_value="inbox", default=True)
@click.option("--kept", "filter_status", flag_value="kept")
@click.option("--archived", "filter_status", flag_value="archived")
@click.option("--all", "filter_status", flag_value="all")
@click.option("--source", default=None)
@click.option("--topic", default=None)
@click.option("-n", "--limit", default=20, type=int)
@click.option("--json", "as_json", is_flag=True)
def list_cmd(filter_status: str, source: str | None, topic: str | None, limit: int, as_json: bool) -> None:
    """列条目。"""
    params: dict[str, Any] = {"limit": limit}
    if filter_status != "all":
        params["status"] = filter_status
    if source:
        params["source_name"] = source
    if topic:
        params["topic"] = topic
    res = Api().get("/api/items", params=params)
    _output(res, as_json)


@cli.command()
@click.argument("query")
@click.option("--mode", type=click.Choice(["hybrid", "fulltext", "semantic"]), default="hybrid")
@click.option("-n", "--limit", default=20, type=int)
@click.option("--json", "as_json", is_flag=True)
def search(query: str, mode: str, limit: int, as_json: bool) -> None:
    """搜索。"""
    res = Api().get("/api/search", params={"q": query, "mode": mode, "limit": limit})
    _output(res, as_json)


@cli.command()
@click.argument("item_id", type=int)
@click.option("--json", "as_json", is_flag=True)
def show(item_id: int, as_json: bool) -> None:
    """看详情。"""
    res = Api().get(f"/api/items/{item_id}")
    if as_json:
        click.echo(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        console.rule(res.get("title_cn") or res.get("title") or "")
        if res.get("url"):
            console.print(f"[dim]{res['url']}[/dim]")
        console.print()
        console.print(res.get("summary_zh") or res.get("summary_en") or "(无摘要)")
        if res.get("recommendation"):
            console.print()
            console.print(f"[bold yellow]推荐理由[/bold yellow]: {res['recommendation']}")


def _patch_status(item_id: int, status: str) -> None:
    res = Api().patch(f"/api/items/{item_id}", json={"status": status})
    click.echo(f"#{res['id']} → {res['status']}")


@cli.command()
@click.argument("item_id", type=int)
def keep(item_id: int) -> None:
    _patch_status(item_id, "kept")


@cli.command()
@click.argument("item_id", type=int)
def archive(item_id: int) -> None:
    _patch_status(item_id, "archived")


@cli.command()
@click.argument("item_id", type=int)
def trash(item_id: int) -> None:
    _patch_status(item_id, "trashed")


@cli.command()
@click.option("--json", "as_json", is_flag=True)
def topics(as_json: bool) -> None:
    """列主题。"""
    res = Api().get("/api/topics")
    if as_json:
        click.echo(json.dumps(res, ensure_ascii=False, indent=2))
        return
    t = Table(show_header=True, header_style="bold")
    t.add_column("slug")
    t.add_column("name", max_width=40)
    t.add_column("count", justify="right")
    t.add_column("last_item")
    for r in res:
        t.add_row(
            r["slug"],
            r["name_zh"],
            str(r.get("item_count", 0)),
            (r.get("last_item_at") or "-")[:19],
        )
    console.print(t)


@cli.command()
@click.argument("source_name")
def trigger(source_name: str) -> None:
    """触发一次 ingestion。"""
    res = Api().post(f"/api/sources/{source_name}/trigger")
    click.echo(json.dumps(res, ensure_ascii=False))


@cli.group("config")
def config_group() -> None:
    """读写 ~/.config/hub/config.toml。"""


@config_group.command("show")
def config_show() -> None:
    click.echo(json.dumps(load(), ensure_ascii=False, indent=2))


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    cfg = load()
    cfg[key] = value
    save(cfg)
    click.echo(f"set {key} = {value}")


if __name__ == "__main__":
    cli()
