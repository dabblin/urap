-- Sprint 4: Warp Mode job queue
-- Run via Supabase SQL Editor or migration runner

CREATE TABLE IF NOT EXISTS urap_warp_jobs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    TEXT NOT NULL,
    icp_label    TEXT NOT NULL DEFAULT '',
    icp          JSONB NOT NULL DEFAULT '{}',
    leads_found  INT DEFAULT 0,
    sequences_queued INT DEFAULT 0,
    generated    JSONB DEFAULT '[]',
    status       TEXT DEFAULT 'complete',
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS urap_warp_jobs_tenant_idx     ON urap_warp_jobs (tenant_id);
CREATE INDEX IF NOT EXISTS urap_warp_jobs_created_at_idx ON urap_warp_jobs (created_at DESC);

ALTER TABLE urap_warp_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "urap_warp_jobs_service_insert"
    ON urap_warp_jobs FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "urap_warp_jobs_service_select"
    ON urap_warp_jobs FOR SELECT
    USING (auth.role() = 'service_role');
