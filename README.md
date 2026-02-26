# Enex — Analyst Prediction Tracker

> A transparent, data-driven accountability layer for Indian equity market predictions.
> Tracks analyst price targets against actual outcomes and ranks predictors by accuracy.

---

## Documentation

Read these in order before touching code:

| Doc | Description |
|-----|-------------|
| [`docs/PLAN.md`](docs/PLAN.md) | Product vision, problem statement, feature phases |
| [`docs/ROLLOUT_PLAN.md`](docs/ROLLOUT_PLAN.md) | Sprint-by-sprint implementation plan, DB schema, API design |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System architecture diagrams (5 Mermaid diagrams) |
| [`docs/CICD_INFRA.md`](docs/CICD_INFRA.md) | CI/CD pipelines, Azure infrastructure, Docker strategy |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Security strategy, threat model, JWT/OTP design |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (App Router) · React 19 · Shadcn/ui · TanStack Query · Zustand |
| Frontend Testing | Vitest · React Testing Library · Playwright |
| Backend | FastAPI · Python 3.12 · SQLAlchemy 2.0 · Alembic · Pydantic v2 |
| Database | PostgreSQL 16 |
| Cache / Queue | Redis 7 · Celery |
| Auth | NextAuth.js v5 (Google OAuth) · MSG91 (Mobile OTP) · Resend (Email OTP) |
| AI | Anthropic Claude API (prediction extraction) |
| Deployment | Azure Container Apps · Azure PostgreSQL · Azure Cache for Redis |

---

## Prerequisites

Install these before starting:

| Tool | Version | Install |
|------|---------|---------|
| Docker Desktop | Latest | https://docs.docker.com/get-docker/ |
| Python | 3.12+ | https://www.python.org/downloads/ |
| uv | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 18+ | https://nodejs.org/ |
| Git | Any | https://git-scm.com/ |

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/acumind/Enex.git
cd Enex
```

### 2. Start local infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL on `localhost:5432` and Redis on `localhost:6379`.

Verify they are running:
```bash
docker compose ps
```

### 3. Set up the backend

```bash
cd backend

# Copy environment file and fill in values
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section below)

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Create the first admin account
uv run python -m app.cli create-admin --email your@email.com

# Start the API server (runs on http://localhost:8000)
uv run uvicorn app.main:app --reload
```

### 4. Set up the frontend

```bash
cd frontend

# Copy environment file and fill in values
cp .env.example .env.local
# Edit .env.local with your values

# Install dependencies
npm install

# Start the dev server (runs on http://localhost:3000)
npm run dev
```

### 5. Start the Celery worker (optional for background jobs)

```bash
cd backend
uv run celery -A app.jobs.celery_app worker --loglevel=debug
```

To also run Celery Beat (job scheduler):
```bash
uv run celery -A app.jobs.celery_app worker --beat --loglevel=debug
```

> **Note:** Beat must run as a single instance only. Do not run multiple Beat processes.

### 6. (Optional) Monitor background jobs

```bash
uv run celery -A app.jobs.celery_app flower --port=5555
# Open http://localhost:5555
```

---

## Running Tests

### Backend

```bash
cd backend

# Run all tests
uv run pytest

# With coverage report
uv run pytest --cov=app --cov-report=term-missing

# Run a specific test file
uv run pytest tests/test_predictions.py -v
```

Integration tests require Docker Compose to be running (they use a real PostgreSQL + Redis).

### Frontend

```bash
cd frontend

# Run all unit/component/integration tests (Vitest)
npm test

# Watch mode (re-runs on file changes)
npm run test:watch

# With coverage report
npm run test:coverage

# Run E2E tests (Playwright — requires dev server)
npm run test:e2e

# E2E with interactive UI
npm run test:e2e:ui
```

### Generate TypeScript API client (after backend schema changes)

```bash
cd frontend
npm run gen-types
# Regenerates lib/generated/api.d.ts from http://localhost:8000/openapi.json
# Run this whenever backend routes or schemas change
# CI will fail if the committed file is out of sync
```

---

## Environment Variables

### Backend (`backend/.env`)

See [`backend/.env.example`](backend/.env.example) for the full annotated list.

Minimum required to start locally:

```env
DATABASE_URL=postgresql+asyncpg://enex:dev_password@localhost:5432/enex
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=any-random-string-for-local-dev
ANTHROPIC_API_KEY=sk-ant-...
```

All other keys (MSG91, Resend, Google OAuth) can be left as placeholders for initial setup — the relevant features will simply error if called.

### Frontend (`frontend/.env.local`)

See [`frontend/.env.example`](frontend/.env.example) for the full annotated list.

Minimum required to start locally:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXTAUTH_SECRET=any-random-string-for-local-dev
NEXTAUTH_URL=http://localhost:3000
```

---

## Project Structure

```
Enex/
├── backend/                        # FastAPI application
│   ├── app/
│   │   ├── api/routes/             # HTTP route handlers (thin layer)
│   │   ├── services/               # Business logic
│   │   ├── repositories/           # Database access (SQLAlchemy)
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── integrations/           # External service adapters
│   │   │   ├── email/              # EmailService protocol + Resend adapter
│   │   │   ├── sms/                # SMSService protocol + MSG91 adapter
│   │   │   ├── ai/                 # AIExtractionService + Claude adapter
│   │   │   ├── price/              # PriceDataService + yfinance adapter
│   │   │   ├── archival/           # ArchivalService + Wayback adapter
│   │   │   └── cache/              # CacheService + Redis adapter
│   │   ├── jobs/                   # Celery background tasks
│   │   └── core/                   # Config, DB session, security, DI
│   ├── migrations/                 # Alembic migration files
│   ├── tests/                      # pytest tests
│   ├── seeds/                      # Seed data (stocks CSV, sample predictions)
│   ├── .env.example
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/                       # Next.js application
│   ├── app/                        # App Router pages and layouts
│   │   ├── (public)/               # SSG/ISR pages (leaderboard, profiles, stocks)
│   │   ├── (auth)/                 # Login page
│   │   ├── (user)/                 # Authenticated user pages
│   │   └── (admin)/                # Admin panel
│   ├── components/                 # Shared UI components
│   ├── lib/
│   │   ├── generated/              # Auto-generated TypeScript API client
│   │   ├── api-client.ts           # Typed API wrapper
│   │   └── auth.ts                 # NextAuth.js config
│   ├── test/                       # Test setup and utilities
│   │   ├── setup.tsx               # Global mocks and jest-dom matchers
│   │   ├── test-utils.tsx          # Custom render, auth mock factories
│   │   └── mocks/                  # Reusable mock objects
│   ├── e2e/                        # Playwright E2E tests (placeholder)
│   ├── vitest.config.ts            # Vitest configuration
│   ├── playwright.config.ts        # Playwright configuration
│   ├── .env.example
│   ├── package.json
│   └── Dockerfile
│
├── infra/                          # Bicep infrastructure as code
│   ├── main.bicep
│   ├── modules/
│   └── parameters/
│
├── docs/                           # All project documentation
│   ├── PLAN.md
│   ├── ROLLOUT_PLAN.md
│   ├── ARCHITECTURE.md
│   ├── CICD_INFRA.md
│   └── SECURITY.md
│
├── .github/workflows/              # GitHub Actions CI/CD
│   ├── ci.yml
│   ├── deploy-staging.yml
│   └── deploy-prod.yml
│
├── docker-compose.yml              # Local development infrastructure
└── README.md
```

---

## Development Workflow

### Adding a new API endpoint

1. Define the Pydantic schema in `backend/app/schemas/`
2. Add the repository method in `backend/app/repositories/`
3. Add the service method in `backend/app/services/`
4. Add the route in `backend/app/api/routes/`
5. Run `npm run gen-types` in the frontend to regenerate the API client

### Adding a database migration

```bash
cd backend

# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "add_predictor_table"

# Review the generated file in migrations/versions/
# Then apply it
uv run alembic upgrade head
```

### Swapping an external service (e.g. Resend → SendGrid)

1. Write a new adapter in `backend/app/integrations/email/sendgrid.py` implementing `EmailService` protocol
2. Update `get_email_service()` in `backend/app/core/dependencies.py` to handle `EMAIL_PROVIDER=sendgrid`
3. Set `EMAIL_PROVIDER=sendgrid` in `.env`
4. No other files need to change

---

## Common Issues

| Problem | Solution |
|---------|---------|
| `connection refused` on DB | `docker compose up -d` — ensure PostgreSQL container is running |
| `alembic: no such table` | Run `uv run alembic upgrade head` to apply migrations |
| `401 Unauthorized` on all requests | JWT_SECRET must match between backend `.env` and frontend `.env.local` |
| Frontend can't reach API | Ensure `NEXT_PUBLIC_API_URL` points to the running backend (`http://localhost:8000/api/v1`) |
| Azure Redis connection fails | Azure Redis uses SSL on port 6380 — use `rediss://` (double-s) not `redis://` |
| Celery tasks not running | Ensure Redis is running and `REDIS_URL` is set in `.env`; start the worker |

---

## Deployment

See [`docs/CICD_INFRA.md`](docs/CICD_INFRA.md) for the full deployment strategy.

**Quick summary:**
- Every PR triggers CI (lint + tests + build check)
- Merge to `main` → auto-deploys to staging
- Git tag `v*.*.*` + manual approval → deploys to production
- Infrastructure provisioned via Bicep: `az deployment group create --template-file infra/main.bicep`

---

## Useful Commands

```bash
# Check backend API docs (auto-generated)
open http://localhost:8000/docs

# Check Celery job queue (Flower UI)
open http://localhost:5555

# Connect to local PostgreSQL
docker exec -it enex-postgres-1 psql -U enex -d enex

# Connect to local Redis
docker exec -it enex-redis-1 redis-cli

# Roll back last migration
cd backend && uv run alembic downgrade -1

# Lint backend
cd backend && uv run ruff check . && uv run mypy .

# Lint frontend
cd frontend && npm run lint && npm run type-check
```
