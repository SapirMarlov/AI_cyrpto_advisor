from unittest.mock import MagicMock, patch

import pytest
import requests

from app.config import TestConfig
from app.providers.news_provider import (
    CryptoPanicNewsProvider,
    RssNewsProvider,
    filter_items_by_assets,
    item_matches_assets,
)

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Crypto Feed</title>
    <item>
      <title>Bitcoin hits new high</title>
      <link>https://example.com/btc</link>
      <pubDate>Fri, 10 Jul 2026 10:00:00 GMT</pubDate>
      <source>CoinTelegraph</source>
    </item>
    <item>
      <title>Ethereum upgrade</title>
      <link>https://example.com/eth</link>
      <pubDate>Fri, 10 Jul 2026 09:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Solana network outage</title>
      <link>https://example.com/sol</link>
      <pubDate>Fri, 10 Jul 2026 08:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def test_cryptopanic_success():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "results": [
            {
                "title": "BTC news",
                "url": "https://example.com/1",
                "published_at": "2026-07-10T10:00:00Z",
                "source": {"title": "CoinDesk"},
            },
            {
                "title": "Unrelated macro headline",
                "url": "https://example.com/2",
                "published_at": "2026-07-10T09:00:00Z",
                "source": {"title": "Wire"},
            },
        ]
    }
    provider = CryptoPanicNewsProvider(TestConfig)
    with patch("app.providers.news_provider.requests.get", return_value=response) as mock_get:
        data = provider.fetch({"interested_assets": ["bitcoin"]})

    assert data["items"][0]["title"] == "BTC news"
    assert data["items"][0]["source"] == "CoinDesk"
    assert len(data["items"]) == 1
    assert mock_get.call_args.kwargs["params"]["currencies"] == "BTC"


def test_cryptopanic_missing_key():
    class NoKey:
        CRYPTOPANIC_API_KEY = ""
        PROVIDER_HTTP_TIMEOUT = 2

    provider = CryptoPanicNewsProvider(NoKey())
    with pytest.raises(ValueError, match="not configured"):
        provider.fetch({})


def test_cryptopanic_timeout():
    provider = CryptoPanicNewsProvider(TestConfig)
    with patch(
        "app.providers.news_provider.requests.get",
        side_effect=requests.Timeout(),
    ):
        with pytest.raises(requests.Timeout):
            provider.fetch({})


def test_cryptopanic_non_200():
    response = MagicMock()
    response.status_code = 503
    provider = CryptoPanicNewsProvider(TestConfig)
    with patch("app.providers.news_provider.requests.get", return_value=response):
        with pytest.raises(ValueError, match="HTTP 503"):
            provider.fetch({})


def test_cryptopanic_malformed():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"results": "nope"}
    provider = CryptoPanicNewsProvider(TestConfig)
    with patch("app.providers.news_provider.requests.get", return_value=response):
        with pytest.raises(ValueError, match="malformed"):
            provider.fetch({})


def test_rss_success():
    response = MagicMock()
    response.status_code = 200
    response.text = SAMPLE_RSS
    provider = RssNewsProvider(TestConfig)
    with patch("app.providers.news_provider.requests.get", return_value=response):
        data = provider.fetch({})

    # Default assets are bitcoin + ethereum; Solana item is dropped.
    assert len(data["items"]) == 2
    assert data["items"][0]["url"] == "https://example.com/btc"
    assert data["items"][0]["source"] == "CoinTelegraph"
    assert data["items"][1]["source"] == "Cointelegraph"
    assert "summary" not in data["items"][0]


def test_rss_filters_to_interested_assets():
    response = MagicMock()
    response.status_code = 200
    response.text = SAMPLE_RSS
    provider = RssNewsProvider(TestConfig)
    with patch("app.providers.news_provider.requests.get", return_value=response):
        data = provider.fetch({"interested_assets": ["solana"]})

    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Solana network outage"


def test_rss_no_matching_assets_raises():
    response = MagicMock()
    response.status_code = 200
    response.text = SAMPLE_RSS
    provider = RssNewsProvider(TestConfig)
    with patch("app.providers.news_provider.requests.get", return_value=response):
        with pytest.raises(ValueError, match="no usable news"):
            provider.fetch({"interested_assets": ["cardano"]})


def test_rss_malformed():
    response = MagicMock()
    response.status_code = 200
    response.text = "<not-rss>"
    provider = RssNewsProvider(TestConfig)
    with patch("app.providers.news_provider.requests.get", return_value=response):
        with pytest.raises(ValueError, match="malformed|missing channel"):
            provider.fetch({})


def test_item_matches_assets_keywords():
    assert item_matches_assets("BTC pumps", ["bitcoin"]) is True
    assert item_matches_assets("Ripple lawsuit", ["xrp"]) is True
    assert item_matches_assets("Market wrap", ["bitcoin"]) is False


def test_filter_items_by_assets_limit():
    items = [
        {"title": "Bitcoin A", "url": "https://a"},
        {"title": "Bitcoin B", "url": "https://b"},
        {"title": "Other", "url": "https://c"},
    ]
    matched = filter_items_by_assets(items, ["bitcoin"], limit=1)
    assert len(matched) == 1
    assert matched[0]["title"] == "Bitcoin A"


def test_news_cache_key_includes_assets():
    provider = RssNewsProvider(TestConfig)
    key_btc = provider.cache_key({"user_id": 1, "interested_assets": ["bitcoin"]})
    key_eth = provider.cache_key({"user_id": 1, "interested_assets": ["ethereum"]})
    assert key_btc != key_eth
    assert "bitcoin" in key_btc
    assert "ethereum" in key_eth


def test_news_static_fallback():
    data = CryptoPanicNewsProvider(TestConfig).static_fallback({})
    assert data["fallback"] is True
    assert data["items"]
