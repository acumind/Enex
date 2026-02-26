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
- **Frontend Testing**: Vitest · React Testing Library · Playwright
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
- **Sprints 0–10 complete** (scaffolding, core data, prediction entry, auth, evaluation, public pages, engagement & polish, hardening/caching, OG images, Zustand, email notifications, proxy migration, admin features, advanced admin: runtime config/system health/eval dashboard/alerts/CSV exports/notification broadcast, admin operations: user management/predictor management/login tracking/bulk actions/stale alerts/announcement banner)
- **Frontend testing framework complete** — Vitest + RTL (138 tests, 22 files), Playwright E2E scaffold
- 435 backend tests passing, 138 frontend tests passing, lint/tsc/build clean
- **Next step: Azure deployment, load testing, production hardening, Playwright E2E suites**

## Git
- Main branch: `main`
- Remote: `github.com/acumind/Enex`
