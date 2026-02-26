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
| **Predictor** | name, slug, type (individual/brokerage/research_firm/media_house/influencer), parent_id (self-ref for individual→firm), designation, bio, website, social_links, avatar, sebi_reg_no, is_verified |
| **Prediction** | predictor_id, stock_symbol, prediction_type (target_price / buy / sell / hold / sector_call), target_price, target_date, prediction_date, source_url, source_type (TV/article/report/tweet), confidence_level (if stated), raw_quote |
| **Stock** | symbol, exchange, name, sector, current_price (cached) |
| **PredictionOutcome** | prediction_id, outcome_status (hit/miss/partial/expired/pending), actual_price_at_target_date, deviation_percentage, evaluated_at |
| **PredictorScorecard** | predictor_id, total_predictions, hits, misses, accuracy_pct, avg_deviation, sector_accuracy (JSON), timeframe_accuracy (JSON), last_updated |

> **Unified Predictor model:** Any entity that publishes stock predictions — individual analysts, brokerage research desks, media houses, influencers, Telegram channels — is tracked as a **Predictor**. Individuals can be linked to their parent firm via `parent_id`, enabling both individual and firm-level accountability. The leaderboard ranks all predictor types together (with type filters).

### 1.2 Prediction Ingestion (Semi-Automated)

Start with a **manual + assisted** approach before going fully agentic:

- **Full submission**: User pastes URL → AI extracts prediction details → user reviews pre-filled form → submits → goes to moderator review queue
- **Suggest a prediction** (low-effort): User pastes just a URL + optional note ("this article has Motilal's target for Reliance"). Goes to a suggestions queue. Moderators or admin can promote it to a full prediction via AI extraction. Designed to lower the barrier — users don't need to verify every field.
- **Admin bulk-import**: Admin pastes multiple URLs (one per line) → system runs AI extraction on each in the background → results land in review queue as drafts. This lets admin seed 20-30 predictions per day during early days to build leaderboard data before the community grows.
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

- **Home page**: Leaderboard of predictors (analysts, firms, media) ranked by accuracy
- **Predictor profile page**: Full history of predictions, hit/miss breakdown, accuracy trend over time. For firms: also shows individual analysts and their roll-up stats
- **Stock page**: All predictions made for a given stock, with outcomes
- **Search**: Find predictors or stocks quickly
- **Filters**: By sector, timeframe, predictor type (individual/firm/media), prediction type

### 1.5 User Roles & Permissions

| Role | Who | Capabilities |
|------|-----|-------------|
| **Visitor** | Unauthenticated | Browse leaderboard, predictor profiles, stock pages, search. Read-only access to all public data. |
| **User** | Registered (OTP/OAuth) | Everything a visitor can + submit predictions (go to review queue), follow predictors, watchlist stocks, receive notifications, manage own profile. |
| **Moderator** | Promoted by admin | Everything a user can + access review queue, approve/reject predictions, edit predictor profiles, flag/edit incorrect data. |
| **Admin** | System owner | Full access: everything above + manage user roles (promote/demote moderators and admins), ban/suspend users, create/edit/delete predictors and stocks, trigger evaluation jobs, access system stats, seed data. |

> **Key rule:** All user-submitted predictions go through the moderator review queue in MVP, regardless of submitter history. No auto-approve for any user role.

### 1.6 Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Frontend** | Next.js (React) | SSR/SSG for SEO (analyst names, stock pages), App Router, good DX |
| **Backend API** | FastAPI (Python) — separate service | Python's data analysis ecosystem (pandas, yfinance, nsetools), best AI/ML integration (Anthropic SDK), async performance |
| **Database** | PostgreSQL | Relational data with complex queries (joins, aggregations, time-series) |
| **ORM** | SQLAlchemy 2.0 + Alembic (migrations) | Mature Python ORM, excellent PostgreSQL support |
| **Cache** | Redis (Upstash) | For leaderboard caching, rate limiting, job queues |
| **Job Scheduler** | Celery + Redis (or ARQ for lightweight async) | Daily outcome evaluation, price fetching, notifications |
| **Auth** | NextAuth.js (frontend) + JWT verification (backend) | Google OAuth + Email OTP + Mobile OTP (MSG91). Three login paths for maximum accessibility |
| **Deployment** | Azure Container Apps (both frontend + backend) | Serverless containers, auto-scaling, single cloud provider |

> **Architecture note:** Frontend and backend are separate services communicating via REST API. This enables independent deployment, leverages Python's strengths for financial data processing, and keeps the API consumable by future mobile apps or third-party integrations.

---

## Phase 2: Scaling Prediction Ingestion

### 2.1 RSS Feed Monitoring (Semi-Automated)

Subscribe to RSS feeds from major financial news sites. New articles are queued, and the system runs AI extraction to identify any stock predictions. All extracted predictions go to the review queue — no auto-approve.

- **RSS sources**: Moneycontrol, Economic Times Markets, LiveMint, Business Standard
- **Pipeline**: RSS poll (every 30 min) → filter for prediction-related articles → AI extraction → review queue
- **Human-in-the-loop**: Moderators review all RSS-extracted predictions before approval. This ensures data quality while significantly increasing volume.

### 2.2 Licensed Data Feeds (If Available)

Explore licensing structured analyst target data from platforms like Trendlyne or StockEdge. This is cleaner, legal, and already structured — no scraping or extraction errors.

### 2.3 Automated Site Crawling & Social Media (Deferred)

Full-scale scraping of financial sites and social media monitoring is **deferred to Phase 4+** due to:

- **Legal risk**: Most financial sites have anti-scraping TOS. No clear safe harbor under Indian IT Act.
- **Cost**: Running LLM extraction on thousands of articles/tweets daily = significant API costs.
- **Noise**: Social media (Twitter/X, YouTube, Telegram) is 95% noise for actionable predictions with specific price targets.
- **Maintenance**: Scrapers break frequently as site layouts change.

If pursued later, the approach would be:
- Start with structured sites only (not social media)
- License data where possible rather than scraping
- Invest in robust entity resolution (mapping names to predictors)
- Budget for ongoing scraper maintenance

```
Phase 2 Pipeline (RSS + Licensed Data):

RSS Feeds / Licensed APIs
    → Article Queue (filtered for predictions)
    → AI Extraction Agent (Claude)
    → Structured Prediction (draft)
    → Review Queue (human verification)
    → Published Prediction
    → Outcome Tracking Pipeline
```

---

## Phase 3: Community & Engagement

### 3.1 User Accounts & Features

- **Follow predictors**: Get notified when any analyst, firm, or media house makes new predictions
- **Watchlist**: Track predictions for stocks you own or are interested in
- **Alerts**: "Predictor X who gave a target of Y for stock Z — that prediction just expired at 40% below target"
- **Community submissions**: Users can submit predictions they spot (from any source type), with source links (moderated)

### 3.2 Predictor Response System

- Allow any predictor (individual, firm, media house) to **claim their profile** and respond
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

- **Sector-wise accuracy**: Which predictors are best at which sectors?
- **Timeframe analysis**: Are they better at short-term or long-term calls?
- **Bull vs. Bear accuracy**: Some predictors are only accurate in bull markets
- **Entity-type comparison**: Are brokerages more accurate than media houses? Do individual analysts outperform their firm's research desk?
- **Firm roll-up**: Aggregate accuracy of all individuals linked to a firm, vs the firm's own direct predictions
- **Contrarian indicator**: Some predictors are so consistently wrong they become useful as reverse indicators
- **Herding detection**: Flag when multiple predictors give suspiciously similar targets simultaneously

### 4.2 Market Context Layer

- Tag predictions with market conditions at the time (bull/bear/sideways, sector rotation phase, macro events)
- This helps users understand if an analyst is genuinely skilled or just riding a trend

### 4.3 Comparison Tools

- Compare two predictors head-to-head (any type: analyst vs analyst, firm vs firm, firm vs media)
- Compare a predictor's picks against a simple index fund return
- "Would you have been better off ignoring this predictor and buying Nifty 50?"

---

## Phase 5: Monetization & Sustainability

### 5.1 Data Moat

Over time, the historical prediction database becomes extremely valuable — no one else will have this longitudinal data of analyst predictions mapped to outcomes. This is the core competitive advantage that enables all monetization.

### 5.2 Payment Infrastructure

| Component | Details |
|-----------|---------|
| **Payment gateway** | Razorpay (Indian market standard) — UPI, cards, net banking, wallets |
| **Subscription billing** | Razorpay Subscriptions API — auto-renewal, plan changes, cancellation |
| **Invoice generation** | GST-compliant invoicing with HSN/SAC codes |
| **Webhook handling** | Payment success/failure → plan activation/deactivation |
| **Refund policy engine** | Pro-rated refunds for annual plans, configurable grace periods |

### 5.3 Freemium Access Gating

| Tier | Access |
|------|--------|
| **Free** | Leaderboard (top 20), predictor profiles (last 10 predictions), basic stock page, community suggestions |
| **Pro** | Full leaderboard, unlimited prediction history, advanced filters, export CSV, email alerts (50/month), API (1K calls/month) |
| **Enterprise** | Everything in Pro + bulk API (100K calls/month), webhook feeds, custom reports, SLA support, white-label embeds |

Implementation: middleware-based gating — check user's plan tier on each request, return `402 Payment Required` with upgrade prompt for gated features.

### 5.4 Premium Analytics Features

| Feature | Description |
|---------|-------------|
| **Advanced leaderboard filters** | Filter by sector, market cap, time period, prediction type, minimum sample size |
| **Head-to-head comparison** | Compare any two predictors across all metrics with visual charts |
| **Sector heatmaps** | Which sectors have the most accurate/inaccurate predictions overall |
| **Portfolio simulator** | "If you followed predictor X's calls, here's your hypothetical return vs Nifty 50" |
| **Custom alerts** | "Notify me when [predictor] with >70% accuracy makes a new call on [sector/stock]" |
| **Accuracy trends** | Is a predictor getting better or worse over time? Rolling accuracy charts |
| **Consensus tracker** | When multiple high-accuracy predictors agree on a stock, surface that signal |
| **Prediction timing analysis** | Analyze which predictors are best at short-term vs long-term calls |

### 5.5 Data & API Access

| Tier | Rate Limit | Features |
|------|------------|----------|
| **Free API** | 100 calls/day | Leaderboard top 20, basic predictor stats |
| **Pro API** | 1,000 calls/day | Full leaderboard, predictor details, prediction history, stock predictions |
| **Enterprise API** | 100,000 calls/day | Everything + bulk endpoints, webhook subscriptions, historical data dumps |

Additional B2B offerings:
- **Embeddable widgets** — `<iframe>` or JS snippet showing predictor scores on third-party sites (fintech apps, broker platforms)
- **Bulk data exports** — Monthly/quarterly data dumps for research institutions
- **Custom reports** — Aggregated accuracy reports for firms benchmarking their own analysts

### 5.6 Advertising & Sponsorship

| Type | Description |
|------|-------------|
| **Contextual ads** | Financial product ads on stock pages (demat accounts, mutual funds, insurance) — non-conflicting |
| **Sponsored predictor profiles** | Brokerages/firms pay for verified badge + enhanced profile placement |
| **Newsletter sponsorship** | Sponsored section in weekly digest emails |

Guidelines: No ads that could create conflicts of interest (e.g., no stock tips ads). Clearly label all sponsored content.

### 5.7 Community & Engagement Features

| Feature | Monetization Angle |
|---------|-------------------|
| **User predictions** | Let registered users make their own predictions, track personal accuracy — builds engagement & data |
| **Comments & discussion** | Threaded comments on predictions — drives daily active usage |
| **Prediction contests** | Monthly/quarterly contests with prizes — viral growth, sponsor potential |
| **Referral program** | Invite friends → earn free Pro days — organic growth engine |
| **Verified predictor claims** | Predictors claim their profile, add context to predictions — builds trust, upsell for enhanced profiles |
| **Community corrections** | Users flag incorrect predictions/outcomes — improves data quality at zero cost |

### 5.8 Premium Notifications

| Channel | Free | Pro |
|---------|------|-----|
| **Email** | Weekly digest only | Real-time + digest, 50 custom alerts/month |
| **Push (web/mobile)** | None | Real-time alerts for followed predictors |
| **SMS** | None | Critical alerts only (new prediction from >80% accuracy predictor on your watchlist) |
| **Telegram/WhatsApp** | None | Bot integration for real-time prediction feeds |

### 5.9 Mobile App (Future)

| Feature | Details |
|---------|---------|
| **React Native app** | Share codebase with web where possible (API-first approach already supports this) |
| **Push notifications** | Native push for prediction alerts |
| **Offline leaderboard** | Cache leaderboard data for offline viewing |
| **Quick submit** | Screenshot → AI extraction of predictions from mobile |

### 5.10 Pricing Strategy (Indian Market)

```
Free:        ₹0/month   — Basic access, community features
Pro:         ₹299/month  — Advanced analytics, alerts, API, exports (₹2,999/year — 2 months free)
Enterprise:  ₹2,999/month — Bulk API, webhooks, custom reports, SLA (₹29,999/year)
```

Benchmarks: Screener.in Pro ₹400/mo, Tijori Finance ₹499/mo, Trendlyne ₹399/mo — ₹299 is competitive for entry.

### 5.11 Implementation Priority

```
Month 7-8:   Payment infra (Razorpay) + Freemium gating middleware + Pro plan
Month 8-9:   Premium analytics (filters, comparisons, portfolio simulator)
Month 9-10:  API access tiers + embeddable widgets
Month 10-11: Community features (user predictions, comments, contests)
Month 11-12: Premium notifications (multi-channel) + mobile app planning
Month 12+:   Enterprise tier, B2B data products, advertising platform
```

---

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Legal pushback from predictors** | They may claim defamation or IP violations | Only use publicly available predictions, always link to source, present data factually without editorializing, allow predictor rebuttals |
| **Data accuracy** | Wrong extraction = wrong scores = lost credibility | Human review queue, confidence thresholds, community correction mechanism, source archival |
| **Market data costs** | Real-time price feeds are expensive | Use end-of-day data (sufficient for target evaluation), free APIs where possible, cache aggressively |
| **Cold start problem** | Not useful until enough predictions are tracked | Seed with historical data (manually enter well-known past predictions), focus on one market (e.g., Indian equities) first |
| **Predictor gaming** | Once tracked, predictors may give vague predictions to avoid being scored | Score vagueness as a negative signal; only track specific, falsifiable predictions |
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
Month 3-4:   Phase 2 — RSS feed monitoring, licensed data feeds, scaled ingestion
Month 4-5:   Phase 3 — Community features, analyst verification, badges
Month 5-7:   Phase 4 — Advanced analytics, comparison tools, automated crawling (if needed)
Month 7-8:   Phase 5a — Payment infra (Razorpay), freemium gating, Pro plan
Month 8-9:   Phase 5b — Premium analytics, API tiers, embeddable widgets
Month 9-11:  Phase 5c — Community features, premium notifications, mobile planning
Month 12+:   Phase 5d — Enterprise tier, B2B data products, advertising
```

---

## Initial Scope Constraints (To Stay Focused)

1. **One market first**: Indian equities (NSE/BSE) — large retail investor base, lots of analyst activity on TV and social media
2. **Equity only**: No derivatives, commodities, or forex predictions initially
3. **Target price predictions only**: The most specific, falsifiable type — skip vague "market outlook" predictions
4. **Top 100 predictors**: Don't try to track everyone; start with the most followed/influential analysts, firms, and media houses
5. **English language only**: Hindi/regional language extraction can come later

---

## Success Metrics

- **Data quality**: >95% accuracy in prediction-to-outcome mapping
- **Coverage**: 500+ tracked predictions within first 3 months of beta
- **User engagement**: Users checking predictor reliability before acting on tips
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
| 5 | Identity verification for predictors? | **Deferred** | `is_verified` field exists in schema. Verification process (claim profile, proof of identity) to be designed in Phase 3. |
| 6 | Historical seeding: How far back? | **Resolved** | ~100 well-known predictions from the past 1-2 years. Focus on top 20-30 most-followed predictors. |
| 7 | Unified predictor model? | **Resolved** | Single `predictors` table covers individuals, firms, media houses, influencers. Individuals link to parent firm via `parent_id`. Scorecards and leaderboard apply to all types equally. |
| 8 | Authentication methods? | **Resolved** | Three login paths: Google OAuth + Email OTP + Mobile OTP (via MSG91). All in MVP. Indian retail investors expect mobile OTP. |
| 9 | User roles and management? | **Resolved** | Four roles: visitor (unauth), user, moderator, admin. All submissions reviewed by moderators. Admin manages roles from UI. Ban/suspend capability in MVP. First admin seeded via CLI. |
| 10 | Prediction input methods? | **Resolved** | MVP: three input paths — full user submission (URL → AI extract → form → review), suggest-a-prediction (low-effort URL+note → suggestions queue), admin bulk-import (batch URLs → AI extraction → review queue). Automated site crawling deferred to Phase 4+. |
