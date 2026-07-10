from unittest.mock import MagicMock, patch

import pytest
import requests

from app.config import TestConfig
from app.providers.gemini_client import GeminiError
from app.providers.meme_provider import RedditGeminiMemeProvider


def _reddit_payload(posts: list[dict]) -> dict:
    return {"data": {"children": [{"data": p} for p in posts]}}


SAMPLE_POSTS = [
    {
        "title": "When BTC dumps",
        "url": "https://i.redd.it/meme1.jpg",
        "permalink": "/r/cryptocurrencymemes/comments/1/",
        "subreddit": "cryptocurrencymemes",
        "ups": 100,
        "num_comments": 10,
        "post_hint": "image",
    },
    {
        "title": "ETH gas fees",
        "url": "https://i.redd.it/meme2.png",
        "permalink": "/r/cryptocurrencymemes/comments/2/",
        "subreddit": "cryptocurrencymemes",
        "ups": 500,
        "num_comments": 40,
        "post_hint": "image",
    },
]


def test_meme_gemini_selection_success():
    reddit_response = MagicMock()
    reddit_response.status_code = 200
    reddit_response.json.return_value = _reddit_payload(SAMPLE_POSTS)

    provider = RedditGeminiMemeProvider(TestConfig)
    with patch("app.providers.meme_provider.requests.get", return_value=reddit_response):
        with patch(
            "app.providers.meme_provider.generate",
            return_value='{"index": 1, "reason": "matches bitcoin humor"}',
        ):
            data = provider.fetch(
                {
                    "interested_assets": ["bitcoin"],
                    "investor_type": "hodler",
                    "content_preferences": ["fun"],
                }
            )

    assert data["selected_by"] == "gemini"
    assert data["title"] == "When BTC dumps"
    assert data["reason"] == "matches bitcoin humor"


def test_meme_gemini_down_uses_top_upvotes():
    reddit_response = MagicMock()
    reddit_response.status_code = 200
    reddit_response.json.return_value = _reddit_payload(SAMPLE_POSTS)

    provider = RedditGeminiMemeProvider(TestConfig)
    with patch("app.providers.meme_provider.requests.get", return_value=reddit_response):
        with patch(
            "app.providers.meme_provider.generate",
            side_effect=GeminiError("down"),
        ):
            data = provider.fetch({"interested_assets": ["ethereum"]})

    assert data["selected_by"] == "upvotes_fallback"
    assert data["title"] == "ETH gas fees"
    assert data["upvotes"] == 500


def test_meme_reddit_down_raises_for_outer_fallback():
    provider = RedditGeminiMemeProvider(TestConfig)
    with patch(
        "app.providers.meme_provider.requests.get",
        side_effect=requests.Timeout(),
    ):
        with pytest.raises(requests.Timeout):
            provider.fetch({})


def test_meme_static_fallback():
    data = RedditGeminiMemeProvider(TestConfig).static_fallback({})
    assert data["fallback"] is True
    assert data["selected_by"] == "static"
