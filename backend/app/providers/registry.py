from __future__ import annotations

from typing import Any

from app.providers.ai_provider import GeminiInsightProvider, TemplateInsightProvider
from app.providers.meme_provider import RedditGeminiMemeProvider
from app.providers.news_provider import CryptoPanicNewsProvider, RssNewsProvider
from app.providers.price_provider import CoinGeckoPriceProvider

PROVIDER_IMPLEMENTATIONS = {
    "prices": {
        "coingecko": CoinGeckoPriceProvider,
    },
    "news": {
        "cryptopanic": CryptoPanicNewsProvider,
        "rss": RssNewsProvider,
    },
    "insight": {
        "gemini": GeminiInsightProvider,
        "template": TemplateInsightProvider,
    },
    "meme": {
        "reddit_gemini": RedditGeminiMemeProvider,
    },
}

_DEFAULTS = {
    "prices": "coingecko",
    "news": "cryptopanic",
    "insight": "gemini",
    "meme": "reddit_gemini",
}


def _selector(config: Any, section: str) -> str:
    attr = {
        "prices": "PRICE_PROVIDER",
        "news": "NEWS_PROVIDER",
        "insight": "AI_PROVIDER",
        "meme": "MEME_PROVIDER",
    }[section]
    value = getattr(config, attr, None) or _DEFAULTS[section]
    if value not in PROVIDER_IMPLEMENTATIONS[section]:
        return _DEFAULTS[section]
    return value


def build_registry(config: Any) -> dict:
    """Return {section: provider_instance} selected from config."""
    registry = {}
    for section in ("prices", "news", "insight", "meme"):
        name = _selector(config, section)
        cls = PROVIDER_IMPLEMENTATIONS[section][name]
        registry[section] = cls(config)
    return registry
