# CLAUDE.md — Nelvra Project Bible

Single source of truth for every Claude session on this project. Read this first, every time.

Last updated: June 2026 | Version: 2.0.0 | Author: Fahad Khan

---

## 1. WHAT IS NELVRA

Nelvra is an open-core LLM observability platform for developers shipping AI-powered products — solo indie hackers to small engineering teams.

**One-line pitch:** "Know when your AI breaks before your users do — monitor, optimize, and understand your LLM app in 60 seconds."

**The problem:** Developers shipping AI products are flying blind in production — prompts degrade silently, API costs spike without warning, response quality drops after model updates.

**The solution:** Capture every LLM interaction, analyze in real time, surface anomalies automatically, and automatically optimize underperforming prompts — with a 60-second SDK integration.

**Primary goal (honest):** Portfolio and resume project to demonstrate real LLM infrastructure skills to recruiters at AI companies (Anthropic, OpenAI, Cohere, AI-first startups). Secondary: build a genuine user base and modest early revenue.

---

## 2. TARGET CUSTOMERS

**Primary:** Solo developers building AI apps, vibe coders spending real money on OpenAI/Anthropic APIs daily, full-stack engineers who added AI features to existing products, indie hackers who've never thought about monitoring.

**NOT for (v1):** Large enterprises with dedicated MLOps teams, very early-stage prototypes with no traffic, teams already using Helicone or Langfuse.

---

## 3. KEY DIFFERENTIATORS (in order of importance)

1. **Prompt Drift Detection** — detects when your prompts silently degrade in production; nobody else headlines this
2. **Automatic Prompt Optimization** — detects underperforming prompts, generates optimized versions via Claude API, one-click deploy
3. **60-Second Setup** — three lines of code, works immediately, no configuration required
4. **Plain English Everything** — no raw metrics, every insight explained in plain language

**Competitive position:** Every competitor shows dashboards. Nelvra tells you when something is wrong and does something about it.

---

## 4. FEATURE SET

### MVP Features (Weeks 1-6)

**Core Monitoring**
- Capture every LLM request and response
- Track: latency, token usage, cost per request, model version, error rate
- Full request/response logging with search and filtering
- Support OpenAI and Anthropic only (add others on demand)
- Real-time dashboard

**Cost Intelligence**
- Real-time cost monitoring per feature, endpoint, model
- Budget alerts — set monthly thresholds, get notified before overspending
- Per-request cost breakdown
- Simple cost anomaly detection (cost > X threshold)

**Basic Alerting**
- Slack alerts
- Email alerts
- Threshold-based: cost spikes, error rate increases, latency spikes

### Phase 2 Features (Weeks 7-10 — The Differentiators)

**Prompt Drift Detection (Hero Feature)**
- Monitor every prompt over time
- Detect quality score drops automatically
- Alert when prompt performance degrades below threshold
- Plain-English explanation: "Your customer support prompt quality dropped 23% in the last 48 hours"
- Full prompt version history

**Prompt Optimization Engine**
- Detect underperforming prompts (high token count, low quality score, high error rate)
- Generate optimized version via Claude API
- Side-by-side diff: original vs optimized
- Estimated savings: "34% fewer tokens, saves ~$120/month at current volume"
- One-click deploy with automatic rollback if quality drops

**Quality Scoring**
- LLM-as-judge quality scoring via Anthropic API
- Track quality scores over time
- Quality degradation alerts

### Features Deliberately Cut from v1
- Business Impact Layer — too complex, needs customer data integrations
- AI Health Score — needs enough data to be meaningful
- Agent Tracing — build after core monitoring works
- Security & Safety Monitoring — enterprise feature
- Kafka — use simple async queues first
- ClickHouse — PostgreSQL handles v1 scale fine
- TimescaleDB — add after v1
- Canadian data residency marketing
- SSO/SAML — enterprise feature
- Mobile app — developers use desktop

---

## 5. TECHNICAL ARCHITECTURE

### Stack

| Layer | Technology | Justification |
|---|---|---|
| SDK Python | `pip install nelvra` | Primary AI development language |
| SDK JavaScript | `npm install @nelvra/sdk` | Frontend/Node.js AI apps |
| API Gateway | FastAPI (Python 3.11+) | Async, high throughput |
| Database | PostgreSQL (only) | No premature optimization |
| Cache | Redis | Rate limiting, real-time counters, session |
| Background Jobs | Celery + Redis | No Kafka complexity yet |
| LLM for AI features | Anthropic API (Claude) | Quality eval, prompt optimization |
| Frontend | Next.js 14 + Tailwind CSS | SSR, great DX, fast dashboards |
| Auth | GitHub OAuth | Target users all have GitHub |
| Infrastructure v1 | Railway or Render | Ship fast first |
| Infrastructure v2 | AWS + Terraform | Production-grade at scale |
| Containerization | Docker + Docker Compose | Local dev and self-hosting |
| CI/CD | GitHub Actions | Automated testing and deployment |
| License | Apache 2.0 | Permissive, enterprise-friendly |

### Architecture Flow

```
Client SDKs (Python / JS)
        ↓ LLM Events
FastAPI Ingestion Gateway (rate limiting, auth, validation)
        ↓
PostgreSQL + Redis (storage + caching)
        ↓
Background Workers (Celery)
  - Quality Evaluator (Anthropic API — LLM-as-judge)
  - Drift Detector (statistical baselines)
  - Prompt Optimizer (Anthropic API)
  - Alert Dispatcher (Slack, email)
        ↓
FastAPI REST API + WebSocket (real-time)
        ↓
Next.js Dashboard
```

### SDK Design

```python
# Python — 3 lines
from nelvra import Nelvra
nelvra = Nelvra(api_key="nvl_xxx")
nelvra.instrument()  # Auto-patches openai, anthropic clients
```

```typescript
// JavaScript
import { Nelvra } from '@nelvra/sdk'
const nelvra = new Nelvra({ apiKey: 'nvl_xxx' })
nelvra.instrument()
```

### Prompt Drift Detection (Simple Statistical Approach)

For each prompt, every hour:
1. Calculate quality score average for last 24 hours
2. Compare to rolling 7-day baseline average
3. If current < baseline by > 15%: flag as degrading
4. Call Claude API for plain-English explanation
5. Send alert, update dashboard via WebSocket

No ML required for v1. Simple statistics work fine.

---

## 6. REPOSITORY STRUCTURE

```
nelvra/
├── CLAUDE.md
├── README.md
├── docker-compose.yml           # local dev
├── docker-compose.prod.yml      # self-hosted production
├── sdks/
│   ├── python/                  # pip install nelvra
│   │   └── nelvra/
│   │       ├── __init__.py
│   │       ├── client.py
│   │       ├── instruments/
│   │       │   ├── openai.py
│   │       │   └── anthropic.py
│   │       └── types.py
│   └── javascript/              # npm install @nelvra/sdk
│       └── src/
│           ├── index.ts
│           ├── client.ts
│           └── instruments/
│               ├── openai.ts
│               └── anthropic.ts
├── backend/
│   ├── api/                     # FastAPI application
│   │   ├── main.py
│   │   ├── routers/             # HTTP only — no business logic here
│   │   │   ├── events.py
│   │   │   ├── projects.py
│   │   │   ├── prompts.py
│   │   │   ├── analytics.py
│   │   │   └── alerts.py
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # All business logic lives here
│   │   └── dependencies.py
│   ├── workers/                 # Celery background tasks
│   │   ├── quality_evaluator.py
│   │   ├── drift_detector.py
│   │   ├── prompt_optimizer.py
│   │   └── alert_dispatcher.py
│   └── migrations/              # Alembic — never modify existing migrations
├── frontend/                    # Next.js dashboard
│   └── app/
│       ├── dashboard/
│       ├── prompts/
│       ├── alerts/
│       └── settings/
└── infra/
    ├── docker/
    └── terraform/               # Add when moving to AWS
```

---

## 7. API DESIGN

**Auth:** `Authorization: Bearer nvl_live_xxxxxxxxxxxxx`

**Core endpoints:**

```
POST   /v1/events
POST   /v1/events/batch

GET    /v1/analytics/overview
GET    /v1/analytics/requests
GET    /v1/analytics/costs
GET    /v1/analytics/quality

GET    /v1/prompts
GET    /v1/prompts/:id
POST   /v1/prompts
PUT    /v1/prompts/:id
GET    /v1/prompts/:id/drift
GET    /v1/prompts/:id/optimize
POST   /v1/prompts/:id/deploy

GET    /v1/alerts
POST   /v1/alerts
DELETE /v1/alerts/:id
GET    /v1/alerts/incidents

GET    /v1/projects
POST   /v1/projects
GET    /v1/projects/:id
PUT    /v1/projects/:id
```

---

## 8. DATA MODELS

### LLMEvent
```typescript
interface LLMEvent {
  id: string           // UUID
  project_id: string
  timestamp: DateTime
  model: string        // gpt-4o, claude-3-5-sonnet, etc.
  provider: string     // openai, anthropic
  prompt_id?: string
  messages: Message[]
  system_prompt?: string
  response_text: string
  finish_reason: string
  prompt_tokens: int
  completion_tokens: int
  total_tokens: int
  cost_usd: float
  latency_ms: int
  user_id?: string
  session_id?: string
  feature?: string
  environment: string  // production, staging, development
  quality_score?: float
  quality_flags?: string[]
  tags: string[]
  custom_metadata: JSON
}
```

### Prompt
```typescript
interface Prompt {
  id: string
  project_id: string
  name: string
  content: string
  variables: string[]
  version: int
  created_at: DateTime
  avg_quality_score: float
  avg_tokens: int
  avg_cost_usd: float
  avg_latency_ms: int
  request_count: int
  quality_trend: enum  // stable, degrading, improving
  drift_detected_at?: DateTime
  drift_explanation?: string
  optimization_status: enum  // none, suggested, testing, deployed
  optimized_version?: string
  optimization_savings?: float
}
```

---

## 9. CODING CONVENTIONS

**General**
- Backend: Python 3.11+, type hints everywhere, Black formatter, ruff linter
- Frontend: TypeScript strict mode, ESLint, Prettier
- Git: Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`)
- Testing: pytest for Python, Vitest for TypeScript, 80%+ coverage target
- Docstrings on all public functions and classes

**Python Backend**
```python
# Always use type hints
async def get_events(
    project_id: str,
    start_time: datetime,
    limit: int = 100
) -> list[LLMEvent]:
    ...

# Always use Pydantic for validation
class EventCreate(BaseModel):
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float = Field(gt=0)
```

**Architecture rules**
- Services handle business logic
- Routers handle HTTP only — never put business logic in routers

**Database**
- All tables: `id` (UUID), `created_at`, `updated_at`
- Soft deletes: `deleted_at` instead of hard deletes
- All foreign keys indexed
- Migrations via Alembic — never modify existing migrations

**Error Handling**
```python
class NelvraException(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code

# Structured error responses always
{
  "error": {
    "code": "INVALID_API_KEY",
    "message": "The provided API key is invalid or expired",
    "docs": "https://docs.nelvra.io/errors/INVALID_API_KEY"
  }
}
```

---

## 10. ENVIRONMENT VARIABLES

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nelvra
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-secret-key
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx

# AI Services
ANTHROPIC_API_KEY=sk-ant-xxx

# Billing
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Notifications
SLACK_BOT_TOKEN=xoxb-xxx

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## 11. BUSINESS MODEL

| Tier | Price | Limits | Key Features |
|---|---|---|---|
| Free / Open Source | $0 | 50k events/mo, 7-day retention | Core monitoring, self-hosted |
| Pro | $29/mo | 500k events/mo, 30-day retention | Drift detection, quality scoring, alerts |
| Team | $99/mo | 5M events/mo, 90-day retention | Prompt optimization, auto-rollback, 5 members |

**Pricing philosophy:** Low to reduce purchase hesitation for v1. Raise prices after 50+ paying users and proven value.

**Year 1 realistic targets:** $500–2,000 MRR. Primary value is resume signal and GitHub presence.

---

## 12. BUILD PLAN

### Phase 1 — MVP (Weeks 1-6)
- **Wk 1-2:** Python SDK (auto-instrument OpenAI + Anthropic), FastAPI ingestion, PostgreSQL schema, basic auth, Docker Compose
- **Wk 3-4:** Next.js + Tailwind, GitHub OAuth, dashboard (volume/cost/latency/errors), request log table, request detail view
- **Wk 5:** JS/TS SDK, threshold alerting, Slack + email alerts
- **Wk 6:** README with demo GIF (do not skip), one-command Docker Compose, landing page, pricing page, Show HN

### Phase 2 — Differentiators (Weeks 7-10)
- **Wk 7-8:** Quality scoring via Claude API, statistical baseline per prompt, drift detection (>15% degradation), plain-English explanation, alerts
- **Wk 9-10:** Detect underperforming prompts, generate optimized version via Claude API, side-by-side diff UI, cost savings estimate, one-click deploy + auto-rollback

### Phase 3 — Cloud SaaS (Weeks 11-16)
- **Wk 11-12:** Tenant isolation, Stripe billing, plan enforcement, self-serve onboarding
- **Wk 13-14:** AWS deployment, GitHub Actions CI/CD, Sentry + uptime monitoring
- **Wk 15-16:** Team management, CSV export, audit logs, performance optimization

---

## 13. THINGS TO AVOID

- Do not build Kafka/ClickHouse/TimescaleDB until you actually need them
- Do not build the business impact layer until paying customers ask for it
- Do not build enterprise features (SSO, SAML, compliance) before enterprise customers exist
- Do not support every LLM provider — OpenAI + Anthropic first
- Do not make the free tier too limited — developers need genuine value before paying
- Do not price like an enterprise product until you have enterprise traction
- Do not abandon the project after the first version — a dead repo hurts more than helps

---

## 14. SUCCESS METRICS

**Resume threshold (what actually matters)**
- 300+ GitHub stars — enough to mention credibly
- 50+ active installs — proof people use it
- 10+ paying customers — proof of commercial viability
- Active commit history — shows maintained, real project

**Product health**
- SDK installation success rate > 95%
- Time to first event: < 5 minutes from signup
- Dashboard load time: < 2 seconds
- API uptime: > 99%

---

## 17. CODING AGENT INSTRUCTIONS

These instructions apply to every coding session. Follow them without exception.

### Session Efficiency
- Be concise in all responses. No preamble, no summaries of what you just did.
- Don't explain code you've written unless asked.
- Don't ask clarifying questions for straightforward tasks — make a reasonable decision and state it in one line.
- When making multiple related changes, batch them into one response.
- If a task is ambiguous, state your assumption in one line and proceed.
- Never repeat back the instructions or summarize the plan before executing.

### Code Philosophy
- Write simple, obvious code first. If it needs a comment to explain what it does, rewrite it until it doesn't.
- Comments explain WHY, never WHAT.
  - Bad: `# loop through events`
  - Good: `# skip malformed events from legacy SDK versions`
- No premature abstraction. Solve the problem in front of you, not imagined future problems.
- If you're adding complexity, state why explicitly before doing it.
- Before making a non-trivial architectural change: explain the tradeoffs and why simpler alternatives were rejected.
- Prefer boring, readable code over clever code.
- Delete code that isn't needed. Don't comment it out.

### Security — Non-Negotiable
- Never log prompt content, model responses, user data, or secrets to stdout or log files.
- All secrets must come from environment variables only — never hardcoded, never stored in comments.
- Validate and sanitize all inbound data before processing or persisting it.
- Treat all inbound event data as untrusted.
- Rate limit public-facing endpoints where abuse could impact security, cost, or availability.
- Use SQLAlchemy ORM or parameterized queries only. Never construct SQL through string concatenation.
- Never commit anything to git that contains a real secret, API key, token, credential, or customer data.

### Dependencies
- Don't add a new dependency without a clear, stated reason.
- Prefer standard library solutions when they're sufficient.
- If adding a dependency, add it to the correct requirements file immediately.
- Remove unused dependencies when encountered.

### Database
- Never modify existing migrations. Always create a new migration.
- Every schema change requires a migration. No exceptions.
- Test migrations both up and down before committing.
- Validate data before writing it to the database.
- Preserve existing data during migrations unless explicitly required otherwise.

### APIs
- Validate inputs at the application boundary.
- Return consistent error formats.
- Preserve backward compatibility unless a versioned breaking change is intentionally introduced.
- Fail safely and return useful error messages without exposing internal implementation details.

### Error Handling
- Handle errors at every external boundary: database operations, file system operations, network requests, third-party APIs, message queues.
- Never silently swallow exceptions.
- Log only the information necessary for debugging without exposing sensitive data.

### Testing
- New business logic requires tests.
- Bug fixes require a regression test when practical.
- Do not update snapshots blindly.
- Tests should verify behavior, not implementation details.
- Existing tests must continue to pass unless requirements intentionally change.

### Scope Control
- Don't build features that are not part of the current phase or requirements.
- Don't over-engineer for scale that does not exist yet.
- Don't create abstractions that are only used once.
- Don't break existing APIs without versioning them.
- Don't leave TODO comments. Either implement the work now or create a tracked issue.
- When requirements are unclear, ask for clarification instead of making assumptions.

### Code Review Checklist
Before considering a task complete, verify:
- Is this the simplest solution that satisfies the requirements?
- Is all inbound data validated?
- Are secrets handled securely?
- Are error cases handled?
- Are tests included where appropriate?
- Does this introduce unnecessary abstractions?
- Does this preserve backward compatibility?
- Can another engineer understand this quickly without additional explanation?
- Is every added line of code necessary?
