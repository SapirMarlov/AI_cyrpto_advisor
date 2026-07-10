from __future__ import annotations

from typing import Any

import requests

from app.providers.base_provider import BaseProvider

# Quiz option ids -> CoinGecko coin ids (/coins/list)
ASSET_TO_COINGECKO = {
    "bitcoin": "bitcoin",
    "ethereum": "ethereum",
    "solana": "solana",
    "xrp": "ripple",
    "cardano": "cardano",
    "dogecoin": "dogecoin",
}

PUBLIC_BASE_URL = "https://api.coingecko.com/api/v3"
PRO_BASE_URL = "https://pro-api.coingecko.com/api/v3"
DEFAULT_USER_AGENT = "AICryptoAdvisor/0.1 (educational; +https://localhost)"


def _resolve_coin_ids(interested_assets: list[str] | None) -> list[str]:
    """Map quiz asset ids to CoinGecko coin ids."""
    assets = interested_assets or list(ASSET_TO_COINGECKO.keys())
    ids = []
    for asset in assets:
        gecko_id = ASSET_TO_COINGECKO.get(asset, asset)
        if gecko_id not in ids:
            ids.append(gecko_id)
    return ids or ["bitcoin", "ethereum"]


def _map_response(raw: dict, interested_assets: list[str] | None) -> dict:
    """Map CoinGecko simple/price JSON to our price shape."""
    assets = interested_assets or list(ASSET_TO_COINGECKO.keys())
    prices: dict[str, dict] = {}
    for asset in assets:
        gecko_id = ASSET_TO_COINGECKO.get(asset, asset)
        entry = raw.get(gecko_id) or {}
        if not isinstance(entry, dict):
            continue
        if "usd" not in entry:
            continue
        prices[asset] = {
            "usd": entry.get("usd"),
            "change_24h": entry.get("usd_24h_change"),
            "market_cap": entry.get("usd_market_cap"),
            "volume_24h": entry.get("usd_24h_vol"),
            "last_updated_at": entry.get("last_updated_at"),
            "coingecko_id": gecko_id,
        }
    if not prices:
        raise ValueError("coingecko response missing usable price fields")
    return {"prices": prices}


def _request_settings(config: Any | None) -> tuple[str, dict[str, str]]:
    """Resolve CoinGecko URL and auth headers from config."""
    pro_key = (getattr(config, "COINGECKO_PRO_API_KEY", "") or "").strip()
    demo_key = (getattr(config, "COINGECKO_DEMO_API_KEY", "") or "").strip()
    user_agent = (
        getattr(config, "COINGECKO_USER_AGENT", None)
        or getattr(config, "REDDIT_USER_AGENT", None)
        or DEFAULT_USER_AGENT
    )
    headers = {"Accept": "application/json", "User-Agent": str(user_agent)}

    if pro_key:
        headers["x-cg-pro-api-key"] = pro_key
        return f"{PRO_BASE_URL}/simple/price", headers
    if demo_key:
        headers["x-cg-demo-api-key"] = demo_key
        return f"{PUBLIC_BASE_URL}/simple/price", headers
    return f"{PUBLIC_BASE_URL}/simple/price", headers


def _http_get(
    url: str,
    *,
    params: dict,
    headers: dict[str, str],
    timeout: float,
) -> requests.Response:
    """GET with one retry on network errors."""
    last_error: Exception | None = None
    for _ in range(2):  # initial try + 1 retry
        try:
            return requests.get(url, params=params, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            last_error = exc
    raise last_error  # type: ignore[misc]


class CoinGeckoPriceProvider(BaseProvider):
    """Price provider backed by CoinGecko simple/price."""

    section = "prices"
    name = "coingecko"

    def __init__(self, config: Any | None = None):
        """Store provider config."""
        self.config = config

    def fetch(self, context: dict) -> dict:
        """Fetch live prices for the user's assets."""
        timeout = float(getattr(self.config, "PROVIDER_HTTP_TIMEOUT", 5))
        interested = context.get("interested_assets")
        coin_ids = _resolve_coin_ids(interested)
        url, headers = _request_settings(self.config)

        response = _http_get(
            url,
            params={
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true",
            },
            headers=headers,
            timeout=timeout,
        )
        if response.status_code == 429:
            raise ValueError("coingecko rate limited (HTTP 429)")
        if response.status_code != 200:
            raise ValueError(f"coingecko returned HTTP {response.status_code}")
        try:
            raw = response.json()
        except ValueError as exc:
            raise ValueError("coingecko response is not JSON") from exc
        if not isinstance(raw, dict):
            raise ValueError("coingecko response malformed")
        return _map_response(raw, interested)

    def static_fallback(self, context: dict) -> dict:
        """Return empty price placeholders when live data fails."""
        interested = context.get("interested_assets") or ["bitcoin", "ethereum"]
        prices = {
            asset: {
                "usd": None,
                "change_24h": None,
                "market_cap": None,
                "volume_24h": None,
                "last_updated_at": None,
                "coingecko_id": ASSET_TO_COINGECKO.get(asset, asset),
            }
            for asset in interested
        }
        return {"prices": prices, "fallback": True}
