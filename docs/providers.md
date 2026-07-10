# Providers guide

How dashboard section providers work, how to **switch** the active implementation, and how to **add** a new one.

Code lives under `backend/app/providers/`. Selection happens in `registry.py` from env vars in `backend/.env`.

Agent workflow: `.cursor/skills/dashboard-providers/SKILL.md` (use when adding or swapping providers).

---

## 1. Sections and current implementations

| Section | Env var | Registry key | Built-in names |
| --- | --- | --- | --- |
| Prices | `PRICE_PROVIDER` | `prices` | `coingecko` |
| News | `NEWS_PROVIDER` | `news` | `cryptopanic`, `rss` |
| AI insight | `AI_PROVIDER` | `insight` | `gemini`, `template` |
| Meme | `MEME_PROVIDER` | `meme` | `reddit_gemini` |

Defaults (if the env var is missing or names an unknown provider):

| Section | Default |
| --- | --- |
| `prices` | `coingecko` |
| `news` | `rss` (Cointelegraph) |
| `insight` | `gemini` |
| `meme` | `reddit_gemini` |

Unknown names fall back to the default for that section (they do not crash the app).

---

## 2. How to change the active provider (registry / env)

You do **not** need to edit Python to swap among already-registered implementations. Set the selector in `backend/.env` (see `backend/.env.example`):

```env
PRICE_PROVIDER=coingecko
NEWS_PROVIDER=rss
AI_PROVIDER=template
MEME_PROVIDER=reddit_gemini
```

Then restart Flask (`python backend\run.py`).

### What the registry does

`build_registry(config)` in `backend/app/providers/registry.py`:

1. Reads `PRICE_PROVIDER` / `NEWS_PROVIDER` / `AI_PROVIDER` / `MEME_PROVIDER` from config.
2. Looks up the class in `PROVIDER_IMPLEMENTATIONS[section][name]`.
3. Instantiates `cls(config)` and returns `{ "prices": ..., "news": ..., "insight": ..., "meme": ... }`.

```python
PROVIDER_IMPLEMENTATIONS = {
    "prices": {
        "coingecko": CoinGeckoPriceProvider,
    },
    "news": {
        "cryptopanic": CryptoPanicNewsProvider,
        "rss": RssNewsProvider,
    },
    "insight": {
        "gemini": GeminiInsightProvider,
        "template": TemplateInsightProvider,
    },
    "meme": {
        "reddit_gemini": RedditGeminiMemeProvider,
    },
}
```

**To use a provider that is already listed above:** only change the matching env var.

**To use a brand-new implementation:** register it in `PROVIDER_IMPLEMENTATIONS` (and usually add a config key) — see section 3.

### Common swaps

| Goal | Change |
| --- | --- |
| News via Cointelegraph RSS (default) | `NEWS_PROVIDER=rss` |
| News via CryptoPanic | `NEWS_PROVIDER=cryptopanic` (+ API key) |
| Insight without Gemini key | `AI_PROVIDER=template` |
| Prices | Keep `PRICE_PROVIDER=coingecko` (only option today) |

Shared knobs:

| Variable | Role |
| --- | --- |
| `PROVIDER_HTTP_TIMEOUT` | Outbound HTTP timeout (seconds) |
| `PROVIDER_CACHE_TTL` | Cache TTL for successful live fetches (seconds) |

Provider-specific keys (`CRYPTOPANIC_API_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL`, CoinGecko keys, Reddit settings) stay in `.env` as documented in `.env.example`. Default model is `gemini-flash-lite-latest`; older ids like `gemini-2.0-flash` may return HTTP 429 with free-tier `limit: 0` and force insight `template_fallback`.

**Reddit memes:** `reddit_gemini` discovers posts via keyless Atom RSS (`/r/{sub}/.rss`). Reddit’s unauthenticated `.json` endpoints return HTTP 403, so do not switch back to JSON without OAuth credentials. Keep `REDDIT_MEME_SUBREDDITS` short (meme-focused subs only) — extra calls hit anonymous HTTP 429 rate limits.

---

## 3. How to add a new provider

### Step 1 — Implement the class

Create or extend a module under `backend/app/providers/` (e.g. `price_provider.py` or a new file). Subclass `BaseProvider`:

```python
from app.providers.base_provider import BaseProvider

class MyPriceProvider(BaseProvider):
    """Short description."""

    section = "prices"   # must match registry section
    name = "my_source"   # must match the registry map key

    def __init__(self, config=None):
        """Store provider config."""
        self.config = config

    def fetch(self, context: dict) -> dict:
        """Fetch live data. Raise on failure (cache/static fallback will run)."""
        # Use getattr(self.config, "PROVIDER_HTTP_TIMEOUT", 5) for timeouts.
        # Map external JSON into the section payload shape (below).
        ...

    def static_fallback(self, context: dict) -> dict:
        """Safe payload when live + cache both fail."""
        ...
```

Rules:

- `fetch` must return a **dict** matching the section shape, or raise.
- Do not catch-and-swallow in a way that returns empty success; let `run_provider` handle live → cache → static.
- Never put API keys in responses or logs.
- Treat third-party content as untrusted; validate/map before returning.

### Step 2 — Register it

In `backend/app/providers/registry.py`:

1. Import the class.
2. Add an entry under the right section in `PROVIDER_IMPLEMENTATIONS`:

```python
"prices": {
    "coingecko": CoinGeckoPriceProvider,
    "my_source": MyPriceProvider,  # new
},
```

3. Optionally change `_DEFAULTS` if this should be the new default.

### Step 3 — Wire config (if needed)

In `backend/app/config.py`, add any new env-backed settings (API keys, base URLs). Document them in `backend/.env.example`.

You do **not** need a new selector env var unless you introduce a **new section**. For an alternate implementation of an existing section, reuse `PRICE_PROVIDER` / `NEWS_PROVIDER` / `AI_PROVIDER` / `MEME_PROVIDER` and set the value to your new registry name:

```env
PRICE_PROVIDER=my_source
```

### Step 4 — Tests

Add at least:

- Happy-path `fetch` with mocked HTTP.
- Failure path (timeout / bad status) so cache or `static_fallback` is exercised.

See [testing-guide.md](./testing-guide.md).

---

## 4. Expected payload shapes (per section)

Keep these shapes stable so the dashboard service and future UI stay compatible.

**Prices**

```json
{
  "prices": {
    "bitcoin": {
      "usd": 60000,
      "change_24h": 1.2,
      "market_cap": 1.2e12,
      "volume_24h": 1e10,
      "last_updated_at": 1710000000,
      "coingecko_id": "bitcoin"
    }
  }
}
```

**News**

```json
{
  "items": [
    {
      "title": "...",
      "url": "https://...",
      "source": "...",
      "published_at": "..."
    }
  ]
}
```

**Insight**

```json
{
  "insight_text": "...",
  "generated_by": "gemini"
}
```

**Meme**

```json
{
  "title": "...",
  "image_url": "https://...",
  "permalink": "https://...",
  "subreddit": "...",
  "upvotes": 0,
  "num_comments": 0,
  "selected_by": "gemini",
  "reason": "..."
}
```

Static fallbacks may add `"fallback": true`.

---

## 5. Runtime flow (reminder)

```
dashboard_service
  → build_registry(config)     # pick classes from env
  → run_provider(provider, …)  # live → cache → static_fallback
  → per-section envelope in GET /api/dashboard/daily
```

One section failing does not fail the whole dashboard response.

---

## 6. Checklist

**Switch existing provider**

- [ ] Set `PRICE_PROVIDER` / `NEWS_PROVIDER` / `AI_PROVIDER` / `MEME_PROVIDER` in `backend/.env`
- [ ] Ensure required API keys for that implementation are set
- [ ] Restart the backend

**Add new provider**

- [ ] Subclass `BaseProvider` with `section`, `name`, `fetch`, `static_fallback`
- [ ] Register under `PROVIDER_IMPLEMENTATIONS` in `registry.py`
- [ ] Add config / `.env.example` keys if needed
- [ ] Set the section env var to the new name
- [ ] Add unit tests (success + failure/fallback)
