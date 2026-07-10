from unittest.mock import MagicMock, patch

import pytest
import requests

from app.config import TestConfig
from app.providers.gemini_client import GeminiError, generate


def _ok_response(text: str = "hello from gemini") -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": text}]}}]
    }
    return response


def test_generate_success():
    with patch("app.providers.gemini_client.requests.post", return_value=_ok_response()) as post:
        text = generate("Say hi", TestConfig)

    assert text == "hello from gemini"
    assert post.called
    _, kwargs = post.call_args
    assert kwargs["headers"]["x-goog-api-key"] == TestConfig.GEMINI_API_KEY
    assert kwargs["timeout"] == TestConfig.PROVIDER_HTTP_TIMEOUT


def test_generate_missing_key():
    class NoKey:
        GEMINI_API_KEY = ""
        GEMINI_MODEL = "gemini-1.5-flash"
        PROVIDER_HTTP_TIMEOUT = 2

    with pytest.raises(GeminiError, match="not configured"):
        generate("prompt", NoKey())


def test_generate_timeout():
    with patch(
        "app.providers.gemini_client.requests.post",
        side_effect=requests.Timeout(),
    ):
        with pytest.raises(GeminiError, match="timed out"):
            generate("prompt", TestConfig)


def test_generate_non_200():
    response = MagicMock()
    response.status_code = 500
    with patch("app.providers.gemini_client.requests.post", return_value=response):
        with pytest.raises(GeminiError, match="HTTP 500"):
            generate("prompt", TestConfig)


def test_generate_malformed_payload():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"candidates": []}
    with patch("app.providers.gemini_client.requests.post", return_value=response):
        with pytest.raises(GeminiError, match="missing candidates"):
            generate("prompt", TestConfig)
