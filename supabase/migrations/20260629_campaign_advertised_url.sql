-- Sprint 10 — Campaign advertised_url
-- Paste into: supabase.com/dashboard/project/rtyzrrbezivflqhaernb/sql/new

alter table urap_campaigns
  add column if not exists advertised_url text not null default '';
