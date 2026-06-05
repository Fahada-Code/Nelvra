# Nelvra

**Know when your AI breaks before your users do — monitor, optimize, and understand your LLM app in 60 seconds.**

Nelvra is an open-core LLM observability platform for developers shipping AI-powered products. While tools like Helicone and Langfuse show you technical metrics, Nelvra goes further — it detects when your prompts silently degrade in production and automatically optimizes them.

---

## Why Nelvra

Developers shipping AI products are flying blind in production:

- Prompts degrade silently over time — nobody notices until users complain
- API costs spike without warning — $300 bills become $3,000 bills overnight
- Response quality drops after model updates — no visibility until churn increases

Nelvra captures every LLM interaction, analyzes it in real time, and tells you when something is wrong — then fixes it.

---

## Features

### Core Monitoring
- Capture every LLM request and response (OpenAI + Anthropic)
- Track latency, token usage, cost per request, model version, error rate
- Real-time dashboard with searchable, filterable request log

### Cost Intelligence
- Real-time cost monitoring per feature, endpoint, and model
- Budget alerts — get notified before you overspend
- Cost anomaly detection

### Prompt Drift Detection *(Phase 2)*
- Monitor every prompt's quality score over time
- Automatically detect when a prompt degrades below its baseline
- Plain-English explanation: *"Your customer support prompt quality dropped 23% in the last 48 hours"*

### Prompt Optimization Engine *(Phase 2)*
- Automatically detect underperforming prompts
- Generate an optimized version via Claude API
- Side-by-side diff with estimated savings: *"34% fewer tokens, saves ~$120/month"*
- One-click deploy with automatic rollback if quality drops

### Alerting
- Slack and email alerts
- Threshold-based: cost spikes, error rate increases, latency spikes

---

## Quick Start

**Self-hosted (Docker Compose):**

```bash
git clone https://github.com/Fahadada-code/nelvra
cd nelvra
docker compose up -d
```

**Python SDK:**

```python
pip install nelvra

from nelvra import Nelvra
nelvra = Nelvra(api_key="nvl_xxx")
nelvra.instrument()  # Auto-patches openai and anthropic clients

# All LLM calls are now automatically tracked
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**JavaScript SDK:**

```typescript
npm install @nelvra/sdk

import { Nelvra } from '@nelvra/sdk'
const nelvra = new Nelvra({ apiKey: 'nvl_xxx' })
nelvra.instrument()  // Auto-patches OpenAI and Anthropic JS clients
```

**HTTP API (any language):**

```bash
curl -X POST https://api.nelvra.io/v1/events \
  -H "Authorization: Bearer nvl_xxx" \
  -d '{"prompt": "...", "response": "...", "model": "gpt-4o", "tokens": 234}'
```

---

## Pricing

| | Free | Pro | Team |
|---|---|---|---|
| **Price** | $0 | $29/mo | $99/mo |
| **Hosting** | Self-hosted | Cloud | Cloud |
| **Events/month** | 50,000 | 500,000 | 5,000,000 |
| **Data retention** | 7 days | 30 days | 90 days |
| **Core monitoring** | ✓ | ✓ | ✓ |
| **Prompt drift detection** | — | ✓ | ✓ |
| **Quality scoring** | — | ✓ | ✓ |
| **Slack + email alerts** | — | ✓ | ✓ |
| **Prompt optimization** | — | — | ✓ |
| **Auto-rollback** | — | — | ✓ |
| **Team members** | — | 1 | 5 |

---

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, PostgreSQL, Redis, Celery
- **Frontend:** Next.js 14, Tailwind CSS
- **SDKs:** Python (pip), JavaScript/TypeScript (npm)
- **AI:** Anthropic API (Claude) for quality scoring and prompt optimization
- **Auth:** GitHub OAuth
- **Infrastructure:** Docker Compose (self-hosted), Railway/Render (cloud v1), AWS (cloud v2)

---

## Project Status

Currently in active development. Phase 1 (MVP) in progress.

- [ ] Python SDK + FastAPI ingestion
- [ ] PostgreSQL schema + auth
- [ ] Next.js dashboard
- [ ] JavaScript SDK + alerting
- [ ] Prompt drift detection
- [ ] Prompt optimization engine
- [ ] Cloud SaaS + billing

---

## License

Apache 2.0 — see [LICENSE](LICENSE)
