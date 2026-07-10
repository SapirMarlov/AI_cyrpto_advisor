from unittest.mock import MagicMock, patch

import pytest
import requests

from app.config import TestConfig
from app.providers.news_provider import CryptoPanicNewsProvider, RssNewsProvider

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
            }
        ]
    }
    provider = CryptoPanicNewsProvider(TestConfig)
    with patch("app.providers.news_provider.requests.get", return_value=response):
        data = provider.fetch({"interested_assets": ["bitcoin"]})

    assert data["items"][0]["title"] == "BTC news"
    assert data["items"][0]["source"] == "CoinDesk"


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

    assert len(data["items"]) == 2
    assert data["items"][0]["url"] == "https://example.com/btc"


def test_rss_malformed():
    response = MagicMock()
    response.status_code = 200
    response.text = "<not-rss>"
    provider = RssNewsProvider(TestConfig)
    with patch("app.providers.news_provider.requests.get", return_value=response):
        with pytest.raises(ValueError, match="malformed|missing channel"):
            provider.fetch({})


def test_news_static_fallback():
    data = CryptoPanicNewsProvider(TestConfig).static_fallback({})
    assert data["fallback"] is True
    assert data["items"]
