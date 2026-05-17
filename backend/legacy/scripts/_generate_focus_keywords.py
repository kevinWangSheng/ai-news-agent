"""Generate focus_keywords block from topics.yaml — DO NOT hand-edit focus_keywords.

Usage:
    python -m scripts._generate_focus_keywords > /tmp/focus.txt
Then paste the YAML list into config.yaml under evaluation.filters.focus_keywords.
"""
import sys
from pathlib import Path

import yaml

TOPICS_FILE = Path(__file__).resolve().parent.parent / "config" / "topics.yaml"


def collect_keywords() -> list[str]:
    topics = yaml.safe_load(TOPICS_FILE.read_text(encoding="utf-8"))["topics"]
    seen: dict[str, None] = {}
    for t in topics:
        for kw in t.get("keywords_en", []) or []:
            seen.setdefault(kw.strip().lower(), None)
        for kw in t.get("keywords_zh", []) or []:
            seen.setdefault(kw.strip(), None)
    return list(seen)


def main() -> int:
    for kw in collect_keywords():
        print(f"      - \"{kw}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
