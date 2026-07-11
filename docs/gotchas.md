# Gotchas and MVP runbook

Short operational notes for the next iteration. Prefer fixing the root cause when practical; keep this file for durable pitfalls.

---

## Auth and sessions

- Session cookie is `HttpOnly`, `SameSite=Lax`, and `Secure` **only when** `FLASK_ENV=production`. Local HTTP clients need `Secure=False` (default in development / tests).
- Frontend must call the API with `credentials: "include"`. Do not store session tokens in `localStorage` / `sessionStorage` (theme preference is the only localStorage use).
- Idle timeout is 24h (`last_active_at`); absolute lifetime is 7d from `created_at`. Sliding renewal cannot extend past the absolute cap.
- Logout deletes the server-side session row and clears the cookie. A stolen cookie after logout is useless.
- CORS: Vite origin must appear in `CORS_ORIGINS`. Prefer `127.0.0.1` over `localhost` on Windows so the browser does not hit IPv6 `::1` while Flask listens on IPv4.
- **Deploy (Vercel + Render):** keep cookies first-party via the Vercel `/api` rewrite. Production `VITE_API_BASE_URL` must be **empty** so the browser calls `https://your-app.vercel.app/api/...`. Do **not** set `VITE_API_BASE_URL` to the Render URL — with `SameSite=Lax`, cross-site credentialed fetches will not keep the session. Do not set cookie `Domain` (host-only on the Vercel host). Still set `CORS_ORIGINS` to the Vercel origin for direct API hits / safety.

## Rate limiting

- Login rate limit is **in-memory** (IP + email). It resets when the Flask process restarts and is **not** shared across workers.
- Production uses **one** gunicorn worker while SQLite lives on a Render disk; more workers would not share the rate-limit map and can contend on SQLite.
- Signup is not rate-limited in the MVP. Add if abuse appears.
- Failed-login tests can flake if the window is time-based and the clock is not controlled — inject or freeze time if that shows up.

## Providers

- Every section uses live → cache → static fallback. Client-facing section errors are generic (`Provider temporarily unavailable`); details stay in server logs.
- Timeouts default to `PROVIDER_HTTP_TIMEOUT` (5s). Cache TTL is `PROVIDER_CACHE_TTL` (300s). Fresh (unexpired) cache is served before live provider calls so dashboard reloads do not burn rate limits; expired cache is only used as a stale fallback after a live failure.
- Meme provider uses a 1-hour TTL and a per-user per-UTC-day cache key so "meme of the day" is not refetched on every page load.
- Keys: `GEMINI_API_KEY` required for `AI_PROVIDER=gemini` and `MEME_PROVIDER=reddit_gemini`. `CRYPTOPANIC_API_KEY` only for `NEWS_PROVIDER=cryptopanic`. CoinGecko works keyless; demo/pro keys raise limits.
- Prefer `GEMINI_MODEL=gemini-flash-lite-latest` (or another current free-tier alias). Older ids like `gemini-2.0-flash` can return HTTP 429 with `limit: 0` even when the key is valid — that is a model/quota mismatch, not a temporary rate limit. Insight then shows `generated_by: template_fallback`.
- Offline / Playwright: set `PRICE_PROVIDER=static`, `NEWS_PROVIDER=static`, `AI_PROVIDER=template`, `MEME_PROVIDER=static`.
- Reddit anonymous rate limits (HTTP 429) are common if too many subreddits are configured — prefer a single `REDDIT_MEME_SUBREDDITS` value; extras are fallback-only after an empty first sub.

## Frontend

- Theme preference is stored in `localStorage`; auth is cookie-only.
- Feedback votes are optimistic and **not** hydrated on dashboard reload (no `GET /api/feedback/votes` yet).
- Vote `item_id` derivation: news → `url`; meme → `permalink` (fallback `image_url`); insight → `insight-{YYYY-MM-DD}` from `generated_at`. Prices are not votable.
- Panel errors are independent — one failed section must not blank the whole dashboard.

## Testing

- Backend: activate `.venv` and set `PYTHONPATH=backend` (or run from an env that already imports `app`).
- Prefer pytest fixtures / temp DB — do not share `backend/instance/app.db` with the test suite.
- Playwright (`e2e/`): `npm install`, `npm run install:browsers` once, then `npm test`. It starts Flask + Vite (frontend on **5174** to avoid clashing with a normal `npm run dev` on 5173) and uses a temp SQLite file under `e2e/.tmp/`.
- Do not delete the e2e DB after the webServer has already applied schema; `e2e/run_backend.py` resets the file **before** `create_app()`.
- Cookie assertions: parse `Set-Cookie` carefully; clear cookies between cases when reusing the Flask test `client`.
- Provider unit tests must mock HTTP — never hit live networks in pytest/Vitest.

## Secrets and config

- Never commit `.env`. Copy from `backend/.env.example` / `frontend/.env.example`. Committed Vite mode files: `frontend/.env.development` and `frontend/.env.production` (empty API base).
- Set a strong `SECRET_KEY` outside local play. Production **refuses to start** if `SECRET_KEY` is still the hardcoded default.
- Unhandled exceptions return a safe `{ ok: false, error: { code: "internal_error", ... } }` envelope — no stack traces to clients. Keep `DEBUG` off in production.

## Public deploy (Vercel + Render)

1. **Render:** apply [`render.yaml`](../render.yaml) (or create a web service with `rootDir: backend`, gunicorn start, disk mount `/var/data`, `DATABASE_PATH=/var/data/app.db`). Set `CORS_ORIGINS` to your Vercel URL and provider keys. Persistent disks need a paid plan and a single instance.
2. **Vercel:** project root = `frontend`. Replace `YOUR-RENDER-SERVICE` in [`frontend/vercel.json`](../frontend/vercel.json) with the Render hostname. Build uses empty `VITE_API_BASE_URL` from `.env.production`.
3. **Smoke:** signup → onboarding → dashboard → vote → logout on the Vercel URL. Confirm `session_id` is set for the Vercel host (Application → Cookies), not for `onrender.com`.

## Manual smoke (demo)

1. `python backend\run.py` and `cd frontend; npm run dev`
2. Signup → onboarding → dashboard → thumbs up on a news item → log out
3. Optionally unset provider keys to confirm section fallbacks still render
