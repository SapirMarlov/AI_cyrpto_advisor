from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.repositories import provider_cache_repository as cache_repo

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    section: str = ""
    name: str = ""

    @abstractmethod
    def fetch(self, context: dict) -> dict:
        """Fetch live data. May raise on failure."""

    @abstractmethod
    def static_fallback(self, context: dict) -> dict:
        """Return a safe static payload when live and cache both fail."""

    def cache_key(self, context: dict) -> str:
        suffix = context.get("cache_suffix", "default")
        user_id = context.get("user_id", "anon")
        return f"{self.section}:{self.name}:{user_id}:{suffix}"


def run_provider(
    provider: BaseProvider,
    context: dict,
    conn: Any,
    config: Any,
) -> dict:
    """
    Run a provider with live -> cache -> static fallback.
    Never raises to the caller.
    """
    ttl = int(getattr(config, "PROVIDER_CACHE_TTL", 300))
    key = provider.cache_key(context)

    try:
        data = provider.fetch(context)
        if not isinstance(data, dict):
            raise ValueError("provider returned non-dict payload")
        cache_repo.set_cached(conn, key, data, ttl)
        return {"data": data, "error": None, "stale": False}
    except Exception as exc:
        logger.warning(
            "provider %s/%s failed: %s",
            provider.section,
            provider.name,
            exc,
        )
        error = {"code": "provider_error", "message": str(exc) or "provider failed"}

        cached = cache_repo.get_cached(conn, key)
        if cached is not None:
            return {
                "data": cached["payload"],
                "error": error,
                "stale": True,
            }

        try:
            fallback = provider.static_fallback(context)
        except Exception as fallback_exc:
            logger.warning(
                "static fallback failed for %s/%s: %s",
                provider.section,
                provider.name,
                fallback_exc,
            )
            fallback = None

        return {"data": fallback, "error": error, "stale": False}
