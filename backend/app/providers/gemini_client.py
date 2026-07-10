from __future__ import annotations

from typing import Any

import requests


class GeminiError(Exception):
    """Raised when a Gemini API call fails."""


def generate(prompt: str, config: Any) -> str:
    """Call Gemini and return the first text part."""
    api_key = getattr(config, "GEMINI_API_KEY", "") or ""
    if not api_key.strip():
        raise GeminiError("GEMINI_API_KEY is not configured")

    model = getattr(config, "GEMINI_MODEL", "gemini-1.5-flash")
    timeout = float(getattr(config, "PROVIDER_HTTP_TIMEOUT", 5))
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )

    try:
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=timeout,
        )
    except requests.Timeout as exc:
        raise GeminiError("gemini request timed out") from exc
    except requests.RequestException as exc:
        raise GeminiError(f"gemini request failed: {exc}") from exc

    if response.status_code != 200:
        raise GeminiError(f"gemini returned HTTP {response.status_code}")

    try:
        payload = response.json()
        candidates = payload.get("candidates") or []
        if not candidates:
            raise GeminiError("gemini response missing candidates")
        parts = candidates[0].get("content", {}).get("parts") or []
        if not parts or "text" not in parts[0]:
            raise GeminiError("gemini response missing text")
        text = parts[0]["text"]
        if not isinstance(text, str) or not text.strip():
            raise GeminiError("gemini returned empty text")
        return text.strip()
    except GeminiError:
        raise
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        raise GeminiError("gemini response malformed") from exc
