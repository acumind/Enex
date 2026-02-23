# Enex - Analyst Prediction Tracker

## Problem Statement

Financial analysts, research firms, and media houses routinely publish stock price targets, buy/sell recommendations, and market predictions. However:

- **No accountability**: Analysts rarely revisit or acknowledge their past predictions, especially wrong ones.
- **Retail investor harm**: Small investors make decisions based on these predictions, often getting stuck in poorly-performing stocks.
- **Survivorship bias**: Only successful calls get highlighted; failures are quietly buried.
- **No centralized tracking**: There is no easy way for a retail investor to check an analyst's historical accuracy before trusting their advice.

Enex solves this by building a transparent, data-driven accountability layer on top of the financial prediction ecosystem.

---

## Core Concept

A web application that:
1. **Ingests** analyst predictions from multiple sources (news, TV, social media, research reports)
2. **Tracks** those predictions against actual market outcomes over time
3. **Scores** analysts, firms, and media houses on prediction accuracy
4. **Informs** retail investors with reliability ratings before they act on any recommendation

---

## Phase 1: Foundation (MVP)

### 1.1 Data Model Design

#### Entities

| Entity | Key Fields |
|--------|------------|
| **Analyst** | name, firm, designation, bio, social_links, avatar, created_at |
| **Firm/MediaHouse** | name, type (brokerage/media/independent), website, logo |
| **Prediction** | analyst_id, stock_symbol, prediction_type (target_price / buy / sell / hold / sector_call), target_price, target_date, prediction_date, source_url, source_type (TV/article/report/tweet), confidence_level (if stated), raw_quote |
| **Stock** | symbol, exchange, name, sector, current_price (cached) |
| **PredictionOutcome** | prediction_id, outcome_status (hit/miss/partial/expired/pending), actual_price_at_target_date, deviation_percentage, evaluated_at |
| **AnalystScorecard** | analyst_id, total_predictions, hits, misses, accuracy_pct, avg_deviation, sector_accuracy (JSON), timeframe_accuracy (JSON), last_updated |

### 1.2 Prediction Ingestion (Semi-Automated)

Start with a **manual + assisted** approach before going fully agentic:

- **Manual entry UI**: Admin/community can submit predictions with source links
- **Structured form**: Stock, analyst, target price, date, source URL, screenshot/archive
- **Duplicate detection**: Prevent the same prediction being entered twice
- **Source archival**: Save a snapshot (screenshot or web archive link) of the source as proof — analysts sometimes delete or edit their predictions

### 1.3 Outcome Evaluation Engine

- **Daily job**: Compare pending predictions against actual stock prices
- **Evaluation logic**:
  - Target price predictions: Did the stock reach the target within the stated timeframe?
  - If no timeframe stated, use configurable defaults (3 months / 6 months / 1 year)
  - Allow a tolerance band (e.g., within 5% of target = partial hit)
  - Track both upside and downside calls separately
- **Price data source**: Use free/affordable market data APIs (Yahoo Finance, NSE/BSE data for Indian markets, Alpha Vantage, etc.)

### 1.4 Basic Web Interface

- **Home page**: Leaderboard of analysts ranked by accuracy
- **Analyst profile page**: Full history of predictions, hit/miss breakdown, accuracy trend over time
- **Stock page**: All predictions made for a given stock, with outcomes
- **Search**: Find analysts or stocks quickly
- **Filters**: By sector, timeframe, firm, prediction type

### 1.5 Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Frontend** | Next.js (React) | SSR/SSG for SEO (analyst names, stock pages), App Router, good DX |
| **Backend API** | FastAPI (Python) — separate service | Python's data analysis ecosystem (pandas, yfinance, nsetools), best AI/ML integration (Anthropic SDK), async performance |
| **Database** | PostgreSQL | Relational data with complex queries (joins, aggregations, time-series) |
| **ORM** | SQLAlchemy 2.0 + Alembic (migrations) | Mature Python ORM, excellent PostgreSQL support |
| **Cache** | Redis (Upstash) | For leaderboard caching, rate limiting, job queues |
| **Job Scheduler** | Celery + Redis (or ARQ for lightweight async) | Daily outcome evaluation, price fetching, notifications |
| **Auth** | NextAuth.js (frontend) + JWT verification (backend) | Google OAuth, user accounts for community submissions |
| **Deployment** | Azure Container Apps (both frontend + backend) | Serverless containers, auto-scaling, single cloud provider |

> **Architecture note:** Frontend and backend are separate services communicating via REST API. This enables independent deployment, leverages Python's strengths for financial data processing, and keeps the API consumable by future mobile apps or third-party integrations.

---

## Phase 2: Agentic Ingestion

This is where the system becomes truly powerful.

### 2.1 AI-Powered Prediction Extraction

Build agents (using Claude API) that can:

- **Monitor news sources**: Scrape/RSS-feed financial news sites for articles containing price targets
- **Parse predictions from unstructured text**: Extract structured data (analyst name, stock, target price, timeframe) from natural language articles
  - Example input: *"Motilal Oswal's Rajat Rajgarhia sees Infosys reaching Rs 2,100 in the next 12 months"*
  - Extracted: `{ analyst: "Rajat Rajgarhia", firm: "Motilal Oswal", stock: "INFY", target: 2100, currency: "INR", timeframe: "12 months", date: "2026-02-20" }`
- **Monitor social media**: Track prominent analysts on X/Twitter for stock calls
- **Monitor TV transcripts**: If transcripts of financial TV shows (CNBC, ET Now, etc.) are available
- **Confidence scoring**: Agent rates its own extraction confidence; low-confidence extractions go to human review queue

### 2.2 Human-in-the-Loop Review

- Extracted predictions land in a **review queue**
- Community moderators or admins verify before publishing
- Over time, high-confidence extractions can be auto-approved
- This prevents garbage data from polluting accuracy scores

### 2.3 Source Monitoring Pipeline

```
Sources (RSS/API/Scraper)
    → Raw Article Queue
    → AI Extraction Agent (Claude)
    → Structured Prediction (draft)
    → Review Queue (human verification)
    → Published Prediction
    → Outcome Tracking Pipeline
```

---

## Phase 3: Community & Engagement

### 3.1 User Accounts & Features

- **Follow analysts**: Get notified when they make new predictions
- **Watchlist**: Track predictions for stocks you own or are interested in
- **Alerts**: "Analyst X who gave a target of Y for stock Z — that prediction just expired at 40% below target"
- **Community submissions**: Users can submit predictions they spot, with source links (moderated)

### 3.2 Analyst Response System

- Allow analysts/firms to **claim their profile** and respond
- They can provide context for why a prediction failed
- This adds fairness — markets are unpredictable, context matters
- But the data remains: the prediction was made, and the outcome is what it is

### 3.3 Reliability Badges

- Simple visual system:
  - **High reliability**: >65% accuracy over 50+ tracked predictions
  - **Moderate reliability**: 45-65% accuracy
  - **Low reliability**: <45% accuracy
  - **Insufficient data**: <10 tracked predictions
- Sector-specific badges (e.g., "Reliable for IT sector, unreliable for pharma")

---

## Phase 4: Advanced Analytics & Intelligence

### 4.1 Deep Analytics

- **Sector-wise accuracy**: Which analysts are best at which sectors?
- **Timeframe analysis**: Are they better at short-term or long-term calls?
- **Bull vs. Bear accuracy**: Some analysts are only accurate in bull markets
- **Firm-level aggregation**: Which brokerages have the best overall track record?
- **Contrarian indicator**: Some analysts are so consistently wrong they become useful as reverse indicators
- **Herding detection**: Flag when multiple analysts give suspiciously similar targets simultaneously

### 4.2 Market Context Layer

- Tag predictions with market conditions at the time (bull/bear/sideways, sector rotation phase, macro events)
- This helps users understand if an analyst is genuinely skilled or just riding a trend

### 4.3 Comparison Tools

- Compare two analysts head-to-head
- Compare an analyst's picks against a simple index fund return
- "Would you have been better off ignoring this analyst and buying Nifty 50?"

---

## Phase 5: Monetization & Sustainability

### 5.1 Revenue Streams (Future)

| Stream | Description |
|--------|-------------|
| **Freemium model** | Basic leaderboard free; detailed analytics, alerts, and API access behind a subscription |
| **API access** | Let fintech apps, robo-advisors, and other platforms query analyst reliability scores |
| **Institutional reports** | Sell aggregated accuracy reports to firms who want to benchmark their analysts |
| **Advertising** | Financial product ads (tasteful, non-conflicting) |
| **Premium alerts** | Real-time notifications when high-accuracy analysts make new calls |

### 5.2 Data Moat

Over time, the historical prediction database becomes extremely valuable — no one else will have this longitudinal data of analyst predictions mapped to outcomes.

---

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Legal pushback from analysts/firms** | They may claim defamation or IP violations | Only use publicly available predictions, always link to source, present data factually without editorializing, allow analyst rebuttals |
| **Data accuracy** | Wrong extraction = wrong scores = lost credibility | Human review queue, confidence thresholds, community correction mechanism, source archival |
| **Market data costs** | Real-time price feeds are expensive | Use end-of-day data (sufficient for target evaluation), free APIs where possible, cache aggressively |
| **Cold start problem** | Not useful until enough predictions are tracked | Seed with historical data (manually enter well-known past predictions), focus on one market (e.g., Indian equities) first |
| **Analyst gaming** | Once tracked, analysts may give vague predictions to avoid being scored | Score vagueness as a negative signal; only track specific, falsifiable predictions |
| **Scope creep** | Trying to cover all markets, all analysts too soon | Start with one market (e.g., NSE/BSE), top 50 analysts, and expand from there |

---

## Rollout Sequence

> See ROLLOUT_PLAN.md for detailed sprint breakdown.

```
Days 1-3:    Sprint 0 — Project scaffolding, DB schema, CI/CD, dev environment
Days 4-10:   Sprint 1 — Core CRUD APIs, stock price fetcher, seed data
Days 11-17:  Sprint 2 — Prediction entry UI, AI extraction, source archival
Days 18-24:  Sprint 3 — Outcome evaluation engine, scorecard computation
Days 25-34:  Sprint 4 — Public interface: leaderboard, profiles, search, SEO
Days 35-41:  Sprint 5 — User auth, watchlists, follow, notifications
Days 42-48:  Sprint 6 — Historical seeding, landing page, polish
             --- MVP Launch (invite-only beta) — ~Week 7 ---
Days 49-55:  Sprint 7 — Beta feedback, bug fixes, rate limiting
Days 56-62:  Sprint 8 — Load testing, security audit, legal pages
             --- Public Beta Launch — ~Week 9 ---
Month 3-4:   Phase 2 — Agentic ingestion (RSS, social media, auto-extraction)
Month 4-5:   Phase 3 — Community features, analyst verification, badges
Month 5-7:   Phase 4 — Advanced analytics, comparison tools
Month 7+:    Phase 5 — Monetization, public API, premium features
```

---

## Initial Scope Constraints (To Stay Focused)

1. **One market first**: Indian equities (NSE/BSE) — large retail investor base, lots of analyst activity on TV and social media
2. **Equity only**: No derivatives, commodities, or forex predictions initially
3. **Target price predictions only**: The most specific, falsifiable type — skip vague "market outlook" predictions
4. **Top 100 analysts/firms**: Don't try to track everyone; start with the most followed/influential ones
5. **English language only**: Hindi/regional language extraction can come later

---

## Success Metrics

- **Data quality**: >95% accuracy in prediction-to-outcome mapping
- **Coverage**: 500+ tracked predictions within first 3 months of beta
- **User engagement**: Users checking analyst reliability before acting on tips
- **Community trust**: Active community submissions and corrections
- **Retention**: Users returning weekly to check leaderboard updates

---

## Open Questions — Resolution Status

| # | Question | Status | Decision |
|---|----------|--------|----------|
| 1 | Target market: India-first, or US equities, or both? | **Resolved** | India-first (NSE/BSE). Large retail base, active analyst ecosystem. |
| 2 | Prediction scope: Only equity price targets? | **Resolved** | Price targets only. Most specific and falsifiable. |
| 3 | Scoring: Simple hit/miss or weighted by magnitude? | **Resolved** | Simple hit/miss with 5% tolerance band for partial hits. Magnitude weighting deferred to Phase 4. |
| 4 | Community moderation model? | **Deferred** | Start with admin-controlled review queue. Wikipedia-style community moderation to be designed in Phase 3. |
| 5 | Identity verification for analysts? | **Deferred** | `is_verified` field exists in schema. Verification process (claim profile, proof of identity) to be designed in Phase 3. |
| 6 | Historical seeding: How far back? | **Resolved** | ~100 well-known predictions from the past 1-2 years. Focus on top 20-30 most-followed analysts/firms. |
