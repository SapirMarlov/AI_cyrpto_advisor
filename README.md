# AI Crypto Advisor

Personalized crypto investor dashboard MVP: signup/login, first-login onboarding quiz, and a daily dashboard with market news, coin prices (list/chart), AI insight, and a meme — plus thumbs up/down feedback for future recommendations.

## Stack

| Layer | Tech |
| --- | --- |
| Frontend | React 18 + TypeScript + Vite + Tailwind + shadcn/ui (Cosmic Night) |
| Backend | Python Flask + gunicorn (production) |
| Database | SQLite (local `backend/instance`; Render disk `/var/data`) |
| Auth | Server-side sessions (HTTP-only cookie) |
| Deploy | Vercel (SPA) + Render (API) |

## Current status

MVP Phases **0–8** are complete on `master`: auth, onboarding, dashboard providers, feedback, hardening, and public-deploy scaffolding (Vercel rewrite + Render Blueprint + docs).

Live deploy still needs your Render hostname in [`frontend/vercel.json`](frontend/vercel.json) and `CORS_ORIGINS` on Render. See [docs/roadmap.md](docs/roadmap.md) and [docs/gotchas.md](docs/gotchas.md).

## Quick start

### Prerequisites

- Python 3.11+ (recommended)
- Node.js 20+ (recommended)
- Git

### Backend

```powershell
# from repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

# copy backend\.env.example → backend\.env and set secrets as needed
# run API (default http://localhost:5000)
python backend\run.py
```

Health check: `GET http://localhost:5000/api/health`

### Frontend

```powershell
cd frontend
npm install
# optional: copy .env.example → .env.development (defaults already point at local Flask)
npm run dev
```

App defaults to Vite’s local URL (`http://127.0.0.1:5173` or `http://localhost:5173`) and calls the API at `http://127.0.0.1:5000` (`VITE_API_BASE_URL` in `.env.development`). Prefer `127.0.0.1` over `localhost` on Windows so the browser does not hit IPv6 `::1` while Flask listens on IPv4. Backend CORS allows both Vite origins with credentials (`CORS_ORIGINS`).

### Tests

```powershell
# backend (venv active, from repo root)
$env:PYTHONPATH = "backend"
pytest backend\tests

# frontend
cd frontend
npm test

# browser e2e
cd e2e
npm install
npm run install:browsers   # once
npm test
```

Full details: [docs/testing-guide.md](docs/testing-guide.md).

## Public deploy (Vercel + Render)

- **Frontend:** Vercel project root `frontend`; rewrite `/api/*` → Render ([`frontend/vercel.json`](frontend/vercel.json)). Production builds use an empty `VITE_API_BASE_URL` so the SPA calls same-origin `/api`.
- **Backend:** Render + gunicorn ([`render.yaml`](render.yaml)); SQLite on a persistent disk at `/var/data` (`DATABASE_PATH=/var/data/app.db`).
- **Cookies:** do **not** point the SPA at the Render URL — session cookies must stay first-party on the Vercel host (`SameSite=Lax`).
- **After first deploy:** replace `YOUR-RENDER-SERVICE.onrender.com` in `vercel.json`, set Render `CORS_ORIGINS` to your Vercel URL, and set `SECRET_KEY` / provider keys.

Step-by-step: [docs/developer-guide.md](docs/developer-guide.md) §3b. Cookie pitfalls: [docs/gotchas.md](docs/gotchas.md).

## Documentation

| Doc | Purpose |
| --- | --- |
| [docs/developer-guide.md](docs/developer-guide.md) | Setup, layout, API, env, git workflow, deploy |
| [docs/providers.md](docs/providers.md) | Add or swap dashboard providers (registry + env) |
| [docs/testing-guide.md](docs/testing-guide.md) | How to run/write tests, fixtures, gates |
| [docs/gotchas.md](docs/gotchas.md) | Auth, providers, e2e, deploy, and ops pitfalls |
| [docs/mvp-architecture.md](docs/mvp-architecture.md) | Architecture and security baseline |
| [docs/roadmap.md](docs/roadmap.md) | Phased implementation plan (P0–P8) |

## Core user flow (MVP)

1. Signup / login (display name + email)
2. First-login onboarding quiz (risk + asset preferences)
3. Daily dashboard (filtered news, prices list/chart, AI insight, meme)
4. Feedback votes (thumbs up/down)

## License

Private MVP — not licensed for public distribution unless stated otherwise.
