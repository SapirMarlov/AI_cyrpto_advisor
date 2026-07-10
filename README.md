# AI Crypto Advisor

Personalized crypto investor dashboard MVP: signup/login, first-login onboarding quiz, and a daily dashboard with market news, coin prices, AI insight, and a meme — plus thumbs up/down feedback for future recommendations.

## Stack

| Layer | Tech |
| --- | --- |
| Frontend | React 18 + TypeScript + Vite |
| Backend | Python Flask |
| Database | SQLite |
| Auth | Server-side sessions (HTTP-only cookie) |

## Current status

Phases **0–4** are implemented on `master` (skeleton, data layer, auth, onboarding, providers + dashboard API). **Phase 5** (feedback voting API) is complete on `phase/5-feedback`. Frontend is still a shell — **Phase 6** is next. See [docs/roadmap.md](docs/roadmap.md).

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
npm run dev
```

App defaults to Vite’s local URL and calls the API at `http://localhost:5000` (override with `VITE_API_BASE_URL`).

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
