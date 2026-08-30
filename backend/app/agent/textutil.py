from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}

SOCIAL_DOMAINS = {
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "t.me",
    "telegram.me",
    "tiktok.com",
}
FORUM_DOMAINS = {
    "nairaland.com",
    "reddit.com",
    "old.reddit.com",
    "www.reddit.com",
    "disqus.com",
    "stackexchange.com",
}
NEWS_HINTS = ("news", "bbc.", "cnn.", "reuters", "guardian", "punchng", "vanguardngr", "premiumtimesng")


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower().removeprefix("www.")
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
    path = parsed.path.rstrip("/") or "/"
    return urlunparse(("https" if parsed.scheme in {"http", "https"} else parsed.scheme or "https", host, path, "", urlencode(query), ""))


def domain_of(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host.removeprefix("www.")


def source_kind_of(url: str) -> str:
    host = domain_of(url)
    if any(host == d or host.endswith("." + d) for d in SOCIAL_DOMAINS):
        return "social"
    if any(host == d or host.endswith("." + d) for d in FORUM_DOMAINS):
        return "forum"
    if any(h in host for h in NEWS_HINTS):
        return "news"
    return "web"


def content_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="ignore")).hexdigest()


def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    return value.strip("-")[:120] or "item"


def normalize_alias(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def fts_match_query(raw: str) -> str:
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", raw or "", flags=re.UNICODE)
    if not tokens:
        return '""'
    return " AND ".join(f'"{t.lower()}"' for t in tokens[:12])
