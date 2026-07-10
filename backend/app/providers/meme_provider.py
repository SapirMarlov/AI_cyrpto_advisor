from __future__ import annotations

import html
import json
import re
import time
from datetime import datetime, timezone
from typing import Any
from xml.etree import ElementTree as ET

import requests

from app.providers.base_provider import BaseProvider
from app.providers.gemini_client import GeminiError, generate

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp")
ATOM_NS = {
    "a": "http://www.w3.org/2005/Atom",
    "m": "http://search.yahoo.com/mrss/",
}
IMG_SRC_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)
LINK_HREF_RE = re.compile(
    r'<a href="(https://(?:i\.redd\.it|preview\.redd\.it)/[^"]+)"',
    re.IGNORECASE,
)
BRACKET_LINK_RE = re.compile(
    r'<a href="(https://[^"]+)"[^>]*>\[link\]</a>',
    re.IGNORECASE,
)


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


def _looks_like_image_url(url: str) -> bool:
    """Return True if the URL path looks like an image file."""
    path = (url or "").lower().split("?")[0]
    return path.endswith(IMAGE_EXTENSIONS)


def _image_url_from_entry(entry: ET.Element) -> str | None:
    """Extract an image URL from an Atom entry (media tags or HTML content)."""
    for tag in ("content", "thumbnail"):
        for el in entry.findall(f".//m:{tag}", ATOM_NS):
            url = html.unescape(el.get("url") or "").strip()
            if url and (_looks_like_image_url(url) or "preview.redd.it" in url or "i.redd.it" in url):
                return url

    content_el = entry.find("a:content", ATOM_NS)
    raw = content_el.text if content_el is not None else ""
    text = html.unescape(raw or "")

    match = IMG_SRC_RE.search(text)
    if match:
        return match.group(1).strip()

    match = LINK_HREF_RE.search(text)
    if match:
        return match.group(1).strip()

    match = BRACKET_LINK_RE.search(text)
    if match:
        url = match.group(1).strip()
        if _looks_like_image_url(url):
            return url

    return None


def _candidate_from_rss_entry(entry: ET.Element, subreddit: str, rank: int) -> dict | None:
    """Map an Atom RSS entry to a meme candidate, or None."""
    title = (entry.findtext("a:title", default="", namespaces=ATOM_NS) or "").strip()
    image_url = _image_url_from_entry(entry)
    if not title or not image_url:
        return None

    link_el = entry.find("a:link", ATOM_NS)
    permalink = (link_el.get("href") if link_el is not None else "") or ""
    if permalink and not permalink.startswith("http"):
        permalink = f"https://www.reddit.com{permalink}"

    # RSS has no score fields; preserve hot/new order as a weak rank signal.
    return {
        "title": title,
        "image_url": image_url,
        "permalink": permalink,
        "subreddit": subreddit,
        "upvotes": max(0, 1000 - rank),
        "num_comments": 0,
    }


def _fetch_subreddit_rss(sub: str, headers: dict, timeout: float) -> bytes:
    """Fetch a subreddit Atom RSS feed (no retry — 429 retries worsen rate limits)."""
    url = f"https://www.reddit.com/r/{sub}/.rss"
    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code != 200:
        raise ValueError(f"reddit returned HTTP {response.status_code} for r/{sub}")
    return response.content


def discover_reddit_memes(config: Any) -> list[dict]:
    """Fetch image meme candidates from configured subreddits via Atom RSS."""
    timeout = float(getattr(config, "PROVIDER_HTTP_TIMEOUT", 5))
    user_agent = getattr(config, "REDDIT_USER_AGENT", "AICryptoAdvisor/0.1")
    raw_subs = getattr(config, "REDDIT_MEME_SUBREDDITS", "cryptocurrencymemes")
    subreddits = [s.strip() for s in str(raw_subs).split(",") if s.strip()]
    headers = {"User-Agent": user_agent, "Accept": "application/atom+xml,application/xml,text/xml"}
    target_count = 15

    candidates: list[dict] = []
    last_error: Exception | None = None
    for index, sub in enumerate(subreddits):
        if index > 0:
            # Reddit rate-limits bursty anonymous RSS; space fallback sub calls.
            time.sleep(1.0)
        try:
            payload = _fetch_subreddit_rss(sub, headers, timeout)
            root = ET.fromstring(payload)
        except requests.RequestException as exc:
            last_error = exc
            continue
        except (ET.ParseError, ValueError) as exc:
            last_error = exc
            continue

        for rank, entry in enumerate(root.findall("a:entry", ATOM_NS)):
            candidate = _candidate_from_rss_entry(entry, sub, rank)
            if candidate:
                candidates.append(candidate)

        # One successful sub is enough for meme-of-the-day. Extra RSS calls
        # burn Reddit's anonymous rate limit and force stale-cache fallbacks.
        if candidates:
            break

    if not candidates:
        if last_error:
            raise last_error
        raise ValueError("reddit returned no image meme candidates")

    # Deduplicate by image url, keep highest rank score first.
    by_url: dict[str, dict] = {}
    for item in candidates:
        existing = by_url.get(item["image_url"])
        if existing is None or item["upvotes"] > existing["upvotes"]:
            by_url[item["image_url"]] = item
    unique = sorted(by_url.values(), key=lambda m: m["upvotes"], reverse=True)
    return unique[:target_count]


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
    # Meme of the day does not need 5-minute refreshes; longer TTL avoids Reddit 429s.
    cache_ttl_seconds = 3600

    def __init__(self, config: Any | None = None):
        """Store provider config."""
        self.config = config

    def cache_key(self, context: dict) -> str:
        """Cache one meme selection per user per UTC day."""
        user_id = context.get("user_id", "anon")
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{self.section}:{self.name}:{user_id}:{day}"

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
