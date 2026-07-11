from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any
from xml.etree.ElementTree import ParseError

import requests

from app.providers.base_provider import BaseProvider

CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"
DEFAULT_RSS_URL = "https://cointelegraph.com/rss"
MAX_NEWS_ITEMS = 10
RSS_SCAN_LIMIT = 60

# Quiz asset ids -> title/body keywords (word-boundary matched).
ASSET_KEYWORDS = {
    "bitcoin": ("bitcoin", "btc"),
    "ethereum": ("ethereum", "ether", "eth"),
    "solana": ("solana", "sol"),
    "xrp": ("xrp", "ripple"),
    "cardano": ("cardano", "ada"),
    "dogecoin": ("dogecoin", "doge"),
}

TICKER_MAP = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "xrp": "XRP",
    "cardano": "ADA",
    "dogecoin": "DOGE",
}


def _http_get(url: str, *, params: dict | None = None, timeout: float = 5) -> requests.Response:
    """GET with one retry on network errors."""
    last_error: Exception | None = None
    for _ in range(2):
        try:
            return requests.get(url, params=params, timeout=timeout)
        except requests.RequestException as exc:
            last_error = exc
    raise last_error  # type: ignore[misc]


def _static_news_fallback() -> dict:
    """Return a safe static news item."""
    return {
        "items": [
            {
                "title": "Crypto markets update unavailable",
                "url": "https://www.coingecko.com/",
                "source": "fallback",
                "published_at": None,
            }
        ],
        "fallback": True,
    }


def _normalize_assets(interested_assets: list[str] | str | None) -> list[str]:
    """Normalize interested asset ids from provider context."""
    if interested_assets is None:
        return ["bitcoin", "ethereum"]
    if isinstance(interested_assets, str):
        return [interested_assets] if interested_assets.strip() else ["bitcoin", "ethereum"]
    cleaned = [str(asset).strip().lower() for asset in interested_assets if str(asset).strip()]
    return cleaned or ["bitcoin", "ethereum"]


def _asset_pattern(assets: list[str]) -> re.Pattern[str] | None:
    """Build a case-insensitive keyword pattern for the user's assets."""
    keywords: list[str] = []
    for asset in assets:
        for keyword in ASSET_KEYWORDS.get(asset, (asset,)):
            keywords.append(re.escape(keyword))
    if not keywords:
        return None
    # Longer tokens first so "bitcoin" wins over accidental short overlaps.
    keywords.sort(key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(keywords) + r")\b", re.IGNORECASE)


def item_matches_assets(text: str, assets: list[str]) -> bool:
    """Return True when text mentions at least one interested asset."""
    pattern = _asset_pattern(assets)
    if pattern is None:
        return True
    return bool(pattern.search(text or ""))


def filter_items_by_assets(items: list[dict], assets: list[str], *, limit: int = MAX_NEWS_ITEMS) -> list[dict]:
    """Keep news items that mention the user's interested assets."""
    matched = []
    for item in items:
        haystack = " ".join(
            str(item.get(field) or "")
            for field in ("title", "source", "summary", "url")
        )
        if item_matches_assets(haystack, assets):
            matched.append(item)
            if len(matched) >= limit:
                break
    return matched


def _news_cache_suffix(context: dict) -> str:
    """Build a cache suffix that changes when watchlist assets change."""
    assets = _normalize_assets(context.get("interested_assets"))
    return "daily:" + ",".join(sorted(assets))


class CryptoPanicNewsProvider(BaseProvider):
    """News provider backed by CryptoPanic."""

    section = "news"
    name = "cryptopanic"

    def __init__(self, config: Any | None = None):
        """Store provider config."""
        self.config = config

    def cache_key(self, context: dict) -> str:
        """Include interested assets so preference changes refresh news."""
        user_id = context.get("user_id", "anon")
        return f"{self.section}:{self.name}:{user_id}:{_news_cache_suffix(context)}"

    def fetch(self, context: dict) -> dict:
        """Fetch news items from CryptoPanic filtered to user assets."""
        api_key = getattr(self.config, "CRYPTOPANIC_API_KEY", "") or ""
        if not api_key.strip():
            raise ValueError("CRYPTOPANIC_API_KEY is not configured")

        timeout = float(getattr(self.config, "PROVIDER_HTTP_TIMEOUT", 5))
        assets = _normalize_assets(context.get("interested_assets"))
        params: dict[str, Any] = {
            "auth_token": api_key,
            "public": "true",
        }
        tickers = [TICKER_MAP.get(asset, asset.upper()) for asset in assets]
        params["currencies"] = ",".join(tickers)

        response = _http_get(CRYPTOPANIC_URL, params=params, timeout=timeout)
        if response.status_code != 200:
            raise ValueError(f"cryptopanic returned HTTP {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError("cryptopanic response is not JSON") from exc

        results = payload.get("results")
        if not isinstance(results, list):
            raise ValueError("cryptopanic response malformed")

        items = []
        for row in results[:40]:
            if not isinstance(row, dict):
                continue
            title = row.get("title")
            url = row.get("url")
            if not title or not url:
                continue
            source = (row.get("source") or {}).get("title") or (row.get("source") or {}).get("domain") or "cryptopanic"
            items.append(
                {
                    "title": title,
                    "url": url,
                    "source": source,
                    "published_at": row.get("published_at"),
                }
            )

        filtered = filter_items_by_assets(items, assets)
        if not filtered:
            raise ValueError("cryptopanic returned no usable news items")
        return {"items": filtered}

    def static_fallback(self, context: dict) -> dict:
        """Return static news when live fetch fails."""
        return _static_news_fallback()


class RssNewsProvider(BaseProvider):
    """News provider backed by an RSS feed."""

    section = "news"
    name = "rss"

    def __init__(self, config: Any | None = None, feed_url: str = DEFAULT_RSS_URL):
        """Store provider config and feed URL."""
        self.config = config
        self.feed_url = feed_url

    def cache_key(self, context: dict) -> str:
        """Include interested assets so preference changes refresh news."""
        user_id = context.get("user_id", "anon")
        return f"{self.section}:{self.name}:{user_id}:{_news_cache_suffix(context)}"

    def fetch(self, context: dict) -> dict:
        """Fetch RSS items and keep only those matching interested assets."""
        timeout = float(getattr(self.config, "PROVIDER_HTTP_TIMEOUT", 5))
        assets = _normalize_assets(context.get("interested_assets"))
        response = _http_get(self.feed_url, timeout=timeout)
        if response.status_code != 200:
            raise ValueError(f"rss feed returned HTTP {response.status_code}")

        try:
            root = ET.fromstring(response.text)
        except ParseError as exc:
            raise ValueError("rss feed malformed") from exc

        channel = root.find("channel")
        if channel is None:
            raise ValueError("rss feed missing channel")

        items = []
        for item in channel.findall("item")[:RSS_SCAN_LIMIT]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = item.findtext("pubDate")
            summary = (item.findtext("description") or "").strip()
            source = (item.findtext("source") or "Cointelegraph").strip() or "Cointelegraph"
            if not title or not link:
                continue
            items.append(
                {
                    "title": title,
                    "url": link,
                    "source": source,
                    "published_at": pub_date,
                    "summary": summary,
                }
            )

        filtered = filter_items_by_assets(items, assets)
        if not filtered:
            raise ValueError("rss feed returned no usable news items")

        # Drop helper field before returning the stable payload shape.
        for row in filtered:
            row.pop("summary", None)
        return {"items": filtered}

    def static_fallback(self, context: dict) -> dict:
        """Return static news when live fetch fails."""
        return _static_news_fallback()
