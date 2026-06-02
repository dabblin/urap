-- Sprint 6: Zapier webhooks, developer API keys, bulk jobs, Autopilot config
-- Run via Supabase SQL Editor (project: rtyzrrbezivflqhaernb)

-- ── Zapier webhook subscriptions ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS urap_zapier_webhooks (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id  TEXT NOT NULL,
    event      TEXT NOT NULL,   -- globalStatus value: meeting_set | qualified | etc.
    url        TEXT NOT NULL,
    name       TEXT DEFAULT '',
    active     BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS urap_zapier_tenant_event_idx ON urap_zapier_webhooks (tenant_id, event, active);

ALTER TABLE urap_zapier_webhooks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "urap_zapier_service_all"
    ON urap_zapier_webhooks
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');


-- ── Developer API keys ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS urap_api_keys (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    TEXT NOT NULL,
    name         TEXT DEFAULT 'Default',
    key_hash     TEXT NOT NULL UNIQUE,
    key_prefix   TEXT NOT NULL,
    active       BOOLEAN DEFAULT TRUE,
    created_at   TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ DEFAULT NULL,
    revoked_at   TIMESTAMPTZ DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS urap_api_keys_tenant_idx   ON urap_api_keys (tenant_id);
CREATE INDEX IF NOT EXISTS urap_api_keys_hash_idx     ON urap_api_keys (key_hash);

ALTER TABLE urap_api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "urap_api_keys_service_all"
    ON urap_api_keys
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');


-- ── Bulk enrichment jobs ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS urap_bulk_jobs (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id  TEXT NOT NULL,
    source     TEXT NOT NULL DEFAULT 'icp',   -- "csv" | "icp"
    total      INT DEFAULT 0,
    enriched   INT DEFAULT 0,
    failed     INT DEFAULT 0,
    status     TEXT DEFAULT 'complete',        -- "running" | "complete" | "error"
    results    JSONB DEFAULT '[]',
    error      TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS urap_bulk_jobs_tenant_idx ON urap_bulk_jobs (tenant_id);
CREATE INDEX IF NOT EXISTS urap_bulk_jobs_created_idx ON urap_bulk_jobs (created_at DESC);

ALTER TABLE urap_bulk_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "urap_bulk_jobs_service_all"
    ON urap_bulk_jobs
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');


-- ── Autopilot config ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS urap_autopilot_configs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         TEXT NOT NULL UNIQUE,
    enabled           BOOLEAN DEFAULT FALSE,
    icp               JSONB NOT NULL DEFAULT '{}',
    schedule_hours    INT DEFAULT 24,
    daily_send_limit  INT DEFAULT 50,
    last_run_at       TIMESTAMPTZ DEFAULT NULL,
    last_run_stats    JSONB DEFAULT NULL,
    updated_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS urap_autopilot_tenant_idx ON urap_autopilot_configs (tenant_id);

ALTER TABLE urap_autopilot_configs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "urap_autopilot_service_all"
    ON urap_autopilot_configs
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');
