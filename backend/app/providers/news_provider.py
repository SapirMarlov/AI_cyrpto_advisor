from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from xml.etree.ElementTree import ParseError

import requests

from app.providers.base_provider import BaseProvider

CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"
DEFAULT_RSS_URL = "https://cointelegraph.com/rss"


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


class CryptoPanicNewsProvider(BaseProvider):
    """News provider backed by CryptoPanic."""

    section = "news"
    name = "cryptopanic"

    def __init__(self, config: Any | None = None):
        """Store provider config."""
        self.config = config

    def fetch(self, context: dict) -> dict:
        """Fetch news items from CryptoPanic."""
        api_key = getattr(self.config, "CRYPTOPANIC_API_KEY", "") or ""
        if not api_key.strip():
            raise ValueError("CRYPTOPANIC_API_KEY is not configured")

        timeout = float(getattr(self.config, "PROVIDER_HTTP_TIMEOUT", 5))
        currencies = context.get("interested_assets") or []
        params: dict[str, Any] = {
            "auth_token": api_key,
            "public": "true",
        }
        if currencies:
            # CryptoPanic expects tickers like BTC,ETH — map common quiz ids.
            ticker_map = {
                "bitcoin": "BTC",
                "ethereum": "ETH",
                "solana": "SOL",
                "xrp": "XRP",
                "cardano": "ADA",
                "dogecoin": "DOGE",
            }
            tickers = [ticker_map.get(a, a.upper()) for a in currencies]
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
        for row in results[:10]:
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

        if not items:
            raise ValueError("cryptopanic returned no usable news items")
        return {"items": items}

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

    def fetch(self, context: dict) -> dict:
        """Fetch news items from the RSS feed."""
        timeout = float(getattr(self.config, "PROVIDER_HTTP_TIMEOUT", 5))
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
        for item in channel.findall("item")[:10]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = item.findtext("pubDate")
            source = (item.findtext("source") or "Cointelegraph").strip() or "Cointelegraph"
            if not title or not link:
                continue
            items.append(
                {
                    "title": title,
                    "url": link,
                    "source": source,
                    "published_at": pub_date,
                }
            )

        if not items:
            raise ValueError("rss feed returned no usable news items")
        return {"items": items}

    def static_fallback(self, context: dict) -> dict:
        """Return static news when live fetch fails."""
        return _static_news_fallback()
