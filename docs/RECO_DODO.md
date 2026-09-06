# Reco — Dodo Payments Monetization & Billing Architecture (Step 27)

## Overview

Reco integrates with **Dodo Payments** (Merchant of Record) in test/sandbox mode to monetize autonomous agent engineering capabilities. The integration enables hosted checkouts, webhook-driven subscription synchronization, and configuration-driven usage limit enforcement for the **Reco Pro** subscription tier, while guaranteeing strict isolation for Track 1 autonomous agent engineering core components.

---

## Existing Dodo Product

| Attribute | Value |
|---|---|
| **Product Name** | Reco Pro |
| **Product ID** | `pdt_0Nmvzbo4wJETkRyCMAEPt` |
| **Price** | $9.00 / month ($900 cents) |
| **Currency** | USD |
| **Billing Type** | Recurring Subscription (`Month`) |
| **Tax Category** | `saas` |
| **Environment** | `test_mode` (Sandbox) |
| **Status** | Active |

---

## Plan & Entitlement Model

Reco defines a clean, configuration-driven entitlement boundary that gates product-level optimizations without affecting evaluation benchmarks:

| Feature / Limit | Reco Free | Reco Pro |
|---|---|---|
| **Monthly Price** | $0 / mo | $9.00 / mo |
| **Max Evolution Generations** | 1 generation ($V_0 \to V_1$) | 5 generations ($V_0 \to \dots \to V_5$) |
| **Candidate Pool Size** | 2 candidates / gen | 5 candidates / gen |
| **Total Optimization Runs** | 3 jobs | 100 jobs |
| **Instant Demo Mode** | Unlimited (Always Free) | Unlimited |
| **Benchmark Suite Access** | Unrestricted (Track 1) | Unrestricted (Track 1) |

---

## Checkout Flow

All checkout sessions are generated strictly server-side using the official Dodo Payments SDK:

```
[User clicks "Upgrade to Pro"]
               │
               ▼
[POST /billing/checkout (Bearer Supabase JWT)]
               │
   (Backend validates caller identity)
               │
               ▼
[Dodo Payments SDK: client.checkout_sessions.create]
  - product_cart: [{ product_id: "pdt_0Nmvzbo4wJETkRyCMAEPt", quantity: 1 }]
  - customer: { email: user.email, name: user.display_name }
  - metadata: { user_id: user.id }
  - return_url: "http://localhost:3000/?checkout=success"
               │
               ▼
[Returns session.checkout_url]
               │
               ▼
[User redirected to Hosted Dodo Checkout]
               │
   (Customer enters test card details)
               │
               ▼
[Dodo processes payment & emits Webhook]
```

---

## Webhook Architecture & Signature Verification

### Configured Endpoint
- **Public URL**: `https://individually-star-toys-loving.trycloudflare.com/api/v1/payments/webhook`
- **FastAPI Path**: `POST /api/v1/payments/webhook`
- **Webhook Endpoint ID**: `ep_3IlLh6t63yjEJAbT12sNPoJG9QZ`

### Signature Verification Mechanism
Dodo Payments webhooks utilize standard HMAC-SHA256 signatures with replay protection via timestamps. Signature verification is executed using the official `standardwebhooks` engine via `client.webhooks.unwrap()`:

1. **Headers Checked**:
   - `webhook-id`: Unique message identifier (`msg_...` or `evt_...`)
   - `webhook-timestamp`: Unix epoch seconds
   - `webhook-signature`: Format `v1,<base64_hmac_sha256>`
2. **Raw Body Preserved**: The endpoint consumes `await request.body()` directly before JSON parsing to avoid byte alteration.
3. **Invalid Signature**: If the signature or timestamp fails verification, the endpoint returns `HTTP 401 Unauthorized` immediately.

### Idempotency Enforcement
Network retries and replay requests are handled idempotently:
1. When a webhook arrives, the backend queries `webhook_events` for `webhook_id`.
2. If already present, processing is short-circuited and an immediate `{"status": "already_processed"}` (200 OK) is returned.
3. Replaying the same webhook 5 times produces 0 duplicate database rows and 0 plan downgrades.

---

## Subscription Lifecycle Handling

Reco subscribes to the canonical set of subscription and payment events:

| Event Type | Dodo Trigger | Reco Plan | Reco Status |
|---|---|---|---|
| `subscription.active` | Successful checkout & mandate creation | `PRO` | `active` |
| `subscription.renewed` | Periodic billing renewal succeeds | `PRO` | `active` |
| `subscription.updated` | Plan or subscription fields update | `PRO` / `FREE` | Synced |
| `subscription.cancelled` | User cancels recurring renewal | `FREE` | `cancelled` |
| `subscription.expired` | Subscription period completes | `FREE` | `expired` |
| `subscription.failed` | Initial mandate or renewal charge fails | `FREE` | `failed` |
| `subscription.on_hold` | Temporary card failure in dunning | `FREE` | `on_hold` |
| `payment.succeeded` | One-time or recurring payment confirmation | `PRO` | `active` |

---

## Supabase Persistence Schema

Database schema is managed in migration [`supabase/migrations/002_billing_schema.sql`](file:///c:/Users/toufi/Desktop/test-ao/supabase/migrations/002_billing_schema.sql):

### 1. `subscriptions`
- `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- `user_id VARCHAR(255) UNIQUE NOT NULL`
- `dodo_customer_id VARCHAR(100)`
- `dodo_subscription_id VARCHAR(100) UNIQUE`
- `product_id VARCHAR(100) NOT NULL`
- `plan VARCHAR(50) NOT NULL DEFAULT 'FREE'` (`FREE`, `PRO`)
- `status VARCHAR(50) NOT NULL DEFAULT 'free'` (`free`, `active`, `on_hold`, `cancelled`, `failed`, `expired`)
- `current_period_start TIMESTAMPTZ`
- `current_period_end TIMESTAMPTZ`
- `created_at TIMESTAMPTZ DEFAULT NOW()`
- `updated_at TIMESTAMPTZ DEFAULT NOW()`

### 2. `webhook_events` (Idempotency Ledger)
- `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- `webhook_id VARCHAR(128) UNIQUE NOT NULL`
- `event_type VARCHAR(100) NOT NULL`
- `status VARCHAR(50) DEFAULT 'processed'`
- `payload JSONB DEFAULT '{}'::jsonb`
- `created_at TIMESTAMPTZ DEFAULT NOW()`

### Row-Level Security (RLS)
- Authenticated users may execute `SELECT` on `subscriptions` where `auth.uid()::text = user_id`.
- Users cannot read other users' billing records.
- All webhook synchronization writes are executed via backend service context.

---

## Investigation of Earlier Failed Delivery

### Symptom
An earlier delivery of `payment.succeeded` was flagged as `FAILED` in the Dodo developer dashboard.

### Root Causes
1. **Route Mismatch / Missing Route**: FastAPI did not have `/api/v1/payments/webhook` mounted in `reco/api/app.py`. Requests received a 404 or connection rejection.
2. **Missing Dependency**: The `standardwebhooks` package required by `dodopayments.webhooks.unwrap()` was not installed.
3. **Tunnel Lifetime**: Temporary Cloudflare tunnel URLs (`trycloudflare.com`) expire when the command-line tunnel process terminates.

### Resolutions
1. Mounted `POST /api/v1/payments/webhook` with proper raw byte body handling.
2. Installed `standardwebhooks` and verified HMAC-SHA256 signature verification.
3. Implemented local in-memory caching and safe failure containment ensuring database or network hiccups return safe fallbacks.

---

## Track 1 Core Engine Isolation

To protect the automated agent engineering core:
- `GoalAnalyzer`, `ArchitectureGenerator`, `AgentGraphRuntime`, `Benchmark`, `FailureAnalyzer`, `MutationEngine`, and `Neatlogs` contain **zero imports** of `reco.billing`.
- If Dodo Payments is unavailable or times out, core agent graph execution and benchmarking continue without interruption.
- Demo mode optimizations bypass billing gates entirely.

---

## Local Development & Cloudflare Tunnel Workflow

For local webhook testing:
1. Start FastAPI: `python -m uvicorn reco.api.app:app --host 0.0.0.0 --port 8000`
2. Start Cloudflare Tunnel: `cloudflared tunnel --url http://localhost:8000`
3. Update or verify the public URL matches the Dodo dashboard webhook settings.
4. Send test events using Dodo Dashboard's "Resend" button or via `standardwebhooks` test payloads.

---

## Production Deployment Checklist

When promoting from test mode to live production:
1. Set `DODO_PAYMENTS_ENVIRONMENT=live_mode` in production secrets.
2. Update `DODO_PAYMENTS_API_KEY` to live production secret key (`dodo_live_...`).
3. Create production webhook endpoint on Dodo dashboard pointing to live HTTPS domain (e.g. `https://reco.ai/api/v1/payments/webhook`).
4. Set `DODO_PAYMENTS_WEBHOOK_KEY` to live webhook signing secret (`whsec_...`).
5. Run Supabase migration `002_billing_schema.sql` on production PostgreSQL instance.
6. Verify live pricing and tax configuration on Reco Pro product.
