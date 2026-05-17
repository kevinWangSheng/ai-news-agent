"""002a Task 18 — KOL handle verification.

Spec asks HEAD `https://x.com/<handle>` per KOL and report.
本机沙盒无外网/无 docker；脚本写好,留给用户在能访问 x.com 的环境跑:

    python -m scripts.verify_kol_handles backend/legacy/config/config.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
import yaml


def collect_handles(cfg: dict) -> list[str]:
    tw = cfg.get("twitter", {})
    return list(tw.get("kol_accounts", [])) + list(tw.get("official_accounts", []))


def verify(handle: str, client: httpx.Client) -> tuple[str, int]:
    try:
        r = client.head(f"https://x.com/{handle}", follow_redirects=True, timeout=10)
        return handle, r.status_code
    except httpx.HTTPError as exc:
        return handle, -1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    args = ap.parse_args()
    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    handles = collect_handles(cfg)
    ok = bad = 0
    with httpx.Client(headers={"User-Agent": "ai-agent-hub/0.1"}) as client:
        for h in handles:
            handle, code = verify(h, client)
            ok_flag = 200 <= code < 400
            print(f"{'PASS' if ok_flag else 'FAIL'} {code:>4}  {handle}")
            if ok_flag:
                ok += 1
            else:
                bad += 1
    print(f"---\n{ok} ok / {bad} bad", file=sys.stderr)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
