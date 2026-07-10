# Testing Guide

How to run, write, and gate tests for AI Crypto Advisor. Agent commit gates also live in `.cursor/rules/testing-and-commit-gates.mdc`.

**Keep this guide current:** when test runners, fixtures, folder layout, or required coverage change, update this file and the short test sections in [README.md](../README.md) / [developer-guide.md](./developer-guide.md).

---

## 1. Quick commands

Run from the **repo root** unless noted. Backend always needs the project `.venv` active.

```powershell
# Backend — all tests
.\.venv\Scripts\Activate.ps1
pytest backend\tests

# Backend — one file
pytest backend\tests\test_auth_routes.py

# Backend — one test by name
pytest backend\tests\test_auth_routes.py -k "signup_login_me"

# Backend — verbose + show print/logs
pytest backend\tests -v -s

# Frontend — once (CI-style)
cd frontend
npm test

# Frontend — watch mode
npm run test:watch
```

Exit code `0` means green. Do not merge a TODO/slice into its phase branch until the **affected** suites pass.

---

## 2. What we test (by layer)

| Layer | Tool | Location | Focus |
| --- | --- | --- | --- |
| Backend unit | pytest | `backend/tests/` | Repositories, services, utils, rate limiter, schema |
| Backend route | pytest + Flask test client | `backend/tests/test_*_routes.py` | Status codes, envelope, cookies, auth guards |
| Frontend unit | Vitest + Testing Library | `frontend/src/**/*.test.tsx` | Components, pages, client helpers |
| e2e (planned) | TBD in Phase 6–7 | TBD | Auth → onboarding → dashboard → vote |

Minimum per roadmap slice: **at least one acceptance test** that proves the slice goal (unit or route/e2e).

---

## 3. Backend testing

### 3.1 Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

`pytest` is listed in `backend/requirements.txt`. No separate `pytest.ini` is required today; discovery picks up `backend/tests/test_*.py`.

### 3.2 Shared fixtures (`backend/tests/conftest.py`)

| Fixture | Use |
| --- | --- |
| `db_conn` | In-memory SQLite with schema applied — repository/unit tests |
| `app` | Flask app with `TestConfig` and a temp file DB under `tmp_path` |
| `client` | `app.test_client()` for HTTP route tests |

Prefer these fixtures over opening ad-hoc connections. Schema is applied via `apply_schema` / `init_db` so tests stay close to production init.

### 3.3 Conventions

- Assert the **envelope**: `ok`, `data`, `error.code` / `error.message`.
- For auth flows, assert `Set-Cookie` / session behavior when relevant (`session_id`).
- Protected routes: always include a **401 unauthorized** negative case.
- Validation: include malformed / unexpected-field cases where the route validates strictly.
- User scoping: repository tests should prove data is tied to the correct `user_id`.
- Do not hit real external APIs in unit/route tests — mock HTTP (Phase 4+ providers).

### 3.4 Current backend suite (snapshot)

Update this list when adding or removing test modules.

| File | Covers |
| --- | --- |
| `test_health.py` | `GET /api/health` |
| `test_response.py` | Success/error envelope helpers |
| `test_schema.py` | Schema apply / tables |
| `test_users_repository.py` | User create/get, duplicate email |
| `test_preferences_repository.py` | Preferences upsert / read |
| `test_feedback_repository.py` | Votes + uniqueness |
| `test_sessions_repository.py` | Session persistence |
| `test_auth_service.py` | Password hash/verify, auth service |
| `test_auth_routes.py` | Signup/login/logout/me |
| `test_auth_guard.py` | `login_required` middleware |
| `test_rate_limiter.py` | Login rate limit window |
| `test_onboarding_routes.py` | Questions + answers |
| `test_provider_base.py` | Provider run + cache fallback |
| `test_gemini_client.py` | Gemini REST helper |
| `test_price_provider.py` | CoinGecko price fetch + failures |
| `test_news_provider.py` | CryptoPanic / RSS fetch + failures |
| `test_ai_provider.py` | Gemini / template insight |
| `test_meme_provider.py` | Reddit + Gemini meme selection |
| `test_dashboard_route.py` | Daily dashboard mixed section outcomes |
| `test_feedback_service.py` | Vote persist, replace, validation helpers |
| `test_feedback_routes.py` | `POST /api/feedback/vote` auth + validation |

### 3.5 Planned backend tests (Phase 6+)

| Area | Expected files / focus |
| --- | --- |
| Frontend e2e (later) | Auth → onboarding → dashboard → vote critical path |

Provider rule: **never** let uncaught provider exceptions reach the route; tests must prove fallbacks.

---

## 4. Frontend testing

### 4.1 Setup

```powershell
cd frontend
npm install
npm test
```

Config: `frontend/vite.config.ts` (`environment: "jsdom"`, `setupFiles: ./src/test/setup.ts`). Setup imports `@testing-library/jest-dom`.

### 4.2 Conventions

- Colocate tests next to code: `Component.test.tsx` or under `src/` with a clear name.
- Prefer Testing Library queries by role/label (`getByRole`, `getByLabelText`) over CSS selectors.
- Parse API envelopes defensively in client tests (`ok` / `data` / `error`).
- Dashboard panels (Phase 6): test **per-section** loading / empty / error so one failure does not imply a blank page.
- Mock `fetch` / `apiClient` — do not call the live Flask server from unit tests.

### 4.3 Current frontend suite (snapshot)

| File | Covers |
| --- | --- |
| `src/App.test.tsx` | Shell renders heading |

### 4.4 Planned frontend / e2e (Phase 6–7)

Critical flows to cover when UI lands:

1. Signup / login / logout  
2. First-login onboarding completion → redirect to dashboard  
3. Dashboard render with mixed section success (mocked API)  
4. Vote buttons (up/down) happy + error paths  

Exact e2e runner (Playwright/Cypress/etc.) is chosen when Phase 6 starts; document the choice here when added.

---

## 5. What to add per slice

Use this checklist when finishing a roadmap slice:

1. **Happy path** — proves the slice works with valid input.
2. **Auth negative** — if the endpoint is protected, unauthenticated → 401.
3. **Validation negative** — bad/missing/extra fields → 400 (or documented code).
4. **Failure path** — for providers: timeout, non-200, malformed JSON, static/cache fallback.
5. **Isolation** — one provider/section failure does not break the whole dashboard response.

Name tests in simple English: `test_login_with_valid_credentials`, `renders application heading`.

---

## 6. Gates before “done”

| Gate | Rule |
| --- | --- |
| Slice complete | Affected tests pass |
| TODO → phase merge | Auto after green tests (see git workflow) |
| Phase → `master` | Ask user; run the relevant full suites first |
| Commit | Ask user unless they already requested a commit |

Security-sensitive paths (auth, onboarding, feedback, providers) need negative tests before marking complete — see `.cursor/rules/security-mvp-baseline.mdc`.

---

## 7. Flaky tests and gotchas

Record durable notes in `docs/gotchas.md` when you find them. Common themes to watch:

- Time-based rate limiter tests — freeze or inject clock if flakes appear.
- Cookie assertions — parse `Set-Cookie` carefully; clear cookies between cases when reusing `client`.
- Provider tests that accidentally call the network — always mock.
- SQLite file DB vs memory — prefer fixtures; avoid sharing a real `instance/app.db` across tests.

---

## 8. Manual smoke (optional)

Useful after pulling or before a demo:

1. Start backend: `python backend\run.py`  
2. `GET /api/health` → `ok: true`  
3. Signup → `GET /api/auth/me` with cookie → onboarding questions → save answers
4. `GET /api/dashboard/daily` with mixed provider keys present/absent
5. `POST /api/feedback/vote` (auth required; replace-on-repeat)

Frontend: `npm run dev` and confirm the shell loads without console errors.
