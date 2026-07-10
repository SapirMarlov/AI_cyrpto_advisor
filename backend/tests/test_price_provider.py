from unittest.mock import MagicMock, patch

import pytest
import requests

from app.config import TestConfig
from app.providers.price_provider import CoinGeckoPriceProvider


def _provider():
    return CoinGeckoPriceProvider(TestConfig)


def test_price_provider_success():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "bitcoin": {"usd": 65000.1, "usd_24h_change": 1.5},
        "ethereum": {"usd": 3200.0, "usd_24h_change": -0.4},
    }
    provider = _provider()
    context = {"interested_assets": ["bitcoin", "ethereum"]}

    with patch("app.providers.price_provider.requests.get", return_value=response) as get:
        data = provider.fetch(context)

    assert data["prices"]["bitcoin"]["usd"] == 65000.1
    assert data["prices"]["bitcoin"]["change_24h"] == 1.5
    assert data["prices"]["ethereum"]["usd"] == 3200.0
    assert get.called


def test_price_provider_timeout():
    provider = _provider()
    with patch(
        "app.providers.price_provider.requests.get",
        side_effect=requests.Timeout(),
    ):
        with pytest.raises(requests.Timeout):
            provider.fetch({"interested_assets": ["bitcoin"]})


def test_price_provider_non_200():
    response = MagicMock()
    response.status_code = 429
    provider = _provider()
    with patch("app.providers.price_provider.requests.get", return_value=response):
        with pytest.raises(ValueError, match="HTTP 429"):
            provider.fetch({"interested_assets": ["bitcoin"]})


def test_price_provider_malformed_payload():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"unexpected": True}
    provider = _provider()
    with patch("app.providers.price_provider.requests.get", return_value=response):
        with pytest.raises(ValueError, match="missing usable"):
            provider.fetch({"interested_assets": ["bitcoin"]})


def test_price_provider_static_fallback():
    data = _provider().static_fallback({"interested_assets": ["solana"]})
    assert data["fallback"] is True
    assert data["prices"]["solana"]["usd"] is None
