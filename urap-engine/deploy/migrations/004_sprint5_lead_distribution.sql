-- Sprint 5: Inbound lead capture & ping-post distribution
-- Run via Supabase SQL Editor (project: rtyzrrbezivflqhaernb)

CREATE TABLE IF NOT EXISTS urap_lead_distribution (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id            TEXT NOT NULL,
    first_name           TEXT DEFAULT '',
    last_name            TEXT DEFAULT '',
    email                TEXT DEFAULT '',
    phone                TEXT DEFAULT '',
    company              TEXT DEFAULT '',
    title                TEXT DEFAULT '',
    ip_address           TEXT DEFAULT '',
    country_code         TEXT DEFAULT 'US',
    source               TEXT DEFAULT 'web',
    intent_signals       JSONB DEFAULT '[]',
    enriched_data        JSONB DEFAULT '{}',
    raw_payload          JSONB DEFAULT '{}',
    status               TEXT DEFAULT 'captured',   -- captured | claimed | rejected
    claimed_by_tenant_id TEXT DEFAULT NULL,
    claimed_at           TIMESTAMPTZ DEFAULT NULL,
    created_at           TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS urap_lead_dist_tenant_idx     ON urap_lead_distribution (tenant_id);
CREATE INDEX IF NOT EXISTS urap_lead_dist_email_idx      ON urap_lead_distribution (email);
CREATE INDEX IF NOT EXISTS urap_lead_dist_created_at_idx ON urap_lead_distribution (created_at DESC);
CREATE INDEX IF NOT EXISTS urap_lead_dist_status_idx     ON urap_lead_distribution (status);

ALTER TABLE urap_lead_distribution ENABLE ROW LEVEL SECURITY;

-- Service role can do everything
CREATE POLICY "urap_lead_dist_service_all"
    ON urap_lead_distribution
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Anonymous insert only — allows embed snippet on client sites to submit leads
CREATE POLICY "urap_lead_dist_anon_insert"
    ON urap_lead_distribution FOR INSERT
    WITH CHECK (auth.role() = 'anon');
