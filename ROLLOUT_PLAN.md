# Enex — Implementation Rollout Plan

> Analyst Prediction Tracker for Indian Equity Markets
> Created: 2026-02-20

---

## Decisions Locked In

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Target market | India-first (NSE/BSE) | Large retail base, active analyst ecosystem on TV/social/print |
| Prediction types | Price targets only | Most specific, falsifiable. Clean hit/miss. No subjectivity. |
| Scoring model | Simple hit/miss with tolerance band | Easy to understand, explain, and trust. 5% tolerance = partial hit. |
| AI in MVP | AI-assisted manual entry | User pastes article URL → Claude pre-fills form → user confirms |
| Frontend | Next.js 15 (App Router) + React | SSR/SSG for SEO, file-system routing, Vercel deployment |
| Backend | FastAPI (Python 3.12+) | Best AI/data analysis ecosystem, yfinance, pandas, Anthropic SDK |
| Architecture | Separate frontend + backend | Flexibility for independent scaling, cleaner API contract |
| Authentication | User accounts from day 1 | Community submissions, watchlists, alerts from launch |
| Historical seeding | ~100 well-known predictions | Avoid cold-start; demonstrate value immediately |
| Deployment | Azure Container Apps | Serverless containers, auto-scaling, single cloud provider |
| Hosting budget | $50–100/month | Managed services, comfortable headroom |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USERS                                      │
│   Retail Investors  │  Community Submitters  │  Admin/Moderators     │
└──────────┬──────────┴───────────┬────────────┴──────────┬───────────┘
           │                      │                       │
           ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js + React)                      │
│                                                                     │
│  Public Pages (SSR/SSG) Authenticated Pages       Admin Panel       │
│  ──────────────────     ──────────────────        ───────────       │
│  • Leaderboard (SSG)   • Submit prediction       • Review queue     │
│  • Analyst profiles    • Watchlist/alerts         • Manage analysts  │
│    (SSG + ISR)         • Follow analysts         • Approve/reject   │
│  • Stock pages (SSG)   • Notification prefs      • Seed data        │
│  • Search/filters                                                   │
│                                                                     │
│  Deployed: Azure Container Apps                                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST API (HTTPS)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI / Python)                       │
│                                                                     │
│  API Layer                  Services                   Workers       │
│  ─────────                  ────────                   ───────       │
│  • /api/predictions         • Prediction service       • Price       │
│  • /api/analysts            • Analyst scoring            fetcher     │
│  • /api/stocks              • Outcome evaluator        • Outcome     │
│  • /api/auth                • AI extraction               evaluator  │
│  • /api/admin               • Source archival           • Scorecard  │
│  • /api/extract (AI)        • Notification service       updater    │
│                                                                     │
│  Deployed: Azure Container Apps                                     │
└───────┬─────────────────┬─────────────────────┬─────────────────────┘
        │                 │                     │
        ▼                 ▼                     ▼
┌──────────────┐  ┌──────────────┐  ┌────────────────────┐
│  PostgreSQL  │  │    Redis     │  │  External Services  │
│              │  │              │  │                     │
│  • Analysts  │  │  • Cache     │  │  • Yahoo Finance    │
│  • Stocks    │  │  • Job queue │  │  • Claude API       │
│  • Predicts  │  │  • Sessions  │  │  • Web Archive API  │
│  • Outcomes  │  │  • Rate limit│  │  • Email (Resend)   │
│  • Users     │  │              │  │  • OAuth providers   │
│              │  │              │  │                     │
│  Azure PG    │  │  Azure Redis │  └────────────────────┘
└──────────────┘  └──────────────┘
```

### Why Separate Frontend + Backend

1. **Independent deployment** — push frontend changes without touching backend
2. **API-first design** — the same backend serves the web app, future mobile app, and public API (Phase 5)
3. **Tech flexibility** — Python backend is ideal for data processing, AI integration, and financial computations
4. **Team scalability** — frontend and backend can be worked on independently

### Why Python (FastAPI) for Backend

1. **Best AI/ML ecosystem** — Anthropic SDK, data processing libraries
2. **Financial data libraries** — `yfinance`, `nsetools`, `pandas` for price data
3. **FastAPI performance** — async, type-safe, auto-generated OpenAPI docs
4. **Rapid development** — Pydantic models, dependency injection, middleware

### Why Next.js (React) for Frontend

1. **SSR/SSG for SEO** — analyst profiles, stock pages, and leaderboard need search engine visibility (people will search for analyst names). Next.js App Router with ISR (Incremental Static Regeneration) delivers both performance and SEO
2. **Built-in routing** — file-system routing, layouts, loading states, error boundaries
3. **Rich component ecosystem** — Shadcn/ui, Recharts for analytics dashboards
4. **TypeScript** — type-safe API consumption with generated types from OpenAPI spec
5. **Containerizable** — Next.js `standalone` output mode produces a minimal Node.js server ideal for Docker/Azure Container Apps

---

## Database Schema Design

### Core Tables

```sql
-- Analysts and firms
CREATE TABLE firms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL UNIQUE,
    type            VARCHAR(50) NOT NULL,          -- 'brokerage', 'media', 'independent', 'individual'
    website         VARCHAR(500),
    logo_url        VARCHAR(500),
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE analysts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,
    slug            VARCHAR(200) NOT NULL UNIQUE,  -- URL-friendly: rajat-rajgarhia
    firm_id         UUID REFERENCES firms(id),
    designation     VARCHAR(200),
    bio             TEXT,
    avatar_url      VARCHAR(500),
    social_links    JSONB DEFAULT '{}',            -- {"twitter": "...", "linkedin": "..."}
    sebi_reg_no     VARCHAR(50),                   -- SEBI registration number if available
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Stocks
CREATE TABLE stocks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol          VARCHAR(30) NOT NULL UNIQUE,   -- e.g., 'RELIANCE', 'INFY' (unique but not PK — symbols can change)
    exchange        VARCHAR(10) NOT NULL,           -- 'NSE', 'BSE'
    bse_code        VARCHAR(10),                   -- BSE scrip code
    name            VARCHAR(200) NOT NULL,
    sector          VARCHAR(100),
    industry        VARCHAR(100),
    market_cap      BIGINT,                        -- cached, updated daily
    current_price   DECIMAL(12,2),                 -- cached, updated daily
    price_updated_at TIMESTAMPTZ,
    is_active       BOOLEAN DEFAULT TRUE,          -- false for delisted/suspended stocks
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Stock daily prices (historical data for outcome evaluation)
CREATE TABLE stock_daily_prices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_id        UUID NOT NULL REFERENCES stocks(id),
    trade_date      DATE NOT NULL,
    open_price      DECIMAL(12,2),
    high_price      DECIMAL(12,2),
    low_price       DECIMAL(12,2),
    close_price     DECIMAL(12,2) NOT NULL,
    volume          BIGINT,
    adjusted_close  DECIMAL(12,2),                 -- adjusted for splits/bonuses
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_id, trade_date)
);

-- Users (defined before predictions due to foreign key dependency)
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(320) NOT NULL UNIQUE,
    name            VARCHAR(200),
    avatar_url      VARCHAR(500),
    password_hash   VARCHAR(200),                  -- for email/password auth (nullable for OAuth-only users)
    role            VARCHAR(20) DEFAULT 'user',    -- 'user', 'moderator', 'admin'
    oauth_provider  VARCHAR(20),                   -- 'google', 'github'
    oauth_id        VARCHAR(200),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ
);

-- Predictions (the heart of the system)
CREATE TABLE predictions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analyst_id      UUID NOT NULL REFERENCES analysts(id),
    stock_id        UUID NOT NULL REFERENCES stocks(id),

    -- The prediction itself
    target_price    DECIMAL(12,2) NOT NULL,
    price_at_prediction DECIMAL(12,2) NOT NULL,    -- stock price when prediction was made
    upside_pct      DECIMAL(8,2) GENERATED ALWAYS AS
                        (((target_price - price_at_prediction) / price_at_prediction) * 100) STORED,
    prediction_date DATE NOT NULL,                 -- when the analyst made the call
    target_date     DATE,                          -- when they expect it to hit (nullable)
    default_eval_date DATE NOT NULL,               -- fallback: prediction_date + 12 months (default timeframe)

    -- Source & provenance
    source_url      VARCHAR(1000) NOT NULL,
    source_type     VARCHAR(30) NOT NULL,          -- 'article', 'tv_transcript', 'research_report', 'tweet', 'interview'
    source_archive_url VARCHAR(1000),              -- web.archive.org snapshot
    raw_quote       TEXT,                          -- exact quote from the analyst

    -- Metadata
    submitted_by    UUID REFERENCES users(id),     -- who submitted this prediction
    extraction_method VARCHAR(30) DEFAULT 'manual', -- 'manual', 'ai_assisted', 'ai_auto'
    ai_confidence   DECIMAL(5,2),                  -- if AI-extracted, confidence score
    status          VARCHAR(20) DEFAULT 'pending_review', -- 'pending_review', 'approved', 'rejected', 'duplicate'
    reviewed_by     UUID REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_target_price CHECK (target_price > 0),
    CONSTRAINT valid_prediction_price CHECK (price_at_prediction > 0)
);

-- Prediction outcomes (evaluated by the system)
CREATE TABLE prediction_outcomes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id   UUID NOT NULL UNIQUE REFERENCES predictions(id),

    outcome_status  VARCHAR(20) NOT NULL,          -- 'hit', 'miss', 'partial_hit', 'pending', 'expired'
    actual_price    DECIMAL(12,2),                 -- closing price at evaluation date
    highest_price   DECIMAL(12,2),                 -- highest closing price during tracking window
    lowest_price    DECIMAL(12,2),                 -- lowest closing price during tracking window
    deviation_pct   DECIMAL(8,2),                  -- how far off the target was

    evaluated_at    TIMESTAMPTZ,                   -- when outcome was determined
    evaluation_date DATE,                          -- the date the prediction expired/was evaluated

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Analyst scorecards (materialized/cached aggregations)
CREATE TABLE analyst_scorecards (
    analyst_id          UUID PRIMARY KEY REFERENCES analysts(id),
    total_predictions   INT DEFAULT 0,
    hits                INT DEFAULT 0,
    misses              INT DEFAULT 0,
    partial_hits        INT DEFAULT 0,
    pending             INT DEFAULT 0,
    accuracy_pct        DECIMAL(5,2),              -- (hits + 0.5*partial) / total_evaluated * 100
    avg_deviation_pct   DECIMAL(8,2),
    avg_upside_predicted DECIMAL(8,2),             -- average boldness of predictions
    best_sector         VARCHAR(100),
    worst_sector        VARCHAR(100),
    sector_accuracy     JSONB DEFAULT '{}',        -- {"IT": 72.5, "Pharma": 45.0, ...}
    streak_current      INT DEFAULT 0,             -- current consecutive hits (or misses if negative)
    last_prediction_date DATE,
    last_updated        TIMESTAMPTZ DEFAULT NOW()
);

-- Notifications
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    type            VARCHAR(50) NOT NULL,          -- 'prediction_outcome', 'new_prediction', 'analyst_update'
    title           VARCHAR(300) NOT NULL,
    message         TEXT,
    data            JSONB DEFAULT '{}',            -- structured payload (prediction_id, analyst_id, etc.)
    is_read         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- User engagement features
CREATE TABLE user_watchlist (
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    stock_id        UUID REFERENCES stocks(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, stock_id)
);

CREATE TABLE user_followed_analysts (
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    analyst_id      UUID REFERENCES analysts(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, analyst_id)
);

-- Indexes for common queries
CREATE INDEX idx_stock_daily_prices_lookup ON stock_daily_prices(stock_id, trade_date DESC);
CREATE INDEX idx_predictions_analyst ON predictions(analyst_id, prediction_date DESC);
CREATE INDEX idx_predictions_stock ON predictions(stock_id, prediction_date DESC);
CREATE INDEX idx_predictions_status ON predictions(status);
CREATE INDEX idx_predictions_date ON predictions(prediction_date DESC);
CREATE INDEX idx_predictions_approved_pending ON predictions(default_eval_date)
    WHERE status = 'approved';
CREATE INDEX idx_outcomes_prediction ON prediction_outcomes(prediction_id);
CREATE INDEX idx_outcomes_status ON prediction_outcomes(outcome_status);
CREATE INDEX idx_scorecards_accuracy ON analyst_scorecards(accuracy_pct DESC)
    WHERE total_predictions >= 10;
CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC)
    WHERE is_read = FALSE;
```

### Evaluation Logic (Pseudocode)

```
For each approved prediction where eval_date <= today AND no final outcome exists:

    1. Get stock price history from prediction_date to eval_date
    2. actual_price = closing price on eval_date (or nearest trading day)
    3. highest_price = max closing price in the window
    4. lowest_price = min closing price in the window

    If prediction is BULLISH (target > price_at_prediction):
        IF highest_price >= target_price:
            outcome = HIT (stock reached the target at some point)
        ELIF highest_price >= target_price * 0.95:
            outcome = PARTIAL_HIT (within 5% tolerance)
        ELSE:
            outcome = MISS

    If prediction is BEARISH (target < price_at_prediction):
        IF lowest_price <= target_price:
            outcome = HIT
        ELIF lowest_price <= target_price * 1.05:
            outcome = PARTIAL_HIT
        ELSE:
            outcome = MISS

    deviation_pct = ((actual_price - target_price) / target_price) * 100

    Store outcome with all price data points
```

---

## Tech Stack (Final)

### Backend

| Component | Technology | Cost |
|-----------|-----------|------|
| Framework | **FastAPI** (Python 3.12+) | Free |
| ORM | **SQLAlchemy 2.0** + Alembic (migrations) | Free |
| Validation | **Pydantic v2** (built into FastAPI) | Free |
| Task Queue | **Celery** + Redis (or **ARQ** for lightweight async) | Free |
| AI | **Anthropic Python SDK** (Claude Sonnet for extraction) | ~$5-15/mo at MVP scale |
| Auth | **python-jose** (JWT verification) — frontend handles OAuth via NextAuth.js | Free |
| Price Data | **yfinance** (primary) + **nsetools** (fallback) | Free |
| Hosting | **Azure Container Apps** (both frontend + backend) | ~$15-30/mo (consumption plan) |
| Database | **Azure Database for PostgreSQL** (Flexible Server, Burstable B1ms) | ~$15-25/mo |
| Cache/Queue | **Azure Cache for Redis** (Basic C0) | ~$15-20/mo |

### Frontend

| Component | Technology | Cost |
|-----------|-----------|------|
| Framework | **Next.js 15** (App Router) + **React 19** | Free |
| Routing | **Next.js file-system routing** (App Router) | Free |
| UI Library | **Shadcn/ui** + **Tailwind CSS** | Free |
| Charts | **Recharts** or **Tremor** | Free |
| State | **TanStack Query** (server state) + **Zustand** (client state) | Free |
| Auth | **NextAuth.js v5** (Google OAuth) | Free |
| API Client | Auto-generated from OpenAPI spec (**openapi-typescript-fetch**) | Free |
| Hosting | **Azure Container Apps** (shared with backend infra) | Included above |

### Estimated Monthly Cost: **$50–90/month**

(Within the $50–100 budget. Azure consumption-based pricing keeps idle costs low. Claude API usage adds ~$5-15/mo.)

---

## Stock Price Data Strategy

### Primary: yfinance (Yahoo Finance)
- **Format**: NSE symbols use `.NS` suffix (e.g., `RELIANCE.NS`), BSE uses `.BO`
- **Pros**: Free, reliable, both historical and current data, well-maintained Python library
- **Cons**: Unofficial API (scrapes Yahoo), no SLA, occasional rate limiting
- **Use for**: Daily end-of-day prices, historical price data for outcome evaluation

### Fallback: nsetools
- **Pros**: Direct NSE data, actively maintained (v2.0.1, March 2025), no authentication needed
- **Cons**: NSE only (no BSE), smaller community, real-time only (limited historical data)
- **Use for**: Real-time price lookups, stock metadata, NSE-specific data

### Strategy
1. Run a **nightly job** (11 PM IST, after market close at 3:30 PM) to fetch EOD prices via yfinance
2. Cache prices in the `stocks` table
3. Use nsetools for on-demand real-time lookups when needed
4. If yfinance fails, queue for retry with exponential backoff
5. Store all fetched price data in the `stock_daily_prices` table for outcome evaluation

---

## AI-Assisted Prediction Entry Flow

This is the "AI-assisted manual entry" approach — the user drives, AI helps.

```
USER                           FRONTEND                        BACKEND
─────                          ────────                        ───────

1. Pastes article URL    →     Sends URL to /api/extract  →   Fetches article content
                                                               (via httpx or newspaper3k)
                                                           →   Sends to Claude Sonnet:
                                                               "Extract stock predictions
                                                                from this article..."
                                                           →   Returns structured data

2. Sees pre-filled form  ←     Renders form with:         ←   Response:
                               • Analyst: "Rajat Rajgarhia"    {analyst, firm, stock,
                               • Firm: "Motilal Oswal"          target_price, timeframe,
                               • Stock: INFY                    raw_quote, confidence}
                               • Target: ₹2,100
                               • Timeframe: 12 months
                               • Quote: "sees Infosys..."
                               • Confidence: 92%

3. Reviews, corrects     →     User can edit any field
   any errors, submits          before submitting

4. Prediction saved      ←     POST /api/predictions      →   Validate, save with
                                                               status='pending_review'
                                                               Archive source URL
```

### Claude Extraction Prompt (Template)

```
You are a financial prediction extractor. Given a news article about
Indian stock markets, extract ALL stock price target predictions.

For each prediction found, return:
{
  "analyst_name": "...",
  "firm_name": "...",
  "stock_name": "...",
  "stock_symbol": "...",      // NSE symbol if identifiable
  "target_price": 0.00,       // in INR
  "current_price_mentioned": 0.00,  // if article mentions current price
  "timeframe": "...",         // e.g., "12 months", "by March 2027"
  "direction": "bullish|bearish",
  "raw_quote": "...",         // exact sentence with the prediction
  "confidence": 0.0           // your confidence in extraction accuracy (0-1)
}

Rules:
- Only extract SPECIFIC price targets (e.g., "target of ₹2,100")
- Skip vague predictions ("stock looks positive", "will do well")
- If timeframe is not mentioned, set to null
- If you're unsure about the stock symbol, set confidence lower
- Extract ALL predictions if the article mentions multiple stocks
```

---

## Source Archival Strategy

Analysts sometimes delete or edit predictions. We need proof.

1. **On prediction submission**: Automatically submit the source URL to the Wayback Machine Save API
   - `POST https://web.archive.org/save/{url}`
   - Store the returned archive URL in `source_archive_url`
2. **Screenshot fallback**: For URLs that can't be archived (paywalled, dynamic), allow users to upload a screenshot
3. **Raw text storage**: Store the extracted article text/quote in the prediction record itself

---

## API Design (Key Endpoints)

### Public Endpoints (no auth)
```
GET  /api/v1/health                         # Health check
GET  /api/v1/leaderboard                    # Top analysts by accuracy (paginated)
GET  /api/v1/leaderboard?sector=IT          # Sector-filtered leaderboard
GET  /api/v1/analysts/:slug                 # Analyst profile + stats
GET  /api/v1/analysts/:slug/predictions     # Analyst's prediction history (paginated)
GET  /api/v1/stocks/:symbol                 # Stock page with all predictions
GET  /api/v1/stocks/:symbol/predictions     # Predictions for a stock (paginated)
GET  /api/v1/predictions/recent             # Recently added predictions (paginated)
GET  /api/v1/search?q=term                  # Search analysts and stocks
GET  /api/v1/stats                          # Platform-wide stats
```

### Authenticated Endpoints (user)
```
POST /api/v1/auth/register                  # Email/password registration
POST /api/v1/auth/login                     # Email/password login
POST /api/v1/auth/verify-token              # Verify NextAuth JWT
GET  /api/v1/auth/me                        # Current user profile
POST /api/v1/predictions                    # Submit a new prediction
POST /api/v1/extract                        # AI-extract from URL (returns pre-filled data)
GET  /api/v1/me/watchlist                   # User's watchlist
POST /api/v1/me/watchlist/:stock_id         # Add stock to watchlist
DELETE /api/v1/me/watchlist/:stock_id       # Remove from watchlist
POST /api/v1/me/follow/:analyst_id          # Follow an analyst
DELETE /api/v1/me/follow/:analyst_id        # Unfollow
GET  /api/v1/me/notifications               # User notifications (paginated)
PATCH /api/v1/me/notifications/:id/read     # Mark notification as read
```

### Admin/Moderator Endpoints
```
GET  /api/v1/admin/review-queue             # Predictions pending review (paginated)
POST /api/v1/admin/predictions/:id/approve  # Approve a prediction
POST /api/v1/admin/predictions/:id/reject   # Reject a prediction
POST /api/v1/admin/analysts                 # Create/edit analyst profiles
POST /api/v1/admin/stocks                   # Add stocks manually
POST /api/v1/admin/trigger-evaluation       # Manually trigger outcome evaluation
```

---

## Background Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| **Price Fetcher** | Daily 11:00 PM IST | Fetch EOD prices for all tracked stocks |
| **Outcome Evaluator** | Daily 11:30 PM IST | Evaluate all pending predictions against current prices |
| **Scorecard Updater** | Daily 11:45 PM IST | Recalculate analyst scorecards after new outcomes |
| **Source Archiver** | On prediction submit | Submit source URL to Wayback Machine |
| **Notification Sender** | After evaluation | Notify users about outcomes for their watchlist/followed analysts |
| **Stale Price Checker** | Weekly | Flag stocks with outdated prices (delisted, suspended) |

---

## Frontend Pages & Layout

### Page Map

```
/                              → Homepage: featured leaderboard + recent predictions
/leaderboard                   → Full leaderboard with filters (sector, timeframe, firm)
/analyst/:slug                 → Analyst profile: bio, stats, prediction history, accuracy chart
/stock/:symbol                 → Stock page: all predictions, consensus target, analyst spread
/predictions                   → Browse all predictions with filters
/submit                        → Submit a prediction (auth required)
/submit?url=...                → AI-assisted submission with pre-filled URL
/search?q=...                  → Search results (analysts + stocks)
/login                         → OAuth login page
/dashboard                     → User dashboard: watchlist, followed analysts, alerts
/admin                         → Admin panel: review queue, manage entities
/about                         → About page, methodology explanation
```

### Key UI Components

1. **Analyst Card** — avatar, name, firm, accuracy badge, total predictions, accuracy %
2. **Prediction Card** — stock, target, current price, analyst, date, outcome status (color-coded)
3. **Accuracy Badge** — visual indicator: green (>65%), yellow (45-65%), red (<45%), gray (insufficient data)
4. **Accuracy Trend Chart** — line chart showing analyst accuracy over time (rolling 20 predictions)
5. **Stock Prediction Spread** — horizontal bar showing all analyst targets for a stock vs current price
6. **Submission Form** — URL input → AI extraction → editable form → submit

---

## Rollout Timeline (Revised)

### Sprint 0: Foundation (Days 1-3)
- [ ] Project scaffolding: backend (FastAPI + uv) + frontend (Next.js + TypeScript)
- [ ] Database schema: Alembic migrations for all core tables (including `stock_daily_prices` and `notifications`)
- [ ] CI/CD pipeline: GitHub Actions for lint, test, deploy
- [ ] Dev environment: Docker Compose (PostgreSQL + Redis)
- [ ] CORS middleware configuration (FastAPI ↔ Next.js frontend)
- [ ] Environment variable management (.env files, config module)
- [ ] Health check endpoint (`GET /api/v1/health`)
- [ ] Deploy skeleton apps: backend + frontend on Azure Container Apps

### Sprint 1: Core Data Layer (Days 4-10)
- [ ] CRUD APIs: analysts, firms, stocks, predictions
- [ ] Stock price fetcher job (yfinance + nsetools)
- [ ] Seed initial stock data: NSE top 200 companies (symbol, name, sector)
- [ ] Admin panel: basic CRUD for analysts, firms
- [ ] Input validation and error handling

### Sprint 2: Prediction Entry & AI Assist (Days 11-17)
- [ ] Manual prediction submission form (frontend)
- [ ] AI extraction endpoint: URL → Claude → structured prediction data
- [ ] Pre-filled form flow (paste URL → review → submit)
- [ ] Source archival (Wayback Machine integration)
- [ ] Duplicate detection (same analyst + stock + similar target + similar date)
- [ ] Review queue for moderators

### Sprint 3: Evaluation Engine (Days 18-24)
- [ ] Historical price data storage (`stock_daily_prices` table)
- [ ] Outcome evaluation job: daily run comparing predictions to actual prices
- [ ] Hit/miss/partial_hit logic with tolerance bands
- [ ] Scorecard computation job
- [ ] Handle edge cases: stock splits, delistings, mergers

### Sprint 4: Public Interface (Days 25-34)
- [ ] Leaderboard page with sorting and filtering
- [ ] Analyst profile pages (stats, prediction history, accuracy trend chart)
- [ ] Stock pages (all predictions, consensus view)
- [ ] Search functionality (full-text search on analyst names, stock names)
- [ ] Responsive design (mobile-first for retail investor audience)
- [ ] SEO: meta tags, structured data (Schema.org), SSG for key pages

### Sprint 5: User Features & Auth (Days 35-41)
- [ ] Google OAuth integration
- [ ] User dashboard (watchlist, followed analysts)
- [ ] Follow/unfollow analysts
- [ ] Stock watchlist
- [ ] Email notifications (Resend API) for prediction outcomes
- [ ] User submission flow with moderation

### Sprint 6: Historical Seeding & Polish (Days 42-48)
- [ ] Research and enter ~100 historical predictions from well-known analysts
- [ ] Backfill historical price data for those predictions
- [ ] Run evaluation engine on historical data
- [ ] Landing page with value proposition
- [ ] About/methodology page (transparency about scoring)
- [ ] Performance optimization (caching, query tuning)
- [ ] Error monitoring (Sentry)

### --- MVP LAUNCH (Invite-Only Beta) — ~Week 7 ---

### Sprint 7: Feedback & Iteration (Days 49-55)
- [ ] Collect beta user feedback
- [ ] Fix bugs and UX issues
- [ ] Add missing filters/sorting options
- [ ] Improve AI extraction accuracy based on real articles
- [ ] Rate limiting and abuse prevention

### Sprint 8: Public Beta Prep (Days 56-62)
- [ ] Load testing
- [ ] Security audit (OWASP top 10)
- [ ] Terms of service, privacy policy, disclaimer
- [ ] Social sharing: OG images for analyst profiles and predictions
- [ ] Twitter/X bot: auto-post when notable predictions hit or miss (optional)

### --- PUBLIC BETA LAUNCH — ~Week 9 ---

---

## Post-MVP Roadmap (Phases 2-5)

### Phase 2: Full Agentic Ingestion (Month 3-4)
- RSS feed monitoring for financial news sites (Moneycontrol, ET, LiveMint, CNBC TV18)
- Automated prediction extraction pipeline with confidence thresholds
- Auto-approve high-confidence extractions, queue others for review
- Social media monitoring (X/Twitter) for analyst calls

### Phase 3: Community & Engagement (Month 4-5)
- Analyst claim/verify profile system
- Analyst rebuttal feature (add context to misses)
- Reliability badges (displayed across the platform)
- Push notifications (web + email digests)
- Community leaderboard (top submitters)

### Phase 4: Advanced Analytics (Month 5-7)
- Sector-wise accuracy breakdown
- Bull vs bear market performance
- Timeframe analysis (short-term vs long-term accuracy)
- Contrarian indicator detection
- Herding detection (multiple analysts giving similar targets)
- "Would you have been better off buying Nifty 50?" comparison
- Head-to-head analyst comparison tool

### Phase 5: Monetization (Month 7+)
- Freemium tier: detailed analytics, API access, premium alerts behind subscription
- Public API for fintech apps
- Institutional accuracy reports
- Premium alerts: real-time notifications when high-accuracy analysts make new calls

---

## Data Sources for News & Predictions

### Primary Sources (for AI-assisted extraction and future scraping)

| Source | Type | Availability |
|--------|------|-------------|
| **Moneycontrol** | Articles, analyst reports | RSS feed available, most comprehensive |
| **Economic Times Markets** | News articles | RSS available |
| **LiveMint** | Market news | RSS available |
| **CNBC TV18** | TV transcripts, articles | Limited RSS |
| **Business Standard** | Research reports | RSS available |
| **Trendlyne** | Aggregated analyst targets | Structured data (potential partner) |
| **Screener.in** | Company fundamentals | API may be available |
| **SEBI RA Database** | Registered analyst list | Public records (for analyst verification) |
| **X/Twitter** | Analyst posts | API (paid tier required) |

### For Historical Seeding
- Manually collect ~100 well-known predictions from the past 1-2 years
- Focus on high-profile calls that were widely reported
- Sources: Moneycontrol archives, ET Markets archives, CNBC TV18 show archives
- Prioritize predictions from the top 20-30 most followed analysts/firms

---

## Key Risks & Mitigations (Updated)

| Risk | Mitigation |
|------|------------|
| **Legal pushback from analysts/firms** | Only track publicly available predictions. Link to original source. Present data factually. Allow analyst rebuttals. Add clear disclaimers. Consult a lawyer before public launch. |
| **Yahoo Finance API instability** | Dual-source strategy (yfinance + nsetools). Cache aggressively. Alert on fetch failures. Consider paid data source upgrade if free sources become unreliable. |
| **AI extraction errors** | Human review queue for ALL AI-extracted predictions in MVP. Track extraction accuracy. Tune prompts based on error patterns. Never auto-approve without sufficient confidence. |
| **Cold start (not enough data)** | Seed 100 historical predictions. Focus on 20-30 top analysts. Make manual submission easy. Build submission community early. |
| **Stock corporate actions** | Track splits, bonuses, mergers. Adjust historical prices accordingly. Flag predictions affected by unforeseeable corporate actions. |
| **Analyst gaming (vague predictions)** | Only accept specific price targets. Require source URL. Community can flag vague/misleading entries. |
| **Scope creep** | Stick to NSE/BSE equities. Price targets only. No derivatives, no commodities, no macro. Expand only after MVP validates. |

---

## Success Criteria for MVP Launch

| Metric | Target |
|--------|--------|
| Tracked predictions | 200+ (100 seeded + 100 new) |
| Analysts covered | 30+ |
| Stocks covered | 50+ |
| Data accuracy | >95% correct prediction-to-outcome mapping |
| AI extraction accuracy | >80% of fields correctly pre-filled |
| Page load time | <2 seconds (leaderboard, profiles) |
| Beta users | 50+ active users within first month |
| Community submissions | 20+ user-submitted predictions in first month |

---

## Project Structure (Directory Layout)

```
enex/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── analysts.py
│   │   │   │   ├── predictions.py
│   │   │   │   ├── stocks.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── admin.py
│   │   │   │   ├── extract.py          # AI extraction endpoint
│   │   │   │   └── leaderboard.py
│   │   │   └── dependencies.py         # Auth middleware, DB session, etc.
│   │   ├── models/                      # SQLAlchemy models
│   │   │   ├── analyst.py
│   │   │   ├── prediction.py
│   │   │   ├── stock.py
│   │   │   ├── user.py
│   │   │   └── outcome.py
│   │   ├── schemas/                     # Pydantic request/response schemas
│   │   │   ├── analyst.py
│   │   │   ├── prediction.py
│   │   │   ├── stock.py
│   │   │   └── common.py               # Pagination, error responses
│   │   ├── services/                    # Business logic
│   │   │   ├── prediction_service.py
│   │   │   ├── evaluation_service.py
│   │   │   ├── scoring_service.py
│   │   │   ├── extraction_service.py    # Claude AI extraction
│   │   │   ├── price_service.py         # Stock price fetching
│   │   │   └── archive_service.py       # Source archival
│   │   ├── jobs/                        # Background tasks
│   │   │   ├── price_fetcher.py
│   │   │   ├── outcome_evaluator.py
│   │   │   ├── scorecard_updater.py
│   │   │   └── notification_sender.py
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic Settings (env vars)
│   │   │   ├── database.py
│   │   │   ├── security.py             # JWT verification, password hashing
│   │   │   └── redis.py
│   │   └── main.py                     # FastAPI app, CORS, router registration
│   ├── alembic/                         # Database migrations
│   ├── tests/
│   ├── pyproject.toml                 # Managed by uv
│   ├── uv.lock                        # uv lockfile
│   └── Dockerfile
│
├── frontend/                            # Next.js 15 (App Router)
│   ├── app/
│   │   ├── layout.tsx                   # Root layout (providers, nav, footer)
│   │   ├── page.tsx                     # Homepage: leaderboard + recent predictions
│   │   ├── leaderboard/
│   │   │   └── page.tsx                 # Full leaderboard with filters (SSG + ISR)
│   │   ├── analyst/
│   │   │   └── [slug]/
│   │   │       └── page.tsx             # Analyst profile (SSG + ISR)
│   │   ├── stock/
│   │   │   └── [symbol]/
│   │   │       └── page.tsx             # Stock page (SSG + ISR)
│   │   ├── predictions/
│   │   │   └── page.tsx                 # Browse predictions
│   │   ├── submit/
│   │   │   └── page.tsx                 # Submit prediction (auth required)
│   │   ├── search/
│   │   │   └── page.tsx                 # Search results
│   │   ├── dashboard/
│   │   │   └── page.tsx                 # User dashboard (auth required)
│   │   ├── admin/
│   │   │   └── page.tsx                 # Admin panel (admin role required)
│   │   ├── login/
│   │   │   └── page.tsx                 # OAuth login
│   │   ├── about/
│   │   │   └── page.tsx                 # Methodology + about
│   │   └── api/auth/
│   │       └── [...nextauth]/
│   │           └── route.ts             # NextAuth.js API route
│   ├── components/
│   │   ├── ui/                          # Shadcn components
│   │   ├── AnalystCard.tsx
│   │   ├── PredictionCard.tsx
│   │   ├── AccuracyBadge.tsx
│   │   ├── LeaderboardTable.tsx
│   │   └── SubmissionForm.tsx
│   ├── lib/
│   │   ├── api-client.ts                # Auto-generated from OpenAPI spec
│   │   ├── auth.ts                      # NextAuth.js config
│   │   └── utils.ts
│   ├── hooks/                           # Custom React hooks
│   ├── stores/                          # Zustand stores
│   ├── public/
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── Dockerfile                     # Next.js standalone output for container deployment
│
├── docker-compose.yml                   # Local dev (Postgres + Redis)
├── PLAN.md                              # Product vision
├── ROLLOUT_PLAN.md                      # This file
└── README.md
```

---

## Deployment Setup

### Local Development
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: enex
      POSTGRES_USER: enex
      POSTGRES_PASSWORD: dev_password
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  pgdata:
```

### Production (Azure)

```
Azure Resource Group: rg-enex
├── Azure Container Apps Environment
│   ├── enex-backend          (FastAPI container, consumption plan)
│   └── enex-frontend         (Next.js container, consumption plan)
├── Azure Database for PostgreSQL (Flexible Server, Burstable B1ms)
├── Azure Cache for Redis (Basic C0)
├── Azure Container Registry   (for Docker images)
├── Azure Key Vault            (secrets: API keys, JWT secret, DB credentials)
└── Azure Monitor / App Insights (logging, metrics, alerting)
```

- **Backend**: FastAPI container deployed to Azure Container Apps (auto-scaling, consumption-based)
- **Frontend**: Next.js container deployed to Azure Container Apps (SSR requires a Node runtime)
- **Database**: Azure Database for PostgreSQL Flexible Server (Burstable B1ms, ~$15-25/mo)
- **Redis**: Azure Cache for Redis Basic C0 (~$15-20/mo)
- **Container Registry**: Azure Container Registry Basic ($5/mo) for Docker images
- **Secrets**: Azure Key Vault (free tier) for API keys, credentials, JWT secrets
- **Monitoring**: Azure Monitor + Application Insights (free tier) + Sentry (free tier)
- **Domain**: Purchase `enex.in` or similar (for Indian market focus)

### CI/CD (GitHub Actions)
```
On push to main:
  1. Run linting (ruff for Python, eslint for TypeScript)
  2. Run tests (pytest for backend, Jest/React Testing Library for frontend)
  3. Type check (mypy for Python, tsc --noEmit for TypeScript)
  4. Build Docker images (backend + frontend)
  5. Push images to Azure Container Registry
  6. Deploy to Azure Container Apps (via az containerapp update or GitHub Actions Azure integration)
```

---

## Authentication Strategy

### Architecture
- **Frontend (Next.js)**: NextAuth.js v5 handles OAuth flow (Google provider), session management, and CSRF protection
- **Backend (FastAPI)**: Receives JWT tokens from the frontend and verifies them. Does NOT manage OAuth flow directly
- **Flow**: User logs in via NextAuth.js → NextAuth creates a session + JWT → frontend sends JWT in `Authorization: Bearer <token>` header → FastAPI middleware verifies the JWT signature and extracts user info

### Auth Endpoints
- `POST /api/v1/auth/register` — email/password registration (hashed with bcrypt via `passlib`)
- `POST /api/v1/auth/login` — email/password login, returns JWT
- `POST /api/v1/auth/verify-token` — validate a NextAuth JWT token
- `GET /api/v1/auth/me` — get current user profile from JWT

### JWT Configuration
- Access token expiry: 1 hour
- Refresh token expiry: 7 days
- Algorithm: HS256 with a shared secret between Next.js and FastAPI
- Token payload: `{ sub: user_id, role: "user"|"moderator"|"admin", exp: ... }`

---

## Implementation Considerations

> These items should be addressed during implementation (Sprint 0/1) but are documented here for planning purposes.

### API Versioning
- All endpoints use `/api/v1/` prefix from day 1
- Example: `GET /api/v1/leaderboard`, `POST /api/v1/predictions`
- Enables non-breaking changes in future versions

### CORS Configuration
- FastAPI CORS middleware must allow the frontend origin
- Dev: `http://localhost:3000`
- Prod: `https://enex-frontend.<azure-region>.azurecontainerapps.io` (or custom domain)
- Allow headers: `Authorization`, `Content-Type`
- Allow methods: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`

### Timezone Handling
- **Store everything in UTC** in the database (use `TIMESTAMPTZ`)
- **Display in IST** (UTC+5:30) on the frontend
- Background jobs use IST-aware scheduling (11 PM IST = 5:30 PM UTC)
- Prediction dates and evaluation dates are `DATE` type (timezone-independent)

### Pagination
- All list endpoints return paginated responses
- Standard format: `{ items: [...], total: N, page: 1, page_size: 20, pages: M }`
- Default page size: 20, max: 100
- Endpoints: leaderboard, predictions, analyst history, stock predictions, notifications, review queue

### Standard API Error Response
```json
{
  "error": {
    "code": "PREDICTION_NOT_FOUND",
    "message": "Prediction with ID xyz does not exist",
    "details": {}
  }
}
```
- HTTP status codes: 400 (validation), 401 (unauthorized), 403 (forbidden), 404 (not found), 422 (unprocessable), 500 (server error)

### Environment Variables
```
# Backend (.env) — in production, stored in Azure Key Vault and injected via Container Apps secrets
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/enex
REDIS_URL=rediss://host:6380/0          # Azure Redis uses SSL on port 6380
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET=<shared-secret>
CORS_ORIGINS=http://localhost:3000,https://enex-frontend.<region>.azurecontainerapps.io
SENTRY_DSN=...

# Frontend (.env.local) — in production, set as Container Apps env vars
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXTAUTH_SECRET=<shared-secret>
NEXTAUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

### Health Check
- `GET /api/v1/health` — returns `{ status: "ok", db: "connected", redis: "connected", version: "0.1.0" }`
- Used by Azure Container Apps for liveness/readiness probes and deployment health checks

### Default Evaluation Timeframe
- When a prediction has no explicit `target_date`, use **12 months** from `prediction_date`
- Stored in `default_eval_date = prediction_date + INTERVAL '12 months'`
- Configurable via environment variable `DEFAULT_EVAL_MONTHS=12`

### Logging & Monitoring
- **Structured logging**: Python `structlog` for JSON-formatted logs
- **Error tracking**: Sentry (free tier) for both backend and frontend
- **Metrics (post-MVP)**: Track prediction volume, job success/failure rates, API latency
- **Alerting**: Sentry alerts for error spikes; Azure Monitor alerts for resource usage and container health

### Evaluation Price Clarification
- `highest_price` and `lowest_price` in `prediction_outcomes` refer to **daily closing prices** (not intraday highs/lows)
- This avoids data cost issues (intraday data is expensive) and is more conservative

---

## Deferred to Phase 3

The following features are intentionally deferred from the MVP to keep scope manageable. They will be implemented in Phase 3 (Community & Engagement):

| Feature | Description | Phase |
|---------|-------------|-------|
| **Community moderation model** | Wikipedia-style community moderation with reputation system. MVP uses admin-controlled review queue only. | Phase 3 |
| **Analyst identity verification** | Process for analysts to claim and verify their profiles. `is_verified` field exists in schema but verification workflow is deferred. | Phase 3 |
| **Reliability badges** | Visual badge system (green/yellow/red) based on accuracy thresholds. Data is available via scorecards; badge UI is deferred. | Phase 3 |
| **Analyst claim & rebuttal** | Allow analysts/firms to claim profiles and provide context for failed predictions. | Phase 3 |
| **Magnitude-weighted scoring** | Weighting scores by boldness of prediction (large upside calls that hit score higher). Simple hit/miss used for MVP. | Phase 4 |

---

## Disclaimer & Legal Considerations

Before public launch, ensure:

1. **Terms of Service** — clearly state: this is not financial advice, data is for informational purposes only
2. **Disclaimer on every page** — "Past accuracy does not guarantee future accuracy. Do your own research."
3. **SEBI compliance** — we are NOT providing investment advice, only tracking publicly available predictions
4. **Data attribution** — always link to original source of the prediction
5. **Right to respond** — allow analysts/firms to claim profiles and add context
6. **Privacy policy** — user data handling, GDPR-style opt-outs
7. **Legal review** — consult a lawyer familiar with Indian securities regulation before public launch

---

*This plan is a living document. Update as decisions evolve during implementation.*
