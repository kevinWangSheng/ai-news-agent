"""Keyword matching with word boundaries for ASCII + substring for CJK.

Used by 004 enricher prefilter (exclude / focus). 002a fix D.13.
"""
import re

_ASCII_ONLY = re.compile(r"^[\x00-\x7f]+$")


def is_ascii(kw: str) -> bool:
    return bool(_ASCII_ONLY.match(kw))


def match_keyword(kw: str, text: str) -> bool:
    """ASCII keywords match with \\b word boundary; CJK keywords match by substring."""
    if not kw or not text:
        return False
    if is_ascii(kw):
        pattern = r"\b" + re.escape(kw) + r"\b"
        return re.search(pattern, text, re.IGNORECASE) is not None
    return kw in text


def matched_keywords(keywords: list[str], text: str) -> list[str]:
    return [kw for kw in keywords if match_keyword(kw, text)]
