# Enex — System Architecture

> Analyst Prediction Tracker for Indian Equity Markets

---

## 1. System Architecture Overview

High-level view of all components, layers, and their interactions.

```mermaid
graph TB
    subgraph USERS["Users"]
        V["Visitor\n(unauthenticated)"]
        U["Registered User"]
        MOD["Moderator"]
        ADM["Admin"]
    end

    subgraph FE["Frontend — Next.js 15 · React 19 · Azure Container Apps"]
        PUB["Public Pages  SSG / ISR\nLeaderboard · Predictor Profiles · Stock Pages · Search"]
        AUTHP["Auth\nPhone OTP · Email OTP · Google OAuth"]
        USERP["User Pages  authenticated\nSubmit Prediction · Suggest · Dashboard · Watchlist"]
        ADMINP["Admin Panel\nReview Queue · Suggestions Queue · Bulk Import · User Management"]
    end

    subgraph BE["Backend — FastAPI · Python 3.12 · Azure Container Apps"]
        subgraph APIL["API Layer"]
            AAUTH["/auth\nOTP · OAuth · JWT"]
            ALB["/leaderboard"]
            APRED["/predictors\nprofiles · members"]
            ASTK["/stocks\nprices · predictions"]
            AADMIN["/admin\nreview · suggestions · bulk"]
            AEXT["/extract\nAI extraction"]
        end

        subgraph SVCS["Services"]
            SPRED["Predictor\nService"]
            SPRDCT["Prediction\nService"]
            SEVAL["Evaluation\nService"]
            SSCORE["Scoring\nService"]
            SAI["AI Extraction\nService"]
            SPRICE["Price\nService"]
            SARCH["Archive\nService"]
            SNOTIF["Notification\nService"]
        end

        subgraph JOBS["Background Jobs — Celery Beat"]
            JPF["Price Fetcher\n11:00 PM IST · daily"]
            JEV["Outcome Evaluator\n11:30 PM IST · daily"]
            JSC["Scorecard Updater\n11:45 PM IST · daily"]
            JNT["Notification Sender\npost-evaluation"]
        end
    end

    subgraph DATAL["Data Layer"]
        subgraph PG["PostgreSQL — Azure Database for PostgreSQL"]
            DP[("predictors")]
            DS[("stocks\ndaily_prices")]
            DPR[("predictions\nprediction_suggestions")]
            DO[("prediction_outcomes")]
            DSC[("predictor_scorecards")]
            DU[("users\notp_codes")]
            DN[("notifications\nwatchlist · follows")]
        end

        subgraph RD["Redis — Azure Cache for Redis"]
            RC["Leaderboard\nCache"]
            RQ["Celery\nJob Queue"]
            RR["Rate Limiting\nOTP Store"]
        end
    end

    subgraph EXT["External Services"]
        EC["Claude API\nSonnet · AI Extraction"]
        EY["Yahoo Finance\nyfinance · primary"]
        EN["nsetools\nNSE · fallback"]
        EW["Wayback Machine\nSource Archival"]
        ER["Resend API\nEmail OTP · Notifications"]
        EM["MSG91 Verify\nMobile OTP · DLT Compliant"]
        EG["Google OAuth 2.0"]
    end

    USERS -->|"HTTPS"| FE
    FE -->|"REST API · HTTPS"| APIL
    APIL --> SVCS
    SVCS <-->|"reads / writes"| PG
    SVCS <-->|"cache · rate limit"| RD
    JOBS <-->|"reads / writes"| PG
    JOBS <-->|"task queue"| RQ

    SAI -->|"extract predictions"| EC
    SPRICE -->|"EOD prices"| EY
    SPRICE -.->|"fallback"| EN
    SARCH -->|"snapshot URL"| EW
    SNOTIF -->|"email"| ER
    AAUTH -->|"email OTP"| ER
    AAUTH -->|"mobile OTP"| EM
    AAUTH -->|"OAuth"| EG
```

---

## 2. Prediction Ingestion Paths

Three distinct paths for predictions to enter the system — all funnel through the moderator review queue before going live.

```mermaid
flowchart TB
    subgraph P1["Path 1 — Full Submission  User-Driven · AI-Assisted"]
        direction TB
        P1A["User pastes article URL"] --> P1B["POST /extract\nFetch article text"]
        P1B --> P1C["Claude Sonnet\nExtract structured prediction"]
        P1C --> P1D["Pre-filled form shown to user\npredictor · stock · target · timeframe · quote"]
        P1D --> P1E["User reviews and corrects fields"]
        P1E --> P1F["POST /predictions\nstatus = pending_review\nSource URL archived to Wayback Machine"]
    end

    subgraph P2["Path 2 — Suggest a Prediction  Low-Effort User Input"]
        direction TB
        P2A["User pastes URL + optional note\ne.g. Motilal's target for Reliance here"] --> P2B["POST /predictions/suggest\nSaved to prediction_suggestions table"]
        P2B --> P2C["Moderator or Admin\nreviews suggestions queue"]
        P2C --> P2D["Click Promote\nRuns AI extraction in background"]
        P2D --> P2E["Draft prediction created\nin review queue"]
    end

    subgraph P3["Path 3 — Admin Bulk Import  Cold-Start Seeding"]
        direction TB
        P3A["Admin pastes up to 20 URLs"] --> P3B["POST /admin/bulk-extract\nQueues background extraction jobs"]
        P3B --> P3C["Celery workers process\neach URL sequentially"]
        P3C --> P3D["Extracted drafts land\nin review queue  extraction_method = ai_auto"]
    end

    RQ["Moderator Review Queue\nApprove · Reject · Edit"]
    APPROVED["Approved Prediction\nstatus = approved"]
    EVAL["Outcome Evaluation Engine\ndaily Celery job"]
    SCORE["Predictor Scorecard Update"]
    NOTIF["User Notifications\nemail via Resend API"]

    P1F --> RQ
    P2E --> RQ
    P3D --> RQ

    RQ -->|"Moderator approves"| APPROVED
    APPROVED --> EVAL
    EVAL --> SCORE
    EVAL --> NOTIF
```

---

## 3. Nightly Evaluation Pipeline

Sequential background jobs that run after market close each day.

```mermaid
flowchart LR
    YF["Yahoo Finance\nyfinance"]
    NSE["nsetools\nNSE fallback"]

    PF["Price Fetcher\n11:00 PM IST\nFetch EOD closing prices\nfor all tracked stocks"]

    DB1[("stock_daily_prices")]

    OE["Outcome Evaluator\n11:30 PM IST\nFor each pending prediction\nwhere eval_date ≤ today:\ncompare target vs actual\nHit · Miss · Partial Hit"]

    DB2[("prediction_outcomes")]

    SU["Scorecard Updater\n11:45 PM IST\nRecompute accuracy %\nstreak · sector stats\nfor all affected predictors"]

    DB3[("predictor_scorecards")]

    NS["Notification Sender\nPost-evaluation\nAlert users following\naffected predictors\nor holding watchlist stocks"]

    RESEND["Resend API\nEmail"]
    USERS["Users"]

    YF -->|"fetch prices"| PF
    NSE -.->|"fallback"| PF
    PF -->|"store"| DB1
    DB1 -->|"price history"| OE
    OE -->|"store outcomes"| DB2
    DB2 -->|"new outcomes"| SU
    SU -->|"store scorecards"| DB3
    DB2 -->|"trigger"| NS
    NS -->|"send"| RESEND
    RESEND --> USERS
```

---

## 4. Authentication Flow

Three login paths supported from day one.

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend Next.js
    participant BE as Backend FastAPI
    participant MSG91 as MSG91 Verify
    participant RESEND as Resend API
    participant GOOGLE as Google OAuth
    participant DB as PostgreSQL

    Note over User,DB: Path A — Mobile OTP
    User->>FE: Enter phone number
    FE->>BE: POST /auth/otp/send  {phone}
    BE->>MSG91: Send 6-digit OTP via DLT template
    MSG91-->>User: SMS with OTP
    User->>FE: Enter OTP
    FE->>BE: POST /auth/otp/verify  {phone, code}
    BE->>DB: Validate OTP, upsert user
    BE-->>FE: JWT access token

    Note over User,DB: Path B — Email OTP
    User->>FE: Enter email address
    FE->>BE: POST /auth/otp/send  {email}
    BE->>RESEND: Send 6-digit OTP via email
    RESEND-->>User: Email with OTP
    User->>FE: Enter OTP
    FE->>BE: POST /auth/otp/verify  {email, code}
    BE->>DB: Validate OTP, upsert user
    BE-->>FE: JWT access token

    Note over User,DB: Path C — Google OAuth
    User->>FE: Click "Continue with Google"
    FE->>GOOGLE: Redirect to Google consent screen
    GOOGLE-->>FE: Auth code via NextAuth.js callback
    FE->>BE: POST /auth/google/callback  {code}
    BE->>DB: Upsert user  merge by email if exists
    BE-->>FE: JWT access token
```

---

## 5. Data Model (Entity Relationships)

```mermaid
erDiagram
    PREDICTORS {
        uuid id PK
        string name
        string slug
        string type
        uuid parent_id FK
        string designation
        string sebi_reg_no
        boolean is_verified
    }

    STOCKS {
        uuid id PK
        string symbol
        string exchange
        string name
        string sector
        decimal current_price
    }

    STOCK_DAILY_PRICES {
        uuid id PK
        uuid stock_id FK
        date trade_date
        decimal close_price
        decimal adjusted_close
    }

    PREDICTIONS {
        uuid id PK
        uuid predictor_id FK
        uuid stock_id FK
        decimal target_price
        decimal price_at_prediction
        date prediction_date
        date target_date
        string source_url
        string status
        uuid submitted_by FK
    }

    PREDICTION_OUTCOMES {
        uuid id PK
        uuid prediction_id FK
        string outcome_status
        decimal actual_price
        decimal deviation_pct
        date evaluation_date
    }

    PREDICTOR_SCORECARDS {
        uuid predictor_id PK
        int total_predictions
        int hits
        int misses
        int partial_hits
        decimal accuracy_pct
        json sector_accuracy
    }

    USERS {
        uuid id PK
        string email
        string phone
        string role
        json auth_methods
        boolean is_active
    }

    PREDICTION_SUGGESTIONS {
        uuid id PK
        string url
        text note
        uuid submitted_by FK
        string status
        uuid promoted_to FK
    }

    PREDICTORS ||--o{ PREDICTORS : "parent firm"
    PREDICTORS ||--o{ PREDICTIONS : "makes"
    PREDICTORS ||--|| PREDICTOR_SCORECARDS : "has"
    STOCKS ||--o{ PREDICTIONS : "is target of"
    STOCKS ||--o{ STOCK_DAILY_PRICES : "has prices"
    PREDICTIONS ||--o| PREDICTION_OUTCOMES : "results in"
    USERS ||--o{ PREDICTIONS : "submits"
    USERS ||--o{ PREDICTION_SUGGESTIONS : "suggests"
```

---

## Component Summary

| Layer | Technology | Hosting |
|-------|-----------|---------|
| Frontend | Next.js 15 · React 19 · Shadcn/ui · TanStack Query | Azure Container Apps |
| Backend API | FastAPI · Python 3.12 · Pydantic v2 · SQLAlchemy 2.0 | Azure Container Apps |
| Database | PostgreSQL (Alembic migrations) | Azure Database for PostgreSQL — Burstable B1ms |
| Cache / Queue | Redis (leaderboard cache · Celery queue · OTP store) | Azure Cache for Redis — Basic C0 |
| Auth | NextAuth.js v5 (Google OAuth) · python-jose (JWT) · MSG91 (mobile OTP) · Resend (email OTP) | — |
| AI Extraction | Claude Sonnet via Anthropic Python SDK | Anthropic API |
| Price Data | yfinance (primary) · nsetools (fallback) | Yahoo Finance / NSE |
| Source Archival | Wayback Machine Save API | Internet Archive |
| Email | Resend API (OTP + notifications) | Resend |
| Monitoring | Sentry (error tracking) | Sentry Cloud |
| **Estimated Cost** | | **$50–90 / month** |
