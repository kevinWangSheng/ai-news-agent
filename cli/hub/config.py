"""User-local CLI config at ~/.config/hub/config.toml (or platform equivalent)."""
from __future__ import annotations

import tomllib
from pathlib import Path

from platformdirs import user_config_dir


def config_path() -> Path:
    return Path(user_config_dir("hub", "ai-agent-hub")) / "config.toml"


def load() -> dict:
    p = config_path()
    if not p.exists():
        return {"api_url": "http://localhost:8000"}
    return tomllib.loads(p.read_text(encoding="utf-8"))


def save(cfg: dict) -> None:
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for k, v in cfg.items():
        if isinstance(v, str):
            lines.append(f'{k} = "{v}"')
        else:
            lines.append(f"{k} = {v}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def api_url() -> str:
    return load().get("api_url", "http://localhost:8000")
