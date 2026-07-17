-- Sprint 10 — Autopilot config table (was referenced by Sprint 6 code but never created)
-- Paste this entire block into: supabase.com/dashboard/project/rtyzrrbezivflqhaernb/sql/new
-- Until this table exists, the engine reads config from the AUTOPILOT_CONFIG_B64 env var.

create table if not exists urap_autopilot_configs (
  id                   uuid primary key default gen_random_uuid(),
  tenant_id            text not null unique,
  enabled              boolean not null default false,
  icp                  jsonb not null default '{}'::jsonb,
  schedule_hours       int  not null default 24,
  daily_send_limit     int  not null default 50,
  route_after_warp     boolean not null default false,
  route_marketplace_id text not null default '',
  route_min_score      int  not null default 60,
  last_run_at          timestamptz,
  last_run_stats       jsonb,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now()
);

create index if not exists idx_autopilot_configs_tenant on urap_autopilot_configs(tenant_id);
