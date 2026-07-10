"""Offline providers that return fixed payloads (used by e2e / demos)."""

from __future__ import annotations

from typing import Any

from app.providers.base_provider import BaseProvider


class StaticNewsProvider(BaseProvider):
    """News provider with a fixed headline list."""

    section = "news"
    name = "static"

    def __init__(self, config: Any = None):
        """Store unused config for registry compatibility."""
        self.config = config

    def fetch(self, context: dict) -> dict:
        """Return deterministic news items."""
        return {
            "items": [
                {
                    "title": "E2E Bitcoin briefing",
                    "url": "https://example.com/e2e-bitcoin",
                    "source": "E2E Wire",
                    "published_at": "2026-07-10T12:00:00Z",
                }
            ]
        }

    def static_fallback(self, context: dict) -> dict:
        """Return the same fixed payload on failure."""
        return self.fetch(context)


class StaticPriceProvider(BaseProvider):
    """Price provider with fixed USD quotes."""

    section = "prices"
    name = "static"

    def __init__(self, config: Any = None):
        """Store unused config for registry compatibility."""
        self.config = config

    def fetch(self, context: dict) -> dict:
        """Return deterministic price quotes."""
        assets = context.get("interested_assets") or ["bitcoin", "ethereum"]
        prices = {}
        for asset in assets:
            prices[asset] = {"usd": 100.0, "change_24h": 1.0}
        return {"prices": prices}

    def static_fallback(self, context: dict) -> dict:
        """Return the same fixed payload on failure."""
        return self.fetch(context)


class StaticMemeProvider(BaseProvider):
    """Meme provider with a fixed image payload."""

    section = "meme"
    name = "static"

    def __init__(self, config: Any = None):
        """Store unused config for registry compatibility."""
        self.config = config

    def fetch(self, context: dict) -> dict:
        """Return a deterministic meme payload."""
        return {
            "title": "E2E crypto meme",
            "image_url": "https://via.placeholder.com/300",
            "permalink": "https://example.com/e2e-meme",
            "subreddit": "e2e",
            "upvotes": 1,
        }

    def static_fallback(self, context: dict) -> dict:
        """Return the same fixed payload on failure."""
        return self.fetch(context)
