from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from app.providers.base_provider import run_provider
from app.providers.registry import build_registry
from app.repositories.preferences_repository import get_preferences


def normalize_config(config: Any) -> Any:
    """Allow providers to use attribute access with Flask's dict-like config."""
    if isinstance(config, dict):
        return SimpleNamespace(
            **{k: v for k, v in config.items() if isinstance(k, str) and k.isupper()}
        )
    return config


def _build_context(user_id: int, preferences: dict | None) -> dict:
    answers = (preferences or {}).get("answers") or {}
    interested = answers.get("interested_assets") or ["bitcoin", "ethereum"]
    if isinstance(interested, str):
        interested = [interested]
    investor_type = answers.get("investor_type")
    if isinstance(investor_type, list):
        investor_type = investor_type[0] if investor_type else None
    content = answers.get("content_preferences") or []
    if isinstance(content, str):
        content = [content]

    return {
        "user_id": user_id,
        "cache_suffix": "daily",
        "interested_assets": interested,
        "investor_type": investor_type,
        "content_preferences": content,
    }


def get_daily_dashboard(
    conn: sqlite3.Connection,
    user_id: int,
    config: Any,
    registry: dict | None = None,
) -> dict:
    config = normalize_config(config)
    preferences = get_preferences(conn, user_id)
    context = _build_context(user_id, preferences)
    providers = registry or build_registry(config)

    # Prices first so insight can use live/fallback price data.
    prices_section = run_provider(providers["prices"], context, conn, config)
    context_with_prices = {**context, "prices": prices_section.get("data") or {}}

    news_section = run_provider(providers["news"], context, conn, config)
    insight_section = run_provider(
        providers["insight"],
        context_with_prices,
        conn,
        config,
    )
    meme_section = run_provider(providers["meme"], context, conn, config)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sections": {
            "news": news_section,
            "prices": prices_section,
            "insight": insight_section,
            "meme": meme_section,
        },
    }
