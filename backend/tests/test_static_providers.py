"""Minimal unit coverage for offline static providers."""

from app.providers.static_providers import (
    StaticMemeProvider,
    StaticNewsProvider,
    StaticPriceProvider,
)


def test_static_news_provider_returns_items():
    data = StaticNewsProvider().fetch({})
    assert len(data["items"]) >= 1
    assert data["items"][0]["url"].startswith("https://")


def test_static_price_provider_maps_assets():
    data = StaticPriceProvider().fetch({"interested_assets": ["bitcoin"]})
    assert data["prices"]["bitcoin"]["usd"] == 100.0


def test_static_meme_provider_has_permalink():
    data = StaticMemeProvider().fetch({})
    assert data["permalink"]
    assert data["image_url"]
