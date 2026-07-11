# Developer Guide

Practical guide for working on AI Crypto Advisor. For product architecture and security intent, see [mvp-architecture.md](./mvp-architecture.md). For ordered slices, see [roadmap.md](./roadmap.md).

**Keep this guide current:** when setup steps, env vars, APIs, folder layout, or workflow change, update this file and the root [README.md](../README.md) in the same change (or immediately after). Test runner/fixture changes belong in [testing-guide.md](./testing-guide.md). See `.cursor/rules/docs-maintenance.mdc`.

---

## 1. Repository layout

```
AI Crypto advisor/
├── README.md                 # Overview + quick start
├── docs/
│   ├── developer-guide.md    # This file
│   ├── providers.md          # Add / swap provider implementations
│   ├── testing-guide.md      # Run/write tests and gates
│   ├── gotchas.md            # Ops pitfalls and MVP runbook
│   ├── mvp-architecture.md
│   └── roadmap.md
├── backend/
│   ├── run.py                # Dev entry: Flask on :5000
│   ├── requirements.txt
│   ├── .env                  # Local secrets (gitignored)
│   ├── app/
│   │   ├── __init__.py       # create_app, blueprint registration
│   │   ├── config.py
│   │   ├── db/               # connection, migrate, schema.sql
│   │   ├── repositories/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── providers/        # Swappable news/prices/insight/meme adapters
│   │   └── utils/            # response envelope, validation, auth_guard
│   ├── instance/             # SQLite DB file (local)
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── .env.example          # VITE_API_BASE_URL
│   └── src/
│       ├── App.tsx           # Router + guards
│       ├── main.tsx
│       ├── auth/             # AuthContext + route guards
│       ├── pages/            # Login, Signup, Onboarding, Dashboard
│       ├── components/       # ui (shadcn), dashboard panels, ThemeToggle
│       ├── services/apiClient.ts
│       └── theme/            # Cosmic Night light/dark preference
├── e2e/                      # Playwright critical-path browser tests
├── .venv/                    # Project-local Python venv (gitignored)
└── .cursor/rules/            # Agent conventions
```

Providers how-to (add / swap implementations): **[providers.md](./providers.md)**.

---

## 2. Environment setup

### 2.1 Python virtualenv (required for backend)

Always use the project-local `.venv` at the **repo root**. Do not install backend deps into the global Python environment.

```powershell
# from repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Confirm the active interpreter:

```powershell
python -c "import sys; print(sys.executable)"
# should point under ...\AI Crypto advisor\.venv\...
```

### 2.2 Frontend

```powershell
cd frontend
npm install
```

### 2.3 Environment variables

Secrets live in `backend/.env` (gitignored). Prefer documenting new keys in `backend/.env.example` when that file exists.

| Variable | Where | Default / notes |
| --- | --- | --- |
| `FLASK_ENV` | backend | `development` — sets `DEBUG` and cookie `Secure` in production |
| `SECRET_KEY` | backend | Dev default in config; **set a strong value** outside local play |
| `DATABASE_PATH` | backend | `backend/instance/app.db` |
| `TEST_DATABASE_PATH` | backend tests | In-memory SQLite URI when unset |
| `PRICE_PROVIDER` | backend | `coingecko` — see [providers.md](./providers.md) |
| `NEWS_PROVIDER` | backend | `rss` (Cointelegraph; or `cryptopanic`) |
| `AI_PROVIDER` | backend | `gemini` (or `template`) |
| `MEME_PROVIDER` | backend | `reddit_gemini` |
| `PROVIDER_HTTP_TIMEOUT` | backend | `5` seconds |
| `PROVIDER_CACHE_TTL` | backend | `300` seconds |
| `GEMINI_API_KEY` | backend | Required for `AI_PROVIDER=gemini` and meme selection |
| `CRYPTOPANIC_API_KEY` | backend | Required for `NEWS_PROVIDER=cryptopanic` |
| `COINGECKO_DEMO_API_KEY` / `COINGECKO_PRO_API_KEY` | backend | Optional; public API works without keys |
| `CORS_ORIGINS` | backend | Comma-separated origins; default `http://localhost:5173,http://127.0.0.1:5173` |
| `VITE_API_BASE_URL` | frontend | `http://127.0.0.1:5000` (prefer over `localhost` on Windows/IPv6) |

Session policy (code defaults in `backend/app/config.py`):

- Cookie: `session_id`, `HttpOnly`, `SameSite=Lax`, `Secure` only when `FLASK_ENV=production`
- Idle timeout: 24h; absolute lifetime: 7d
- Login rate limit: 5 attempts / 15 minutes per IP + email

---

## 3. Running locally

### Backend

```powershell
.\.venv\Scripts\Activate.ps1
python backend\run.py
```

- Base URL: `http://localhost:5000`
- Health: `GET /api/health` → `{ "ok": true, "data": { "status": "healthy" }, "error": null }`
- SQLite schema is applied on app init via `init_db`.

### Frontend

```powershell
cd frontend
npm run dev
```

API client uses `credentials: "include"` so session cookies work cross-origin in local dev. Flask-CORS is enabled with `supports_credentials=True` for origins in `CORS_ORIGINS` (default includes both `http://localhost:5173` and `http://127.0.0.1:5173`). Use `127.0.0.1` for the API base URL so browsers do not try IPv6 `localhost` (`::1`) against an IPv4-only Flask bind.

### Frontend routes

| Path | Guard | Page |
| --- | --- | --- |
| `/login`, `/signup` | Guest only | Auth forms |
| `/onboarding` | Authed + incomplete onboarding | Quiz |
| `/dashboard` | Authed + onboarding complete | Daily panels + votes |

### Useful scripts

| Command | Purpose |
| --- | --- |
| `python backend\run.py` | Start Flask |
| `pytest backend\tests` | Backend unit/route tests |
| `npm run dev` (in `frontend`) | Vite dev server |
| `npm test` (in `frontend`) | Vitest once |
| `npm run build` (in `frontend`) | Typecheck + production build |

---

## 4. Architecture (how code is layered)

Dependency order for new work:

**schema → repositories → services → routes → frontend**

| Layer | Responsibility |
| --- | --- |
| `routes/` | HTTP only: validate payload, call service, return envelope |
| `services/` | Business rules (auth, onboarding, dashboard aggregation, feedback) |
| `repositories/` | SQLite access; always scope by `user_id` from session for protected writes |
| `providers/` | External APIs behind swappable interfaces — [providers.md](./providers.md) |
| `utils/` | Shared envelope, validation, `login_required` |

### Response envelope (all APIs)

Success:

```json
{ "ok": true, "data": { }, "error": null }
```

Error:

```json
{ "ok": false, "data": null, "error": { "code": "string", "message": "string" } }
```

Helpers: `backend/app/utils/response.py`. Frontend types: `frontend/src/services/apiClient.ts`.

### Auth model

- Passwords hashed with bcrypt; never stored plaintext.
- Session token in HTTP-only cookie; identity from server session only (`g.current_user`).
- Never accept client-provided `user_id` for protected writes.
- Protected routes use `@login_required` from `app.utils.auth_guard`.

---

## 5. API reference (implemented vs planned)

### Implemented

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/api/health` | No | Smoke / readiness |
| `POST` | `/api/auth/signup` | No | Body: `{ email, password, name }` → 201 + session cookie |
| `POST` | `/api/auth/login` | No | Body: `{ email, password }`; rate limited |
| `POST` | `/api/auth/logout` | Session | Clears server session + cookie |
| `GET` | `/api/auth/me` | Session | Current user + onboarding state |
| `GET` | `/api/onboarding/questions` | Session | Static quiz questions |
| `POST` | `/api/onboarding/answers` | Session | Validates + saves preferences |
| `GET` | `/api/dashboard/daily` | Session | Per-section news/prices/insight/meme (partial success) |
| `POST` | `/api/feedback/vote` | Session | Body: `{ item_id, item_type, vote_type }`; upsert replace |

Dashboard returns **per-section** payloads (`news`, `prices`, `insight`, `meme`) so one provider failure does not fail the whole response. Feedback votes use replace-on-repeat for the same `(user, item_type, item_id)`. Client derives vote `item_id` from news `url`, meme `permalink`/`image_url`, and `insight-{YYYY-MM-DD}`. Unhandled server errors return a safe `internal_error` envelope (no stack traces).

---

## 6. Database

Schema: `backend/app/db/schema.sql`

| Table | Purpose |
| --- | --- |
| `users` | Email + password hash |
| `user_preferences` | Onboarding answers JSON + completion flag |
| `feedback_votes` | Unique vote per `(user_id, item_type, item_id)` |
| `provider_cache` | Cached provider payloads (Phase 4+) |
| `sessions` | Server-side session rows |

Migrations: `apply_schema` on init (idempotent `CREATE IF NOT EXISTS`). Prefer additive, reversible changes when evolving schema.

---

## 7. Testing

See **[testing-guide.md](./testing-guide.md)** for commands, fixtures, conventions, suite inventory, and gates.

Quick run:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "backend"
pytest backend\tests

cd frontend
npm test

cd ..\e2e
npm test
```

### Definition of done (slice)

1. Tests for the slice pass (see testing guide checklist).
2. No secrets committed.
3. Docs updated if public contracts/setup/test runners changed.
4. Ask before committing; after green tests, TODO branch merges into the phase branch automatically per git workflow.

---

## 8. Git workflow

Full rules: `.cursor/rules/git-workflow.mdc`.

```
master  ← stable; merge phase only with explicit user approval
  └── phase/<n>-<slug>
        └── <slice-id>-<slug>   e.g. p4-s3-price-provider
```

1. Start phase branch from clean `master`.
2. One TODO/slice branch per roadmap item.
3. After tests pass → merge TODO → phase (no extra ask).
4. When the phase is complete → **ask** before merging into `master`.
5. Commit only when the user asks; one logical change per commit; never commit `.env`.

Message format: `<type>: <imperative summary>` (`feat`, `fix`, `test`, `refactor`, `chore`, `docs`).

---

## 9. Agent / Cursor conventions

Project rules under `.cursor/rules/`:

| Rule | Focus |
| --- | --- |
| `mvp-delivery-standards.mdc` | Stack, slice size, roadmap order |
| `git-workflow.mdc` | Branches and commits |
| `backend-api-conventions.mdc` | Flask layering, envelope, providers |
| `frontend-mvp-conventions.mdc` | UI states, route guards, Composer prompts |
| `security-mvp-baseline.mdc` | Auth, validation, secrets |
| `testing-and-commit-gates.mdc` | Test gates and gotchas |
| `docs-maintenance.mdc` | Keep README + this guide updated |

Skills under `.cursor/skills/` (e.g. `crypto-mvp-execution`, `commit-helper`, `dashboard-providers`) encode recurring workflows.

---

## 10. Roadmap progress (snapshot)

Update this table when a phase lands on `master` or a phase branch is the active integration line.

| Phase | Topic | Status |
| --- | --- | --- |
| 0 | Project skeleton | Done |
| 1 | Data layer | Done |
| 2 | Auth + sessions | Done |
| 3 | Onboarding | Done |
| 4 | Providers + dashboard API | Done |
| 5 | Feedback voting API | Done |
| 6 | Frontend screens | Done |
| 7 | Hardening + delivery | Done |

---

## 11. Common pitfalls

See **[gotchas.md](./gotchas.md)** for the full runbook. Highlights:

- **Wrong Python env:** always activate `.venv` before `pip` / `pytest` / `run.py`.
- **Running Flask from wrong cwd:** `DATABASE_PATH` default is relative (`backend/instance/app.db`); prefer running from repo root as documented.
- **Session cookies in browser:** frontend must use `credentials: "include"`; cookie is not in `localStorage`.
- **CORS in local dev:** Vite origin must be listed in `CORS_ORIGINS`; Flask uses `supports_credentials=True`.
- **Provider failures:** never let third-party exceptions bubble to the route; use section-level fallbacks.
- **Secrets:** `.env` is gitignored; rotate any key that was ever committed or pasted into chat logs.
- **e2e ports:** Playwright serves the UI on `5174` so it does not clash with a normal Vite `5173` session.
