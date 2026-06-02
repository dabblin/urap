-- URAP Sprint 7 — BizReach Route Tab + Money Tab Integration
-- Phase 1: Marketplace configs + routing sessions
-- Phase 2: CPL auction race results

-- ── urap_marketplace_configs — per-tenant webhook URLs for buyer marketplaces ──
CREATE TABLE IF NOT EXISTS urap_marketplace_configs (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       TEXT        NOT NULL,
  marketplace_id  TEXT        NOT NULL,
  webhook_url     TEXT        NOT NULL DEFAULT '',
  api_key         TEXT        NOT NULL DEFAULT '',
  cpl             FLOAT       NOT NULL DEFAULT 0.0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, marketplace_id)
);

CREATE INDEX IF NOT EXISTS idx_urap_mp_configs_tenant
  ON urap_marketplace_configs (tenant_id);

-- ── urap_routing_sessions — audit log of every lead dispatch ─────────────────
CREATE TABLE IF NOT EXISTS urap_routing_sessions (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           TEXT        NOT NULL,
  marketplace_id      TEXT        NOT NULL,
  marketplace_name    TEXT        NOT NULL DEFAULT '',
  leads_routed        INT         NOT NULL DEFAULT 0,
  estimated_earnings  FLOAT       NOT NULL DEFAULT 0.0,
  failed              INT         NOT NULL DEFAULT 0,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_urap_routing_sessions_tenant
  ON urap_routing_sessions (tenant_id, created_at DESC);

-- ── urap_race_results — CPL auction outcomes (Bass.EXE / race_agents) ────────
CREATE TABLE IF NOT EXISTS urap_race_results (
  id                       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id                TEXT        NOT NULL,
  lead_id                  TEXT        NOT NULL DEFAULT '',
  winner_marketplace_id    TEXT        NOT NULL DEFAULT '',
  winner_marketplace_name  TEXT        NOT NULL DEFAULT '',
  winning_cpl              FLOAT       NOT NULL DEFAULT 0.0,
  all_bids                 JSONB       NOT NULL DEFAULT '[]',
  dispatched               BOOLEAN     NOT NULL DEFAULT FALSE,
  error                    TEXT        NOT NULL DEFAULT '',
  created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- all_bids JSON shape: [{"marketplace_id":"px","marketplace_name":"PX Marketplace","cpl":45.0,"accepted":true,"error":""}, ...]

CREATE INDEX IF NOT EXISTS idx_urap_race_results_tenant
  ON urap_race_results (tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_urap_race_results_lead
  ON urap_race_results (lead_id);
