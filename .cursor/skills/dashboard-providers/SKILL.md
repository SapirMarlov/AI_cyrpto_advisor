---
name: dashboard-providers
description: >
  Add, replace, or swap AI Crypto Advisor dashboard providers (prices, news,
  insight, meme). Use when changing PRICE_PROVIDER, NEWS_PROVIDER, AI_PROVIDER,
  or MEME_PROVIDER; editing registry.py or BaseProvider; adding a new free API
  adapter; or replacing CoinGecko, CryptoPanic, RSS, Gemini, template, or Reddit
  meme implementations.
---

# Dashboard Providers

## When to use

- User asks to add, replace, or swap a dashboard provider
- Editing `backend/app/providers/` or `registry.py`
- Changing `PRICE_PROVIDER` / `NEWS_PROVIDER` / `AI_PROVIDER` / `MEME_PROVIDER`
- Wiring a new free/public API behind a section

Human-facing detail: `docs/providers.md`. Read that file if payload shapes or env lists are unclear.

## Decide first: swap vs add

| Goal | Action |
| --- | --- |
| Use an **already registered** name | Change only `backend/.env` (and restart Flask) |
| Use a **new** implementation | Implement class → register → config → tests → set env |

Do not invent a new selector env var unless adding a **new section**. Reuse the four existing selectors.

## Current registry map

| Section | Env var | Names |
| --- | --- | --- |
| `prices` | `PRICE_PROVIDER` | `coingecko` |
| `news` | `NEWS_PROVIDER` | `cryptopanic`, `rss` |
| `insight` | `AI_PROVIDER` | `gemini`, `template` |
| `meme` | `MEME_PROVIDER` | `reddit_gemini` (Reddit Atom RSS + Gemini) |

Unknown env values fall back to section defaults in `registry.py` (`_DEFAULTS`).

Common swaps:

```env
NEWS_PROVIDER=rss
AI_PROVIDER=template
```

## Add a provider (checklist)

Copy and track:

```
- [ ] 1. Subclass BaseProvider
- [ ] 2. Register in PROVIDER_IMPLEMENTATIONS
- [ ] 3. Config + .env.example (if new secrets/URLs)
- [ ] 4. Set section env var to new name
- [ ] 5. Tests: success + failure/fallback
- [ ] 6. Update docs/providers.md if map/shapes change
```

### 1. Class

Path: `backend/app/providers/` (extend existing module or add one file).

```python
from app.providers.base_provider import BaseProvider

class MyNewsProvider(BaseProvider):
    """Short description."""

    section = "news"       # prices | news | insight | meme
    name = "my_source"     # must match registry key

    def __init__(self, config=None):
        """Store provider config."""
        self.config = config

    def fetch(self, context: dict) -> dict:
        """Fetch live data. Raise on failure."""
        timeout = float(getattr(self.config, "PROVIDER_HTTP_TIMEOUT", 5))
        # HTTP with timeout; map external JSON → section payload shape
        ...

    def static_fallback(self, context: dict) -> dict:
        """Safe payload when live + cache fail."""
        ...
```

Hard rules:

- `fetch` returns a **dict** or **raises** — let `run_provider` do live → cache → static
- Match the section payload shape (see below); do not invent UI-breaking fields as required
- Timeouts on all outbound calls; free/public APIs only for MVP
- Never leak API keys in responses or logs; validate/map untrusted external content
- One-line docstrings on methods (project backend convention)

### 2. Register

In `backend/app/providers/registry.py`:

1. Import the class
2. Add under the correct section in `PROVIDER_IMPLEMENTATIONS`
3. Change `_DEFAULTS` only if this should become the default

### 3. Config

If needed, add keys on `Config` in `backend/app/config.py` and document in `backend/.env.example`. Never commit `backend/.env`.

### 4. Activate

```env
NEWS_PROVIDER=my_source
```

Restart: `python backend/run.py` (venv active, from repo root).

### 5. Tests

Under `backend/tests/`, at least:

- Happy-path `fetch` with mocked HTTP
- Failure path (timeout / non-200) so cache or `static_fallback` runs

Run: `pytest backend/tests` with `.venv` active.

## Payload shapes (stable)

**prices:** `{ "prices": { "<asset>": { "usd", "change_24h", "market_cap", "volume_24h", "last_updated_at", "coingecko_id" } } }`

**news:** `{ "items": [ { "title", "url", "source", "published_at" } ] }`

**insight:** `{ "insight_text", "generated_by" }`

**meme:** `{ "title", "image_url", "permalink", "subreddit", "upvotes", "num_comments", "selected_by", "reason" }`

Static fallbacks may set `"fallback": true`.

## Runtime (do not bypass)

```
dashboard_service → build_registry(config) → run_provider(...) → per-section dashboard payload
```

One section failure must not fail the whole dashboard.

## Done when

- [ ] Registered and selectable via env
- [ ] Success + failure tests pass
- [ ] No secrets committed
- [ ] `docs/providers.md` updated if the public map or shapes changed
- [ ] Ask before committing (git workflow)
