"""URL normalization for dedup key."""
from urllib.parse import urlparse, urlunparse


TRACKING_PREFIXES = ("utm_", "ref", "fbclid", "gclid", "mc_cid", "mc_eid")


def normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    p = urlparse(url)
    if not p.scheme:
        p = urlparse("https://" + url)

    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    path = p.path.rstrip("/") or "/"

    query_pairs = []
    if p.query:
        for kv in p.query.split("&"):
            if not kv:
                continue
            k = kv.split("=", 1)[0]
            if any(k.startswith(prefix) for prefix in TRACKING_PREFIXES):
                continue
            query_pairs.append(kv)
    query = "&".join(query_pairs)

    return urlunparse(("https", host, path, "", query, ""))
