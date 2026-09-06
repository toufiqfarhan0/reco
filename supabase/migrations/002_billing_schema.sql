-- ============================================================================
-- Reco — Autonomous Agent Engineering System
-- Migration 002: Billing & Subscription Schema (Step 27)
-- Target: PostgreSQL / Supabase
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SUBSCRIPTIONS TABLE
-- Stores normalized Dodo Payments subscription status securely tied to user_id.
-- No payment credentials, full card numbers, or signing keys are ever stored.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    dodo_customer_id VARCHAR(100),
    dodo_subscription_id VARCHAR(100) UNIQUE,
    product_id VARCHAR(100) NOT NULL,
    plan VARCHAR(50) NOT NULL DEFAULT 'FREE' CHECK (plan IN ('FREE', 'PRO')),
    status VARCHAR(50) NOT NULL DEFAULT 'free' CHECK (status IN ('free', 'pending', 'active', 'on_hold', 'cancelled', 'failed', 'expired')),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_subscriptions_user UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_dodo_sub_id ON subscriptions(dodo_subscription_id);

-- ----------------------------------------------------------------------------
-- 2. WEBHOOK EVENTS TABLE (Idempotency Ledger)
-- Tracks processed webhook delivery IDs to guarantee safe duplicate delivery.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id VARCHAR(128) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'processed',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_webhook_id ON webhook_events(webhook_id);

-- ----------------------------------------------------------------------------
-- 3. ROW-LEVEL SECURITY (RLS)
-- Authenticated users may only read their own subscription state.
-- Webhook processing & mutation restricted to backend / service_role.
-- ----------------------------------------------------------------------------
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to view their own subscription
CREATE POLICY "Users can view own subscription"
    ON subscriptions
    FOR SELECT
    TO authenticated
    USING (auth.uid()::text = user_id);

-- Allow service role full access for webhook synchronization
CREATE POLICY "Service role manages subscriptions"
    ON subscriptions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow service role full access for webhook events
CREATE POLICY "Service role manages webhook events"
    ON webhook_events
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
