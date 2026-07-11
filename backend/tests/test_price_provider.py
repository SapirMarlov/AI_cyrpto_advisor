from unittest.mock import MagicMock, patch

import pytest
import requests

from app.config import TestConfig
from app.providers.price_provider import CoinGeckoPriceProvider, _request_settings


def _provider(config=None):
    return CoinGeckoPriceProvider(config or TestConfig)


def test_price_provider_success_maps_markets_fields_and_sparkline():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = [
        {
            "id": "bitcoin",
            "current_price": 65000.1,
            "market_cap": 1.2e12,
            "total_volume": 2.8e10,
            "price_change_percentage_24h": 1.5,
            "last_updated": "2026-07-10T12:00:00.000Z",
            "sparkline_in_7d": {"price": [64000.0, 64500.5, 65000.1]},
        },
        {
            "id": "ethereum",
            "current_price": 3200.0,
            "market_cap": 3.8e11,
            "total_volume": 1.1e10,
            "price_change_percentage_24h": -0.4,
            "last_updated": "2026-07-10T12:00:00.000Z",
            "sparkline_in_7d": {"price": [3210.0, 3190.0, 3200.0]},
        },
    ]
    provider = _provider()
    context = {"interested_assets": ["bitcoin", "ethereum"]}

    with patch("app.providers.price_provider.requests.get", return_value=response) as get:
        data = provider.fetch(context)

    assert data["prices"]["bitcoin"]["usd"] == 65000.1
    assert data["prices"]["bitcoin"]["change_24h"] == 1.5
    assert data["prices"]["bitcoin"]["market_cap"] == 1.2e12
    assert data["prices"]["bitcoin"]["volume_24h"] == 2.8e10
    assert data["prices"]["bitcoin"]["last_updated_at"] == "2026-07-10T12:00:00.000Z"
    assert data["prices"]["bitcoin"]["sparkline_7d"] == [64000.0, 64500.5, 65000.1]
    assert data["prices"]["ethereum"]["usd"] == 3200.0

    _, kwargs = get.call_args
    assert kwargs["params"]["vs_currency"] == "usd"
    assert kwargs["params"]["sparkline"] == "true"
    assert "User-Agent" in kwargs["headers"]


def test_price_provider_timeout():
    provider = _provider()
    with patch(
        "app.providers.price_provider.requests.get",
        side_effect=requests.Timeout(),
    ):
        with pytest.raises(requests.Timeout):
            provider.fetch({"interested_assets": ["bitcoin"]})


def test_price_provider_rate_limited():
    response = MagicMock()
    response.status_code = 429
    provider = _provider()
    with patch("app.providers.price_provider.requests.get", return_value=response):
        with pytest.raises(ValueError, match="rate limited"):
            provider.fetch({"interested_assets": ["bitcoin"]})


def test_price_provider_non_200():
    response = MagicMock()
    response.status_code = 500
    provider = _provider()
    with patch("app.providers.price_provider.requests.get", return_value=response):
        with pytest.raises(ValueError, match="HTTP 500"):
            provider.fetch({"interested_assets": ["bitcoin"]})


def test_price_provider_malformed_payload():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"unexpected": True}
    provider = _provider()
    with patch("app.providers.price_provider.requests.get", return_value=response):
        with pytest.raises(ValueError, match="malformed"):
            provider.fetch({"interested_assets": ["bitcoin"]})


def test_price_provider_static_fallback():
    data = _provider().static_fallback({"interested_assets": ["solana"]})
    assert data["fallback"] is True
    assert data["prices"]["solana"]["usd"] is None
    assert data["prices"]["solana"]["market_cap"] is None
    assert data["prices"]["solana"]["sparkline_7d"] is None


def test_request_settings_demo_key():
    class DemoConfig:
        COINGECKO_DEMO_API_KEY = "demo-key"
        COINGECKO_PRO_API_KEY = ""
        COINGECKO_USER_AGENT = "test-agent"

    url, headers = _request_settings(DemoConfig())
    assert url.endswith("/coins/markets")
    assert url.startswith("https://api.coingecko.com/")
    assert headers["x-cg-demo-api-key"] == "demo-key"
    assert headers["User-Agent"] == "test-agent"


def test_request_settings_pro_key_preferred():
    class ProConfig:
        COINGECKO_DEMO_API_KEY = "demo-key"
        COINGECKO_PRO_API_KEY = "pro-key"
        COINGECKO_USER_AGENT = "test-agent"

    url, headers = _request_settings(ProConfig())
    assert url.endswith("/coins/markets")
    assert url.startswith("https://pro-api.coingecko.com/")
    assert headers["x-cg-pro-api-key"] == "pro-key"
    assert "x-cg-demo-api-key" not in headers
