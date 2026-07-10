from unittest.mock import MagicMock, patch

import pytest
import requests

from app.config import TestConfig
from app.providers.gemini_client import GeminiError
from app.providers.meme_provider import RedditGeminiMemeProvider


def _rss_feed(entries: list[tuple[str, str, str]]) -> bytes:
    """Build a minimal Atom RSS feed: (title, permalink, image_url)."""
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">',
    ]
    for title, permalink, image_url in entries:
        parts.append(
            "<entry>"
            f"<title>{title}</title>"
            f'<link href="{permalink}"/>'
            f'<media:thumbnail url="{image_url}"/>'
            f'<content type="html">&lt;img src="{image_url}" /&gt;</content>'
            "</entry>"
        )
    parts.append("</feed>")
    return "".join(parts).encode("utf-8")


SAMPLE_RSS = _rss_feed(
    [
        (
            "When BTC dumps",
            "https://www.reddit.com/r/cryptocurrencymemes/comments/1/",
            "https://i.redd.it/meme1.jpg",
        ),
        (
            "ETH gas fees",
            "https://www.reddit.com/r/cryptocurrencymemes/comments/2/",
            "https://i.redd.it/meme2.png",
        ),
    ]
)


def _ok_rss_response(body: bytes = SAMPLE_RSS) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.content = body
    return response


def test_meme_gemini_selection_success():
    provider = RedditGeminiMemeProvider(TestConfig)
    with patch("app.providers.meme_provider.requests.get", return_value=_ok_rss_response()):
        with patch("app.providers.meme_provider.time.sleep"):
            with patch(
                "app.providers.meme_provider.generate",
                return_value='{"index": 0, "reason": "matches bitcoin humor"}',
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
    assert data["image_url"] == "https://i.redd.it/meme1.jpg"


def test_meme_gemini_down_uses_top_upvotes():
    provider = RedditGeminiMemeProvider(TestConfig)
    with patch("app.providers.meme_provider.requests.get", return_value=_ok_rss_response()):
        with patch("app.providers.meme_provider.time.sleep"):
            with patch(
                "app.providers.meme_provider.generate",
                side_effect=GeminiError("down"),
            ):
                data = provider.fetch({"interested_assets": ["ethereum"]})

    assert data["selected_by"] == "upvotes_fallback"
    # First RSS entry gets the highest synthetic rank score.
    assert data["title"] == "When BTC dumps"


def test_meme_skips_failed_subreddit_and_uses_others():
    fail = MagicMock()
    fail.status_code = 403
    fail.content = b""
    ok = _ok_rss_response()

    provider = RedditGeminiMemeProvider(TestConfig)
    with patch(
        "app.providers.meme_provider.requests.get",
        side_effect=[fail, ok],
    ):
        with patch("app.providers.meme_provider.time.sleep"):
            with patch(
                "app.providers.meme_provider.generate",
                return_value='{"index": 0, "reason": "ok"}',
            ):
                data = provider.fetch({})

    assert data["selected_by"] == "gemini"
    assert data["title"] == "When BTC dumps"


def test_meme_stops_after_enough_candidates():
    many = _rss_feed(
        [
            (
                f"Meme {i}",
                f"https://www.reddit.com/r/cryptocurrencymemes/comments/{i}/",
                f"https://i.redd.it/meme{i}.jpg",
            )
            for i in range(15)
        ]
    )
    get_mock = MagicMock(return_value=_ok_rss_response(many))

    provider = RedditGeminiMemeProvider(TestConfig)
    with patch("app.providers.meme_provider.requests.get", get_mock):
        with patch("app.providers.meme_provider.time.sleep"):
            with patch(
                "app.providers.meme_provider.generate",
                return_value='{"index": 0, "reason": "ok"}',
            ):
                data = provider.fetch({})

    # First sub already fills the target; do not call remaining subs (avoids 429).
    assert get_mock.call_count == 1
    assert data["title"] == "Meme 0"


def test_meme_reddit_down_raises_for_outer_fallback():
    provider = RedditGeminiMemeProvider(TestConfig)
    with patch(
        "app.providers.meme_provider.requests.get",
        side_effect=requests.Timeout(),
    ):
        with patch("app.providers.meme_provider.time.sleep"):
            with pytest.raises(requests.Timeout):
                provider.fetch({})


def test_meme_static_fallback():
    data = RedditGeminiMemeProvider(TestConfig).static_fallback({})
    assert data["fallback"] is True
    assert data["selected_by"] == "static"
