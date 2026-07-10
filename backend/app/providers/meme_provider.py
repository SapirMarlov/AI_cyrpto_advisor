from __future__ import annotations

import json
import re
from typing import Any

import requests

from app.providers.base_provider import BaseProvider
from app.providers.gemini_client import GeminiError, generate

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp")


def _static_meme() -> dict:
    """Return a safe static meme payload."""
    return {
        "title": "HODL on — meme feed temporarily unavailable",
        "image_url": "https://via.placeholder.com/600x400.png?text=Crypto+Meme",
        "permalink": "https://www.reddit.com/r/cryptocurrencymemes/",
        "subreddit": "cryptocurrencymemes",
        "upvotes": 0,
        "num_comments": 0,
        "reason": "static fallback",
        "selected_by": "static",
        "fallback": True,
    }


def _is_image_post(post: dict) -> bool:
    """Return True if the Reddit post looks like an image."""
    url = (post.get("url") or "").lower().split("?")[0]
    if url.endswith(IMAGE_EXTENSIONS):
        return True
    if post.get("post_hint") == "image":
        return True
    preview = post.get("preview") or {}
    images = preview.get("images") or []
    return bool(images)


def _candidate_from_post(post: dict) -> dict | None:
    """Map a Reddit post to a meme candidate, or None."""
    if not _is_image_post(post):
        return None
    title = (post.get("title") or "").strip()
    image_url = post.get("url") or ""
    if not title or not image_url:
        return None
    permalink = post.get("permalink") or ""
    if permalink and not permalink.startswith("http"):
        permalink = f"https://www.reddit.com{permalink}"
    return {
        "title": title,
        "image_url": image_url,
        "permalink": permalink,
        "subreddit": post.get("subreddit") or "",
        "upvotes": int(post.get("ups") or 0),
        "num_comments": int(post.get("num_comments") or 0),
    }


def discover_reddit_memes(config: Any) -> list[dict]:
    """Fetch image meme candidates from configured subreddits."""
    timeout = float(getattr(config, "PROVIDER_HTTP_TIMEOUT", 5))
    user_agent = getattr(config, "REDDIT_USER_AGENT", "AICryptoAdvisor/0.1")
    raw_subs = getattr(config, "REDDIT_MEME_SUBREDDITS", "cryptocurrencymemes")
    subreddits = [s.strip() for s in str(raw_subs).split(",") if s.strip()]
    headers = {"User-Agent": user_agent}

    candidates: list[dict] = []
    last_error: Exception | None = None
    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/hot.json"
        try:
            response = requests.get(
                url,
                params={"limit": 25},
                headers=headers,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            last_error = exc
            continue
        if response.status_code != 200:
            last_error = ValueError(f"reddit returned HTTP {response.status_code} for r/{sub}")
            continue
        try:
            payload = response.json()
        except ValueError as exc:
            last_error = exc
            continue
        children = ((payload.get("data") or {}).get("children")) or []
        for child in children:
            post = (child or {}).get("data") or {}
            candidate = _candidate_from_post(post)
            if candidate:
                candidates.append(candidate)

    if not candidates:
        if last_error:
            raise last_error
        raise ValueError("reddit returned no image meme candidates")

    # Deduplicate by image url, keep highest upvotes first.
    by_url: dict[str, dict] = {}
    for item in candidates:
        existing = by_url.get(item["image_url"])
        if existing is None or item["upvotes"] > existing["upvotes"]:
            by_url[item["image_url"]] = item
    unique = sorted(by_url.values(), key=lambda m: m["upvotes"], reverse=True)
    return unique[:15]


def _pick_top_upvoted(candidates: list[dict], reason: str, selected_by: str) -> dict:
    """Pick the candidate with the most upvotes."""
    top = max(candidates, key=lambda m: m["upvotes"])
    return {
        **top,
        "reason": reason,
        "selected_by": selected_by,
    }


def _parse_gemini_choice(text: str, candidate_count: int) -> tuple[int, str]:
    """Parse Gemini's JSON meme choice from free text."""
    # Prefer fenced or raw JSON object.
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("gemini meme selection missing JSON")
    payload = json.loads(match.group(0))
    index = int(payload.get("index"))
    reason = str(payload.get("reason") or "selected by gemini")
    if index < 0 or index >= candidate_count:
        raise ValueError("gemini meme index out of range")
    return index, reason


def select_meme_with_gemini(candidates: list[dict], context: dict, config: Any) -> dict:
    """Ask Gemini to pick one meme from the candidates."""
    prefs = {
        "interested_assets": context.get("interested_assets") or [],
        "investor_type": context.get("investor_type"),
        "content_preferences": context.get("content_preferences") or [],
    }
    listed = [
        {
            "index": i,
            "title": c["title"],
            "subreddit": c["subreddit"],
            "upvotes": c["upvotes"],
            "num_comments": c["num_comments"],
        }
        for i, c in enumerate(candidates)
    ]
    prompt = (
        "Pick the single most viral and relevant crypto meme for this user.\n"
        f"User preferences: {json.dumps(prefs)}\n"
        f"Candidates: {json.dumps(listed)}\n"
        'Respond with JSON only: {"index": <int>, "reason": "<short reason>"}'
    )
    text = generate(prompt, config)
    index, reason = _parse_gemini_choice(text, len(candidates))
    chosen = candidates[index]
    return {**chosen, "reason": reason, "selected_by": "gemini"}


class RedditGeminiMemeProvider(BaseProvider):
    """Meme provider using Reddit discovery and Gemini selection."""

    section = "meme"
    name = "reddit_gemini"

    def __init__(self, config: Any | None = None):
        """Store provider config."""
        self.config = config

    def fetch(self, context: dict) -> dict:
        """Discover Reddit memes and pick one with Gemini."""
        candidates = discover_reddit_memes(self.config)
        try:
            return select_meme_with_gemini(candidates, context, self.config)
        except (GeminiError, ValueError, json.JSONDecodeError, TypeError, KeyError):
            return _pick_top_upvoted(
                candidates,
                reason="gemini unavailable; selected highest upvotes",
                selected_by="upvotes_fallback",
            )

    def static_fallback(self, context: dict) -> dict:
        """Return a static meme when live fetch fails."""
        return _static_meme()
