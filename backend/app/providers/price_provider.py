from __future__ import annotations

from typing import Any

import requests

from app.providers.base_provider import BaseProvider

# Quiz option ids -> CoinGecko coin ids
ASSET_TO_COINGECKO = {
    "bitcoin": "bitcoin",
    "ethereum": "ethereum",
    "solana": "solana",
    "xrp": "ripple",
    "cardano": "cardano",
    "dogecoin": "dogecoin",
}

COINGECKO_SIMPLE_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"


def _resolve_coin_ids(interested_assets: list[str] | None) -> list[str]:
    assets = interested_assets or list(ASSET_TO_COINGECKO.keys())
    ids = []
    for asset in assets:
        gecko_id = ASSET_TO_COINGECKO.get(asset, asset)
        if gecko_id not in ids:
            ids.append(gecko_id)
    return ids or ["bitcoin", "ethereum"]


def _map_response(raw: dict, interested_assets: list[str] | None) -> dict:
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
            "coingecko_id": gecko_id,
        }
    if not prices:
        raise ValueError("coingecko response missing usable price fields")
    return {"prices": prices}


def _http_get(url: str, params: dict, timeout: float) -> requests.Response:
    last_error: Exception | None = None
    for _ in range(2):  # initial try + 1 retry
        try:
            return requests.get(url, params=params, timeout=timeout)
        except requests.RequestException as exc:
            last_error = exc
    raise last_error  # type: ignore[misc]


class CoinGeckoPriceProvider(BaseProvider):
    section = "prices"
    name = "coingecko"

    def __init__(self, config: Any | None = None):
        self.config = config

    def fetch(self, context: dict) -> dict:
        timeout = float(getattr(self.config, "PROVIDER_HTTP_TIMEOUT", 5))
        interested = context.get("interested_assets")
        coin_ids = _resolve_coin_ids(interested)
        response = _http_get(
            COINGECKO_SIMPLE_PRICE_URL,
            params={
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=timeout,
        )
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
        interested = context.get("interested_assets") or ["bitcoin", "ethereum"]
        prices = {
            asset: {"usd": None, "change_24h": None, "coingecko_id": ASSET_TO_COINGECKO.get(asset, asset)}
            for asset in interested
        }
        return {"prices": prices, "fallback": True}
