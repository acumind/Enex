# Enex — CI/CD & Infrastructure Strategy

> Analyst Prediction Tracker for Indian Equity Markets

---

## 1. Environments

Two cloud environments only — keeps costs within the $50–100/month budget during MVP.

| Environment | Purpose | Infrastructure |
|-------------|---------|---------------|
| **Local** | Day-to-day development | Docker Compose (PostgreSQL + Redis run locally) |
| **Staging** | Pre-production testing and QA | Azure Container Apps — smaller SKUs |
| **Production** | Live application | Azure Container Apps — full SKUs |

Developers never need a cloud environment for local development. Docker Compose provides a fully functional local stack.

---

## 2. Azure Infrastructure

### Resource Layout (per environment)

```
Azure Resource Group: enex-staging / enex-prod
│
├── Azure Container Registry (ACR)             ← shared across both environments
│   ├── enex-backend:<sha>
│   ├── enex-frontend:<sha>
│   └── enex-backend:<version-tag>             ← production-promoted images
│
├── Azure Container Apps Environment
│   ├── Container App: enex-backend            ← FastAPI
│   │   └── Ingress: external HTTPS
│   ├── Container App: enex-frontend           ← Next.js
│   │   └── Ingress: external HTTPS
│   └── Container App: enex-worker             ← Celery worker (same image as backend)
│       └── Ingress: none (internal only)
│
├── Azure Database for PostgreSQL              ← Flexible Server
│   ├── staging: Burstable B1ms (1 vCPU, 2 GB RAM)
│   └── prod:    Burstable B2s  (2 vCPU, 4 GB RAM)
│
├── Azure Cache for Redis
│   ├── staging: Basic C0
│   └── prod:    Basic C1
│
└── Azure Key Vault                            ← all runtime secrets
    ├── DATABASE-URL
    ├── REDIS-URL
    ├── RESEND-API-KEY
    ├── MSG91-API-KEY
    ├── ANTHROPIC-API-KEY
    ├── GOOGLE-CLIENT-ID
    ├── GOOGLE-CLIENT-SECRET
    └── JWT-SECRET-KEY
```

Container Apps pulls secrets from Key Vault at startup via **managed identity** — no credentials stored in GitHub or container environment variables directly.

### Estimated Monthly Cost

| Resource | Staging | Production |
|----------|---------|-----------|
| Container Apps (3 containers) | ~$5 | ~$20 |
| PostgreSQL Flexible Server | ~$15 | ~$25 |
| Redis Cache | ~$15 | ~$20 |
| Container Registry | ~$5 | ~$5 |
| Key Vault | ~$1 | ~$1 |
| **Total** | **~$41/mo** | **~$71/mo** |

Total across both environments: **~$112/mo** — within the $50–100/month production budget with staging included.

---

## 3. Infrastructure as Code

All Azure resources are defined as **Bicep files** — Azure-native IaC, version-controlled alongside the application.

```
infra/
├── main.bicep                    ← orchestrates all modules
├── modules/
│   ├── container-apps.bicep
│   ├── postgresql.bicep
│   ├── redis.bicep
│   ├── key-vault.bicep
│   └── container-registry.bicep
└── parameters/
    ├── staging.json
    └── production.json
```

**Provision a new environment from scratch:**
```bash
az deployment group create \
  --resource-group enex-prod \
  --template-file infra/main.bicep \
  --parameters infra/parameters/production.json
```

Infrastructure is fully reproducible — any environment can be recreated from scratch in under 10 minutes.

---

## 4. Docker Strategy

### Multi-Stage Builds

Both services use multi-stage Dockerfiles to keep production images minimal and secure.

**Backend (FastAPI):**
```
Stage 1 — builder:    Install uv, resolve + install dependencies
Stage 2 — production: Copy only installed packages + app code
                       No dev tools, no build cache, no uv binary
                       Final image target: ~200 MB
                       Runs as non-root user (appuser)
```

**Frontend (Next.js):**
```
Stage 1 — deps:       npm ci (install all dependencies)
Stage 2 — builder:    next build → outputs .next/standalone
Stage 3 — runner:     Copy standalone output only
                       No node_modules in production image
                       Final image target: ~120 MB
                       Runs as non-root user (nextjs)
```

**Celery Worker:**

Uses the **same Docker image as the backend** — different entrypoint only:
- Backend container: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Worker container: `celery -A app.jobs.celery_app worker --loglevel=info`

No separate Dockerfile to maintain. Worker auto-scales independently in Container Apps.

### Image Tagging Strategy

| Tag | When created | Purpose |
|-----|-------------|---------|
| `sha-{git-commit}` | Every CI build | Immutable reference to exact code |
| `staging-latest` | Every merge to main | Points to current staging deployment |
| `v1.2.3` | On git tag | Immutable production release tag |
| `latest` | On production deploy | Points to current production deployment |

---

## 5. CI/CD Pipelines

Three GitHub Actions workflows:

```
.github/workflows/
├── ci.yml              ← every pull request
├── deploy-staging.yml  ← every merge to main
└── deploy-prod.yml     ← every git tag (v*.*.*)
```

---

### Workflow 1: CI (every pull request)

**Trigger:** `pull_request` targeting `main`

```
┌─────────────────────────────────────────────┐
│  Pull Request opened / updated              │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
   ┌─────▼──────┐      ┌──────▼──────┐
   │  backend   │      │  frontend   │   ← parallel jobs
   │  CI job    │      │  CI job     │
   └─────┬──────┘      └──────┬──────┘
         │                    │
   ┌─────▼──────┐      ┌──────▼──────┐
   │ ruff lint  │      │ eslint      │
   │ mypy check │      │ tsc check   │
   │ bandit     │      │ jest tests  │
   │ pip-audit  │      │ npm audit   │
   │ pytest     │      │             │
   │ (unit +    │      │             │
   │  integration      │             │
   │  via Docker │      │             │
   │  Compose)  │      │             │
   └─────┬──────┘      └──────┬──────┘
         │                    │
         └──────────┬─────────┘
                    │
          ┌─────────▼──────────┐
          │  docker build      │   ← verify both images build cleanly
          │  (no push to ACR)  │      fails fast if Dockerfile is broken
          └────────────────────┘
```

**Integration tests** spin up a real PostgreSQL + Redis via Docker Compose inside the CI runner. No mocking the database layer — tests run Alembic migrations and hit a real DB.

**PR is blocked from merging if any step fails.**

---

### Workflow 2: Deploy to Staging (merge to main)

**Trigger:** `push` to `main` (after CI passes)

```
┌─────────────────────────────────────────────┐
│  Merge to main                              │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Build & push      │   ← docker build + push to ACR
         │  images to ACR     │      tag: sha-{commit}
         │  (backend +        │      tag: staging-latest
         │   frontend)        │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Run DB migrations  │   ← alembic upgrade head
         │  (one-off Container │      against staging PostgreSQL
         │   Apps job)         │      runs BEFORE new containers start
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Deploy to staging  │   ← az containerapp update
         │  backend + frontend │      rolling update — zero downtime
         │  + celery worker    │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Smoke tests        │   ← GET /api/v1/health → 200
         │                     │      leaderboard page loads
         │                     │      auth OTP send endpoint responds
         └────────────────────┘
```

---

### Workflow 3: Deploy to Production (git tag)

**Trigger:** `push` tag matching `v*.*.*` (e.g. `v1.0.0`)

```
┌─────────────────────────────────────────────┐
│  git tag v1.0.0 pushed                      │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Manual approval    │   ← GitHub Environment protection rule
         │  gate               │      required reviewer must approve
         │                     │      before pipeline continues
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Promote image      │   ← re-tag ACR image
         │  from staging       │      sha-abc → v1.0.0 + latest
         │  (no rebuild)       │      same artifact that passed staging
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Run DB migrations  │   ← alembic upgrade head → production DB
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Deploy to prod     │   ← rolling update
         │  backend + frontend │
         │  + celery worker    │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Smoke tests        │
         │  + Sentry release   │   ← sentry-cli releases new version
         │                     │      maps stack traces to source maps
         └────────────────────┘
```

**Key rule:** Production always runs a pre-built image that already passed staging — never a fresh build from a tag.

---

## 6. Database Migration Strategy

Migrations are the riskiest part of any deployment. Hard rules:

| Rule | Detail |
|------|--------|
| **Migrations run before new code** | Old code must be compatible with the new schema during rolling deploy |
| **Always backwards-compatible** | Add columns as nullable first → populate data → add constraint in a later migration |
| **Never `DROP` in the same migration as `ADD`** | Split into separate releases — drop only after verifying new code works |
| **Alembic revision per PR** | Every schema change ships with its migration file in the same PR |
| **Rollback = forward migration** | Never run `alembic downgrade` in production — write a new migration that reverts the change |
| **Separate DB user for migrations** | Alembic runs as `enex_migrations` with DDL rights; app runs as `enex_app` with DML only |

**Migration as a Container Apps job:**
```bash
# Runs as an ephemeral one-off job before the new containers start
az containerapp job start \
  --name enex-migrations \
  --resource-group enex-prod \
  --image enex-backend:v1.0.0 \
  --command "alembic upgrade head"
```

---

## 7. Secrets Management

| Context | Method |
|---------|--------|
| Local development | `.env` file (git-ignored, never committed) |
| CI/CD (GitHub Actions) | GitHub Actions encrypted secrets (`AZURE_CREDENTIALS`, `ACR_PASSWORD`) |
| Staging runtime | Azure Key Vault via managed identity |
| Production runtime | Azure Key Vault via managed identity |

Application code reads secrets via `pydantic-settings` — indifferent to where the value originates:

```python
# core/config.py
class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    RESEND_API_KEY: str
    ANTHROPIC_API_KEY: str
    JWT_SECRET_KEY: str
    ...
    model_config = SettingsConfigDict(env_file=".env")
```

In staging and production, Azure Container Apps injects Key Vault values as environment variables via managed identity reference — same interface, different source.

---

## 8. Local Development

Docker Compose provides a fully local stack — no cloud resources needed for development:

```
docker-compose.yml
├── postgres:16-alpine    → localhost:5432
├── redis:7-alpine        → localhost:6379
└── (optional) flower     → localhost:5555  ← Celery job monitor
```

**Developer workflow:**
```bash
# Start local dependencies
docker compose up -d

# Run backend
uv run uvicorn app.main:app --reload

# Run frontend
npm run dev

# Run Celery worker
uv run celery -A app.jobs.celery_app worker --loglevel=debug

# Run migrations
uv run alembic upgrade head
```

---

## 9. Monitoring & Observability

| Concern | Tool | What it covers |
|---------|------|---------------|
| **Error tracking** | Sentry | Exceptions in backend + frontend with stack traces and release tracking |
| **Uptime / health** | Azure Container Apps health probes | Liveness + readiness checks on `GET /api/v1/health` |
| **Infrastructure metrics** | Azure Monitor | CPU, memory, request count, latency per container |
| **Job monitoring** | Flower | Celery job queue status, failed tasks, worker health |
| **Structured logs** | Azure Log Analytics | JSON logs from all containers, queryable with KQL |
| **Alerting** | Azure Monitor alerts | Notify on error rate spike, container restart, job failure |

### Health Check Endpoint

```
GET /api/v1/health

Response 200:
{
  "status": "ok",
  "db": "ok",
  "redis": "ok",
  "version": "1.0.0"
}

Response 503 (if DB or Redis unreachable):
{
  "status": "degraded",
  "db": "error",
  "redis": "ok"
}
```

Container Apps uses this endpoint for both liveness (restart if unhealthy) and readiness (stop sending traffic if not ready) probes.

---

## 10. End-to-End Deployment Flow

```
Developer pushes PR
    └─→ CI runs: lint + type check + tests + build check
        └─→ All checks pass → PR reviewed and merged to main
            └─→ Staging deploy triggers automatically
                └─→ Build image → push to ACR → migrate DB → deploy → smoke tests
                    └─→ QA signs off on staging
                        └─→ Developer pushes tag: git tag v1.0.0 && git push --tags
                            └─→ Manual approval gate (required reviewer approves)
                                └─→ Promote staging image → migrate prod DB
                                    └─→ Rolling deploy to production
                                        └─→ Smoke tests pass → Sentry release created
```

**No manual deployments. No SSH into servers. No hotfixes outside the pipeline.**
