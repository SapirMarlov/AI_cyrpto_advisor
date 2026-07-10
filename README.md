# AI Crypto Advisor

Personalized crypto investor dashboard MVP: signup/login, first-login onboarding quiz, and a daily dashboard with market news, coin prices, AI insight, and a meme — plus thumbs up/down feedback for future recommendations.

## Stack

| Layer | Tech |
| --- | --- |
| Frontend | React 18 + TypeScript + Vite + Tailwind + shadcn/ui (Cosmic Night) |
| Backend | Python Flask |
| Database | SQLite |
| Auth | Server-side sessions (HTTP-only cookie) |

## Current status

Phases **0–5** are on `master`. **Phase 6** (frontend screens: auth, onboarding, dashboard + votes) is implemented on `phase/6-frontend`. Phase 7 (hardening) is next. See [docs/roadmap.md](docs/roadmap.md).

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

# run API (default http://localhost:5000)
python backend\run.py
```

Health check: `GET http://localhost:5000/api/health`

### Frontend

```powershell
cd frontend
npm install
# optional: copy .env.example → .env
npm run dev
```

App defaults to Vite’s local URL (`http://127.0.0.1:5173` or `http://localhost:5173`) and calls the API at `http://127.0.0.1:5000` (override with `VITE_API_BASE_URL`). Prefer `127.0.0.1` over `localhost` on Windows so the browser does not hit IPv6 `::1` while Flask listens on IPv4. Backend CORS allows both Vite origins with credentials (`CORS_ORIGINS`).

### Tests

```powershell
# backend (venv active, from repo root)
pytest backend\tests

# frontend
cd frontend
npm test
```

Full details: [docs/testing-guide.md](docs/testing-guide.md).

## Documentation

| Doc | Purpose |
| --- | --- |
| [docs/developer-guide.md](docs/developer-guide.md) | Setup, layout, API, env, git workflow |
| [docs/providers.md](docs/providers.md) | Add or swap dashboard providers (registry + env) |
| [docs/testing-guide.md](docs/testing-guide.md) | How to run/write tests, fixtures, gates |
| [docs/mvp-architecture.md](docs/mvp-architecture.md) | Architecture and security baseline |
| [docs/roadmap.md](docs/roadmap.md) | Phased implementation plan (P0–P7) |

## Core user flow (target MVP)

1. Signup / login  
2. First-login onboarding quiz  
3. Daily dashboard (news, prices, insight, meme)  
4. Feedback votes (thumbs up/down)

## License

Private MVP — not licensed for public distribution unless stated otherwise.
