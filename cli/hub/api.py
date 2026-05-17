"""httpx wrapper with Chinese-friendly error messages."""
from __future__ import annotations

import json
from typing import Any

import click
import httpx

from hub.config import api_url


class Api:
    def __init__(self, base: str | None = None) -> None:
        self.base = base or api_url()

    def request(self, method: str, path: str, **kw: Any) -> Any:
        try:
            r = httpx.request(method, self.base + path, timeout=30, **kw)
        except httpx.ConnectError:
            raise click.ClickException(f"无法连接 {self.base},请确认 backend 已启动")
        except httpx.HTTPError as exc:
            raise click.ClickException(f"网络错误: {exc}")
        if r.status_code >= 400:
            try:
                detail = r.json().get("detail")
            except (json.JSONDecodeError, ValueError):
                detail = r.text[:300]
            raise click.ClickException(f"接口错误 {r.status_code}: {detail}")
        if r.headers.get("content-type", "").startswith("application/json"):
            return r.json()
        return r.text

    def get(self, path: str, **kw: Any) -> Any:
        return self.request("GET", path, **kw)

    def post(self, path: str, json: Any = None, **kw: Any) -> Any:
        return self.request("POST", path, json=json, **kw)

    def patch(self, path: str, json: Any = None, **kw: Any) -> Any:
        return self.request("PATCH", path, json=json, **kw)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)
