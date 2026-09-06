# AGY Prompt 08 — Dodo Payments Monetization & Final Full-System Verification

## AO Session Setup
```bash
# 1. Create GitHub Issue
# Title: feat: dodo payments checkout, webhook verification, and end-to-end regression audit

# 2. Spawn AO Session
ao session spawn --name "08-dodo-e2e-verification" --issue 8

# 3. Run with AGY CLI
agy --file docs/prompts/08_dodo_payments_and_e2e_verification.md
```

---

## Objective
Implement monetization using **Dodo Payments** (hosted checkout sessions, authentic HMAC webhook verification with `standardwebhooks`, and entitlement gating for Reco Pro). Run the complete full-system verification suite across all backend, frontend, and production build boundaries.

## Context & Architecture
- System: **Reco** (Autonomous Agent Engineering System)
- Monetization Partner: **Dodo Payments** (`https://dodopayments.com/`)
- Reference Docs:
  - [Dodo Payments Integration Guide](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_DODO.md)
  - [E2E Verification Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_E2E_VERIFICATION.md)
  - [Master Prompt Specification](file:///c:/Users/toufi/Desktop/test-ao/PROMPT.md)

## Requirements to Implement

### 1. Dodo Payments Billing Service (`reco/billing/service.py`)
- Product Tier: "Reco Pro" subscription ($9.00/month).
- Implement hosted Checkout Session creation:
  - Endpoint: `POST /billing/checkout`
  - Body: `{ user_id, email, return_url }`
  - Returns redirect checkout URL generated via Dodo Payments API.
- Implement Portal Session creation for subscription management (`POST /billing/portal`).

### 2. Webhook Ingestion & HMAC Verification
- Mount webhook endpoint: `POST /billing/webhook`.
- Verify authentic signatures using `standardwebhooks.Webhook`:
  - Enforce timestamp freshness and anti-replay protection.
  - Parse events: `payment.succeeded`, `subscription.active`, `subscription.cancelled`, `subscription.renewed`.
  - Update user entitlement status in `user_entitlements` table.
- Enforce strict Decoupling: A payment gateway downtime must NEVER crash or block core agent generation or local benchmarks.

### 3. Full-System Regression & Security Audit
- Ensure zero secrets are exposed in logs, client responses, or test files.
- Verify that only Track 1 (Automated Agent Engineering) components are active.
- Confirm all 3 benchmark domains execute with accurate 4-axis metrics.

## Verification & Acceptance Criteria
1. Webhook endpoint rejects forged or unsigned payloads with 400 Bad Request, and accepts authentically signed payloads with 200 OK.
2. Complete test regression passes:
   ```bash
   # Backend Test Suite (All tests pass)
   python -m pytest tests/ -q

   # Frontend Test Suite (All tests pass)
   npm test --prefix frontend

   # Production Build Check
   npm run build --prefix frontend
   ```
3. Generate final verification report artifact confirming system readiness.
