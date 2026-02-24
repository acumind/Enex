# Enex — Security Strategy

> Analyst Prediction Tracker for Indian Equity Markets

---

## 1. Authentication & Session Security

### JWT Design

| Decision | Detail |
|----------|--------|
| **Short-lived access tokens** | 15-minute expiry — limits blast radius if a token is stolen |
| **Refresh tokens** | 7-day expiry, stored in `httpOnly` + `Secure` + `SameSite=Strict` cookie — never in `localStorage` |
| **Token rotation** | Every refresh issues a new refresh token and invalidates the old one (tracked in Redis) |
| **Token revocation** | On logout, refresh token is blacklisted in Redis until its natural expiry |
| **Algorithm** | RS256 (asymmetric) — backend signs with private key, frontend verifies with public key |
| **Claims** | `sub` (user ID), `role`, `iat`, `exp` — no sensitive data in payload |

### OTP Security

| Rule | Detail |
|------|--------|
| **6-digit codes** | 10^6 combinations; short window makes brute force impractical |
| **5-minute expiry** | `expires_at` enforced in `otp_codes` table |
| **Max 3 verification attempts** | `attempts` counter on the OTP record — 4th attempt automatically invalidates the code |
| **Rate limiting on send** | Max 3 OTP sends per identifier per 10 minutes (Redis counter) — prevents SMS/email bombing |
| **One-time use** | `used_at` is set on first successful verification — replay attacks impossible |
| **Constant-time comparison** | Codes compared with `hmac.compare_digest()` — prevents timing attacks |
| **Hashed storage** | OTP codes stored as SHA-256 hash — plaintext never persisted |

---

## 2. API Security

### Request Authentication & Authorization Flow

```
Every incoming request:
  1. Extract Bearer token from Authorization header
  2. Verify JWT signature using public key
  3. Check token expiry (exp claim)
  4. Load user from DB (or Redis session cache)
  5. Check user.is_active → reject if banned or suspended
  6. Check user.role if endpoint requires elevated access
  7. Pass typed, verified user object to route handler
```

### Role Enforcement

Role checking is a FastAPI dependency — applied declaratively per route, never forgotten:

```python
# Public — no auth required
@router.get("/leaderboard")
async def get_leaderboard(): ...

# Authenticated users only
@router.post("/predictions")
async def submit_prediction(user: User = Depends(get_current_user)): ...

# Moderators and admins only
@router.post("/admin/predictions/{id}/approve")
async def approve_prediction(user: User = Depends(require_role("moderator", "admin"))): ...

# Admins only
@router.patch("/admin/users/{id}/role")
async def change_user_role(user: User = Depends(require_role("admin"))): ...
```

Role is re-verified on every request from the database — a role change (e.g. ban, demotion) takes effect on the next API call without requiring the user to log out.

### Rate Limiting

Applied in-app via Redis atomic counters, in addition to Azure Container Apps ingress throttling:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /auth/otp/send` | 3 requests | per identifier per 10 min |
| `POST /auth/otp/verify` | 5 requests | per identifier per 15 min |
| `POST /extract` (AI extraction) | 10 requests | per user per hour |
| `POST /predictions` (submit) | 20 requests | per user per day |
| `POST /admin/bulk-extract` | 5 requests | per admin per hour |
| Public read endpoints | 100 requests | per IP per minute |

Rate limit counters use Redis `INCR` + `EXPIRE` — atomic, fast, and automatically cleaned up.

### Input Validation

Every request body is validated by **Pydantic v2** before reaching any service logic:

```
HTTP Request
    → Pydantic schema: validates shape, types, field constraints
    → Custom validators: enforce business rules
         (target_price > 0, prediction_date not in future,
          source_url must be http/https scheme,
          phone must match E.164 format,
          stock symbol must be uppercase alphanumeric)
    → Validated, typed Python object passed to service layer
```

Raw user input **never** reaches the database or an AI prompt directly.

---

## 3. Injection Attack Prevention

### SQL Injection

Not possible by design. SQLAlchemy ORM uses parameterised queries exclusively. Direct string concatenation into queries is never used. For the rare case where raw SQL is required (complex analytics queries), SQLAlchemy's `text()` with bound parameters is the only accepted form:

```python
# Never — SQL injection vector
db.execute(f"SELECT * FROM predictions WHERE stock_symbol = '{symbol}'")

# Always — parameterised, safe
db.execute(
    text("SELECT * FROM predictions WHERE stock_symbol = :symbol"),
    {"symbol": symbol}
)
```

### Prompt Injection (AI Extraction Endpoint)

The `/extract` endpoint is a high-risk surface — users submit URLs and article content is sent to Claude. Layered mitigations:

| Layer | Mitigation |
|-------|-----------|
| **Server-side fetch** | The backend fetches the URL — users never control the raw text sent to Claude |
| **Content length cap** | Article text truncated to 8,000 tokens before sending — prevents context stuffing |
| **Structured output** | Claude returns JSON only via tool use mode — no free-form text that could influence app logic |
| **Output validation** | Pydantic validates Claude's response — unexpected fields dropped, malformed output returns an extraction error, not a crash |
| **No write access** | The extraction service is read-only — it cannot write to the database |
| **User input stripped** | Any user-supplied notes or hints are never appended to the Claude prompt |

### XSS Prevention

| Layer | Mitigation |
|-------|-----------|
| **React escapes by default** | JSX renders all values as escaped text — `dangerouslySetInnerHTML` is never used |
| **Structured API responses** | API returns typed JSON — frontend decides how to render, no raw HTML from the server |
| **Content Security Policy** | Strict CSP header blocks inline scripts and unauthorised external script sources |
| **Security headers** | `X-Content-Type-Options: nosniff` prevents MIME-type sniffing attacks |

### CSRF Prevention

| Mechanism | Detail |
|-----------|--------|
| **JWT in Authorization header** | All state-mutating requests use `Authorization: Bearer <token>` — forged cross-site forms cannot set custom headers |
| **Refresh token via `SameSite=Strict` cookie** | Cookie is never sent on cross-origin requests |
| **CORS whitelist** | Backend rejects requests from origins not in the configured allowlist |

---

## 4. CORS Configuration

```python
# Only the known frontend origin is allowed — never "*" in production
CORS_ORIGINS = {
    "local":   ["http://localhost:3000"],
    "staging": ["https://staging.enex.in"],
    "prod":    ["https://enex.in"],
}

# Credentials (cookies) only allowed from whitelisted origins
# All other origins receive 403 on preflight
```

---

## 5. Secrets & Credentials Management

```
Rule: No secret ever appears in the codebase, CI logs, or error responses.

├── Local dev         .env file (git-ignored, never committed)
├── CI/CD             GitHub Actions encrypted secrets (masked in all logs)
├── Staging/Prod      Azure Key Vault (managed identity — no passwords needed)
└── Runtime           pydantic-settings reads from environment — app is source-agnostic
```

Additional rules:
- **API keys are never logged** — structured logging middleware strips any field named `*key*`, `*secret*`, `*password*`, `*token*`, `*credential*`
- **Database connection strings never appear in error responses** — caught and replaced with a generic message at the exception middleware level
- **JWT secret is rotated** by updating Key Vault — old tokens expire naturally within their 15-minute window
- **Dependency on `.env.example`** — a sanitised `.env.example` with placeholder values is committed to guide new developers; `.env` is in `.gitignore`

---

## 6. Data Protection

### Sensitive Field Handling

| Field | Storage | API Exposure |
|-------|---------|-------------|
| Phone numbers | Plain E.164 in DB, access controlled | Masked as `+91·····1234` in public/shared responses; full value only to authenticated owner |
| Email addresses | Plain in DB, access controlled | Never returned in public endpoints; only to authenticated owner |
| OTP codes | SHA-256 hash only — plaintext never persisted | Never returned in any response |
| JWT signing key | Azure Key Vault only | Never in DB, never in logs |
| `ban_reason` | Plain in DB | Only visible to admin role — not to the banned user |
| `oauth_id` | Plain in DB | Never returned in any API response |

### Database Security

| Control | Detail |
|---------|--------|
| **Least privilege** | App DB user (`enex_app`) has `SELECT, INSERT, UPDATE, DELETE` only — no `DROP`, `ALTER`, `TRUNCATE`, `CREATE` |
| **Separate migration role** | Alembic runs as `enex_migrations` with DDL rights — completely separate from the app user |
| **TLS in transit** | All connections to Azure PostgreSQL enforce SSL — plaintext connections rejected at server level |
| **Private networking** | PostgreSQL and Redis are on the Azure VNet — not accessible from the public internet |
| **Automated backups** | Azure PostgreSQL: 7-day retention (staging), 30-day retention (production), point-in-time restore enabled |
| **No direct DB access in production** | No DB GUIs or admin tools exposed publicly — access only via bastion or Azure Portal with MFA |

---

## 7. Infrastructure Security

| Control | Detail |
|---------|--------|
| **Private networking** | PostgreSQL and Redis sit on a private Azure VNet — only Container Apps can reach them; no public endpoint |
| **Managed identity** | Containers authenticate to Key Vault via Azure Managed Identity — no stored credentials anywhere |
| **HTTPS everywhere** | Azure Container Apps enforces HTTPS; HTTP automatically redirects to HTTPS |
| **Non-root containers** | Both Dockerfiles add a non-root user — `USER appuser` in the final stage; never run as root |
| **Read-only filesystem** | Container Apps configured with a read-only root filesystem — only `/tmp` is writable |
| **No SSH access** | No SSH server in any image — debugging via Azure Container Apps log streaming only |
| **Image scanning** | Azure Container Registry runs vulnerability scanning on every pushed image (Microsoft Defender for Containers) |
| **Immutable image tags** | Production deploys reference immutable `sha-{commit}` or `v{semver}` tags — never `:latest` in prod |

---

## 8. HTTP Security Headers

Set on all responses from both the frontend (Next.js) and backend (FastAPI middleware):

```
Strict-Transport-Security : max-age=31536000; includeSubDomains; preload
Content-Security-Policy   : default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';
                             img-src 'self' data: https:; connect-src 'self' https://api.enex.in;
                             frame-ancestors 'none'
X-Content-Type-Options    : nosniff
X-Frame-Options           : DENY
Referrer-Policy           : strict-origin-when-cross-origin
Permissions-Policy        : geolocation=(), microphone=(), camera=(), payment=()
```

---

## 9. Dependency Security

**Backend (Python):**
```
pip-audit     → scans installed packages for known CVEs (runs on every PR)
bandit        → Python static security analysis: detects hardcoded secrets,
                 insecure hash functions, shell injection patterns (runs on every PR)
Dependabot    → automated PRs for outdated or vulnerable packages
uv.lock       → committed lockfile — reproducible installs, no surprise upgrades
```

**Frontend (Node.js):**
```
npm audit     → scans for vulnerable packages (runs on every PR)
Dependabot    → automated PRs for outdated or vulnerable packages
package-lock  → committed lockfile
```

**Semgrep:**
```
semgrep       → cross-language SAST: detects injection patterns, insecure crypto,
                 hardcoded credentials, dangerous functions (runs on every PR)
```

---

## 10. Security Testing in the CI Pipeline

| Stage | Tool | What is checked |
|-------|------|----------------|
| Every PR | `ruff` | Python code style and common bugs |
| Every PR | `mypy` | Type safety — prevents entire classes of runtime errors |
| Every PR | `bandit` | Python security anti-patterns |
| Every PR | `pip-audit` | Known CVEs in Python dependencies |
| Every PR | `npm audit` | Known CVEs in Node.js dependencies |
| Every PR | `semgrep` | Hardcoded secrets, injection patterns, insecure usage |
| Pre-production | OWASP ZAP | Automated DAST baseline scan against staging environment |
| Pre-public launch | Manual audit | Full OWASP Top 10 review (Sprint 8) |

---

## 11. Threat Model

| Threat | Attack Vector | Mitigation |
|--------|--------------|-----------|
| **Stolen access token** | XSS, network interception | 15-min expiry limits damage window; stored in memory not localStorage |
| **Stolen refresh token** | Cookie theft | `httpOnly` + `Secure` + `SameSite=Strict`; rotation detects reuse |
| **OTP brute force** | Automated guessing | 3-attempt lockout + rate limiting + 5-min expiry |
| **SMS/email bombing** | Repeated OTP sends | 3 sends per identifier per 10 min; MSG91 + Resend have their own abuse controls |
| **SQL injection** | Malicious input in API fields | SQLAlchemy parameterised queries — impossible by construction |
| **Prompt injection** | Malicious content in submitted URLs | Server-side fetch, length cap, structured output mode, Pydantic output validation |
| **XSS** | Injected scripts in user content | React auto-escaping + strict CSP headers |
| **CSRF** | Forged cross-site requests | JWT in Authorization header + SameSite cookies + CORS whitelist |
| **Secrets leakage** | Exposed in logs or code | Key Vault + managed identity + log field scrubbing |
| **Privilege escalation** | Manipulated JWT claims | Role re-verified from DB on every request — JWT claims not trusted for role decisions |
| **Insider DB access** | Direct DB connection | App user has no DDL rights; DB not publicly accessible; all access audited |
| **Vulnerable dependencies** | Outdated packages with CVEs | `pip-audit` + `npm audit` + Dependabot in CI |
| **Container breakout** | Malicious container process | Non-root user + read-only filesystem + no privileged mode |
| **Stale banned sessions** | Banned user continues using valid token | `user.is_active` checked on every authenticated request from DB |

---

## 12. Compliance & Legal Considerations

| Area | Approach |
|------|---------|
| **Data minimisation** | Only collect email or phone (not both required), name optional — minimum viable identity |
| **Right to deletion** | User account deletion removes personal data; prediction submissions (public interest data) are anonymised rather than deleted |
| **Prediction data legality** | Only publicly available predictions are tracked; source URL always linked; no prediction data is sold or licensed in MVP |
| **SEBI compliance** | Platform is informational only — no investment advice. Clear disclaimers on all pages. Legal review before public launch (Sprint 8). |
| **IT Act (India)** | User data stored in Azure India region where available; privacy policy published before public beta |
