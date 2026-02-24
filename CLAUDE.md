# Enex — Claude Code Project Context

## What is this project?
Analyst Prediction Tracker for Indian equity markets. Tracks stock price target predictions made by analysts/firms/media against actual outcomes and ranks them by accuracy.

## Documentation (read before making changes)
- `docs/PLAN.md` — Product vision, phases, scope constraints
- `docs/ROLLOUT_PLAN.md` — Sprint plan, DB schema, API endpoints, auth strategy
- `docs/ARCHITECTURE.md` — System diagrams (Mermaid): architecture, ingestion paths, eval pipeline, auth flow, ERD
- `docs/CICD_INFRA.md` — CI/CD pipelines, Azure infra, Docker strategy, secrets management
- `docs/SECURITY.md` — JWT/OTP design, threat model, injection prevention, security headers

## Tech stack
- **Backend**: FastAPI · Python 3.12 · SQLAlchemy 2.0 · Alembic · Pydantic v2 · Celery · Redis
- **Frontend**: Next.js 16 (App Router) · React 19 · Shadcn/ui · TanStack Query · Zustand · NextAuth.js v5
- **Database**: PostgreSQL 16
- **AI**: Anthropic Claude API (prediction extraction)
- **Deployment**: Azure Container Apps

## Architecture patterns
- **Backend**: Layered (Routes → Services → Repositories → Models/Schemas) with FastAPI Dependency Injection
- **Frontend**: Server-first rendering (RSC for public pages, Client Components for interactive) + feature-based route groups
- **External services**: Protocol + Adapter + DI pattern for loose coupling (see `integrations/` folder structure)
  - Each external dependency (email, SMS, AI, price data, archival, cache) has a Protocol interface and swappable adapter
  - Provider selection is config-driven via env vars (e.g. `EMAIL_PROVIDER=resend`)

## Key decisions
- JWT: HS256 with 24h access / 30d refresh for dev; configurable for production via env vars
- OTP: 6-digit, 5-min expiry, max 3 attempts, rate limited (5/hour/identifier), hashed storage
- All user-submitted predictions go through moderator review queue (no auto-approve)
- Three prediction input paths: full submission (AI-assisted), suggest-a-prediction (low-effort), admin bulk-import
- Unified `predictors` table for all types (individual, brokerage, research_firm, media_house, influencer)

## Current status
- **Sprint 0 complete** — full project scaffolding deployed
  - Backend: FastAPI + uv + Alembic + 12 ORM models + health endpoint + tests
  - Frontend: Next.js 16 + Shadcn/ui + route stubs
  - Docker Compose (PostgreSQL 16 + Redis 7)
  - CI pipeline (GitHub Actions) + deploy workflow stubs
  - Dockerfiles (multi-stage, non-root) for both services
  - See `docs/TASK_SUMMARY.md` for detailed sprint log
- **Next step: Sprint 1 — Core Data Layer**
  - CRUD APIs for predictors, stocks, predictions
  - Role-based access control (admin/moderator guards)
  - Admin user management + create-admin CLI
  - Stock seeding (NSE top 200)
  - Repository + Service layer implementation

## Development workflow
- Work on feature branches, PR into `main`
- Pre-commit hooks run ruff, mypy, trailing-whitespace checks
- CI runs on pull requests: backend (lint + type + migrate + test) + frontend (lint + type) + Docker build

## Git
- Main branch: `main`
- Remote: `github.com/acumind/Enex`
