-- URAP — Sprint 1 initial schema
-- Run against your Supabase project via the SQL editor or CLI.

-- ── Tenants ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS urap_tenants (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id                 TEXT UNIQUE NOT NULL,
  api_key                   TEXT NOT NULL,
  name                      TEXT,
  zapier_webhook_url        TEXT,
  stripe_subscription_item_id TEXT,
  created_at                TIMESTAMPTZ DEFAULT NOW()
);

-- ── Contacts (enrichment cache) ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS urap_contacts (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           TEXT NOT NULL,
  lead_id             TEXT UNIQUE NOT NULL,
  name                TEXT NOT NULL,
  email               TEXT UNIQUE NOT NULL,
  phone               TEXT,
  linkedin_url        TEXT,
  company             TEXT NOT NULL,
  title               TEXT DEFAULT '',
  intent_signals      JSONB DEFAULT '[]',
  global_status       TEXT NOT NULL DEFAULT 'prospecting',
  channel_state       JSONB NOT NULL DEFAULT '{"email":"idle","sms":"idle","linkedin":"idle","voice":"idle"}',
  enrichment_source   TEXT,          -- 'prospeo' | 'snov' | 'hunter' | 'manual'
  email_verified      BOOLEAN DEFAULT FALSE,
  last_activity       TIMESTAMPTZ DEFAULT NOW(),
  assigned_agent      TEXT,
  consent_record      JSONB,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_urap_contacts_tenant ON urap_contacts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_urap_contacts_status ON urap_contacts(global_status);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_urap_contacts_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS urap_contacts_updated_at ON urap_contacts;
CREATE TRIGGER urap_contacts_updated_at
  BEFORE UPDATE ON urap_contacts
  FOR EACH ROW EXECUTE FUNCTION update_urap_contacts_updated_at();

-- ── Consent Ledger (insert-only — Sprint 2 TrustedForm) ──────────────────────
CREATE TABLE IF NOT EXISTS urap_consent_ledger (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id         TEXT NOT NULL,
  tenant_id       TEXT NOT NULL,
  source          TEXT NOT NULL,        -- TrustedForm cert URL
  consented_at    TIMESTAMPTZ NOT NULL,
  ip_address      TEXT NOT NULL,
  one_to_one_rule BOOLEAN NOT NULL DEFAULT TRUE,
  platform_name   TEXT NOT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: ledger is insert-only — no UPDATE or DELETE allowed
ALTER TABLE urap_consent_ledger ENABLE ROW LEVEL SECURITY;
CREATE POLICY "urap_consent_insert_only"
  ON urap_consent_ledger FOR INSERT WITH CHECK (true);

-- ── Enrichment Cache (dedup API calls across tenants) ─────────────────────────
CREATE TABLE IF NOT EXISTS urap_enrichment_cache (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email           TEXT UNIQUE NOT NULL,
  enrichment_data JSONB NOT NULL,
  source          TEXT NOT NULL,
  verified        BOOLEAN DEFAULT FALSE,
  expires_at      TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '30 days'),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_enrichment_cache_expires ON urap_enrichment_cache(expires_at);
