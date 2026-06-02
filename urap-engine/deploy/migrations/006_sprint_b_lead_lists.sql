-- URAP Sprint B — Lead Lists
-- Named lists that users save from Company Search results.
-- Run via: supabase db push  OR  paste into Supabase SQL editor.

-- ── urap_lead_lists — list metadata ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS urap_lead_lists (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   TEXT        NOT NULL,
  name        TEXT        NOT NULL,
  item_count  INT         NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_urap_lead_lists_tenant
  ON urap_lead_lists (tenant_id, created_at DESC);

-- ── urap_lead_list_items — per-company rows ───────────────────────────────────
CREATE TABLE IF NOT EXISTS urap_lead_list_items (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  list_id       UUID        NOT NULL REFERENCES urap_lead_lists(id) ON DELETE CASCADE,
  tenant_id     TEXT        NOT NULL,
  company_name  TEXT        NOT NULL DEFAULT '',
  domain        TEXT        DEFAULT '',
  website       TEXT        DEFAULT '',
  phone         TEXT        DEFAULT '',
  email         TEXT        DEFAULT '',
  contact_name  TEXT        DEFAULT '',
  contact_title TEXT        DEFAULT '',
  industry      TEXT        DEFAULT '',
  location      TEXT        DEFAULT '',
  source        TEXT        DEFAULT '',
  added_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_urap_lead_list_items_list
  ON urap_lead_list_items (list_id);
